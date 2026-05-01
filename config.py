"""
config.py - جميع الإعدادات
"""

import os

# ============================================================
# Telegram
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# ============================================================
# Anthropic API (للذكاء الاصطناعي)
# ============================================================
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ============================================================
# Timing
# ============================================================
INTERVAL_MINUTES = int(os.environ.get("INTERVAL_MINUTES", "1"))

# ============================================================
# RSS Sources - 10 مصادر
# ============================================================
RSS_FEEDS = [
    {"name": "CoinTelegraph",    "url": "https://cointelegraph.com/rss"},
    {"name": "CoinDesk",         "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "Decrypt",          "url": "https://decrypt.co/feed"},
    {"name": "CryptoSlate",      "url": "https://cryptoslate.com/feed/"},
    {"name": "Bitcoin Magazine",  "url": "https://bitcoinmagazine.com/feed"},
    {"name": "NewsBTC",          "url": "https://www.newsbtc.com/feed/"},
    {"name": "CryptoNews",       "url": "https://cryptonews.com/news/feed/"},
    {"name": "BeInCrypto",       "url": "https://beincrypto.com/feed/"},
    {"name": "The Block",        "url": "https://www.theblock.co/rss.xml"},
    {"name": "Blockworks",       "url": "https://blockworks.co/feed"},
]

# ============================================================
# Keywords
# ============================================================
IMPORTANT_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "bnb", "solana", "sol",
    "xrp", "ripple", "cardano", "ada", "dogecoin", "doge",
    "etf", "sec", "halving", "hack", "hacked", "exploit",
    "ban", "banned", "regulation", "legal", "lawsuit",
    "crash", "dump", "pump", "surge", "rally", "bull", "bear",
    "all-time high", "ath", "record", "billion", "trillion",
    "binance", "coinbase", "blackrock", "fed", "federal reserve",
    "tether", "usdt", "stablecoin", "defi", "nft",
    "trading", "price", "market", "exchange", "liquidation",
    "futures", "options", "whale", "institutional",
]

BREAKING_KEYWORDS = [
    "breaking", "urgent", "just in", "alert", "emergency",
    "hack", "hacked", "exploit", "crash", "ban", "banned",
    "collapse", "sec", "arrested", "scam", "rug pull"
]

HIGH_IMPACT_KEYWORDS = [
    "btc", "bitcoin", "ethereum", "eth", "etf", "sec",
    "regulation", "crash", "pump", "halving", "blackrock"
]

POSITIVE_WORDS = [
    "surge", "rally", "pump", "bull", "record", "high", "gain",
    "approved", "launch", "partnership", "adoption", "growth",
    "profit", "rises", "jumps", "soars", "breakout", "ath"
]

NEGATIVE_WORDS = [
    "crash", "dump", "bear", "ban", "hack", "fall", "drop",
    "loss", "decline", "lawsuit", "warning", "risk", "fear",
    "sell", "plunge", "tumbles", "falls", "exploit", "scam"
]

# ============================================================
# CoinGecko
# ============================================================
COIN_MAP = {
    "bitcoin": "bitcoin",   "btc": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum",
    "bnb": "binancecoin",
    "solana": "solana",     "sol": "solana",
    "xrp": "ripple",        "ripple": "ripple",
    "cardano": "cardano",   "ada": "cardano",
    "dogecoin": "dogecoin", "doge": "dogecoin",
}

COINGECKO_CACHE_SECONDS = 300  # 5 دقائق

# ============================================================
# Price Alerts
# ============================================================
PRICE_ALERT_COINS = {
    "bitcoin":    "BTC",
    "ethereum":   "ETH",
    "solana":     "SOL",
    "binancecoin": "BNB",
}
PRICE_ALERT_THRESHOLD = 3.0   # % تغيير في ساعة يطلق التنبيه
PRICE_CHECK_CACHE = {}        # { coin_id: (price, timestamp) }
PRICE_ALERT_INTERVAL = 300    # كل 5 دقائق نتحقق من السعر

# ============================================================
# AI Filter
# ============================================================
AI_SCORE_THRESHOLD  = 6       # من 10 — ما دون هاد الرقم ما ينشرش
AI_CACHE_ENABLED    = True

# ============================================================
# Duplicate Detection
# ============================================================
SIMILARITY_THRESHOLD = 0.80

# ============================================================
# Posting
# ============================================================
MAX_POSTS_PER_CYCLE  = 5
DELAY_BETWEEN_POSTS  = 3
MAX_RETRIES_TELEGRAM = 3
PIN_BREAKING_NEWS    = True   # تثبيت الأخبار العاجلة والمؤثرة فقط
