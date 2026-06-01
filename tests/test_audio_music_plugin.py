"""Tests for the audio_music Modality Plugin (ADR-0002, ADR-0007).

Three seams under test:

- ``validate_slot_values`` coerces TEXT / FLOAT / SEED slot values
  and enforces manifest validation rules including the ``seconds``
  numeric bounds the ACE-Step manifest declares.
- The progress mapper produces a monotone 0..100 sequence covering
  the ``Executing`` / ``Progress`` / ``ExecutionComplete`` events
  emitted by the standard ``KSampler`` ACE-Step samples through.
- ``render_outputs`` builds a :class:`DiscordPayload` with the MP3
  attachment, a duration label, the tag prompt, requested seconds,
  seed, and (when ffmpeg is available) a waveform preview attachment.

No live ComfyUI; no Discord runtime.
"""

from __future__ import annotations

import struct
import uuid
import wave
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
from core.modalities import audio_common
from core.modalities.audio_music.plugin import (
    KSAMPLER_NODE_ID_DEFAULT,
    AudioMusicPlugin,
)
from core.modalities.base import SlotValueValidationError
from core.run import Output, Run, RunStatus


@pytest.fixture
def manifest():
    return load_manifest("workflows/manifests/audio_music_acestep.yaml")


@pytest.fixture
def plugin() -> AudioMusicPlugin:
    return AudioMusicPlugin()


def _write_tiny_wav(path: Path) -> Path:
    import math

    sample_rate = 8000
    n = sample_rate // 4
    frames = bytearray()
    for i in range(n):
        amp = int(0.3 * 32767 * math.sin(2 * math.pi * 440 * i / sample_rate))
        frames.extend(struct.pack("<h", amp))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(bytes(frames))
    return path


class TestPluginContract:
    def test_modality(self, plugin: AudioMusicPlugin) -> None:
        assert plugin.modality == Modality.AUDIO_MUSIC

    def test_output_media_is_mp3(self, plugin: AudioMusicPlugin) -> None:
        assert plugin.output_media == ["audio/mpeg"]

    def test_exposes_sampler_node_id(self) -> None:
        assert KSAMPLER_NODE_ID_DEFAULT == "5"


class TestValidateSlotValues:
    @pytest.mark.asyncio
    async def test_simple_prompt_and_random_seed(
        self, plugin: AudioMusicPlugin, manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            manifest,
            {"prompt": "upbeat synthwave 120bpm", "seed": "random", "seconds": 10},
        )
        assert out["prompt"] == "upbeat synthwave 120bpm"
        assert isinstance(out["seed"], int)
        assert isinstance(out["seconds"], float)
        assert out["seconds"] == 10.0

    @pytest.mark.asyncio
    async def test_rejects_empty_prompt(
        self, plugin: AudioMusicPlugin, manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(manifest, {"prompt": ""})

    @pytest.mark.asyncio
    async def test_rejects_unknown_slot(
        self, plugin: AudioMusicPlugin, manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest, {"prompt": "x", "nonsense": 1}
            )

    @pytest.mark.asyncio
    async def test_rejects_zero_seconds(
        self, plugin: AudioMusicPlugin, manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest, {"prompt": "x", "seconds": 0}
            )

    @pytest.mark.asyncio
    async def test_rejects_excessive_seconds(
        self, plugin: AudioMusicPlugin, manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest, {"prompt": "x", "seconds": 9999}
            )

    @pytest.mark.asyncio
    async def test_negative_prompt_accepts_empty(
        self, plugin: AudioMusicPlugin, manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            manifest, {"prompt": "x", "negative_prompt": ""}
        )
        assert out["negative_prompt"] == ""


class TestProgressMapper:
    def test_reconnected_yields_none_first(self, plugin: AudioMusicPlugin) -> None:
        mapper = plugin.progress_mapper()
        assert mapper.update(Reconnected()) is None

    def test_first_executing_reports_one(self, plugin: AudioMusicPlugin) -> None:
        mapper = plugin.progress_mapper()
        assert mapper.update(Executing(node="5", prompt_id="p")) == 1

    def test_progress_scales_into_band(self, plugin: AudioMusicPlugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Executing(node="5", prompt_id="p"))
        v = mapper.update(Progress(node="5", value=4, max=8))
        assert v is not None and 1 <= v <= 99

    def test_progress_full_step_count_caps_at_99(
        self, plugin: AudioMusicPlugin
    ) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Executing(node="5", prompt_id="p"))
        v = mapper.update(Progress(node="5", value=8, max=8))
        assert v == 99

    def test_monotone_across_progress(self, plugin: AudioMusicPlugin) -> None:
        mapper = plugin.progress_mapper()
        seen = []
        mapper.update(Executing(node="5", prompt_id="p"))
        for v in range(1, 9):
            r = mapper.update(Progress(node="5", value=v, max=8))
            if r is not None:
                seen.append(r)
        assert seen == sorted(seen)
        assert seen[-1] <= 99

    def test_execution_complete_pins_100(self, plugin: AudioMusicPlugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Executing(node="5", prompt_id="p"))
        mapper.update(Progress(node="5", value=2, max=8))
        assert mapper.update(ExecutionComplete(prompt_id="p")) == 100

    def test_executing_null_node_pins_100(
        self, plugin: AudioMusicPlugin
    ) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Executing(node="5", prompt_id="p"))
        assert mapper.update(Executing(node=None, prompt_id="p")) == 100

    def test_repeat_pct_returns_none(self, plugin: AudioMusicPlugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Executing(node="5", prompt_id="p"))
        assert mapper.update(Executing(node="5", prompt_id="p")) is None

    def test_reconnected_returns_last_pct(
        self, plugin: AudioMusicPlugin
    ) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Executing(node="5", prompt_id="p"))
        mapper.update(Progress(node="5", value=4, max=8))
        assert mapper.update(Reconnected(attempt=1)) is not None


