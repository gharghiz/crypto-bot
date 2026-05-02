"""
web.py - Flask web server
يعرض الأخبار المنشورة في البوت على موقع إلكتروني
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "cryptobot.db")

def get_news(page=1, per_page=20, search=None):
    offset = (page - 1) * per_page
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if search:
        rows = conn.execute(
            """SELECT * FROM posted_news
               WHERE title LIKE ?
               ORDER BY posted_at DESC
               LIMIT ? OFFSET ?""",
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
        total = conn.execute("SELECT COUNT(*) FROM posted_news").fetchone()[0]

    conn.close()
    return [dict(r) for r in rows], total

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    stats = {
        "total":   conn.execute("SELECT COUNT(*) FROM posted_news").fetchone()[0],
        "today":   conn.execute("SELECT COUNT(*) FROM posted_news WHERE posted_at >= date('now')").fetchone()[0],
        "sources": conn.execute("SELECT source, COUNT(*) as c FROM posted_news GROUP BY source ORDER BY c DESC").fetchall(),
    }
    conn.close()
    stats["sources"] = [{"name": r[0], "count": r[1]} for r in stats["sources"]]
    return stats

@app.route("/")
def index():
    page   = int(request.args.get("page", 1))
    search = request.args.get("q", "").strip()
    news, total = get_news(page=page, search=search or None)
    stats  = get_stats()
    pages  = (total + 19) // 20
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
