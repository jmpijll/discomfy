# ADR-0002: Modality plugins, not per-model branches

**Status:** accepted (v3.0 design phase, 2026-06-01)

## Context

v2.x has switch statements on `model_type` scattered across at least 11
files. Adding video meant adding a `VideoGenerator` class with a parallel
copy of much of `ImageGenerator`'s logic. Adding audio would require a
third copy. The bot's behaviour _per modality_ (how progress is rendered,
how outputs are posted to Discord, what post-Run buttons make sense) is
genuinely modality-specific; the bot's behaviour _per model_ within a
modality almost always isn't.

## Decision

A **Plugin** is a Python module under `core/modalities/<modality>/` that
implements a fixed `ModalityPlugin` Protocol. The Modality Registry maps
each `Modality` enum value to exactly one Plugin instance. There is one
Plugin per Modality; there is no per-model code.

```python
# core/modalities/base.py (sketch - real version lives in code)
class ModalityPlugin(Protocol):
    modality: Modality          # IMAGE_T2I, IMAGE_EDIT, IMAGE_UPSCALE, VIDEO, AUDIO_TTS, AUDIO_MUSIC
    output_media: list[str]     # ["image/png"], ["video/mp4"], ["audio/mp3"], ...

    async def validate_slot_values(
        self, manifest: Manifest, values: SlotValues
    ) -> SlotValues: ...
    """Type-coerce + run validation rules from manifest. Return canonical values."""

    def progress_mapper(self) -> ProgressMapper: ...
    """Translate ComfyUI WS events for this modality into a 0-100 percent stream."""

    async def render_outputs(
        self, run: Run, outputs: list[Output]
    ) -> DiscordPayload: ...
    """Build the Discord message (embed + files) that posts the Run's outputs."""

    def default_post_actions(self, manifest: Manifest) -> list[Action]: ...
    """Modality-default Action buttons (manifest can override)."""
```

### What lives in the Plugin (modality-specific)

- **Image plugin**: PNG vs. JPG decision, lossless-then-lossy compression
  ladder for Discord 25 MB cap, post-Run buttons (Upscale, Animate, Edit,
  Re-roll seed). One ProgressMapper based on KSampler step events.
- **Video plugin**: MP4 attachment vs. uploaded link if > 25 MB, thumbnail
  generation via `ffmpeg`, post-Run buttons (Upscale frame, Re-roll seed).
  ProgressMapper combines image-style step % with frame count.
- **Audio TTS plugin**: MP3 fallback for Discord, attachment with waveform
  preview, post-Run buttons (Re-generate, Edit voice). ProgressMapper
  reflects single-pass generation.
- **Audio music plugin**: MP3 + duration label, post-Run buttons (Extend,
  Re-roll). ProgressMapper similar to TTS.
- **Image upscale plugin**: identical output rendering to image t2i but
  different defaults and no Upscale-of-Upscale chain (action elision).

### What does NOT live in the Plugin

- Knowledge of FLUX vs. Qwen vs. WAN. Plugins read the Manifest, not the
  model name.
- HTTP/WebSocket details. The Plugin receives a `Run` (already executing)
  and ComfyUI events arrive as a typed stream.
- Discord plumbing beyond `DiscordPayload`. The bot layer handles
  interaction lifecycle, deferral, edits, error handling.

## Consequences

- Adding "image t2i with FLUX 2 Klein" requires writing a manifest and
  zero Python.
- Adding "audio TTS" requires writing one Plugin (`core/modalities/audio_tts/`)
  plus one or more manifests.
- Per-model modal subclasses go away (ADR-0003).
- The Plugin is unit-testable in isolation; a Modality Plugin's correctness
  doesn't depend on a running ComfyUI.

## Rejected alternatives

- **Per-workflow Strategy classes** - what we have now. The whole point
  is to stop branching per model.
- **Single mega-Plugin with `modality` switch inside** - resurrects the
  switch statement we are escaping.
- **Plugin per output type (image vs. video vs. audio)** - too coarse.
  Image t2i and image upscale share an output type (`image/png`) but
  meaningfully different action buttons and validation. Image edit is
  also "image out" but its inputs include 1-N source images. Splitting
  by Modality (which is output + intent) maps cleanly to Discord UX.
