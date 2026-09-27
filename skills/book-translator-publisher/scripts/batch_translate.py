#!/usr/bin/env python3
"""
batch_translate.py: Robust chunked book translation using Gemini Flash Lite.
"""
import sys, os, json, time, urllib.request

sys.stdout.reconfigure(encoding='utf-8')

API_KEY = os.environ.get('GEMINI_API_KEY')
MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

def translate_chunk(chunk_text, glossary=None):
    glossary_instr = ""
    if glossary:
        glossary_instr = "Обов'язковий глосарій термінів:\n" + "\n".join(f"- {k} -> {v}" for k, v in glossary.items())

    prompt = f"""Переклади наступний уривок наукової/історичної книги українською мовою.
Зберігай стиль оригінального автора, фахову термінологію та розмітку.
{glossary_instr}

Текст для перекладу:
{chunk_text}"""

    for m in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                cand = data.get('candidates', [{}])[0]
                return cand.get('content', {}).get('parts', [{}])[0].get('text', '')
        except Exception:
            time.sleep(2)
    raise RuntimeError("Translation retries exhausted")
