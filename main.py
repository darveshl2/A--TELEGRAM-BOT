import asyncio
import ipaddress
import logging
import os
import re
import socket
import ssl
import threading
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import aiohttp
import dns.asyncresolver
from flask import Flask
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from google import genai
from google.genai import types as genai_types

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
ai = genai.Client(api_key=GEMINI_API_KEY)

MAX_HTML = 5_000_000
HTTP_TIMEOUT = 15
MAX_REDIRECTS = 5

class BotStates(StatesGroup):
    waiting_for_ai = State()
    waiting_for_url = State()
    waiting_for_security_url = State()

MESSAGES = {
    "tj": {
        "welcome": "Ассалому алейкум! Ба Cyber AI Bot хуш омадед.",
        "ai": "🤖 Gemini AI",
        "scan": "🔍 Сканкунии пурраи сайт",
        "html": "📄 HTML-и сайт",
        "phone": "📞 Санҷиши рақам",
        "photo": "🖼 Таҳлили акс",
        "help": "ℹ️ Ҷӯё",
        "ask_ai": "Савол ё вазифаро фиристед:",
        "ask_url": "Линки сайтро фиристед (https://...):",
        "ask_phone": "Рақамро бо + ва рамзи кишвар фиристед:",
    },
    "ru": {
        "welcome": "Здравствуйте! Добро пожаловать в Cyber AI Bot.",
        "ai": "🤖 Gemini AI",
        "scan": "🔍 Полное сканирование сайта",
        "html": "📄 HTML сайта",
        "phone": "📞 Проверка номера",
        "photo": "🖼 Анализ изображения",
        "help": "ℹ️ Помощь",
        "ask_ai": "Отправьте вопрос или задачу:",
        "ask_url": "Отправьте URL сайта (https://...):",
        "ask_phone": "Отправьте номер с + и кодом страны:",
    },
    "en": {
        "welcome": "Hello! Welcome to Cyber AI Bot.",
        "ai": "🤖 Gemini AI",
        "scan": "🔍 Full website scan",
        "html": "📄 Website HTML",
        "phone": "📞 Phone check",
        "photo": "🖼 Image analysis",
        "help": "ℹ️ Help",
        "ask_ai": "Send your question or task:",
        "ask_url": "Send a website URL (https://...):",
        "ask_phone": "Send a number with + and country code:",
    }
}

user_languages = {}

def lang_of(user_id):
    return user_languages.get(user_id, "tj")

def msg(user_id, key):
    return MESSAGES[lang_of(user_id)][key]

def keyboard(user_id):
    m = MESSAGES[lang_of(user_id)]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=m["ai"]), KeyboardButton(text=m["scan"])],
            [KeyboardButton(text=m["html"]), KeyboardButton(text=m["phone"])],
            [KeyboardButton(text=m["photo"]), KeyboardButton(text=m["help"])],
            [KeyboardButton(text="🌐 Забон / Язык / Language")],
        ],
        resize_keyboard=True,
    )

@dp.message(Command("start"))
async def def_start(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang_tj")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
        ]
    )
    await message.answer("Забонро интихоб кунед / Выберите язык / Choose language:", reply_markup=kb)

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(call: types.CallbackQuery):
    user_languages[call.from_user.id] = call.data.split("_")[1]
    await call.answer()
    await call.message.answer(msg(call.from_user.id, "welcome"), reply_markup=keyboard(call.from_user.id))

@dp.message(F.text == "🌐 Забон / Язык / Language")
async def language_button(message: types.Message):
    await def_start(message)

# ----------------- SAFE PUBLIC-URL ACCESS -----------------

def public_ip(ip_text):
    ip = ipaddress.ip_address(ip_text)
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified)

async def resolve_public(host):
    try:
        infos = await asyncio.to_thread(socket.getaddrinfo, host, None)
        return all(public_ip(item[4][0]) for item in infos)
    except socket.gaierror:
        return False
async def validate_url(url):
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        raise ValueError("URL нодуруст аст.")
    if p.username or p.password:
        raise ValueError("URL бо username/password иҷозат нест.")
    if not await resolve_public(p.hostname):
        raise ValueError("Суроға ба сервери маҳаллӣ ё хусусӣ ишора мекунад.")
    return url

