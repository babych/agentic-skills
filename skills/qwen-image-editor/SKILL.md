---
name: qwen-image-editor
description: Edit, modify, inpaint, or restyle images using the local or remote Qwen-Image-Edit (Uncensored GGUF) model running on ComfyUI API. Use this skill whenever the user asks to modify an existing photo, replace backgrounds, change clothing, add objects, adjust hair/styles, or perform uncensored image editing.
---

# Qwen Image Editor Skill

This skill allows Antigravity to perform AI image editing tasks by communicating directly with a running **ComfyUI** instance hosting the **Qwen-Image-Edit (Uncensored)** DiT model.

## Capabilities
- **Instruction-based Image Editing:** "Change the car color to red", "Add sunglasses", "Make the background a tropical beach", "Replace outfit with a suit".
- **Uncensored & Creative Control:** Full uncensored prompt adherence without safety refusals.
- **Identity & Detail Preservation:** Preserves faces, poses, lighting, and composition while only editing the requested elements.

## How to Execute

Use the provided Python script `scripts/edit_image.py` inside the skill:

```bash
python .agents/skills/qwen-image-editor/scripts/edit_image.py \
  --image "<path_to_input_image>" \
  --prompt "<editing_instruction_in_english>" \
  --output "<path_to_output_image>" \
  --steps 4
```

### Parameters:
- `--image` (required): Absolute or relative path to the source image.
- `--prompt` (required): Text instruction describing the exact edit.
- `--output` (optional): Path where the resulting image should be saved.
- `--steps` (optional, default 4): Number of diffusion sampling steps (4 is optimal for Rapid/Turbo DiT).
- `--url` (optional, default `http://127.0.0.1:8188`): ComfyUI endpoint URL.

## Workflow API Template
The API workflow JSON is located at:
`C:\AI_Tools\ComfyUI_Qwen\qwen_image_edit_api.json`
