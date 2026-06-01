"""Apply user-supplied Slot values to a ComfyUI workflow JSON.

This is the v3 replacement for v2's `WorkflowUpdater` - no model
branching, no class-type knowledge. The function is pure: it copies
the workflow dict and writes each Slot's value to its manifest-declared
(node, field) target(s).
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, Iterable, Mapping

from core.manifest.schema import Action, Manifest

if TYPE_CHECKING:
    from core.run import Output


class SlotApplyError(ValueError):
    """A slot value could not be applied to the workflow."""


class ActionMappingError(ValueError):
    """An Action's source-output -> target-slot map could not be resolved."""


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


def apply_action_mapping(
    action: Action,
    outputs: Iterable["Output"],
) -> dict[str, Any]:
    """Build target-Manifest SlotValues from a finished Run's Outputs.

    For each :class:`~core.manifest.schema.ActionMap` entry in ``action``,
    find the first Output whose ``role`` matches ``map.from_output`` and
    copy its ComfyUI input-side filename (``output.filename``) into the
    target slot named ``map.to_slot``.

    The returned dict is shaped for
    :meth:`core.modalities.base.ModalityPlugin.validate_slot_values` of
    the *target* Manifest. Action chains are pure data per ADR-0001 -
    this function performs no validation against the target Manifest
    (the Plugin layer does that after).

    Raises:
        ActionMappingError: if any ``from_output`` role has no Output.
    """
    outputs_list = list(outputs)
    result: dict[str, Any] = {}
    for entry in action.map:
        matches = [o for o in outputs_list if o.role == entry.from_output]
        if not matches:
            raise ActionMappingError(
                f"action '{action.id}': no Output with role "
                f"'{entry.from_output.value}' to feed slot '{entry.to_slot}'"
            )
        result[entry.to_slot] = matches[0].filename
    return result


__all__ = [
    "ActionMappingError",
    "SlotApplyError",
    "apply_action_mapping",
    "apply_slots",
]
