# 🚀 Agentic Skills Collection

Curated collection of production-grade skills and security enclaves for modern agentic AI systems (**Google Antigravity**, **Claude Code**, **Cursor**, **Codex**, and **OpenCode / Agent Zero**).

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Universal Skills](https://img.shields.io/badge/Agent%20Standard-Universal%20Skills-brightgreen.svg)](https://github.com/babych/agentic-skills)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/babych/agentic-skills/pulls)

---

## 📦 Skills Catalog

| Skill Name | Description | Target Platforms | Category |
|---|---|---|---|
| [**`vault-skill`**](./skills/vault-skill) | Hardware-anchored (DPAPI + AES-256-GCM) encrypted key vault with semantic access catalog for safe agent JIT secret execution. | All Agents / Windows | Security & Enclave |
| [**`shop-talk-dev`**](./skills/shop-talk-dev) | Human dev-to-dev ("shop talk") style for technical docs, READMEs, PRs, and commit messages. Drops AI fluff and buzzwords. | All Agents | Technical Writing |
| [**`static-pwa-edge-skill`**](./skills/static-pwa-edge-skill) | Autonomous Progressive Web Apps (PWA) with Cloudflare Pages/D1, Web Push notifications, i18n, and offline cache. | Antigravity / Claude | Web & Cloud |
| [**`zero-hop-code-skill`**](./skills/zero-hop-code-skill) | Zero-dependency, zero-VRAM BM25/IDF AST-boundary codebase search engine for single-hop edits. | All Agents | Developer Tools |
| [**`windows-node-ssh-bootstrap`**](./skills/windows-node-ssh-bootstrap) | Automated OpenSSH server setup, passwordless key auth, and firewall rules for Windows GPU nodes. | All Agents | Infrastructure |
| [**`book-translator-publisher`**](./skills/book-translator-publisher) | End-to-end publishing pipeline for books using Typst, Gemini Flash Lite, and Gemini Vision. | Antigravity / Gemini | Publishing |

---

## 🛠️ How to Install & Use Across Different Agent Frameworks

All skills follow the standard `SKILL.md` specification with YAML frontmatter, making them plug-and-play across major AI platforms:

### 1. 🪐 Google Antigravity
Skills can be installed globally or per-workspace:
- **Global (All Workspaces)**:
  - Windows: `%USERPROFILE%\.gemini\config\skills\<skill-name>\`
  - Linux / macOS: `~/.gemini/config/skills/<skill-name>/`
- **Project-Specific**:
  ```bash
  mkdir -p .agents/skills
  cp -r /path/to/agentic-skills/skills/vault-skill .agents/skills/
  ```
- **Trigger**: Activated automatically via semantic matching or slash command (e.g. `/vault-skill`, `/security-audit`).

### 2. 🟣 Claude Code (Anthropic)
Claude Code loads custom skills directly from your global or project instructions:
- **Project Scope**:
  Place the skill inside `.claude/skills/` or reference the skill directory in `CLAUDE.md`:
  ```bash
  mkdir -p .claude/skills
  cp -r /path/to/agentic-skills/skills/vault-skill .claude/skills/
  ```
- **Global Scope**:
  Add the skill's instructions path into `~/.claude/config.json` or copy to `~/.claude/skills/`.

### 3. ⚡ Cursor & Roo Code / Cline
- **Cursor Rules**:
  Symlink or copy the skill's `SKILL.md` into your `.cursorrules` or `.cursor/rules/`:
  ```bash
  mkdir -p .cursor/rules
  cp skills/vault-skill/SKILL.md .cursor/rules/vault-skill.mdc
  ```
- **Roo Code / Cline**:
  Add the skill folder to `.clinerules/` or `.roomodes/`.

### 4. 🐍 OpenCode, Agent Zero & Custom Python Agents
Skills with Python backends (like `vault-skill` and `zero-hop-code-skill`) expose direct CLI tools:
```bash
# Direct zero-dependency tool call from any agent:
python skills/vault-skill/vault_manager.py list
python skills/zero-hop-code-skill/scripts/code_memory.py search "auth handler"
```

---

## 💡 Quick Start: Example Workflow with `vault-skill`

To enable any agent to run privileged commands without leaking secrets into conversation transcripts:

1. **Set your Master PIN once**:
   ```bash
   python skills/vault-skill/vault_manager.py set-pin
   ```
2. **Store your deployment token**:
   ```powershell
   $env:VAULT_PIN="1234"
   $env:VAULT_SECRET_VALUE="cf_api_token_here"
   python skills/vault-skill/vault_manager.py set CLOUDFLARE_API_TOKEN --desc "Pages & Workers deploy token"
   ```
3. **Agent retrieves token Just-In-Time (JIT)**:
   ```powershell
   $env:CLOUDFLARE_API_TOKEN = python skills/vault-skill/vault_manager.py get CLOUDFLARE_API_TOKEN
   npx wrangler deploy
   ```
   *The token never appears in conversation history, terminal arguments, or log files.*

---

## 🤝 Contributing
Feel free to submit pull requests for new agent skills, security improvements, or adapter guides for other agent frameworks!

## 📄 License
MIT License. Free for open source and commercial use.
