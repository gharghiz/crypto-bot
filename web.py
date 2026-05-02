"""
web.py - Flask web server
"""

from flask import Flask, render_template, jsonify, request
import os, sys

# نضيفو المسار باش يلقى database.py
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, get_news, get_stats

app = Flask(__name__)

# إنشاء الجدول عند البداية
init_db()

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
