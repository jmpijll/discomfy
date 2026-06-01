# Slice 4 (#6) - image_upscale smoke runs

**Status:** `TODO_SMOKE` - ComfyUI at `http://172.27.1.165:8188`
was unreachable from the agent's network at the time the slice was
implemented (`curl http://172.27.1.165:8188/system_stats` timed out
after 5s). Defer smoke per the same rule applied to Slice 2; the
orchestrator runs deferred smokes from a node with network access to
the user's ComfyUI box.

## Planned commands

```bash
# 1. Generate a source image with the Slice 1 manifest.
python scripts/v3_smoke.py \
    --manifest qwen_image_2512 \
    --slot prompt="a single red panda eating bamboo in a bamboo forest, sharp, detailed"

# 2. Capture the path of the resulting PNG, e.g.
#    output/v3_smoke/<prompt_id>/qwen_image_2512_00001_.png
# 3. Upscale it with the latent manifest (uploads via the v3_smoke harness extension).
python scripts/v3_smoke.py \
    --manifest image_upscale_latent \
    --slot source_image=output/v3_smoke/<prompt_id>/qwen_image_2512_00001_.png \
    --slot scale_by=2.0
```

## What to record once the smoke runs

For each Run capture:

- `prompt_id` from ComfyUI
- output path under `output/v3_smoke/<prompt_id>/`
- output byte count
- wall-clock latency reported by `v3_smoke.py`
- whether `_upload_image_slots` returned a server-side filename for
  the `source_image` slot (line in logs: `uploaded slot 'source_image' file ... as ... (N bytes)`)

The `image_upscale_pixel_ultimate` manifest is conditionally registered;
its smoke is OPTIONAL until the operator installs an upscale model
(e.g. `4x_foolhardy_Remacri.pth` under `ComfyUI/models/upscale_models`).
Until then, `pytest tests/test_upscale_manifest_loading.py::TestPixelManifestIsConditional`
verifies it stays disabled.

---

## Slice 6 (#8) - LTX-Video 2.3 22B t2v + i2v smoke runs

**Status:** `LIVE_OK` - both manifests ran end-to-end against
`http://172.27.1.165:8188` from worktree
`/Users/jamievanderpijll/discomfy-slice-6-ltx`.

### Server-side findings (recorded so the next slice picks them up)

While iterating on the workflow we hit two server-side issues that the
`/object_info` discovery alone could not predict:

1. **`LTXVGemmaCLIPModelLoader` fails with `No files matching pattern 'tokenizer.model' ...`.**
   The custom node expects a Gemma `tokenizer.model` sentencepiece file
   bundled next to the safetensors weights. The server is missing it.
   Replacement: the LTX 2.x successor `LTXAVTextEncoderLoader`
   (`text_encoder=gemma_3_12B_it.safetensors`, `ckpt_name=ltx-2.3-22b-dev-fp8.safetensors`)
   loads the same Gemma weights without that file and exports a
   standard `CLIP` socket compatible with `CLIPTextEncode`.
2. **`LTXVQ8LoraModelLoader` fails with `name 'hadamard_transform' is not defined`.**
   The Q8 loader's runtime path imports `hadamard_transform` (a CUDA
   kernel from `fast-hadamard-transform`) that is not installed on this
   server. Replacement: plain `LoraLoaderModelOnly` accepts the same
   `ltx-2.3-22b-distilled-lora-384.safetensors` file and produces
   equivalent output for non-quantized use; switching loaders cost no
   model files and dropped the dependency to "stock ComfyUI".
3. **`LTXVGemmaEnhancePrompt` raised `min() iterable argument is empty`**
   when fed the `LTXAVTextEncoderLoader`'s CLIP. Skipped; the user's
   prompt is fed straight into `CLIPTextEncode`. If the operator wants
   prompt enhancement back, install Gemma's `tokenizer.model` so
   `LTXVGemmaCLIPModelLoader` becomes usable and switch the manifest's
   `prompt` target back to its `prompt` field.

