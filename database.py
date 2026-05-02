"""
database.py - PostgreSQL + SQLite fallback
"""

import os
import sqlite3
from utils import logger, now_utc

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# ============================================================
# تحديد نوع قاعدة البيانات
# ============================================================

USE_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith("postgres"))

if USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
        logger.info("✅ PostgreSQL mode")
    except ImportError:
        logger.warning("⚠️ psycopg2 غير موجود — نستعمل SQLite")
        USE_POSTGRES = False

DB_PATH = os.environ.get("DB_PATH", "cryptobot.db")

# ============================================================
# Connections
# ============================================================

def get_pg_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def get_sqlite_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================
# Init
# ============================================================

def init_db():
    if USE_POSTGRES:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS posted_news (
                        id        TEXT PRIMARY KEY,
                        title     TEXT,
                        source    TEXT,
                        posted_at TEXT
                    )
                """)
            conn.commit()
    else:
        with get_sqlite_connection() as conn:
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

# ============================================================
# is_posted
# ============================================================

def is_posted(news_id: str) -> bool:
    if USE_POSTGRES:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM posted_news WHERE id = %s", (news_id,))
                return cur.fetchone() is not None
    else:
        with get_sqlite_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM posted_news WHERE id = ?", (news_id,)
            ).fetchone()
            return row is not None

# ============================================================
# mark_posted
# ============================================================

def mark_posted(news_id: str, title: str, source: str):
    posted_at = now_utc().isoformat()
    if USE_POSTGRES:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO posted_news (id, title, source, posted_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (news_id, title, source, posted_at))
            conn.commit()
    else:
        with get_sqlite_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO posted_news (id, title, source, posted_at) VALUES (?, ?, ?, ?)",
                (news_id, title, source, posted_at)
            )
            conn.commit()

# ============================================================
# get_recent_titles
# ============================================================

def get_recent_titles(limit: int = 100) -> list:
    if USE_POSTGRES:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT title FROM posted_news ORDER BY posted_at DESC LIMIT %s", (limit,)
                )
                return [r[0] for r in cur.fetchall()]
    else:
        with get_sqlite_connection() as conn:
            rows = conn.execute(
                "SELECT title FROM posted_news ORDER BY posted_at DESC LIMIT ?", (limit,)
            ).fetchall()
            return [r["title"] for r in rows]

# ============================================================
# get_news (للموقع)
# ============================================================

def get_news(page: int = 1, per_page: int = 20, search: str = None):
    offset = (page - 1) * per_page
    if USE_POSTGRES:
        with get_pg_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if search:
                    cur.execute(
                        "SELECT * FROM posted_news WHERE title ILIKE %s ORDER BY posted_at DESC LIMIT %s OFFSET %s",
                        (f"%{search}%", per_page, offset)
                    )
                    rows = cur.fetchall()
                    cur.execute("SELECT COUNT(*) FROM posted_news WHERE title ILIKE %s", (f"%{search}%",))
                else:
                    cur.execute(
                        "SELECT * FROM posted_news ORDER BY posted_at DESC LIMIT %s OFFSET %s",
                        (per_page, offset)
                    )
                    rows = cur.fetchall()
                    cur.execute("SELECT COUNT(*) FROM posted_news")
                total = cur.fetchone()["count"]
        return [dict(r) for r in rows], total
    else:
        with get_sqlite_connection() as conn:
            if search:
                rows = conn.execute(
                    "SELECT * FROM posted_news WHERE title LIKE ? ORDER BY posted_at DESC LIMIT ? OFFSET ?",
                    (f"%{search}%", per_page, offset)
                ).fetchall()
                total = conn.execute(
                    "SELECT COUNT(*) FROM posted_news WHERE title LIKE ?", (f"%{search}%",)
                ).fetchone()[0]
            else:
                rows = conn.execute(
                    "SELECT * FROM posted_news ORDER BY posted_at DESC LIMIT ? OFFSET ?",
                    (per_page, offset)
                ).fetchall()
                total = conn.execute("SELECT COUNT(*) FROM posted_news").fetchone()[0]
        return [dict(r) for r in rows], total

# ============================================================
# get_stats (للموقع)
# ============================================================

def get_stats():
    try:
        if USE_POSTGRES:
            with get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM posted_news")
                    total = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM posted_news WHERE posted_at >= CURRENT_DATE::text")
                    today = cur.fetchone()[0]
                    cur.execute("SELECT source, COUNT(*) as c FROM posted_news GROUP BY source ORDER BY c DESC")
                    sources = [{"name": r[0], "count": r[1]} for r in cur.fetchall()]
        else:
            with get_sqlite_connection() as conn:
                total   = conn.execute("SELECT COUNT(*) FROM posted_news").fetchone()[0]
                today   = conn.execute("SELECT COUNT(*) FROM posted_news WHERE posted_at >= date('now')").fetchone()[0]
                sources = [{"name": r[0], "count": r[1]} for r in conn.execute(
                    "SELECT source, COUNT(*) as c FROM posted_news GROUP BY source ORDER BY c DESC"
                ).fetchall()]
        return {"total": total, "today": today, "sources": sources}
    except Exception as e:
        logger.warning(f"⚠️ get_stats error: {e}")
        return {"total": 0, "today": 0, "sources": []}

# ============================================================
# cleanup_old
# ============================================================

def cleanup_old(days: int = 30):
    if USE_POSTGRES:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM posted_news WHERE posted_at < (NOW() - INTERVAL '%s days')::text",
                    (days,)
                )
            conn.commit()
    else:
        with get_sqlite_connection() as conn:
            conn.execute(
                "DELETE FROM posted_news WHERE posted_at < datetime('now', ?)",
                (f'-{days} days',)
            )
            conn.commit()
