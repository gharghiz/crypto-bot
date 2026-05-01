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
# Timing (UTC)
# ============================================================
INTERVAL_MINUTES = int(os.environ.get("INTERVAL_MINUTES", "30"))

# أوقات الذروة بالـ UTC (المغرب = UTC+1)
# 6-9 صباح UTC = 7-10 صباح المغرب
# 17-22 UTC = 18-23 مساء المغرب
PEAK_HOURS_UTC = list(range(6, 10)) + list(range(17, 23))

# ============================================================
# RSS Sources
# ============================================================
RSS_FEEDS = [
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss"},
    {"name": "CoinDesk",      "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "Decrypt",       "url": "https://decrypt.co/feed"},
    {"name": "CryptoSlate",   "url": "https://cryptoslate.com/feed/"},
    {"name": "Bitcoin Magazine", "url": "https://bitcoinmagazine.com/feed"},
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
# Duplicate Detection
# ============================================================
SIMILARITY_THRESHOLD = 0.80  # 80%

# ============================================================
# Posting
# ============================================================
MAX_POSTS_PER_CYCLE  = 5
DELAY_BETWEEN_POSTS  = 5   # ثواني
MAX_RETRIES_TELEGRAM = 3
