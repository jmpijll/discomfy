"""Image-text-to-image Plugin (ADR-0002).

Modality contract:

- ``output_media``: ``["image/png"]``
- Validator: coerces TEXT / INT / FLOAT / SEED / ENUM slots, applies
  ``slots[].validation`` rules from the Manifest.
- ProgressMapper: accumulates KSampler step progress across multiple
  sampler nodes (Qwen-2512 has two: 8 + 4 steps) into a single 0-100
  percentage so the Discord embed shows monotone progress.
- Renderer: builds a Discord embed listing prompt / size / seed and
  attaches each Output as a file.
- Default actions: respect the Manifest's declared Actions verbatim.
  No hard-coded Upscale/Animate/Edit so future-manifest authors stay
  in control.
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


class _SteppedProgressMapper:
    """Sum ``progress`` events across all sampler nodes into one percentage.

    The Qwen-Image 2512 workflow has two KSamplers (8 steps + 4 steps).
    ComfyUI's ``progress`` events carry ``{node, value, max}`` per sampler;
    if we only watch one we miss the second pass.

    Strategy: track the most-recent ``(value, max)`` per node, sum into
    a global ``(value, max)`` denominator. The reported percentage is
    clamped monotone: percentage never decreases mid-Run, so the user
    never sees a Discord embed jump backwards when a new sampler node
    begins and the denominator grows.
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


class ImageT2IPlugin:
    """Plugin for the ``image_t2i`` Modality. ADR-0002 contract."""

    modality: Modality = Modality.IMAGE_T2I
    output_media: list[str] = ["image/png"]

    async def validate_slot_values(
        self, manifest: Manifest, values: SlotValues
    ) -> SlotValues:
        coerced = coerce_slot_values_against_manifest(manifest, values)
        enforce_validation_rules(manifest, coerced)
        return coerced

    def progress_mapper(self) -> ProgressMapper:
        return _SteppedProgressMapper()

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
        width = run.slot_values.get("width")
        height = run.slot_values.get("height")
        if width and height:
            fields.append(
                {"name": "Size", "value": f"{width}x{height}", "inline": True}
            )
        seed = run.slot_values.get("seed")
        if seed is not None:
            fields.append({"name": "Seed", "value": str(seed), "inline": True})
        lora = run.slot_values.get("lora")
        if lora:
            fields.append({"name": "LoRA", "value": str(lora), "inline": True})
        embed: dict[str, Any] = {
            "title": run.manifest_id,
            "color": 0x5865F2,
            "fields": fields,
            "footer": {
                "text": f"prompt_id: {run.prompt_id}" if run.prompt_id else ""
            },
        }
        if images:
            embed["image"] = {"url": f"attachment://{images[0].filename}"}
        return DiscordPayload(embed=embed, files=files)

    def default_post_actions(self, manifest: Manifest) -> list[Action]:
        return list(manifest.actions)


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "\u2026"


__all__ = ["ImageT2IPlugin"]
