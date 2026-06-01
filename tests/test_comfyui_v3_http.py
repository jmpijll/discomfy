"""Tests for core.comfyui.v3.http.ComfyHTTPClient.

aiohttp is mocked at the ``ClientSession`` boundary; no live HTTP. The
goal is to assert that each method posts to the right endpoint, sends
the right body shape, and turns ComfyUI responses (or errors) into
typed results / ``ComfyHTTPError``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import pytest

from core.comfyui.v3.http import ComfyHTTPClient, ComfyHTTPError


class _FakeResponse:
    def __init__(
        self, *, status: int = 200, text: str = "{}", json_data: Any = None
    ) -> None:
        self.status = status
        self._text = text
        self._json = json_data

    async def text(self) -> str:
        return self._text

    async def read(self) -> bytes:
        return self._text.encode("utf-8")

    async def json(self) -> Any:
        return self._json


class _FakeSession:
    def __init__(self) -> None:
        self.closed = False
        self.calls: list[dict[str, Any]] = []
        self._responses: dict[tuple[str, str], _FakeResponse] = {}

    def set_response(self, method: str, url: str, response: _FakeResponse) -> None:
        self._responses[(method.upper(), url)] = response

    def _resolve(self, method: str, url: str) -> _FakeResponse:
        try:
            return self._responses[(method.upper(), url)]
        except KeyError as e:
            raise AssertionError(f"unexpected {method} {url}") from e

    @asynccontextmanager
    async def post(self, url: str, *, json: Any = None, data: Any = None):
        self.calls.append({"method": "POST", "url": url, "json": json, "data": data})
        yield self._resolve("POST", url)

    @asynccontextmanager
    async def get(self, url: str, *, params: Any = None):
        self.calls.append({"method": "GET", "url": url, "params": params})
        yield self._resolve("GET", url)

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_session() -> _FakeSession:
    return _FakeSession()


@pytest.fixture
def client(fake_session: _FakeSession) -> ComfyHTTPClient:
    c = ComfyHTTPClient("http://example.com:8188/", client_id="test-cid")
    c._session = fake_session  # type: ignore[attr-defined]
    return c


@pytest.mark.asyncio
async def test_queue_prompt_posts_and_returns_id(
    client: ComfyHTTPClient, fake_session: _FakeSession
) -> None:
    fake_session.set_response(
        "POST",
        "http://example.com:8188/prompt",
        _FakeResponse(text='{"prompt_id": "abc-123"}'),
    )
    pid = await client.queue_prompt({"workflow": "x"})
    assert pid == "abc-123"
    assert fake_session.calls[0]["json"] == {
        "prompt": {"workflow": "x"},
        "client_id": "test-cid",
    }


@pytest.mark.asyncio
async def test_queue_prompt_non_200_raises_http_error(
    client: ComfyHTTPClient, fake_session: _FakeSession
) -> None:
    fake_session.set_response(
        "POST",
        "http://example.com:8188/prompt",
        _FakeResponse(status=500, text="server exploded"),
    )
    with pytest.raises(ComfyHTTPError) as exc:
        await client.queue_prompt({})
    assert exc.value.status_code == 500
    assert "server exploded" in (exc.value.body or "")


@pytest.mark.asyncio
async def test_queue_prompt_missing_id_raises(
    client: ComfyHTTPClient, fake_session: _FakeSession
) -> None:
    fake_session.set_response(
        "POST",
        "http://example.com:8188/prompt",
        _FakeResponse(text='{"oops": true}'),
    )
    with pytest.raises(ComfyHTTPError) as exc:
        await client.queue_prompt({})
    assert "prompt_id" in str(exc.value)


@pytest.mark.asyncio
async def test_get_history(client: ComfyHTTPClient, fake_session: _FakeSession) -> None:
    fake_session.set_response(
        "GET",
        "http://example.com:8188/history/abc-123",
        _FakeResponse(text='{"abc-123": {"outputs": {}}}'),
    )
    out = await client.get_history("abc-123")
    assert "abc-123" in out


@pytest.mark.asyncio
async def test_get_view_returns_bytes(
    client: ComfyHTTPClient, fake_session: _FakeSession
) -> None:
    fake_session.set_response(
        "GET", "http://example.com:8188/view", _FakeResponse(text="binary-pixels")
    )
    data = await client.get_view("foo.png")
    assert data == b"binary-pixels"
    assert fake_session.calls[-1]["params"] == {
        "filename": "foo.png",
        "type": "output",
        "subfolder": "",
    }


@pytest.mark.asyncio
async def test_get_object_info(
    client: ComfyHTTPClient, fake_session: _FakeSession
) -> None:
    fake_session.set_response(
        "GET",
        "http://example.com:8188/object_info",
        _FakeResponse(text='{"KSampler": {}}'),
    )
    out = await client.get_object_info()
    assert "KSampler" in out


@pytest.mark.asyncio
async def test_session_required(fake_session: _FakeSession) -> None:
    client = ComfyHTTPClient("http://example.com:8188/")
    with pytest.raises(ComfyHTTPError) as exc:
        await client.queue_prompt({})
    assert "session is not open" in str(exc.value)
