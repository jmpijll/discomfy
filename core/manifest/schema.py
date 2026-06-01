"""Pydantic schema for v3 workflow Manifests.

ADR-0001 is the spec. This module is the executable form of that spec.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.manifest.roles import Modality, Role

SCHEMA_VERSION: int = 1


class SlotType(str, Enum):
    TEXT = "text"
    INT = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ENUM_STATIC = "enum_static"
    ENUM_DYNAMIC = "enum_dynamic"
    SEED = "seed"
    IMAGE = "image"
    AUDIO = "audio"


class UIHint(str, Enum):
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    NUMBER = "number"
    SEED = "seed"
    SELECT = "select"
    SELECT_STATIC = "select_static"
    BOOLEAN = "boolean"
    IMAGE = "image"
    AUDIO = "audio"


class Target(BaseModel):
    """One {node, field} pair where a Slot's value lands."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    node: str = Field(..., description="ComfyUI node id (string key in workflow JSON)")
    field: str = Field(..., description="Top-level input field on that node")


class SlotValidation(BaseModel):
    """Optional validation rules. Plugins use these to reject bad values."""

    model_config = ConfigDict(extra="forbid")

    min: float | int | None = None
    max: float | int | None = None
    min_length: int | None = None
    max_length: int | None = None
    multiple_of: int | None = None
    pattern: str | None = None
    accepts: list[str] | None = Field(
        default=None,
        description="Allowed mime-type prefixes for IMAGE/AUDIO slots, e.g. ['image/png', 'image/jpeg']",
    )


class SlotUI(BaseModel):
    """Discord-rendering hints for a Slot. ADR-0003 maps these to components."""

    model_config = ConfigDict(extra="forbid")

    hint: UIHint
    label: str
    placeholder: str | None = None
    default: Any | None = Field(
        default=None,
        description="Default value or the literal string 'random' for SEED slots",
    )
    required: bool = True
    step: int | float | None = None
    attachment_position: int | None = Field(
        default=None,
        description="1-indexed position on the slash command if hint is IMAGE/AUDIO",
    )


class Slot(BaseModel):
    """A user-facing parameter of a Workflow."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    type: SlotType
    role: Role
    target: Target | None = None
    targets: list[Target] | None = None
    options_from: str | None = Field(
        default=None,
        description="Resolved at View-construction time. Examples: 'comfyui.loras', 'comfyui.samplers'.",
    )
    options: list[str] | None = Field(
        default=None,
        description="Inline options for SELECT_STATIC slots.",
    )
    ui: SlotUI
    validation: SlotValidation | None = None

    @model_validator(mode="after")
    def _exactly_one_target(self) -> "Slot":
        if self.target is None and not self.targets:
            raise ValueError(
                f"slot '{self.name}': must declare 'target' or 'targets'"
            )
        if self.target is not None and self.targets:
            raise ValueError(
                f"slot '{self.name}': cannot declare both 'target' and 'targets'"
            )
        return self

    @model_validator(mode="after")
    def _options_for_enum(self) -> "Slot":
        if self.type == SlotType.ENUM_DYNAMIC and not self.options_from:
            raise ValueError(
                f"slot '{self.name}': enum_dynamic requires 'options_from'"
            )
        if self.type == SlotType.ENUM_STATIC and not self.options:
            raise ValueError(
                f"slot '{self.name}': enum_static requires inline 'options'"
            )
        return self

    def resolved_targets(self) -> list[Target]:
        """Return all (node, field) targets as a list, regardless of which form the manifest used."""
        if self.targets:
            return list(self.targets)
        if self.target is None:
            return []
        return [self.target]


class Output(BaseModel):
    """A file the Workflow produces."""

    model_config = ConfigDict(extra="forbid")

    role: Literal[Role.OUTPUT_IMAGE, Role.OUTPUT_VIDEO, Role.OUTPUT_AUDIO]
    node: str = Field(..., description="ComfyUI node id whose output we collect")
    media: str = Field(
        ...,
        description="MIME type. Plugins use this to choose a Discord renderer.",
    )


class ActionMap(BaseModel):
    """One source-output -> target-slot wire in an Action."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    from_output: Role
    to_slot: str


class Action(BaseModel):
    """A post-Run interaction (Discord button) wired to another Workflow."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    label: str
    target_workflow: str = Field(
        ...,
        description="Manifest id of the Workflow this Action triggers",
    )
    map: list[ActionMap] = Field(default_factory=list)


class Requires(BaseModel):
    """Dependencies a Manifest needs from ComfyUI to be runnable.

    Each list is checked against `/object_info` at registration; missing
    items disable the manifest with a logged warning - they do not crash
    the bot.
    """

    model_config = ConfigDict(extra="forbid")

    packs: list[str] = Field(default_factory=list)
    unets: list[str] = Field(default_factory=list)
    vaes: list[str] = Field(default_factory=list)
    clips: list[str] = Field(default_factory=list)
    loras: list[str] = Field(default_factory=list)
    checkpoints: list[str] = Field(default_factory=list)
    upscale_models: list[str] = Field(default_factory=list)


class Manifest(BaseModel):
    """A v3 workflow Manifest. ADR-0001."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(..., description="Must equal SCHEMA_VERSION (1)")
    id: str = Field(..., min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(..., min_length=1)
    description: str = ""
    modality: Modality
    workflow_file: str = Field(
        ...,
        description="Path (relative to repo root) to the ComfyUI JSON",
    )
    requires: Requires = Field(default_factory=Requires)
    slots: list[Slot] = Field(default_factory=list)
    outputs: list[Output] = Field(default_factory=list, min_length=1)
    actions: list[Action] = Field(default_factory=list)

    @model_validator(mode="after")
    def _supported_schema_version(self) -> "Manifest":
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported schema_version {self.schema_version}; expected {SCHEMA_VERSION}"
            )
        return self

    @model_validator(mode="after")
    def _slot_names_unique(self) -> "Manifest":
        seen: set[str] = set()
        for slot in self.slots:
            if slot.name in seen:
                raise ValueError(f"duplicate slot name '{slot.name}'")
            seen.add(slot.name)
        return self

    @model_validator(mode="after")
    def _action_ids_unique(self) -> "Manifest":
        seen: set[str] = set()
        for action in self.actions:
            if action.id in seen:
                raise ValueError(f"duplicate action id '{action.id}'")
            seen.add(action.id)
        return self

    def slots_by_name(self) -> dict[str, Slot]:
        return {slot.name: slot for slot in self.slots}


__all__ = [
    "SCHEMA_VERSION",
    "Action",
    "ActionMap",
    "Manifest",
    "Output",
    "Requires",
    "Slot",
    "SlotType",
    "SlotUI",
    "SlotValidation",
    "Target",
    "UIHint",
]
