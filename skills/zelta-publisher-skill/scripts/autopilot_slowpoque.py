import os
import sys
import json
import time
import argparse
import subprocess
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta

PORTAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "ai-news-portal"))
STATE_FILE = os.path.join(os.path.dirname(__file__), "autopilot_state.json")
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "slowpoque_config.json")

KYIV_TZ = timezone(timedelta(hours=2))

def get_kyiv_today_str() -> str:
    return datetime.now(KYIV_TZ).strftime("%Y-%m-%d")

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_post_date": None,
        "last_post_id": None,
        "posted_article_ids": [],
        "target_account": "@slowpoque618",
        "threads_user_id": "40528597693420809"
    }

def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def load_credentials() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def run_d1_query(sql: str) -> list:
    escaped_sql = sql.replace('"', '\\"')
    cmd = f'npx wrangler d1 execute pulsepress-news-db --remote --command "{escaped_sql}"'
    proc = subprocess.run(
        cmd,
        cwd=PORTAL_DIR,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Wrangler D1 execution failed: {proc.stderr or proc.stdout}")

    stdout = proc.stdout
    json_start = stdout.find("[")
    json_end = stdout.rfind("]")
    if json_start != -1 and json_end != -1:
        raw_json = stdout[json_start:json_end + 1]
        data = json.loads(raw_json)
        if data and "results" in data[0]:
            return data[0]["results"]
    return []

def get_candidates(limit: int = 10) -> list:
    since_ts = int((time.time() - 86400 * 2) * 1000)
    sql = (
        f"SELECT a.id, a.importance_score, a.image_url, a.created_at, t.title, t.summary, t.content_md "
        f"FROM articles a JOIN article_translations t ON a.id = t.article_id "
        f"WHERE t.lang_code = 'uk' AND a.created_at >= {since_ts} "
        f"ORDER BY a.importance_score DESC, a.created_at DESC LIMIT {limit};"
    )
    return run_d1_query(sql)

def synthesize_analytical_take(title: str, summary: str, content: str = "") -> str:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            prompt_instruction = (
                "Ти — аналітик, який веде особистий мікроблог у Threads (@slowpoque618). "
                "Твій стиль: сухий, логічний, фактологічний, розбір причин і наслідків. "
                "КАТЕГОРИЧНО ЗАБОРОНЕНО: вітання на кшталт 'Slowpoque на зв'язку', клікбейт, пусті емоції, посилання чи URL. "
                "Вимоги: "
                "1. Рівно 3 короткі абзаци (хук із суттю -> конкретні цифри/факти -> аналітичний висновок/наслідок). "
                "2. Загальна довжина: від 320 до 450 символів (максимум 480). "
                "3. Без жодних лінків чи хештегів. "
                f"Новина:\nЗаголовок: {title}\nСуть: {summary}\nДеталі: {content[:1000]}"
            )
            body = {
                "contents": [{"parts": [{"text": prompt_instruction}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300}
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                clean_lines = [line.strip() for line in text.split("\n") if line.strip() and not line.strip().startswith("http")]
                clean_text = "\n\n".join(clean_lines)
                if len(clean_text) <= 500:
                    return clean_text
        except Exception:
            pass

    first_sentence = summary.split(". ")[0].strip()
    if not first_sentence.endswith("."):
        first_sentence += "."
    body_part = summary[len(first_sentence):].strip()
    if not body_part:
        body_part = summary

    formatted = f"{title}.\n\n{body_part}\n\nСухі факти без зайвого шуму."
    if len(formatted) > 490:
        formatted = f"{title}.\n\n{body_part[:400].rsplit('.', 1)[0]}."
    return formatted[:495]

def publish_to_threads(token: str, user_id: str, text: str, image_url: str = None) -> dict:
    safe_text = text[:500]
    create_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    publish_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"

    container_id = None
    if image_url and (image_url.startswith("http://") or image_url.startswith("https://")):
        params = urllib.parse.urlencode({
            "media_type": "IMAGE",
            "image_url": image_url,
            "text": safe_text,
            "access_token": token
        })
        req = urllib.request.Request(create_url, data=params.encode("utf-8"), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                container_id = data.get("id")
                time.sleep(2)
        except Exception:
            container_id = None

    if not container_id:
        params = urllib.parse.urlencode({
            "media_type": "TEXT",
            "text": safe_text,
            "access_token": token
        })
        req = urllib.request.Request(create_url, data=params.encode("utf-8"), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                container_id = data.get("id")
                time.sleep(2)
        except urllib.error.HTTPError as e:
            return {"ok": False, "error": e.read().decode("utf-8")}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    if not container_id:
        return {"ok": False, "error": "Failed to create Threads container"}

    pub_params = urllib.parse.urlencode({
        "creation_id": container_id,
        "access_token": token
    })
    pub_req = urllib.request.Request(publish_url, data=pub_params.encode("utf-8"), method="POST")
    try:
        with urllib.request.urlopen(pub_req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"ok": True, "id": data.get("id")}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": e.read().decode("utf-8")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def pick_top_story(state: dict) -> dict:
    candidates = get_candidates(limit=10)
    posted_ids = set(state.get("posted_article_ids", []))
    for c in candidates:
        if c["id"] not in posted_ids:
            return c
    return candidates[0] if candidates else None

def main():
    parser = argparse.ArgumentParser(description="Threads Slowpoque Daily Autopilot")
    parser.add_argument("--run", action="store_true", help="Execute daily autopilot run")
    parser.add_argument("--preview", action="store_true", help="Preview candidate selection and rewrite without posting")
    parser.add_argument("--force", action="store_true", help="Force publish today even if already posted")
    parser.add_argument("--status", action="store_true", help="Display autopilot status and eligibility")
    args = parser.parse_args()

    state = load_state()
    creds = load_credentials()
    today_str = get_kyiv_today_str()

    already_posted_today = (state.get("last_post_date") == today_str)

    if args.status or (not args.run and not args.preview and not args.force):
        candidate = pick_top_story(state)
        print("=== THREADS SLOWPOQUE AUTOPILOT STATUS ===")
        print(f"Target Account:     {state.get('target_account', '@slowpoque618')}")
        print(f"Today (Kyiv):       {today_str}")
        print(f"Last Post Date:     {state.get('last_post_date')}")
        print(f"Last Post ID:       {state.get('last_post_id')}")
        print(f"Posted History:     {len(state.get('posted_article_ids', []))} articles")
        print(f"Already Posted:     {'YES (Today is completed)' if already_posted_today else 'NO (Eligible for run)'}")
        if candidate:
            print(f"\nNext Top Candidate:\n  ID:    {candidate['id']}\n  Score: {candidate['importance_score']}\n  Title: {candidate['title']}")
        return

    candidate = pick_top_story(state)
    if not candidate:
        print("No story candidate found in the last 48 hours.")
        return

    text = synthesize_analytical_take(candidate["title"], candidate["summary"], candidate.get("content_md", ""))

    if args.preview:
        print("=== AUTOPILOT CANDIDATE PREVIEW ===")
        print(f"Candidate ID:   {candidate['id']}")
        print(f"Score:          {candidate['importance_score']}")
        print(f"Original Title: {candidate['title']}")
        print(f"Image URL:      {candidate['image_url']}")
        print(f"Character Count:{len(text)}")
        print("\n--- GENERATED THREADS POST ---")
        print(text)
        print("-------------------------------")
        return

    if already_posted_today and not args.force:
        print(f"Notice: Autopilot already ran today ({today_str}). Today is completed.")
        print(f"Last Post ID: {state.get('last_post_id')}")
        print("Use --force if you wish to override the once-daily limit.")
        return

    token = creds.get("access_token")
    user_id = creds.get("user_id") or creds.get("threads_user_id")
    if not token or not user_id:
        print("Error: Missing credentials in slowpoque_config.json", file=sys.stderr)
        sys.exit(1)

    print(f"Publishing top candidate '{candidate['title'][:50]}...' to {state.get('target_account', '@slowpoque618')}...")
    res = publish_to_threads(token, user_id, text, candidate.get("image_url"))

    if res.get("ok"):
        post_id = res.get("id")
        print(f"Success! Published post ID: {post_id}")
        state["last_post_date"] = today_str
        state["last_post_id"] = post_id
        if candidate["id"] not in state["posted_article_ids"]:
            state["posted_article_ids"].append(candidate["id"])
        save_state(state)
        print("Autopilot state successfully updated.")
    else:
        print(f"Failed to publish: {res.get('error')}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
