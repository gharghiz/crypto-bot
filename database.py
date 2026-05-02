"""
database.py - SQLite للحفاظ على الأخبار المنشورة
"""

import sqlite3
import os
from utils import logger, now_utc

DB_PATH = os.environ.get("DB_PATH", "cryptobot.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posted_news (
                id        TEXT PRIMARY KEY,
                title     TEXT,
                source    TEXT,
                posted_at TEXT
            )
        """)
        conn.commit()
    logger.info("✅ قاعدة البيانات جاهزة")

def is_posted(news_id: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM posted_news WHERE id = ?", (news_id,)
        ).fetchone()
    return row is not None

def mark_posted(news_id: str, title: str, source: str):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO posted_news (id, title, source, posted_at) VALUES (?, ?, ?, ?)",
            (news_id, title, source, now_utc().isoformat())
        )
        conn.commit()

def get_recent_titles(limit: int = 100) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT title FROM posted_news ORDER BY posted_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [r["title"] for r in rows]

def cleanup_old(days: int = 30):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM posted_news WHERE posted_at < datetime('now', ?)",
            (f'-{days} days',)
        )
        conn.commit()
