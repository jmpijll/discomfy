"""Audio music Plugin (ADR-0002, ADR-0007).

Drives ACE-Step 1.5 manifests today; will host any future music or
SFX manifest the operator drops in (Stable Audio Open, MusicGen, etc.)
with no code change. ACE-Step is a single-pass diffusion model whose
sampling steps stream through the standard ``KSampler`` ``Progress``
events, so this Plugin uses a step-aware mapper instead of the
single-pass mapper used by Fish-Speech TTS.
"""

from core.modalities.audio_music.plugin import AudioMusicPlugin

__all__ = ["AudioMusicPlugin"]
