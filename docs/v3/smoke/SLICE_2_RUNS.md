# Slice 2 (#4) - flux2_klein image_t2i smoke runs

ComfyUI: `http://172.27.1.165:8188` (RTX 5090, ComfyUI 0.21.0).

## Loader chain (the fix)

The original PR #14 used `DualCLIPLoader(type="flux2")`, which does not
exist on ComfyUI 0.21.0 (`type="flux2"` is only valid on the *single*
`CLIPLoader`). FLUX 2 Klein on 0.21 is driven by:

- `UNETLoader(unet_name="flux-2-klein-9b.safetensors")`
- `CLIPLoader(clip_name="qwen_3_8b_fp8mixed.safetensors", type="flux2")`
  - **Qwen 3 8B**, not Gemma. Confirmed live: a Gemma + flux2 chain
    fails at the model forward pass with `Input img and txt tensors
    must have 3 dimensions.` Qwen-3 8B emits the
    `[batch, 512, 12288]` conditioning the dual-stream architecture
    expects (see `capitan01R/ComfyUI-Flux2Klein-Enhancer` analysis).
- `VAELoader(vae_name="flux2-vae.safetensors")`
- `LoraLoaderModelOnly(lora_name="Klein-consistency.safetensors", strength_model=0.0)`
- `EmptyFlux2LatentImage(width, height, batch_size=1)`
- `KSampler(steps=20, cfg=1.0, sampler_name="euler", scheduler="simple")`
- `VAEDecode` -> `SaveImage`

Standard `KSampler` works fine; `Flux2Scheduler` +
`SamplerCustomAdvanced` is **not** required. cfg=1.0 means the
distilled FLUX path ignores the negative_prompt slot at sample time
while still surfacing it in the Setup UI.

## Run 1 - 2026-06-02 — green smoke (PR #14 fix)

```bash
COMFYUI_URL=http://172.27.1.165:8188 python scripts/v3_smoke.py \
    --manifest flux2_klein \
    --slot 'prompt=A red panda eating bamboo, photorealistic, soft natural light' \
    --slot 'width=1024' --slot 'height=1024' --slot 'seed=20260602'
```

| field        | value                                                                            |
| ------------ | -------------------------------------------------------------------------------- |
| status       | `SMOKE OK`                                                                       |
| prompt_id    | `e9335020-fc3f-4be1-a977-06ebf593f408`                                           |
| latency      | `9.00 s`                                                                         |
| output bytes | `1 940 463` (1.85 MB)                                                             |
| output path  | `output/v3_smoke/e9335020-fc3f-4be1-a977-06ebf593f408/flux2_klein_00001_.png`    |
| output role  | `output_image`                                                                   |
| output media | `image/png`                                                                      |
| steps logged | 1/20 -> 20/20 on node `8` (KSampler), then `9` (VAEDecode), `10` (SaveImage)     |

`requires` block satisfied against live `/object_info`:

- UNET: `flux-2-klein-9b.safetensors`
- VAE: `flux2-vae.safetensors`
- CLIP: `qwen_3_8b_fp8mixed.safetensors`

The two `unet` static-select alternatives
(`flux-2-klein-9b.safetensors`, `darkBeastMar2126Latest_dbkleinv2BFS.safetensors`)
both appear in `UNETLoader.unet_name` options on the live server, so
either choice satisfies `validate_requires`.
