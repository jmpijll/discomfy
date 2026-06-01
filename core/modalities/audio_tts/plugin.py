"""AudioTTS Modality Plugin (ADR-0002, ADR-0007).

Modality contract:

- ``output_media``: ``["audio/mpeg"]``. Manifests must declare an MP3
  output (typically via ``SaveAudioMP3``); WAV-emitting workflows are
  expected to chain through :func:`core.modalities.audio_common.transcode_to_mp3`
  before the renderer is invoked.
- Validator: coerces TEXT / SEED / ENUM slots through the shared helper
  and applies manifest ``validation`` rules. AUDIO slots accept either
  a filesystem path string or a ``{filename, mime, data}`` dict (so the
  bot can hand attached Discord uploads straight through).
- ProgressMapper: TTS is single-pass; some Fish-Speech versions emit
  step events, some don't. The mapper reports 5% on first executing
  event, mirrors any explicit ``progress`` events linearly, and pins
  100% on ``ExecutionComplete`` / ``Executing(node=None)``. Monotone.
- Renderer: posts the MP3 as a Discord attachment plus a duration label
  embed and (when ffmpeg is available) a waveform PNG preview.
- Default actions: respects the Manifest's declared Actions verbatim.
  v3.0 manifests ship with no audio Actions; future re-roll buttons
  will be authored in YAML.
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

_ACCEPTED_AUDIO_DICT_KEYS = {"filename", "mime", "data"}


class _SinglePassProgressMapper:
    """Simple monotone progress for single-pass TTS workflows.

    Strategy:

    - ``Reconnected`` / unrelated events: return ``None`` (no change).
    - First ``Executing`` for a real node: 5% (lets the user see *something*
      while Fish-Speech loads its checkpoint).
    - ``Progress`` events on any node: scale ``value/max`` into the
      remaining 5..95% band and report monotone.
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
                return self._maybe_set(5)
            return None

        if isinstance(event, Progress):
            max_steps = max(int(event.max), 1)
            value = max(0, min(int(event.value), max_steps))
            band_pct = int(5 + (value / max_steps) * 90)
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


class AudioTTSPlugin:
    """Plugin for the ``audio_tts`` Modality. ADR-0002 contract."""

    modality: Modality = Modality.AUDIO_TTS
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
        return _SinglePassProgressMapper()

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
        text = run.slot_values.get("text") or run.slot_values.get("prompt")
        if text:
            fields.append(
                {
                    "name": "Text",
                    "value": _truncate(str(text), 1024),
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
        seed = run.slot_values.get("seed")
        if seed is not None:
            fields.append({"name": "Seed", "value": str(seed), "inline": True})
        voice_ref = run.slot_values.get("voice_reference")
        if voice_ref:
            fields.append(
                {
                    "name": "Voice reference",
                    "value": _audio_label(voice_ref),
                    "inline": True,
                }
            )
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


def _audio_label(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("filename", "<audio>"))
    if isinstance(value, (str, Path)):
        return Path(str(value)).name
    return "<audio>"


__all__ = ["AudioTTSPlugin"]
