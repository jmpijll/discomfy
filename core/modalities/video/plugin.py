"""Video Plugin (ADR-0002).

Modality contract:

- ``output_media``: ``["video/mp4"]``
- Validator: shared coerce + validation helpers from :mod:`core.modalities.base`.
  Image-type Slots (``init_image``) pass through as opaque values; the bot
  uploads the attachment to ComfyUI and writes the resulting filename into
  the Slot value before :func:`core.manifest.apply_slots` is called.
- ProgressMapper: two-phase, designed for the multi-UNET dual-KSampler
  pattern (HIGH-noise pass + LOW-noise pass) of WAN 2.2 i2v. The two
  KSampler nodes each emit their own ``Progress`` stream; we sum them
  into a single percentage that occupies 0-95% of the bar. The remaining
  5% is reserved for post-sampling nodes (VAE decode, VHS_VideoCombine
  assembly) which fire ``Executing`` events but no ``Progress`` events.
- Renderer: posts the MP4 file as a Discord attachment with an embed
  carrying prompt, frame count, duration (assuming 16 fps default - the
  VHS default and the Wan 2.2 native frame rate), and file size. If the
  file exceeds 25 MB (Discord's per-message cap for non-Nitro bots) the
  Plugin returns a content message naming the ComfyUI-side filename and
  omits the attachment; external upload is a v3.x deliverable.
- Default actions: respect the Manifest's declared Actions verbatim.
"""

from __future__ import annotations

from typing import Any

from core.manifest.roles import Modality, Role
from core.manifest.schema import Action, Manifest
from core.modalities.base import (
    ProgressMapper,
    SlotValueValidationError,
    SlotValues,
    coerce_slot_values_against_manifest,
    enforce_validation_rules,
)
from core.run import DiscordFile, DiscordPayload, Output, Run

DEFAULT_VIDEO_FPS: int = 16
DISCORD_FILE_CAP_BYTES: int = 25 * 1024 * 1024
SAMPLING_CEILING: int = 95
POST_SAMPLE_BUMP: int = 2
POST_SAMPLE_CEILING: int = 99


class _DualSamplerProgressMapper:
    """Sum dual-sampler progress + bump on post-sampling Executing events.

    The WAN 2.2 i2v pipeline runs two ``KSampler`` nodes in sequence:
    the HIGH-noise UNET on the early timesteps, then the LOW-noise UNET
    on the refinement timesteps. Each KSampler emits its own ``progress``
    stream. We accumulate per-node ``(value, max)`` into a global ratio
    and scale to 0-95% so post-sampling work has somewhere to go.

    Post-sampling nodes (``VAEDecode``, ``VHS_VideoCombine``) emit
    ``executing`` events but no ``progress`` events; we bump 2% per
    ``Executing`` of a node we've never seen progress for (capped at 99%)
    until ``ExecutionComplete`` or ``Executing(node=None)`` flips the bar
    to 100%.
    """

    def __init__(self) -> None:
        self._per_node: dict[str, tuple[int, int]] = {}
        self._post_sample_bumps: int = 0
        self._sampling_seen: bool = False
        self._last_pct: int | None = None
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
            return self._mark_complete()
        if isinstance(event, Executing) and event.node is None and event.prompt_id:
            return self._mark_complete()
        if isinstance(event, Progress):
            self._sampling_seen = True
            node = event.node or "_default_"
            max_steps = max(int(event.max), 1)
            value = max(0, min(int(event.value), max_steps))
            self._per_node[node] = (value, max_steps)
            total_value = sum(v for v, _ in self._per_node.values())
            total_max = sum(m for _, m in self._per_node.values())
            if total_max <= 0:
                return None
            pct = int((total_value / total_max) * SAMPLING_CEILING)
            return self._monotone(pct)
        if isinstance(event, Executing) and event.node is not None:
            if self._sampling_seen and event.node not in self._per_node:
                self._post_sample_bumps += 1
                pct = min(
                    SAMPLING_CEILING + POST_SAMPLE_BUMP * self._post_sample_bumps,
                    POST_SAMPLE_CEILING,
                )
                return self._monotone(pct)
        return None

    def _mark_complete(self) -> int:
        self._complete = True
        self._last_pct = 100
        return 100

    def _monotone(self, pct: int) -> int | None:
        if self._complete:
            pct = 100
        if self._last_pct is not None:
            pct = max(pct, self._last_pct)
        if pct == self._last_pct:
            return None
        self._last_pct = pct
        return pct


