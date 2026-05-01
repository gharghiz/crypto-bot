"""
Crypto & Trading News Bot - Enhanced Version
✅ سعر العملة مع كل خبر
✅ تحليل المشاعر
✅ أوقات النشر الذكية
✅ تنبيهات عاجلة
"""

import sys
import traceback

print("🚀 البوت بدا يشتغل...", flush=True)

try:
    import feedparser
    import requests
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

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")
INTERVAL_MINUTES   = int(os.environ.get("INTERVAL_MINUTES", "30"))

POSTED_FILE = "posted_news.json"

# ============================================================
# ✅ التحقق من المفاتيح
# ============================================================

def check_env():
    required = {
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID":   TELEGRAM_CHAT_ID,
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

# ============================================================
# 🎯 الكلمات المفتاحية
# ============================================================

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

# كلمات التنبيه العاجل
URGENT_KEYWORDS = [
    "hack", "hacked", "exploit", "crash", "ban", "banned",
    "breaking", "urgent", "alert", "emergency", "collapse",
    "sec", "lawsuit", "arrested", "scam", "rug pull"
]

# كلمات إيجابية وسلبية للمشاعر
POSITIVE_WORDS = [
    "surge", "rally", "pump", "bull", "record", "high", "gain",
    "approved", "launch", "partnership", "adoption", "growth",
    "profit", "rises", "jumps", "soars", "breakout", "ath"
]

NEGATIVE_WORDS = [
    "crash", "dump", "bear", "ban", "hack", "fall", "drop",
    "loss", "decline", "lawsuit", "warning", "risk", "fear",
    "sell", "plunge", "tumbles", "falls", "exploit", "scam"
]

# العملات وكودها في CoinGecko
COIN_MAP = {
    "bitcoin": "bitcoin",   "btc": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum",
    "bnb": "binancecoin",
    "solana": "solana",     "sol": "solana",
    "xrp": "ripple",        "ripple": "ripple",
    "cardano": "cardano",   "ada": "cardano",
    "dogecoin": "dogecoin", "doge": "dogecoin",
    "tether": "tether",     "usdt": "tether",
}

# ============================================================
# 📊 جلب سعر العملة من CoinGecko (مجاني)
# ============================================================

def get_coin_price(title):
    title_lower = title.lower()
    coin_id = None

    for keyword, cid in COIN_MAP.items():
        if keyword in title_lower:
            coin_id = cid
            break

    if not coin_id:
        return None

    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if coin_id in data:
            price  = data[coin_id]["usd"]
            change = data[coin_id].get("usd_24h_change", 0)
            change = round(change, 2)

            # تنسيق السعر
            if price >= 1:
                price_str = f"${price:,.2f}"
            else:
                price_str = f"${price:.6f}"

            arrow = "📈" if change >= 0 else "📉"
            sign  = "+" if change >= 0 else ""
            return f"{arrow} {price_str} ({sign}{change}%)"
    except Exception as e:
        print(f"⚠️ ما قدرناش نجيب السعر: {e}", flush=True)

    return None

# ============================================================
# 😊 تحليل المشاعر
# ============================================================

def analyze_sentiment(title):
    title_lower = title.lower()
    pos_score = sum(1 for w in POSITIVE_WORDS if w in title_lower)
    neg_score = sum(1 for w in NEGATIVE_WORDS if w in title_lower)

    if pos_score > neg_score:
        return "🟢"  # إيجابي
    elif neg_score > pos_score:
        return "🔴"  # سلبي
    else:
        return "🟡"  # محايد

# ============================================================
# ⚡ تحقق من الخبر العاجل
# ============================================================

def is_urgent(title):
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in URGENT_KEYWORDS)

# ============================================================
# ⏰ أوقات النشر الذكية
# ============================================================

def is_peak_time():
    # أوقات الذروة: 7-10 صباح و 6-11 مساء (توقيت المغرب GMT+1)
    hour = datetime.now().hour
    return (7 <= hour <= 10) or (18 <= hour <= 23)

