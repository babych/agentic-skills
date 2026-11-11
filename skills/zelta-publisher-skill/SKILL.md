---
name: zelta-publisher-skill
description: "Autonomous news & social publishing skill for Zelta News (zeltanews.com). Distinguishes short Twitter/X takes (pure social broadcast with NO website links to maximize organic reach) from full news stories (5-language website article insertion in Cloudflare D1 + Google Indexing API + multi-channel syndication)."
---

# ⚡ Zelta Publisher Skill (`zelta-publisher-skill`)

Autonomous publishing intelligence for **Zelta News** (`https://zeltanews.com`) and its multi-channel social syndication network (Telegram, Bluesky, Threads, Facebook).

---

## 🚫 STRICT ZERO-LINKS POLICY ACROSS ALL SOCIAL NETWORKS

**MANDATORY ALGORITHMIC REACH STANDARD**:
- **NEVER** include outbound links, URLs, domain mentions (e.g. `zeltanews.com`), or CTA link blocks (e.g. `👉 Читати статтю...`, `Аналітика — на zeltanews.com`) in any social post across **Threads, Telegram, Bluesky, or Facebook**.
- Social media algorithms (especially Meta Threads & Facebook) heavily penalize posts with links, cutting reach by 70–90%.
- Every social publication must be 100% native and self-contained: title + hook + concrete numbers + provocative debate question + tags/image.
- The link-block scrubber (`stripAllLinkBlocks` / `strip_link_blocks`) is permanently enforced in the worker and broadcast scripts.

---

## 🧭 Operational Modes

When the user provides a news snippet, tweet, screenshot, or URL, evaluate the intent and select the appropriate mode:

```
                  User provides context
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
[Mode 1: Editorial Priority Queue]   [Mode 2: Urgent Immediate Broadcast]
- PRIMARY & DEFAULT WORKFLOW         - ONLY when explicitly instructed:
- User provides topic, prompt, link,   "терміново", "запости прямо зараз",
  text snippet, or request             "без очікування / без черги"
- Enqueues to D1 `editorial_queue`   - Skips queue and immediately broadcasts
- Consumed on NEXT HOURLY CRON run     to social media without site article
  instead of generic RSS news
- 5-language story + Google Indexing
  + Multi-channel social broadcast
```

---

## 📰 Mode 1: Editorial Priority Queue (DEFAULT WORKFLOW)

### Core Principle
By default, the Google Cloud Run C# agent (`zelta-news-agent`) runs an autonomous cron job every hour (`0 * * * *`) via Google Cloud Scheduler that checks for pending editorial items and picks top stories.
Whenever the user invokes `/zelta-publisher-skill` with a story topic, URL, or news snippet, **ALWAYS add it to the Editorial Priority Queue** (`editorial_queue` in D1 `pulsepress-news-db`).

On the next cron trigger:
1. The Cloud Run agent detects the pending queue item.
2. It generates a full-length, authoritative 5-language investigation (`uk`, `en`, `pl`, `de`, `es`) with concrete numbers, facts, and structure.
3. The Critic Agent reviews and verifies Zero-Links and character constraints.
4. Media is attached (or Wikimedia resolved).
5. Persisted to D1 and marked `completed`.
6. Google Indexing API pinged (< 1s) and syndicated across social channels (Telegram, Threads, Bluesky, Facebook).

### Enqueue Execution
Run `scripts/enqueue_editorial.py`:

```powershell
python C:\Users\Dmytro\source\repos\Github\agentic-skills\skills\zelta-publisher-skill\scripts\enqueue_editorial.py `
  --prompt "В Україні медіанний щомісячний платіж за іпотекою у 2026 році становить 13 000 – 18 300 грн. Навіщо аренди по 30к?" `
  --notes "єОселя 3% і 7%, порівняння витрат на оренду та володіння житлом" `
  --category "ukraine" `
  --importance 88
```

Supported categories: `ukraine`, `world`, `tech`, `celebs`, `culture`, `sports`, `science`.

To view current queue status:
```powershell
python C:\Users\Dmytro\source\repos\Github\agentic-skills\skills\zelta-publisher-skill\scripts\enqueue_editorial.py --list
```

To update an existing item (e.g. change category to celebs, reset to pending):
```powershell
python C:\Users\Dmytro\source\repos\Github\agentic-skills\skills\zelta-publisher-skill\scripts\enqueue_editorial.py `
  --update-id "<ID>" `
  --new-category "celebs" `
  --new-status "pending"
```

---

## 🚀 Mode 2: Urgent Immediate Social Broadcast (Only on Explicit Request)

### Core Principle
Used **ONLY** when the user explicitly commands immediate publication without waiting for the cron ("терміново", "запости зараз", "без черги").
Social platform algorithms (Threads, Bluesky, Facebook) significantly suppress reach when a post contains external outbound links. Mode 2 publishes pure native content with zero outbound links, maximizing impressions and virality.

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
  --image-path "C:\path\to\local_image.jpg"
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

---

## 🤖 Mode 3: Daily Slowpoque Threads Autopilot (@slowpoque618)

### Core Principle
Once per 24 hours, selects the top-impact story from the primary account (Zelta News D1 database), generates a thoughtful, dry analytical rewrite tailored for Threads, and publishes it with zero outbound links and attached authentic visual evidence.

### Constraints & Standards
1. **Posting Frequency**: Exactly 1 post per day (evening prime time window).
2. **Tone**: Objective, dry, factual analysis. Never use boilerplate greetings like 'Slowpoque на зв\'язку'. Focus on causes, numbers, and consequences (e.g. how disabling border cell towers reduced air raid alerts).
3. **Link Policy**: Strictly ZERO outbound links (no URLs in body or comments) to prevent Threads algorithmic penalization.
4. **Length**: Strictly under 500 characters.
5. **State & History**: Managed via scripts/autopilot_state.json. Prevents duplicate postings.

### Autopilot CLI Execution
`powershell
# Check current autopilot eligibility and next top candidate
python agentic-skills/skills/zelta-publisher-skill/scripts/autopilot_slowpoque.py --status

# Preview candidate selection and analytical rewrite
python agentic-skills/skills/zelta-publisher-skill/scripts/autopilot_slowpoque.py --preview

# Run daily autopilot (respects once-daily constraint)
python agentic-skills/skills/zelta-publisher-skill/scripts/autopilot_slowpoque.py --run

# Force run (bypasses once-daily limit if needed)
python agentic-skills/skills/zelta-publisher-skill/scripts/autopilot_slowpoque.py --force
`