class VideoPlugin:
    """Plugin for the ``video`` Modality. ADR-0002 contract."""

    modality: Modality = Modality.VIDEO
    output_media: list[str] = ["video/mp4"]

    async def validate_slot_values(
        self, manifest: Manifest, values: SlotValues
    ) -> SlotValues:
        coerced = coerce_slot_values_against_manifest(manifest, values)
        enforce_validation_rules(manifest, coerced)
        return coerced

    def progress_mapper(self) -> ProgressMapper:
        return _DualSamplerProgressMapper()

    async def render_outputs(
        self, run: Run, outputs: list[Output]
    ) -> DiscordPayload:
        videos = [o for o in outputs if o.role == Role.OUTPUT_VIDEO]
        primary = videos[0] if videos else None

        fields: list[dict[str, Any]] = []
        prompt = run.slot_values.get("prompt")
        if prompt:
            fields.append(
                {
                    "name": "Prompt",
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
        frame_count = run.slot_values.get("frame_count")
        if frame_count is not None:
            fields.append(
                {
                    "name": "Frames",
                    "value": str(frame_count),
                    "inline": True,
                }
            )
            duration = _format_duration(int(frame_count), DEFAULT_VIDEO_FPS)
            fields.append(
                {
                    "name": "Duration",
                    "value": duration,
                    "inline": True,
                }
            )
        width = run.slot_values.get("width")
        height = run.slot_values.get("height")
        if width and height:
            fields.append(
                {"name": "Size", "value": f"{width}x{height}", "inline": True}
            )
        seed = run.slot_values.get("seed")
        if seed is not None:
            fields.append({"name": "Seed", "value": str(seed), "inline": True})

        if primary is not None:
            fields.append(
                {
                    "name": "File size",
                    "value": _format_bytes(primary.size_bytes),
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

        files: list[DiscordFile] = []
        content: str | None = None

        if primary is None:
            embed["description"] = "No video output."
            return DiscordPayload(embed=embed, files=files)

        if primary.size_bytes > DISCORD_FILE_CAP_BYTES:
            content = (
                f"\u26a0\ufe0f Video `{primary.filename}` is "
                f"{_format_bytes(primary.size_bytes)}, over Discord's "
                f"{_format_bytes(DISCORD_FILE_CAP_BYTES)} attachment cap. "
                "Fetch it from ComfyUI's `/view?filename="
                f"{primary.filename}&type=output` endpoint. External upload "
                "lands in v3.x."
            )
            embed.setdefault("description", "")
            embed["description"] = (embed["description"] + "\n" if embed["description"] else "") + (
                f"File too large for Discord attachment ({_format_bytes(primary.size_bytes)})."
            )
        else:
            files.append(
                DiscordFile(
                    filename=primary.filename,
                    content_type=primary.media,
                    data=primary.bytes_read,
                )
            )

        return DiscordPayload(embed=embed, files=files, content=content)

    def default_post_actions(self, manifest: Manifest) -> list[Action]:
        return list(manifest.actions)


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "\u2026"


def _format_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    if n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / (1024 * 1024 * 1024):.2f} GB"


def _format_duration(frame_count: int, fps: int) -> str:
    if fps <= 0:
        return f"{frame_count} frames"
    seconds = frame_count / fps
    if seconds < 60:
        return f"{seconds:.1f}s @ {fps}fps"
    minutes, secs = divmod(seconds, 60)
    return f"{int(minutes)}m{secs:04.1f}s @ {fps}fps"


__all__ = ["DISCORD_FILE_CAP_BYTES", "DEFAULT_VIDEO_FPS", "VideoPlugin"]
