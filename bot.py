"""
bot.py - إرسال الرسائل لتيليغرام
"""

import time
import requests
from utils import logger
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MAX_RETRIES_TELEGRAM

_session = requests.Session()

def send_message(text: str) -> bool:
    """إرسال رسالة لتيليغرام مع retry"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":                  TELEGRAM_CHAT_ID,
        "text":                     text,
        "parse_mode":               "HTML",
        "disable_web_page_preview": True,
    }

    for attempt in range(1, MAX_RETRIES_TELEGRAM + 1):
        try:
            resp = _session.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("✅ تم النشر في تيليغرام")
                return True
            elif resp.status_code == 429:
                # Rate limit
                retry_after = resp.json().get("parameters", {}).get("retry_after", 10)
                logger.warning(f"⏳ Rate limit — ننتظر {retry_after}s")
                time.sleep(retry_after)
            else:
                logger.error(f"❌ تيليغرام error {resp.status_code}: {resp.text}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ محاولة {attempt}/{MAX_RETRIES_TELEGRAM} فشلت: {e}")
            time.sleep(3 * attempt)

    logger.error("❌ فشل الإرسال بعد جميع المحاولات")
    return False
