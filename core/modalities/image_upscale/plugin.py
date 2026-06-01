"""Image-upscale Plugin (ADR-0002).

Modality contract:

- ``output_media``: ``["image/png"]`` (same as image_t2i; the difference
  is intent, not file type).
- Validator: coerces TEXT / INT / FLOAT / SEED / ENUM / IMAGE slots and
  applies ``slots[].validation`` rules from the Manifest. IMAGE slots
  carry the ComfyUI input filename (already uploaded by the bot or the
  smoke harness).
- ProgressMapper: same shape as image_t2i - sums step events across
  whichever sampler / decoder nodes ComfyUI reports. The latent manifest
  has only a VAEDecode (no sampler) and may emit only an ``executing``
  ladder; the pure-pixel manifest has no sampler either. The mapper
  still reports 100 on completion.
- Renderer: builds a Discord embed that surfaces the source filename,
  the requested scale factor, and (when discoverable) the output
  filename + byte count, then attaches each Output PNG.
- Default actions: empty list. We deliberately do NOT chain
  "Upscale of Upscale" onto our own outputs - the user can re-run the
  workflow with a different scale if they want more.
"""

from __future__ import annotations

from typing import Any

from core.manifest.roles import Modality, Role
from core.manifest.schema import Action, Manifest
from core.modalities.base import (
    ProgressMapper,
    SlotValues,
    coerce_slot_values_against_manifest,
    enforce_validation_rules,
)
from core.run import DiscordFile, DiscordPayload, Output, Run


class _StepProgressMapper:
    """Translate ComfyUI events into a monotone 0-100 percentage.

    Upscale workflows often produce few or no ``progress`` events (no
    sampler) - the mapper still reaches 100 on ``ExecutionComplete`` or
    on the closing ``executing(node=None)`` event so the Discord embed
    advances to "done".
    """

    def __init__(self) -> None:
        self._per_node: dict[str, tuple[int, int]] = {}
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
            self._complete = True
            self._last_pct = 100
            return 100
        if isinstance(event, Executing) and event.node is None and event.prompt_id:
            self._complete = True
            self._last_pct = 100
            return 100
        if not isinstance(event, Progress):
            return None
        node = event.node or "_default_"
        max_steps = max(int(event.max), 1)
        value = max(0, min(int(event.value), max_steps))
        self._per_node[node] = (value, max_steps)
        total_value = sum(v for v, _ in self._per_node.values())
        total_max = sum(m for _, m in self._per_node.values())
        if total_max <= 0:
            return None
        pct = int((total_value / total_max) * 100)
        if self._complete:
            pct = 100
        if self._last_pct is not None:
            pct = max(pct, self._last_pct)
        if pct == self._last_pct:
            return None
        self._last_pct = pct
        return pct


class ImageUpscalePlugin:
    """Plugin for the ``image_upscale`` Modality. ADR-0002 contract."""

    modality: Modality = Modality.IMAGE_UPSCALE
    output_media: list[str] = ["image/png"]

    async def validate_slot_values(
        self, manifest: Manifest, values: SlotValues
    ) -> SlotValues:
        coerced = coerce_slot_values_against_manifest(manifest, values)
        enforce_validation_rules(manifest, coerced)
        return coerced

    def progress_mapper(self) -> ProgressMapper:
        return _StepProgressMapper()

    async def render_outputs(
        self, run: Run, outputs: list[Output]
    ) -> DiscordPayload:
        images = [o for o in outputs if o.role == Role.OUTPUT_IMAGE]
        files = [
            DiscordFile(
                filename=o.filename,
                content_type=o.media,
                data=o.bytes_read,
            )
            for o in images
        ]
        fields: list[dict[str, Any]] = []
        source = run.slot_values.get("source_image")
        if source:
            fields.append(
                {
                    "name": "Source",
                    "value": _truncate(str(source), 1024),
                    "inline": False,
                }
            )
        scale_by = run.slot_values.get("scale_by")
        if scale_by is not None:
            fields.append(
                {
                    "name": "Scale",
                    "value": f"x{scale_by}",
                    "inline": True,
                }
            )
        upscale_model = run.slot_values.get("upscale_model")
        if upscale_model:
            fields.append(
                {
                    "name": "Upscale model",
                    "value": _truncate(str(upscale_model), 1024),
                    "inline": True,
                }
            )
        if images:
            fields.append(
                {
                    "name": "Output",
                    "value": (
                        f"{images[0].filename} "
                        f"({images[0].size_bytes:,} bytes)"
                    ),
                    "inline": False,
                }
            )
        embed: dict[str, Any] = {
            "title": run.manifest_id,
            "color": 0x57F287,
            "fields": fields,
            "footer": {
                "text": f"prompt_id: {run.prompt_id}" if run.prompt_id else ""
            },
        }
        if images:
            embed["image"] = {"url": f"attachment://{images[0].filename}"}
        return DiscordPayload(embed=embed, files=files)

    def default_post_actions(self, manifest: Manifest) -> list[Action]:
        """No default Actions for upscale Runs.

        Returning an empty list prevents "Upscale of Upscale" buttons on
        upscale outputs - an infinite-loop UX trap. Manifest-declared
        Actions are intentionally ignored for this Modality; if a user
        wants to re-run with a different scale they can invoke the
        slash command again.
        """
        return []


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "\u2026"


__all__ = ["ImageUpscalePlugin"]
