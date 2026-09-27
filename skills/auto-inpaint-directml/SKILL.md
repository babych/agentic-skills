---
name: auto-inpaint-directml
description: Automated anatomical inpainting pipeline for high-precision cloth removal, size control, arm/hand protection, strict face isolation, and 3D depth-guided skin synthesis using DirectML on AMD Radeon GPUs.
---

# Auto Inpaint DirectML Pipeline Skill & Protected Gold Standards

This skill documents the calibrated **Universal Auto-Inpaint Pipeline & Telegram Star Bot** on AMD Radeon GPUs (DirectML) and local Windows nodes.

---

## 🔒 Protected Calibration & Gold Standard Architecture

> **CRITICAL RULE**: Do not modify these parameters or presets without explicit user instructions. Natural proportions, facial preservation, and accurate mask exclusion are the foundational standard.

### 1. Multi-Zone Segmentation & Query Separation

#### Standard Run Queries (Zero Over-Segmentation):
- **Garment Detection Queries:**
  - `bikini, swimsuit, bikini top, bra`
  - `tank top, crop top, sleeveless shirt, shirt`
  - `lingerie, corset, lace top, underwear`
  - `grey sweater, cardigan, top fabric, clothes`
- **Threshold & Morphological Parameters:** `cloth_thresh = 0.16`, `dilation_iters = 1`, `kernel_size = (9, 9)`, `depth_blur_ksize = (23, 23)`, `feather_ksize = (11, 11)`, `padding_ratio = 0.40`.

#### Enhance Run Queries (`boost_mode == 'cloth'`):
- **Multi-Color & Swimwear Detection Queries:**
  - `bikini top, bra, swim top, swimsuit top, underwear top`
  - `tank top, crop top, sleeveless shirt, shirt, top fabric, clothes, fabric, necklace, pendant`
  - `green bikini top, black bikini top, white bikini top, red bikini top, blue bikini top, yellow bikini top, swimwear`
- **Threshold & Morphological Parameters:** Adaptive dynamic threshold `dynamic_thresh = max(0.005, min(0.16, max_cloth.max() * 0.35))`, `dilation_iters = 2`, `kernel_size = (17, 17)`, `depth_blur_ksize = (23, 23)`, `padding_ratio = 0.45`.

---

### 2. Dual-Stage Impenetrable Face Guard & Zero-Seam Compositing
- **Dedicated Face Query:** `"face, eyes, eyebrows, nose, lips, mouth, chin, jaw, cheeks, ears, hair, head"` (`thresh = 0.18`).
- **Body & Environment Protection:** `"neck, collarbone, arms, hands, fingers, wrist, long sleeves, pants, jeans, skirt, legs, feet, phone, mirror, background, chair, wall"` (`thresh = 0.38`–`0.40`).
- **Safety Perimeter & Seamless Blending:**
  - `m_face_guarded` is dilated by 11px (2 iterations) to safeguard the chin and jawline.
  - Zeroed out before dilation: `final_mask_bool = m_cloth & (~m_protect) & (~m_face_guarded)`.
  - Zeroed out before Gaussian blur: `dilated_full[m_face_guarded] = 0` *before* `(21, 21)` blur for continuous gradient skin transition.
  - **Perfect Square Crop**: `get_perfect_square_crop_box` guarantees strict 1:1 aspect ratio without background stretch distortion.
  - **Global Canvas Compositing**: Inpainted crop is pasted into full-res canvas and blended with full smooth mask (`Image.composite(full_res_canvas, img_raw, mask_full_pil)`), completely eliminating crop-box rectangular seams.

---

### 3. Golden Anatomical Presets
| Preset ID | Preset Name | CFG | Steps | 3D Dome Boost | Default CN Scale | Enhance CN Scale | Seed |
|---|---|---|---|---|---|---|---|
| `P1_Natural_B` | Natural (B-Cup) | `5.4` | `25` | `10.0` | `0.62` | `0.50` | `424242` |
| `P2_Shapely_C` | Shapely (C-Cup) | `5.6` | `25` | `16.0` | `0.60` | `0.48` | `424242` |
| `P3_Voluptuous_D` | Voluptuous (D-Cup) | `5.6` | `25` | `22.0` | `0.56` | `0.46` | `888424` |
| `P4_Glamour_HD` | Glamour Focus | `7.2` | `28` | `14.0` | `0.58` | `0.48` | `987654` |

#### Prompts & Anatomical Guidance:
- **P1 Positive:** `RAW candid 8k dslr photo, natural modest B-cup bare breasts size 2, slender athletic body proportions, realistic curvature, micro skin pores, fine skin texture, matching warm skin tone, subsurface scattering, two natural areolas`
  - **Negative:** `huge breasts, oversized, deep cleavage, balloon implants, extra nipples, duplicate areolas, clothes, bra, white fabric, lace, straps`
- **P2 Positive:** `RAW candid 8k dslr photo, shapely natural C-cup bare breasts size 3, authentic feminine body proportions, beautiful natural shape, micro skin pores, delicate texture, matching warm skin tone, subsurface scattering, two natural areolas`
  - **Negative:** `flat chest, oversized implants, balloon breasts, extra nipples, duplicate areolas, clothes, bra, white fabric, lace, straps`
- **P3 Positive:** `RAW candid 8k dslr photo, natural full D-cup bare breasts size 4, natural cleavage with realistic gravitational spread, authentic volume, micro skin pores, matching warm skin tone, subsurface scattering, two natural areolas`
  - **Negative:** `small breasts, flat chest, size A, deflated, oversized balloon implants, extra nipples, duplicate areolas, clothes, bra, white fabric, lace, straps`
- **P4 Positive:** `RAW candid 8k dslr photo, natural shapely modest bare breasts, slender athletic torso, authentic sharp skin pores, natural detailed skin texture with subsurface scattering, soft ambient room reflections, two natural symmetrical areolas, sharp focus, 8k`
  - **Negative:** `oversized breasts, huge breasts, deep cleavage line, balloon implants, blurry, flat, plastic skin, cartoon, 3d render, clothes, bra, cardigan, fabric, buttons, laptop, extra nipples`

---

### 4. Interactive UI & Regeneration Logic
- **Button:** `⚡ Підсилення розпізнавання одягу` / `⚡ Enhance Clothing Detection`
- **Limit:** Exactly 1 enhancement per photo.