# ============================================================
# 🔍 فلترة الأخبار
# ============================================================

def is_important(title):
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in IMPORTANT_KEYWORDS)

# ============================================================
# 📰 جلب الأخبار من RSS
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
# 📨 النشر في تيليغرام
# ============================================================

def post_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":                  TELEGRAM_CHAT_ID,
        "text":                     text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ تم النشر في تيليغرام", flush=True)
            return True
        else:
            print(f"❌ خطأ في تيليغرام: {response.text}", flush=True)
            return False
    except Exception as e:
        print(f"❌ خطأ في تيليغرام: {e}", flush=True)
        return False

# ============================================================
# ✍️ تنسيق الرسالة
# ============================================================

def format_message(news_item, urgent=False):
    title     = news_item.get("title", "")
    source    = news_item.get("source", "")
    sentiment = analyze_sentiment(title)
    price     = get_coin_price(title)
    hashtags  = "#Crypto #Trading #Bitcoin #BTC"

    # هيدر الخبر العاجل
    header = "⚡️ <b>خبر عاجل!</b>\n\n" if urgent else ""

    # بناء الرسالة
    message = f"{header}{sentiment} <b>{title}</b>\n\n"

    if price:
        message += f"💰 {price}\n\n"

    message += f"📌 {source}\n{hashtags}"

    return message

# ============================================================
# 🚀 الدورة الرئيسية
# ============================================================

def run_once(force=False):
    # إيلا مو وقت ذروة ومو force (مو خبر عاجل) ما ننشروش
    if not force and not is_peak_time():
        print(f"⏳ مو وقت ذروة — ما غادي ننشروش دابا", flush=True)
        return

    print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] جاري البحث عن أخبار جديدة...", flush=True)

    posted_ids     = load_posted()
    all_news       = get_news_from_rss()

    if not all_news:
        print("⚠️ ما لقيناش أخبار", flush=True)
        return

    important_news = [n for n in all_news if is_important(n["title"])]
    print(f"🎯 {len(important_news)} خبر مهم من أصل {len(all_news)}", flush=True)

    new_count = 0
    for item in important_news:
        news_id = item["id"]
        if news_id in posted_ids:
            continue

        urgent  = is_urgent(item["title"])
        message = format_message(item, urgent=urgent)
        post_to_telegram(message)

        posted_ids.add(news_id)
        new_count += 1

        # أقصاه 5 في وقت الذروة، 1 للأخبار العاجلة
        if urgent:
            break
        if new_count >= 5:
            break

        time.sleep(5)

    save_posted(posted_ids)
    print(f"✅ تم نشر {new_count} خبر جديد", flush=True)

# ============================================================
# 🏁 البداية
# ============================================================

def main():
    check_env()
    print(f"🤖 البوت شغال! سيتحقق كل {INTERVAL_MINUTES} دقيقة\n", flush=True)

    post_to_telegram(
        f"🚀 <b>البوت بدا يشتغل!</b>\n\n"
        f"⏱️ يتحقق كل {INTERVAL_MINUTES} دقيقة\n"
        f"⏰ ينشر في أوقات الذروة: 7-10 صباح و 6-11 مساء\n"
        f"⚡️ الأخبار العاجلة تنشر فوراً في أي وقت"
    )

    while True:
        try:
            # الأخبار العاجلة تنشر في أي وقت
            posted_ids = load_posted()
            all_news   = get_news_from_rss()
            urgent_news = [
                n for n in all_news
                if is_urgent(n["title"]) and str(n["id"]) not in posted_ids
            ]

            if urgent_news:
                print(f"⚡️ لقينا {len(urgent_news)} خبر عاجل!", flush=True)
                for item in urgent_news[:2]:
                    message = format_message(item, urgent=True)
                    post_to_telegram(message)
                    posted_ids.add(str(item["id"]))
                    time.sleep(3)
                save_posted(posted_ids)
            else:
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
