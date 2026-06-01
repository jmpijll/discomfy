# Slice 9 (issue #9) - audio_tts smoke runs

**Branch:** `slice/9-fish-tts`
**Modality:** `audio_tts`
**Manifests under test:**
- `audio_tts_fish_simple` (`workflows/audio_tts_fish_simple.json`)
- `audio_tts_fish_voiceclone` (`workflows/audio_tts_fish_voiceclone.json`)

**ComfyUI target:** `http://172.27.1.165:8188`

## Status: TODO_SMOKE - DEFERRED

Live ComfyUI was not reachable from the agent worktree at the time of
this slice. The TCP probe to `172.27.1.165:8188` timed out twice during
the slice (once before implementation, once before smoke).

Per `AGENTS.md` ("Never skip the live smoke") and the slice
instructions ("If ComfyUI unreachable: defer per the standard rule"),
the live smoke is deferred. The smoke must be run by the maintainer
(or a follow-up agent on a network with access to the ComfyUI host)
before merging this PR.

### Reproducing the smoke when ComfyUI is reachable

```bash
source venv/bin/activate

# Simple Fish-Speech TTS (uses the built-in s2-pro voice).
python scripts/v3_smoke.py \
  --manifest audio_tts_fish_simple \
  --slot text="Hello world, this is a Fish-Speech tracer-bullet smoke." \
  --slot seed=42

# Voice-clone Fish-Speech TTS.
# Provide a 5-30s reference clip; the helper line below makes a short
# 440Hz sine reference if no real clip is available.
ffmpeg -y -f lavfi -i sine=frequency=440:duration=5 /tmp/ref.wav

python scripts/v3_smoke.py \
  --manifest audio_tts_fish_voiceclone \
  --slot text="Voice-cloning tracer bullet via Fish-Speech S2." \
  --slot voice_reference=/tmp/ref.wav \
  --slot seed=7
```

### What to capture

For each run, fill in a row in the table below before merging:

| run | manifest | prompt_id | output_path | bytes | duration_s | latency_s |
| --- | --- | --- | --- | --- | --- | --- |
| simple | audio_tts_fish_simple | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |
| voiceclone | audio_tts_fish_voiceclone | _TBD_ | _TBD_ | _TBD_ | _TBD_ | _TBD_ |

### Acceptance evidence

- [ ] `audio_tts_fish_simple` smoke produced an MP3 under `output/v3_smoke/<prompt_id>/`.
- [ ] `audio_tts_fish_voiceclone` smoke uploaded the reference audio
      via `upload_audio` and produced an MP3 in the cloned voice.
- [ ] Both runs reported a non-negative duration in `package_for_discord`.
- [ ] No `model_type`/`DyPE`/`hidream`/`krea` strings introduced in code.

## Notes for the live smoke runner

- `core/modalities/audio_common.py` ships ffmpeg-aware duration probing
  and waveform PNG rendering. On a host without ffmpeg / ffprobe, the
  duration falls back to a `wave` stdlib probe for WAV files (returns
  `-1.0` for MP3/FLAC) and waveform rendering returns `None`. The
  Plugin tolerates both cases - the Discord embed shows `Duration:
  unknown` and posts the audio without a preview.
- `imageio-ffmpeg` is already a transitive dep and bundles a private
  ffmpeg binary; `audio_common._find_ffmpeg` falls back to it when
  `$PATH` has no ffmpeg.
- `scripts/v3_smoke.py` now uploads any `audio` Slot whose value
  resolves to a local file before queuing the workflow, replacing the
  override with the filename ComfyUI assigned. Already-uploaded names
  (no path separator, file not present locally) are passed through.
