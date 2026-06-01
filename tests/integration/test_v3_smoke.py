"""Live ComfyUI integration smoke for the v3 tracer-bullet manifest.

Marked ``@pytest.mark.integration`` and gated on the
``DISCOMFY_INTEGRATION=1`` environment variable so CI stays fast and
deterministic. Run locally:

    DISCOMFY_INTEGRATION=1 pytest tests/integration/test_v3_smoke.py -v

The test imports :func:`scripts.v3_smoke.run_smoke` and runs the whole
v3 path end-to-end against ComfyUI at ``COMFYUI_URL`` (default
``http://172.27.1.165:8188``). Success: a PNG > 1 KB written to disk
within the test's per-test timeout.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.v3_smoke import run_smoke  # noqa: E402

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.environ.get("DISCOMFY_INTEGRATION") != "1",
        reason="set DISCOMFY_INTEGRATION=1 to run live ComfyUI smoke",
    ),
]


COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://172.27.1.165:8188")


@pytest.mark.asyncio
async def test_qwen_image_2512_end_to_end(tmp_path: Path) -> None:
    result = await run_smoke(
        manifest_id="qwen_image_2512",
        slot_overrides={
            "prompt": (
                "an integration-test photograph of a single red panda "
                "eating bamboo, soft window light"
            ),
            "seed": "42",
        },
        base_url=COMFYUI_URL,
        manifests_dir=REPO_ROOT / "workflows" / "manifests",
        output_dir=tmp_path,
        timeout_seconds=600,
    )
    assert result.prompt_id
    assert result.outputs, "expected at least one Output"
    image = result.outputs[0]
    assert image.media == "image/png"
    assert image.path.exists()
    assert image.size_bytes > 1024, "expected a real PNG > 1KB"
    assert result.latency_seconds > 0