async def fetch_public(url):
    current = await validate_url(url)
    timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
    headers = {"User-Agent": "CyberAI-DefensiveScanner/1.0"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        for _ in range(MAX_REDIRECTS + 1):
            async with session.get(current, allow_redirects=False) as r:
                body = await r.text(errors="ignore")
                if r.status in {301, 302, 303, 307, 308}:
                    location = r.headers.get("Location")
                    if not location:
                        break
                    current = await validate_url(urljoin(current, location))
                    continue
                if len(body) > MAX_HTML:
                    body = body[:MAX_HTML]
                return current, r.status, r.headers, body
    raise ValueError("Зиёда аз ҳадди redirect.")

# ----------------- HTML / METADATA -----------------

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta = []
        self.links = []
        self.scripts = []
        self.forms = []
        self._title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        tag = tag.lower()
        if tag == "title":
            self._title = True
        if tag == "meta" and ("name" in a or "property" in a):
            self.meta.append(a.get("name") or a.get("property"), a.get("content", ""))
        if tag == "a" and a.get("href"):
            self.links.append(a.get("href"))
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        if tag == "form":
            self.forms.append(a.get("action", ""))

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._title = False

    def handle_data(self, data):
        if self._title:
            self.title += data.strip()

# ----------------- DNS -----------------

async def dns_records(host):
    result = {}
    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = 4
    resolver.lifetime = 5
    for rtype in ("A", "AAAA", "CNAME", "MX", "NS", "TXT"):
        try:
            answers = await resolver.resolve(host, rtype)
            result[rtype] = [answer.to_text() for answer in answers]
        except Exception:
            result[rtype] = []
    return result

# ----------------- TLS -----------------

def tls_info(host, port=443):
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=8) as raw:
        with context.wrap_socket(raw, server_hostname=host) as s:
            cert = s.getpeercert()
            cipher = s.cipher()
            version = s.version()

    sans = [x[1] for x in cert.get("subjectAltName", []) if x[0] == "DNS"]
    expires = cert.get("notAfter", "")
    days_left = None
    if expires:
        try:
            expire_time = datetime.strptime(expires, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days_left = (expire_time - datetime.now(timezone.utc)).days
        except ValueError:
            pass

    return {
        "expires": expires,
        "days_left": days_left,
        "sans": sans[:100],
        "tls_version": version,
        "cipher": cipher[0] if cipher else "",
    }

# ----------------- SECURITY ANALYSIS -----------------

SEC_HEADERS = {
    "strict-transport-security": "HSTS",
    "content-security-policy": "CSP",
    "x-content-type-options": "X-Content-Type-Options",
    "x-frame-options": "X-Frame-Options",
    "referrer-policy": "Referrer-Policy",
    "permissions-policy": "Permissions-Policy",
    "cross-origin-opener-policy": "COOP",
    "cross-origin-resource-policy": "CORP",
}

def security_report(url, status, headers, body):
    p = urlparse(url)
    parser = PageParser()
    parser.feed(body)
    lower_headers = {k.lower(): v for k, v in headers.items()}
    findings = []
    score = 100

    if p.scheme == "https":
        findings.append("🟢 HTTPS фаъол аст")
    else:
        score -= 25
        findings.append("🔴 HTTPS фаъол нест")

    for key, label in SEC_HEADERS.items():
        if key in lower_headers:
            findings.append(f"🟢 {label}: мавҷуд")
        else:
            findings.append(f"🟡 {label}: ёфт нашуд")
            score -= 5

    if headers.get("Server"):
        findings.append(f"ℹ️ Server header: {headers.get('Server')}")

    cookies = headers.getall("Set-Cookie", [])
    for cookie in cookies[:20]:
        low = cookie.lower()
        missing = []
        if "secure" not in low:
            missing.append("Secure")
        if "httponly" not in low:
            missing.append("HttpOnly")
        if "samesite" not in low:
            missing.append("SameSite")
        if missing:
            findings.append(f"🟡 Cookie flags missing: {', '.join(missing)}")

    mixed = re.findall(r"""(?i)src=["'](http://[^\s"'<]+)""", body, re.I)
    if mixed:
        findings.append(f"🔴 Mixed-content references: {len(mixed)}")
        score = min(10, score - len(mixed))

    return {
        "score": max(0, min(100, score)),
        "status": status,
        "title": parser.title[:200],
        "links": len(parser.links),
        "scripts": len(parser.scripts),
        "forms": len(parser.forms),
        "findings": findings,
    }

def detect_technologies(headers, body):
    text = body.lower()
    h = " ".join(f"{k}:{v}" for k, v in headers.items()).lower()
    signatures = {
        "WordPress": ["wp-content", "wp-includes"],
        "Shopify": ["cdn.shopify.com", "shopify"],
        "Next.js": ["_next_data_", "/_next/"],
        "React": ["react", "react-dom"],
        "Vue": ["vue.js", "vue"],
        "Laravel": ["laravel_session"],
        "Django": ["csrfmiddlewaretoken"],
        "Cloudflare": ["cf-ray"],
    }
    return sorted(name for name, needles in signatures.items() if any(x in text or x in h for x in needles))

# ----------------- FULL DEFENSIVE SCAN -----------------

async def full_scan(url):
    final_url, status, headers, body = await fetch_public(url)
    host = urlparse(final_url).hostname

    report = security_report(final_url, status, headers, body)
    report["final_url"] = final_url
    report["dns"] = await dns_records(host)
    report["technologies"] = detect_technologies(headers, body)

    if urlparse(final_url).scheme == "https":
        try:
            report["tls"] = await asyncio.to_thread(tls_info, host, 443)
        except Exception as e:
            report["tls_error"] = str(e)
    else:
        report["tls"] = None

    for path, key in (("/robots.txt", "robots"), ("/sitemap.xml", "sitemap")):
        try:
            u = await validate_url(urljoin(final_url, path))
            _, st, h, b = await fetch_public(u)
            report[key] = {
                "status": st,
                "content_type": h.get("Content-Type", ""),
                "size": len(b),
                "present": 200 <= st < 400,
            }
        except Exception as e:
            report[key] = {"present": False, "error": str(e)}

    return report

def format_scan(report):
    lines = [
        "🛡 CYBER AI - DEFENSIVE REPORT",
        f"🔗 URL: {report['final_url']}",
        f"📊 HTTP status: {report['status']}",
        f"🔑 Security score: {report['score']}/100",
        f"📑 Title: {report.get('title') or '-'}",
        f"🔗 Links: {report['links']}",
        f"📜 Scripts: {report['scripts']}",
        f"📝 Forms: {report['forms']}",
        "",
        "🔒 Security:",
        *report["findings"],
        "",
        "🌐 DNS:",
    ]
    for rtype, values in report["dns"].items():
        if values:
            lines.append(f"{rtype}: " + ", ".join(values[:10]))

    tls = report.get("tls")
    if tls:
        lines += [
            "",
            "🔒 TLS:",
            f"Version: {tls['tls_version']}",
            f"Cipher: {tls['cipher']}",
            f"Expires: {tls['expires']}",
            f"Days left: {tls['days_left']}",
            f"Certificate SANs: {len(tls['sans'])}",
        ]

    lines += [
        "",
        "💻 Technologies:",
        ", ".join(report["technologies"]) if report["technologies"] else "Unknown",
        "",
        "📁 Passive files:",
        f"robots.txt: {'present' if report['robots'].get('present') else 'not found'}",
        f"sitemap.xml: {'present' if report['sitemap'].get('present') else 'not found'}",
        "",
        "ℹ️ Танҳо санҷишҳои ғайрифаъол ва маълумоти оммавӣ истифода мешаванд.",
    ]
    return "\n".join(lines)

@dp.message(F.text.in_([MESSAGES["tj"]["scan"], MESSAGES["ru"]["scan"], MESSAGES["en"]["scan"]]))
async def scan_start(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_security_url)
    await message.answer(msg(message.from_user.id, "ask_url"))

@dp.message(BotStates.waiting_for_security_url, F.text)
async def scan_run(message: types.Message, state: FSMContext):
    status = await message.answer("Сканукунии пурраи ғайрифаъол оғоз шуд...")
    try:
        report = await full_scan(message.text.strip())
        text = format_scan(report)

        lang = lang_of(message.from_user.id)
        prompt = (
            f"Language: {lang}\n"
            "Summarize this defensive security report. Explain the important findings "
            "and safe remediation steps. Do not propose exploitation.\n\n" + text
        )
        ai_response = await asyncio.to_thread(
            ai.models.generate_content,
            model=GEMINI_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                system_instruction="You are a defensive cybersecurity assistant.",
                max_output_tokens=1800,
            ),
        )
        final = text + "\n\n🤖 Gemini analysis:\n" + (ai_response.text or "")
        await status.edit_text(final[:3900])
    except Exception as e:
        logging.exception("Full scan failed")
        await status.edit_text(f"❌ Хатогӣ: {e}")
    finally:
        await state.clear()

