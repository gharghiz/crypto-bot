"""
web.py - Flask web server
RSS Feed + Cache + SEO + Admin
"""

from flask import Flask, render_template, jsonify, request, Response
import os
import time
from database import init_db, get_news, get_news_by_id, get_stats

app = Flask(__name__)
init_db()

SITE_URL     = os.environ.get("SITE_URL", "https://rare-spontaneity-production-1b51.up.railway.app")
SITE_NAME    = "CryptositNews"
GSC_META_TAG = os.environ.get("GSC_META_TAG", "")
ADMIN_KEY    = os.environ.get("ADMIN_KEY", "cryptosit2025")

# ============================================================
# Page cache
# ============================================================

_page_cache = {}
PAGE_CACHE_TTL = 120

def page_cache_get(key):
    if key in _page_cache:
        data, ts = _page_cache[key]
        if time.time() - ts < PAGE_CACHE_TTL:
            return data
        del _page_cache[key]
    return None

def page_cache_set(key, data):
    _page_cache[key] = (data, time.time())

# ============================================================
# Category mapping
# ============================================================

def get_category(title: str) -> str:
    t = title.lower()
    if any(k in t for k in ["breaking", "urgent", "hack", "hacked", "exploit", "crash", "ban", "banned", "scam"]):
        return "breaking"
    if "bitcoin" in t or "btc" in t:
        return "bitcoin"
    if "ethereum" in t or " eth " in t or "ether " in t:
        return "ethereum"
    if any(k in t for k in ["defi", "uniswap", "aave", "compound", "protocol", "staking", "liquidity"]):
        return "defi"
    if any(k in t for k in ["nft", "non-fungible", "opensea", "metaverse"]):
        return "nft"
    if any(k in t for k in ["sec", "regulation", "legal", "congress", "government", "legislation", "lawsuit"]):
        return "regulation"
    if any(k in t for k in ["solana", "cardano", "ripple", "dogecoin", "bnb", "binance", "xrp", "doge", "ada", " sol "]):
        return "altcoin"
    return "market"

def filter_by_category(news_list: list, category: str) -> list:
    if not category or category == "all":
        return news_list
    return [n for n in news_list if get_category(n["title"]) == category]

# ============================================================
# Main page
# ============================================================

