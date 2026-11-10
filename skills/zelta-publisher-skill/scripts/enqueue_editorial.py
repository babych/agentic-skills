import os
import sys
import uuid
import time
import json
import argparse
import subprocess

PORTAL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "ai-news-portal"))

def run_d1_query(sql: str) -> dict:
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
        return data[0] if data else {}
    return {}

def enqueue_story(prompt: str, notes: str = None, media_url: str = None, category: str = "ukraine", importance: int = 85) -> str:
    item_id = str(uuid.uuid4())
    now = int(time.time() * 1000)
    
    clean_prompt = prompt.replace("'", "''")
    clean_notes = f"'{notes.replace('\'', '\'\'')}'" if notes else "NULL"
    clean_media = f"'{media_url.replace('\'', '\'\'')}'" if media_url else "NULL"
    clean_cat = category.replace("'", "''")
    
    sql = (
        f"INSERT INTO editorial_queue (id, prompt, context_notes, media_url, category, importance, status, created_at) "
        f"VALUES ('{item_id}', '{clean_prompt}', {clean_notes}, {clean_media}, '{clean_cat}', {importance}, 'pending', {now});"
    )
    run_d1_query(sql)
    return item_id

def list_queue(status: str = None) -> list:
    where_clause = f"WHERE status = '{status}'" if status else ""
    sql = f"SELECT id, prompt, category, importance, status, datetime(created_at/1000, 'unixepoch', 'localtime') as created FROM editorial_queue {where_clause} ORDER BY created_at DESC LIMIT 10;"
    res = run_d1_query(sql)
    return res.get("results", [])

def update_item(item_id: str, category: str = None, status: str = None) -> None:
    updates = []
    if category:
        updates.append(f"category = '{category}'")
    if status:
        updates.append(f"status = '{status}'")
        if status == "pending":
            updates.append("error_message = NULL")
            updates.append("processed_at = NULL")
    if not updates:
        return
    sql = f"UPDATE editorial_queue SET {', '.join(updates)} WHERE id = '{item_id}';"
    run_d1_query(sql)

def main():
    parser = argparse.ArgumentParser(description="Zelta News Editorial Priority Queue Manager")
    parser.add_argument("--prompt", help="Editorial prompt or topic angle to enqueue")
    parser.add_argument("--notes", help="Additional background notes, data, quotes or context")
    parser.add_argument("--media-url", help="Direct URL or site path to primary hero image")
    parser.add_argument("--category", default="ukraine", help="Story category (ukraine, tech, world, celebs, etc.)")
    parser.add_argument("--importance", type=int, default=85, help="Importance score (1-100)")
    parser.add_argument("--list", action="store_true", help="List recent editorial queue items")
    parser.add_argument("--status", help="Filter --list by status (pending, processing, completed, failed)")
    parser.add_argument("--update-id", help="Item ID to update")
    parser.add_argument("--new-category", help="New category for --update-id")
    parser.add_argument("--new-status", help="New status for --update-id (e.g. pending)")
    args = parser.parse_args()

    if args.list:
        items = list_queue(args.status)
        print(f"\nEditorial Queue ({len(items)} items):")
        print(json.dumps(items, indent=2, ensure_ascii=False))
        return

    if args.update_id:
        update_item(args.update_id, category=args.new_category, status=args.new_status)
        print(f"Updated item {args.update_id}: category={args.new_category}, status={args.new_status}")
        return

    if not args.prompt:
        parser.print_help()
        sys.exit(1)

    print(f"Enqueueing editorial story: '{args.prompt[:60]}...'")
    item_id = enqueue_story(
        prompt=args.prompt,
        notes=args.notes,
        media_url=args.media_url,
        category=args.category,
        importance=args.importance
    )
    print("\nSUCCESS: Enqueued for the next scheduled cron cycle.")
    print(f"Queue ID: {item_id}")
    print(f"Category: {args.category}")
    print("Status: pending (will replace generic RSS news on next hourly run)")

if __name__ == "__main__":
    main()
