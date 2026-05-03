"""
processor.py - معالجة الأخبار
FIX: is_important مصلحة + duplicate check أحسن
"""

import time
import difflib
import threading
import requests
from utils import logger, safe_html
from config import (
    IMPORTANT_KEYWORDS, BREAKING_KEYWORDS, HIGH_IMPACT_KEYWORDS,
    POSITIVE_WORDS, NEGATIVE_WORDS, COIN_MAP,
    COINGECKO_CACHE_SECONDS, SIMILARITY_THRESHOLD,
)
from ai import generate_ai_insight

_price_cache = {}
_price_lock  = threading.Lock()
_session     = requests.Session()

# ============================
# Market Data
# ============================

def get_market_data(title: str):
    title_lower = title.lower()
    coin_id = None
    for keyword, cid in COIN_MAP.items():
        if keyword in title_lower:
            coin_id = cid
            break

    if not coin_id:
        return None

    now = time.time()
    with _price_lock:
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
            },
            timeout=5
        )
        raw = resp.json().get(coin_id, {})
        if not raw:
            return None

        price      = raw.get("usd", 0)
        change_1h  = round(raw.get("usd_1h_change", 0), 2)
        change_24h = round(raw.get("usd_24h_change", 0), 2)

        def fmt(c):
            return f"{'▲' if c >= 0 else '▼'} {'+' if c >= 0 else ''}{c}%"

        result = {
            "price":      f"${price:,.2f}",
            "change_1h":  fmt(change_1h),
            "change_24h": fmt(change_24h),
        }

        with _price_lock:
            _price_cache[coin_id] = (result, now)
        return result

    except Exception as e:
        logger.warning(f"⚠️ Market error: {e}")
        return None

# ============================
# Sentiment
# ============================

def analyze_sentiment(title: str) -> str:
    t   = title.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos > neg:
        return "🟢"
    elif neg > pos:
        return "🔴"
    return "🟡"

# ============================
# FIX: is_important — فلترة حقيقية بدل return True
# ============================

def is_important(title: str) -> bool:
    """يرجع True إذا العنوان يحتوي على keyword مهم"""
    t = title.lower()
    return any(kw in t for kw in IMPORTANT_KEYWORDS)

def is_breaking(title: str) -> bool:
    return any(k in title.lower() for k in BREAKING_KEYWORDS)

def is_high_impact(title: str) -> bool:
    return any(k in title.lower() for k in HIGH_IMPACT_KEYWORDS)

# ============================
# FIX: Duplicate — thread-safe بـ lock
# ============================

_dup_lock = threading.Lock()

def is_duplicate(title: str, recent_titles: list) -> bool:
    """
    يفحص إذا كان العنوان مشابه لخبر سبق — thread-safe
    نستعمل آخر 50 عنوان فقط لتوفير الوقت
    """
    title_lower = title.lower()
    with _dup_lock:
        for prev in recent_titles[-50:]:
            prev_lower = prev.lower()
            # مطابقة تامة
            if title_lower == prev_lower:
                return True
            # أحدهم يحتوي الآخر
            if title_lower in prev_lower or prev_lower in title_lower:
                return True
            # تشابه كبير
            if difflib.SequenceMatcher(None, title_lower, prev_lower).ratio() >= SIMILARITY_THRESHOLD:
                return True
    return False

# ============================
# Format Message + AI
# ============================

def format_message(item: dict):
    title   = item["title"]
    source  = item["source"]
    url     = item.get("url", "")

    breaking = item.get("breaking", False)
    high     = item.get("high_impact", False)

    sentiment = analyze_sentiment(title)
    market    = get_market_data(title)

    # AI فقط للأخبار المهمة
    ai = {"summary": "", "sentiment": "", "reason": ""}
    if breaking or high:
        ai = generate_ai_insight(title)

    # العنوان
    headline = f"{sentiment} {safe_html(title)}"
    if breaking:
        headline = f"🚨 <b>BREAKING:</b> {safe_html(title)}"

    msg = f"{headline}\n\n"

    # بيانات السوق
    if market:
        msg += f"💰 {market['price']}\n"
        msg += f"⏱ 1h: {market['change_1h']} | 24h: {market['change_24h']}\n\n"

    # AI Insight
    if ai.get("summary"):
        msg += (
            f"🧠 <b>AI Insight</b>\n"
            f"├ {safe_html(ai['summary'])}\n"
            f"├ {safe_html(ai['sentiment'])}\n"
            f"└ {safe_html(ai['reason'])}\n\n"
        )

    msg += f"📌 {safe_html(source)}\n"

    # رابط الخبر إذا موجود
    if url:
        msg += f"🔗 <a href=\"{url}\">Read More</a>\n"

    msg += "#Crypto"

    return msg, ai

# ============================
# Prioritize — Breaking أولاً ثم High Impact
# ============================

def prioritize(news_list: list) -> list:
    """ترتيب الأخبار: breaking أولاً، ثم high_impact، ثم الباقي"""
    breaking    = [n for n in news_list if n.get("breaking")]
    high_impact = [n for n in news_list if n.get("high_impact") and not n.get("breaking")]
    rest        = [n for n in news_list if not n.get("breaking") and not n.get("high_impact")]
    return breaking + high_impact + rest
