"""Manifest layer for DisComfy v3 - workflows as data, not code.

A Manifest is a YAML file in `workflows/manifests/<id>.yaml` that
declares everything the bot needs to know about a Workflow: its
Modality, Slots, NodeMap, Outputs, Actions, and required Packs/models.

See `docs/v3/adr/0001-workflow-manifest-format.md` for the full
specification.
"""

from core.manifest.applier import (
    ActionMappingError,
    SlotApplyError,
    apply_action_mapping,
    apply_slots,
)
from core.manifest.loader import (
    ManifestLoadError,
    load_manifest,
    load_manifest_directory,
)
from core.manifest.roles import Modality, Role
from core.manifest.schema import (
    Action,
    ActionMap,
    Manifest,
    Output,
    Requires,
    Slot,
    SlotType,
    SlotUI,
    SlotValidation,
    Target,
    UIHint,
)

__all__ = [
    "Action",
    "ActionMap",
    "ActionMappingError",
    "Manifest",
    "ManifestLoadError",
    "Modality",
    "Output",
    "Requires",
    "Role",
    "Slot",
    "SlotApplyError",
    "SlotType",
    "SlotUI",
    "SlotValidation",
    "Target",
    "UIHint",
    "apply_action_mapping",
    "apply_slots",
    "load_manifest",
    "load_manifest_directory",
]
