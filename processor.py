"""
processor.py - معالجة وتحليل الأخبار
"""

import time
import difflib
import hashlib
import requests
from utils import logger, safe_html
from config import (
    IMPORTANT_KEYWORDS, BREAKING_KEYWORDS, HIGH_IMPACT_KEYWORDS,
    POSITIVE_WORDS, NEGATIVE_WORDS, COIN_MAP,
    COINGECKO_CACHE_SECONDS, SIMILARITY_THRESHOLD,
)

# ============================================================
# CoinGecko Cache
# ============================================================
_price_cache = {}
_session = requests.Session()

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

        price      = raw.get("usd", 0)
        change_1h  = round(raw.get("usd_1h_change", 0), 2)
        change_24h = round(raw.get("usd_24h_change", 0), 2)
        mcap       = raw.get("usd_market_cap", 0)

        price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
        mcap_str  = f"${mcap/1e9:.1f}B" if mcap >= 1e9 else f"${mcap/1e6:.0f}M"

        def fmt(c):
            return f"{'▲' if c >= 0 else '▼'} {'+' if c >= 0 else ''}{c}%"

        result = {
            "price":      price_str,
            "change_1h":  fmt(change_1h),
            "change_24h": fmt(change_24h),
            "mcap":       mcap_str,
        }
        _price_cache[coin_id] = (result, now)
        return result
    except Exception as e:
        logger.warning(f"⚠️ CoinGecko: {e}")
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
    return "🟡"

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
# Format Message
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
        return f"🚀 <b>{t}</b>" if sentiment == "🟢" else f"⚠️ <b>{t}</b>" if sentiment == "🔴" else f"🟡 <b>{t}</b>"
    return f"{sentiment} {t}"

def get_engagement_hook(title: str, high_impact: bool) -> str:
    if not high_impact:
        return ""
    idx = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(ENGAGEMENT_HOOKS)
    return f"\n\n💬 {ENGAGEMENT_HOOKS[idx]}"

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
