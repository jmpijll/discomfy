# Slice 3a (issue #5) - image_edit smoke runs (Qwen-Image-Edit 2511)

**Branch:** `slice/5-qwen-edit`
**Modality:** `image_edit`
**Manifests under test:**
- `qwen_image_edit_2511_1image` (`workflows/qwen_image_edit_2511_1image.json`)
- `qwen_image_edit_2511_2images` (`workflows/qwen_image_edit_2511_2images.json`)
- `qwen_image_edit_2511_3images` (`workflows/qwen_image_edit_2511_3images.json`)

**ComfyUI target:** `http://172.27.1.165:8188` (RTX 5090, fp8 mixed UNET)

**Models discovered from `/object_info`:**
- UNET: `qwen_image_edit_2511_fp8mixed.safetensors`
- CLIP: `qwen_2.5_vl_7b_fp8_scaled.safetensors` (`type: qwen_image`)
- VAE: `qwen_image_vae.safetensors`
- Lightning LoRA (baked at node 4, strength 1.0):
  `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors`
- User LoRA default (node 5, strength 0.0 by default):
  `QWEN_EDIT_ACTION_V1.safetensors`

**Scope note:** Slice 3 (#5) also covers FLUX Kontext on Klein. That
half is **deferred to a follow-up issue / PR** because the Klein
workflow is gated on Slice 2 fixing FLUX 2 Klein first. Issue #5 stays
open after Slice 3a merges; the follow-up PR will close it.

## Status: PASSED

All three variants ran end-to-end against the live ComfyUI on
2026-06-02 and produced a decoded PNG within the expected ~20s
latency budget for the 4-step Lightning LoRA.

### Source images (generated via `qwen_image_2512` first)

| purpose | prompt_id | local file |
| --- | --- | --- |
| red panda (subject) | `7f774e28-3c96-4fda-8b39-b85e4fe84318` | `output/v3_smoke/7f774e28-.../final_output_00007_.png` |
| leather armchair (scene)  | `2419e6ff-e25c-4a61-b6c0-49b064490763` | `output/v3_smoke/2419e6ff-.../final_output_00009_.png` |
| parrot (color reference) | `003693d4-8de8-44e4-9578-e4af52b0cd3a` | `output/v3_smoke/003693d4-.../final_output_00010_.png` |

### 1-image variant

| field | value |
| --- | --- |
| manifest | `qwen_image_edit_2511_1image` |
| prompt | "add a small wooden cabin in the background, with smoke rising from its chimney" |
| inputs | `image_1` = red panda |
| prompt_id | `f46e87b3-19a8-41f6-8a97-d5aa5cf9aaf2` |
| latency | 21.77 s |
| output bytes | 2,333,633 |
| output | `qwen_edit_2511_00001_.png` |

### 2-image variant

| field | value |
| --- | --- |
| manifest | `qwen_image_edit_2511_2images` |
| prompt | "Place the red panda from image 1 sitting on top of the leather armchair from image 2" |
| inputs | `image_1` = red panda, `image_2` = armchair |
| prompt_id | `8f1e061c-2526-408a-aa81-77ce8b4865da` |
| latency | 17.14 s |
| output bytes | 1,896,280 |
| output | `qwen_edit_2511_00002_.png` |

### 3-image variant

| field | value |
| --- | --- |
| manifest | `qwen_image_edit_2511_3images` |
| prompt | "The red panda from image 1 wearing the colors of the parrot from image 3, sitting on the armchair from image 2" |
| inputs | `image_1` = red panda, `image_2` = armchair, `image_3` = parrot |
| prompt_id | `eeb3bf7a-1747-4750-8f87-5a1c0e2d5d14` |
| latency | 20.47 s |
| output bytes | 2,139,755 |
| output | `qwen_edit_2511_00003_.png` |

## Reproducing the smokes

```bash
source venv/bin/activate

# 1) generate a fresh source image via the t2i manifest
python scripts/v3_smoke.py \
  --manifest qwen_image_2512 \
  --slot prompt="a single red panda eating bamboo in a forest clearing" \
  --slot width=1024 --slot height=1024 --slot lora_strength=0.0
# note the output path it prints, then use it below as --slot image_1=...

# 2) 1-image edit
python scripts/v3_smoke.py \
  --manifest qwen_image_edit_2511_1image \
  --slot prompt="add a small wooden cabin in the background" \
  --slot image_1=/path/from/step/1.png \
  --slot lora_strength=0.0

# 3) 2-image edit (generate a second source the same way first)
python scripts/v3_smoke.py \
  --manifest qwen_image_edit_2511_2images \
  --slot prompt="Place the subject from image 1 onto the scene from image 2" \
  --slot image_1=/path/to/subject.png \
  --slot image_2=/path/to/scene.png \
  --slot lora_strength=0.0

# 4) 3-image edit
python scripts/v3_smoke.py \
  --manifest qwen_image_edit_2511_3images \
  --slot prompt="subject of image 1, attire from image 2, scene from image 3" \
  --slot image_1=/path/to/subject.png \
  --slot image_2=/path/to/attire.png \
  --slot image_3=/path/to/scene.png \
  --slot lora_strength=0.0
```

## Notes on the graph

- Each variant shares nodes 1-15 (loaders + Lightning LoRA + user
  LoRA stack + `ModelSamplingAuraFlow` + `CFGNorm` + first `LoadImage`
  + `ImageScaleToTotalPixels` to ~1.5 MP + `VAEEncode` + the two
  `TextEncodeQwenImageEditPlus` conditioning nodes + `KSampler` +
  `VAEDecode` + `SaveImage`).
- The 2-image variant adds node `16` (`LoadImage`); the 3-image
  variant adds nodes `16` and `17`. Extra source images are wired
  directly into `image2`/`image3` of nodes `11` (negative) and `12`
  (positive) without re-scaling, matching the reference flow ComfyUI's
  `TextEncodeQwenImageEditPlus` author has shipped.
- The user LoRA at node 5 defaults to strength `0.0` so the manifest
  is safe to register on any server with the declared LoRA filename
  installed; users can opt in to a Qwen-Edit LoRA via the slot's
  `select` UI.
