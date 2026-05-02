"""
web.py - Flask web server مع SEO كامل
"""

from flask import Flask, render_template, jsonify, request, Response
import os
from database import init_db, get_news, get_news_by_id, get_stats

app = Flask(__name__)
init_db()

SITE_URL = os.environ.get("SITE_URL", "https://rare-spontaneity-production-1b51.up.railway.app")

# ============================================================
# Main page
# ============================================================

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

# ============================================================
# Article page — query مباشر بدون جلب 1000 خبر
# ============================================================

@app.route("/news/<path:news_id>")
def news_page(news_id):
    item = get_news_by_id(news_id)
    if not item:
        return "Not Found", 404
    return render_template("article.html", item=item, site_url=SITE_URL)

# ============================================================
# API
# ============================================================

@app.route("/api/news")
def api_news():
    page   = int(request.args.get("page", 1))
    search = request.args.get("q", "").strip()
    news, total = get_news(page=page, search=search or None)
    return jsonify({"news": news, "total": total})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# ============================================================
# SEO — sitemap.xml
# ============================================================

@app.route("/sitemap.xml")
def sitemap():
    news, total = get_news(page=1, per_page=1000)
    urls = [f"<url><loc>{SITE_URL}/</loc><changefreq>hourly</changefreq><priority>1.0</priority></url>"]
    for item in news:
        nid = item["id"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        urls.append(
            f"<url><loc>{SITE_URL}/news/{nid}</loc>"
            f"<lastmod>{item['posted_at'][:10]}</lastmod>"
            f"<changefreq>never</changefreq><priority>0.8</priority></url>"
        )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(urls)}
</urlset>"""
    return Response(xml, mimetype="application/xml")

# ============================================================
# SEO — robots.txt
# ============================================================

@app.route("/robots.txt")
def robots():
    content = f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml"""
    return Response(content, mimetype="text/plain")

# ============================================================
# Entry
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
