#!/usr/bin/env python3
"""
vision_evaluator.py: Audits extracted illustrations, filters out lines/noise/letters,
and generates authentic Ukrainian captions via Gemini Flash Lite Vision.
"""
import sys, os, json, base64, time, urllib.request
from PIL import Image
import io

sys.stdout.reconfigure(encoding='utf-8')

API_KEY = os.environ.get('GEMINI_API_KEY')
MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

def evaluate_image(img_path, context=""):
    with Image.open(img_path) as im:
        im = im.convert("RGB")
        im.thumbnail((512, 512), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=80)
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    prompt = f"""Ти — науковий редактор книги. Оціни це зображення (біля тексту: "{context[:150]}"):
1. Чи це справжня ілюстрація (фотографія, креслення, анатомічна схема)?
   ВІДХИЛИ (is_valid: false), якщо це: пусте місце, випадкова лінія, обрізана літера або розмитий зріз.
2. Якщо справжня (is_valid: true):
   - Склади точний, стислий український підпис (caption_ua).
   - Визнач тему/термін (topic).

Відповідай ВИКЛЮЧНО JSON:
{{
  "is_valid": true_або_false,
  "reject_reason": "чому відхилено",
  "caption_ua": "підпис українською",
  "topic": "назва розділу чи статті"
}}"""

    for m in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}, {"inlineData": {"mimeType": "image/jpeg", "data": img_b64}}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                cand = data.get('candidates', [{}])[0]
                text = cand.get('content', {}).get('parts', [{}])[0].get('text', '')
                return json.loads(text)
        except Exception:
            continue
    return {"is_valid": False, "reject_reason": "API error"}
