"""Tests for core.manifest.applier - the pure function that writes Slot
values into a ComfyUI workflow JSON."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from core.manifest.applier import SlotApplyError, apply_slots
from core.manifest.loader import load_manifest


@pytest.fixture
def qwen_manifest():
    return load_manifest("workflows/manifests/qwen_image_2512.yaml")


@pytest.fixture
def qwen_workflow():
    return json.loads(Path("workflows/qwen_image_2512_lora.json").read_text())


class TestApplySlotsHappyPath:
    def test_writes_prompt(self, qwen_manifest, qwen_workflow):
        out = apply_slots(qwen_workflow, qwen_manifest, {"prompt": "a red panda"})
        assert out["18"]["inputs"]["text"] == "a red panda"

    def test_does_not_mutate_input(self, qwen_manifest, qwen_workflow):
        before = copy.deepcopy(qwen_workflow)
        apply_slots(qwen_workflow, qwen_manifest, {"prompt": "anything"})
        assert qwen_workflow == before

    def test_multi_target_seed_writes_to_both_nodes(self, qwen_manifest, qwen_workflow):
        out = apply_slots(qwen_workflow, qwen_manifest, {"seed": 12345})
        assert out["8"]["inputs"]["seed"] == 12345
        assert out["14"]["inputs"]["seed"] == 12345

    def test_preserves_unwritten_fields(self, qwen_manifest, qwen_workflow):
        out = apply_slots(qwen_workflow, qwen_manifest, {"prompt": "x"})
        assert out["8"]["inputs"]["sampler_name"] == "euler"
        assert out["28"]["inputs"]["unet_name"].startswith("qwen_image_2512_")

    def test_writes_multiple_slots_in_one_call(self, qwen_manifest, qwen_workflow):
        out = apply_slots(
            qwen_workflow,
            qwen_manifest,
            {"prompt": "x", "negative_prompt": "y", "width": 1024, "height": 1024},
        )
        assert out["18"]["inputs"]["text"] == "x"
        assert out["17"]["inputs"]["text"] == "y"
        assert out["59"]["inputs"]["width"] == 1024
        assert out["59"]["inputs"]["height"] == 1024

    def test_empty_values_returns_workflow_clone(self, qwen_manifest, qwen_workflow):
        out = apply_slots(qwen_workflow, qwen_manifest, {})
        assert out == qwen_workflow
        assert out is not qwen_workflow


class TestApplySlotsErrors:
    def test_unknown_slot_name_raises(self, qwen_manifest, qwen_workflow):
        with pytest.raises(SlotApplyError) as exc:
            apply_slots(qwen_workflow, qwen_manifest, {"not_a_slot": 1})
        assert "unknown slot" in str(exc.value).lower()

    def test_missing_target_node_raises(self, qwen_manifest):
        from core.manifest.schema import Manifest

        m = Manifest.model_validate(qwen_manifest.model_dump())
        broken_workflow: dict = {}
        with pytest.raises(SlotApplyError) as exc:
            apply_slots(broken_workflow, m, {"prompt": "x"})
        assert "not in the workflow" in str(exc.value)

    def test_missing_target_field_raises(self, qwen_manifest, qwen_workflow):
        broken = copy.deepcopy(qwen_workflow)
        del broken["18"]["inputs"]["text"]
        with pytest.raises(SlotApplyError) as exc:
            apply_slots(broken, qwen_manifest, {"prompt": "x"})
        assert "not on node" in str(exc.value)

    def test_node_without_inputs_raises(self, qwen_manifest, qwen_workflow):
        broken = copy.deepcopy(qwen_workflow)
        broken["18"]["inputs"] = "not a dict"
        with pytest.raises(SlotApplyError) as exc:
            apply_slots(broken, qwen_manifest, {"prompt": "x"})
        assert "no 'inputs'" in str(exc.value)
