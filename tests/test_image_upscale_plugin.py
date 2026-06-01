"""Tests for the image_upscale Plugin (ADR-0002, Slice 4).

Three seams under test:

- ``validate_slot_values`` coerces raw user input to canonical types
  (IMAGE slots pass through as strings; numeric slots coerce + validate)
  and enforces manifest ``validation`` rules.
- The progress mapper reaches 100 on ``ExecutionComplete`` even when the
  upscale workflow emits no ``progress`` events.
- ``render_outputs`` produces a :class:`DiscordPayload` exposing source
  filename, scale factor, and the output attachment.
- ``default_post_actions`` returns an empty list regardless of what the
  Manifest declares - no Upscale-of-Upscale chain.

No live ComfyUI; no Discord runtime.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from core.comfyui.v3.ws import (
    Executing,
    ExecutionComplete,
    Progress,
    Reconnected,
)
from core.manifest import load_manifest
from core.manifest.roles import Modality, Role
from core.modalities.base import SlotValueValidationError
from core.modalities.image_upscale.plugin import ImageUpscalePlugin
from core.run import Output, Run, RunStatus


@pytest.fixture
def latent_manifest():
    return load_manifest("workflows/manifests/upscale_latent.yaml")


@pytest.fixture
def pixel_manifest():
    return load_manifest("workflows/manifests/upscale_pixel_ultimate.yaml")


@pytest.fixture
def plugin() -> ImageUpscalePlugin:
    return ImageUpscalePlugin()


class TestPluginContract:
    def test_modality(self, plugin: ImageUpscalePlugin) -> None:
        assert plugin.modality == Modality.IMAGE_UPSCALE

    def test_output_media_is_png(self, plugin: ImageUpscalePlugin) -> None:
        assert plugin.output_media == ["image/png"]


class TestValidateSlotValues:
    @pytest.mark.asyncio
    async def test_image_slot_string_passes_through(
        self, plugin, latent_manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            latent_manifest,
            {"source_image": "uploaded_input.png", "scale_by": "2.0"},
        )
        assert out["source_image"] == "uploaded_input.png"
        assert isinstance(out["scale_by"], float)
        assert out["scale_by"] == 2.0

    @pytest.mark.asyncio
    async def test_scale_below_min_rejected(
        self, plugin, latent_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                latent_manifest,
                {"source_image": "x.png", "scale_by": "1.0"},
            )

    @pytest.mark.asyncio
    async def test_scale_above_max_rejected(
        self, plugin, latent_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                latent_manifest,
                {"source_image": "x.png", "scale_by": "5.0"},
            )

    @pytest.mark.asyncio
    async def test_unknown_slot_rejected(
        self, plugin, latent_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                latent_manifest, {"source_image": "x.png", "nope": 1}
            )

    @pytest.mark.asyncio
    async def test_pixel_manifest_accepts_model_string(
        self, plugin, pixel_manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            pixel_manifest,
            {
                "source_image": "x.png",
                "upscale_model": "4x_foolhardy_Remacri.pth",
                "scale_by": "0.5",
            },
        )
        assert out["upscale_model"] == "4x_foolhardy_Remacri.pth"
        assert out["scale_by"] == 0.5


class TestProgressMapper:
    def test_reconnected_returns_none_initially(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        assert mapper.update(Reconnected()) is None

    def test_execution_complete_jumps_to_100(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        assert mapper.update(ExecutionComplete(prompt_id="x")) == 100

    def test_executing_null_node_means_done(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        assert mapper.update(Executing(node=None, prompt_id="x")) == 100

    def test_progress_events_are_monotone(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        seq = []
        for v in range(1, 5):
            seq.append(mapper.update(Progress(node="5", value=v, max=4)))
        filtered = [s for s in seq if s is not None]
        assert filtered == sorted(filtered)
        assert filtered[-1] == 100


class TestRenderOutputs:
    @pytest.mark.asyncio
    async def test_renders_source_scale_and_attachment(
        self, plugin, latent_manifest, tmp_path: Path
    ) -> None:
        png_bytes = b"\x89PNG\r\n\x1a\nupscaled-pixels"
        out_path = tmp_path / "upscale_latent_00001_.png"
        out_path.write_bytes(png_bytes)
        run = Run(
            id=uuid.uuid4().hex,
            manifest_id=latent_manifest.id,
            prompt_id="prompt-abc",
            slot_values={
                "source_image": "qwen_image_2512_0001.png",
                "scale_by": 2.0,
            },
            status=RunStatus.COMPLETE,
        )
        output = Output(
            role=Role.OUTPUT_IMAGE,
            media="image/png",
            path=out_path,
            bytes_read=png_bytes,
        )
        payload = await plugin.render_outputs(run, [output])
        assert payload.embed["title"] == latent_manifest.id
        field_names = [f["name"] for f in payload.embed["fields"]]
        assert "Source" in field_names
        assert "Scale" in field_names
        assert "Output" in field_names
        assert len(payload.files) == 1
        assert payload.files[0].filename == "upscale_latent_00001_.png"
        assert payload.embed["image"]["url"] == (
            "attachment://upscale_latent_00001_.png"
        )

    @pytest.mark.asyncio
    async def test_renders_upscale_model_when_pixel(
        self, plugin, pixel_manifest, tmp_path: Path
    ) -> None:
        out_path = tmp_path / "p.png"
        out_path.write_bytes(b"x")
        run = Run(
            id="r",
            manifest_id=pixel_manifest.id,
            slot_values={
                "source_image": "src.png",
                "upscale_model": "4x_foolhardy_Remacri.pth",
                "scale_by": 0.5,
            },
        )
        output = Output(
            role=Role.OUTPUT_IMAGE,
            media="image/png",
            path=out_path,
            bytes_read=b"x",
        )
        payload = await plugin.render_outputs(run, [output])
        field_names = [f["name"] for f in payload.embed["fields"]]
        assert "Upscale model" in field_names

    @pytest.mark.asyncio
    async def test_no_outputs_yields_no_files(
        self, plugin, latent_manifest
    ) -> None:
        run = Run(id="x", manifest_id=latent_manifest.id)
        payload = await plugin.render_outputs(run, [])
        assert payload.files == []
        assert "image" not in payload.embed


class TestDefaultPostActions:
    def test_returns_empty_for_latent_manifest(
        self, plugin, latent_manifest
    ) -> None:
        assert plugin.default_post_actions(latent_manifest) == []

    def test_returns_empty_for_pixel_manifest(
        self, plugin, pixel_manifest
    ) -> None:
        assert plugin.default_post_actions(pixel_manifest) == []

    def test_ignores_manifest_actions_even_if_present(
        self, plugin, latent_manifest
    ) -> None:
        """An Upscale manifest with declared actions still yields no buttons.

        Defends the no-chain UX guarantee against an operator who adds
        actions to their upscale manifest later. Plugin must elide them.
        """
        from core.manifest.schema import Action, ActionMap
        from core.manifest.roles import Role as _Role

        latent_manifest.actions.append(
            Action(
                id="upscale",
                label="Upscale again",
                target_workflow="image_upscale_latent",
                map=[
                    ActionMap(
                        from_output=_Role.OUTPUT_IMAGE,
                        to_slot="source_image",
                    )
                ],
            )
        )
        assert plugin.default_post_actions(latent_manifest) == []
