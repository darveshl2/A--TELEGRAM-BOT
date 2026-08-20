import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "bot.db")


def get_connection():
    return sqlite3.connect(DATABASE)


# Сохтани база
    def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        user_id INTEGER UNIQUE,
        date_joined TEXT,
        activity INTEGER DEFAULT 0,
        permissions TEXT DEFAULT 'user'
    )
    """)

    # Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()


# Илова кардани корбар
def add_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO users
        (user_id, date_joined)
        VALUES (?, ?)
        """,
        (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()


# Илова кардани фаъолият
def add_activity(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET activity = activity + 1
        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


# Сабти лог
def add_log(user_id, action):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO logs
        (user_id, action, date)
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            action,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    conn.commit()
    conn.close()


# Гирифтани маълумоти корбар
def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cursor.fetchone()

    conn.close()

    return user
