"""
database.py - PostgreSQL + SQLite fallback
مستقل بدون dependency على utils
"""

import os
import logging
import sqlite3
from datetime import datetime, timezone

# Logger مستقل
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("database")

def now_utc():
    return datetime.now(timezone.utc)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
DB_PATH      = os.environ.get("DB_PATH", "cryptobot.db")

# ============================================================
# تحديد نوع قاعدة البيانات
# ============================================================

USE_POSTGRES = bool(DATABASE_URL and "postgres" in DATABASE_URL)

if USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
        logger.info("✅ PostgreSQL mode")
    except ImportError:
        logger.warning("⚠️ psycopg2 غير موجود — نستعمل SQLite")
        USE_POSTGRES = False
else:
    logger.info("✅ SQLite mode")

# ============================================================
# Connections
# ============================================================

def get_pg_conn():
    url = DATABASE_URL
    # Railway كتعطي postgres:// — psycopg2 محتاج postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url)

def get_sqlite_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================
# Init
# ============================================================

def init_db():
    try:
        if USE_POSTGRES:
            with get_pg_conn() as conn:
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
            with get_sqlite_conn() as conn:
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
    except Exception as e:
        logger.error(f"❌ init_db error: {e}")

# ============================================================
# is_posted
# ============================================================

def is_posted(news_id: str) -> bool:
    try:
        if USE_POSTGRES:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM posted_news WHERE id = %s", (news_id,))
                    return cur.fetchone() is not None
        else:
            with get_sqlite_conn() as conn:
                return conn.execute(
                    "SELECT 1 FROM posted_news WHERE id = ?", (news_id,)
                ).fetchone() is not None
    except Exception as e:
        logger.error(f"❌ is_posted error: {e}")
        return False

# ============================================================
# mark_posted
# ============================================================

def mark_posted(news_id: str, title: str, source: str):
    posted_at = now_utc().isoformat()
    try:
        if USE_POSTGRES:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO posted_news (id, title, source, posted_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (news_id, title, source, posted_at))
                conn.commit()
        else:
            with get_sqlite_conn() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO posted_news (id, title, source, posted_at) VALUES (?, ?, ?, ?)",
                    (news_id, title, source, posted_at)
                )
                conn.commit()
    except Exception as e:
        logger.error(f"❌ mark_posted error: {e}")

# ============================================================
# get_recent_titles
# ============================================================

def get_recent_titles(limit: int = 100) -> list:
    try:
        if USE_POSTGRES:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT title FROM posted_news ORDER BY posted_at DESC LIMIT %s", (limit,)
                    )
                    return [r[0] for r in cur.fetchall()]
        else:
            with get_sqlite_conn() as conn:
                rows = conn.execute(
                    "SELECT title FROM posted_news ORDER BY posted_at DESC LIMIT ?", (limit,)
                ).fetchall()
                return [r["title"] for r in rows]
    except Exception as e:
        logger.error(f"❌ get_recent_titles error: {e}")
        return []

# ============================================================
# get_news (للموقع)
# ============================================================

def get_news(page: int = 1, per_page: int = 20, search: str = None):
    offset = (page - 1) * per_page
    try:
        if USE_POSTGRES:
            with get_pg_conn() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    if search:
                        cur.execute(
                            "SELECT * FROM posted_news WHERE title ILIKE %s ORDER BY posted_at DESC LIMIT %s OFFSET %s",
                            (f"%{search}%", per_page, offset)
                        )
                        rows = cur.fetchall()
                        cur.execute("SELECT COUNT(*) as count FROM posted_news WHERE title ILIKE %s", (f"%{search}%",))
                    else:
                        cur.execute(
                            "SELECT * FROM posted_news ORDER BY posted_at DESC LIMIT %s OFFSET %s",
                            (per_page, offset)
                        )
                        rows = cur.fetchall()
                        cur.execute("SELECT COUNT(*) as count FROM posted_news")
                    total = cur.fetchone()["count"]
            return [dict(r) for r in rows], total
        else:
            with get_sqlite_conn() as conn:
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
    except Exception as e:
        logger.error(f"❌ get_news error: {e}")
        return [], 0

# ============================================================
# get_stats (للموقع)
# ============================================================

def get_stats():
    try:
        if USE_POSTGRES:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM posted_news")
                    total = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM posted_news WHERE posted_at::date = CURRENT_DATE")
                    today = cur.fetchone()[0]
                    cur.execute("SELECT source, COUNT(*) as c FROM posted_news GROUP BY source ORDER BY c DESC")
                    sources = [{"name": r[0], "count": r[1]} for r in cur.fetchall()]
        else:
            with get_sqlite_conn() as conn:
                total   = conn.execute("SELECT COUNT(*) FROM posted_news").fetchone()[0]
                today   = conn.execute("SELECT COUNT(*) FROM posted_news WHERE posted_at >= date('now')").fetchone()[0]
                sources = [{"name": r[0], "count": r[1]} for r in conn.execute(
                    "SELECT source, COUNT(*) as c FROM posted_news GROUP BY source ORDER BY c DESC"
                ).fetchall()]
        return {"total": total, "today": today, "sources": sources}
    except Exception as e:
        logger.error(f"❌ get_stats error: {e}")
        return {"total": 0, "today": 0, "sources": []}

# ============================================================
# cleanup_old
# ============================================================

def cleanup_old(days: int = 30):
    try:
        if USE_POSTGRES:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM posted_news WHERE posted_at::timestamp < NOW() - INTERVAL '%s days'" % days
                    )
                conn.commit()
        else:
            with get_sqlite_conn() as conn:
                conn.execute(
                    "DELETE FROM posted_news WHERE posted_at < datetime('now', ?)",
                    (f'-{days} days',)
                )
                conn.commit()
    except Exception as e:
        logger.error(f"❌ cleanup_old error: {e}")