# ----------------- HTML -----------------

@dp.message(F.text.in_([MESSAGES["tj"]["html"], MESSAGES["ru"]["html"], MESSAGES["en"]["html"]]))
async def html_start(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_url)
    await message.answer(msg(message.from_user.id, "ask_url"))

@dp.message(BotStates.waiting_for_url, F.text)
async def html_get(message: types.Message, state: FSMContext):
    try:
        final_url, status, headers, body = await fetch_public(message.text.strip())
        if "text/html" not in headers.get("Content-Type", "").lower() and "html" not in body.lower():
            raise ValueError("Ҷавоб HTML нест.")

        path = "website.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)

        await message.answer_document(
            FSInputFile(path),
            caption=f"HTML: {final_url}\nHTTP status: {status}",
        )
        os.remove(path)
    except Exception as e:
        await message.answer(f"❌ {e}")
    finally:
        await state.clear()

# ----------------- GEMINI -----------------

SYSTEM = """
You are a helpful multilingual AI assistant.
Answer in the user's language.
For cybersecurity, provide defensive and authorized guidance only.
Never claim to know private information about a person from a phone number.
"""

@dp.message(F.text.in_([MESSAGES["tj"]["ai"], MESSAGES["ru"]["ai"], MESSAGES["en"]["ai"]]))
async def ai_start(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_ai)
    await message.answer(msg(message.from_user.id, "ask_ai"))

