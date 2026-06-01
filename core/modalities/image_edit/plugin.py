"""Image-edit Plugin (ADR-0002).

Modality contract:

- ``output_media``: ``["image/png"]``. The edit workflows decode a
  latent into a PNG just like ``image_t2i``; what makes this Modality
  distinct from ``image_t2i`` is that it takes one or more *existing*
  images as inputs (via ``TextEncodeQwenImageEditPlus`` for Qwen, or
  Kontext-style nodes for FLUX Klein in the follow-up slice).
- Validator: coerces TEXT / INT / FLOAT / SEED / ENUM / IMAGE slots
  and applies ``slots[].validation`` rules from the Manifest. IMAGE
  slots carry the ComfyUI input filename (the bot or the smoke harness
  uploads the local file first and writes the server-side name into
  the slot value).
- ProgressMapper: sums ``progress`` events across whichever sampler
  nodes ComfyUI reports for the active prompt, identical to the
  ``image_t2i`` mapper. Qwen-Image-Edit-2511 runs a single 4-step
  KSampler with the Lightning LoRA, so the mapper sees one node.
- Renderer: builds a Discord embed surfacing the edit instruction,
  every source filename the Run consumed, the seed, and attaches the
  decoded PNG.
- Default actions: respect the Manifest's declared Actions verbatim.
  Image-edit outputs are valid inputs to upscale and animate Runs;
  the Manifest decides which buttons to expose so future-Manifest
  authors stay in control.
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


class _SteppedProgressMapper:
    """Sum ``progress`` events across all sampler nodes into one percentage.

    Mirrors the ``image_t2i`` mapper. Qwen-Image-Edit-2511 with the
    Lightning LoRA samples in 4 steps on a single KSampler so the
    denominator stays constant once the first event arrives; the same
    code still handles future edit workflows that chain multiple
    samplers (e.g. a refiner pass) without any change.
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


class ImageEditPlugin:
    """Plugin for the ``image_edit`` Modality. ADR-0002 contract."""

    modality: Modality = Modality.IMAGE_EDIT
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
                    "name": "Instruction",
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
        sources = _collect_source_image_slot_values(run)
        if sources:
            fields.append(
                {
                    "name": "Sources",
                    "value": _truncate("\n".join(sources), 1024),
                    "inline": False,
                }
            )
        seed = run.slot_values.get("seed")
        if seed is not None:
            fields.append({"name": "Seed", "value": str(seed), "inline": True})
        lora = run.slot_values.get("lora")
        if lora:
            fields.append({"name": "LoRA", "value": str(lora), "inline": True})
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
            "color": 0xEB459E,
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


def _collect_source_image_slot_values(run: Run) -> list[str]:
    """Fallback: pick image_1/image_2/image_3 from slot_values by name.

    Used when the renderer has no Manifest handle. Sorted by suffix so
    output is stable regardless of dict iteration order.
    """
    out: list[tuple[str, str]] = []
    for name, value in run.slot_values.items():
        if not value:
            continue
        if name == "image_1" or name == "image":
            out.append((name, str(value)))
        elif name.startswith("image_") and name[6:].isdigit():
            out.append((name, str(value)))
    out.sort(key=lambda pair: pair[0])
    return [v for _, v in out]


def _truncate(s: str, limit: int) -> str:
    if len(s) <= limit:
        return s
    return s[: limit - 1] + "\u2026"


__all__ = ["ImageEditPlugin"]