These are logged here so a follow-up slice can fix the server install
or revise the manifests once the Gemma tokenizer + Q8 dep land.

### 1. T2V

```bash
COMFYUI_URL=http://172.27.1.165:8188 python scripts/v3_smoke.py \
    --manifest ltxv_2_3_22b_t2v \
    --slot prompt="a slow cinematic dolly across a foggy harbor at sunrise, gentle waves, soft golden light" \
    --slot width=768 --slot height=512 \
    --slot frame_count=49 \
    --slot seed=12345 \
    --timeout 900
```

- `prompt_id`: `5955945b-0162-4730-b886-99d82c1a42ca`
- output: `output/v3_smoke/5955945b-0162-4730-b886-99d82c1a42ca/ltxv_2_3_22b_t2v_00001.mp4`
- size: `384576` bytes (~376 KB)
- wall-clock latency: `33.04 s`
- progress shape: one `SamplerCustomAdvanced` `progress` stream (node 14, 1/8 -> 8/8 over ~16 s), then `VAEDecode` (node 15) + `VHS_VideoCombine` (node 16) as post-sample Executing events, then `ExecutionComplete`. The shared `VideoPlugin` `_DualSamplerProgressMapper` happily handled the single-stream variant - no code changes required (see `tests/test_video_plugin_ltx_compat.py::TestSingleSamplerProgressMapping`).

### 2. I2V (chained from `qwen_image_2512`)

The harness uploads the local source image via `/upload/image` and
rewrites the `init_image` slot to the server-side filename before
`apply_slots`:

```bash
# First generate a source image with Qwen-Image 2512.
COMFYUI_URL=http://172.27.1.165:8188 python scripts/v3_smoke.py \
    --manifest qwen_image_2512 \
    --slot prompt="a single fluffy red panda standing on a moss-covered log in a misty forest at dawn, soft cinematic light, shallow depth of field" \
    --slot width=1024 --slot height=1024 \
    --slot seed=99
# -> prompt_id=402f9033-617c-4413-8d2d-b39128c974ec
# -> output/v3_smoke/402f9033-617c-4413-8d2d-b39128c974ec/final_output_00008_.png  (3126261 bytes)

# Now animate it with LTX-Video 2.3 22B i2v.
COMFYUI_URL=http://172.27.1.165:8188 python scripts/v3_smoke.py \
    --manifest ltxv_2_3_22b_i2v \
    --slot prompt="the red panda slowly turns its head toward the camera, soft breeze ruffling its fur, gentle drifting mist" \
    --slot init_image=output/v3_smoke/402f9033-617c-4413-8d2d-b39128c974ec/final_output_00008_.png \
    --slot width=768 --slot height=768 \
    --slot frame_count=49 \
    --slot seed=55 \
    --timeout 900
```

- `prompt_id` (qwen source image): `402f9033-617c-4413-8d2d-b39128c974ec`
- `prompt_id` (LTX i2v): `c043322d-886f-44da-902c-ce978248eb67`
- output: `output/v3_smoke/c043322d-886f-44da-902c-ce978248eb67/ltxv_2_3_22b_i2v_00001.mp4`
- size: `470635` bytes (~459 KB)
- wall-clock latency: `42.85 s` (i2v Run only - excludes qwen source image generation)
- the `init_image` slot was uploaded as `final_output_00008_.png` (`3126261` bytes) by `_upload_image_slots` and the slot value was rewritten before `apply_slots`. The `LTXVImgToVideo` node (id "9") then conditioned the latent on the uploaded frame.

### Plugin reuse

No `VideoPlugin` changes. The slice 5 dual-sampler progress mapper
sums per-node `Progress` streams and gracefully degrades to a single
stream for LTX's `SamplerCustomAdvanced`. The `validate_slot_values`
coercion + bound enforcement and the MP4 `render_outputs` pipeline
work as-is against the LTX manifests. See
`tests/test_video_plugin_ltx_compat.py` for the synthetic stream and
slot-validation coverage.

