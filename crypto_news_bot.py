"""
Crypto & Trading News Bot - RSS Version
مهيأ للنشر على Railway.app
"""

import sys
import traceback

print("🚀 البوت بدا يشتغل...", flush=True)

try:
    import feedparser
    print("✅ feedparser OK", flush=True)
    import tweepy
    print("✅ tweepy OK", flush=True)
    import time
    import json
    import os
    from datetime import datetime
    print("✅ جميع المكتبات محملة", flush=True)
except Exception as e:
    print(f"❌ خطأ في تحميل المكتبات: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

# ============================================================
# ⚙️ الإعدادات
# ============================================================

TWITTER_API_KEY       = os.environ.get("TWITTER_API_KEY")
TWITTER_API_SECRET    = os.environ.get("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN  = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN  = os.environ.get("TWITTER_BEARER_TOKEN")
INTERVAL_MINUTES      = int(os.environ.get("INTERVAL_MINUTES", "30"))

POSTED_FILE = "posted_news.json"

# ============================================================
# ✅ التحقق من المفاتيح
# ============================================================

def check_env():
    required = {
        "TWITTER_API_KEY": TWITTER_API_KEY,
        "TWITTER_API_SECRET": TWITTER_API_SECRET,
        "TWITTER_ACCESS_TOKEN": TWITTER_ACCESS_TOKEN,
        "TWITTER_ACCESS_SECRET": TWITTER_ACCESS_SECRET,
        "TWITTER_BEARER_TOKEN": TWITTER_BEARER_TOKEN,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"❌ ناقصين هاد المفاتيح:\n" + "\n".join(missing), flush=True)
        sys.exit(1)
    print("✅ جميع المفاتيح موجودة", flush=True)

# ============================================================
# 📡 مصادر RSS
# ============================================================

RSS_FEEDS = [
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss"},
    {"name": "CoinDesk",      "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "Decrypt",       "url": "https://decrypt.co/feed"},
]

IMPORTANT_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "bnb", "solana", "sol",
    "xrp", "ripple", "cardano", "ada", "dogecoin", "doge",
    "etf", "sec", "halving", "hack", "hacked", "exploit",
    "ban", "banned", "regulation", "legal", "lawsuit",
    "crash", "dump", "pump", "surge", "rally", "bull", "bear",
    "all-time high", "ath", "record", "billion", "trillion",
    "binance", "coinbase", "blackrock", "fed", "federal reserve",
    "tether", "usdt", "stablecoin", "defi", "nft",
    "trading", "price", "market", "exchange", "liquidation",
    "futures", "options", "whale", "institutional",
]

# ============================================================
# 🔍 فلترة الأخبار
# ============================================================

def is_important(title):
    title_lower = title.lower()
    for keyword in IMPORTANT_KEYWORDS:
        if keyword.lower() in title_lower:
            return True
    return False

# ============================================================
# 📰 جلب الأخبار
# ============================================================

def get_news_from_rss():
    all_news = []
    for feed in RSS_FEEDS:
        try:
            print(f"📡 جاري جلب الأخبار من {feed['name']}...", flush=True)
            parsed = feedparser.parse(feed["url"])
            for entry in parsed.entries[:20]:
                all_news.append({
                    "id":     entry.get("id", entry.get("link", "")),
                    "title":  entry.get("title", ""),
                    "url":    entry.get("link", ""),
                    "source": feed["name"]
                })
        except Exception as e:
            print(f"❌ خطأ في {feed['name']}: {e}", flush=True)
    print(f"📊 جلبنا {len(all_news)} خبر", flush=True)
    return all_news

# ============================================================
# 💾 تتبع المنشور
# ============================================================

def load_posted():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted(posted_ids):
    with open(POSTED_FILE, "w") as f:
        json.dump(list(posted_ids)[-500:], f)

# ============================================================
# 🐦 النشر في تويتر
# ============================================================

def post_to_twitter(text):
    try:
        client = tweepy.Client(
            bearer_token=TWITTER_BEARER_TOKEN,
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        client.create_tweet(text=text)
        print("✅ تم النشر في تويتر", flush=True)
        return True
    except Exception as e:
        print(f"❌ خطأ في تويتر: {e}", flush=True)
        traceback.print_exc()
        return False

# ============================================================
# ✍️ تنسيق التويت
# ============================================================

def format_tweet(news_item):
    title    = news_item.get("title", "")
    url      = news_item.get("url", "")
    source   = news_item.get("source", "")
    hashtags = "#Crypto #Trading #Bitcoin #BTC"
    tweet    = f"📰 {title}\n\n🔗 {url}\n\n📌 {source}\n{hashtags}"
    if len(tweet) > 280:
        max_title = 280 - len(url) - len(source) - len(hashtags) - 20
        title = title[:max_title] + "..."
        tweet = f"📰 {title}\n\n🔗 {url}\n\n📌 {source}\n{hashtags}"
    return tweet

# ============================================================
# 🚀 الدورة الرئيسية
# ============================================================

def run_once():
    print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] جاري البحث...", flush=True)
    posted_ids    = load_posted()
    all_news      = get_news_from_rss()
    if not all_news:
        print("⚠️ ما لقيناش أخبار", flush=True)
        return
    important_news = [n for n in all_news if is_important(n["title"])]
    print(f"🎯 {len(important_news)} خبر مهم", flush=True)
    new_count = 0
    for item in important_news[:5]:
        news_id = item["id"]
        if news_id in posted_ids:
            continue
        tweet = format_tweet(item)
        post_to_twitter(tweet)
        posted_ids.add(news_id)
        new_count += 1
        time.sleep(10)
    save_posted(posted_ids)
    print(f"✅ تم نشر {new_count} خبر جديد", flush=True)

def main():
    check_env()
    print(f"🤖 البوت شغال! سينشر كل {INTERVAL_MINUTES} دقيقة\n", flush=True)
    while True:
        try:
            run_once()
        except Exception as e:
            print(f"❌ خطأ غير متوقع: {e}", flush=True)
            traceback.print_exc()
        print(f"😴 ينتظر {INTERVAL_MINUTES} دقيقة...", flush=True)
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ خطأ فادح: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)
