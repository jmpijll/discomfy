"""Image text-to-image Plugin (ADR-0002).

Exactly one Plugin per Modality. This one renders ``image/png`` outputs,
maps two-pass KSampler progress to a single 0-100 stream, and offers
Upscale / Animate / Edit as default post-Run Actions (each manifest can
override).
"""

from core.modalities.image_t2i.plugin import ImageT2IPlugin

__all__ = ["ImageT2IPlugin"]
