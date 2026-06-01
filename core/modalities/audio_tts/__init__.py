"""Audio text-to-speech Plugin (ADR-0002, ADR-0007).

Drives Fish-Speech S2 manifests today; will host any future TTS
manifest the operator drops in (e.g. KugelAudio, Chatterbox) with no
code change. Reference-audio uploads are supported via the AUDIO Slot
type so VoiceClone manifests work end-to-end.
"""

from core.modalities.audio_tts.plugin import AudioTTSPlugin

__all__ = ["AudioTTSPlugin"]
