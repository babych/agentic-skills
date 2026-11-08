# 🚀 Agentic Skills Collection

Curated collection of custom production-grade skills for AI agents (Google Antigravity, Claude Code, Cursor, and OpenCode), hardware-anchored security enclaves, edge web standards, and developer productivity tools.

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Agentic AI](https://img.shields.io/badge/Agents-Universal%20Skill%20Standard-brightgreen.svg)](https://github.com/babych/agentic-skills)

---

## 📦 Skills Catalog

| Skill Name | Description | Category |
|---|---|---|
| [**`vault-skill`**](./skills/vault-skill) | Hardware-anchored (DPAPI + AES-256-GCM) encrypted key vault with semantic access catalog for safe agent execution. | Security & Enclave |
| [**`shop-talk-dev`**](./skills/shop-talk-dev) | Human dev-to-dev ("shop talk") style for technical docs, READMEs, PRs, and commit messages. Drops AI fluff and buzzwords. | Technical Writing |
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
cp -r /path/to/agentic-skills/skills/vault-skill .agents/skills/
```

### Option B: Install Globally (Available across projects)
Copy the skill folder to your agent configuration directory:
* **Antigravity / Gemini:** `%USERPROFILE%\.gemini\config\skills\` or `~/.gemini/config/skills/`
* **Claude Code / OpenCode:** your user agent skills directory

---

## 📄 License
MIT License. Free for open source and commercial use.
