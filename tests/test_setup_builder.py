"""Tests for bot.setup.builder.SetupBuilder (ADR-0003).

The tests assert against the binning + select-option plan, not the
Discord component tree, because the planning step is pure and
testable. Component-level tests would need a Discord runtime.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bot.setup.builder import (
    MAX_MODAL_TEXT_INPUTS,
    MAX_SELECT_OPTIONS,
    SetupBuildError,
    SetupBuilder,
)
from core.comfyui.v3.capability import Inventory
from core.manifest import load_manifest
from core.manifest.schema import (
    Manifest,
    Output,
    Slot,
    SlotType,
    SlotUI,
    Target,
    UIHint,
)


@pytest.fixture
def manifest():
    return load_manifest("workflows/manifests/qwen_image_2512.yaml")


@pytest.fixture
def inventory() -> Inventory:
    return Inventory(
        json.loads(
            Path("tests/fixtures/object_info_slim.json").read_text(encoding="utf-8")
        )
    )


class TestQwenManifestBinning:
    def test_modal_text_holds_five_text_slots(
        self, manifest: Manifest, inventory: Inventory
    ) -> None:
        plan = SetupBuilder(manifest, inventory).build()
        assert len(plan.binning.modal_text) <= MAX_MODAL_TEXT_INPUTS
        assert [s.name for s in plan.binning.modal_text] == [
            "prompt",
            "negative_prompt",
            "width",
            "height",
            "seed",
        ]

    def test_lora_strength_overflows_to_second_modal(
        self, manifest: Manifest, inventory: Inventory
    ) -> None:
        plan = SetupBuilder(manifest, inventory).build()
        assert plan.binning.has_overflow
        assert [s.name for s in plan.binning.overflow_text] == ["lora_strength"]

    def test_lora_becomes_select_with_resolved_options(
        self, manifest: Manifest, inventory: Inventory
    ) -> None:
        plan = SetupBuilder(manifest, inventory).build()
        assert [s.name for s in plan.binning.selects] == ["lora"]
        options = plan.select_options["lora"]
        assert "qwen_image_2512_j0k3_lora_v1.safetensors" in options
        assert len(options) <= MAX_SELECT_OPTIONS

    def test_no_booleans_no_attachments(
        self, manifest: Manifest, inventory: Inventory
    ) -> None:
        plan = SetupBuilder(manifest, inventory).build()
        assert plan.binning.booleans == []
        assert plan.binning.attachments == []


class TestCaps:
    def test_select_truncated_to_25(self) -> None:
        big_options = [f"opt_{i}.safetensors" for i in range(40)]
        manifest = _synthetic_manifest_with_big_select()
        inv = _InventoryStub(big_options)
        plan = SetupBuilder(manifest, inv).build()
        assert len(plan.select_options["lora"]) == MAX_SELECT_OPTIONS
        assert plan.overflow_truncated["lora"] == 40 - MAX_SELECT_OPTIONS

    def test_more_than_five_text_slots_overflow_in_order(self) -> None:
        slots = [
            Slot(
                name=f"t{i}",
                type=SlotType.TEXT,
                role="prompt_positive",
                target=Target(node="1", field=f"f{i}"),
                ui=SlotUI(hint=UIHint.SHORT_TEXT, label=f"L{i}"),
            )
            for i in range(7)
        ]
        manifest = _wrap_slots(slots)
        plan = SetupBuilder(manifest, _InventoryStub([])).build()
        assert [s.name for s in plan.binning.modal_text] == [
            "t0",
            "t1",
            "t2",
            "t3",
            "t4",
        ]
        assert [s.name for s in plan.binning.overflow_text] == ["t5", "t6"]


class TestErrors:
    def test_select_dynamic_without_options_from_raises(self) -> None:
        slot = Slot(
            name="lora",
            type=SlotType.ENUM_STATIC,
            role="lora",
            target=Target(node="1", field="x"),
            options=["a.safetensors"],
            ui=SlotUI(hint=UIHint.SELECT_STATIC, label="LoRA"),
        )
        manifest = _wrap_slots([slot])
        plan = SetupBuilder(manifest, _InventoryStub([])).build()
        assert plan.select_options["lora"] == ["a.safetensors"]


# Helpers and stubs


class _InventoryStub:
    """A tiny stand-in for Inventory that returns a fixed lora list."""

    def __init__(self, loras: list[str]) -> None:
        self._loras = loras

    def options_for(self, source: str) -> list[str]:
        if source == "comfyui.loras":
            return list(self._loras)
        return []


def _synthetic_manifest_with_big_select() -> Manifest:
    slots = [
        Slot(
            name="prompt",
            type=SlotType.TEXT,
            role="prompt_positive",
            target=Target(node="1", field="text"),
            ui=SlotUI(hint=UIHint.SHORT_TEXT, label="Prompt"),
        ),
        Slot(
            name="lora",
            type=SlotType.ENUM_DYNAMIC,
            role="lora",
            target=Target(node="2", field="lora_name"),
            options_from="comfyui.loras",
            ui=SlotUI(hint=UIHint.SELECT, label="LoRA", required=False),
        ),
    ]
    return _wrap_slots(slots)


def _wrap_slots(slots: list[Slot]) -> Manifest:
    return Manifest(
        schema_version=1,
        id="synthetic",
        name="Synthetic",
        modality="image_t2i",
        workflow_file="workflows/qwen_image_2512_lora.json",
        slots=slots,
        outputs=[Output(role="output_image", node="13", media="image/png")],
    )
