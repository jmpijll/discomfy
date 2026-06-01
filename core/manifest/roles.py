"""Closed enums for Manifest Modalities and Roles.

`CONTEXT.md` defines these terms; this module is the single source of
truth for the legal values. Adding a new Modality or Role is
intentionally a code change because the Plugin layer needs to know what
each one means semantically.
"""

from __future__ import annotations

from enum import Enum


class Modality(str, Enum):
    """The output kind a Workflow produces.

    See ADR-0002. There is exactly one Plugin per Modality.
    """

    IMAGE_T2I = "image_t2i"
    IMAGE_EDIT = "image_edit"
    IMAGE_UPSCALE = "image_upscale"
    VIDEO = "video"
    AUDIO_TTS = "audio_tts"
    AUDIO_MUSIC = "audio_music"


class Role(str, Enum):
    """Logical role a Slot plays in a Workflow.

    Plugins read manifests by Role, never by node id. Adding a new Role
    requires teaching at least one Plugin what it means.
    """

    PROMPT_POSITIVE = "prompt_positive"
    PROMPT_NEGATIVE = "prompt_negative"
    SEED = "seed"
    LATENT_SIZE = "latent_size"
    SAMPLER_NAME = "sampler_name"
    SCHEDULER = "scheduler"
    STEPS = "steps"
    CFG = "cfg"
    DENOISE = "denoise"
    MODEL = "model"
    MODEL_HIGH = "model_high"
    MODEL_LOW = "model_low"
    VAE = "vae"
    CLIP = "clip"
    LORA = "lora"
    LORA_STRENGTH = "lora_strength"
    SOURCE_IMAGE = "source_image"
    SOURCE_IMAGE_2 = "source_image_2"
    SOURCE_IMAGE_3 = "source_image_3"
    INIT_IMAGE = "init_image"
    REFERENCE_AUDIO = "reference_audio"
    DURATION_SECONDS = "duration_seconds"
    DYPE_EXPONENT = "dype_exponent"
    BATCH_SIZE = "batch_size"
    OUTPUT_IMAGE = "output_image"
    OUTPUT_VIDEO = "output_video"
    OUTPUT_AUDIO = "output_audio"


__all__ = ["Modality", "Role"]
