"""Typed WebSocket consumer for ComfyUI (ADR-0004).

Yields a stream of Pydantic ``ComfyEvent`` instances. Reconnects on
``WebSocketException`` with exponential backoff but emits a
``Reconnected`` event so a ``ProgressMapper`` can resync.

This module is the v3 replacement for ``core/comfyui/websocket.py``.

The WebSocket is opened eagerly on ``__aenter__`` because ComfyUI does
not buffer broadcast messages: any client that connects AFTER a Run
finishes never sees its ``execution_complete``. Establishing the
connection before ``queue_prompt`` is the caller's responsibility - the
``async with WSClient(...)`` block guarantees that.
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import AsyncIterator, Union

from pydantic import BaseModel, ConfigDict
import websockets
from websockets.exceptions import WebSocketException

logger = logging.getLogger(__name__)


class _EventBase(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class Executing(_EventBase):
    """ComfyUI started executing a node (node=None means run complete)."""

    type: str = "executing"
    prompt_id: str | None = None
    node: str | None = None


class Progress(_EventBase):
    """Step progress within a node (e.g. KSampler step)."""

    type: str = "progress"
    prompt_id: str | None = None
    node: str | None = None
    value: int = 0
    max: int = 0


class ExecutionComplete(_EventBase):
    """The prompt finished executing successfully."""

    type: str = "execution_complete"
    prompt_id: str


class ExecutionError(_EventBase):
    """The prompt failed."""

    type: str = "execution_error"
    prompt_id: str
    message: str = ""
    node_id: str | None = None
    node_type: str | None = None


class Executed(_EventBase):
    """A node finished and produced outputs."""

    type: str = "executed"
    prompt_id: str | None = None
    node: str | None = None
    output: dict = {}


class BinaryPreview(_EventBase):
    """A binary preview frame for a still-running sampler."""

    model_config = ConfigDict(extra="ignore", frozen=True, arbitrary_types_allowed=True)

    type: str = "binary_preview"
    prompt_id: str | None = None
    image_bytes: bytes = b""
    mime: str = "image/jpeg"


class Reconnected(_EventBase):
    """The WS connection was lost and re-established."""

    type: str = "reconnected"
    attempt: int = 1


ComfyEvent = Union[
    Executing,
    Progress,
    ExecutionComplete,
    ExecutionError,
    Executed,
    BinaryPreview,
    Reconnected,
]


class WSClient:
    """Async WebSocket consumer for ComfyUI.

    Yields typed events. Eagerly connects on ``__aenter__`` so the caller
    can ``queue_prompt`` afterwards with the guarantee that events
    addressed to ``client_id`` will reach this client. Reconnects on
    transient errors with exponential backoff.

    Typical use::

        async with WSClient("http://172.27.1.165:8188", client_id=cid) as ws:
            prompt_id = await http.queue_prompt(workflow)
            async for event in ws.events():
                if isinstance(event, ExecutionComplete) and event.prompt_id == prompt_id:
                    break
    """

    def __init__(
        self,
        base_url: str,
        *,
        client_id: str | None = None,
        recv_timeout: float = 30.0,
        max_backoff_seconds: float = 30.0,
        max_reconnect_attempts: int = 0,
        connect_timeout: float = 10.0,
    ) -> None:
        """
        Args:
            base_url: The ComfyUI base URL (http:// or https://). Scheme is
                rewritten to ws:// or wss:// for the WS connection.
            client_id: Persistent client id. Generated if absent. Must match
                the id passed to the HTTP client's ``queue_prompt`` so the
                server addresses events to us.
            recv_timeout: Per-message recv timeout. On timeout the loop
                iterates so cancellation is observed promptly.
            max_backoff_seconds: Cap on reconnect backoff.
            max_reconnect_attempts: 0 = retry forever.
            connect_timeout: Max time for the initial WS connect.
        """
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id or str(uuid.uuid4())
        self.recv_timeout = recv_timeout
        self.max_backoff_seconds = max_backoff_seconds
        self.max_reconnect_attempts = max_reconnect_attempts
        self.connect_timeout = connect_timeout
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._closed = asyncio.Event()
        self._reconnect_attempt = 0

    @property
    def ws_url(self) -> str:
        scheme = "wss" if self.base_url.startswith("https://") else "ws"
        host = self.base_url.split("://", 1)[1]
        return f"{scheme}://{host}/ws?clientId={self.client_id}"

    async def __aenter__(self) -> "WSClient":
        await self._connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _connect(self) -> None:
        """Open the WS. Raises on initial connect failure."""
        ws = await asyncio.wait_for(
            websockets.connect(self.ws_url), timeout=self.connect_timeout
        )
        self._ws = ws

    async def close(self) -> None:
        self._closed.set()
        if self._ws is not None and not self._ws.close_code:
            try:
                await self._ws.close()
            except Exception:
                pass
        self._ws = None

    async def events(self) -> AsyncIterator[ComfyEvent]:
        """Async-iterate over typed ComfyUI events.

        The iterator ends when ``close()`` is called or the consumer
        breaks. Transient disconnects trigger a reconnect + ``Reconnected``
        event; the iterator only ends permanently if reconnection budget
        is exhausted (``max_reconnect_attempts``) or ``close()`` is called.
        """
        backoff = 1.0
        while not self._closed.is_set():
            if self._ws is None:
                try:
                    await self._connect()
                except Exception as e:  # noqa: BLE001 - report any connect failure
                    self._reconnect_attempt += 1
                    if (
                        self.max_reconnect_attempts
                        and self._reconnect_attempt > self.max_reconnect_attempts
                    ):
                        logger.error(
                            "WSClient giving up after %d reconnect attempts: %s",
                            self._reconnect_attempt,
                            e,
                        )
                        return
                    wait = min(backoff, self.max_backoff_seconds)
                    logger.warning(
                        "WSClient reconnect failed (%s); retrying in %.1fs (attempt %d)",
                        e,
                        wait,
                        self._reconnect_attempt,
                    )
                    await asyncio.sleep(wait)
                    backoff = min(backoff * 2, self.max_backoff_seconds)
                    continue
                yield Reconnected(attempt=self._reconnect_attempt)
                self._reconnect_attempt = 0
                backoff = 1.0
            ws = self._ws
            assert ws is not None
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=self.recv_timeout)
            except asyncio.TimeoutError:
                continue
            except WebSocketException as e:
                logger.warning("WSClient WS error: %s; will reconnect", e)
                self._ws = None
                continue
            except asyncio.CancelledError:
                raise
            event = _parse_message(raw)
            if event is not None:
                yield event


def _parse_message(raw: bytes | str) -> ComfyEvent | None:
    """Parse a raw WS frame into a typed event.

    Binary frames are interpreted per the ComfyUI preview protocol:
    8 leading bytes are header (event_type uint32 BE, image_type uint32 BE),
    followed by image bytes. Unknown text-message types are dropped (None).
    """
    if isinstance(raw, (bytes, bytearray)):
        if len(raw) < 8:
            return None
        image_type_code = int.from_bytes(raw[4:8], "big")
        mime = "image/jpeg" if image_type_code == 1 else (
            "image/png" if image_type_code == 2 else "application/octet-stream"
        )
        return BinaryPreview(image_bytes=bytes(raw[8:]), mime=mime)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    msg_type = data.get("type")
    payload = data.get("data", {}) or {}
    if msg_type == "executing":
        return Executing(
            prompt_id=payload.get("prompt_id"),
            node=_to_str_or_none(payload.get("node")),
        )
    if msg_type == "progress":
        return Progress(
            prompt_id=payload.get("prompt_id"),
            node=_to_str_or_none(payload.get("node")),
            value=int(payload.get("value", 0) or 0),
            max=int(payload.get("max", 0) or 0),
        )
    if msg_type == "execution_complete":
        pid = payload.get("prompt_id")
        if not pid:
            return None
        return ExecutionComplete(prompt_id=pid)
    if msg_type in ("execution_error", "execution_interrupted"):
        pid = payload.get("prompt_id") or ""
        return ExecutionError(
            prompt_id=pid,
            message=str(
                payload.get("exception_message") or payload.get("message") or ""
            ),
            node_id=_to_str_or_none(payload.get("node_id")),
            node_type=payload.get("node_type"),
        )
    if msg_type == "executed":
        return Executed(
            prompt_id=payload.get("prompt_id"),
            node=_to_str_or_none(payload.get("node")),
            output=payload.get("output") or {},
        )
    return None


def _to_str_or_none(value) -> str | None:
    if value is None:
        return None
    return str(value)


__all__ = [
    "BinaryPreview",
    "ComfyEvent",
    "Executed",
    "Executing",
    "ExecutionComplete",
    "ExecutionError",
    "Progress",
    "Reconnected",
    "WSClient",
]
