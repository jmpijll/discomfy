# Slice 8 (issue #10) - audio_music smoke runs

**Branch:** `slice/10-acestep`
**Modality:** `audio_music`
**Manifests under test:**
- `audio_music_acestep` (`workflows/audio_music_acestep.json`)

**ComfyUI target:** `http://172.27.1.165:8188`
**Worktree:** `/Users/jamievanderpijll/discomfy-slice-8-ace`

## Status: BLOCKED - ACE-Step 1.5 checkpoint not installed on server

Live `/object_info` from `http://172.27.1.165:8188` confirms the
ACE-Step Pack is present (the `comfy_extras.nodes_ace` python_module
registers `EmptyAceStep1.5LatentAudio`, `TextEncodeAceStepAudio1.5`,
`VAEDecodeAudio`), but the actual checkpoint file
`ace_step_1.5_turbo_aio.safetensors` is **not** in any of the model
folders the server exposes:

- `GET /models/checkpoints` -> `['ltx-2.3-22b-dev-fp8.safetensors']`
- `GET /models/diffusion_models` -> no `acestep_*` or `ace_*` entries
- `GET /models/vae` -> no `ace_*` entries
- `GET /models/text_encoders` -> no `qwen_*_ace15` entries

Attempting to queue the manifest therefore fails at the requires
gate, before any prompt is sent:

```
$ python scripts/v3_smoke.py --manifest audio_music_acestep \
    --slot prompt="upbeat electronic synthwave, 120 bpm, melodic" \
    --slot seconds=10 --slot seed=42
SMOKE FAILED: manifest 'audio_music_acestep' has unmet requires:
  - missing checkpoint: ace_step_1.5_turbo_aio.safetensors
```

This matches the open question raised in
[`docs/v3/scope.md`](../scope.md) item 3
("ACE-Step audio uses `VAEDecodeAudio` which requires a separate audio
VAE... Confirm it ships embedded with the ACE-Step model or document
the extra-asset requirement"). The Comfy-Org AIO repackaged variant
embeds the audio VAE in a single checkpoint, so installing one file
unblocks the slice.

Attempting to use the ComfyUI-Manager `/manager/queue/install_model`
endpoint for an automated install was rejected ("Invalid model install
request is detected") because the AIO checkpoint is not on the
Manager's curated whitelist. Manual install by the operator is the
unblock path.

### To unblock

On the ComfyUI host, download the AIO checkpoint and drop it into
`ComfyUI/models/checkpoints/`:

```
# Linux / macOS
wget -O ComfyUI/models/checkpoints/ace_step_1.5_turbo_aio.safetensors \
  https://huggingface.co/Comfy-Org/ace_step_1.5_ComfyUI_files/resolve/main/checkpoints/ace_step_1.5_turbo_aio.safetensors

# Windows (PowerShell)
Invoke-WebRequest `
  -Uri https://huggingface.co/Comfy-Org/ace_step_1.5_ComfyUI_files/resolve/main/checkpoints/ace_step_1.5_turbo_aio.safetensors `
  -OutFile ComfyUI\models\checkpoints\ace_step_1.5_turbo_aio.safetensors
```

The file is ~6.5 GB. ComfyUI will pick it up on the next `/object_info`
fetch; no server restart is required because `CheckpointLoaderSimple`
reads `models/checkpoints/` lazily.

## Reproducing the smoke once the model is installed

```bash
source venv/bin/activate

python scripts/v3_smoke.py \
  --manifest audio_music_acestep \
  --slot prompt="upbeat electronic synthwave, 120 bpm, melodic" \
  --slot seconds=10 \
  --slot seed=42
```

Expected:

- `apply_slots` writes `prompt` into node 3 (`tags`),
  `negative_prompt` into node 4 (`tags`), `seconds` into node 2
  (`seconds`) and nodes 3/4 (`duration`), and `seed` into node 5
  (`seed`).
- `KSampler` (node 5) emits 8 `Progress` events; the
  `_StepAwareProgressMapper` reports 1% on first executing event and
  scales linearly into 99% as steps complete, pinned to 100% on
  `ExecutionComplete`.
- `SaveAudioMP3` (node 7) writes one `.mp3` to the ComfyUI output
  folder; the smoke downloads it to `output/v3_smoke/<prompt_id>/`.

### What to capture

For each run, fill in a row in the table below before merging:

| run | prompt_id | output_path | bytes | duration_s | latency_s |
| --- | --- | --- | --- | --- | --- |
| acestep_synthwave | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

### Acceptance evidence

- [ ] `audio_music_acestep` smoke produced an MP3 under `output/v3_smoke/<prompt_id>/`.
- [ ] Smoke wall-clock latency under 60 s for a 10 s clip (RTX 5090, 8 steps).
- [ ] `package_for_discord` reports a positive duration (ffmpeg or
      `wave` fallback) and the file is under Discord's 25 MB cap.
- [ ] No `model_type` / `DyPE` / `hidream` / `krea` strings introduced
      in code (`grep -E 'model_type|DyPE|hidream|krea' core/ bot/`
      returns nothing new).

## Notes for the live smoke runner

- `core/modalities/audio_common.py` is shared with `audio_tts`; no
  changes are required for ACE-Step. The Plugin's renderer reuses
  `package_for_discord` and `render_waveform_png`.
- The manifest exposes `seconds` as a single Slot with three NodeMap
  targets (`EmptyAceStep1.5LatentAudio.seconds`,
  `TextEncodeAceStepAudio1.5.duration` on the positive encoder, and
  the same on the negative encoder). The applier writes the value to
  all three so the latent allocation and the encoded conditioning
  agree on the clip length.
- ACE-Step 1.5's `generate_audio_codes` flag is set to `false` in the
  workflow JSON. Enabling it improves quality but adds 30-90 s of LLM
  inference per Run; the tracer-bullet keeps it off so the smoke is
  fast.
