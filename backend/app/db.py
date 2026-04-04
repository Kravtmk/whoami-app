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

    # ВАЖНО: включаем foreign keys в SQLite (по умолчанию могут быть OFF)
    cursor.execute("PRAGMA foreign_keys = ON;")
    


    

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL UNIQUE,
        display_name TEXT
    );
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS
    idx_users_telegram_id
    ON users(telegram_id);
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        percent INTEGER NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS day_logs (
        user_id INTEGER NOT NULL,
        day TEXT NOT NULL,
        sleep_minutes INTEGER DEFAULT 480,
        buffer_minutes INTEGER DEFAULT 120,
        PRIMARY KEY (user_id, day),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS segments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        day TEXT NOT NULL,
        role_id INTEGER NOT NULL,
        minutes INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES roles(id)
    );
    """)

    conn.commit()
    conn.close()

def upsert_user(telegram_id: int, display_name: str | None = None) -> dict:
    """
    Создаёт пользователя если его нет.
    Если есть — обновляет display_name (если передан).
    Возвращает row как dict: {"id":..., "telegram_id":..., "display_name":...}
    """
    conn = get_connection()
    cur = conn.cursor()

    # создать если нет
    cur.execute(
        """
        INSERT OR IGNORE INTO users(telegram_id, display_name)
        VALUES(?, ?)
        """,
        (telegram_id, display_name),
    )

    # обновить имя (если передали)
    if display_name:
        cur.execute(
            """
            UPDATE users
            SET display_name = ?
            WHERE telegram_id = ?
            """,
            (display_name, telegram_id),
        )

    conn.commit()

    cur.execute(
        "SELECT id, telegram_id, display_name FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    row = cur.fetchone()
    conn.close()

    return dict(row) if row else {}


def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, telegram_id, display_name FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None