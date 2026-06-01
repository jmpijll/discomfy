"""Typed view over ComfyUI's ``/object_info`` JSON (ADR-0004).

The Inventory is the single point of knowledge for "what's installed":
which UNETs / VAEs / CLIPs / LoRAs / checkpoints / upscale models the
server can load, which samplers / schedulers KSampler exposes, which
custom-node packs (python modules) are present.

Plugins consult the Inventory; the SetupBuilder resolves
``options_from`` slots from it; the bot validates each Manifest's
``requires`` block against it at registration time.

This module deliberately does not cache the inventory on import; the
caller refreshes it by re-fetching ``/object_info``. v3 refreshes on
each bot start; the View layer can refresh on-demand to pick up
newly installed LoRAs without a restart (ADR-0003).
"""

from __future__ import annotations

from typing import Any, Iterable

from core.manifest.schema import Requires


class Inventory:
    """Typed wrapper around a raw ``/object_info`` dict.

    Pass a JSON dict (e.g. from :py:meth:`core.comfyui.v3.http.ComfyHTTPClient.get_object_info`)
    to the constructor; query the helpers. The Inventory does not mutate
    the underlying dict.
    """

    def __init__(self, object_info: dict[str, Any]) -> None:
        if not isinstance(object_info, dict):
            raise TypeError(
                f"Inventory requires an object_info dict, got {type(object_info).__name__}"
            )
        self._raw = object_info

    @property
    def raw(self) -> dict[str, Any]:
        """The underlying ``/object_info`` dict. Treat as read-only."""
        return self._raw

    def has_node(self, node_name: str) -> bool:
        """True if the server registers ``node_name`` as a node class."""
        return node_name in self._raw

    def python_module_for(self, node_name: str) -> str | None:
        """Return the ``python_module`` ComfyUI records for ``node_name``."""
        node = self._raw.get(node_name)
        if not isinstance(node, dict):
            return None
        return node.get("python_module")

    def has_pack(self, python_module: str) -> bool:
        """True if any registered node lives under ``python_module``.

        ``python_module`` is ComfyUI's identifier for a Pack (e.g.
        ``custom_nodes.ComfyUI-WanVideoWrapper``). Core nodes live under
        ``nodes`` or ``comfy_extras.*``; third-party Packs live under
        ``custom_nodes.<name>``.
        """
        for node in self._raw.values():
            if isinstance(node, dict) and node.get("python_module") == python_module:
                return True
        return False

    def unets(self) -> list[str]:
        """All UNET filenames the server can load."""
        return self._node_option_list("UNETLoader", "unet_name")

    def vaes(self) -> list[str]:
        """All VAE filenames the server can load."""
        return self._node_option_list("VAELoader", "vae_name")

    def clips(self) -> list[str]:
        """All text-encoder filenames the server can load."""
        return self._node_option_list("CLIPLoader", "clip_name")

    def loras(self) -> list[str]:
        """All LoRA filenames the server can load.

        Reads from ``LoraLoader.lora_name`` if present, falling back to
        ``LoraLoaderModelOnly.lora_name``. Both nodes share the same
        underlying folder, but a stripped server may expose only one.
        """
        for node in ("LoraLoader", "LoraLoaderModelOnly"):
            opts = self._node_option_list(node, "lora_name")
            if opts:
                return opts
        return []

    def checkpoints(self) -> list[str]:
        """All ``*.safetensors`` checkpoints the server can load."""
        return self._node_option_list("CheckpointLoaderSimple", "ckpt_name")

    def upscale_models(self) -> list[str]:
        """All upscale models the server can load."""
        return self._node_option_list("UpscaleModelLoader", "model_name")

    def samplers(self) -> list[str]:
        """Sampler names KSampler exposes."""
        return self._node_option_list("KSampler", "sampler_name")

    def schedulers(self) -> list[str]:
        """Scheduler names KSampler exposes."""
        return self._node_option_list("KSampler", "scheduler")

    def options_for(self, source: str) -> list[str]:
        """Resolve a manifest ``options_from`` source string to a list.

        Supported sources match ADR-0003:

        - ``comfyui.unets``
        - ``comfyui.vaes``
        - ``comfyui.clips``
        - ``comfyui.loras``
        - ``comfyui.checkpoints``
        - ``comfyui.upscale_models``
        - ``comfyui.samplers``
        - ``comfyui.schedulers``

        Unknown sources return an empty list and the caller may decide
        whether that's a registration failure or a tolerable empty UI.
        """
        mapping = {
            "comfyui.unets": self.unets,
            "comfyui.vaes": self.vaes,
            "comfyui.clips": self.clips,
            "comfyui.loras": self.loras,
            "comfyui.checkpoints": self.checkpoints,
            "comfyui.upscale_models": self.upscale_models,
            "comfyui.samplers": self.samplers,
            "comfyui.schedulers": self.schedulers,
        }
        fn = mapping.get(source)
        return fn() if fn else []

    def validate_requires(self, requires: Requires) -> list[str]:
        """Return a list of human-readable messages for missing dependencies.

        Empty list = the Manifest's ``requires`` block is fully satisfied.
        Each message names the missing item by category so the operator
        can fix the install without guessing.
        """
        problems: list[str] = []
        problems.extend(
            self._missing("UNET", requires.unets, self.unets())
        )
        problems.extend(
            self._missing("VAE", requires.vaes, self.vaes())
        )
        problems.extend(
            self._missing("CLIP", requires.clips, self.clips())
        )
        problems.extend(
            self._missing("LoRA", requires.loras, self.loras())
        )
        problems.extend(
            self._missing("checkpoint", requires.checkpoints, self.checkpoints())
        )
        problems.extend(
            self._missing(
                "upscale model", requires.upscale_models, self.upscale_models()
            )
        )
        for pack in requires.packs:
            if not self.has_pack(pack):
                problems.append(f"missing Pack (python_module): {pack}")
        return problems

    def _node_option_list(self, node: str, field: str) -> list[str]:
        node_def = self._raw.get(node)
        if not isinstance(node_def, dict):
            return []
        inputs = node_def.get("input", {})
        for section in ("required", "optional"):
            spec = inputs.get(section, {})
            if not isinstance(spec, dict):
                continue
            entry = spec.get(field)
            if isinstance(entry, list) and entry and isinstance(entry[0], list):
                return [str(o) for o in entry[0]]
        return []

    @staticmethod
    def _missing(
        category: str,
        wanted: Iterable[str],
        available: Iterable[str],
    ) -> list[str]:
        available_set = set(available)
        return [
            f"missing {category}: {name}"
            for name in wanted
            if name not in available_set
        ]


__all__ = ["Inventory"]
