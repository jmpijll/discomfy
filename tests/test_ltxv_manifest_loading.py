"""Manifest-loading + requires-validation tests for LTX-Video 2.3 22B.

These manifests are the second `video` Modality member alongside
wan22_i2v. They exercise:

- a single-checkpoint model load (no UNET pair, unlike WAN 2.2);
- a Gemma-3-12B CLIP encoder pinned via `requires.clips`;
- the LTX Q8 distilled LoRA as the default `requires.loras` entry
  and as the default value of the dynamic `lora` slot;
- LTXVImgToVideo wiring for the i2v variant with an `init_image`
  Slot exposed at attachment_position 1 so it can be chained from
  qwen_image_2512's `output_image`.

No live ComfyUI; the test reads ``object_info_slim.json`` and the
workflow JSON files directly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.comfyui.v3.capability import Inventory
from core.manifest import load_manifest
from core.manifest.applier import apply_slots
from core.manifest.roles import Modality, Role


FIXTURE = Path(__file__).parent / "fixtures" / "object_info_slim.json"
REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def t2v_manifest():
    return load_manifest("workflows/manifests/ltxv_2_3_22b_t2v.yaml")


@pytest.fixture(scope="module")
def i2v_manifest():
    return load_manifest("workflows/manifests/ltxv_2_3_22b_i2v.yaml")


@pytest.fixture(scope="module")
def inventory() -> Inventory:
    return Inventory(json.loads(FIXTURE.read_text(encoding="utf-8")))


@pytest.fixture(scope="module")
def t2v_workflow() -> dict:
    return json.loads(
        (REPO_ROOT / "workflows" / "ltxv_2_3_22b_t2v.json").read_text(
            encoding="utf-8"
        )
    )


@pytest.fixture(scope="module")
def i2v_workflow() -> dict:
    return json.loads(
        (REPO_ROOT / "workflows" / "ltxv_2_3_22b_i2v.json").read_text(
            encoding="utf-8"
        )
    )


class TestT2VManifestShape:
    def test_id_and_modality(self, t2v_manifest) -> None:
        assert t2v_manifest.id == "ltxv_2_3_22b_t2v"
        assert t2v_manifest.modality == Modality.VIDEO

    def test_requires_checkpoint_clip_and_lora(self, t2v_manifest) -> None:
        assert "ltx-2.3-22b-dev-fp8.safetensors" in t2v_manifest.requires.checkpoints
        assert "gemma_3_12B_it.safetensors" in t2v_manifest.requires.clips
        assert (
            "ltx-2.3-22b-distilled-lora-384.safetensors"
            in t2v_manifest.requires.loras
        )

    def test_no_unets_required(self, t2v_manifest) -> None:
        assert t2v_manifest.requires.unets == []
        assert t2v_manifest.requires.vaes == []

    def test_slot_roles(self, t2v_manifest) -> None:
        by_name = t2v_manifest.slots_by_name()
        assert by_name["prompt"].role == Role.PROMPT_POSITIVE
        assert by_name["negative_prompt"].role == Role.PROMPT_NEGATIVE
        assert by_name["width"].role == Role.LATENT_SIZE
        assert by_name["height"].role == Role.LATENT_SIZE
        assert by_name["frame_count"].role == Role.BATCH_SIZE
        assert by_name["seed"].role == Role.SEED
        assert by_name["lora"].role == Role.LORA
        assert by_name["lora_strength"].role == Role.LORA_STRENGTH

    def test_prompt_targets_clip_text_encode(self, t2v_manifest) -> None:
        slot = t2v_manifest.slots_by_name()["prompt"]
        targets = slot.resolved_targets()
        assert len(targets) == 1
        assert targets[0].node == "6"
        assert targets[0].field == "text"

    def test_lora_options_from_inventory(self, t2v_manifest) -> None:
        slot = t2v_manifest.slots_by_name()["lora"]
        assert slot.options_from == "comfyui.loras"

    def test_output_is_video_mp4(self, t2v_manifest) -> None:
        assert len(t2v_manifest.outputs) == 1
        assert t2v_manifest.outputs[0].role == Role.OUTPUT_VIDEO
        assert t2v_manifest.outputs[0].media == "video/mp4"
        assert t2v_manifest.outputs[0].node == "16"


class TestI2VManifestShape:
    def test_id_and_modality(self, i2v_manifest) -> None:
        assert i2v_manifest.id == "ltxv_2_3_22b_i2v"
        assert i2v_manifest.modality == Modality.VIDEO

    def test_requires_match_t2v(self, i2v_manifest, t2v_manifest) -> None:
        assert i2v_manifest.requires.checkpoints == t2v_manifest.requires.checkpoints
        assert i2v_manifest.requires.clips == t2v_manifest.requires.clips
        assert i2v_manifest.requires.loras == t2v_manifest.requires.loras
        assert i2v_manifest.requires.packs == t2v_manifest.requires.packs

    def test_init_image_slot_required_with_attachment_position(
        self, i2v_manifest
    ) -> None:
        slot = i2v_manifest.slots_by_name()["init_image"]
        assert slot.role == Role.INIT_IMAGE
        assert slot.ui.required is True
        assert slot.ui.attachment_position == 1
        targets = slot.resolved_targets()
        assert targets[0].node == "8"
        assert targets[0].field == "image"

    def test_size_slots_target_imgtovideo_node(self, i2v_manifest) -> None:
        by_name = i2v_manifest.slots_by_name()
        for name in ("width", "height", "frame_count"):
            tgt = by_name[name].resolved_targets()[0]
            assert tgt.node == "9", f"{name} should target LTXVImgToVideo node"

    def test_output_is_video_mp4(self, i2v_manifest) -> None:
        assert len(i2v_manifest.outputs) == 1
        assert i2v_manifest.outputs[0].role == Role.OUTPUT_VIDEO
        assert i2v_manifest.outputs[0].media == "video/mp4"
        assert i2v_manifest.outputs[0].node == "17"


class TestRequiresValidationAgainstInventory:
    def test_t2v_requires_satisfied(self, t2v_manifest, inventory) -> None:
        missing = inventory.validate_requires(t2v_manifest.requires)
        assert missing == [], missing

    def test_i2v_requires_satisfied(self, i2v_manifest, inventory) -> None:
        missing = inventory.validate_requires(i2v_manifest.requires)
        assert missing == [], missing

    def test_missing_checkpoint_is_reported(self, t2v_manifest) -> None:
        starved = Inventory(
            {
                "CheckpointLoaderSimple": {
                    "input": {
                        "required": {"ckpt_name": [[]]}
                    }
                },
                "CLIPLoader": {
                    "input": {
                        "required": {
                            "clip_name": [["gemma_3_12B_it.safetensors"]]
                        }
                    }
                },
                "LoraLoaderModelOnly": {
                    "input": {
                        "required": {
                            "lora_name": [
                                ["ltx-2.3-22b-distilled-lora-384.safetensors"]
                            ]
                        }
                    }
                },
                "AnyVHSNode": {
                    "python_module": "custom_nodes.comfyui-videohelpersuite"
                },
            }
        )
        missing = starved.validate_requires(t2v_manifest.requires)
        assert any(
            "ltx-2.3-22b-dev-fp8.safetensors" in m for m in missing
        ), missing

    def test_missing_lora_is_reported(self, t2v_manifest) -> None:
        starved = Inventory(
            {
                "CheckpointLoaderSimple": {
                    "input": {
                        "required": {
                            "ckpt_name": [["ltx-2.3-22b-dev-fp8.safetensors"]]
                        }
                    }
                },
                "CLIPLoader": {
                    "input": {
                        "required": {
                            "clip_name": [["gemma_3_12B_it.safetensors"]]
                        }
                    }
                },
                "LoraLoaderModelOnly": {
                    "input": {"required": {"lora_name": [[]]}}
                },
                "AnyVHSNode": {
                    "python_module": "custom_nodes.comfyui-videohelpersuite"
                },
            }
        )
        missing = starved.validate_requires(t2v_manifest.requires)
        assert any(
            "ltx-2.3-22b-distilled-lora-384.safetensors" in m for m in missing
        ), missing


class TestSlotsMapToWorkflowNodes:
    """Every Slot's target node/field must exist in its workflow JSON."""

    def test_t2v_slots_resolve(self, t2v_manifest, t2v_workflow) -> None:
        for slot in t2v_manifest.slots:
            for target in slot.resolved_targets():
                node = t2v_workflow.get(target.node)
                assert node is not None, (
                    f"t2v slot '{slot.name}' targets missing node '{target.node}'"
                )
                inputs = node.get("inputs", {})
                assert target.field in inputs, (
                    f"t2v slot '{slot.name}' targets unknown field "
                    f"'{target.field}' on node '{target.node}' ({sorted(inputs)})"
                )

    def test_i2v_slots_resolve(self, i2v_manifest, i2v_workflow) -> None:
        for slot in i2v_manifest.slots:
            for target in slot.resolved_targets():
                node = i2v_workflow.get(target.node)
                assert node is not None, (
                    f"i2v slot '{slot.name}' targets missing node '{target.node}'"
                )
                inputs = node.get("inputs", {})
                assert target.field in inputs, (
                    f"i2v slot '{slot.name}' targets unknown field "
                    f"'{target.field}' on node '{target.node}' ({sorted(inputs)})"
                )

    def test_t2v_output_node_exists(self, t2v_manifest, t2v_workflow) -> None:
        for out in t2v_manifest.outputs:
            assert out.node in t2v_workflow, (
                f"t2v output node '{out.node}' missing from workflow JSON"
            )

    def test_i2v_output_node_exists(self, i2v_manifest, i2v_workflow) -> None:
        for out in i2v_manifest.outputs:
            assert out.node in i2v_workflow, (
                f"i2v output node '{out.node}' missing from workflow JSON"
            )

    def test_t2v_uses_lora_loader_model_only(self, t2v_workflow) -> None:
        # NOTE: we tried LTXVQ8LoraModelLoader first (per the slice 6 issue
        # hint) but the live server is missing the `hadamard_transform`
        # Python dependency it needs. The plain ComfyUI LoraLoaderModelOnly
        # works for this LoRA and produces equivalent output for non-Q8 use.
        assert t2v_workflow["3"]["class_type"] == "LoraLoaderModelOnly"
        assert (
            t2v_workflow["3"]["inputs"]["lora_name"]
            == "ltx-2.3-22b-distilled-lora-384.safetensors"
        )

    def test_t2v_uses_ltxav_text_encoder_loader(self, t2v_workflow) -> None:
        assert t2v_workflow["2"]["class_type"] == "LTXAVTextEncoderLoader"
        assert (
            t2v_workflow["2"]["inputs"]["text_encoder"]
            == "gemma_3_12B_it.safetensors"
        )
        assert (
            t2v_workflow["2"]["inputs"]["ckpt_name"]
            == "ltx-2.3-22b-dev-fp8.safetensors"
        )

    def test_i2v_uses_ltxav_text_encoder_loader(self, i2v_workflow) -> None:
        assert i2v_workflow["2"]["class_type"] == "LTXAVTextEncoderLoader"
        assert (
            i2v_workflow["2"]["inputs"]["text_encoder"]
            == "gemma_3_12B_it.safetensors"
        )

    def test_i2v_uses_ltxv_img_to_video(self, i2v_workflow) -> None:
        assert i2v_workflow["9"]["class_type"] == "LTXVImgToVideo"

    def test_t2v_uses_empty_ltxv_latent(self, t2v_workflow) -> None:
        assert t2v_workflow["8"]["class_type"] == "EmptyLTXVLatentVideo"


