"""Tests for core.comfyui.v3.capability.Inventory.

The Inventory wraps ComfyUI's ``/object_info`` JSON; tests use a slimmed
fixture (only the nodes the v3 manifests touch) so they stay fast and
deterministic.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.comfyui.v3.capability import Inventory
from core.manifest.schema import Requires


@pytest.fixture
def object_info() -> dict:
    return json.loads(
        Path("tests/fixtures/object_info_slim.json").read_text(encoding="utf-8")
    )


@pytest.fixture
def inventory(object_info: dict) -> Inventory:
    return Inventory(object_info)


class TestInventoryAccessors:
    def test_unets_returns_installed_models(self, inventory: Inventory) -> None:
        unets = inventory.unets()
        assert (
            "qwen_image_2512_fp8_e4m3fn_scaled_comfyui_4steps_v1.0.safetensors"
            in unets
        )

    def test_vaes_includes_qwen_vae(self, inventory: Inventory) -> None:
        assert "qwen_image_vae.safetensors" in inventory.vaes()

    def test_clips_includes_qwen_clip(self, inventory: Inventory) -> None:
        assert "qwen_2.5_vl_7b_fp8_scaled.safetensors" in inventory.clips()

    def test_loras_falls_back_to_lora_loader_model_only(
        self, inventory: Inventory
    ) -> None:
        loras = inventory.loras()
        assert "qwen_image_2512_j0k3_lora_v1.safetensors" in loras

    def test_samplers_returns_known_samplers(self, inventory: Inventory) -> None:
        samplers = inventory.samplers()
        assert "euler" in samplers
        assert len(samplers) > 10

    def test_schedulers_returns_known_schedulers(
        self, inventory: Inventory
    ) -> None:
        schedulers = inventory.schedulers()
        assert "beta" in schedulers

    def test_options_for_known_source(self, inventory: Inventory) -> None:
        assert inventory.options_for("comfyui.loras") == inventory.loras()
        assert inventory.options_for("comfyui.samplers") == inventory.samplers()

    def test_options_for_unknown_source_is_empty(
        self, inventory: Inventory
    ) -> None:
        assert inventory.options_for("comfyui.does_not_exist") == []


class TestInventoryHasNode:
    def test_has_node_true_for_registered(self, inventory: Inventory) -> None:
        assert inventory.has_node("UNETLoader") is True

    def test_has_node_false_for_missing(self, inventory: Inventory) -> None:
        assert inventory.has_node("NonexistentPack_Node") is False

    def test_python_module_for_known_node(self, inventory: Inventory) -> None:
        assert inventory.python_module_for("UNETLoader") == "nodes"

    def test_python_module_for_unknown_node(self, inventory: Inventory) -> None:
        assert inventory.python_module_for("NopeNode") is None

    def test_has_pack_true_for_core_module(self, inventory: Inventory) -> None:
        assert inventory.has_pack("nodes") is True

    def test_has_pack_false_for_missing_module(
        self, inventory: Inventory
    ) -> None:
        assert (
            inventory.has_pack("custom_nodes.ComfyUI-WanVideoWrapper") is False
        )


class TestValidateRequires:
    def test_satisfied_requires_returns_empty_list(
        self, inventory: Inventory
    ) -> None:
        req = Requires(
            unets=[
                "qwen_image_2512_fp8_e4m3fn_scaled_comfyui_4steps_v1.0.safetensors"
            ],
            vaes=["qwen_image_vae.safetensors"],
            clips=["qwen_2.5_vl_7b_fp8_scaled.safetensors"],
        )
        assert inventory.validate_requires(req) == []

    def test_missing_unet_reported(self, inventory: Inventory) -> None:
        req = Requires(unets=["definitely_not_installed.safetensors"])
        problems = inventory.validate_requires(req)
        assert len(problems) == 1
        assert "UNET" in problems[0]
        assert "definitely_not_installed.safetensors" in problems[0]

    def test_missing_pack_reported(self, inventory: Inventory) -> None:
        req = Requires(packs=["custom_nodes.ComfyUI-Nonsense"])
        problems = inventory.validate_requires(req)
        assert len(problems) == 1
        assert "Pack" in problems[0]
        assert "ComfyUI-Nonsense" in problems[0]

    def test_mixed_missing_each_category(self, inventory: Inventory) -> None:
        req = Requires(
            unets=["missing.safetensors"],
            vaes=["missing_vae.safetensors"],
            loras=["missing_lora.safetensors"],
        )
        problems = inventory.validate_requires(req)
        assert len(problems) == 3
        joined = "\n".join(problems)
        assert "UNET" in joined and "VAE" in joined and "LoRA" in joined


class TestInventoryConstructor:
    def test_rejects_non_dict(self) -> None:
        with pytest.raises(TypeError):
            Inventory("not a dict")  # type: ignore[arg-type]

    def test_empty_dict_yields_empty_lists(self) -> None:
        inv = Inventory({})
        assert inv.unets() == []
        assert inv.loras() == []
        assert inv.samplers() == []
        assert inv.has_node("anything") is False
