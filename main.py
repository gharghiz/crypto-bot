"""
main.py - نقطة البداية
"""

import sys
import time
import traceback

from utils import logger, is_peak_time, now_utc
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    INTERVAL_MINUTES, MAX_POSTS_PER_CYCLE, DELAY_BETWEEN_POSTS
)
from database import init_db, is_posted, mark_posted, get_recent_titles, cleanup_old
from scraper import fetch_all_news
from processor import is_important, is_breaking, is_high_impact, is_duplicate, format_message, prioritize
from bot import send_message

# ============================================================
# Startup check
# ============================================================

def check_env():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("❌ TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID ناقصين!")
        sys.exit(1)
    logger.info("✅ جميع المفاتيح موجودة")

# ============================================================
# Process & enrich news
# ============================================================

def enrich(news_list: list) -> list:
    """إضافة flags لكل خبر"""
    enriched = []
    for item in news_list:
        title = item["title"]
        if not is_important(title):
            continue
        item["breaking"]    = is_breaking(title)
        item["high_impact"] = is_high_impact(title)
        enriched.append(item)
    return enriched

# ============================================================
# Main cycle
# ============================================================

def run_cycle(force: bool = False):
    logger.info(f"🔄 دورة جديدة — UTC {now_utc().strftime('%H:%M:%S')}")

    # إيلا مو وقت ذروة ومو force، نشوفو الأخبار العاجلة فقط
    peak = is_peak_time()

    all_news   = fetch_all_news()
    enriched   = enrich(all_news)
    prioritized = prioritize(enriched)

    recent_titles = get_recent_titles(100)
    posted_count  = 0

    for item in prioritized:
        news_id = item["id"]
        title   = item["title"]
        breaking = item.get("breaking", False)

        # الأخبار العاجلة تنشر دايماً — الباقي غير في وقت الذروة أو force
        if not breaking and not peak and not force:
            continue

        # تحقق من قاعدة البيانات
        if is_posted(news_id):
            continue

        # تحقق من التشابه
        if is_duplicate(title, recent_titles):
            logger.info(f"🔁 خبر مشابه تجاهلناه: {title[:60]}")
            continue

        # نشر
        message = format_message(item)
        success = send_message(message)

        if success:
            mark_posted(news_id, title, item["source"])
            recent_titles.append(title)
            posted_count += 1

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

    logger.info(f"🤖 البوت بدا | كل {INTERVAL_MINUTES} دقيقة | UTC")

    send_message(
        f"🚀 <b>البوت بدا يشتغل!</b>\n\n"
        f"⏱ يتحقق كل {INTERVAL_MINUTES} دقيقة\n"
        f"⚡️ الأخبار العاجلة تنشر فوراً\n"
        f"🕐 {now_utc().strftime('%H:%M UTC')}"
    )

    # تنظيف أسبوعي
    cleanup_old(days=30)

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
