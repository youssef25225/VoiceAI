import requests
import os

HF_TOKEN = os.getenv("HF_TOKEN")

SYSTEM_PROMPT = """أنت مساعد صوتي اسمك بوسف، شاب مصري من إسكندرية.
ردودك قصيرة جداً وطبيعية زي البشر.
بتتكلم عامية مصرية بس، جمل 1-2 سطر، بدون فصحى."""


def build_prompt(history: list) -> str:
    prompt = f"<s>[INST] {SYSTEM_PROMPT} [/INST] أهلاً </s>"
    for msg in history[-6:]:
        role = msg.get("role", "")
        content = msg.get("content", "").strip()
        if not content:
            continue
        if role == "user":
            prompt += f"[INST] {content} [/INST] "
        elif role == "assistant":
            prompt += f"{content} </s>"
    return prompt


def generate_full(history: list) -> str:
    if not HF_TOKEN:
        return "مفيش توكن يا معلم"

    prompt = build_prompt(history)

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 100,
            "temperature": 0.7,
            "do_sample": True,
            "return_full_text": False,
        }
    }

    try:
        r = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            json=payload,
            timeout=60
        )
    except requests.exceptions.Timeout:
        return "الشبكة بطيئة يا معلم"
    except requests.exceptions.ConnectionError:
        return "مش قادر أتصل"

    if r.status_code == 503:
        return "النموذج بيتحمل، استنى شوية وجرب تاني"
    
    if r.status_code == 429:
        return "في ضغط على السيرفر، جرب تاني بعد شوية"

    if r.status_code != 200:
        return f"غلطة {r.status_code}: {r.text[:100]}"

    data = r.json()

    if isinstance(data, list) and data:
        text = data[0].get("generated_text", "").strip()
    elif isinstance(data, dict):
        text = data.get("generated_text", "").strip()
    else:
        return "مفيش رد"

    # امسح أي حاجة بعد [INST]
    if "[INST]" in text:
        text = text[:text.index("[INST]")].strip()

    return text or "مش فاهم، ممكن تعيد؟"
