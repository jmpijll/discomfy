"""Modality registry (ADR-0002).

Maps each :class:`~core.manifest.roles.Modality` enum value to exactly
one :class:`~core.modalities.base.ModalityPlugin` instance. Code never
branches on model name; the bot looks up by Modality and dispatches.
"""

from __future__ import annotations

from core.manifest.roles import Modality
from core.modalities.base import ModalityPlugin


class ModalityRegistry:
    """One Plugin per Modality. Re-registration replaces the prior Plugin."""

    def __init__(self) -> None:
        self._plugins: dict[Modality, ModalityPlugin] = {}

    def register(self, plugin: ModalityPlugin) -> None:
        """Bind ``plugin.modality`` to ``plugin``."""
        if plugin.modality in self._plugins and self._plugins[plugin.modality] is not plugin:
            # Replacing is allowed (for tests / hot-reload), but log noisily
            # so accidental shadowing is visible at startup.
            import logging

            logging.getLogger(__name__).warning(
                "Replacing existing Plugin for modality %s", plugin.modality.value
            )
        self._plugins[plugin.modality] = plugin

    def get(self, modality: Modality) -> ModalityPlugin:
        try:
            return self._plugins[modality]
        except KeyError as e:
            raise KeyError(
                f"No Plugin registered for modality {modality.value}"
            ) from e

    def __contains__(self, modality: Modality) -> bool:
        return modality in self._plugins

    def modalities(self) -> list[Modality]:
        return list(self._plugins.keys())


default_registry = ModalityRegistry()


def _wire_default_plugins() -> None:
    """Register every Plugin that ships in v3.

    Imported here to avoid import cycles between Plugin modules and the
    registry. Slice 1 ships only ``image_t2i``; later slices append to
    this function.
    """
    from core.modalities.image_t2i.plugin import ImageT2IPlugin
    from core.modalities.image_upscale.plugin import ImageUpscalePlugin

    default_registry.register(ImageT2IPlugin())
    default_registry.register(ImageUpscalePlugin())


_wire_default_plugins()


__all__ = ["ModalityRegistry", "default_registry"]
