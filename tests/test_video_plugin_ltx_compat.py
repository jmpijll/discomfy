"""VideoPlugin compatibility tests with the LTX-Video 2.3 22B manifests.

The VideoPlugin (slice 5) was designed around the WAN 2.2 dual-KSampler
pattern (two `Progress` streams, one per UNET pass). The LTX-Video
manifests use a single `SamplerCustomAdvanced` node so they emit only
one `Progress` stream. The mapper must handle that gracefully without
any code change.

This module also exercises ``validate_slot_values`` against both LTX
manifests to confirm the shared coerce/enforce path works for the
LTX-specific slot shapes (frame_count multiple_of=8, width/height
multiple_of=32, dynamic LoRA enum, optional init_image), and re-uses
``render_outputs`` with synthetic Output bytes to confirm the embed
carries the LTX manifest id and the per-Slot fields the plugin extracts.
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
    DEFAULT_VIDEO_FPS,
    DISCORD_FILE_CAP_BYTES,
    VideoPlugin,
)
from core.run import Output, Run, RunStatus


@pytest.fixture
def plugin() -> VideoPlugin:
    return VideoPlugin()


@pytest.fixture
def t2v_manifest():
    return load_manifest("workflows/manifests/ltxv_2_3_22b_t2v.yaml")


@pytest.fixture
def i2v_manifest():
    return load_manifest("workflows/manifests/ltxv_2_3_22b_i2v.yaml")


class TestLTXManifestsLoadUnderVideoPlugin:
    def test_t2v_modality_is_video(self, t2v_manifest, plugin) -> None:
        assert t2v_manifest.modality == plugin.modality
        assert plugin.output_media == ["video/mp4"]

    def test_i2v_modality_is_video(self, i2v_manifest, plugin) -> None:
        assert i2v_manifest.modality == plugin.modality

    @pytest.mark.asyncio
    async def test_t2v_validate_coerces_dimensions_and_seed(
        self, plugin, t2v_manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            t2v_manifest,
            {
                "prompt": "a calm ocean wave at dusk",
                "width": "768",
                "height": "512",
                "frame_count": "97",
                "seed": "random",
                "lora_strength": "0.8",
            },
        )
        assert out["width"] == 768
        assert out["height"] == 512
        assert out["frame_count"] == 97
        assert isinstance(out["seed"], int)
        assert out["lora_strength"] == pytest.approx(0.8)

    @pytest.mark.asyncio
    async def test_t2v_rejects_below_min_frame_count(
        self, plugin, t2v_manifest
    ) -> None:
        # LTX requires length = 1 + 8k; we keep min=9 but no multiple_of
        # constraint since the (8k+1) pattern doesn't fit `multiple_of`.
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                t2v_manifest,
                {"prompt": "x", "frame_count": "4"},
            )

    @pytest.mark.asyncio
    async def test_t2v_rejects_over_max_frame_count(
        self, plugin, t2v_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                t2v_manifest,
                {"prompt": "x", "frame_count": "1024"},
            )

    @pytest.mark.asyncio
    async def test_t2v_rejects_off_multiple_width(
        self, plugin, t2v_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                t2v_manifest,
                {"prompt": "x", "width": "770"},
            )

    @pytest.mark.asyncio
    async def test_i2v_accepts_init_image_filename(
        self, plugin, i2v_manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            i2v_manifest,
            {
                "prompt": "the subject turns",
                "init_image": "uploaded_qwen_frame.png",
                "frame_count": "97",
            },
        )
        assert out["init_image"] == "uploaded_qwen_frame.png"
        assert out["frame_count"] == 97

    @pytest.mark.asyncio
    async def test_i2v_rejects_unknown_slot(
        self, plugin, i2v_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                i2v_manifest,
                {"prompt": "x", "init_image": "x.png", "not_a_slot": 1},
            )


class TestSingleSamplerProgressMapping:
    """LTX uses one SamplerCustomAdvanced node; the mapper must cope."""

    def test_single_sampler_climbs_to_95(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        outputs = []
        for v in range(1, 9):
            outputs.append(mapper.update(Progress(node="14", value=v, max=8)))
        filtered = [p for p in outputs if p is not None]
        assert filtered == sorted(filtered), filtered
        assert filtered[-1] == 95

    def test_post_sample_bump_after_single_stream(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Progress(node="14", value=8, max=8))
        decode = mapper.update(Executing(node="15", prompt_id="p"))
        combine = mapper.update(Executing(node="16", prompt_id="p"))
        assert decode == 97
        assert combine == 99

    def test_ltx_synthetic_event_stream(self, plugin) -> None:
        """Walk through a realistic LTX t2v event order."""
        mapper = plugin.progress_mapper()
        events = [
            Executing(node="1", prompt_id="p"),  # CheckpointLoaderSimple
            Executing(node="2", prompt_id="p"),  # GemmaCLIPModelLoader
            Executing(node="3", prompt_id="p"),  # Q8 LoRA loader
            Executing(node="4", prompt_id="p"),  # ModelSamplingLTXV
            Executing(node="5", prompt_id="p"),  # GemmaEnhancePrompt
            Executing(node="6", prompt_id="p"),  # CLIPTextEncode +
            Executing(node="7", prompt_id="p"),  # CLIPTextEncode -
            Executing(node="8", prompt_id="p"),  # EmptyLTXVLatentVideo
            Executing(node="14", prompt_id="p"),  # SamplerCustomAdvanced
            Progress(node="14", value=1, max=8, prompt_id="p"),
            Progress(node="14", value=4, max=8, prompt_id="p"),
            Progress(node="14", value=8, max=8, prompt_id="p"),
            Executing(node="15", prompt_id="p"),  # VAEDecode
            Executing(node="16", prompt_id="p"),  # VHS_VideoCombine
            ExecutionComplete(prompt_id="p"),
        ]
        series = []
        for ev in events:
            pct = mapper.update(ev)
            if pct is not None:
                series.append(pct)
        assert series[0] > 0
        assert series == sorted(series)
        assert series[-1] == 100
        assert max(s for s in series if s < 100) >= 95

    def test_reconnect_replays_last_pct(self, plugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Progress(node="14", value=3, max=8))
        last = mapper.update(Reconnected())
        assert last is not None


class TestRenderOutputsForLTXManifests:
    @pytest.mark.asyncio
    async def test_t2v_render_carries_size_and_seed(
        self, plugin, t2v_manifest, tmp_path: Path
    ) -> None:
        data = b"\x00\x00\x00\x20ftypmp42" + b"\x00" * 256
        out_path = tmp_path / "ltxv_t2v_00001.mp4"
        out_path.write_bytes(data)
        run = Run(
            id=uuid.uuid4().hex,
            manifest_id=t2v_manifest.id,
            prompt_id="prompt-id-ltx-t2v",
            slot_values={
                "prompt": "a slow cinematic pan",
                "negative_prompt": "static",
                "width": 768,
                "height": 512,
                "frame_count": 97,
                "seed": 11,
            },
            status=RunStatus.COMPLETE,
        )
        output = Output(
            role=Role.OUTPUT_VIDEO,
            media="video/mp4",
            path=out_path,
            bytes_read=data,
        )
        payload = await plugin.render_outputs(run, [output])
        assert payload.embed["title"] == t2v_manifest.id
        names = [f["name"] for f in payload.embed["fields"]]
        assert "Prompt" in names
        assert "Frames" in names
        assert "Size" in names
        assert "Seed" in names
        assert len(payload.files) == 1
        assert payload.files[0].filename == "ltxv_t2v_00001.mp4"

    @pytest.mark.asyncio
    async def test_i2v_render_with_no_outputs(
        self, plugin, i2v_manifest
    ) -> None:
        run = Run(id="x", manifest_id=i2v_manifest.id)
        payload = await plugin.render_outputs(run, [])
        assert payload.files == []
        assert "description" in payload.embed


class TestDefaultPostActions:
    def test_t2v_actions_passthrough(self, plugin, t2v_manifest) -> None:
        actions = plugin.default_post_actions(t2v_manifest)
        assert actions == []  # t2v ships no post-Actions

    def test_i2v_actions_passthrough(self, plugin, i2v_manifest) -> None:
        actions = plugin.default_post_actions(i2v_manifest)
        assert actions == []  # i2v ships no post-Actions either
