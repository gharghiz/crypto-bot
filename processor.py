"""
processor.py - معالجة وتحليل الأخبار مع AI و تحليل السوق
"""

import time
import difflib
import requests
import hashlib
from utils import logger, safe_html
from config import (
    IMPORTANT_KEYWORDS, BREAKING_KEYWORDS, HIGH_IMPACT_KEYWORDS,
    POSITIVE_WORDS, NEGATIVE_WORDS, COIN_MAP,
    COINGECKO_CACHE_SECONDS, SIMILARITY_THRESHOLD,
    ANTHROPIC_API_KEY, AI_SCORE_THRESHOLD, AI_CACHE_ENABLED
)

_session = requests.Session()

# ============================================================
# CoinGecko — سعر + تحليل السوق
# ============================================================
_price_cache = {}

def get_market_data(title: str) -> dict | None:
    """جلب سعر + تحليل السوق الكامل"""
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
        raw    = resp.json().get(coin_id, {})
        price  = raw.get("usd", 0)
        ch_24h = round(raw.get("usd_24h_change", 0), 2)
        ch_1h  = round(raw.get("usd_1h_in_currency", 0), 2)
        mcap   = raw.get("usd_market_cap", 0)

        price_str = f"${price:,.2f}" if price >= 1 else f"${price:.6f}"
        sign_24   = "+" if ch_24h >= 0 else ""
        sign_1h   = "+" if ch_1h  >= 0 else ""
        trend     = "📈" if ch_24h >= 0 else "📉"
        mcap_str  = f"${mcap/1e9:.1f}B" if mcap >= 1e9 else f"${mcap/1e6:.1f}M"

        result = {
            "price":    price_str,
            "ch_24h":   f"{sign_24}{ch_24h}%",
            "ch_1h":    f"{sign_1h}{ch_1h}%",
            "mcap":     mcap_str,
            "trend":    trend,
            "coin_id":  coin_id,
            "raw_24h":  ch_24h,
        }
        _price_cache[coin_id] = (result, now)
        return result
    except Exception as e:
        logger.warning(f"⚠️ CoinGecko error: {e}")
        return None

def format_market_block(data: dict) -> str:
    """تنسيق بلوك تحليل السوق"""
    return (
        f"💰 {data['trend']} {data['price']}\n"
        f"📊 24h: {data['ch_24h']} | 1h: {data['ch_1h']}\n"
        f"🏦 Market Cap: {data['mcap']}"
    )

# ============================================================
# AI Filter — Claude API
# ============================================================
_ai_cache = {}

def ai_score_news(title: str) -> tuple[int, str]:
    """
    يعطي الخبر نقطة من 10 وتعليق قصير
    returns: (score, comment)
    """
    if not ANTHROPIC_API_KEY:
        return 7, ""  # بدون AI نعتبرو مقبول

    cache_key = hashlib.md5(title.encode()).hexdigest()
    if AI_CACHE_ENABLED and cache_key in _ai_cache:
        return _ai_cache[cache_key]

    try:
        prompt = f"""You are a crypto news analyst. Rate this news headline for market impact.

Headline: "{title}"

Respond with ONLY this JSON format (no other text):
{{"score": 7, "comment": "Short insight in 1 sentence"}}

Score guide:
9-10: Major market-moving news (ETF approval, exchange hack, major ban)
7-8: Important news (regulation update, big price move, institutional buying)
5-6: Moderate interest
1-4: Low impact or opinion piece"""

        resp = _session.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=8
        )

        text = resp.json()["content"][0]["text"].strip()
        import json
        parsed  = json.loads(text)
        score   = int(parsed.get("score", 7))
        comment = parsed.get("comment", "")

        if AI_CACHE_ENABLED:
            _ai_cache[cache_key] = (score, comment)

        return score, comment

    except Exception as e:
        logger.warning(f"⚠️ AI scoring error: {e}")
        return 7, ""  # في حالة خطأ نعتبرو مقبول

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
    return any(k in title.lower() for k in IMPORTANT_KEYWORDS)

def is_breaking(title: str) -> bool:
    return any(k in title.lower() for k in BREAKING_KEYWORDS)

def is_high_impact(title: str) -> bool:
    return any(k in title.lower() for k in HIGH_IMPACT_KEYWORDS)

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

def format_message(item: dict) -> str:
    title       = item["title"]
    source      = item["source"]
    breaking    = item.get("breaking", False)
    high_impact = item.get("high_impact", False)
    ai_comment  = item.get("ai_comment", "")
    sentiment   = analyze_sentiment(title)
    market      = get_market_data(title)
    hashtags    = "#Crypto #Trading #Bitcoin #BTC"

    # هيدر
    if breaking:
        header = f"🚨 <b>BREAKING:</b> {safe_html(title)}"
    elif high_impact and sentiment == "🟢":
        header = f"🚀 <b>{safe_html(title)}</b>"
    elif high_impact and sentiment == "🔴":
        header = f"⚠️ <b>{safe_html(title)}</b>"
    else:
        header = f"{sentiment} {safe_html(title)}"

    msg = f"{header}\n\n"

    # تعليق AI
    if ai_comment:
        msg += f"🤖 {safe_html(ai_comment)}\n\n"

    # تحليل السوق
    if market:
        msg += f"{format_market_block(market)}\n\n"

    # engagement hook للأخبار المؤثرة
    if high_impact or breaking:
        idx  = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(ENGAGEMENT_HOOKS)
        msg += f"💬 {ENGAGEMENT_HOOKS[idx]}\n\n"

    msg += f"📌 {safe_html(source)}\n{hashtags}"
    return msg

# ============================================================
# Prioritize
# ============================================================

def prioritize(news_list: list) -> list:
    breaking = [n for n in news_list if n.get("breaking")]
    high     = [n for n in news_list if n.get("high_impact") and not n.get("breaking")]
    regular  = [n for n in news_list if not n.get("breaking") and not n.get("high_impact")]
    return breaking + high + regular
