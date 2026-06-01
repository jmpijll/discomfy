# DisComfy v3.0 - Scope

Derived from the live ComfyUI probe (`docs/v3/discovery.md`,
`docs/v3/workflows-static.md`) on 2026-06-01 against
`http://172.27.1.165:8188` (ComfyUI 0.21.0, RTX 5090, 32 GB VRAM).

## Headline reality check

Of the **13 workflow JSONs** currently in `workflows/`, exactly **one
(`qwen_image_2512_lora.json`)** still runs end-to-end against the user's
current model inventory. The other 12 reference models (`flux1-dev-fp8`,
`flux1-krea-dev`, `hidream_i1_full_fp8`, `qwen_image_edit_2509`,
`Wan2.1-VACE-14B-Q8_0.gguf`, ...), CLIPs (`clip_l`, `t5xxl_fp8`,
`clip_g_hidream`, `umt5-xxl-encoder-Q8_0.gguf`), or LoRAs (`ALEX`,
`wypk3`, `Qwen-Image-Edit-Lightning-4steps-V1.0`) that no longer exist on
the server.

This means v3 is not a "refactor existing workflows" job - it is a
"rebuild manifests against the current inventory" job. The old JSONs are
archaeology and most can be deleted in Slice 9.

## Live inventory snapshot (the design must respect this)

### Diffusion models (UNETLoader)

| File | Family | Use |
| --- | --- | --- |
| `flux-2-klein-9b.safetensors` | FLUX 2 Klein 9B | image t2i (primary) |
| `darkBeastMar2126Latest_dbkleinv2BFS.safetensors` | community Klein | image t2i |
| `qwen_image_2512_fp8_e4m3fn.safetensors` | Qwen-Image 2512 | image t2i |
| `qwen_image_2512_fp8_e4m3fn_scaled_comfyui_4steps_v1.0.safetensors` | Qwen 2512 distilled | image t2i fast |
| `qwen_image_edit_2511_fp8mixed.safetensors` | Qwen-Image-Edit 2511 | image edit |
| `wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8H.safetensors` | WAN 2.2 high-noise | video i2v/t2v |
| `wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8L.safetensors` | WAN 2.2 low-noise | video (paired with H) |

### Checkpoints (CheckpointLoaderSimple)

- `ltx-2.3-22b-dev-fp8.safetensors` (LTX-Video 2.3 22B - video t2v/i2v)

### VAEs

`ae.safetensors` (FLUX 1), `flux2-vae.safetensors` (FLUX 2),
`qwen_image_vae.safetensors`, `wan_2.1_vae.safetensors`, `pixel_space`.

### Text encoders / CLIPs

`gemma_3_12B_it[_fp4_mixed].safetensors`,
`mistral_3_small_flux2_fp8.safetensors`,
`qwen_2.5_vl_7b_fp8_scaled.safetensors`, `qwen_3_4b.safetensors`,
`qwen_3_8b_fp8mixed.safetensors`, `umt5_xxl_fp8_e4m3fn_scaled.safetensors`.

### LoRAs (16, abridged)

Klein-consistency, Qwen-Image-2512-Lightning-4steps, Qwen-Edit-2511-Lightning-4steps,
SVI_v2_PRO_Wan2.2-I2V-A14B HIGH+LOW, LTX-2.3 distilled-lora-384, plus
six `qwen_image_2512_*_lora_v1` content LoRAs.

### Custom node packs (top, by node count)

`RES4LYF` (294), `comfyui-kjnodes` (235), `Comfyroll_CustomNodes` (199),
`ComfyUI-Impact-Pack` (197), `comfyui_layerstyle` (169),
`ComfyUI-WanVideoWrapper` (146), `crt-nodes` (135), `ComfyUI-LTXVideo` (76),
`comfyui_essentials` (62), `comfyui-videohelpersuite` (40),
`comfyui-frame-interpolation` (16), `gguf` (13).

## In scope for v3.0

A workflow is **in scope** if it runs against the current inventory and at
least one user story below depends on it.

### Image (t2i)

- **FLUX 2 Klein 9B (LoRA)** - new primary t2i path. Replaces `flux_lora`,
  `flux_krea_lora`, `dype-flux-krea-lora` (none of which run anyway).
- **Qwen-Image 2512 (LoRA)** - already runs (`qwen_image_2512_lora.json`)
  via the existing JSON. Carry the JSON forward, write a v3 manifest for it.
- **Qwen-Image 2512 4-step distilled** - same model, distilled UNET +
  Lightning LoRA, sub-10s generations. Manifest variant of the above.

`HiDream` and `ZI Turbo` from v2.x are **out** - their UNETs/LoRAs are no
longer installed.

### Image (edit)

- **FLUX Kontext** - all four `FluxKontext*` nodes are present
  (`FluxKontextImageScale`, `FluxKontextMaxImageNode`,
  `FluxKontextProImageNode`, `FluxKontextMultiReferenceLatentMethod`). The
  existing `flux_kontext_edit.json` references a missing UNET; rebuild
  against `flux-2-klein-9b` (Kontext is a node-graph pattern, not a
  separate model - confirm in tracer-bullet smoke).
- **Qwen-Image-Edit 2511** - eight `TextEncodeQwenImageEdit*` variants
  available. Replace the three near-duplicate `qwen_image_edit*.json`
  files with **one** parameterized manifest that exposes 1-3 image slots
  (Slice 3).

### Image (upscale)

