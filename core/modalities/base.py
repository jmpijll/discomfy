"""Modality Plugin Protocol and helpers (ADR-0002).

A :class:`ModalityPlugin` is everything modality-specific to a Workflow's
output kind: how Slot values are validated, how ComfyUI progress events
become a 0-100 percentage, how Outputs are rendered into a Discord
message, and what post-Run Actions the bot offers by default.

Plugins are unit-testable in isolation; nothing here imports Discord or
ComfyUI directly.
"""

from __future__ import annotations

from typing import Any, Iterable, Protocol, runtime_checkable

from core.manifest.roles import Modality
from core.manifest.schema import Action, Manifest
from core.run import DiscordPayload, Output, Run

SlotValues = dict[str, Any]


class SlotValueValidationError(ValueError):
    """A Slot value failed manifest validation.

    Carries the slot name plus a human-readable reason. Plugins raise
    this; the bot turns it into an ephemeral Discord error.
    """

    def __init__(self, slot: str, reason: str):
        self.slot = slot
        self.reason = reason
        super().__init__(f"slot '{slot}': {reason}")


class ProgressMapper(Protocol):
    """Translate ComfyUI WS events into a 0-100 percentage.

    Plugins return one of these from
    :meth:`ModalityPlugin.progress_mapper`. The bot feeds it events from
    :mod:`core.comfyui.v3.ws` and re-renders the Discord progress embed
    when the percentage changes meaningfully.
    """

    def update(self, event: Any) -> int | None:
        """Apply an event, return the latest percentage (0-100) or None.

        Returning ``None`` means "no change worth re-rendering". The bot
        is free to drop returns under a small delta even when non-None;
        the mapper just reports its best estimate.
        """
        ...


@runtime_checkable
class ModalityPlugin(Protocol):
    """The Plugin Protocol (ADR-0002).

    One instance per Modality. The :mod:`core.modalities.registry` module
    wires them up at import time.
    """

    modality: Modality
    output_media: list[str]

    async def validate_slot_values(
        self, manifest: Manifest, values: SlotValues
    ) -> SlotValues:
        """Type-coerce + run validation rules. Return canonical values.

        Implementations should raise :class:`SlotValueValidationError`
        on bad input. The returned dict is what
        :func:`core.manifest.apply_slots` receives.
        """
        ...

    def progress_mapper(self) -> ProgressMapper:
        """Return a fresh ProgressMapper for one Run."""
        ...

    async def render_outputs(
        self, run: Run, outputs: list[Output]
    ) -> DiscordPayload:
        """Build the Discord message that posts the Run's Outputs."""
        ...

    def default_post_actions(self, manifest: Manifest) -> list[Action]:
        """Modality-default Action buttons. Manifests can override."""
        ...


def coerce_slot_values_against_manifest(
    manifest: Manifest, values: SlotValues
) -> SlotValues:
    """Shared helper: coerce raw slot values to their declared SlotType.

    Most Plugins call this from :meth:`validate_slot_values` before
    running their own modality-specific rules. The coercion is small and
    deliberately strict; unknown values raise
    :class:`SlotValueValidationError`.
    """
    import random

    from core.manifest.schema import SlotType

    slots = manifest.slots_by_name()
    out: SlotValues = {}
    for name, raw in values.items():
        slot = slots.get(name)
        if slot is None:
            raise SlotValueValidationError(name, "unknown slot")
        try:
            if slot.type == SlotType.TEXT:
                out[name] = "" if raw is None else str(raw)
            elif slot.type == SlotType.INT:
                out[name] = int(raw)
            elif slot.type == SlotType.FLOAT:
                out[name] = float(raw)
            elif slot.type == SlotType.BOOLEAN:
                out[name] = _coerce_bool(raw)
            elif slot.type == SlotType.SEED:
                out[name] = _coerce_seed(raw)
            elif slot.type in (SlotType.ENUM_STATIC, SlotType.ENUM_DYNAMIC):
                out[name] = "" if raw is None else str(raw)
            elif slot.type in (SlotType.IMAGE, SlotType.AUDIO):
                out[name] = raw
            else:
                out[name] = raw
        except (TypeError, ValueError) as e:
            raise SlotValueValidationError(name, f"could not coerce: {e}") from e
    return out


def enforce_validation_rules(
    manifest: Manifest, values: SlotValues
) -> None:
    """Apply ``slots[].validation`` rules to coerced values.

    Plugins call this after coercion. Raises
    :class:`SlotValueValidationError` on the first failure (Discord
    surfaces one error at a time anyway).
    """
    slots = manifest.slots_by_name()
    for name, value in values.items():
        slot = slots.get(name)
        if slot is None or slot.validation is None:
            continue
        v = slot.validation
        if v.min is not None and isinstance(value, (int, float)) and value < v.min:
            raise SlotValueValidationError(name, f"must be >= {v.min}")
        if v.max is not None and isinstance(value, (int, float)) and value > v.max:
            raise SlotValueValidationError(name, f"must be <= {v.max}")
        if v.min_length is not None and hasattr(value, "__len__") and len(value) < v.min_length:
            raise SlotValueValidationError(
                name, f"must be at least {v.min_length} characters"
            )
        if v.max_length is not None and hasattr(value, "__len__") and len(value) > v.max_length:
            raise SlotValueValidationError(
                name, f"must be at most {v.max_length} characters"
            )
        if (
            v.multiple_of is not None
            and isinstance(value, (int, float))
            and (value % v.multiple_of) != 0
        ):
            raise SlotValueValidationError(
                name, f"must be a multiple of {v.multiple_of}"
            )


def _coerce_bool(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        return bool(raw)
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in ("1", "true", "yes", "on"):
            return True
        if s in ("0", "false", "no", "off", ""):
            return False
    raise ValueError(f"not a boolean: {raw!r}")


def _coerce_seed(raw: Any) -> int:
    import random

    if raw is None:
        return random.randint(0, 2**63 - 1)
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in ("", "random", "rand", "rng"):
            return random.randint(0, 2**63 - 1)
        try:
            return int(s)
        except ValueError as e:
            raise ValueError(f"seed must be 'random' or an integer, got {raw!r}") from e
    if isinstance(raw, float):
        return int(raw)
    raise ValueError(f"seed must be 'random' or an integer, got {raw!r}")


def _any_iter(x: Any) -> Iterable[Any]:
    """Tolerant iterable cast for tests."""
    if isinstance(x, (list, tuple, set)):
        return x
    return [x]


__all__ = [
    "ModalityPlugin",
    "ProgressMapper",
    "SlotValueValidationError",
    "SlotValues",
    "coerce_slot_values_against_manifest",
    "enforce_validation_rules",
]
