"""
web.py - Flask web server
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "cryptobot.db")

def init_db():
    """إنشاء الجدول إيلا ما كانش موجود"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS posted_news (
                    id        TEXT PRIMARY KEY,
                    title     TEXT,
                    source    TEXT,
                    posted_at TEXT
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"DB init error: {e}")

def get_news(page=1, per_page=20, search=None):
    try:
        offset = (page - 1) * per_page
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if search:
                rows = conn.execute(
                    "SELECT * FROM posted_news WHERE title LIKE ? ORDER BY posted_at DESC LIMIT ? OFFSET ?",
                    (f"%{search}%", per_page, offset)
                ).fetchall()
                total = conn.execute(
                    "SELECT COUNT(*) FROM posted_news WHERE title LIKE ?",
                    (f"%{search}%",)
                ).fetchone()[0]
            else:
                rows = conn.execute(
                    "SELECT * FROM posted_news ORDER BY posted_at DESC LIMIT ? OFFSET ?",
                    (per_page, offset)
                ).fetchall()
                total = conn.execute(
                    "SELECT COUNT(*) FROM posted_news"
                ).fetchone()[0]
        return [dict(r) for r in rows], total
    except Exception as e:
        print(f"get_news error: {e}")
        return [], 0

def get_stats():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            total  = conn.execute("SELECT COUNT(*) FROM posted_news").fetchone()[0]
            today  = conn.execute("SELECT COUNT(*) FROM posted_news WHERE posted_at >= date('now')").fetchone()[0]
            sources = conn.execute(
                "SELECT source, COUNT(*) as c FROM posted_news GROUP BY source ORDER BY c DESC"
            ).fetchall()
        return {
            "total":   total,
            "today":   today,
            "sources": [{"name": r[0], "count": r[1]} for r in sources]
        }
    except Exception as e:
        print(f"get_stats error: {e}")
        return {"total": 0, "today": 0, "sources": []}

@app.route("/")
def index():
    page   = int(request.args.get("page", 1))
    search = request.args.get("q", "").strip()
    news, total = get_news(page=page, search=search or None)
    stats  = get_stats()
    pages  = max(1, (total + 19) // 20)
    return render_template("index.html",
        news=news, stats=stats,
        page=page, pages=pages,
        total=total, search=search
    )

@app.route("/api/news")
def api_news():
    page   = int(request.args.get("page", 1))
    search = request.args.get("q", "").strip()
    news, total = get_news(page=page, search=search or None)
    return jsonify({"news": news, "total": total})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# إنشاء DB عند البداية
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
