"""Tests for the video Plugin (ADR-0002).

Three seams under test:

- ``validate_slot_values`` coerces / validates raw user input against
  the WAN 2.2 i2v manifest, accepting image-slot values as opaque
  filename strings (the SmokeHarness uploads then writes them back).
- The dual-sampler ProgressMapper sums HIGH-pass + LOW-pass KSampler
  ``Progress`` events into a monotone 0-95% stream, bumps on
  post-sampling ``Executing`` events (VAEDecode + VHS_VideoCombine),
  and flips to 100% on ``ExecutionComplete``.
- ``render_outputs`` produces a :class:`DiscordPayload` carrying an MP4
  attachment plus an embed with prompt / frame count / duration / size,
  and falls back to a content message (no attachment) for files over
  the 25 MB Discord cap.

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
from core.modalities.video.plugin import (
    DISCORD_FILE_CAP_BYTES,
    VideoPlugin,
)
from core.run import Output, Run, RunStatus


@pytest.fixture
def manifest():
    return load_manifest("workflows/manifests/wan22_i2v.yaml")


@pytest.fixture
def plugin() -> VideoPlugin:
    return VideoPlugin()


class TestPluginContract:
    def test_modality(self, plugin: VideoPlugin) -> None:
        assert plugin.modality == Modality.VIDEO

    def test_output_media_is_mp4(self, plugin: VideoPlugin) -> None:
        assert plugin.output_media == ["video/mp4"]


class TestValidateSlotValues:
    @pytest.mark.asyncio
    async def test_coerces_frame_count_string_to_int(
        self, plugin, manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            manifest,
            {
                "prompt": "x",
                "init_image": "frame.png",
                "frame_count": "17",
            },
        )
        assert isinstance(out["frame_count"], int)
        assert out["frame_count"] == 17

    @pytest.mark.asyncio
    async def test_init_image_passes_through_filename(
        self, plugin, manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            manifest,
            {"prompt": "x", "init_image": "uploaded_frame.png"},
        )
        assert out["init_image"] == "uploaded_frame.png"

    @pytest.mark.asyncio
    async def test_init_image_accepts_dict_with_filename(
        self, plugin, manifest
    ) -> None:
        attachment = {"filename": "uploaded_frame.png", "subfolder": ""}
        out = await plugin.validate_slot_values(
            manifest,
            {"prompt": "x", "init_image": attachment},
        )
        assert out["init_image"] == attachment

    @pytest.mark.asyncio
    async def test_seed_random_becomes_int(self, plugin, manifest) -> None:
        out = await plugin.validate_slot_values(
            manifest,
            {"prompt": "x", "init_image": "f.png", "seed": "random"},
        )
        assert isinstance(out["seed"], int)

    @pytest.mark.asyncio
    async def test_enforces_steps_high_max(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest,
                {
                    "prompt": "x",
                    "init_image": "f.png",
                    "steps_high": "99",
                },
            )

    @pytest.mark.asyncio
    async def test_enforces_steps_low_min(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest,
                {
                    "prompt": "x",
                    "init_image": "f.png",
                    "steps_low": "1",
                },
            )

    @pytest.mark.asyncio
    async def test_enforces_frame_count_bounds(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest,
                {
                    "prompt": "x",
                    "init_image": "f.png",
                    "frame_count": "500",
                },
            )

    @pytest.mark.asyncio
    async def test_enforces_cfg_bounds(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest,
                {
                    "prompt": "x",
                    "init_image": "f.png",
                    "cfg": "999.0",
                },
            )

    @pytest.mark.asyncio
    async def test_rejects_unknown_slot(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest,
                {"prompt": "x", "init_image": "f.png", "not_a_slot": 1},
            )


class TestProgressMapper:
    def test_reconnect_returns_last(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        assert mapper.update(Reconnected()) is None
        mapper.update(Progress(node="11", value=2, max=4))
        assert mapper.update(Reconnected()) is not None

    def test_caps_sampling_at_95(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        first = mapper.update(Progress(node="11", value=4, max=4))
        second = mapper.update(Progress(node="12", value=4, max=4))
        # First call sees only node 11 at 4/4 -> 95%. Second call adds
        # node 12 at 4/4 -> (4+4)/(4+4)*95 = 95%, which is the same as
        # the last reported value so the mapper returns None.
        assert first == 95
        assert second is None

    def test_monotone_across_two_samplers(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        out = []
        for v in range(1, 5):
            out.append(mapper.update(Progress(node="11", value=v, max=4)))
        for v in range(1, 5):
            out.append(mapper.update(Progress(node="12", value=v, max=4)))
        filtered = [p for p in out if p is not None]
        assert filtered == sorted(filtered), filtered
        assert filtered[-1] == 95

    def test_post_sample_executing_bumps_past_95(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Progress(node="11", value=4, max=4))
        mapper.update(Progress(node="12", value=4, max=4))
        bump1 = mapper.update(Executing(node="13", prompt_id="x"))
        bump2 = mapper.update(Executing(node="14", prompt_id="x"))
        assert bump1 == 97
        assert bump2 == 99

    def test_post_sample_capped_at_99(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Progress(node="11", value=4, max=4))
        mapper.update(Progress(node="12", value=4, max=4))
        last = None
        for node_id in ["13", "14", "15", "16", "17"]:
            last = mapper.update(Executing(node=node_id, prompt_id="x")) or last
        assert last == 99

    def test_executing_for_sampler_node_is_not_a_post_bump(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Progress(node="11", value=4, max=4))
        mapper.update(Progress(node="12", value=2, max=4))
        result = mapper.update(Executing(node="12", prompt_id="x"))
        assert result is None

    def test_pre_sampling_executing_is_ignored(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        result = mapper.update(Executing(node="7", prompt_id="x"))
        assert result is None

    def test_execution_complete_sets_100(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Progress(node="11", value=1, max=4))
        assert mapper.update(ExecutionComplete(prompt_id="x")) == 100

    def test_executing_null_node_sets_100(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Progress(node="11", value=1, max=4))
        assert mapper.update(Executing(node=None, prompt_id="x")) == 100

    def test_wan22_synthetic_stream(self, plugin) -> None:
        """Walk through a realistic WAN 2.2 i2v event sequence."""
        mapper = plugin.progress_mapper()
        events = [
            Executing(node="1", prompt_id="p"),  # UNETLoader HIGH
            Executing(node="2", prompt_id="p"),  # UNETLoader LOW
            Executing(node="7", prompt_id="p"),  # LoadImage
            Executing(node="10", prompt_id="p"),  # WanImageToVideo
            Executing(node="11", prompt_id="p"),  # HIGH KSampler
            Progress(node="11", value=1, max=4, prompt_id="p"),
            Progress(node="11", value=2, max=4, prompt_id="p"),
            Progress(node="11", value=3, max=4, prompt_id="p"),
            Progress(node="11", value=4, max=4, prompt_id="p"),
            Executing(node="12", prompt_id="p"),  # LOW KSampler
            Progress(node="12", value=1, max=4, prompt_id="p"),
            Progress(node="12", value=2, max=4, prompt_id="p"),
            Progress(node="12", value=3, max=4, prompt_id="p"),
            Progress(node="12", value=4, max=4, prompt_id="p"),
            Executing(node="13", prompt_id="p"),  # VAEDecode (post-sample)
            Executing(node="14", prompt_id="p"),  # VHS_VideoCombine
            ExecutionComplete(prompt_id="p"),
        ]
        series = []
        for ev in events:
            pct = mapper.update(ev)
            if pct is not None:
                series.append(pct)
        assert series[0] > 0
        assert max(series) == 100
        assert series == sorted(series)
        assert 95 in series or any(p >= 95 for p in series)


class TestRenderOutputs:
    @pytest.mark.asyncio
    async def test_builds_payload_with_mp4_attachment(
        self, plugin, manifest, tmp_path: Path
    ) -> None:
        mp4_bytes = b"\x00\x00\x00\x20ftypmp42" + b"\x00" * 64
        out_path = tmp_path / "wan22_i2v_00001.mp4"
        out_path.write_bytes(mp4_bytes)
        run = Run(
            id=uuid.uuid4().hex,
            manifest_id=manifest.id,
            prompt_id="prompt-id-xyz",
            slot_values={
                "prompt": "camera pans right",
                "negative_prompt": "blurry",
                "init_image": "src.png",
                "frame_count": 17,
                "seed": 42,
            },
            status=RunStatus.COMPLETE,
        )
        output = Output(
            role=Role.OUTPUT_VIDEO,
            media="video/mp4",
            path=out_path,
            bytes_read=mp4_bytes,
        )
        payload = await plugin.render_outputs(run, [output])

        assert payload.embed["title"] == manifest.id
        field_names = [f["name"] for f in payload.embed["fields"]]
        assert "Prompt" in field_names
        assert "Negative" in field_names
        assert "Frames" in field_names
        assert "Duration" in field_names
        assert "Seed" in field_names
        assert "File size" in field_names
        assert len(payload.files) == 1
        assert payload.files[0].filename == "wan22_i2v_00001.mp4"
        assert payload.files[0].content_type == "video/mp4"
        assert payload.files[0].data == mp4_bytes
        assert payload.content is None

    @pytest.mark.asyncio
    async def test_oversize_video_omits_attachment(
        self, plugin, manifest, tmp_path: Path
    ) -> None:
        oversized = b"\x00" * (DISCORD_FILE_CAP_BYTES + 1024)
        out_path = tmp_path / "huge.mp4"
        out_path.write_bytes(oversized)
        run = Run(
            id="x",
            manifest_id=manifest.id,
            prompt_id="pid",
            slot_values={"prompt": "x", "frame_count": 81},
        )
        output = Output(
            role=Role.OUTPUT_VIDEO,
            media="video/mp4",
            path=out_path,
            bytes_read=oversized,
        )
        payload = await plugin.render_outputs(run, [output])
        assert payload.files == []
        assert payload.content is not None
        assert "huge.mp4" in payload.content
        assert "/view" in payload.content
        assert "description" in payload.embed
        assert "too large" in payload.embed["description"].lower()

    @pytest.mark.asyncio
    async def test_no_outputs_yields_no_files(self, plugin, manifest) -> None:
        run = Run(id="x", manifest_id=manifest.id)
        payload = await plugin.render_outputs(run, [])
        assert payload.files == []
        assert "description" in payload.embed

    @pytest.mark.asyncio
    async def test_truncates_long_prompt(
        self, plugin, manifest, tmp_path: Path
    ) -> None:
        mp4 = b"\x00" * 128
        out_path = tmp_path / "v.mp4"
        out_path.write_bytes(mp4)
        run = Run(
            id="x",
            manifest_id=manifest.id,
            slot_values={"prompt": "x" * 5000},
        )
        output = Output(
            role=Role.OUTPUT_VIDEO,
            media="video/mp4",
            path=out_path,
            bytes_read=mp4,
        )
        payload = await plugin.render_outputs(run, [output])
        prompt_field = next(
            f for f in payload.embed["fields"] if f["name"] == "Prompt"
        )
        assert len(prompt_field["value"]) <= 1024


class TestDefaultPostActions:
    def test_returns_manifest_actions_verbatim(self, plugin, manifest) -> None:
        actions = plugin.default_post_actions(manifest)
        assert [a.id for a in actions] == [a.id for a in manifest.actions]
        assert actions == []  # v3.0 wan22_i2v ships no actions yet
