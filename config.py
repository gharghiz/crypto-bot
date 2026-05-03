"""
config.py - جميع الإعدادات
"""

import os

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")

# Timing
INTERVAL_MINUTES = int(os.environ.get("INTERVAL_MINUTES", "5"))

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# RSS Sources - 15 مصدر
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
    {"name": "CoinGape",         "url": "https://coingape.com/feed/"},
    {"name": "AMBCrypto",        "url": "https://ambcrypto.com/feed/"},
    {"name": "U.Today",          "url": "https://u.today/rss"},
    {"name": "Bitcoinist",       "url": "https://bitcoinist.com/feed/"},
    {"name": "CryptoSlate News", "url": "https://cryptoslate.com/news/feed/"},
]

# Keywords — موسعة باش ينشر أكثر
IMPORTANT_KEYWORDS = [
    # عملات
    "bitcoin", "btc", "ethereum", "eth", "bnb", "solana", "sol",
    "xrp", "ripple", "cardano", "ada", "dogecoin", "doge",
    "crypto", "cryptocurrency", "blockchain", "web3", "token",
    # أحداث
    "etf", "sec", "halving", "hack", "hacked", "exploit",
    "ban", "banned", "regulation", "legal", "lawsuit",
    "crash", "dump", "pump", "surge", "rally", "bull", "bear",
    "all-time high", "ath", "record", "billion", "million",
    # مؤسسات
    "binance", "coinbase", "blackrock", "fed", "federal reserve",
    "tether", "usdt", "stablecoin", "defi", "nft",
    # تداول
    "trading", "price", "market", "exchange", "liquidation",
    "futures", "options", "whale", "institutional", "wallet",
    "mining", "miner", "network", "protocol", "layer",
]

BREAKING_KEYWORDS = [
    "breaking", "urgent", "just in", "alert", "emergency",
    "hack", "hacked", "exploit", "crash", "ban", "banned",
    "collapse", "sec", "arrested", "scam", "rug pull"
]

HIGH_IMPACT_KEYWORDS = [
    "etf", "sec", "regulation", "crash", "pump", "halving",
    "blackrock", "federal reserve", "ban", "hack", "exploit",
    "all-time high", "ath", "liquidation", "whale", "breaking"
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

# CoinGecko
COIN_MAP = {
    "bitcoin": "bitcoin",   "btc": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum",
    "bnb": "binancecoin",
    "solana": "solana",     "sol": "solana",
    "xrp": "ripple",        "ripple": "ripple",
    "cardano": "cardano",   "ada": "cardano",
    "dogecoin": "dogecoin", "doge": "dogecoin",
}
COINGECKO_CACHE_SECONDS = 300

# Price Alerts
PRICE_ALERT_COINS = {
    "bitcoin":     "BTC",
    "ethereum":    "ETH",
    "binancecoin": "BNB",
    "solana":      "SOL",
    "ripple":      "XRP",
}
PRICE_ALERT_THRESHOLD = float(os.environ.get("PRICE_ALERT_THRESHOLD", "3.0"))
PRICE_CHECK_INTERVAL  = int(os.environ.get("PRICE_CHECK_INTERVAL", "5"))

# Duplicate Detection — خففناها باش ينشر أكثر
SIMILARITY_THRESHOLD = 0.85

# Posting — زدنا عدد المنشورات
MAX_POSTS_PER_CYCLE  = 8
DELAY_BETWEEN_POSTS  = 2
MAX_RETRIES_TELEGRAM = 3
