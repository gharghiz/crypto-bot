"""
database.py - PostgreSQL + SQLite fallback
مع columns للـ AI
"""

import os
import logging
import sqlite3
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("database")

def now_utc():
    return datetime.now(timezone.utc)

DATABASE_URL = os.environ.get("DATABASE_URL", "")
DB_PATH      = os.environ.get("DB_PATH", "cryptobot.db")

USE_POSTGRES = bool(DATABASE_URL and "postgres" in DATABASE_URL)

if USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
        logger.info("✅ PostgreSQL mode")
    except ImportError:
        logger.warning("⚠️ psycopg2 غير موجود — SQLite")
        USE_POSTGRES = False
else:
    logger.info("✅ SQLite mode")

# ============================================================
# Connection
# ============================================================

def get_pg_conn():
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if "sslmode" not in url:
        url += "?sslmode=require" if "?" not in url else "&sslmode=require"
    return psycopg2.connect(url)

def get_sqlite_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================
# Init — مع AI columns
# ============================================================

def init_db():
    try:
        if USE_POSTGRES:
            conn = get_pg_conn()
            cur  = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS posted_news (
                    id        TEXT PRIMARY KEY,
                    title     TEXT,
                    source    TEXT,
                    posted_at TEXT,
                    summary   TEXT,
                    sentiment TEXT,
                    reason    TEXT
                )
            """)
            # إيلا الجدول قديم بلا AI columns نزيدهم
            for col in ["summary", "sentiment", "reason"]:
                try:
                    cur.execute(f"ALTER TABLE posted_news ADD COLUMN {col} TEXT")
                except Exception:
                    pass
            conn.commit()
            cur.close(); conn.close()
        else:
            with get_sqlite_conn() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS posted_news (
                        id TEXT PRIMARY KEY, title TEXT, source TEXT, posted_at TEXT,
                        summary TEXT, sentiment TEXT, reason TEXT
                    )
                """)
                for col in ["summary", "sentiment", "reason"]:
                    try:
                        conn.execute(f"ALTER TABLE posted_news ADD COLUMN {col} TEXT")
                    except Exception:
                        pass
                conn.commit()
        logger.info("✅ DB جاهزة")
    except Exception as e:
        logger.error(f"❌ init_db: {e}")

# ============================================================
# is_posted
# ============================================================

def is_posted(news_id: str) -> bool:
    try:
        if USE_POSTGRES:
            conn = get_pg_conn()
            cur  = conn.cursor()
            cur.execute("SELECT 1 FROM posted_news WHERE id = %s", (news_id,))
            result = cur.fetchone() is not None
            cur.close(); conn.close()
            return result
        else:
            with get_sqlite_conn() as conn:
                return conn.execute(
                    "SELECT 1 FROM posted_news WHERE id = ?", (news_id,)
                ).fetchone() is not None
    except Exception as e:
        logger.error(f"❌ is_posted: {e}")
        return False

# ============================================================
# mark_posted — مع AI data
# ============================================================

def mark_posted(news_id: str, title: str, source: str,
                summary: str = "", sentiment: str = "", reason: str = ""):
    posted_at = now_utc().isoformat()
    try:
        if USE_POSTGRES:
            conn = get_pg_conn()
            cur  = conn.cursor()
            cur.execute("""
                INSERT INTO posted_news (id, title, source, posted_at, summary, sentiment, reason)
                VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
            """, (news_id, title, source, posted_at, summary, sentiment, reason))
            conn.commit(); cur.close(); conn.close()
        else:
            with get_sqlite_conn() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO posted_news
                    (id, title, source, posted_at, summary, sentiment, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (news_id, title, source, posted_at, summary, sentiment, reason))
                conn.commit()
    except Exception as e:
        logger.error(f"❌ mark_posted: {e}")

# ============================================================
# get_recent_titles
# ============================================================

