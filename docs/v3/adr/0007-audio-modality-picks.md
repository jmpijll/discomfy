# ADR-0007: Audio modality - Fish-Speech for TTS, ACE-Step for music

**Status:** accepted (v3.0 design phase, 2026-06-01)

## Context

The Phase 0 plan guessed at `F5-TTS` (TTS) and `ACE-Step / Stable Audio
Open` (music) as audio picks. The Phase 1 live probe confirmed that
**F5-TTS is not installed** on the user's ComfyUI server, but a complete
Fish-Speech S2 node pack is, alongside ACE-Step 1.5 + Stable Audio.
Picks must follow the actual install, not assumptions.

## Decision

### TTS: Fish-Speech S2

The live `/object_info` registers four Fish-Speech nodes:

- `FishS2TTS` - text -> audio with a built-in voice
- `FishS2VoiceCloneTTS` - text + reference audio -> cloned voice
- `FishS2MultiSpeakerTTS` - script with speaker tags -> multi-voice audio
- `FishS2MultiSpeakerSplitTTS` - same, but emits per-speaker tracks

v3.0 ships **two manifests** under `modality: audio_tts`:

1. `audio_tts_fish_simple.yaml` - `FishS2TTS`, slot for prompt text only,
   default voice. Tracer-bullet for the audio Modality plugin (Slice 7).
2. `audio_tts_fish_voiceclone.yaml` - `FishS2VoiceCloneTTS`, adds a
   reference-audio attachment slot. Demonstrates Plugin handling of
   audio-input slots, not just image-input slots.

`FishS2MultiSpeaker*` is deferred to v3.x. It would need a custom
modality_input parser for the speaker-tagged script format.

### Music / SFX: ACE-Step 1.5

Live nodes confirm an ACE-Step pipeline:

- `EmptyAceStep1.5LatentAudio` - latent allocation (1.5 is the current
  ACE-Step generation; the older `EmptyAceStepLatentAudio` is also
  present as a fallback)
- `TextEncodeAceStepAudio1.5` - text conditioning
- standard `KSampler` over the audio latent
- `VAEDecodeAudio` -> `SaveAudioMP3`

v3.0 ships **one manifest** under `modality: audio_music`:

1. `audio_music_acestep.yaml` - prompt text + duration in seconds + seed
   slots; outputs MP3 with duration label (Slice 8).

Stable Audio remains documented but deferred:
`ConditioningStableAudio` is the only Stable Audio node currently
exposed, and it requires a Stable Audio Open checkpoint that is not in
the user's checkpoint inventory. Adding it later means dropping the
checkpoint file in and writing a manifest - zero code change.

### Plugin architecture

- One Modality Plugin per audio kind: `core/modalities/audio_tts/` and
  `core/modalities/audio_music/`. They share an `audio_common.py` for
  Discord MP3 packaging, duration metadata extraction, and waveform
  preview generation.
- Output rendering posts the audio file as a Discord attachment with an
  embed showing duration and a waveform PNG generated server-side via
  `ffmpeg` (already a transitive dep via `imageio-ffmpeg`).
- Discord file size cap is 25 MB; ACE-Step at default settings produces
  < 5 MB MP3, Fish-Speech < 2 MB. No compression ladder needed for
  v3.0.
- Reference audio uploads (`FishS2VoiceCloneTTS`) go through ComfyUI's
  `/upload/audio` endpoint, which the v2 client doesn't use today;
  ADR-0004's `core/comfyui/http.py` adds an `upload_audio` method.

## Consequences

- The first audio-anything ships in Slice 7 (TTS simple), validating
  end-to-end audio handling. Slice 8 then adds music with confidence
  the Plugin shape is right.
- We do not own a TTS or music model upgrade path; both ride on the
  user's ComfyUI install.
- If the user uninstalls Fish-Speech or ACE-Step, the manifests fail
  registration and the `/tts` / `/music` slash commands return "no
  workflow available for this Modality" instead of crashing.

## Rejected alternatives

- **F5-TTS** (original plan guess) - **not installed** on the live server.
  The static analysis would have produced a runtime error on first
  invocation.
- **Chatterbox / Piper / KokoroTTS** - none installed.
- **Kugel-Audio TTS** - installed (`KugelAudioTTSNode`,
  `KugelAudioVoiceCloneNode`) but the node interface is less stable than
  Fish-Speech and the upstream project has had breaking changes within
  the last quarter. Picked Fish-Speech for stability; revisit in v3.x.
- **ElevenLabs / Stability TTS** (external API nodes are present) -
  out of scope per ADR-0006: v3.0 stays self-hosted-ComfyUI-only.
- **Stable Audio Open as the music default** - underlying Stable Audio
  checkpoint is not in the user's `models/checkpoints/`. ACE-Step is
  fully provisioned (UNET via the standard path, conditioning + decode
  nodes installed) and is the right default.
