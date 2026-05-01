"""
utils.py - أدوات مساعدة
"""

import html
import logging
import re
from datetime import datetime, timezone

# ============================================================
# Logging
# ============================================================

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s UTC | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.Formatter.converter = lambda *args: datetime.now(timezone.utc).timetuple()
    return logging.getLogger("cryptobot")

logger = setup_logger()

# ============================================================
# UTC Time
# ============================================================

def now_utc():
    return datetime.now(timezone.utc)

def is_peak_time():
    from config import PEAK_HOURS_UTC
    return now_utc().hour in PEAK_HOURS_UTC

# ============================================================
# HTML Safety
# ============================================================

def safe_html(text: str) -> str:
    """تأمين النص قبل الإرسال لتيليغرام"""
    return html.escape(str(text))

# ============================================================
# URL Cleaning
# ============================================================

def clean_url(url: str) -> str:
    """إزالة tracking parameters من الروابط"""
    if not url:
        return ""
    url = re.sub(r'\?utm_[^&]*(&[^&]*)*', '', url)
    url = re.sub(r'&utm_[^&]*', '', url)
    url = url.rstrip('?&')
    return url

# ============================================================
# Title Cleaning
# ============================================================

def clean_title(title: str) -> str:
    """تنظيف العنوان"""
    title = re.sub(r'\s+', ' ', title).strip()
    # إزالة source prefix مثل "CoinDesk: "
    title = re.sub(r'^[\w\s]+:\s*', '', title) if ':' in title[:30] else title
    # اقتصار العنوان على 200 حرف
    if len(title) > 200:
        title = title[:197] + "..."
    return title
