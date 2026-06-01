"""Tests covering the two audio_tts manifests authored in Slice 7.

These guard against accidental schema regressions: that the YAML on
disk parses, that key facts (modality, output mime, voice-clone slot
shape) are preserved, and that the registry routes the modality to
the AudioTTSPlugin.
"""

from __future__ import annotations

import pytest

from core.manifest import load_manifest
from core.manifest.roles import Modality, Role
from core.manifest.schema import SlotType
from core.modalities import default_registry
from core.modalities.audio_tts.plugin import AudioTTSPlugin


@pytest.fixture
def simple_manifest():
    return load_manifest("workflows/manifests/audio_tts_fish_simple.yaml")


@pytest.fixture
def voiceclone_manifest():
    return load_manifest("workflows/manifests/audio_tts_fish_voiceclone.yaml")


class TestSimpleManifest:
    def test_modality_is_audio_tts(self, simple_manifest) -> None:
        assert simple_manifest.modality == Modality.AUDIO_TTS

    def test_output_is_mp3(self, simple_manifest) -> None:
        assert len(simple_manifest.outputs) == 1
        assert simple_manifest.outputs[0].role == Role.OUTPUT_AUDIO
        assert simple_manifest.outputs[0].media == "audio/mpeg"

    def test_text_slot_required(self, simple_manifest) -> None:
        slots = simple_manifest.slots_by_name()
        assert "text" in slots
        text_slot = slots["text"]
        assert text_slot.type == SlotType.TEXT
        assert text_slot.ui.required is True

    def test_seed_slot_present(self, simple_manifest) -> None:
        slots = simple_manifest.slots_by_name()
        assert "seed" in slots
        assert slots["seed"].type == SlotType.SEED

    def test_requires_fish_pack(self, simple_manifest) -> None:
        assert "custom_nodes.ComfyUI-FishAudioS2" in simple_manifest.requires.packs

    def test_no_actions(self, simple_manifest) -> None:
        assert simple_manifest.actions == []


class TestVoiceCloneManifest:
    def test_modality_is_audio_tts(self, voiceclone_manifest) -> None:
        assert voiceclone_manifest.modality == Modality.AUDIO_TTS

    def test_voice_reference_slot_audio_required(self, voiceclone_manifest) -> None:
        slots = voiceclone_manifest.slots_by_name()
        assert "voice_reference" in slots
        slot = slots["voice_reference"]
        assert slot.type == SlotType.AUDIO
        assert slot.role == Role.REFERENCE_AUDIO
        assert slot.ui.required is True
        assert slot.ui.attachment_position == 1

    def test_voice_reference_accepts_listed(self, voiceclone_manifest) -> None:
        slots = voiceclone_manifest.slots_by_name()
        accepts = slots["voice_reference"].validation.accepts
        assert accepts is not None
        assert "audio/wav" in accepts
        assert "audio/mpeg" in accepts

    def test_text_slot_is_long_text(self, voiceclone_manifest) -> None:
        slots = voiceclone_manifest.slots_by_name()
        from core.manifest.schema import UIHint

        assert slots["text"].ui.hint == UIHint.LONG_TEXT

    def test_output_is_mp3(self, voiceclone_manifest) -> None:
        assert voiceclone_manifest.outputs[0].media == "audio/mpeg"

    def test_requires_fish_pack(self, voiceclone_manifest) -> None:
        assert (
            "custom_nodes.ComfyUI-FishAudioS2"
            in voiceclone_manifest.requires.packs
        )


class TestRegistryWiring:
    def test_audio_tts_modality_resolves_to_plugin(
        self, simple_manifest
    ) -> None:
        plugin = default_registry.get(simple_manifest.modality)
        assert isinstance(plugin, AudioTTSPlugin)
        assert plugin.modality == Modality.AUDIO_TTS

    def test_voiceclone_modality_resolves_to_plugin(
        self, voiceclone_manifest
    ) -> None:
        plugin = default_registry.get(voiceclone_manifest.modality)
        assert isinstance(plugin, AudioTTSPlugin)
