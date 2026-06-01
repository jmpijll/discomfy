"""DisComfy v3 ComfyUI client layer.

Thin, typed wrapper over ComfyUI's HTTP + WebSocket surface (ADR-0004).

Three modules and nothing else:

- :mod:`core.comfyui.v3.http` - aiohttp wrapper around the REST endpoints
  (queue, history, view, upload, system_stats, object_info).
- :mod:`core.comfyui.v3.ws` - typed WebSocket consumer that yields
  Pydantic ``Event`` objects.
- :mod:`core.comfyui.v3.capability` - typed view of ``/object_info`` that
  Plugins query for installed models / packs / samplers.

Coexists with the v2 ``core/comfyui/`` package; both are importable.
v3 code MUST import from ``core.comfyui.v3``; v2 code paths remain
untouched until Slice 9.
"""

from core.comfyui.v3.capability import Inventory
from core.comfyui.v3.http import ComfyHTTPClient, ComfyHTTPError
from core.comfyui.v3.ws import (
    BinaryPreview,
    ComfyEvent,
    Executed,
    Executing,
    ExecutionComplete,
    ExecutionError,
    Progress,
    Reconnected,
    WSClient,
)

__all__ = [
    "BinaryPreview",
    "ComfyEvent",
    "ComfyHTTPClient",
    "ComfyHTTPError",
    "Executed",
    "Executing",
    "ExecutionComplete",
    "ExecutionError",
    "Inventory",
    "Progress",
    "Reconnected",
    "WSClient",
]
