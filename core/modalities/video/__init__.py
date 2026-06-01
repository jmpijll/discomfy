"""Video Modality Plugin package (ADR-0002).

Exposes :class:`VideoPlugin`; the Modality Registry wires it up.
"""

from __future__ import annotations

from core.modalities.video.plugin import VideoPlugin

__all__ = ["VideoPlugin"]