def get_recent_titles(limit: int = 200) -> list:
    try:
        if USE_POSTGRES:
            conn = get_pg_conn()
            cur  = conn.cursor()
            cur.execute("SELECT title FROM posted_news ORDER BY posted_at DESC LIMIT %s", (limit,))
            rows = [r[0] for r in cur.fetchall()]
            cur.close(); conn.close()
            return rows
        else:
            with get_sqlite_conn() as conn:
                return [r["title"] for r in conn.execute(
                    "SELECT title FROM posted_news ORDER BY posted_at DESC LIMIT ?", (limit,)
                ).fetchall()]
    except Exception as e:
        logger.error(f"❌ get_recent_titles: {e}")
        return []

# ============================================================
# get_news_by_id — query مباشر للـ SEO page
# ============================================================

def get_news_by_id(news_id: str):
    try:
        if USE_POSTGRES:
            conn = get_pg_conn()
            cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM posted_news WHERE id = %s", (news_id,))
            row = cur.fetchone()
            cur.close(); conn.close()
            return dict(row) if row else None
        else:
            with get_sqlite_conn() as conn:
                row = conn.execute(
                    "SELECT * FROM posted_news WHERE id = ?", (news_id,)
                ).fetchone()
                return dict(row) if row else None
    except Exception as e:
        logger.error(f"❌ get_news_by_id: {e}")
        return None

# ============================================================
# get_news
# ============================================================

def get_news(page: int = 1, per_page: int = 20, search: str = None):
    offset = (page - 1) * per_page
    try:
        if USE_POSTGRES:
            conn = get_pg_conn()
            cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
            cur.close(); conn.close()
            return [dict(r) for r in rows], total
        else:
            with get_sqlite_conn() as conn:
                if search:
                    rows  = conn.execute("SELECT * FROM posted_news WHERE title LIKE ? ORDER BY posted_at DESC LIMIT ? OFFSET ?", (f"%{search}%", per_page, offset)).fetchall()
                    total = conn.execute("SELECT COUNT(*) FROM posted_news WHERE title LIKE ?", (f"%{search}%",)).fetchone()[0]
                else:
                    rows  = conn.execute("SELECT * FROM posted_news ORDER BY posted_at DESC LIMIT ? OFFSET ?", (per_page, offset)).fetchall()
                    total = conn.execute("SELECT COUNT(*) FROM posted_news").fetchone()[0]
                return [dict(r) for r in rows], total
    except Exception as e:
        logger.error(f"❌ get_news: {e}")
        return [], 0

# ============================================================
# get_stats
# ============================================================

def get_stats():
    try:
        if USE_POSTGRES:
            conn = get_pg_conn()
            cur  = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM posted_news")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM posted_news WHERE posted_at >= (NOW() - INTERVAL '24 hours')::text")
            today = cur.fetchone()[0]
            cur.execute("SELECT source, COUNT(*) as c FROM posted_news GROUP BY source ORDER BY c DESC")
            sources = [{"name": r[0], "count": r[1]} for r in cur.fetchall()]
            cur.close(); conn.close()
        else:
            with get_sqlite_conn() as conn:
                total   = conn.execute("SELECT COUNT(*) FROM posted_news").fetchone()[0]
                today   = conn.execute("SELECT COUNT(*) FROM posted_news WHERE posted_at >= date('now')").fetchone()[0]
                sources = [{"name": r[0], "count": r[1]} for r in conn.execute(
                    "SELECT source, COUNT(*) as c FROM posted_news GROUP BY source ORDER BY c DESC"
                ).fetchall()]
        return {"total": total, "today": today, "sources": sources}
    except Exception as e:
        logger.error(f"❌ get_stats: {e}")
        return {"total": 0, "today": 0, "sources": []}

# ============================================================
# cleanup_old
# ============================================================

def cleanup_old(days: int = 30):
    try:
        if USE_POSTGRES:
            conn = get_pg_conn()
            cur  = conn.cursor()
            cur.execute(f"DELETE FROM posted_news WHERE posted_at::timestamp < NOW() - INTERVAL '{days} days'")
            conn.commit(); cur.close(); conn.close()
        else:
            with get_sqlite_conn() as conn:
                conn.execute("DELETE FROM posted_news WHERE posted_at < datetime('now', ?)", (f'-{days} days',))
                conn.commit()
    except Exception as e:
        logger.error(f"❌ cleanup_old: {e}")
