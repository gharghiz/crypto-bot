"""
main.py - نقطة البداية
✅ ينشر دايماً بدون قيود وقت
✅ تثبيت غير الأخبار المؤثرة على السوق
❌ تم إلغاء فلاتر الجودة والأهمية (ينشر كل الأخبار)
✅ تنبيهات السعر
"""

import sys
import time
import traceback
import requests
from utils import logger, now_utc, safe_html
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    INTERVAL_MINUTES, MAX_POSTS_PER_CYCLE, DELAY_BETWEEN_POSTS,
    PRICE_ALERT_COINS, PRICE_ALERT_THRESHOLD, PRICE_CHECK_INTERVAL,
)
from database import init_db, is_posted, mark_posted, get_recent_titles, cleanup_old
from scraper import fetch_all_news
from processor import (
    is_breaking, is_high_impact,
    is_duplicate, format_message, prioritize, quality_score
)
from bot import send_message, send_price_alert

# ============================================================
# Startup check
# ============================================================

def check_env():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID ناقصين!")
        sys.exit(1)
    logger.info("✅ جميع المفاتيح موجودة")

# ============================================================
# Price Alert System
# ============================================================

_last_prices  = {}   # { coin_id: price }
_last_price_check = 0

_session = requests.Session()

def check_price_alerts():
    """يتحقق من تغييرات الأسعار ويبعت تنبيه إيلا تجاوزت الحد"""
    global _last_price_check, _last_prices

    now = time.time()
    if now - _last_price_check < PRICE_CHECK_INTERVAL * 60:
        return  # مزال ما حان وقت التحقق

    _last_price_check = now
    coin_ids = ",".join(PRICE_ALERT_COINS.keys())

    try:
        resp = _session.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coin_ids,
                "vs_currencies": "usd",
                "include_1hr_change": "true",
            },
            timeout=5
        )
        data = resp.json()
    except Exception as e:
        logger.warning(f"⚠️ فشل جلب الأسعار: {e}")
        return

    for coin_id, symbol in PRICE_ALERT_COINS.items():
        raw = data.get(coin_id, {})
        if not raw:
            continue

        price    = raw.get("usd", 0)
        change1h = round(raw.get("usd_1h_change", 0), 2)

        # إيلا التغيير في ساعة تجاوز الحد
        if abs(change1h) >= PRICE_ALERT_THRESHOLD:
            direction = "🚀 صعود" if change1h > 0 else "🔴 هبوط"
            sign      = "+" if change1h > 0 else ""
            price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"

            alert_msg = (
                f"⚡️ <b>تنبيه السعر — {symbol}</b>\n\n"
                f"{direction} حاد في آخر ساعة!\n\n"
                f"💰 السعر الحالي: {price_str}\n"
                f"📈 التغيير (1h): {sign}{change1h}%\n\n"
                f"#Crypto #{symbol} #PriceAlert"
            )

            logger.info(f"⚡️ تنبيه سعر: {symbol} {sign}{change1h}%")
            send_price_alert(alert_msg)

# ============================================================
# Enrich news (بدون فلاتر حجب)
# ============================================================

def enrich(news_list: list) -> list:
    enriched = []
    for item in news_list:
        title = item["title"]
        
        # ✅ الفلاتر تم إلغاؤها: كنمرر كل الأخبار بلا ما نحسبهم
        item["breaking"]    = is_breaking(title)
        item["high_impact"] = is_high_impact(title)
        item["quality"]     = quality_score(title) # بنحسبها بلا ما نمشيها، باش تخدم فالتثبيت
        enriched.append(item)
        
    return enriched

# ============================================================
# Main cycle
# ============================================================

def run_cycle():
    logger.info(f"🔄 دورة جديدة — UTC {now_utc().strftime('%H:%M:%S')}")

    # تنبيهات السعر
    check_price_alerts()

    all_news    = fetch_all_news()
    enriched    = enrich(all_news)
    prioritized = prioritize(enriched)

    recent_titles = get_recent_titles(100)
    posted_count  = 0

    for item in prioritized:
        news_id     = item["id"]
        title       = item["title"]
        high_impact = item.get("high_impact", False)
        breaking    = item.get("breaking", False)

        if is_posted(news_id):
            continue

        # كنحافظ على فلتر التكرار باش ما يصيفط نفس الخبر مرات
        if is_duplicate(title, recent_titles):
            logger.info(f"🔁 مشابه: {title[:60]}")
            continue

        message    = format_message(item)
        message_id = send_message(message)

        if message_id:
            mark_posted(news_id, title, item["source"])
            recent_titles.append(title)
            posted_count += 1

        if posted_count >= MAX_POSTS_PER_CYCLE:
            break

        time.sleep(DELAY_BETWEEN_POSTS)

    logger.info(f"✅ نشرنا {posted_count} خبر")

# ============================================================
# Entry point
# ============================================================

def main():
    check_env()
    init_db()
    cleanup_old(days=30)

    logger.info(f"🤖 البوت بدا | كل {INTERVAL_MINUTES} دقيقة")

    send_message(
        f"🚀 <b>البوت بدا يشتغل!</b>\n\n"
        f"⏱ ينشر كل {INTERVAL_MINUTES} دقيقة\n"
        f"📌 تثبيت الأخبار المؤثرة على السوق فقط\n"
        f"⚡️ تنبيهات السعر عند تحرك ≥{PRICE_ALERT_THRESHOLD}% في ساعة\n"
        f"🔓 الفلاتر مغلقة (ينشر كل الأخبار)\n"
        f"🕐 {now_utc().strftime('%H:%M UTC')}"
    )

    while True:
        try:
            run_cycle()
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            traceback.print_exc()

        logger.info(f"😴 ينتظر {INTERVAL_MINUTES} دقيقة...")
        time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"❌ خطأ فادح: {e}")
        traceback.print_exc()
        sys.exit(1)
