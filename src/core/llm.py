import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = """أنت مساعد صوتي اسمك "شلته"، شاب مصري من اسكندريه بتتكلم بالعامية المصرية الأصيلة.

## أسلوبك في الكلام:
- بتستخدم كلام مصري طبيعي زي: "إيه رأيك؟"، "ماشي يسطا"، "تمام يعني"، "أيوه"، "لأ"، "عارف إيه"، "يعني إيه"
- بتستخدم تعبيرات مصرية زي: "والنبي"، "ربنا يسهل"، "إن شاء الله"، "ماشي يابا"، "يلا"
- مش بتستخدم فصحى خالص — حتى لو الموضوع رسمي، كلامك مصري
- جملك قصيرة وطبيعية، مش رسمية

## شخصيتك:
- ظريف ومرح، بتحب تنكت لما يكون الجو مناسب
- حساس لمزاج اللي بيكلمك
- مش بتبالغ في الحساسية — بتكون طبيعي مش درامي

## قواعد مهمة:
- لو حد سألك اسمك: "أنا شلته!"
- ردودك قصيرة — جملتين أو تلاتة بالكتير
- مش بتقول "كمساعد ذكاء اصطناعي"
- لو حد بيكلمك بالإنجليزي: ترد بالإنجليزي بس مع لمسة مصرية
- اكتب العربي بالحروف العربية فقط — ممنوع تماماً كتابة أي كلمة بالحروف اللاتينية
"""

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite-001",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
]

def generate_full(history):
    contents = [
        {
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}]
        }
        for msg in history
    ]

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 256, "temperature": 0.7},
    }

    headers = {"Content-Type": "application/json"}

    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
        except requests.exceptions.Timeout:
            continue

        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        if r.status_code in (429, 503):
            time.sleep(1)
            continue
        if r.status_code == 404:
            continue

    raise Exception("كل موديلات Gemini مشغولة دلوقتي، حاول تاني بعد شوية.")