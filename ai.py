"""
ai.py - OpenAI integration
غير للأخبار المهمة باش نوفرو التكلفة
"""

import logging
from config import OPENAI_API_KEY

logger = logging.getLogger("cryptobot")

def generate_ai_insight(title: str) -> dict:
    """تحليل الخبر — يرجع summary + sentiment + reason"""
    empty = {"summary": "", "sentiment": "", "reason": ""}

    if not OPENAI_API_KEY:
        return empty

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""Analyze this crypto news headline:
"{title}"

Return ONLY in this exact format (no extra text):
SUMMARY: (max 20 words)
SENTIMENT: (Bullish / Bearish / Neutral)
REASON: (max 15 words)"""
            }],
            temperature=0.3,
            max_tokens=120,
        )

        text      = response.choices[0].message.content
        summary   = sentiment = reason = ""

        for line in text.splitlines():
            line = line.strip()
            if line.startswith("SUMMARY:"):
                summary   = line[8:].strip()
            elif line.startswith("SENTIMENT:"):
                sentiment = line[10:].strip()
            elif line.startswith("REASON:"):
                reason    = line[7:].strip()

        return {"summary": summary, "sentiment": sentiment, "reason": reason}

    except Exception as e:
        logger.warning(f"⚠️ AI error: {e}")
        return empty
