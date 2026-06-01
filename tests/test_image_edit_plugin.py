"""Tests for the image_edit Plugin (ADR-0002, Slice 3a).

Seams under test:

- Plugin contract surface (``modality`` / ``output_media``).
- ``validate_slot_values`` coerces raw user input to canonical types
  (IMAGE slots pass through as strings; TEXT/SEED/ENUM/FLOAT coerce
  and validation rules fire), and rejects unknown slots / out-of-range
  numbers.
- ``progress_mapper`` reaches 100 on ``ExecutionComplete`` and on the
  closing ``executing(node=None)`` event, and is monotone.
- ``render_outputs`` builds an embed that surfaces the edit
  instruction, the seed, every source-image filename, and attaches the
  output PNG.
- ``default_post_actions`` echoes the Manifest's declared Actions (the
  image_edit Modality is a legitimate chain point - "Upscale this
  edit" and "Animate this edit" are valid follow-ups).
- The Plugin is registered in :data:`core.modalities.default_registry`
  for :class:`Modality.IMAGE_EDIT`.

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
from core.manifest.schema import Action, ActionMap
from core.modalities import default_registry
from core.modalities.base import SlotValueValidationError
from core.modalities.image_edit.plugin import ImageEditPlugin
from core.run import Output, Run, RunStatus


@pytest.fixture
def manifest_1():
    return load_manifest("workflows/manifests/qwen_image_edit_2511_1image.yaml")


@pytest.fixture
def manifest_2():
    return load_manifest("workflows/manifests/qwen_image_edit_2511_2images.yaml")


@pytest.fixture
def manifest_3():
    return load_manifest("workflows/manifests/qwen_image_edit_2511_3images.yaml")


@pytest.fixture
def plugin() -> ImageEditPlugin:
    return ImageEditPlugin()


class TestPluginContract:
    def test_modality(self, plugin: ImageEditPlugin) -> None:
        assert plugin.modality == Modality.IMAGE_EDIT

    def test_output_media_is_png(self, plugin: ImageEditPlugin) -> None:
        assert plugin.output_media == ["image/png"]

    def test_registered_in_default_registry(self) -> None:
        registered = default_registry.get(Modality.IMAGE_EDIT)
        assert isinstance(registered, ImageEditPlugin)


class TestValidateSlotValues:
    @pytest.mark.asyncio
    async def test_coerces_seed_and_passes_image(self, plugin, manifest_1):
        out = await plugin.validate_slot_values(
            manifest_1,
            {
                "prompt": "make the sky red",
                "image_1": "uploaded_source.png",
                "seed": "12345",
                "lora_strength": "0.5",
            },
        )
        assert out["prompt"] == "make the sky red"
        assert out["image_1"] == "uploaded_source.png"
        assert out["seed"] == 12345
        assert isinstance(out["lora_strength"], float)
        assert out["lora_strength"] == 0.5

    @pytest.mark.asyncio
    async def test_seed_random_string(self, plugin, manifest_1):
        out = await plugin.validate_slot_values(
            manifest_1,
            {
                "prompt": "x",
                "image_1": "a.png",
                "seed": "random",
            },
        )
        assert isinstance(out["seed"], int)
        assert 0 <= out["seed"] < 2**63

    @pytest.mark.asyncio
    async def test_empty_prompt_rejected(self, plugin, manifest_1):
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest_1,
                {
                    "prompt": "",
                    "image_1": "a.png",
                },
            )

    @pytest.mark.asyncio
    async def test_lora_strength_above_max_rejected(self, plugin, manifest_1):
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest_1,
                {
                    "prompt": "x",
                    "image_1": "a.png",
                    "lora_strength": "5.0",
                },
            )

    @pytest.mark.asyncio
    async def test_unknown_slot_rejected(self, plugin, manifest_1):
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest_1,
                {
                    "prompt": "x",
                    "image_1": "a.png",
                    "nope": "anything",
                },
            )

    @pytest.mark.asyncio
    async def test_two_image_manifest_accepts_both_sources(
        self, plugin, manifest_2
    ):
        out = await plugin.validate_slot_values(
            manifest_2,
            {
                "prompt": "compose",
                "image_1": "a.png",
                "image_2": "b.png",
            },
        )
        assert out["image_1"] == "a.png"
        assert out["image_2"] == "b.png"

    @pytest.mark.asyncio
    async def test_three_image_manifest_accepts_all_sources(
        self, plugin, manifest_3
    ):
        out = await plugin.validate_slot_values(
            manifest_3,
            {
                "prompt": "compose",
                "image_1": "a.png",
                "image_2": "b.png",
                "image_3": "c.png",
            },
        )
        assert out["image_1"] == "a.png"
        assert out["image_2"] == "b.png"
        assert out["image_3"] == "c.png"


class TestProgressMapper:
    def test_reconnected_returns_none_initially(self, plugin):
        mapper = plugin.progress_mapper()
        assert mapper.update(Reconnected()) is None

    def test_execution_complete_jumps_to_100(self, plugin):
        mapper = plugin.progress_mapper()
        assert mapper.update(ExecutionComplete(prompt_id="x")) == 100

    def test_executing_null_node_means_done(self, plugin):
        mapper = plugin.progress_mapper()
        assert mapper.update(Executing(node=None, prompt_id="x")) == 100

    def test_progress_events_are_monotone(self, plugin):
        mapper = plugin.progress_mapper()
        seq = []
        for v in range(1, 5):
            seq.append(mapper.update(Progress(node="13", value=v, max=4)))
        filtered = [s for s in seq if s is not None]
        assert filtered == sorted(filtered)
        assert filtered[-1] == 100


class TestRenderOutputs:
    @pytest.mark.asyncio
    async def test_renders_instruction_seed_sources_and_attachment(
        self, plugin, manifest_1, tmp_path: Path
    ):
        png_bytes = b"\x89PNG\r\n\x1a\nedited-pixels"
        out_path = tmp_path / "qwen_edit_2511_00001_.png"
        out_path.write_bytes(png_bytes)
        run = Run(
            id=uuid.uuid4().hex,
            manifest_id=manifest_1.id,
            prompt_id="prompt-xyz",
            slot_values={
                "prompt": "Replace the background with a snowy mountain",
                "negative_prompt": "blurry, low-res",
                "image_1": "source_in.png",
                "seed": 4242,
                "lora": "QWEN_EDIT_ACTION_V1.safetensors",
                "lora_strength": 0.0,
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
        assert payload.embed["title"] == manifest_1.id
        names = [f["name"] for f in payload.embed["fields"]]
        assert "Instruction" in names
        assert "Negative" in names
        assert "Sources" in names
        assert "Seed" in names
        assert "Output" in names
        assert len(payload.files) == 1
        assert payload.files[0].filename == "qwen_edit_2511_00001_.png"
        assert payload.embed["image"]["url"] == (
            "attachment://qwen_edit_2511_00001_.png"
        )

    @pytest.mark.asyncio
    async def test_renders_all_three_sources_in_order(
        self, plugin, manifest_3, tmp_path: Path
    ):
        png_bytes = b"x"
        out_path = tmp_path / "edit3.png"
        out_path.write_bytes(png_bytes)
        run = Run(
            id="r",
            manifest_id=manifest_3.id,
            slot_values={
                "prompt": "compose them",
                "image_1": "subject.png",
                "image_2": "outfit.png",
                "image_3": "scene.png",
            },
        )
        output = Output(
            role=Role.OUTPUT_IMAGE,
            media="image/png",
            path=out_path,
            bytes_read=png_bytes,
        )
        payload = await plugin.render_outputs(run, [output])
        sources_field = next(
            f for f in payload.embed["fields"] if f["name"] == "Sources"
        )
        assert "subject.png" in sources_field["value"]
        assert "outfit.png" in sources_field["value"]
        assert "scene.png" in sources_field["value"]
        idx_sub = sources_field["value"].index("subject.png")
        idx_out = sources_field["value"].index("outfit.png")
        idx_sce = sources_field["value"].index("scene.png")
        assert idx_sub < idx_out < idx_sce

    @pytest.mark.asyncio
    async def test_no_outputs_yields_no_files(self, plugin, manifest_1):
        run = Run(id="x", manifest_id=manifest_1.id)
        payload = await plugin.render_outputs(run, [])
        assert payload.files == []
        assert "image" not in payload.embed


class TestDefaultPostActions:
    def test_returns_manifest_actions(self, plugin, manifest_1):
        actions = plugin.default_post_actions(manifest_1)
        ids = {a.id for a in actions}
        assert "upscale" in ids
        assert "animate" in ids

    def test_returns_a_new_list_not_shared(self, plugin, manifest_1):
        returned = plugin.default_post_actions(manifest_1)
        returned.append(
            Action(
                id="extra",
                label="x",
                target_workflow="image_upscale_latent",
                map=[ActionMap(from_output=Role.OUTPUT_IMAGE, to_slot="source_image")],
            )
        )
        assert "extra" not in {a.id for a in manifest_1.actions}
