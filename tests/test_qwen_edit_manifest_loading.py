"""Tests for the three Qwen-Image-Edit 2511 manifests (Slice 3a).

Each manifest must:

- Load without schema errors and expose the expected ``id`` and
  :class:`Modality.IMAGE_EDIT`.
- Declare exact filenames in ``requires`` (UNET / VAE / CLIP / LoRAs)
  that match what ``/object_info`` would advertise on a server with
  Qwen-Image-Edit-2511 installed.
- Validate against a hand-built ``Inventory`` that supplies those
  exact filenames (positive path) and fail validation when any of the
  required filenames is absent (negative path).
- Cover every slot's manifest target with a node that exists in the
  workflow JSON (no orphans).
- Apply cleanly via :func:`core.manifest.apply_slots` with a
  representative slot-values dict, exercising the user-facing image
  slot wiring for 1/2/3 inputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from core.comfyui.v3.capability import Inventory
from core.manifest import apply_slots, load_manifest, load_manifest_directory
from core.manifest.roles import Modality

REPO_ROOT = Path(__file__).resolve().parents[1]

QWEN_EDIT_UNET = "qwen_image_edit_2511_fp8mixed.safetensors"
QWEN_VAE = "qwen_image_vae.safetensors"
QWEN_CLIP = "qwen_2.5_vl_7b_fp8_scaled.safetensors"
QWEN_LIGHTNING_LORA = (
    "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"
)
QWEN_USER_LORA = "QWEN_EDIT_ACTION_V1.safetensors"


@pytest.fixture
def manifest_1():
    return load_manifest("workflows/manifests/qwen_image_edit_2511_1image.yaml")


@pytest.fixture
def manifest_2():
    return load_manifest("workflows/manifests/qwen_image_edit_2511_2images.yaml")


@pytest.fixture
def manifest_3():
    return load_manifest("workflows/manifests/qwen_image_edit_2511_3images.yaml")


def _inventory_with_all() -> Inventory:
    """Build an Inventory shaped like a server with everything installed."""
    object_info: dict[str, Any] = {
        "UNETLoader": {
            "input": {
                "required": {
                    "unet_name": [[QWEN_EDIT_UNET, "other.safetensors"], {}],
                }
            },
            "python_module": "nodes",
        },
        "VAELoader": {
            "input": {
                "required": {
                    "vae_name": [[QWEN_VAE], {}],
                }
            },
            "python_module": "nodes",
        },
        "CLIPLoader": {
            "input": {
                "required": {
                    "clip_name": [[QWEN_CLIP], {}],
                }
            },
            "python_module": "nodes",
        },
        "LoraLoaderModelOnly": {
            "input": {
                "required": {
                    "lora_name": [[QWEN_LIGHTNING_LORA, QWEN_USER_LORA], {}],
                }
            },
            "python_module": "nodes",
        },
    }
    return Inventory(object_info)


def _inventory_without(*, drop_lora: str | None = None, drop_unet: bool = False) -> Inventory:
    object_info: dict[str, Any] = {
        "UNETLoader": {
            "input": {
                "required": {
                    "unet_name": [
                        ["other.safetensors"]
                        if drop_unet
                        else [QWEN_EDIT_UNET],
                        {},
                    ],
                }
            },
            "python_module": "nodes",
        },
        "VAELoader": {
            "input": {
                "required": {"vae_name": [[QWEN_VAE], {}]},
            },
            "python_module": "nodes",
        },
        "CLIPLoader": {
            "input": {
                "required": {"clip_name": [[QWEN_CLIP], {}]},
            },
            "python_module": "nodes",
        },
        "LoraLoaderModelOnly": {
            "input": {
                "required": {
                    "lora_name": [
                        [
                            lora
                            for lora in (QWEN_LIGHTNING_LORA, QWEN_USER_LORA)
                            if lora != drop_lora
                        ],
                        {},
                    ],
                }
            },
            "python_module": "nodes",
        },
    }
    return Inventory(object_info)


class TestManifestLoading:
    @pytest.mark.parametrize(
        "fixture_name,expected_id",
        [
            ("manifest_1", "qwen_image_edit_2511_1image"),
            ("manifest_2", "qwen_image_edit_2511_2images"),
            ("manifest_3", "qwen_image_edit_2511_3images"),
        ],
    )
    def test_loads_with_expected_id_and_modality(
        self, request, fixture_name: str, expected_id: str
    ) -> None:
        m = request.getfixturevalue(fixture_name)
        assert m.id == expected_id
        assert m.modality == Modality.IMAGE_EDIT

    def test_directory_load_includes_all_three(self) -> None:
        loaded, errors = load_manifest_directory("workflows/manifests")
        ids = {m.id for m in loaded}
        assert "qwen_image_edit_2511_1image" in ids
        assert "qwen_image_edit_2511_2images" in ids
        assert "qwen_image_edit_2511_3images" in ids
        assert not errors, f"unexpected manifest load errors: {errors}"


class TestRequiresValidation:
    @pytest.mark.parametrize(
        "fixture_name",
        ["manifest_1", "manifest_2", "manifest_3"],
    )
    def test_satisfied_with_full_inventory(
        self, request, fixture_name: str
    ) -> None:
        m = request.getfixturevalue(fixture_name)
        inv = _inventory_with_all()
        assert inv.validate_requires(m.requires) == []

    def test_unet_missing_disables(self, manifest_1) -> None:
        inv = _inventory_without(drop_unet=True)
        problems = inv.validate_requires(manifest_1.requires)
        assert problems
        assert any(QWEN_EDIT_UNET in p for p in problems)

    def test_lightning_lora_missing_disables(self, manifest_2) -> None:
        inv = _inventory_without(drop_lora=QWEN_LIGHTNING_LORA)
        problems = inv.validate_requires(manifest_2.requires)
        assert problems
        assert any(QWEN_LIGHTNING_LORA in p for p in problems)


class TestNodeMapCoversWorkflow:
    """Every Slot target must point at a node in the workflow JSON."""

    @pytest.mark.parametrize(
        "fixture_name",
        ["manifest_1", "manifest_2", "manifest_3"],
    )
    def test_every_slot_target_resolves(
        self, request, fixture_name: str
    ) -> None:
        m = request.getfixturevalue(fixture_name)
        workflow_path = REPO_ROOT / m.workflow_file
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        for slot in m.slots:
            for target in slot.resolved_targets():
                assert target.node in workflow, (
                    f"slot '{slot.name}' targets missing node "
                    f"'{target.node}' in {m.id}"
                )
                inputs = workflow[target.node]["inputs"]
                assert target.field in inputs, (
                    f"slot '{slot.name}' targets missing field "
                    f"'{target.field}' on node '{target.node}' in {m.id}"
                )

    @pytest.mark.parametrize(
        "fixture_name",
        ["manifest_1", "manifest_2", "manifest_3"],
    )
    def test_every_output_node_exists(
        self, request, fixture_name: str
    ) -> None:
        m = request.getfixturevalue(fixture_name)
        workflow_path = REPO_ROOT / m.workflow_file
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        for spec in m.outputs:
            assert spec.node in workflow, (
                f"output node '{spec.node}' missing from {m.id}'s workflow"
            )


class TestSlotCounts:
    def test_1image_has_one_image_slot(self, manifest_1) -> None:
        image_slots = [s for s in manifest_1.slots if s.type.value == "image"]
        assert len(image_slots) == 1
        assert image_slots[0].name == "image_1"

    def test_2image_has_two_image_slots(self, manifest_2) -> None:
        image_slots = [s for s in manifest_2.slots if s.type.value == "image"]
        names = {s.name for s in image_slots}
        assert names == {"image_1", "image_2"}

    def test_3image_has_three_image_slots(self, manifest_3) -> None:
        image_slots = [s for s in manifest_3.slots if s.type.value == "image"]
        names = {s.name for s in image_slots}
        assert names == {"image_1", "image_2", "image_3"}

    def test_attachment_positions_are_1_indexed_and_unique(
        self, manifest_3
    ) -> None:
        positions = sorted(
            s.ui.attachment_position
            for s in manifest_3.slots
            if s.ui.attachment_position is not None
        )
        assert positions == [1, 2, 3]


class TestApplySlots:
    def test_one_image_apply_writes_through(self, manifest_1) -> None:
        workflow = json.loads(
            (REPO_ROOT / manifest_1.workflow_file).read_text("utf-8")
        )
        out = apply_slots(
            workflow,
            manifest_1,
            {
                "prompt": "make the sky red",
                "negative_prompt": "blurry",
                "image_1": "src.png",
                "seed": 42,
                "lora": QWEN_USER_LORA,
                "lora_strength": 0.0,
            },
        )
        assert out["12"]["inputs"]["prompt"] == "make the sky red"
        assert out["11"]["inputs"]["prompt"] == "blurry"
        assert out["8"]["inputs"]["image"] == "src.png"
        assert out["13"]["inputs"]["seed"] == 42
        assert out["5"]["inputs"]["lora_name"] == QWEN_USER_LORA
        assert out["5"]["inputs"]["strength_model"] == 0.0

    def test_two_image_apply_wires_both_sources(self, manifest_2) -> None:
        workflow = json.loads(
            (REPO_ROOT / manifest_2.workflow_file).read_text("utf-8")
        )
        out = apply_slots(
            workflow,
            manifest_2,
            {
                "prompt": "compose",
                "image_1": "a.png",
                "image_2": "b.png",
            },
        )
        assert out["8"]["inputs"]["image"] == "a.png"
        assert out["16"]["inputs"]["image"] == "b.png"
        assert out["11"]["inputs"]["image2"] == ["16", 0]
        assert out["12"]["inputs"]["image2"] == ["16", 0]

    def test_three_image_apply_wires_all_sources(self, manifest_3) -> None:
        workflow = json.loads(
            (REPO_ROOT / manifest_3.workflow_file).read_text("utf-8")
        )
        out = apply_slots(
            workflow,
            manifest_3,
            {
                "prompt": "compose",
                "image_1": "a.png",
                "image_2": "b.png",
                "image_3": "c.png",
            },
        )
        assert out["8"]["inputs"]["image"] == "a.png"
        assert out["16"]["inputs"]["image"] == "b.png"
        assert out["17"]["inputs"]["image"] == "c.png"
        assert out["11"]["inputs"]["image3"] == ["17", 0]
        assert out["12"]["inputs"]["image3"] == ["17", 0]


class TestRequiredFilenamesArePopulated:
    """Workflow JSON loader fields must contain the exact required filenames.

    Mirrors the "no model branching" rule: a manifest's ``requires``
    list and the workflow JSON's loader inputs must agree.
    """

    @pytest.mark.parametrize(
        "fixture_name",
        ["manifest_1", "manifest_2", "manifest_3"],
    )
    def test_unet_clip_vae_lora_names_match_requires(
        self, request, fixture_name: str
    ) -> None:
        m = request.getfixturevalue(fixture_name)
        workflow = json.loads(
            (REPO_ROOT / m.workflow_file).read_text("utf-8")
        )
        loader_filenames: set[str] = set()
        for node in workflow.values():
            inputs = node.get("inputs", {})
            for key in ("unet_name", "clip_name", "vae_name", "lora_name"):
                if key in inputs and isinstance(inputs[key], str):
                    loader_filenames.add(inputs[key])
        declared = (
            set(m.requires.unets)
            | set(m.requires.vaes)
            | set(m.requires.clips)
            | set(m.requires.loras)
        )
        assert loader_filenames <= declared, (
            f"workflow uses filenames not in requires: "
            f"{loader_filenames - declared}"
        )
