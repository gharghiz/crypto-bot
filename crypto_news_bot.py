"""
Crypto & Trading News Bot
ينشر آخر أخبار التداول والعملات الرقمية في تويتر/X وتيليغرام
مهيأ للنشر على Railway.app
"""

import requests
import tweepy
import time
import json
import os
from datetime import datetime

# ============================================================
# ⚙️ الإعدادات - تتقرأ من Environment Variables في Railway
# ============================================================

TWITTER_API_KEY        = os.environ.get("TWITTER_API_KEY")
TWITTER_API_SECRET     = os.environ.get("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN   = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET  = os.environ.get("TWITTER_ACCESS_SECRET")
TWITTER_BEARER_TOKEN   = os.environ.get("TWITTER_BEARER_TOKEN")

TELEGRAM_BOT_TOKEN     = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID       = os.environ.get("TELEGRAM_CHAT_ID")

CRYPTOPANIC_API_KEY    = os.environ.get("CRYPTOPANIC_API_KEY")

INTERVAL_MINUTES       = int(os.environ.get("INTERVAL_MINUTES", "30"))

POSTED_FILE = "posted_news.json"

# ============================================================
# ✅ التحقق من المفاتيح عند الإقلاع
# ============================================================

def check_env():
    required = {
        "TWITTER_API_KEY": TWITTER_API_KEY,
        "TWITTER_API_SECRET": TWITTER_API_SECRET,
        "TWITTER_ACCESS_TOKEN": TWITTER_ACCESS_TOKEN,
        "TWITTER_ACCESS_SECRET": TWITTER_ACCESS_SECRET,
        "TWITTER_BEARER_TOKEN": TWITTER_BEARER_TOKEN,
        "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
        "CRYPTOPANIC_API_KEY": CRYPTOPANIC_API_KEY,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"❌ ناقصين هاد المفاتيح في Variables:\n" + "\n".join(missing))
        exit(1)
    print("✅ جميع المفاتيح موجودة")

# ============================================================
# 📰 جلب الأخبار من CryptoPanic
# ============================================================

def get_crypto_news():
    url = "https://cryptopanic.com/api/v1/posts/"
    params = {
        "auth_token": CRYPTOPANIC_API_KEY,
        "filter": "hot",
        "kind": "news",
        "public": "true"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"❌ خطأ في جلب الأخبار: {e}")
        send_error_to_telegram(f"❌ خطأ في جلب الأخبار: {e}")
        return []

# ============================================================
# 💾 تتبع الأخبار المنشورة
# ============================================================

def load_posted():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_posted(posted_ids):
    ids_list = list(posted_ids)[-500:]
    with open(POSTED_FILE, "w") as f:
        json.dump(ids_list, f)

# ============================================================
# 🐦 النشر في تويتر/X
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
        print("✅ تم النشر في تويتر")
        return True
    except Exception as e:
        print(f"❌ خطأ في تويتر: {e}")
        send_error_to_telegram(f"❌ خطأ في تويتر: {e}")
        return False

# ============================================================
# 📨 النشر في تيليغرام
# ============================================================

def post_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ تم النشر في تيليغرام")
            return True
        else:
            print(f"❌ خطأ في تيليغرام: {response.text}")
            return False
    except Exception as e:
        print(f"❌ خطأ في تيليغرام: {e}")
        return False

# ============================================================
# ⚠️ إرسال تنبيهات الأخطاء لتيليغرام
# ============================================================

def send_error_to_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"⚠️ <b>تنبيه البوت</b>\n\n{message}\n\n⏰ {datetime.now().strftime('%H:%M - %d/%m/%Y')}",
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload, timeout=10)
    except:
        pass

# ============================================================
# ✍️ تنسيق الرسالة
# ============================================================

def format_message(news_item, platform="twitter"):
    title = news_item.get("title", "")
    url   = news_item.get("url", "")
    hashtags = "#Crypto #Trading #Bitcoin #BTC"

    currencies = news_item.get("currencies", [])
    if currencies:
        for c in currencies[:2]:
            symbol = c.get("code", "")
            if symbol and f"#{symbol}" not in hashtags:
                hashtags += f" #{symbol}"

    if platform == "twitter":
        message = f"📰 {title}\n\n{url}\n\n{hashtags}"
        if len(message) > 280:
            max_title = 280 - len(url) - len(hashtags) - 10
            title = title[:max_title] + "..."
            message = f"📰 {title}\n\n{url}\n\n{hashtags}"
    else:
        message = (
            f"📰 <b>{title}</b>\n\n"
            f"🔗 <a href='{url}'>اقرأ المزيد</a>\n\n"
            f"{hashtags}\n\n"
            f"⏰ {datetime.now().strftime('%H:%M - %d/%m/%Y')}"
        )

    return message

# ============================================================
# 🚀 الدورة الرئيسية
# ============================================================

def run_once():
    print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] جاري البحث عن أخبار جديدة...")

    posted_ids = load_posted()
    news_list  = get_crypto_news()

    if not news_list:
        print("⚠️ ما لقيناش أخبار")
        return

    new_count = 0
    for item in news_list[:5]:
        news_id = str(item.get("id"))

        if news_id in posted_ids:
            continue

        tw_msg = format_message(item, platform="twitter")
        post_to_twitter(tw_msg)
        time.sleep(2)

        tg_msg = format_message(item, platform="telegram")
        post_to_telegram(tg_msg)

        posted_ids.add(news_id)
        new_count += 1
        time.sleep(5)

    save_posted(posted_ids)
    print(f"✅ تم نشر {new_count} خبر جديد")

def main():
    check_env()
    print("🤖 بوت أخبار الكريبتو شغال على Railway!")
    print(f"⏱️ سينشر كل {INTERVAL_MINUTES} دقيقة\n")

    # رسالة ترحيبية على تيليغرام
    post_to_telegram(
        f"🚀 <b>البوت بدا يشتغل!</b>\n\n"
        f"⏱️ سينشر كل {INTERVAL_MINUTES} دقيقة\n"
        f"⏰ {datetime.now().strftime('%H:%M - %d/%m/%Y')}"
    )

    while True:
        run_once()
        print(f"😴 ينتظر {INTERVAL_MINUTES} دقيقة...")
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    main()
