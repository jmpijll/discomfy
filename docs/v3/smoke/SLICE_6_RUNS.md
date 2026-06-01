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
