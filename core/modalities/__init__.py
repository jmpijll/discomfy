"""Modality plugins for DisComfy v3 (ADR-0002).

Each :class:`~core.manifest.roles.Modality` maps to exactly one Plugin
implementing the :class:`~core.modalities.base.ModalityPlugin` Protocol.
Plugins know about output media, validation rules, Discord rendering,
progress mapping, and default post-Run actions. They do not know about
specific models - that is what Manifests are for.

The :mod:`core.modalities.registry` module exposes a global
``ModalityRegistry`` instance so the bot can dispatch by Modality.
"""

from core.modalities.audio_tts.plugin import AudioTTSPlugin
from core.modalities.base import (
    ModalityPlugin,
    ProgressMapper,
    SlotValueValidationError,
    SlotValues,
)
from core.modalities.image_t2i.plugin import ImageT2IPlugin
from core.modalities.image_upscale.plugin import ImageUpscalePlugin
from core.modalities.registry import ModalityRegistry, default_registry

__all__ = [
    "AudioTTSPlugin",
    "ImageT2IPlugin",
    "ImageUpscalePlugin",
    "ModalityPlugin",
    "ModalityRegistry",
    "ProgressMapper",
    "SlotValueValidationError",
    "SlotValues",
    "default_registry",
]
