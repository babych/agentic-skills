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
[Mode 1: Short Take / X Quote]      [Mode 2: Full Newsroom Story]
- User pastes a tweet, quote,       - User provides long-form text,
  short update, or says "пости        press release, or requests a full
  без лінку / короткий твіт"          article for zeltanews.com
- NO website article created        - Generates 5-language story
- NO site link attached             - Writes to Cloudflare D1 DB
- Direct broadcast across social    - Dispatches Google Indexing API
  channels for maximum algorithm    - Syndicates with first-comment
  organic reach (zero downrank)       link placement
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
  --image-url "https://example.com/photo.jpg"
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
- **Languages**: Ukrainian (`uk`), English (`en`), German (`de`), Japanese (`ja`), Spanish (`es`).
- **Fields**: `slug`, `title`, `summary`, `content_md`, `seo_title`, `seo_description`, `tags`, `social_hook`.
- **Image**: High-res editorial photo with 1280px optimized thumbnail.

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
