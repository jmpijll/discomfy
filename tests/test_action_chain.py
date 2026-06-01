"""Tests for Manifest Action chains (Slice 4 / ADR-0001).

When the Author clicks an Action button under a posted image, the bot
maps each declared ``ActionMap`` entry from the source Run's Outputs
into a SlotValues dict shaped for the *target* Manifest. The wiring is
pure data: no Python switch statement gets to participate.

These tests verify:

- ``apply_action_mapping`` produces a SlotValues dict whose keys match
  the target Manifest's slot names and whose values are the source
  Output filenames.
- The dict it produces validates cleanly against the target Manifest
  through the target Modality's Plugin.
- The Slice 1 manifest (``qwen_image_2512``) wires its ``upscale``
  Action to the Slice 4 latent-upscale manifest by id, exactly as
  ADR-0001's example shows.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.manifest import (
    Manifest,
    apply_action_mapping,
    load_manifest,
)
from core.manifest.applier import ActionMappingError
from core.manifest.roles import Role
from core.modalities import default_registry
from core.run import Output


@pytest.fixture
def source_manifest() -> Manifest:
    """The Slice 1 manifest that declares an upscale Action."""
    return load_manifest("workflows/manifests/qwen_image_2512.yaml")


@pytest.fixture
def upscale_manifest() -> Manifest:
    return load_manifest("workflows/manifests/upscale_latent.yaml")


@pytest.fixture
def png_output(tmp_path: Path) -> Output:
    png_path = tmp_path / "qwen_image_2512_00042_.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    return Output(
        role=Role.OUTPUT_IMAGE,
        media="image/png",
        path=png_path,
        bytes_read=b"\x89PNG\r\n\x1a\nfake",
    )


class TestUpscaleActionWiring:
    def test_source_manifest_declares_upscale_action(
        self, source_manifest: Manifest
    ) -> None:
        upscale = next(
            (a for a in source_manifest.actions if a.id == "upscale"), None
        )
        assert upscale is not None, source_manifest.actions

    def test_upscale_action_targets_latent_upscale_by_id(
        self, source_manifest: Manifest, upscale_manifest: Manifest
    ) -> None:
        upscale = next(a for a in source_manifest.actions if a.id == "upscale")
        assert upscale.target_workflow == upscale_manifest.id

    def test_upscale_action_maps_output_image_to_source_image(
        self, source_manifest: Manifest
    ) -> None:
        upscale = next(a for a in source_manifest.actions if a.id == "upscale")
        assert len(upscale.map) == 1
        wire = upscale.map[0]
        assert wire.from_output == Role.OUTPUT_IMAGE
        assert wire.to_slot == "source_image"


class TestApplyActionMapping:
    def test_produces_slot_values_with_output_filename(
        self,
        source_manifest: Manifest,
        png_output: Output,
    ) -> None:
        upscale = next(a for a in source_manifest.actions if a.id == "upscale")
        values = apply_action_mapping(upscale, [png_output])
        assert values == {"source_image": png_output.filename}

    def test_raises_when_required_role_is_missing(
        self,
        source_manifest: Manifest,
    ) -> None:
        upscale = next(a for a in source_manifest.actions if a.id == "upscale")
        with pytest.raises(ActionMappingError):
            apply_action_mapping(upscale, [])

    def test_uses_first_matching_output_when_multiple(
        self,
        source_manifest: Manifest,
        tmp_path: Path,
    ) -> None:
        first = Output(
            role=Role.OUTPUT_IMAGE,
            media="image/png",
            path=tmp_path / "first.png",
            bytes_read=b"a",
        )
        second = Output(
            role=Role.OUTPUT_IMAGE,
            media="image/png",
            path=tmp_path / "second.png",
            bytes_read=b"b",
        )
        upscale = next(a for a in source_manifest.actions if a.id == "upscale")
        values = apply_action_mapping(upscale, [first, second])
        assert values == {"source_image": "first.png"}


class TestChainedValuesValidateAgainstTargetPlugin:
    @pytest.mark.asyncio
    async def test_chained_values_pass_upscale_plugin_validation(
        self,
        source_manifest: Manifest,
        upscale_manifest: Manifest,
        png_output: Output,
    ) -> None:
        upscale = next(a for a in source_manifest.actions if a.id == "upscale")
        chained = apply_action_mapping(upscale, [png_output])

        plugin = default_registry.get(upscale_manifest.modality)
        coerced = await plugin.validate_slot_values(upscale_manifest, chained)

        assert coerced["source_image"] == png_output.filename
