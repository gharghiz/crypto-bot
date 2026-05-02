"""
ai.py - OpenAI integration للتحليل الذكي للأخبار
"""

import logging
from config import OPENAI_API_KEY

logger = logging.getLogger("cryptobot")

def generate_ai_insight(title: str) -> dict:
    """تحليل الخبر بـ AI — يرجع summary + sentiment + reason"""
    if not OPENAI_API_KEY:
        return {"summary": "", "sentiment": "", "reason": ""}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        prompt = f"""Analyze this crypto news headline:

"{title}"

Return ONLY in this exact format:
SUMMARY: (max 20 words)
SENTIMENT: (Bullish / Bearish / Neutral)
REASON: (max 15 words)"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150,
        )

        text    = response.choices[0].message.content
        summary = sentiment = reason = ""

        for line in text.splitlines():
            if line.startswith("SUMMARY:"):
                summary   = line.replace("SUMMARY:", "").strip()
            elif line.startswith("SENTIMENT:"):
                sentiment = line.replace("SENTIMENT:", "").strip()
            elif line.startswith("REASON:"):
                reason    = line.replace("REASON:", "").strip()

        return {"summary": summary, "sentiment": sentiment, "reason": reason}

    except Exception as e:
        logger.warning(f"⚠️ AI error: {e}")
        return {"summary": "", "sentiment": "", "reason": ""}
