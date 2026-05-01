"""
main.py - نقطة البداية
مع AI filter + تنبيهات السعر + تثبيت ذكي
"""

import sys
import time
import traceback
import requests

from utils import logger, now_utc
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    INTERVAL_MINUTES, MAX_POSTS_PER_CYCLE, DELAY_BETWEEN_POSTS,
    AI_SCORE_THRESHOLD, ANTHROPIC_API_KEY,
    PRICE_ALERT_COINS, PRICE_ALERT_THRESHOLD, PRICE_ALERT_INTERVAL,
    PIN_BREAKING_NEWS
)
from database import init_db, is_posted, mark_posted, get_recent_titles, cleanup_old
from scraper import fetch_all_news
from processor import (
    is_important, is_breaking, is_high_impact,
    is_duplicate, format_message, prioritize, ai_score_news
)
from bot import send_message, pin_message

# ============================================================
# Startup check
# ============================================================

def check_env():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID ناقصين!")
        sys.exit(1)
    if ANTHROPIC_API_KEY:
        logger.info("🤖 AI Filter: مفعل")
    else:
        logger.info("🤖 AI Filter: غير مفعل — زيد ANTHROPIC_API_KEY في Variables")
    logger.info("✅ جميع المفاتيح موجودة")

# ============================================================
# Price Alerts
# ============================================================
_last_prices     = {}
_last_alert_time = {}
_price_session   = requests.Session()

def check_price_alerts():
    """تحقق من تحركات السعر الكبيرة وأرسل تنبيه"""
    coin_ids = ",".join(PRICE_ALERT_COINS.keys())
    try:
        resp = _price_session.get(
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
        logger.warning(f"⚠️ Price alert check error: {e}")
        return

    now = time.time()
    for coin_id, symbol in PRICE_ALERT_COINS.items():
        raw    = data.get(coin_id, {})
        price  = raw.get("usd", 0)
        ch_1h  = raw.get("usd_1h_in_currency", 0)

        if not price or ch_1h is None:
            continue

        # ما نبعتش تنبيه قبل PRICE_ALERT_INTERVAL ثانية
        last_alert = _last_alert_time.get(coin_id, 0)
        if now - last_alert < PRICE_ALERT_INTERVAL:
            continue

        abs_change = abs(ch_1h)
        if abs_change >= PRICE_ALERT_THRESHOLD:
            direction = "🚀 pumping" if ch_1h > 0 else "📉 dumping"
            sign      = "+" if ch_1h > 0 else ""
            price_str = f"${price:,.2f}"
            alert_msg = (
                f"⚡️ <b>Price Alert — {symbol}</b>\n\n"
                f"{direction} {sign}{round(ch_1h, 2)}% in the last hour!\n\n"
                f"💰 Current Price: {price_str}\n\n"
                f"#Crypto #{symbol} #PriceAlert"
            )
            msg_id = send_message(alert_msg)
            if msg_id:
                pin_message(msg_id)
                _last_alert_time[coin_id] = now
                logger.info(f"⚡️ Price alert sent for {symbol}: {sign}{ch_1h}%")

# ============================================================
# Enrich news
# ============================================================

def enrich(news_list: list) -> list:
    enriched = []
    for item in news_list:
        title = item["title"]
        if not is_important(title):
            continue
        item["breaking"]    = is_breaking(title)
        item["high_impact"] = is_high_impact(title)

        # AI scoring — غير للأخبار غير العاجلة لتوفير وقت
        if ANTHROPIC_API_KEY and not item["breaking"]:
            score, comment = ai_score_news(title)
            item["ai_score"]   = score
            item["ai_comment"] = comment
            if score < AI_SCORE_THRESHOLD:
                logger.info(f"🤖 AI رفض الخبر (score {score}): {title[:60]}")
                continue
        else:
            item["ai_score"]   = 10
            item["ai_comment"] = ""

        enriched.append(item)
    return enriched

# ============================================================
# Main cycle
# ============================================================

_last_price_check = 0

def run_cycle():
    global _last_price_check
    logger.info(f"🔄 دورة جديدة — UTC {now_utc().strftime('%H:%M:%S')}")

    # تحقق من تنبيهات السعر كل 5 دقائق
    now = time.time()
    if now - _last_price_check >= PRICE_ALERT_INTERVAL:
        check_price_alerts()
        _last_price_check = now

    all_news    = fetch_all_news()
    enriched    = enrich(all_news)
    prioritized = prioritize(enriched)

    recent_titles = get_recent_titles(100)
    posted_count  = 0

    for item in prioritized:
        news_id     = item["id"]
        title       = item["title"]
        breaking    = item.get("breaking", False)
        high_impact = item.get("high_impact", False)

        if is_posted(news_id):
            continue

        if is_duplicate(title, recent_titles):
            logger.info(f"🔁 خبر مشابه تجاهلناه: {title[:60]}")
            continue

        message    = format_message(item)
        message_id = send_message(message)

        if message_id:
            mark_posted(news_id, title, item["source"])
            recent_titles.append(title)
            posted_count += 1

            # تثبيت غير للأخبار العاجلة أو المؤثرة فقط
            if PIN_BREAKING_NEWS and (breaking or high_impact):
                pin_message(message_id)

        if posted_count >= MAX_POSTS_PER_CYCLE:
            break

        time.sleep(DELAY_BETWEEN_POSTS)

    logger.info(f"✅ نشرنا {posted_count} خبر في هاد الدورة")

# ============================================================
# Entry point
# ============================================================

def main():
    check_env()
    init_db()
    cleanup_old(days=30)

    logger.info(f"🤖 البوت بدا | كل {INTERVAL_MINUTES} دقيقة | UTC")

    ai_status = "مفعل 🤖" if ANTHROPIC_API_KEY else "غير مفعل"
    send_message(
        f"🚀 <b>البوت بدا يشتغل!</b>\n\n"
        f"⏱ ينشر كل {INTERVAL_MINUTES} دقيقة\n"
        f"📌 التثبيت: الأخبار العاجلة والمؤثرة فقط\n"
        f"⚡️ تنبيهات السعر: مفعلة (تغيير {'>'} {PRICE_ALERT_THRESHOLD}% في ساعة)\n"
        f"🤖 فلتر AI: {ai_status}\n"
        f"🕐 {now_utc().strftime('%H:%M UTC')}"
    )

    while True:
        try:
            run_cycle()
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع: {e}")
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
