"""Image upscale Plugin (ADR-0002).

The ``image_upscale`` Modality renders ``image/png`` outputs just like
``image_t2i`` but exposes different Slots (a source image + a scale
factor, no prompt) and offers NO default post-Run Actions: chaining
"Upscale" onto an already-upscaled output is an infinite-loop UX trap.
"""

from core.modalities.image_upscale.plugin import ImageUpscalePlugin

__all__ = ["ImageUpscalePlugin"]
