---
name: qwen-image-remote-setup
description: Complete deployment guide, automation scripts, and hardware-specific configurations for installing and running Qwen Image 2.1 and Qwen-Image-Edit (Uncensored) on remote AMD Radeon RX 6600 (8GB VRAM RDNA2) workstations across Windows and Linux.
---

# Qwen Image 2.1 / Edit Setup Guide for AMD Radeon RX 6600 (8GB VRAM)

This skill provides step-by-step instructions, installation scripts, environment configuration, and memory optimizations for deploying **Qwen Image 2.1** and **Qwen-Image-Edit (Uncensored)** on a remote host equipped with an **AMD Radeon RX 6600** (8GB GDDR6, RDNA2 / Navi 23 / gfx1032).

---

## Hardware Profile: AMD Radeon RX 6600
- **VRAM:** 8 GB GDDR6 (128-bit bus, 224 GB/s bandwidth + 32MB Infinity Cache)
- **Architecture:** RDNA2 (Navi 23, GFX Target: `gfx1032`)
- **Strategy for 8GB VRAM:**
  Since full FP16 Qwen models require >24GB, on RX 6600 we use **4-bit GGUF quantization** (`Q4_K_M` / `Q4_0`) with **Dynamic VRAM Offloading** (Text Encoder on RAM/VRAM offload, DiT model active in VRAM).

---

## 1. Automated Deployment on Windows (DirectML & GGUF)

### Step 1: Prerequisites
- Python 3.10.x (recommended: 3.10.11)
- Git for Windows
- Visual C++ Redistributable 2015-2022

### Step 2: Automated Installation Script
Create and run `setup_rx6600_windows.bat` on the remote PC:

```bat
@echo off
title Setup Qwen Image Edit for Radeon RX 6600
echo ======================================================================
echo  Setting up ComfyUI + Qwen Image 2.1 on AMD Radeon RX 6600
echo ======================================================================

:: 1. Clone ComfyUI
if not exist "ComfyUI" (
    git clone https://github.com/comfyanonymous/ComfyUI.git
)
cd ComfyUI

:: 2. Create Virtual Environment
python -m venv venv
call venv\Scripts\activate

:: 3. Install PyTorch with DirectML
python -m pip install --upgrade pip
pip install torch-directml torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
pip install gguf aiohttp huggingface_hub

:: 4. Install Custom Nodes
cd custom_nodes
if not exist "ComfyUI-GGUF" git clone https://github.com/city96/ComfyUI-GGUF.git
if not exist "comfyui_controlnet_aux" git clone https://github.com/Fannovel16/comfyui_controlnet_aux.git
if not exist "comfyui-reactor-node" git clone https://github.com/Gourieff/comfyui-reactor-node.git
cd ..

:: 5. Create Model Directories
mkdir models\diffusion_models 2>nul
mkdir models\text_encoders 2>nul
mkdir models\vae 2>nul

echo.
echo Environment ready! Now downloading Qwen Image Edit models...
python download_qwen_models.py
pause
```

### Step 3: Model Downloader (`download_qwen_models.py`)
```python
import os
import shutil
from huggingface_hub import hf_hub_download

BASE = r"models"
DIFFUSION = os.path.join(BASE, "diffusion_models")
TEXT_ENC = os.path.join(BASE, "text_encoders")
VAE_DIR = os.path.join(BASE, "vae")

REPO = "ChrisColeTech/qwen-image-edit-uncensored-GGUF"
FILES = [
    ("split/diffusion_models/qwen-image-edit-2511-uncensored-Q4_K_M.gguf", DIFFUSION, "qwen-image-edit-2511-uncensored-Q4_K_M.gguf"),
    ("split/text_encoders/Qwen2.5-VL-7B-Instruct-q4_0.gguf", TEXT_ENC, "Qwen2.5-VL-7B-Instruct-q4_0.gguf"),
    ("split/text_encoders/Qwen2.5-VL-7B-Instruct-mmproj-f16.gguf", TEXT_ENC, "Qwen2.5-VL-7B-Instruct-mmproj-f16.gguf"),
    ("split/vae/qwen_image_vae.safetensors", VAE_DIR, "qwen_image_vae.safetensors"),
]

for filename, target_dir, target_name in FILES:
    print(f"[+] Downloading {target_name}...")
    cached = hf_hub_download(repo_id=REPO, filename=filename)
    dst = os.path.join(target_dir, target_name)
    shutil.copy2(cached, dst)
    print(f"    Saved: {dst}")
```

### Step 4: Remote Launch Script (`run_remote_rx6600.bat`)
```bat
@echo off
title ComfyUI Remote - AMD Radeon RX 6600
cd /d %~dp0\ComfyUI
call venv\Scripts\activate

:: Optimal memory management for 8GB RX 6600
python main.py --listen 0.0.0.0 --port 8188 --reserve-vram 1.0 --highvram
pause
```

---

## 2. Ultra-Performance Deployment on Linux (ROCm 6.x)

If the remote PC runs Ubuntu 22.04 / 24.04, native **ROCm (HIP)** provides **3x-5x faster** generation speeds than Windows DirectML on RX 6600:

### Linux Setup Steps:
```bash
# 1. Install ROCm 6.1
sudo apt update && sudo apt install -y python3-venv python3-pip git wget

# 2. Setup GFX override for Radeon RX 6600 (Navi 23)
export HSA_OVERRIDE_GFX_VERSION=10.3.0
export ROCM_PATH=/opt/rocm
export HIP_VISIBLE_DEVICES=0

# 3. Create venv & install ROCm PyTorch
python3 -m venv venv_rocm
source venv_rocm/bin/activate
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.1
pip install -r ComfyUI/requirements.txt gguf huggingface_hub

# 4. Start ComfyUI for LAN/Remote access
python3 ComfyUI/main.py --listen 0.0.0.0 --port 8188
```

---

## 3. Remote Control & API Integration

### Accessing ComfyUI over Network:
- **Web UI:** `http://<REMOTE_PC_IP>:8188`
- **Port Forwarding via SSH Tunnel (if behind NAT/Firewall):**
  ```bash
  ssh -L 8188:127.0.0.1:8188 user@remote_pc_ip
  ```

### Executing Remote Image Edits from Antigravity:
Use the skill script pointing to the remote IP:
```bash
python .agents/skills/qwen-image-editor/scripts/edit_image.py \
  --image "input_photo.jpg" \
  --prompt "keep background and pose, natural edit" \
  --url "http://<REMOTE_PC_IP>:8188" \
  --steps 4
```

---

## 4. RX 6600 VRAM Optimization Tips

1. **GGUF Quantization Choice:**
   - **`Q4_K_M`:** Optimal balance between visual detail and memory footprint. Fits comfortably into 8GB VRAM alongside the VL text encoder.
2. **Step Count:**
   - Qwen Image Edit is trained for **4 steps** with Euler/Simple sampler. Do not use 20–30 steps (it wastes compute without improving output).
3. **CFG Scale:**
   - Always keep `cfg = 1.0` (it is a flow-matching / turbo DiT architecture; CFG > 1.0 produces burnt artifacts).
