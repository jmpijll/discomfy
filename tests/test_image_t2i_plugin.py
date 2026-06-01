"""Tests for the image_t2i Plugin (ADR-0002).

Three seams under test:

- ``validate_slot_values`` coerces raw user input to canonical types
  and enforces manifest ``validation`` rules.
- The progress mapper sums KSampler step events across multiple sampler
  nodes into a single monotone 0-100 percentage.
- ``render_outputs`` produces a well-shaped :class:`DiscordPayload`
  with the expected file attachments and embed fields.

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
from core.modalities.image_t2i.plugin import ImageT2IPlugin
from core.run import Output, Run, RunStatus


@pytest.fixture
def manifest():
    return load_manifest("workflows/manifests/qwen_image_2512.yaml")


@pytest.fixture
def plugin() -> ImageT2IPlugin:
    return ImageT2IPlugin()


class TestPluginContract:
    def test_modality(self, plugin: ImageT2IPlugin) -> None:
        assert plugin.modality == Modality.IMAGE_T2I

    def test_output_media_is_png(self, plugin: ImageT2IPlugin) -> None:
        assert plugin.output_media == ["image/png"]


class TestValidateSlotValues:
    @pytest.mark.asyncio
    async def test_coerces_str_int_to_int(self, plugin, manifest) -> None:
        out = await plugin.validate_slot_values(
            manifest, {"prompt": "x", "width": "1024", "height": "1024"}
        )
        assert isinstance(out["width"], int)
        assert out["width"] == 1024

    @pytest.mark.asyncio
    async def test_seed_random_becomes_int(self, plugin, manifest) -> None:
        out = await plugin.validate_slot_values(
            manifest, {"prompt": "x", "seed": "random"}
        )
        assert isinstance(out["seed"], int)
        assert 0 <= out["seed"] < 2**63

    @pytest.mark.asyncio
    async def test_seed_explicit_int_string_preserved(
        self, plugin, manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            manifest, {"prompt": "x", "seed": "42"}
        )
        assert out["seed"] == 42

    @pytest.mark.asyncio
    async def test_seed_empty_or_blank_becomes_random_int(
        self, plugin, manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            manifest, {"prompt": "x", "seed": "  "}
        )
        assert isinstance(out["seed"], int)

    @pytest.mark.asyncio
    async def test_rejects_unknown_slot_name(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest, {"prompt": "x", "not_a_slot": 1}
            )

    @pytest.mark.asyncio
    async def test_enforces_min_violation(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest, {"prompt": "x", "width": "256"}
            )

    @pytest.mark.asyncio
    async def test_enforces_max_violation(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest, {"prompt": "x", "width": "8192"}
            )

    @pytest.mark.asyncio
    async def test_enforces_multiple_of(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest, {"prompt": "x", "width": "777"}
            )

    @pytest.mark.asyncio
    async def test_enforces_max_length(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest, {"prompt": "x" * 3000}
            )


class TestProgressMapper:
    def test_no_progress_returns_none(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        assert mapper.update(Reconnected()) is None

    def test_single_node_progress(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        assert mapper.update(Progress(node="8", value=2, max=8)) == 25
        assert mapper.update(Progress(node="8", value=8, max=8)) == 100

    def test_monotone_across_two_nodes(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        out = []
        for v in range(1, 9):
            out.append(mapper.update(Progress(node="8", value=v, max=8)))
        out.append(mapper.update(Progress(node="14", value=1, max=4)))
        out.append(mapper.update(Progress(node="14", value=2, max=4)))
        out.append(mapper.update(Progress(node="14", value=3, max=4)))
        out.append(mapper.update(Progress(node="14", value=4, max=4)))
        filtered = [p for p in out if p is not None]
        assert filtered == sorted(filtered), filtered
        assert filtered[-1] == 100

    def test_execution_complete_sets_100(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Progress(node="8", value=1, max=8))
        assert mapper.update(ExecutionComplete(prompt_id="x")) == 100

    def test_executing_null_node_sets_100(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Progress(node="8", value=1, max=8))
        assert mapper.update(Executing(node=None, prompt_id="x")) == 100

    def test_ignores_unrelated_events(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Progress(node="8", value=2, max=8))
        assert mapper.update(Executing(node="14", prompt_id="x")) is None


class TestRenderOutputs:
    @pytest.mark.asyncio
    async def test_builds_payload_with_image_attachment(
        self, plugin, manifest, tmp_path: Path
    ) -> None:
        png_bytes = b"\x89PNG\r\n\x1a\nfake-pixels"
        out_path = tmp_path / "smoke_00001_.png"
        out_path.write_bytes(png_bytes)
        run = Run(
            id=uuid.uuid4().hex,
            manifest_id=manifest.id,
            prompt_id="prompt-id-xyz",
            slot_values={"prompt": "a red panda", "width": 1024, "height": 1024, "seed": 42},
            status=RunStatus.COMPLETE,
        )
        output = Output(
            role=Role.OUTPUT_IMAGE,
            media="image/png",
            path=out_path,
            bytes_read=png_bytes,
        )
        payload = await plugin.render_outputs(run, [output])
        assert payload.embed["title"] == manifest.id
        field_names = [f["name"] for f in payload.embed["fields"]]
        assert "Prompt" in field_names
        assert "Size" in field_names
        assert "Seed" in field_names
        assert len(payload.files) == 1
        assert payload.files[0].filename == "smoke_00001_.png"
        assert payload.files[0].content_type == "image/png"
        assert payload.files[0].data == png_bytes
        assert payload.embed["image"]["url"] == "attachment://smoke_00001_.png"

    @pytest.mark.asyncio
    async def test_truncates_long_prompt(self, plugin, manifest, tmp_path) -> None:
        run = Run(
            id="x",
            manifest_id=manifest.id,
            slot_values={"prompt": "x" * 5000},
        )
        out_path = tmp_path / "f.png"
        out_path.write_bytes(b"d")
        output = Output(
            role=Role.OUTPUT_IMAGE,
            media="image/png",
            path=out_path,
            bytes_read=b"d",
        )
        payload = await plugin.render_outputs(run, [output])
        prompt_field = next(
            f for f in payload.embed["fields"] if f["name"] == "Prompt"
        )
        assert len(prompt_field["value"]) <= 1024

    @pytest.mark.asyncio
    async def test_no_outputs_yields_no_files(self, plugin, manifest) -> None:
        run = Run(id="x", manifest_id=manifest.id)
        payload = await plugin.render_outputs(run, [])
        assert payload.files == []
        assert "image" not in payload.embed


class TestDefaultPostActions:
    def test_returns_manifest_actions_verbatim(self, plugin, manifest) -> None:
        actions = plugin.default_post_actions(manifest)
        assert [a.id for a in actions] == [a.id for a in manifest.actions]
