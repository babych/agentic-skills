---
name: qwen-gpu-studio
description: Unified GPU rendering, anatomical inpainting, and creative AI studio powered by Qwen 2.1 Image Edit DiT and ComfyUI. Covers remote GPU node management (headless RX 6600 XT DirectML/ROCm, Cloud L40S), zero-defect face guarding, 100% facial identity anchoring, and anti-grain VAE synthesis.
---

# Qwen GPU Studio & Inpainting Pipeline (Qwen 2.1 + ComfyUI + DirectML/ROCm)

Unified operational framework, calibrated gold standards, and deployment recipes for running **Qwen 2.1**, **Qwen-Image-Edit (Uncensored DiT)**, and **Universal Inpainting Pipelines** across local/remote AMD Radeon nodes (`itx` / RX 6600 XT 8GB) and high-performance Cloud GPUs (L40S / A100).

---

## 1. 🛡️ Multi-Zone Segmentation & Strict Inpaint Separation

### A. Standard Run Queries (Zero Over-Segmentation):
- **Garment Detection Queries:**
  - `"bikini, swimsuit, bikini top, bra"`
  - `"tank top, crop top, sleeveless shirt, shirt"`
  - `"lingerie, corset, lace top, underwear"`
  - `"grey sweater, cardigan, top fabric, clothes"`
  *(Note: Color-specific queries like "black bikini top" are strictly excluded from standard run to prevent regular black t-shirts from engulfing shoulders and sleeves).*
- **Parameters:** `cloth_thresh = 0.16`, `dilation_iters = 1`, `kernel_size = (9, 9)`, `depth_blur_ksize = (23, 23)`, `feather_ksize = (11, 11)`, `padding_ratio = 0.40`.

### B. Enhance Run Queries (`boost_mode == 'cloth'`):
- **Garment Detection Queries (Multi-Color & Swimwear Activated):**
  - `"bikini top, bra, swim top, swimsuit top, underwear top"`
  - `"tank top, crop top, sleeveless shirt, shirt, top fabric, clothes, fabric, necklace, pendant"`
  - `"green bikini top, black bikini top, white bikini top, red bikini top, blue bikini top, yellow bikini top, swimwear"`
- **Parameters:** Adaptive dynamic threshold `dynamic_thresh = max(0.005, min(0.16, max_cloth.max() * 0.35))`, `dilation_iters = 2`, `kernel_size = (17, 17)`, `depth_blur_ksize = (23, 23)`, `padding_ratio = 0.45`.

---

## 2. 👤 Dual-Stage Impenetrable Face Guard & Zero-Seam Compositing

- **Dedicated Face Detection Query:**
  `"face, eyes, eyebrows, nose, lips, mouth, chin, jaw, cheeks, ears, hair, head"` (detection threshold `0.18`).
- **General Body Protection Query:**
  `"neck, collarbone, arms, hands, fingers, wrist, long sleeves, pants, jeans, skirt, legs, feet, phone, mirror, background, chair, wall"` (protection threshold `0.38`–`0.40`).
- **Face Guard Exclusion & Seamless Blending:**
  1. **Perimeter Dilation:** Face mask is dilated with an 11x11 kernel by 2 iterations (`m_face_guarded`) around chin, jaw, and neck.
  2. **Boolean Subtraction:** `final_mask_bool = m_cloth & (~m_protect) & (~m_face_guarded)`.
  3. **Pre-Blur Zeroing:** `dilated_full[m_face_guarded] = 0` *before* Gaussian blur `(21, 21)` to ensure smooth transitions without harsh collar lines.
  4. **Strict 1:1 Aspect Ratio:** `get_perfect_square_crop_box` prevents background stretching.
  5. **Global Canvas Compositing:** Inpainted crop is placed onto a full-sized raw canvas copy and blended with the continuous feathered mask (`Image.composite(full_res_canvas, img_raw, mask_full_pil)`). Zero crop boundary seams.

---

## 3. 🎨 Calibrated Anatomical Presets

| Preset ID | Preset Name | CFG | Steps | 3D Dome Boost | Default CN Scale | Enhance CN Scale | Seed |
|---|---|---|---|---|---|---|---|
| `P0_Petite_Flat` | Petite Flat (Size 0 / AA-Cup) | `5.0` | `25` | `0.0` | `0.68` | `0.55` | `424242` |
| `P1_Natural_B` | Natural (B-Cup) | `5.4` | `25` | `10.0` | `0.62` | `0.50` | `424242` |
| `P2_Shapely_C` | Shapely (C-Cup) | `5.6` | `25` | `16.0` | `0.60` | `0.48` | `424242` |
| `P3_Voluptuous_D` | Voluptuous (D-Cup) | `5.6` | `25` | `22.0` | `0.56` | `0.46` | `888424` |
| `P4_Glamour_HD` | Glamour Focus | `7.2` | `28` | `14.0` | `0.58` | `0.48` | `987654` |

