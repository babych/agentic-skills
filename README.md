# 🚀 Custom Antigravity Skills Collection

Curated collection of custom production-grade **Google Antigravity** skills, edge web standards, and publishing automation tools.

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Antigravity](https://img.shields.io/badge/Agent-Google%20Antigravity-orange.svg)](https://antigravity.google)

---

## 📦 Custom Skills Catalog

| Skill Name | Description | Category |
|---|---|---|
| [**`static-pwa-edge-skill`**](./skills/static-pwa-edge-skill) | Autonomous Progressive Web Apps (PWA) with Cloudflare Pages/D1, Web Push notifications, i18n, and offline cache. | Web & Cloud |
| [**`zero-hop-code-skill`**](./skills/zero-hop-code-skill) | Zero-dependency, zero-VRAM BM25/IDF AST-boundary codebase search engine for single-hop edits. | Developer Tools |
| [**`windows-node-ssh-bootstrap`**](./skills/windows-node-ssh-bootstrap) | Automated OpenSSH server setup, passwordless key auth, and firewall rules for Windows GPU nodes. | Infrastructure |
| [**`book-translator-publisher`**](./skills/book-translator-publisher) | End-to-end publishing pipeline for books using Typst, Gemini Flash Lite, and Gemini Vision. | Publishing |

---

## 🛠️ How to Install & Use Skills

### Option A: Install to a Specific Workspace
Clone or copy the desired skill folder into your project's `.agents/skills/` directory:
```bash
mkdir -p .agents/skills
cp -r /path/to/antigravity-skills/skills/zero-hop-code-skill .agents/skills/
```

### Option B: Install Globally (Available in all projects)
Copy the skill folder to your user's global Antigravity configuration directory:
* **Windows:** `%USERPROFILE%\.gemini\antigravity\skills\`
* **Linux / macOS:** `~/.gemini/antigravity/skills/`

---

## 📄 License
MIT License. Free for open source and commercial use.
