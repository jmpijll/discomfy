"""Tests for the audio_tts Modality Plugin (ADR-0002, ADR-0007).

Three seams under test:

- ``validate_slot_values`` coerces TEXT / SEED / AUDIO slot values,
  enforces manifest validation rules including ``accepts`` mime
  filters, and rejects shape-bad audio dicts.
- The progress mapper produces a monotone 0..100 sequence covering
  the ``Executing`` / ``Progress`` / ``ExecutionComplete`` events
  Fish-Speech surfaces in practice.
- ``render_outputs`` builds a :class:`DiscordPayload` with the MP3
  attachment, a duration label, and (when ffmpeg is available) a
  waveform preview attachment.

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
from core.modalities.audio_tts.plugin import AudioTTSPlugin
from core.modalities.base import SlotValueValidationError
from core.run import Output, Run, RunStatus


@pytest.fixture
def simple_manifest():
    return load_manifest("workflows/manifests/audio_tts_fish_simple.yaml")


@pytest.fixture
def voiceclone_manifest():
    return load_manifest("workflows/manifests/audio_tts_fish_voiceclone.yaml")


@pytest.fixture
def plugin() -> AudioTTSPlugin:
    return AudioTTSPlugin()


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
    def test_modality(self, plugin: AudioTTSPlugin) -> None:
        assert plugin.modality == Modality.AUDIO_TTS

    def test_output_media_is_mp3(self, plugin: AudioTTSPlugin) -> None:
        assert plugin.output_media == ["audio/mpeg"]


class TestValidateSlotValues:
    @pytest.mark.asyncio
    async def test_simple_text_and_random_seed(
        self, plugin: AudioTTSPlugin, simple_manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            simple_manifest, {"text": "hello", "seed": "random"}
        )
        assert out["text"] == "hello"
        assert isinstance(out["seed"], int)

    @pytest.mark.asyncio
    async def test_rejects_empty_text(
        self, plugin: AudioTTSPlugin, simple_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(simple_manifest, {"text": ""})

    @pytest.mark.asyncio
    async def test_rejects_unknown_slot(
        self, plugin: AudioTTSPlugin, simple_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                simple_manifest, {"text": "x", "nonsense": 1}
            )

    @pytest.mark.asyncio
    async def test_audio_slot_accepts_path_string(
        self, plugin: AudioTTSPlugin, voiceclone_manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            voiceclone_manifest,
            {"text": "hi", "voice_reference": "ref.wav"},
        )
        assert out["voice_reference"] == "ref.wav"

    @pytest.mark.asyncio
    async def test_audio_slot_accepts_pathlib(
        self, plugin: AudioTTSPlugin, voiceclone_manifest, tmp_path: Path
    ) -> None:
        p = tmp_path / "ref.wav"
        p.write_bytes(b"x")
        out = await plugin.validate_slot_values(
            voiceclone_manifest,
            {"text": "hi", "voice_reference": p},
        )
        assert out["voice_reference"] == str(p)

    @pytest.mark.asyncio
    async def test_audio_slot_accepts_attachment_dict(
        self, plugin: AudioTTSPlugin, voiceclone_manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            voiceclone_manifest,
            {
                "text": "hi",
                "voice_reference": {
                    "filename": "user.wav",
                    "mime": "audio/wav",
                    "data": b"riffwavedata",
                },
            },
        )
        ref = out["voice_reference"]
        assert ref["filename"] == "user.wav"
        assert ref["mime"] == "audio/wav"
        assert ref["data"] == b"riffwavedata"

    @pytest.mark.asyncio
    async def test_audio_slot_rejects_bad_dict_keys(
        self, plugin: AudioTTSPlugin, voiceclone_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                voiceclone_manifest,
                {
                    "text": "hi",
                    "voice_reference": {
                        "filename": "user.wav",
                        "data": b"x",
                        "extra": "nope",
                    },
                },
            )

    @pytest.mark.asyncio
    async def test_audio_slot_rejects_unaccepted_mime(
        self, plugin: AudioTTSPlugin, voiceclone_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                voiceclone_manifest,
                {
                    "text": "hi",
                    "voice_reference": {
                        "filename": "user.flac",
                        "mime": "audio/flac",
                        "data": b"x",
                    },
                },
            )

    @pytest.mark.asyncio
    async def test_audio_slot_accepts_listed_mime(
        self, plugin: AudioTTSPlugin, voiceclone_manifest
    ) -> None:
        out = await plugin.validate_slot_values(
            voiceclone_manifest,
            {
                "text": "hi",
                "voice_reference": {
                    "filename": "user.wav",
                    "mime": "audio/wav",
                    "data": b"x",
                },
            },
        )
        assert out["voice_reference"]["mime"] == "audio/wav"

    @pytest.mark.asyncio
    async def test_audio_slot_rejects_wrong_type(
        self, plugin: AudioTTSPlugin, voiceclone_manifest
    ) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                voiceclone_manifest,
                {"text": "hi", "voice_reference": 12345},
            )


class TestProgressMapper:
    def test_reconnected_yields_none(self, plugin: AudioTTSPlugin) -> None:
        mapper = plugin.progress_mapper()
        assert mapper.update(Reconnected()) is None

    def test_first_executing_reports_5(self, plugin: AudioTTSPlugin) -> None:
        mapper = plugin.progress_mapper()
        assert mapper.update(Executing(node="1", prompt_id="p")) == 5

    def test_progress_scales_into_band(self, plugin: AudioTTSPlugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Executing(node="1", prompt_id="p"))
        v = mapper.update(Progress(node="1", value=5, max=10))
        assert v is not None and 5 <= v <= 95

    def test_monotone_across_progress(self, plugin: AudioTTSPlugin) -> None:
        mapper = plugin.progress_mapper()
        seen = []
        mapper.update(Executing(node="1", prompt_id="p"))
        for v in range(1, 11):
            r = mapper.update(Progress(node="1", value=v, max=10))
            if r is not None:
                seen.append(r)
        assert seen == sorted(seen)
        assert seen[-1] <= 95

    def test_execution_complete_pins_100(self, plugin: AudioTTSPlugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Executing(node="1", prompt_id="p"))
        mapper.update(Progress(node="1", value=2, max=10))
        assert mapper.update(ExecutionComplete(prompt_id="p")) == 100

    def test_executing_null_node_pins_100(self, plugin: AudioTTSPlugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Executing(node="1", prompt_id="p"))
        assert mapper.update(Executing(node=None, prompt_id="p")) == 100

    def test_repeat_pct_returns_none(self, plugin: AudioTTSPlugin) -> None:
        mapper = plugin.progress_mapper()
        mapper.update(Executing(node="1", prompt_id="p"))
        assert mapper.update(Executing(node="1", prompt_id="p")) is None


class TestRenderOutputs:
    @pytest.mark.asyncio
    async def test_builds_payload_with_mp3_and_duration(
        self,
        plugin: AudioTTSPlugin,
        simple_manifest,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        out_path = _write_tiny_wav(tmp_path / "tts_00001_.wav")
        run = Run(
            id=uuid.uuid4().hex,
            manifest_id=simple_manifest.id,
            prompt_id="prompt-id-xyz",
            slot_values={"text": "Hello world", "seed": 42},
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

        assert payload.embed["title"] == simple_manifest.id
        field_names = [f["name"] for f in payload.embed["fields"]]
        assert "Text" in field_names
        assert "Duration" in field_names
        assert "Seed" in field_names

        attached_names = [f.filename for f in payload.files]
        assert out_path.name in attached_names

    @pytest.mark.asyncio
    async def test_oversize_skips_attachment_with_note(
        self,
        plugin: AudioTTSPlugin,
        simple_manifest,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from core.modalities import audio_common as ac

        oversize_bytes = b"\x00" * (ac.DISCORD_AUDIO_SIZE_LIMIT_BYTES + 16)
        out_path = tmp_path / "huge.mp3"
        out_path.write_bytes(oversize_bytes)

        run = Run(
            id="r",
            manifest_id=simple_manifest.id,
            slot_values={"text": "x"},
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
    async def test_voice_reference_appears_in_embed(
        self,
        plugin: AudioTTSPlugin,
        voiceclone_manifest,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        out_path = _write_tiny_wav(tmp_path / "out.wav")
        run = Run(
            id="r",
            manifest_id=voiceclone_manifest.id,
            slot_values={
                "text": "voice clone",
                "voice_reference": "ref-uploaded.wav",
            },
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
        assert "Voice reference" in names

    @pytest.mark.asyncio
    async def test_no_outputs_yields_no_files(
        self, plugin: AudioTTSPlugin, simple_manifest
    ) -> None:
        run = Run(id="r", manifest_id=simple_manifest.id)
        payload = await plugin.render_outputs(run, [])
        assert payload.files == []


class TestDefaultPostActions:
    def test_returns_manifest_actions_verbatim(
        self, plugin: AudioTTSPlugin, simple_manifest
    ) -> None:
        assert plugin.default_post_actions(simple_manifest) == list(
            simple_manifest.actions
        )