@dp.message(BotStates.waiting_for_ai, F.text)
async def ai_text(message: types.Message, state: FSMContext):
    try:
        response = await asyncio.to_thread(
            ai.models.generate_content,
            model=GEMINI_MODEL,
            contents=f"Language: {lang_of(message.from_user.id)}\n{message.text}",
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM,
                max_output_tokens=2500,
            ),
        )
        answer = response.text or "Ҷавоб гирифта нашуд."
        for i in range(0, len(answer), 3900):
            await message.answer(answer[i : i + 3900])
    except Exception as e:
        await message.answer(f"❌ Gemini error: {e}")
    finally:
        await state.clear()

@dp.message(BotStates.waiting_for_ai, F.photo)
async def ai_image(message: types.Message, state: FSMContext):
    try:
        f = await bot.get_file(message.photo[-1].file_id)
        stream = await bot.download_file(f.file_path)
        data = stream.read()

        part = genai_types.Part.from_bytes(data=data, mime_type="image/jpeg")
        prompt = message.caption or "Ин аксро таҳлил кун."
        response = await asyncio.to_thread(
            ai.models.generate_content,
            model=GEMINI_MODEL,
            contents=[part, f"Language: {lang_of(message.from_user.id)}\n{prompt}"],
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM,
                max_output_tokens=2200,
            ),
        )
        await message.answer(response.text or "Ҷавоб гирифта нашуд.")
    except Exception as e:
        await message.answer(f"❌ Image analysis error: {e}")
    finally:
        await state.clear()

# ----------------- PHONE - NON-IDENTIFYING -----------------

@dp.message(F.text.in_([MESSAGES["tj"]["phone"], MESSAGES["ru"]["phone"], MESSAGES["en"]["phone"]]))
async def phone_start(message: types.Message):
    await message.answer(msg(message.from_user.id, "ask_phone"))

@dp.message(F.text.regexp(r"^\+\d{7,15}$"))
async def phone_check(message: types.Message):
    number = message.text.strip()
    await message.answer(
        f"📱 Phone check\n"
        f"Формат: дуруст менамояд\n"
        f"Рақам баъд аз +: {len(number) - 1}\n\n"
        f"Маълумоти хусусии соҳиби рақам ё рӯйхати аккаунтҳо "
        f"Instagram/TikTok/WhatsApp/Telegram аз рӯи рақам ҷустуҷӯ карда намешавад."
    )

# ----------------- PHOTO / HELP -----------------

@dp.message(F.text.in_([MESSAGES["tj"]["photo"], MESSAGES["ru"]["photo"], MESSAGES["en"]["photo"]]))
async def photo_help(message: types.Message):
    await message.answer("Аксро фиристед ва дар каप्शन нависед, ки чӣ таҳлил кардан лозим аст.")

@dp.message(F.text.in_([MESSAGES["tj"]["help"], MESSAGES["ru"]["help"], MESSAGES["en"]["help"]]))
async def help_message(message: types.Message):
    await message.answer(
        "🤖 Cyber AI Bot\n"
        "• Gemini AI ва таҳлили акс\n"
        "• Full defensive website scan\n"
        "  * DNS: A/AAAA/CNAME/MX/NS/TXT\n"
        "  * TLS certificate information\n"
        "  * HTTPS & security headers\n"
        "  * Cookie security flags\n"
        "  * Mixed-content detection\n"
        "  * robots.txt / sitemap.xml\n"
        "  * Basic technology detection\n"
        "• Public HTML retrieval\n"
        "Ин версия прокси, brute-force, credential theft, account takeover ё ҷустуҷӯи маълумоти хусусии одамро иҷро намекунад."
    )

# ----------------- HEALTH CHECK -----------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Cyber AI Bot is running."

def run_web():
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    asyncio.run(main())
