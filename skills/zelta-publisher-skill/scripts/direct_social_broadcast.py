import os
import sys
import json
import time
import base64
import argparse
import urllib.request
import urllib.error
import urllib.parse

DEFAULT_WORKER_ENDPOINT = "https://ai-news-portal.memory1024.workers.dev/broadcast-short"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "slowpoque_config.json")

def load_slowpoque_credentials():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def strip_link_blocks(text: str) -> str:
    if not text:
        return ""
    lines = text.split("\n")
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if stripped.startswith("http://") or stripped.startswith("https://") or stripped.startswith("👉"):
            continue
        if any(domain in lower for domain in ["zeltanews.com", "t.me/", "threads.net", "facebook.com", "bsky.app"]):
            continue
        if any(lower.startswith(prefix) for prefix in ["посилання", "читати", "деталі", "детальніше", "повний аналіз", "аналітика", "read more", "read full"]):
            continue
        clean_lines.append(line)
    result = "\n".join(clean_lines)
    import re
    result = re.sub(r'https?://\S+', '', result)
    result = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', result)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()

def publish_to_threads_direct(token: str, user_id: str, text: str, image_url: str = None) -> dict:
    safe_text = strip_link_blocks(text)[:500]
    create_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    publish_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"

    container_id = None
    if image_url:
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
                if container_id:
                    for _ in range(6):
                        time.sleep(2)
                        status_url = f"https://graph.threads.net/v1.0/{container_id}?fields=status,error_message&access_token={token}"
                        try:
                            s_req = urllib.request.Request(status_url)
                            with urllib.request.urlopen(s_req, timeout=15) as s_resp:
                                s_data = json.loads(s_resp.read().decode("utf-8"))
                                if s_data.get("status") == "FINISHED":
                                    break
                                if s_data.get("status") == "ERROR":
                                    container_id = None
                                    break
                        except Exception:
                            pass
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

def broadcast_via_worker(
    text: str,
    image_url: str = None,
    image_base64: str = None,
    threads_text: str = None,
    bluesky_text: str = None,
    worker_url: str = DEFAULT_WORKER_ENDPOINT
) -> dict:
    clean_text = strip_link_blocks(text)
    clean_threads = strip_link_blocks(threads_text or text)[:490]
    clean_bluesky = strip_link_blocks(bluesky_text or text)[:290]
    payload = {
        "text": clean_text,
        "image_url": image_url,
        "image_base64": image_base64,
        "threads_text": clean_threads,
        "bluesky_text": clean_bluesky
    }
    req = urllib.request.Request(
        worker_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": e.read().decode("utf-8")}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Zelta News Direct Multi-Channel Social Broadcast")
    parser.add_argument("--text", required=True, help="Post content / commentary")
    parser.add_argument("--image-url", default=None, help="Optional image URL (public HTTP/HTTPS)")
    parser.add_argument("--image-path", default=None, help="Optional local image file path to upload and broadcast")
    parser.add_argument("--threads-text", default=None, help="Optional custom text for Threads (<500 chars)")
    parser.add_argument("--bluesky-text", default=None, help="Optional custom text for Bluesky (<300 chars)")
    parser.add_argument("--worker-url", default=DEFAULT_WORKER_ENDPOINT, help="Cloudflare Worker broadcast endpoint")
    parser.add_argument("--target", choices=["all", "slowpoque", "main"], default="all", help="Target profile: slowpoque (manual analysis), main (default worker channels), or all")
    args = parser.parse_args()

    image_base64 = None
    if args.image_path:
        if not os.path.exists(args.image_path):
            print(f"Error: image file not found at {args.image_path}", file=sys.stderr)
            sys.exit(1)
        with open(args.image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

    results = {}

    if args.target in ["all", "main"]:
        print(f"Broadcasting to main Zelta News social network via {args.worker_url}...")
        worker_res = broadcast_via_worker(
            text=args.text,
            image_url=args.image_url,
            image_base64=image_base64,
            threads_text=args.threads_text,
            bluesky_text=args.bluesky_text,
            worker_url=args.worker_url
        )
        results["main_channels"] = worker_res

    if args.target in ["all", "slowpoque"]:
        creds = load_slowpoque_credentials()
        th_user_id = creds.get("user_id") or creds.get("threads_user_id") if creds else None
        if creds and creds.get("access_token") and th_user_id:
            print("Publishing analytical take to @slowpoque618 on Threads...")
            th_text = args.threads_text or args.text
            th_res = publish_to_threads_direct(
                token=creds["access_token"],
                user_id=th_user_id,
                text=th_text,
                image_url=args.image_url
            )
            results["slowpoque_threads"] = th_res
        else:
            if args.target == "slowpoque":
                print("Error: slowpoque credentials not found in slowpoque_config.json", file=sys.stderr)
                sys.exit(1)

    print("\n--- BROADCAST RESULT ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
