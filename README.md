# 🌌 Custom Antigravity Skills Collection

Curated collection of custom production-grade **Google Antigravity** skills, remote GPU orchestration workflows, and publishing automation tools.

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Antigravity](https://img.shields.io/badge/Agent-Google%20Antigravity-orange.svg)](https://antigravity.google)

---

## 📚 Custom Skills Catalog

| Skill Name | Description | Category |
|---|---|---|
| [**`skill-creator`**](./skills/skill-creator) | Complete engineering framework for architecting, structuring, and testing new Antigravity skills. | Meta / Dev |
| [**`windows-node-ssh-bootstrap`**](./skills/windows-node-ssh-bootstrap) | Automated OpenSSH server setup, passwordless key auth, and firewall rules for Windows GPU nodes. | Infrastructure |
| [**`remote-gpu-node`**](./skills/remote-gpu-node) | Connect, deploy, monitor, and execute AI models on headless AMD/Nvidia GPU nodes over SSH. | Infrastructure |
| [**`auto-inpaint-directml`**](./skills/auto-inpaint-directml) | DirectML anatomical inpainting pipeline with strict face guard and 3D depth guidance on AMD GPUs. | AI Pipeline |
| [**`qwen-image-editor`**](./skills/qwen-image-editor) | DiT flow-matching image editing with Qwen-Image-Edit via ComfyUI. | AI Pipeline |
| [**`qwen-image-remote-setup`**](./skills/qwen-image-remote-setup) | Hardware-specific deployment guides for running Qwen DiT models on AMD Radeon & Nvidia GPUs. | AI Pipeline |
| [**`book-translator-publisher`**](./skills/book-translator-publisher) | End-to-end publishing pipeline for books using Typst, Gemini Flash Lite, and Gemini Vision. | Publishing |

---

## 🚀 How to Install & Use Skills

### Option A: Install to a Specific Workspace
Clone or copy the desired skill folder into your project's `.agents/skills/` directory:
```bash
mkdir -p .agents/skills
cp -r /path/to/antigravity-skills/skills/windows-node-ssh-bootstrap .agents/skills/
```

### Option B: Install Globally (Available in all projects)
Copy the skill folder to your user's global Antigravity configuration directory:
* **Windows:** `%USERPROFILE%\.gemini\antigravity\skills\`
* **Linux / macOS:** `~/.gemini/antigravity/skills/`

---

## 🛠️ Contributing New Skills
1. Fork this repository.
2. Follow the [**`skill-creator`**](./skills/skill-creator) standard to create your new skill directory with a valid `SKILL.md`.
3. Open a Pull Request!

---

## 📄 License
MIT License. Free for open source and commercial use.
