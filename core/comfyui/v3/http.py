"""Thin aiohttp wrapper around ComfyUI's REST surface (ADR-0004).

One method per endpoint. No retries inside this layer - retries are a
Run-level concern (ADR-0006). Connection pooling via a single
``aiohttp.ClientSession`` per client instance; lifecycle owned by the
caller via the ``async with`` protocol.

This module is the v3 replacement for ``core/comfyui/client.py``. It
deliberately does NOT depend on anything from the v2 package so that
deletion in Slice 9 is mechanical.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class ComfyHTTPError(Exception):
    """ComfyUI HTTP call failed.

    Attributes:
        status_code: HTTP status code if the response made it back.
        body: Response body (truncated) for diagnosis.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        body: str | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class ComfyHTTPClient:
    """Async client for the ComfyUI REST API.

    Use as an async context manager:

        async with ComfyHTTPClient("http://172.27.1.165:8188") as http:
            prompt_id = await http.queue_prompt(workflow)
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 300.0,
        client_id: str | None = None,
        connector_limit: int = 10,
        connector_limit_per_host: int = 5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client_id = client_id or str(uuid.uuid4())
        self._connector_limit = connector_limit
        self._connector_limit_per_host = connector_limit_per_host
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "ComfyHTTPClient":
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def open(self) -> None:
        """Open the underlying aiohttp session. Idempotent."""
        if self._session is not None and not self._session.closed:
            return
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            connector=aiohttp.TCPConnector(
                limit=self._connector_limit,
                limit_per_host=self._connector_limit_per_host,
            ),
        )

    async def close(self) -> None:
        """Close the underlying aiohttp session. Idempotent."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    def _require_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise ComfyHTTPError(
                "ComfyHTTPClient session is not open; use `async with` or call open()"
            )
        return self._session

    async def queue_prompt(self, workflow: dict[str, Any]) -> str:
        """POST /prompt and return the ComfyUI-assigned prompt_id."""
        payload = {"prompt": workflow, "client_id": self.client_id}
        url = f"{self.base_url}/prompt"
        session = self._require_session()
        try:
            async with session.post(url, json=payload) as resp:
                body = await resp.text()
                if resp.status != 200:
                    raise ComfyHTTPError(
                        f"queue_prompt failed: HTTP {resp.status}",
                        status_code=resp.status,
                        body=_truncate(body),
                    )
                try:
                    data = json.loads(body)
                except json.JSONDecodeError as e:
                    raise ComfyHTTPError(
                        f"queue_prompt returned invalid JSON: {e}",
                        body=_truncate(body),
                    ) from e
                prompt_id = data.get("prompt_id")
                if not prompt_id:
                    raise ComfyHTTPError(
                        f"queue_prompt response missing prompt_id: {data}",
                        body=_truncate(body),
                    )
                return prompt_id
        except aiohttp.ClientError as e:
            raise ComfyHTTPError(f"queue_prompt network error: {e}") from e

    async def get_history(self, prompt_id: str) -> dict[str, Any]:
        """GET /history/{prompt_id}. Returns the raw history dict."""
        url = f"{self.base_url}/history/{prompt_id}"
        return await self._get_json(url, "get_history")

    async def get_view(
        self,
        filename: str,
        *,
        type: str = "output",
        subfolder: str = "",
    ) -> bytes:
        """GET /view?filename=...&type=...&subfolder=... -> raw file bytes."""
        params = {"filename": filename, "type": type, "subfolder": subfolder}
        url = f"{self.base_url}/view"
        session = self._require_session()
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise ComfyHTTPError(
                        f"get_view({filename}) failed: HTTP {resp.status}",
                        status_code=resp.status,
                        body=_truncate(body),
                    )
                return await resp.read()
        except aiohttp.ClientError as e:
            raise ComfyHTTPError(f"get_view network error: {e}") from e

    async def get_object_info(self) -> dict[str, Any]:
        """GET /object_info. Returns the full node catalog (~6 MB JSON)."""
        url = f"{self.base_url}/object_info"
        return await self._get_json(url, "get_object_info")

    async def get_system_stats(self) -> dict[str, Any]:
        """GET /system_stats. Returns RAM/VRAM/device info."""
        url = f"{self.base_url}/system_stats"
        return await self._get_json(url, "get_system_stats")

    async def get_queue(self) -> dict[str, Any]:
        """GET /queue. Returns running + pending queue contents."""
        url = f"{self.base_url}/queue"
        return await self._get_json(url, "get_queue")

    async def upload_image(
        self,
        filename: str,
        data: bytes,
        *,
        type: str = "input",
        subfolder: str = "",
        overwrite: bool = True,
        content_type: str = "image/png",
    ) -> dict[str, Any]:
        """POST /upload/image. Returns ComfyUI's upload response dict."""
        return await self._upload(
            endpoint="upload/image",
            field_name="image",
            filename=filename,
            data=data,
            content_type=content_type,
            extra={
                "type": type,
                "subfolder": subfolder,
                "overwrite": "true" if overwrite else "false",
            },
        )

    async def upload_audio(
        self,
        filename: str,
        data: bytes,
        *,
        type: str = "input",
        subfolder: str = "",
        overwrite: bool = True,
        content_type: str = "audio/mpeg",
    ) -> dict[str, Any]:
        """POST /upload/audio (alias of /upload/image for audio mimes)."""
        return await self._upload(
            endpoint="upload/image",
            field_name="image",
            filename=filename,
            data=data,
            content_type=content_type,
            extra={
                "type": type,
                "subfolder": subfolder,
                "overwrite": "true" if overwrite else "false",
            },
        )

    async def _get_json(self, url: str, op: str) -> dict[str, Any]:
        session = self._require_session()
        try:
            async with session.get(url) as resp:
                body = await resp.text()
                if resp.status != 200:
                    raise ComfyHTTPError(
                        f"{op} failed: HTTP {resp.status}",
                        status_code=resp.status,
                        body=_truncate(body),
                    )
                try:
                    return json.loads(body)
                except json.JSONDecodeError as e:
                    raise ComfyHTTPError(
                        f"{op} returned invalid JSON: {e}",
                        body=_truncate(body),
                    ) from e
        except aiohttp.ClientError as e:
            raise ComfyHTTPError(f"{op} network error: {e}") from e

    async def _upload(
        self,
        *,
        endpoint: str,
        field_name: str,
        filename: str,
        data: bytes,
        content_type: str,
        extra: dict[str, str],
    ) -> dict[str, Any]:
        session = self._require_session()
        form = aiohttp.FormData()
        form.add_field(
            field_name, data, filename=filename, content_type=content_type
        )
        for k, v in extra.items():
            form.add_field(k, v)
        url = f"{self.base_url}/{endpoint}"
        try:
            async with session.post(url, data=form) as resp:
                body = await resp.text()
                if resp.status != 200:
                    raise ComfyHTTPError(
                        f"upload({filename}) failed: HTTP {resp.status}",
                        status_code=resp.status,
                        body=_truncate(body),
                    )
                try:
                    return json.loads(body)
                except json.JSONDecodeError as e:
                    raise ComfyHTTPError(
                        f"upload returned invalid JSON: {e}",
                        body=_truncate(body),
                    ) from e
        except aiohttp.ClientError as e:
            raise ComfyHTTPError(f"upload network error: {e}") from e


def _truncate(s: str, limit: int = 512) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + f"...(+{len(s) - limit} chars)"


__all__ = ["ComfyHTTPClient", "ComfyHTTPError"]
