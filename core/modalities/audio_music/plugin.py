"""AudioMusic Modality Plugin (ADR-0002, ADR-0007).

Modality contract:

- ``output_media``: ``["audio/mpeg"]``. Manifests must declare an MP3
  output (typically via ``SaveAudioMP3``); WAV-emitting workflows are
  expected to chain through
  :func:`core.modalities.audio_common.transcode_to_mp3` before the
  renderer is invoked. Mirrors the audio_tts contract so the v3
  Discord renderer can dispatch by Modality without special-casing.
- Validator: coerces TEXT / FLOAT / INT / SEED slots through the
  shared helper and applies manifest ``validation`` rules. ACE-Step
  manifests do not currently expose audio-input slots (no reference
  audio), but the helper tolerates them in case a future music
  manifest accepts a melody seed.
- ProgressMapper: ACE-Step samples through the standard ``KSampler``
  node, which streams ``Progress(value, max)`` events for every step.
  The mapper scales those directly into the 0..100 band and is
  monotone, so jitter in event ordering never moves the bar backward.
  The sampler node id is exposed via :attr:`KSAMPLER_NODE_ID_DEFAULT`
  so the bot's renderer can label the current phase.
- Renderer: posts the MP3 as a Discord attachment plus an embed with
  the tag prompt, declared duration, seed, and (when ffmpeg is
  available) a waveform PNG preview. Reuses the shared
  :func:`core.modalities.audio_common.package_for_discord` helper.
- Default actions: respects the Manifest's declared Actions verbatim.
  v3.0 ACE-Step manifests ship with no Actions; future re-roll
  buttons will be authored in YAML.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.manifest.roles import Modality, Role
from core.manifest.schema import Action, Manifest, SlotType
from core.modalities.audio_common import (
    AudioPackage,
    package_for_discord,
)
from core.modalities.base import (
    ProgressMapper,
    SlotValueValidationError,
    SlotValues,
    coerce_slot_values_against_manifest,
    enforce_validation_rules,
)
from core.run import DiscordFile, DiscordPayload, Output, Run

WAVEFORM_FILENAME_TEMPLATE = "{stem}_waveform.png"
"""Filename pattern used for the optional waveform preview attachment."""

KSAMPLER_NODE_ID_DEFAULT = "5"
"""Workflow node id of the ACE-Step KSampler in the shipped manifest.