- **In scope** as a Modality, but **gated**: `UpscaleModelLoader` returned
  zero models on probe. v3.0 lands the Modality with two paths:
  1. **Latent upscale** (`LatentUpscaleBy` + tiled VAE decode) - works now,
     no extra models needed.
  2. **Pixel upscale** (`ImageUpscaleWithModel` + UltimateSDUpscale) -
     requires user to drop a `.pth` into `ComfyUI/models/upscale_models/`.
     The manifest declares a `requires.upscale_models` precondition that
     `Manifest` registration will refuse if the inventory is empty.

### Video

- **WAN 2.2 i2v** - HIGH+LOW noise pair UNETs present, SVI_v2_PRO LoRA pair
  available, `WanVaceToVideo` node exists, `VHS_VideoCombine` for output.
  Slice 5.
- **LTX-Video 2.3 22B t2v/i2v** - full LTX node pack (`CRTAutoDLLTX23*`,
  `LTX2*`, 76 LTXVideo nodes, plus matching checkpoint). Slice 6.
- **WAN VACE 14B (existing repo workflow)** - **out**. The Q8 GGUF is not
  installed and Wan 2.2 is the active line.

### Audio TTS

- **Fish-Speech (FishS2*)** - `FishS2TTS`, `FishS2VoiceCloneTTS`,
  `FishS2MultiSpeakerTTS`, `FishS2MultiSpeakerSplitTTS` present. **This
  is the v3.0 TTS pick**, not F5-TTS as originally guessed in the plan.
  Slice 7.
- Out: F5-TTS, ChatterboxTTS - not installed.
- Deferred: ElevenLabs / Stability TTS - external API, requires key
  management, scoped to v3.x.

### Audio music / SFX

- **ACE-Step 1.5** - `EmptyAceStep1.5LatentAudio`,
  `TextEncodeAceStepAudio1.5`, decoded via `VAEDecodeAudio`. Generation is
  a regular `KSampler` over an audio latent. Slice 8.
- Deferred: Stability text-to-audio (`StabilityTextToAudio`) - external
  API, v3.x.

## Out of scope for v3.0

- **Text generation** as a Modality. The Discord bot does not need to
  produce text outputs. `vision` nodes (`AILab_QwenVL*`) may be used
  internally for prompt expansion in a v3.x quality-of-life pass.
- **External API modalities** (ElevenLabs, Stability, BFL, Recraft, Vidu,
  Bytedance, Kling). The bot stays self-hosted-ComfyUI-only in v3.0.
- **Image-to-image (i2i)** as a top-level Modality distinct from `image_edit`.
  If `image_edit` covers it, we don't add a third bucket.
- **AnimateDiff / Mochi / Cosmos / HunyuanVideo** video models - even
  though their nodes are installed, the user's actual checkpoints/UNETs
  for those are not provisioned. Reassess in v3.x.
- **HiDream**, **ZI Turbo**, original FLUX 1 (dev / krea / DyPE-on-krea) -
  models are gone. The corresponding workflow JSONs and the per-model
  branches in `core/`, `bot/ui/generation/` will be deleted in Slice 9.
- **`hidream_full_config-1.json`** - explicitly delete; both the model and
  the no-LoRA variant are dominated.
- Two of the three near-duplicate `qwen_image_edit_*.json` files - merged
  into one parameterized manifest in Slice 3.

## Slice mapping (becomes Phase 4 issues)

| Slice | Modality | Workflow | Notes |
| ---: | --- | --- | --- |
| 1 | image_t2i | Qwen-Image 2512 (4-step) | tracer-bullet; carries `qwen_image_2512_lora.json` |
| 2 | image_t2i | FLUX 2 Klein 9B (LoRA) | new primary t2i, replaces FLUX 1 family |
| 3 | image_edit | Qwen-Image-Edit 2511 (1-3 inputs) | one manifest with image_count slot |
| 3b | image_edit | FLUX Kontext on Klein | second manifest |
| 4 | image_upscale | latent + UltimateSDUpscale | conditional on upscale_models |
| 5 | video | WAN 2.2 i2v (HIGH+LOW LoRA pair) | Slice 5 |
| 6 | video | LTX-Video 2.3 22B t2v/i2v | Slice 6 |
| 7 | audio_tts | Fish-Speech (FishS2VoiceCloneTTS as default) | Slice 7 |
| 8 | audio_music | ACE-Step 1.5 | Slice 8 |
| 9 | - | delete v2 dead workflows + per-model branches | cleanup |
| 10 | - | release v3.0 | tag + Docker + docs |

## Open questions surfaced by discovery

These do not block ADRs but go into the PRD risk register.

1. The two FLUX 2 Klein UNETs differ by LoRA bake-in (vanilla vs. dbklein).
   Which should be the v3.0 default? Default to vanilla `flux-2-klein-9b`,
   expose the other as a model-selection slot.
2. WAN 2.2 i2v normally takes a HIGH-noise + LOW-noise UNET pair through
   two sequential KSamplers. The Manifest spec needs to support multi-UNET
   workflows; ADR-001 must include an example.
3. ACE-Step audio uses `VAEDecodeAudio` which requires a separate audio
   VAE (none enumerated by `VAELoader`). Confirm it ships embedded with the
   ACE-Step model or document the extra-asset requirement.
4. `UpscaleModelLoader` returned zero options. Confirm with user whether
   this is intentional (latent-only upscale) or models simply weren't put
   into `models/upscale_models/`.
5. There is no `comfyui-frame-interpolation` UNET-style model exposure;
   `RIFE VFI` is a code-only node. Confirm Slice 5 (WAN i2v) ships with
   RIFE-based smoothing as in the v2 video workflow.
