import os
import sys
import json
import argparse
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

def escape_telegram_markdown(text: str) -> str:
    reserved = r"_*[]()~`>#+-=|{}.!\""
    res = ""
    for char in text:
        if char in reserved:
            res += f"\\{char}"
        else:
            res += char
    return res

def post_to_telegram(bot_token: str, chat_id: str, text: str, image_url: str = None) -> dict:
    if not bot_token or not chat_id:
        return {"status": "skipped", "reason": "missing credentials"}
    
    if image_url:
        endpoint = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": escape_telegram_markdown(text),
            "parse_mode": "MarkdownV2"
        }
    else:
        endpoint = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": escape_telegram_markdown(text),
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": False
        }
    
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return {"status": "ok", "response": json.loads(resp.read().decode("utf-8"))}
    except urllib.error.HTTPError as e:
        return {"status": "error", "code": e.code, "message": e.read().decode("utf-8")}

def post_to_bluesky(handle: str, app_password: str, text: str, image_url: str = None) -> dict:
    if not handle or not app_password:
        return {"status": "skipped", "reason": "missing credentials"}
    
    session_req = urllib.request.Request(
        "https://bsky.social/xrpc/com.atproto.server.createSession",
        data=json.dumps({"identifier": handle, "password": app_password}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(session_req) as resp:
            session_data = json.loads(resp.read().decode("utf-8"))
            access_jwt = session_data["accessJwt"]
            did = session_data["did"]
    except urllib.error.HTTPError as e:
        return {"status": "error", "stage": "auth", "message": e.read().decode("utf-8")}

    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    }

    post_req = urllib.request.Request(
        "https://bsky.social/xrpc/com.atproto.repo.createRecord",
        data=json.dumps({
            "repo": did,
            "collection": "app.bsky.feed.post",
            "record": record
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_jwt}"
        }
    )
    try:
        with urllib.request.urlopen(post_req) as resp:
            return {"status": "ok", "response": json.loads(resp.read().decode("utf-8"))}
    except urllib.error.HTTPError as e:
        return {"status": "error", "stage": "createRecord", "message": e.read().decode("utf-8")}

def post_to_threads(token: str, user_id: str, text: str, image_url: str = None) -> dict:
    if not token or not user_id:
        return {"status": "skipped", "reason": "missing credentials"}
    
    create_url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    publish_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
    
    container_id = None
    if image_url:
        params = urllib.parse.urlencode({
            "media_type": "IMAGE",
            "image_url": image_url,
            "text": text,
            "access_token": token
        }).encode("utf-8")
        req = urllib.request.Request(create_url, data=params, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                container_id = res_data.get("id")
        except urllib.error.HTTPError:
            container_id = None
    
    if not container_id:
        params = urllib.parse.urlencode({
            "media_type": "TEXT",
            "text": text,
            "access_token": token
        }).encode("utf-8")
        req = urllib.request.Request(create_url, data=params, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                container_id = res_data.get("id")
        except urllib.error.HTTPError as e:
            return {"status": "error", "stage": "create_container", "message": e.read().decode("utf-8")}
    
    import time
    time.sleep(2)

    pub_params = urllib.parse.urlencode({
        "creation_id": container_id,
        "access_token": token
    }).encode("utf-8")
    pub_req = urllib.request.Request(publish_url, data=pub_params, method="POST")
    try:
        with urllib.request.urlopen(pub_req) as resp:
            return {"status": "ok", "response": json.loads(resp.read().decode("utf-8"))}
    except urllib.error.HTTPError as e:
        return {"status": "error", "stage": "publish", "message": e.read().decode("utf-8")}

def post_to_facebook(page_token: str, page_id: str, text: str, image_url: str = None) -> dict:
    if not page_token or not page_id:
        return {"status": "skipped", "reason": "missing credentials"}
    
    if image_url:
        endpoint = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        params = urllib.parse.urlencode({
            "url": image_url,
            "caption": text,
            "published": "true",
            "access_token": page_token
        }).encode("utf-8")
    else:
        endpoint = f"https://graph.facebook.com/v19.0/{page_id}/feed"
        params = urllib.parse.urlencode({
            "message": text,
            "access_token": page_token
        }).encode("utf-8")
    
    req = urllib.request.Request(endpoint, data=params, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return {"status": "ok", "response": json.loads(resp.read().decode("utf-8"))}
    except urllib.error.HTTPError as e:
        return {"status": "error", "code": e.code, "message": e.read().decode("utf-8")}

def main():
    parser = argparse.ArgumentParser(description="Zelta News Direct Multi-Channel Social Broadcast")
    parser.add_argument("--text", required=True, help="Post content / commentary")
    parser.add_argument("--image-url", default=None, help="Optional image URL")
    parser.add_argument("--tg-token", default=os.getenv("TELEGRAM_BOT_TOKEN"))
    parser.add_argument("--tg-chat", default=os.getenv("TELEGRAM_CHAT_ID"))
    parser.add_argument("--bsky-handle", default=os.getenv("BLUESKY_HANDLE", "zeltanews.com"))
    parser.add_argument("--bsky-password", default=os.getenv("BLUESKY_APP_PASSWORD"))
    parser.add_argument("--threads-token", default=os.getenv("THREADS_ACCESS_TOKEN"))
    parser.add_argument("--threads-user-id", default=os.getenv("THREADS_USER_ID", "39837470959232272"))
    parser.add_argument("--fb-token", default=os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN"))
    parser.add_argument("--fb-page-id", default=os.getenv("FACEBOOK_PAGE_ID", "1437499976110623"))
    args = parser.parse_args()

    results = {}
    print("Broadcasting to Telegram...")
    results["telegram"] = post_to_telegram(args.tg_token, args.tg_chat, args.text, args.image_url)

    print("Broadcasting to Bluesky...")
    results["bluesky"] = post_to_bluesky(args.bsky_handle, args.bsky_password, args.text, args.image_url)

    print("Broadcasting to Threads...")
    results["threads"] = post_to_threads(args.threads_token, args.threads_user_id, args.text, args.image_url)

    print("Broadcasting to Facebook...")
    results["facebook"] = post_to_facebook(args.fb_token, args.fb_page_id, args.text, args.image_url)

    print("\n--- BROADCAST SUMMARY ---")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