class TestApplySlots:
    """End-to-end: user values flow through apply_slots into the workflow."""

    def test_t2v_apply_writes_user_values(
        self, t2v_manifest, t2v_workflow
    ) -> None:
        updated = apply_slots(
            t2v_workflow,
            t2v_manifest,
            {
                "prompt": "a slow cinematic pan across a misty harbor at dawn",
                "negative_prompt": "blurry",
                "width": 640,
                "height": 384,
                "frame_count": 49,
                "seed": 12345,
                "lora": "ltx-2.3-22b-distilled-lora-384.safetensors",
                "lora_strength": 1.0,
            },
        )
        assert (
            updated["6"]["inputs"]["text"]
            == "a slow cinematic pan across a misty harbor at dawn"
        )
        assert updated["7"]["inputs"]["text"] == "blurry"
        assert updated["8"]["inputs"]["width"] == 640
        assert updated["8"]["inputs"]["height"] == 384
        assert updated["8"]["inputs"]["length"] == 49
        assert updated["13"]["inputs"]["noise_seed"] == 12345
        assert (
            updated["3"]["inputs"]["lora_name"]
            == "ltx-2.3-22b-distilled-lora-384.safetensors"
        )

    def test_i2v_apply_writes_init_image_filename(
        self, i2v_manifest, i2v_workflow
    ) -> None:
        updated = apply_slots(
            i2v_workflow,
            i2v_manifest,
            {
                "prompt": "the subject turns slowly",
                "init_image": "uploaded_qwen_frame.png",
                "width": 768,
                "height": 768,
                "frame_count": 97,
                "seed": 7,
            },
        )
        assert updated["8"]["inputs"]["image"] == "uploaded_qwen_frame.png"
        assert updated["9"]["inputs"]["width"] == 768
        assert updated["9"]["inputs"]["height"] == 768
        assert updated["9"]["inputs"]["length"] == 97
        assert updated["14"]["inputs"]["noise_seed"] == 7
