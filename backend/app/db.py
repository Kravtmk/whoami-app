import sqlite3
from pathlib import Path

DB_PATH = Path("/data/whoami.db")

def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=5,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        percent INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS day_logs (
        user_id TEXT NOT NULL,
        day TEXT NOT NULL,
        sleep_minutes INTEGER DEFAULT 480,
        buffer_minutes INTEGER DEFAULT 120,
        PRIMARY KEY (user_id, day)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        day TEXT NOT NULL,
        role_id INTEGER NOT NULL,
        minutes INTEGER NOT NULL,
        FOREIGN KEY (role_id) REFERENCES roles(id)
    )
    """)

    conn.commit()
    conn.close()