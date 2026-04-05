
#Later we will switch to postgresql
import sqlite3

def init_db():
    conn = sqlite3.connect("yves.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id TEXT PRIMARY KEY,
            level TEXT DEFAULT 'unknown'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def register_user(chat_id):
    conn = sqlite3.connect("yves.db")
    conn.execute(
        "INSERT OR IGNORE INTO users (chat_id) VALUES (?)",
        (chat_id,)
    )
    conn.commit()
    conn.close()

def get_level(chat_id):
    conn = sqlite3.connect("yves.db")
    row = conn.execute(
        "SELECT level FROM users WHERE chat_id=?",
        (chat_id,)
    ).fetchone()
    conn.close()
    return row[0] if row else "unknown"

def update_level(chat_id, level):
    conn = sqlite3.connect("yves.db")
    conn.execute(
        "UPDATE users SET level=? WHERE chat_id=?",
        (level, chat_id)
    )
    conn.commit()
    conn.close()

def get_history(chat_id):
    conn = sqlite3.connect("yves.db")
    rows = conn.execute(
        #This is the context window ( RN WE ARE USING 20 MESSAGES. )
        "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT 20",
        (chat_id,)
    ).fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def save_message(chat_id, role, content):
    conn = sqlite3.connect("yves.db")
    conn.execute(
        "INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)",
        (chat_id, role, content)
    )
    conn.commit()
    conn.close()