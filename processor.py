"""
processor.py - معالجة وتحليل الأخبار
"""

import time
import difflib
from utils import logger, safe_html, now_utc
from config import (
    IMPORTANT_KEYWORDS, BREAKING_KEYWORDS, HIGH_IMPACT_KEYWORDS,
    POSITIVE_WORDS, NEGATIVE_WORDS, COIN_MAP,
    COINGECKO_CACHE_SECONDS, SIMILARITY_THRESHOLD
)
import requests

# ============================================================
# CoinGecko Cache
# ============================================================
_price_cache = {}  # { coin_id: (price_data, timestamp) }
_session = requests.Session()

def get_coin_price(title: str):
    """جلب سعر العملة مع Cache"""
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
            return data  # كاش ما زال صالح

    try:
        resp = _session.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": coin_id, "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=5
        )
        raw = resp.json().get(coin_id, {})
        price  = raw.get("usd", 0)
        change = round(raw.get("usd_24h_change", 0), 2)
        arrow  = "📈" if change >= 0 else "📉"
        sign   = "+" if change >= 0 else ""
        price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
        result = f"{arrow} {price_str} ({sign}{change}%)"
        _price_cache[coin_id] = (result, now)
        return result
    except Exception as e:
        logger.warning(f"⚠️ CoinGecko error: {e}")
        return None

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
    """إعادة كتابة العنوان بأسلوب جذاب"""
    t = title.strip()

    # إيلا كان خبر عاجل
    if breaking:
        return f"🚨 <b>BREAKING:</b> {safe_html(t)}"

    # إيلا كان خبر مؤثر بزاف
    if high_impact:
        if sentiment == "🟢":
            return f"🚀 <b>{safe_html(t)}</b>"
        elif sentiment == "🔴":
            return f"⚠️ <b>{safe_html(t)}</b>"

    return f"{sentiment} {safe_html(t)}"

def get_engagement_hook(title: str, high_impact: bool) -> str:
    """زيد سؤال engagement إيلا كان الخبر مؤثر"""
    if not high_impact:
        return ""
    import hashlib
    idx = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(ENGAGEMENT_HOOKS)
    return f"\n\n💬 {ENGAGEMENT_HOOKS[idx]}"

# ============================================================
# Format Message
# ============================================================

def format_message(item: dict) -> str:
    title      = item["title"]
    source     = item["source"]
    breaking   = item.get("breaking", False)
    high_impact = item.get("high_impact", False)
    sentiment  = analyze_sentiment(title)
    price      = get_coin_price(title)
    hook       = get_engagement_hook(title, high_impact)
    hashtags   = "#Crypto #Trading #Bitcoin #BTC"

    headline = rewrite_title(title, sentiment, breaking, high_impact)

    msg = f"{headline}\n\n"
    if price:
        msg += f"💰 {price}\n\n"
    msg += f"📌 {safe_html(source)}\n{hashtags}{hook}"

    return msg

# ============================================================
# Prioritize
# ============================================================

def prioritize(news_list: list) -> list:
    """ترتيب الأخبار: عاجلة → مؤثرة → عادية"""
    breaking   = [n for n in news_list if n.get("breaking")]
    high       = [n for n in news_list if n.get("high_impact") and not n.get("breaking")]
    regular    = [n for n in news_list if not n.get("breaking") and not n.get("high_impact")]
    return breaking + high + regular
