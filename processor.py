"""
processor.py - معالجة وتحليل الأخبار
فلتر الجودة المحلي + تحليل السوق + sentiment
"""

import time
import difflib
from utils import logger, safe_html, now_utc
from config import (
    IMPORTANT_KEYWORDS, BREAKING_KEYWORDS, HIGH_IMPACT_KEYWORDS,
    POSITIVE_WORDS, NEGATIVE_WORDS, COIN_MAP,
    COINGECKO_CACHE_SECONDS, SIMILARITY_THRESHOLD, MIN_QUALITY_SCORE
)
import requests

# ============================================================
# CoinGecko Cache
# ============================================================
_price_cache = {}
_session = requests.Session()

def get_market_data(title: str) -> dict | None:
    """جلب بيانات السوق الكاملة: سعر + تغيير 1h و 24h + market cap"""
    title_lower = title.lower()
    coin_id = None
    for keyword, cid in COIN_MAP.items():
        if keyword in title_lower:
            coin_id = cid
            break
    if not coin_id:
        return None

    now = time.time()
    if coin_id in _price_cache:
        data, ts = _price_cache[coin_id]
        if now - ts < COINGECKO_CACHE_SECONDS:
            return data

    try:
        resp = _session.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_1hr_change": "true",
                "include_market_cap": "true",
            },
            timeout=5
        )
        raw = resp.json().get(coin_id, {})
        if not raw:
            return None

        price     = raw.get("usd", 0)
        change_1h = round(raw.get("usd_1h_change", 0), 2)
        change_24h = round(raw.get("usd_24h_change", 0), 2)
        mcap      = raw.get("usd_market_cap", 0)

        price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
        mcap_str  = f"${mcap/1e9:.1f}B" if mcap >= 1e9 else f"${mcap/1e6:.0f}M"

        def fmt_change(c):
            sign  = "+" if c >= 0 else ""
            arrow = "▲" if c >= 0 else "▼"
            return f"{arrow} {sign}{c}%"

        result = {
            "price":     price_str,
            "change_1h":  fmt_change(change_1h),
            "change_24h": fmt_change(change_24h),
            "mcap":       mcap_str,
            "raw_24h":    change_24h,
        }
        _price_cache[coin_id] = (result, now)
        return result
    except Exception as e:
        logger.warning(f"⚠️ CoinGecko error: {e}")
        return None

# ============================================================
# Quality Score (فلتر محلي بدون AI)
# ============================================================

# كلمات ترفع النقطة
HIGH_VALUE_WORDS = [
    "billion", "trillion", "record", "all-time high", "ath",
    "etf", "sec", "regulation", "blackrock", "federal reserve",
    "halving", "hack", "exploit", "crash", "pump", "whale",
    "institutional", "approved", "rejected", "ban", "lawsuit",
]

# كلمات تخفض النقطة (أخبار عادية ومملة)
LOW_VALUE_WORDS = [
    "opinion", "analysis", "weekly", "monthly", "roundup",
    "interview", "podcast", "recap", "guide", "how to",
    "explained", "what is", "basics", "beginner",
]

def quality_score(title: str) -> int:
    """يعطي نقطة من 0 إلى 10 للخبر"""
    t = title.lower()
    score = 5  # نقطة ابتدائية

    for w in HIGH_VALUE_WORDS:
        if w in t:
            score += 1

    for w in LOW_VALUE_WORDS:
        if w in t:
            score -= 1

    # خبر عاجل = نقطة قصوى
    if any(k in t for k in BREAKING_KEYWORDS):
        score += 3

    return max(0, min(10, score))

# ============================================================
# Sentiment
# ============================================================

def analyze_sentiment(title: str) -> str:
    t = title.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos > neg:   return "🟢"
    elif neg > pos: return "🔴"
    else:           return "🟡"

# ============================================================
# Keyword checks
# ============================================================

def is_important(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in IMPORTANT_KEYWORDS)

def is_breaking(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in BREAKING_KEYWORDS)

def is_high_impact(title: str) -> bool:
    """الأخبار لي تأثيرها قوي على السوق — هاد هي فقط لي تتثبت"""
    t = title.lower()
    return any(k in t for k in HIGH_IMPACT_KEYWORDS)

# ============================================================
# Duplicate Detection
# ============================================================

def is_duplicate(title: str, recent_titles: list) -> bool:
    for prev in recent_titles:
        ratio = difflib.SequenceMatcher(None, title.lower(), prev.lower()).ratio()
        if ratio >= SIMILARITY_THRESHOLD:
            return True
    return False

# ============================================================
# Engaging Rewrite
# ============================================================

ENGAGEMENT_HOOKS = [
    "What do you think? 👇",
    "Bullish or bearish? 🤔",
    "Are you buying or waiting? 💭",
    "Traders are watching this closely 👀",
]

def rewrite_title(title: str, sentiment: str, breaking: bool, high_impact: bool) -> str:
    t = safe_html(title.strip())
    if breaking:
        return f"🚨 <b>BREAKING:</b> {t}"
    if high_impact:
        if sentiment == "🟢":
            return f"🚀 <b>{t}</b>"
        elif sentiment == "🔴":
            return f"⚠️ <b>{t}</b>"
    return f"{sentiment} {t}"

def get_engagement_hook(title: str, high_impact: bool) -> str:
    if not high_impact:
        return ""
    import hashlib
    idx = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(ENGAGEMENT_HOOKS)
    return f"\n\n💬 {ENGAGEMENT_HOOKS[idx]}"

# ============================================================
# Format Message
# ============================================================

def format_message(item: dict) -> str:
    title       = item["title"]
    source      = item["source"]
    breaking    = item.get("breaking", False)
    high_impact = item.get("high_impact", False)
    sentiment   = analyze_sentiment(title)
    market      = get_market_data(title)
    hook        = get_engagement_hook(title, high_impact)
    hashtags    = "#Crypto #Trading #Bitcoin #BTC"

    headline = rewrite_title(title, sentiment, breaking, high_impact)
    msg = f"{headline}\n\n"

    # تحليل السوق الكامل
    if market:
        msg += (
            f"💰 {market['price']}\n"
            f"⏱ 1h: {market['change_1h']}  |  📅 24h: {market['change_24h']}\n"
            f"📊 MCap: {market['mcap']}\n\n"
        )

    msg += f"📌 {safe_html(source)}\n{hashtags}{hook}"
    return msg

# ============================================================
# Prioritize
# ============================================================

def prioritize(news_list: list) -> list:
    breaking = [n for n in news_list if n.get("breaking")]
    high     = [n for n in news_list if n.get("high_impact") and not n.get("breaking")]
    regular  = [n for n in news_list if not n.get("breaking") and not n.get("high_impact")]
    return breaking + high + regular
