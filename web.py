"""
web.py - Flask web server مع SEO
"""

from flask import Flask, render_template, jsonify, request
import os
from database import init_db, get_news, get_stats

app = Flask(__name__)
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

@app.route("/news/<path:news_id>")
def news_page(news_id):
    # نجيب الخبر من قاعدة البيانات
    news, _ = get_news(page=1, per_page=1000)
    item = next((n for n in news if n["id"] == news_id), None)
    if not item:
        return "Not Found", 404
    return render_template("article.html", item=item)

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
