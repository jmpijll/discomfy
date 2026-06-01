"""Tests for the two upscale manifests + conditional registration (Slice 4).

The latent manifest is always available; the pixel-ultimate manifest
must register only when ``Inventory.upscale_models()`` is non-empty
AND contains the declared ``requires.upscale_models`` filename.

These tests exercise the *registration gate* (does the manifest's
``requires`` block validate against a given Inventory?) without
touching a live ComfyUI.
"""

from __future__ import annotations

from typing import Any

import pytest

from core.comfyui.v3.capability import Inventory
from core.manifest import load_manifest, load_manifest_directory
from core.manifest.roles import Modality


@pytest.fixture
def latent_manifest():
    return load_manifest("workflows/manifests/upscale_latent.yaml")


@pytest.fixture
def pixel_manifest():
    return load_manifest("workflows/manifests/upscale_pixel_ultimate.yaml")


def _inventory_with(
    *,
    upscale_models: list[str] | None = None,
    vaes: list[str] | None = None,
) -> Inventory:
    """Build an Inventory whose option-list helpers return the given lists.

    Hand-crafted ``object_info``-shaped dict so we don't depend on the
    slim fixture's coverage of every node class.
    """
    object_info: dict[str, Any] = {
        "VAELoader": {
            "input": {
                "required": {
                    "vae_name": [list(vaes or []), {}],
                },
            },
            "python_module": "nodes",
        },
        "UpscaleModelLoader": {
            "input": {
                "required": {
                    "model_name": [list(upscale_models or []), {}],
                },
            },
            "python_module": "comfy_extras.nodes_upscale_model",
        },
    }
    return Inventory(object_info)


class TestLatentManifestIsAlwaysAvailable:
    def test_loads_with_expected_id_and_modality(
        self, latent_manifest
    ) -> None:
        assert latent_manifest.id == "image_upscale_latent"
        assert latent_manifest.modality == Modality.IMAGE_UPSCALE

    def test_satisfied_by_inventory_with_qwen_vae(
        self, latent_manifest
    ) -> None:
        inv = _inventory_with(vaes=["qwen_image_vae.safetensors"])
        assert inv.validate_requires(latent_manifest.requires) == []

    def test_disabled_if_qwen_vae_missing(self, latent_manifest) -> None:
        inv = _inventory_with(vaes=[])
        problems = inv.validate_requires(latent_manifest.requires)
        assert problems
        assert any("VAE" in p for p in problems)

    def test_declares_no_actions(self, latent_manifest) -> None:
        assert latent_manifest.actions == []

    def test_declares_attachment_position_on_source_image(
        self, latent_manifest
    ) -> None:
        slot = latent_manifest.slots_by_name()["source_image"]
        assert slot.ui.attachment_position == 1


class TestPixelManifestIsConditional:
    def test_loads_with_expected_id(self, pixel_manifest) -> None:
        assert pixel_manifest.id == "image_upscale_pixel_ultimate"
        assert pixel_manifest.modality == Modality.IMAGE_UPSCALE

    def test_disabled_when_inventory_has_no_upscale_models(
        self, pixel_manifest
    ) -> None:
        """The scenario from `docs/v3/discovery.md`: zero upscale models.

        The manifest's declared ``requires.upscale_models`` is non-empty,
        so ``validate_requires`` must flag it as unavailable - the bot
        will refuse to register it.
        """
        inv = _inventory_with(upscale_models=[])
        problems = inv.validate_requires(pixel_manifest.requires)
        assert problems
        assert any(
            "4x_foolhardy_Remacri.pth" in p and "upscale model" in p
            for p in problems
        ), problems

    def test_enabled_when_inventory_has_the_declared_model(
        self, pixel_manifest
    ) -> None:
        inv = _inventory_with(
            upscale_models=["4x_foolhardy_Remacri.pth", "other.pth"]
        )
        assert inv.validate_requires(pixel_manifest.requires) == []

    def test_disabled_when_only_other_models_present(
        self, pixel_manifest
    ) -> None:
        """Operator installed an upscale model but not the one declared."""
        inv = _inventory_with(upscale_models=["4x-ClearRealityV1.pth"])
        problems = inv.validate_requires(pixel_manifest.requires)
        assert problems
        assert any("4x_foolhardy_Remacri.pth" in p for p in problems)

    def test_declares_upscale_model_select(self, pixel_manifest) -> None:
        slot = pixel_manifest.slots_by_name()["upscale_model"]
        assert slot.options_from == "comfyui.upscale_models"


class TestManifestDirectoryLoads:
    def test_directory_load_includes_both_upscale_manifests(self) -> None:
        loaded, errors = load_manifest_directory("workflows/manifests")
        ids = {m.id for m in loaded}
        assert "image_upscale_latent" in ids
        assert "image_upscale_pixel_ultimate" in ids
        assert not errors, f"unexpected manifest load errors: {errors}"