---

## 4. ☁️ Qwen Cloud Multi-Variant Standard (Golden Reference + Soft Natural)

In cloud/remote generation pipelines, always generate and return **TWO (2) variants**:

### Variant 1: Golden Benchmark Reference (Modest B-Cup)
- **Prompt:** `"remove all clothing and swimwear, natural modest B-cup bare breasts size 2, slender athletic body proportions, authentic natural skin texture, delicate natural micro-pores, soft diffused lighting, matching warm skin tone, raw 35mm dslr photograph"`
- **Negative Prompt:** `"plastic skin, airbrushed, wax, doll, cartoon, 3d render, blurry, noisy skin, blotchy texture, spots, blemishes, clothes, fabric, bra, swimsuit, huge breasts, balloon implants, extra nipples"`
- **CFG:** `2.8`, **Steps:** `25`, **Seed:** `888424`

### Variant 2: Soft Realistic Curve
- **Prompt:** `"remove all clothing, authentic feminine bare breasts natural shape, beautiful natural curvature, realistic candid photo, soft natural skin texture, delicate subsurface scattering, matching original lighting"`
- **Negative Prompt:** `"plastic skin, airbrushed, wax, doll, cartoon, 3d render, noisy, blotchy, spots, blemishes, clothes, fabric, bra, swimsuit, oversized breasts, balloon implants, duplicate areolas"`
- **CFG:** `2.6`, **Steps:** `25`, **Seed:** `424242`

---

## 5. 🎭 Creative AI Studio & 100% Facial Identity Retention

### A. Architectural Principles
1. **🚫 NO Naive 2D Alpha Cutout Overlays**: Never attempt 2D circular/elliptical face masking or alpha-blending of the original face on top of generated results. It creates visible edge seams, mismatching neck lighting, unnatural head tilt, and cartoonish "cut & paste" artifacts.
2. **✨ Pure Generative Synthesis with Transformer Latent Anchoring**: Let Qwen 2.5/2.1 DiT render the complete scene holistically so that lighting, subsurface scattering, hair contact, and collar shadows blend with 100% optical consistency.

### B. ⚓ Golden Prompt Anchoring Formula
Every creative instruction or preset MUST append the mandatory identity retention suffix:
```text
keep exact same person, 100% exact original face, sharp focused eyes and gaze, exact original lips and expression, preserve original lighting, exact original skin color and tone, seamless photorealistic integration, no text
```

### C. 🎛️ Calibrated Inference Hyperparameters
- **CFG (Guidance Scale):** Strictly `1.8` – `2.1` (Golden baseline: `1.95`). *(Higher CFG >2.5 distorts facial identity, creates waxy/plastic skin, and causes identity drift).*
- **Steps:** `20` – `24` (Optimal: `22` steps on L40S / Rapid DiT).
- **Default Seed:** `888424` (or `424242`).
- **Negative Prompt:**
  ```text
  plastic skin, airbrushed, wax, doll, cartoon, 3d render, blurry, noisy, distorted eyes, extra fingers, text, watermark, deformed anatomy, bad proportions, bad lighting
  ```

### D. 🧼 Anti-Grain Texture-Fix VAE Benchmark
- **Root Cause of Texture Grain:** Stock `qwen_image_vae.safetensors` inherently leaves a faint 2-px checkerboard/grain pattern on fine skin micro-textures, sky gradients, and fabrics regardless of quantization.
- **Golden Standard Fix:** Use `madebyollin/texture-fix-vae-for-qwen-image-2.1` (`texture_fix_vae_for_qwen_image_2.1_bf16.safetensors`). Drop-in replacement with identical shapes, eliminating the checkerboard lattice while preserving natural skin pores.

---

## 6. 🖥️ Remote GPU Node Management & Deployment

### Hardware Profile: AMD Radeon RX 6600 XT (8GB VRAM)
- **Host Alias:** `itx` (`ITX@192.168.1.152`)
- **Key Authentication:** `~/.ssh/id_ed25519_github` via `~/.ssh/config`
- **8GB VRAM Strategy:** 4-bit GGUF quantization (`Q4_K_M` / `Q4_0`) with Dynamic VRAM Offloading (VL text encoder on RAM/offload, DiT in VRAM).

### Node Health Check
```powershell
powershell -File scripts/check_node.ps1
```

### ComfyUI Remote Execution via API
```bash
python scripts/edit_image.py \
  --image "<path_to_input_image>" \
  --prompt "change clothes to a sharp tailored dark navy business suit, keep exact same person, 100% exact original face, sharp focused eyes and gaze, preserve original lighting" \
  --url "http://192.168.1.152:8188" \
  --steps 22
```

### Launch ComfyUI with Optimal 8GB Memory Allocation
```bat
python main.py --listen 0.0.0.0 --port 8188 --reserve-vram 1.0 --highvram
```
