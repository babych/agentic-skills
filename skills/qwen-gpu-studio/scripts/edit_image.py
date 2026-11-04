import argparse
import asyncio
import json
import os
import sys
import time
import urllib.request
import uuid
import aiohttp

DEFAULT_COMFY_URL = "http://127.0.0.1:8188"
WORKFLOW_TEMPLATE = r"C:\AI_Tools\ComfyUI_Qwen\qwen_image_edit_api.json"

async def edit_image(image_path: str, prompt_text: str, output_path: str = None, comfy_url: str = DEFAULT_COMFY_URL, steps: int = 4, seed: int = None):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image not found: {image_path}")

    if seed is None:
        import random
        seed = random.randint(1, 1000000000)

    # 1. Read input image bytes
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    filename = f"qwen_input_{uuid.uuid4().hex[:8]}_{os.path.basename(image_path)}"

    print(f"[+] Connecting to ComfyUI at {comfy_url}...")
    async with aiohttp.ClientSession() as session:
        # Check server health
        try:
            async with session.get(f"{comfy_url}/system_stats", timeout=5) as resp:
                if resp.status != 200:
                    raise ConnectionError(f"ComfyUI server returned status {resp.status}")
        except Exception as e:
            print(f"[-] Error: Could not connect to ComfyUI server at {comfy_url}. Make sure ComfyUI is running.")
            sys.exit(1)

        # 2. Upload image to ComfyUI
        form = aiohttp.FormData()
        form.add_field('image', img_bytes, filename=filename, content_type='image/png')
        form.add_field('overwrite', 'true')
        print(f"[+] Uploading image '{filename}'...")
        async with session.post(f"{comfy_url}/upload/image", data=form) as upload_resp:
            if upload_resp.status != 200:
                raise RuntimeError(f"Failed to upload image: {await upload_resp.text()}")

        # 3. Load workflow template
        with open(WORKFLOW_TEMPLATE, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        # 4. Inject parameters
        workflow["1"]["inputs"]["image"] = filename
        workflow["16"]["inputs"]["prompt"] = prompt_text
        workflow["3"]["inputs"]["steps"] = steps
        workflow["3"]["inputs"]["noise_seed"] = seed

        client_id = str(uuid.uuid4())
        payload = {"prompt": workflow, "client_id": client_id}

        print(f"[+] Submitting prompt: '{prompt_text}' (Steps: {steps}, Seed: {seed})...")
        async with session.post(f"{comfy_url}/prompt", json=payload) as prompt_resp:
            prompt_data = await prompt_resp.json()
            if "prompt_id" not in prompt_data:
                raise RuntimeError(f"Prompt failed: {prompt_data}")
            prompt_id = prompt_data["prompt_id"]
            print(f"[+] Queued task ID: {prompt_id}")

        # 5. Poll for completion
        print("[+] Processing image (running Qwen-Image-Edit DiT)...")
        start_time = time.time()
        output_filename = None
        while True:
            await asyncio.sleep(2)
            async with session.get(f"{comfy_url}/history/{prompt_id}") as hist_resp:
                hist = await hist_resp.json()
                if prompt_id in hist:
                    task_info = hist[prompt_id]
                    # Check for errors
                    if "status" in task_info and task_info["status"].get("status_str") == "error":
                        raise RuntimeError(f"Execution error: {task_info['status'].get('messages')}")
                    
                    outputs = task_info.get("outputs", {})
                    for nid, out in outputs.items():
                        if "images" in out and len(out["images"]) > 0:
                            output_filename = out["images"][0]["filename"]
                            break
                    if output_filename:
                        break

            elapsed = int(time.time() - start_time)
            print(f"    Elapsed: {elapsed}s...", end="\r")

        print(f"\n[+] Generation completed in {int(time.time() - start_time)}s! Output image: {output_filename}")

        # 6. Download resulting image
        if not output_path:
            output_dir = os.path.dirname(os.path.abspath(image_path))
            output_path = os.path.join(output_dir, f"edited_{os.path.basename(image_path)}")

        async with session.get(f"{comfy_url}/view?filename={output_filename}") as img_resp:
            result_bytes = await img_resp.read()
            with open(output_path, "wb") as out_f:
                out_f.write(result_bytes)

        print(f"[+] Saved edited image to: {output_path}")
        return output_path

def main():
    parser = argparse.ArgumentParser(description="Edit image using local Qwen-Image-Edit ComfyUI API")
    parser.add_argument("--image", "-i", required=True, help="Path to input image")
    parser.add_argument("--prompt", "-p", required=True, help="Editing instruction (prompt)")
    parser.add_argument("--output", "-o", default=None, help="Path to save edited output image")
    parser.add_argument("--steps", "-s", type=int, default=4, help="Sampling steps (default: 4)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--url", default=DEFAULT_COMFY_URL, help="ComfyUI server URL")

    args = parser.parse_args()
    asyncio.run(edit_image(args.image, args.prompt, args.output, args.url, args.steps, args.seed))

if __name__ == "__main__":
    main()