class TestRenderOutputs:
    @pytest.mark.asyncio
    async def test_builds_payload_with_mp3_and_metadata(
        self,
        plugin: AudioMusicPlugin,
        manifest,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        out_path = _write_tiny_wav(tmp_path / "ace_00001_.wav")
        run = Run(
            id=uuid.uuid4().hex,
            manifest_id=manifest.id,
            prompt_id="prompt-id-xyz",
            slot_values={
                "prompt": "upbeat synthwave 120bpm",
                "negative_prompt": "harsh, low quality",
                "seconds": 10.0,
                "seed": 42,
            },
            status=RunStatus.COMPLETE,
        )
        output = Output(
            role=Role.OUTPUT_AUDIO,
            media="audio/mpeg",
            path=out_path,
            bytes_read=out_path.read_bytes(),
        )
        monkeypatch.setattr(audio_common, "_find_ffmpeg", lambda: None)
        payload = await plugin.render_outputs(run, [output])

        assert payload.embed["title"] == manifest.id
        field_names = [f["name"] for f in payload.embed["fields"]]
        assert "Tags" in field_names
        assert "Negative" in field_names
        assert "Duration" in field_names
        assert "Requested" in field_names
        assert "Seed" in field_names

        attached_names = [f.filename for f in payload.files]
        assert out_path.name in attached_names

    @pytest.mark.asyncio
    async def test_oversize_skips_attachment_with_note(
        self,
        plugin: AudioMusicPlugin,
        manifest,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from core.modalities import audio_common as ac

        oversize_bytes = b"\x00" * (ac.DISCORD_AUDIO_SIZE_LIMIT_BYTES + 16)
        out_path = tmp_path / "huge.mp3"
        out_path.write_bytes(oversize_bytes)

        run = Run(
            id="r",
            manifest_id=manifest.id,
            slot_values={"prompt": "x"},
        )
        output = Output(
            role=Role.OUTPUT_AUDIO,
            media="audio/mpeg",
            path=out_path,
            bytes_read=oversize_bytes,
        )
        monkeypatch.setattr(audio_common, "_find_ffmpeg", lambda: None)
        payload = await plugin.render_outputs(run, [output])

        assert payload.files == []
        assert "over Discord" in (payload.embed.get("description") or "")

    @pytest.mark.asyncio
    async def test_no_outputs_yields_no_files(
        self, plugin: AudioMusicPlugin, manifest
    ) -> None:
        run = Run(id="r", manifest_id=manifest.id)
        payload = await plugin.render_outputs(run, [])
        assert payload.files == []

    @pytest.mark.asyncio
    async def test_negative_prompt_omitted_when_empty(
        self,
        plugin: AudioMusicPlugin,
        manifest,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        out_path = _write_tiny_wav(tmp_path / "ace.wav")
        run = Run(
            id="r",
            manifest_id=manifest.id,
            slot_values={"prompt": "synth", "negative_prompt": ""},
        )
        output = Output(
            role=Role.OUTPUT_AUDIO,
            media="audio/mpeg",
            path=out_path,
            bytes_read=out_path.read_bytes(),
        )
        monkeypatch.setattr(audio_common, "_find_ffmpeg", lambda: None)
        payload = await plugin.render_outputs(run, [output])
        names = [f["name"] for f in payload.embed["fields"]]
        assert "Negative" not in names


class TestDefaultPostActions:
    def test_returns_manifest_actions_verbatim(
        self, plugin: AudioMusicPlugin, manifest
    ) -> None:
        assert plugin.default_post_actions(manifest) == list(manifest.actions)