@app.route("/")
def index():
    page       = int(request.args.get("page", 1))
    search     = request.args.get("q", "").strip()
    active_tab = request.args.get("tab", "").strip()

    cache_key = f"page_{page}_{search}_{active_tab}"
    cached = page_cache_get(cache_key)
    if cached and not search:
        return cached

    if active_tab and active_tab != "all":
        all_news, _ = get_news(page=1, per_page=500, search=search or None)
        filtered    = filter_by_category(all_news, active_tab)
        per_page    = 20
        total       = len(filtered)
        start       = (page - 1) * per_page
        news        = filtered[start:start + per_page]
    else:
        news, total = get_news(page=1, per_page=200, search=search or None)

    stats = get_stats()
    pages = max(1, (total + 19) // 20)

    rendered = render_template("index.html",
        news=news, stats=stats,
        page=page, pages=pages,
        total=total, search=search,
        active_tab=active_tab,
        gsc_meta=GSC_META_TAG,
    )

    if not search:
        page_cache_set(cache_key, rendered)

    return rendered

# ============================================================
# Article page
# ============================================================

@app.route("/news/<path:news_id>")
def news_page(news_id):
    item = get_news_by_id(news_id)
    if not item:
        return "Not Found", 404
    return render_template("article.html", item=item, site_url=SITE_URL)

# ============================================================
# RSS Feed
# ============================================================

@app.route("/feed")
@app.route("/feed.xml")
@app.route("/rss")
@app.route("/rss.xml")
def rss_feed():
    cached = page_cache_get("rss_feed")
    if cached:
        return Response(cached, mimetype="application/rss+xml")

    news, _ = get_news(page=1, per_page=50)
    items   = []

    for item in news:
        title    = item["title"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        link     = f"{SITE_URL}/news/{item['id']}"
        pub_date = item["posted_at"][:19].replace("T", " ") + " UTC"
        source   = item["source"].replace("&","&amp;")
        desc     = (item.get("summary") or item["title"]).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

        items.append(f"""  <item>
    <title>{title}</title>
    <link>{link}</link>
    <description>{desc}</description>
    <pubDate>{pub_date}</pubDate>
    <source>{source}</source>
    <guid isPermaLink="true">{link}</guid>
  </item>""")

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{SITE_NAME} — Live Crypto News</title>
  <link>{SITE_URL}</link>
  <description>Real-time crypto and trading news</description>
  <language>en-us</language>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
{"".join(items)}
</channel>
</rss>"""

    page_cache_set("rss_feed", rss)
    return Response(rss, mimetype="application/rss+xml")

# ============================================================
# API
# ============================================================

@app.route("/api/news")
def api_news():
    page   = int(request.args.get("page", 1))
    search = request.args.get("q", "").strip()
    cat    = request.args.get("cat", "").strip()
    news, total = get_news(page=page, search=search or None)
    if cat:
        news = filter_by_category(news, cat)
    return jsonify({"news": news, "total": total})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# ============================================================
# Admin — حذف DB
# ============================================================

@app.route("/admin/clear")
def admin_clear():
    """حذف telegram_log فقط — الموقع ما يتأثرش"""
    key = request.args.get("key", "")
    if key != ADMIN_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        from database import get_pg_conn, get_sqlite_conn, USE_POSTGRES, cache_clear

        if USE_POSTGRES:
            conn = get_pg_conn(); cur = conn.cursor()
            # إنشاء الجدول إيلا ما كانش موجود
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telegram_log (
                    id TEXT PRIMARY KEY, posted_at TEXT
                )
            """)
            cur.execute("DELETE FROM telegram_log")
            deleted = cur.rowcount
            conn.commit(); cur.close(); conn.close()
        else:
            with get_sqlite_conn() as conn:
                conn.execute("""CREATE TABLE IF NOT EXISTS telegram_log (id TEXT PRIMARY KEY, posted_at TEXT)""")
                cur = conn.execute("DELETE FROM telegram_log")
                deleted = cur.rowcount
                conn.commit()

        cache_clear()
        _page_cache.clear()
        return jsonify({"status": "✅ telegram_log cleared", "deleted": deleted, "note": "posted_news (website) untouched"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/init")
def admin_init():
    """إنشاء جميع الجداول — شغلو مرة واحدة بعد deploy"""
    key = request.args.get("key", "")
    if key != ADMIN_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        from database import init_db
        init_db()
        return jsonify({"status": "✅ DB initialized"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================
# SEO
# ============================================================

@app.route("/sitemap.xml")
def sitemap():
    cached = page_cache_get("sitemap")
    if cached:
        return Response(cached, mimetype="application/xml")

    news, _ = get_news(page=1, per_page=1000)
    urls = [f"<url><loc>{SITE_URL}/</loc><changefreq>hourly</changefreq><priority>1.0</priority></url>"]

    for cat in ["bitcoin","ethereum","defi","nft","regulation","market","altcoin","breaking"]:
        urls.append(f"<url><loc>{SITE_URL}/?tab={cat}</loc><changefreq>hourly</changefreq><priority>0.9</priority></url>")

    for item in news:
        nid = item["id"].replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        urls.append(f"<url><loc>{SITE_URL}/news/{nid}</loc><lastmod>{item['posted_at'][:10]}</lastmod><changefreq>never</changefreq><priority>0.8</priority></url>")

    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{"".join(urls)}\n</urlset>'
    page_cache_set("sitemap", xml)
    return Response(xml, mimetype="application/xml")

@app.route("/robots.txt")
def robots():
    return Response(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml", mimetype="text/plain")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
