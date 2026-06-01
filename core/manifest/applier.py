"""Apply user-supplied Slot values to a ComfyUI workflow JSON.

This is the v3 replacement for v2's `WorkflowUpdater` - no model
branching, no class-type knowledge. The function is pure: it copies
the workflow dict and writes each Slot's value to its manifest-declared
(node, field) target(s).
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

from core.manifest.schema import Manifest


class SlotApplyError(ValueError):
    """A slot value could not be applied to the workflow."""


def apply_slots(
    workflow: Mapping[str, Any],
    manifest: Manifest,
    values: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a deep copy of `workflow` with `values` written through `manifest`.

    Args:
        workflow: ComfyUI graph as parsed from the workflow JSON.
        manifest: Manifest whose Slots map names to (node, field) targets.
        values: name -> value for each slot. Slots without a value in
            `values` keep whatever default the workflow JSON contains.

    Raises:
        SlotApplyError: if `values` references an unknown slot name, or
            if a manifest target points at a node/field not present in
            the workflow.
    """
    slots = manifest.slots_by_name()

    unknown = set(values) - set(slots)
    if unknown:
        raise SlotApplyError(
            f"unknown slot name(s) in values: {sorted(unknown)}"
        )

    out: dict[str, Any] = copy.deepcopy(dict(workflow))

    for slot_name, raw_value in values.items():
        slot = slots[slot_name]
        for target in slot.resolved_targets():
            node = out.get(target.node)
            if node is None:
                raise SlotApplyError(
                    f"slot '{slot_name}' targets node '{target.node}' which is not in the workflow"
                )
            inputs = node.get("inputs")
            if not isinstance(inputs, dict):
                raise SlotApplyError(
                    f"slot '{slot_name}' target node '{target.node}' has no 'inputs' object"
                )
            if target.field not in inputs:
                raise SlotApplyError(
                    f"slot '{slot_name}' targets field '{target.field}' which is not on node '{target.node}'"
                )
            inputs[target.field] = raw_value
    return out


__all__ = ["SlotApplyError", "apply_slots"]
