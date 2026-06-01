"""Tests for core.comfyui.v3.ws message parsing.

The live WS connection is exercised by the integration smoke; this unit
test pins the message-parsing seam so a ComfyUI WS schema drift fails
fast in CI without needing the server.
"""

from __future__ import annotations

import json

from core.comfyui.v3.ws import (
    BinaryPreview,
    Executed,
    Executing,
    ExecutionComplete,
    ExecutionError,
    Progress,
    _parse_message,
)


def _msg(type_: str, **data) -> str:
    return json.dumps({"type": type_, "data": data})


class TestParseTextMessages:
    def test_executing_with_node(self) -> None:
        ev = _parse_message(_msg("executing", node=18, prompt_id="abc"))
        assert isinstance(ev, Executing)
        assert ev.node == "18"
        assert ev.prompt_id == "abc"

    def test_executing_with_null_node(self) -> None:
        ev = _parse_message(_msg("executing", node=None, prompt_id="abc"))
        assert isinstance(ev, Executing)
        assert ev.node is None

    def test_progress(self) -> None:
        ev = _parse_message(_msg("progress", value=3, max=8, node="8", prompt_id="x"))
        assert isinstance(ev, Progress)
        assert ev.value == 3 and ev.max == 8
        assert ev.node == "8"

    def test_execution_complete(self) -> None:
        ev = _parse_message(_msg("execution_complete", prompt_id="abc"))
        assert isinstance(ev, ExecutionComplete)
        assert ev.prompt_id == "abc"

    def test_execution_complete_without_id_is_dropped(self) -> None:
        assert _parse_message(_msg("execution_complete")) is None

    def test_execution_error(self) -> None:
        ev = _parse_message(
            _msg(
                "execution_error",
                prompt_id="abc",
                exception_message="boom",
                node_id=13,
                node_type="SaveImage",
            )
        )
        assert isinstance(ev, ExecutionError)
        assert ev.message == "boom"
        assert ev.node_id == "13"
        assert ev.node_type == "SaveImage"

    def test_executed_with_output(self) -> None:
        ev = _parse_message(
            _msg("executed", node=13, prompt_id="abc", output={"images": [{"filename": "x.png"}]})
        )
        assert isinstance(ev, Executed)
        assert ev.output["images"][0]["filename"] == "x.png"

    def test_unknown_type_dropped(self) -> None:
        assert _parse_message(_msg("crystools.monitor", value=0.5)) is None

    def test_invalid_json_dropped(self) -> None:
        assert _parse_message("not json") is None


class TestParseBinaryMessages:
    def test_jpeg_preview(self) -> None:
        header = (1).to_bytes(4, "big") + (1).to_bytes(4, "big")
        ev = _parse_message(header + b"jpeg-bytes")
        assert isinstance(ev, BinaryPreview)
        assert ev.mime == "image/jpeg"
        assert ev.image_bytes == b"jpeg-bytes"

    def test_png_preview(self) -> None:
        header = (1).to_bytes(4, "big") + (2).to_bytes(4, "big")
        ev = _parse_message(header + b"png-bytes")
        assert isinstance(ev, BinaryPreview)
        assert ev.mime == "image/png"

    def test_short_binary_dropped(self) -> None:
        assert _parse_message(b"\x00\x00") is None
