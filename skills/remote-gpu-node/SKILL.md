---
name: remote-gpu-node
description: Connect, deploy, monitor, and execute AI models (Ollama, llama.cpp Vulkan, ComfyUI, PyTorch DirectML) and automation scripts on the headless remote AMD Radeon RX 6600 XT (8GB VRAM) Windows node at 192.168.1.152.
---

# Remote AMD GPU Node Controller (RX 6600 XT / 8GB VRAM)

This skill provides operational procedures, automation scripts, and deployment recipes for managing and running AI workloads on the headless Windows 11 remote node.

---

## 1. Remote Node Hardware & Network Profile

| Parameter | Specification / Value |
| :--- | :--- |
| **SSH Host Alias** | `itx` (or `ITX@192.168.1.152`) |
| **Authentication** | Key-based (`~/.ssh/id_ed25519_github`), configured in `~/.ssh/config` |
| **Operating System** | Microsoft Windows 11 Pro |
| **GPU** | **AMD Radeon RX 6600 XT (8 GB GDDR6)** |
| **CPU** | Intel(R) Core(TM) i5-8600K (6 Cores / 3.60 GHz) |
| **RAM** | 16 GB DDR4 |
| **Storage** | `C:` System (137 GB free), `D:\` Fast Storage (425 GB free) |

---

## 2. Remote Command Execution Quick Reference

All remote commands should be executed from the local shell using `ssh itx`:

### Run PowerShell Command
```powershell
ssh itx 'powershell -NoProfile -Command "<command>"'
```

### Check GPU & Memory Status
```powershell
ssh itx 'powershell -NoProfile -Command "Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, Status; Get-PSDrive C, D | Select-Object Root, @{N=\"FreeGB\";E={[math]::Round($_.Free/1GB,1)}}"'
```

### Transfer Files (Local to Remote)
```powershell
# Copy a script or weights file to D:\AI_Workspace\
scp local_file.py itx:"D:/AI_Workspace/"
```

### Transfer Files (Remote to Local)
```powershell
scp itx:"D:/AI_Workspace/output.png" ./output.png
```

---

## 3. Recommended AI Runtime Engines for RX 6600 XT (8GB VRAM)

### A. Ollama (LLM Server with REST API)
Best for general LLM serving (Llama 3.1 8B, Qwen 2.5 7B, Mistral, DeepSeek 7B/8B):

1. **Install Ollama on Remote Node:**
```powershell
ssh itx 'powershell -NoProfile -Command "winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements"'
```

2. **Set Ollama to listen on all interfaces (LAN access):**
```powershell
ssh itx 'powershell -NoProfile -Command "[System.Environment]::SetEnvironmentVariable(\"OLLAMA_HOST\", \"0.0.0.0:11434\", [System.EnvironmentVariableTarget]::User); [System.Environment]::SetEnvironmentVariable(\"OLLAMA_MODELS\", \"D:\ollama_models\", [System.EnvironmentVariableTarget]::User)"'
```

3. **Pull and Run 7B/8B Models (Q4_K_M fits 100% in 8GB VRAM):**
```powershell
ssh itx "ollama run qwen2.5:7b"
ssh itx "ollama run llama3.1:8b"
```

---

### B. llama.cpp / llama-server (High-Speed Vulkan Engine)
Best for maximum token generation speed and OpenAI-compatible API on Windows:

1. **Download Precompiled Vulkan Binary:**
```powershell
ssh itx 'powershell -NoProfile -Command "New-Item -ItemType Directory -Path D:\llama_vulkan -Force; cd D:\llama_vulkan; Invoke-WebRequest -Uri https://github.com/ggerganov/llama.cpp/releases/latest/download/llama-b4000-bin-win-vulkan-x64.zip -OutFile llama_vulkan.zip; Expand-Archive llama_vulkan.zip -DestinationPath D:\llama_vulkan -Force"'
```

2. **Start OpenAI-Compatible Server on Port 8080:**
```powershell
ssh itx 'D:\llama_vulkan\llama-server.exe -m "D:\models\qwen2.5-7b-instruct-q4_k_m.gguf" -ngl 99 --host 0.0.0.0 --port 8080'
```

---

### C. ComfyUI / Image Generation (DirectML / GGUF)
Best for Qwen-Image-Edit, SD 1.5, SDXL with 4-bit quantizations:
- Directory: `D:\ComfyUI\`
- Torch Backend: `torch-directml`
- Models stored on: `D:\ComfyUI\models\`

---

## 4. Maintenance & Headless Operations

- **No Monitor Required:** The node operates completely headless.
- **Power Management:** System is configured not to sleep on idle.
- **Reboot Node Remotely:**
  ```powershell
  ssh itx 'shutdown /r /t 0'
  ```