The Discord renderer can display "Sampling (node 5)" while the
progress events advance. Bumping this requires re-authoring the
workflow JSON; it is intentionally exposed as a constant so the UI
can render a descriptive label without re-parsing the manifest.
"""

_ACCEPTED_AUDIO_DICT_KEYS = {"filename", "mime", "data"}


class _StepAwareProgressMapper:
    """Monotone progress for ACE-Step KSampler runs.

    ACE-Step always samples through a single KSampler node and emits
    one ``Progress`` event per denoising step. The strategy:

    - ``Reconnected`` / unrelated events: return the last percentage
      (no UI churn).
    - First ``Executing`` for a real node: 1% (lets the user see the
      run picked up before any step has emitted).
    - ``Progress`` events on any node: scale ``value/max`` linearly
      into 1..99% and report monotone.
    - ``ExecutionComplete`` or ``Executing(node=None)``: 100%.
    """

    def __init__(self) -> None:
        self._last_pct: int | None = None
        self._seen_node_executing: bool = False
        self._complete: bool = False

    def update(self, event: Any) -> int | None:
        from core.comfyui.v3.ws import (
            Executing,
            ExecutionComplete,
            Progress,
            Reconnected,
        )

        if isinstance(event, Reconnected):
            return self._last_pct

        if isinstance(event, ExecutionComplete):
            self._complete = True
            return self._maybe_set(100)

        if isinstance(event, Executing):
            if event.node is None and event.prompt_id:
                self._complete = True
                return self._maybe_set(100)
            if not self._seen_node_executing:
                self._seen_node_executing = True
                return self._maybe_set(1)
            return None

        if isinstance(event, Progress):
            max_steps = max(int(event.max), 1)
            value = max(0, min(int(event.value), max_steps))
            band_pct = int(1 + (value / max_steps) * 98)
            return self._maybe_set(band_pct)

        return None

    def _maybe_set(self, pct: int) -> int | None:
        pct = max(0, min(100, pct))
        if self._last_pct is not None and pct < self._last_pct:
            pct = self._last_pct
        if pct == self._last_pct:
            return None
        self._last_pct = pct
        return pct


class AudioMusicPlugin:
    """Plugin for the ``audio_music`` Modality. ADR-0002 contract."""

    modality: Modality = Modality.AUDIO_MUSIC
    output_media: list[str] = ["audio/mpeg"]

    async def validate_slot_values(
        self, manifest: Manifest, values: SlotValues
    ) -> SlotValues:
        coerced = coerce_slot_values_against_manifest(manifest, values)
        coerced = self._coerce_audio_slots(manifest, coerced)
        enforce_validation_rules(manifest, coerced)
        self._enforce_audio_mime_accepts(manifest, coerced)
        return coerced

    def progress_mapper(self) -> ProgressMapper:
        return _StepAwareProgressMapper()

    async def render_outputs(
        self, run: Run, outputs: list[Output]
    ) -> DiscordPayload:
        audio_outputs = [o for o in outputs if o.role == Role.OUTPUT_AUDIO]
        files: list[DiscordFile] = []
        durations: list[str] = []
        oversize_notes: list[str] = []

        for o in audio_outputs:
            try:
                pkg = package_for_discord(o.path, o.media)
            except FileNotFoundError:
                pkg = AudioPackage(
                    filename=o.filename,
                    content_type=o.media,
                    data=o.bytes_read,
                    duration_seconds=-1.0,
                    waveform_png=None,
                    oversize=len(o.bytes_read) > 25 * 1024 * 1024,
                )

            durations.append(pkg.duration_label())

            if pkg.oversize:
                oversize_notes.append(
                    f"{pkg.filename} is {_human_bytes(pkg.size_bytes)} "
                    f"(over Discord's 25 MB cap); not attached."
                )
                continue

            files.append(
                DiscordFile(
                    filename=pkg.filename,
                    content_type=pkg.content_type,
                    data=pkg.data,
                )
            )
            if pkg.waveform_png is not None:
                files.append(
                    DiscordFile(
                        filename=WAVEFORM_FILENAME_TEMPLATE.format(
                            stem=Path(pkg.filename).stem
                        ),
                        content_type="image/png",
                        data=pkg.waveform_png,
                    )
                )

        embed = self._build_embed(run, durations, audio_outputs)
        if oversize_notes:
            note = "\n".join(oversize_notes)
            existing = embed.get("description") or ""
            embed["description"] = (existing + "\n" + note).strip() if existing else note

        return DiscordPayload(embed=embed, files=files)

    def default_post_actions(self, manifest: Manifest) -> list[Action]:
        return list(manifest.actions)

    def _coerce_audio_slots(
        self, manifest: Manifest, values: SlotValues
    ) -> SlotValues:
        slots = manifest.slots_by_name()
        out: SlotValues = dict(values)
        for name, raw in list(values.items()):
            slot = slots.get(name)
            if slot is None or slot.type != SlotType.AUDIO:
                continue
            out[name] = self._coerce_one_audio_value(name, raw)
        return out

    def _coerce_one_audio_value(self, slot_name: str, raw: Any) -> Any:
        if raw is None:
            return None
        if isinstance(raw, str):
            return raw
        if isinstance(raw, Path):
            return str(raw)
        if isinstance(raw, dict):
            unknown = set(raw) - _ACCEPTED_AUDIO_DICT_KEYS
            if unknown:
                raise SlotValueValidationError(
                    slot_name,
                    f"audio dict has unexpected keys: {sorted(unknown)}; "
                    f"expected subset of {sorted(_ACCEPTED_AUDIO_DICT_KEYS)}",
                )
            if "filename" not in raw or "data" not in raw:
                raise SlotValueValidationError(
                    slot_name,
                    "audio dict must include at least 'filename' and 'data'",
                )
            if not isinstance(raw["filename"], str):
                raise SlotValueValidationError(
                    slot_name, "audio dict 'filename' must be a string"
                )
            if not isinstance(raw["data"], (bytes, bytearray)):
                raise SlotValueValidationError(
                    slot_name, "audio dict 'data' must be bytes"
                )
            mime = raw.get("mime")
            if mime is not None and not isinstance(mime, str):
                raise SlotValueValidationError(
                    slot_name, "audio dict 'mime' must be a string"
                )
            return {
                "filename": raw["filename"],
                "mime": mime or "application/octet-stream",
                "data": bytes(raw["data"]),
            }
        raise SlotValueValidationError(
            slot_name,
            f"unsupported value for audio slot: {type(raw).__name__}; "
            "expected str path, pathlib.Path, or {filename, mime, data} dict",
        )

    def _enforce_audio_mime_accepts(
        self, manifest: Manifest, values: SlotValues
    ) -> None:
        slots = manifest.slots_by_name()
        for name, value in values.items():
            slot = slots.get(name)
            if slot is None or slot.type != SlotType.AUDIO:
                continue
            if slot.validation is None or not slot.validation.accepts:
                continue
            if not isinstance(value, dict):
                continue
            mime = value.get("mime")
            if not mime:
                continue
            accepts = [a.lower() for a in slot.validation.accepts]
            if mime.lower() not in accepts:
                raise SlotValueValidationError(
                    name,
                    f"mime '{mime}' is not accepted; expected one of {accepts}",
                )

    def _build_embed(
        self,
        run: Run,
        durations: list[str],
        audio_outputs: list[Output],
    ) -> dict[str, Any]:
        fields: list[dict[str, Any]] = []
        prompt = run.slot_values.get("prompt") or run.slot_values.get("tags")
        if prompt:
            fields.append(
                {
                    "name": "Tags",
                    "value": _truncate(str(prompt), 1024),
                    "inline": False,
                }
            )
        negative = run.slot_values.get("negative_prompt")
        if negative:
            fields.append(
                {
                    "name": "Negative",
                    "value": _truncate(str(negative), 1024),
                    "inline": False,
                }
            )
        if durations:
            fields.append(
                {
                    "name": "Duration",
                    "value": ", ".join(durations),
                    "inline": True,
                }
            )
        seconds = run.slot_values.get("seconds")
        if seconds is not None:
            fields.append(
                {
                    "name": "Requested",
                    "value": f"{float(seconds):g}s",
                    "inline": True,
                }
            )
        seed = run.slot_values.get("seed")
        if seed is not None:
            fields.append({"name": "Seed", "value": str(seed), "inline": True})
        embed: dict[str, Any] = {
            "title": run.manifest_id,
            "color": 0x5865F2,
            "fields": fields,
            "footer": {
                "text": f"prompt_id: {run.prompt_id}" if run.prompt_id else ""
            },
        }
        if audio_outputs:
            stem = Path(audio_outputs[0].filename).stem
            preview_name = WAVEFORM_FILENAME_TEMPLATE.format(stem=stem)
            embed["image"] = {"url": f"attachment://{preview_name}"}
        return embed


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "\u2026"


def _human_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024**2:
        return f"{n / 1024:.1f} KB"
    return f"{n / (1024**2):.1f} MB"


__all__ = ["AudioMusicPlugin", "KSAMPLER_NODE_ID_DEFAULT"]
