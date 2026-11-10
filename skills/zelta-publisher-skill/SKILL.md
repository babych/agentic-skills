---
name: zelta-publisher-skill
description: "Autonomous news & social publishing skill for Zelta News (zeltanews.com). Distinguishes short Twitter/X takes (pure social broadcast with NO website links to maximize organic reach) from full news stories (5-language website article insertion in Cloudflare D1 + Google Indexing API + multi-channel syndication)."
---

# ⚡ Zelta Publisher Skill (`zelta-publisher-skill`)

Autonomous publishing intelligence for **Zelta News** (`https://zeltanews.com`) and its multi-channel social syndication network (Telegram, Bluesky, Threads, Facebook).

---

## 🧭 Operational Modes

When the user provides a news snippet, tweet, screenshot, or URL, evaluate the intent and select the appropriate mode:

```
                  User provides context
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
[Mode 1: Short Take / X Quote]      [Mode 2: Editorial Priority Queue]
- User pastes a tweet, quote,       - User provides topic, prompt, or
  short update, or says "пости        request for zeltanews.com
  без лінку / короткий твіт"        - Enqueues to D1 `editorial_queue`
- NO website article created        - Consumed on NEXT HOURLY CRON run
- Direct broadcast across social      instead of generic internet news
  channels for viral organic reach  - 5-language story + Google Indexing
```

---

## 🚀 Mode 1: Short Take / Twitter / X Quote (No Site Link)

### Core Principle
Social platform algorithms (Threads, Bluesky, Facebook) significantly suppress reach when a post contains external outbound links. Mode 1 publishes pure native content with zero outbound links, maximizing impressions and virality.

### Formatting Guidelines
- **Headline / Hook**: 1 punchy line in bold (Telegram Markdown: `*...*`).
- **Body**: 2 to 4 concise bullet points or short paragraphs delivering the essence, exact figures, and context.
- **Tone**: Pragmatic, direct, authoritative shop talk (zero AI clichés like "варто зазначити", "знаменує нову еру", "a game changer").
- **Hashtags**: 2–3 targeted tags at the end (e.g. `#новини #геополітика #технології`).
- **Media**: If the user provided an image, attachment, or direct image URL, include it in the broadcast.

### Broadcast Execution
Run the bundled script `scripts/direct_social_broadcast.py`:

```powershell
python C:\Users\Dmytro\source\repos\Github\agentic-skills\skills\zelta-publisher-skill\scripts\direct_social_broadcast.py `
  --text "🔥 Президент США оголосив про новий пакет допомоги...`n`nДеталі..." `
  --image-path "C:\path\to\local_image.jpg" # або --image-url "https://example.com/photo.jpg"
```

---

## 📰 Mode 2: Editorial Priority Queue (Cron-Driven Replacement of Generic News)

### Core Principle
By default, the Cloudflare Worker runs an autonomous cron job every hour (`0 * * * *`) that picks generic news from RSS feeds.
When the user invokes `/zelta-publisher-skill` with a story topic or question, it adds it to the **Editorial Priority Queue** (`editorial_queue` in D1).

On the next cron trigger:
1. The worker detects the pending queue item before any RSS feeds.
2. It generates a full-length, authoritative 5-language investigation (`uk`, `en`, `pl`, `de`, `es`) with concrete numbers, facts, and structure.
3. Media is attached (or Wikimedia resolved).
4. Persisted to D1 and marked `completed`.
5. Google Indexing API pinged (< 1s) and syndicated across social channels.

### Enqueue Execution
Run `scripts/enqueue_editorial.py`:

```powershell
python C:\Users\Dmytro\source\repos\Github\agentic-skills\skills\zelta-publisher-skill\scripts\enqueue_editorial.py `
  --prompt "В Україні медіанний щомісячний платіж за іпотекою у 2026 році становить 13 000 – 18 300 грн. Навіщо аренди по 30к?" `
  --notes "єОселя 3% і 7%, порівняння витрат на оренду та володіння житлом" `
  --category "ukraine" `
  --importance 88
```

To view current queue status:
```powershell
python C:\Users\Dmytro\source\repos\Github\agentic-skills\skills\zelta-publisher-skill\scripts\enqueue_editorial.py --list
```

If specific credentials are needed from the vault:
```powershell
# Retrieve tokens via vault-skill if required:
# python C:\Users\Dmytro\.gemini\config\skills\vault-skill\vault_manager.py describe <KEY>
```

---

## 📰 Mode 2: Full Editorial Story (Website + Indexing + Syndication)

### Step 1: Autonomous Content Generation
Generate complete bilingual or 5-language story payloads:
- **Languages**: Ukrainian (`uk`), English (`en`), Polish (`pl`), German (`de`), Spanish (`es`).
- **Fields**: `slug`, `title`, `summary`, `content_md`, `seo_title`, `seo_description`, `tags`, `social_hook`.
- **User-Provided Original Visuals (STRICT RULE)**:
  - If the user provides an image, infographic, or map screenshot, **ALWAYS use it as the primary evidence**:
    1. Save the image to `public/images/` and host it directly on the site CDN.
    2. Set `image_url` of the article to the authentic provided image/crop.
    3. **Embed the image directly into `content_md`** across all languages (`![Description](/images/...)`) with an explanatory caption.
  - Never replace user-provided authentic maps/evidence with generic stock photos from Wikimedia.
- **Image Fallback**: If no user image is provided, use high-res editorial photo with 1280px optimized thumbnail.

### Step 2: Cloudflare D1 Database Insertion
Insert into `pulsepress-news-db` using `npx wrangler d1 execute`:

```bash
cd c:\Users\Dmytro\source\repos\Github\ai-news-portal
npx wrangler d1 execute pulsepress-news-db --remote --command "INSERT INTO articles (id, slug, image_url, image_source, category, importance, created_at, published_at, translations_json) VALUES (...)"
```

### Step 3: Google Indexing API Instant Notification
Notify Googlebot in < 1s using the service account WebCrypto JWT:
- Targeted URLs: `https://zeltanews.com/uk/news/<slug>`, `https://zeltanews.com/en/news/<slug>`, etc.

### Step 4: Social Distribution with Link Protection
- **Telegram**: Formatted Markdown message with bold title, hook, and button/link.
- **Threads**: Main image/text post without link; URL posted in the immediate reply comment.
- **Facebook**: Photo post with caption; URL posted in the immediate first comment.
- **Bluesky**: Rich-text post with embedded link facet and card preview.

---

## 🛡️ Security & Zero-Leak Standards
1. **Never print plain-text tokens** in chat, summaries, or commit logs.
2. Store all persistent keys in `vault-skill` or Cloudflare Worker environment secrets.
3. Keep changes atomic and test all social endpoints before mass distribution.
