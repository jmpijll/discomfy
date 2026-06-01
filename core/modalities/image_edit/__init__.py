"""Image-edit Plugin (ADR-0002).

The ``image_edit`` Modality takes between one and three source images
plus a natural-language edit instruction and produces a single
``image/png`` output. Different Manifests under this Modality wire
different numbers of source-image Slots; the Plugin is shared.
"""

from core.modalities.image_edit.plugin import ImageEditPlugin

__all__ = ["ImageEditPlugin"]
