"""Manifest-loading + requires-validation tests for WAN 2.2 i2v.

The manifest is the architectural test of ADR-0001's multi-UNET pattern:
two ``requires.unets`` entries, two ``role: model_high`` / ``model_low``
slots, two distinct UNETLoader targets.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.comfyui.v3.capability import Inventory
from core.manifest import load_manifest
from core.manifest.roles import Modality, Role


FIXTURE = Path(__file__).parent / "fixtures" / "object_info_slim.json"


@pytest.fixture(scope="module")
def manifest():
    return load_manifest("workflows/manifests/wan22_i2v.yaml")


@pytest.fixture(scope="module")
def inventory() -> Inventory:
    return Inventory(json.loads(FIXTURE.read_text(encoding="utf-8")))


class TestManifestShape:
    def test_id_and_modality(self, manifest) -> None:
        assert manifest.id == "wan22_i2v"
        assert manifest.modality == Modality.VIDEO

    def test_declares_high_and_low_unet(self, manifest) -> None:
        assert (
            "wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8H.safetensors"
            in manifest.requires.unets
        )
        assert (
            "wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8L.safetensors"
            in manifest.requires.unets
        )

    def test_declares_lora_pair(self, manifest) -> None:
        assert (
            "SVI_v2_PRO_Wan2.2-I2V-A14B_HIGH_lora_rank_128_fp16.safetensors"
            in manifest.requires.loras
        )
        assert (
            "SVI_v2_PRO_Wan2.2-I2V-A14B_LOW_lora_rank_128_fp16.safetensors"
            in manifest.requires.loras
        )

    def test_has_model_high_and_low_slots(self, manifest) -> None:
        by_name = manifest.slots_by_name()
        assert by_name["model_high"].role == Role.MODEL_HIGH
        assert by_name["model_low"].role == Role.MODEL_LOW

    def test_init_image_slot_is_required(self, manifest) -> None:
        slot = manifest.slots_by_name()["init_image"]
        assert slot.role == Role.INIT_IMAGE
        assert slot.ui.required is True
        assert slot.ui.attachment_position == 1

    def test_output_is_video_mp4(self, manifest) -> None:
        assert len(manifest.outputs) == 1
        assert manifest.outputs[0].role == Role.OUTPUT_VIDEO
        assert manifest.outputs[0].media == "video/mp4"

    def test_seed_targets_both_samplers(self, manifest) -> None:
        seed = manifest.slots_by_name()["seed"]
        targets = seed.resolved_targets()
        target_nodes = sorted(t.node for t in targets)
        assert target_nodes == ["11", "12"]


class TestRequiresValidationAgainstInventory:
    def test_fully_satisfied(self, manifest, inventory) -> None:
        missing = inventory.validate_requires(manifest.requires)
        assert missing == [], missing

    def test_missing_high_unet_reports_high(self, manifest) -> None:
        from core.manifest.schema import Requires

        starved = Inventory(
            {
                "UNETLoader": {
                    "input": {
                        "required": {
                            "unet_name": [
                                [
                                    "wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8L.safetensors"
                                ]
                            ]
                        }
                    }
                },
                "VAELoader": {
                    "input": {
                        "required": {
                            "vae_name": [["wan_2.1_vae.safetensors"]]
                        }
                    }
                },
                "CLIPLoader": {
                    "input": {
                        "required": {
                            "clip_name": [
                                ["umt5_xxl_fp8_e4m3fn_scaled.safetensors"]
                            ]
                        }
                    }
                },
                "LoraLoaderModelOnly": {
                    "input": {
                        "required": {
                            "lora_name": [
                                [
                                    "SVI_v2_PRO_Wan2.2-I2V-A14B_HIGH_lora_rank_128_fp16.safetensors",
                                    "SVI_v2_PRO_Wan2.2-I2V-A14B_LOW_lora_rank_128_fp16.safetensors",
                                ]
                            ]
                        }
                    }
                },
                "AnyVHSNode": {
                    "python_module": "custom_nodes.comfyui-videohelpersuite"
                },
            }
        )
        missing = starved.validate_requires(manifest.requires)
        assert any("FP8H" in m for m in missing)
        assert not any("FP8L" in m for m in missing)

    def test_missing_lora_pair_reports_both(self, manifest) -> None:
        starved = Inventory(
            {
                "UNETLoader": {
                    "input": {
                        "required": {
                            "unet_name": [
                                [
                                    "wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8H.safetensors",
                                    "wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8L.safetensors",
                                ]
                            ]
                        }
                    }
                },
                "VAELoader": {
                    "input": {
                        "required": {
                            "vae_name": [["wan_2.1_vae.safetensors"]]
                        }
                    }
                },
                "CLIPLoader": {
                    "input": {
                        "required": {
                            "clip_name": [
                                ["umt5_xxl_fp8_e4m3fn_scaled.safetensors"]
                            ]
                        }
                    }
                },
                "LoraLoaderModelOnly": {
                    "input": {
                        "required": {"lora_name": [[]]}
                    }
                },
                "AnyVHSNode": {
                    "python_module": "custom_nodes.comfyui-videohelpersuite"
                },
            }
        )
        missing = starved.validate_requires(manifest.requires)
        assert sum(1 for m in missing if "SVI_v2_PRO" in m) == 2
