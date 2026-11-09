import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.error

DEFAULT_WORKER_ENDPOINT = "https://ai-news-portal.memory1024.workers.dev/broadcast-short"

def broadcast_via_worker(
    text: str,
    image_url: str = None,
    image_base64: str = None,
    threads_text: str = None,
    bluesky_text: str = None,
    worker_url: str = DEFAULT_WORKER_ENDPOINT
) -> dict:
    payload = {
        "text": text,
        "image_url": image_url,
        "image_base64": image_base64,
        "threads_text": threads_text or text[:490],
        "bluesky_text": bluesky_text or text[:290]
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
    args = parser.parse_args()

    image_base64 = None
    if args.image_path:
        if not os.path.exists(args.image_path):
            print(f"Error: image file not found at {args.image_path}", file=sys.stderr)
            sys.exit(1)
        with open(args.image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

    print(f"Broadcasting to Zelta News social network via {args.worker_url}...")
    res = broadcast_via_worker(
        text=args.text,
        image_url=args.image_url,
        image_base64=image_base64,
        threads_text=args.threads_text,
        bluesky_text=args.bluesky_text,
        worker_url=args.worker_url
    )
    print("\n--- BROADCAST RESULT ---")
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
