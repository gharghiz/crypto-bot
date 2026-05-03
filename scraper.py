"""
scraper.py - جلب الأخبار من RSS بشكل parallel
FIX: retry بسيط على الـ feeds الفاشلة
"""

import time
import feedparser
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import logger, clean_title, clean_url
from config import RSS_FEEDS

session = requests.Session()
session.headers.update({"User-Agent": "CryptoNewsBot/2.0"})

MAX_RETRIES = 2  # محاولتين في حالة الفشل

def fetch_feed(feed: dict) -> list:
    """جلب feed واحد مع retry"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            parsed = feedparser.parse(feed["url"])
            # feedparser ما يرمي exception — نتحقق من bozo
            if parsed.bozo and not parsed.entries:
                raise ValueError(f"bozo feed: {parsed.bozo_exception}")

            news = []
            for entry in parsed.entries[:25]:
                news_id = entry.get("id") or entry.get("link", "")
                title   = clean_title(entry.get("title", ""))
                url     = clean_url(entry.get("link", ""))
                if not title or not news_id:
                    continue
                news.append({
                    "id":     news_id,
                    "title":  title,
                    "url":    url,
                    "source": feed["name"],
                })
            logger.info(f"📡 {feed['name']}: {len(news)} خبر")
            return news

        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(f"⚠️ محاولة {attempt}/{MAX_RETRIES} — {feed['name']}: {e}")
                time.sleep(2 * attempt)
            else:
                logger.warning(f"⚠️ فشل نهائي {feed['name']}: {e}")
    return []

def fetch_all_news() -> list:
    """جلب الأخبار من جميع المصادر بشكل parallel"""
    all_news = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_feed, feed): feed for feed in RSS_FEEDS}
        for future in as_completed(futures):
            try:
                all_news.extend(future.result())
            except Exception as e:
                logger.warning(f"⚠️ خطأ في scraper: {e}")
    logger.info(f"📊 إجمالي: {len(all_news)} خبر")
    return all_news
