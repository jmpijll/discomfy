"""DisComfy v3 end-to-end smoke harness against a live ComfyUI.

Usage::

    python scripts/v3_smoke.py \
        --manifest qwen_image_2512 \
        --slot prompt="a single red panda eating bamboo"

    # i2v with an attachment - the harness uploads the file and writes the
    # ComfyUI-side filename into the slot value before applying:
    python scripts/v3_smoke.py \
        --manifest wan22_i2v \
        --slot prompt="camera pans right" \
        --slot init_image=output/v3_smoke/abc/img.png \
        --slot frame_count=17

Loads the manifest registry from ``workflows/manifests/``, validates the
named manifest's ``requires`` against the live ``/object_info``, uploads
any IMAGE slot whose value is a local file path (via ``/upload/image``)
and rewrites the value to the server-side filename, applies user-supplied
slot overrides via the v3 ``apply_slots``, queues the workflow with the
v3 ``ComfyHTTPClient``, follows progress with the v3 ``WSClient`` until
``ExecutionComplete``, downloads every Output the manifest declares
(images, videos via ``VHS_VideoCombine``'s legacy ``gifs`` bucket, or
audio), saves them to ``output/v3_smoke/<prompt_id>/`` and reports prompt
id, output paths, sizes, and wall-clock latency.

This script is the validation gate for every v3 slice. It runs without
Discord, exits 0 on success, non-zero on failure with a clear message.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.comfyui.v3 import (  # noqa: E402
    ComfyHTTPClient,
    ComfyHTTPError,
    Executing,
    ExecutionComplete,
    ExecutionError,
    Inventory,
    Progress,
    Reconnected,
    WSClient,
)
from core.manifest import (  # noqa: E402
    Manifest,
    apply_slots,
    load_manifest_directory,
)
from core.manifest.roles import Role  # noqa: E402
from core.manifest.schema import SlotType  # noqa: E402
from core.modalities import default_registry  # noqa: E402
from core.run import Output, Run, RunStatus  # noqa: E402

DEFAULT_COMFYUI_URL = "http://172.27.1.165:8188"
DEFAULT_MANIFESTS_DIR = REPO_ROOT / "workflows" / "manifests"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output" / "v3_smoke"
DEFAULT_TIMEOUT_SECONDS = 600.0


class SmokeResult:
    """Structured result the harness returns; tests can introspect."""

    def __init__(
        self,
        *,
        manifest: Manifest,
        prompt_id: str,
        outputs: list[Output],
        latency_seconds: float,
        run: Run,
    ) -> None:
        self.manifest = manifest
        self.prompt_id = prompt_id
        self.outputs = outputs
        self.latency_seconds = latency_seconds
        self.run = run

    @property
    def total_bytes(self) -> int:
        return sum(len(o.bytes_read) for o in self.outputs)


class SmokeError(RuntimeError):
    """The smoke run failed in a way the operator should see."""


def _parse_slot_pairs(pairs: list[str]) -> dict[str, str]:
    """Convert ``--slot key=value`` strings into a dict."""
    out: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SmokeError(
                f"--slot expects KEY=VALUE, got: {pair!r}"
            )
        k, v = pair.split("=", 1)
        out[k.strip()] = v
    return out


def load_registry(
    manifests_dir: Path,
) -> tuple[dict[str, Manifest], list[str]]:
    """Load every manifest under ``manifests_dir``.

    Returns ``(by_id, errors)``. ``errors`` is a list of human-readable
    messages for manifests that failed to load.
    """
    loaded, errors = load_manifest_directory(manifests_dir)
    by_id: dict[str, Manifest] = {m.id: m for m in loaded}
    error_msgs = [str(e) for e in errors]
    return by_id, error_msgs


async def validate_registry_against_inventory(
    registry: dict[str, Manifest],
    inventory: Inventory,
) -> dict[str, list[str]]:
    """Return per-manifest list of missing-dep messages (empty list = OK)."""
    return {mid: inventory.validate_requires(m.requires) for mid, m in registry.items()}


async def run_smoke(
    *,
    manifest_id: str,
    slot_overrides: dict[str, Any],
    base_url: str = DEFAULT_COMFYUI_URL,
    manifests_dir: Path = DEFAULT_MANIFESTS_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    progress_callback=None,
) -> SmokeResult:
    """Execute one v3 Run end-to-end.

    Args:
        manifest_id: id (filename stem) of the manifest to run.
        slot_overrides: raw slot values (strings ok; coercion happens).
        base_url: ComfyUI URL.
        manifests_dir: where to look for manifest YAMLs.
        output_dir: destination for downloaded output bytes.
        timeout_seconds: max wall-clock budget for the Run.
        progress_callback: optional ``async (event, pct) -> None``.

    Returns:
        SmokeResult on success.

    Raises:
        SmokeError on any failure (manifest missing, requires unmet,
        applier failure, queue failure, execution_error, output missing).
    """
    logger = logging.getLogger("v3_smoke")
    registry, load_errors = load_registry(manifests_dir)
    if load_errors:
        for msg in load_errors:
            logger.warning("manifest load error: %s", msg)
    if manifest_id not in registry:
        raise SmokeError(
            f"manifest '{manifest_id}' not found in {manifests_dir} "
            f"(available: {sorted(registry)})"
        )
    manifest = registry[manifest_id]

    workflow_path = REPO_ROOT / manifest.workflow_file
    if not workflow_path.is_file():
        raise SmokeError(
            f"workflow file missing: {workflow_path} (referenced by {manifest_id})"
        )
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))

    plugin = default_registry.get(manifest.modality)
    logger.info(
        "Using Plugin %s for modality %s",
        plugin.__class__.__name__,
        manifest.modality.value,
    )

    client_id = uuid.uuid4().hex
    async with ComfyHTTPClient(base_url, client_id=client_id) as http:
        logger.info("Fetching /object_info from %s ...", base_url)
        try:
            object_info = await http.get_object_info()
        except ComfyHTTPError as e:
            raise SmokeError(f"could not fetch /object_info: {e}") from e
        inventory = Inventory(object_info)

        missing = inventory.validate_requires(manifest.requires)
        if missing:
            raise SmokeError(
                f"manifest '{manifest_id}' has unmet requires:\n  - "
                + "\n  - ".join(missing)
            )
        logger.info("Manifest '%s' requires satisfied.", manifest_id)

        try:
            slot_overrides = await _upload_image_slots(
                http=http,
                manifest=manifest,
                slot_overrides=slot_overrides,
                logger=logger,
            )
        except SmokeError:
            raise
        except Exception as e:
            raise SmokeError(f"image slot upload failed: {e}") from e

        try:
            slot_overrides = await _resolve_audio_inputs(
                http=http,
                manifest=manifest,
                slot_overrides=slot_overrides,
                logger=logger,
            )
        except SmokeError:
            raise
        except Exception as e:
            raise SmokeError(f"audio upload preprocess failed: {e}") from e

        try:
            coerced = await plugin.validate_slot_values(manifest, slot_overrides)
        except Exception as e:
            raise SmokeError(f"slot validation failed: {e}") from e
        logger.info("Coerced slot values: %s", _redact_for_log(coerced))

        try:
            workflow_to_queue = apply_slots(workflow, manifest, coerced)
        except Exception as e:
            raise SmokeError(f"apply_slots failed: {e}") from e

        run = Run(
            id=uuid.uuid4().hex,
            manifest_id=manifest.id,
            slot_values=coerced,
            status=RunStatus.QUEUED,
        )

        t0 = time.monotonic()

        async with WSClient(base_url, client_id=client_id) as ws:
            ws_events = ws.events()

            try:
                prompt_id = await http.queue_prompt(workflow_to_queue)
            except ComfyHTTPError as e:
                raise SmokeError(f"queue_prompt failed: {e}") from e
            run.prompt_id = prompt_id
            run.status = RunStatus.RUNNING
            logger.info("Queued prompt_id=%s", prompt_id)

            mapper = plugin.progress_mapper()

            async def _await_completion() -> None:
                async for event in ws_events:
                    if isinstance(event, Reconnected):
                        logger.info("ws reconnected (attempt=%d)", event.attempt)
                        continue
                    pid = getattr(event, "prompt_id", None)
                    if pid is not None and pid != prompt_id:
                        continue
                    pct = mapper.update(event)
                    if isinstance(event, Progress):
                        logger.info(
                            "progress node=%s %d/%d (%s%%)",
                            event.node,
                            event.value,
                            event.max,
                            pct if pct is not None else "--",
                        )
                    elif isinstance(event, Executing):
                        if event.node is None and pid == prompt_id:
                            logger.info(
                                "execution finished (executing node=<end>) prompt_id=%s",
                                pid,
                            )
                            if progress_callback is not None:
                                await progress_callback(event, pct)
                            return
                        logger.info(
                            "executing node=%s",
                            event.node if event.node else "<end>",
                        )
                    elif isinstance(event, ExecutionComplete):
                        logger.info("execution_complete prompt_id=%s", pid)
                        if progress_callback is not None:
                            await progress_callback(event, pct)
                        return
                    elif isinstance(event, ExecutionError):
                        raise SmokeError(
                            f"ComfyUI execution_error on node {event.node_id} "
                            f"({event.node_type}): {event.message}"
                        )
                    if progress_callback is not None:
                        await progress_callback(event, pct)

            try:
                await asyncio.wait_for(_await_completion(), timeout=timeout_seconds)
            except asyncio.TimeoutError as e:
                raise SmokeError(
                    f"timed out after {timeout_seconds:.0f}s waiting for prompt_id={prompt_id}"
                ) from e

        history = await http.get_history(prompt_id)
        entry = history.get(prompt_id)
        if not entry:
            raise SmokeError(
                f"prompt_id {prompt_id} missing from /history response"
            )

        outputs = await _collect_outputs(
            http=http,
            manifest=manifest,
            history_entry=entry,
            run=run,
            output_dir=output_dir,
            logger=logger,
        )

        run.status = RunStatus.COMPLETE
        run.output_files = [o.path for o in outputs]

        latency = time.monotonic() - t0
        return SmokeResult(
            manifest=manifest,
            prompt_id=prompt_id,
            outputs=outputs,
            latency_seconds=latency,
            run=run,
        )


async def _upload_image_slots(
    *,
    http: ComfyHTTPClient,
    manifest: Manifest,
    slot_overrides: dict[str, Any],
    logger: logging.Logger,
) -> dict[str, Any]:
    """Resolve IMAGE-type slot values that look like local file paths.

    For each Manifest slot whose ``type`` is ``IMAGE``, if the user
    supplied a string that points to an existing file, upload it to
    ComfyUI's ``/upload/image`` endpoint and replace the slot value
    with the server-side filename returned in the response. Values
    that are not file paths (e.g. already-uploaded filenames) pass
    through untouched.

    This is what makes ``--slot source_image=/path/to/file.png`` work
    against any manifest that exposes an IMAGE slot, without the
    harness needing to know which manifests have such slots.
    """
    slots = manifest.slots_by_name()
    updated = dict(slot_overrides)
    for name, value in list(slot_overrides.items()):
        slot = slots.get(name)
        if slot is None or slot.type != SlotType.IMAGE:
            continue
        if not isinstance(value, str):
            continue
        candidate = Path(value)
        if not candidate.is_file():
            continue
        data = candidate.read_bytes()
        ext = candidate.suffix.lower()
        content_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(ext, "application/octet-stream")
        try:
            resp = await http.upload_image(
                candidate.name,
                data,
                content_type=content_type,
            )
        except ComfyHTTPError as e:
            raise SmokeError(
                f"upload of slot '{name}' file {candidate} failed: {e}"
            ) from e
        server_name = resp.get("name") or candidate.name
        updated[name] = server_name
        logger.info(
            "uploaded slot '%s' file %s as %s (%d bytes)",
            name,
            candidate,
            server_name,
            len(data),
        )
    return updated


async def _collect_outputs(
    *,
    http: ComfyHTTPClient,
    manifest: Manifest,
    history_entry: dict[str, Any],
    run: Run,
    output_dir: Path,
    logger: logging.Logger,
) -> list[Output]:
    """Download every Output the manifest declares for this prompt."""
    node_outputs: dict[str, dict[str, Any]] = history_entry.get("outputs", {}) or {}
    if not node_outputs:
        raise SmokeError(
            f"history for prompt_id={run.prompt_id} has no outputs"
        )

    target_dir = output_dir / (run.prompt_id or run.id)
    target_dir.mkdir(parents=True, exist_ok=True)

    collected: list[Output] = []
    for spec in manifest.outputs:
        node_data = node_outputs.get(spec.node)
        if not node_data:
            raise SmokeError(
                f"manifest '{manifest.id}' declares output on node '{spec.node}' "
                f"but history has no outputs for that node (got: {sorted(node_outputs)})"
            )
        buckets = _candidate_buckets_for_media(spec.media)
        files: list[dict[str, Any]] = []
        for bucket in buckets:
            entries = node_data.get(bucket, []) or []
            if entries:
                files = entries
                logger.info(
                    "found %d %s entries on node '%s'",
                    len(entries),
                    bucket,
                    spec.node,
                )
                break
        if not files:
            raise SmokeError(
                f"node '{spec.node}' produced no {'/'.join(buckets)} for prompt "
                f"{run.prompt_id}; node_data keys={sorted(node_data)}"
            )
        for f in files:
            filename = f.get("filename")
            if not filename:
                continue
            data = await http.get_view(
                filename,
                type=f.get("type", "output"),
                subfolder=f.get("subfolder", "") or "",
            )
            local_path = target_dir / filename
            local_path.write_bytes(data)
            logger.info(
                "downloaded %s (%d bytes) -> %s",
                filename,
                len(data),
                local_path,
            )
            collected.append(
                Output(
                    role=spec.role,
                    media=spec.media,
                    path=local_path,
                    bytes_read=data,
                )
            )
    return collected


_AUDIO_EXT_MIME = {
    ".wav": "audio/wav",
    ".wave": "audio/wav",
    ".mp3": "audio/mpeg",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".opus": "audio/opus",
}


async def _resolve_audio_inputs(
    *,
    http: "ComfyHTTPClient",
    manifest: Manifest,
    slot_overrides: dict[str, Any],
    logger: logging.Logger,
) -> dict[str, Any]:
    """Upload any local path supplied for an AUDIO Slot, swap in the filename.

    For each manifest Slot with ``type: audio``, a string value is
    interpreted as a local filesystem path. The file is read, uploaded
    via the v3 client's ``upload_audio`` (alias for ``/upload/image``
    with audio mimes per ADR-0007), and the override is replaced with
    the filename ComfyUI assigned. Already-uploaded names (no path
    separator and no existing file) are passed through unchanged so
    operators can reference inputs they previously uploaded.
    """
    slots = manifest.slots_by_name()
    out: dict[str, Any] = dict(slot_overrides)
    for name, raw in list(slot_overrides.items()):
        slot = slots.get(name)
        if slot is None or slot.type != SlotType.AUDIO:
            continue
        if not isinstance(raw, str):
            continue
        path = Path(raw).expanduser()
        if not path.is_file():
            if "/" not in raw and "\\" not in raw:
                logger.info(
                    "audio slot '%s' value %r looks like an existing ComfyUI input; using verbatim",
                    name,
                    raw,
                )
                continue
            raise SmokeError(
                f"audio slot '{name}' references missing file: {path}"
            )
        data = path.read_bytes()
        ext = path.suffix.lower()
        content_type = _AUDIO_EXT_MIME.get(ext, "application/octet-stream")
        try:
            resp = await http.upload_audio(
                filename=path.name,
                data=data,
                content_type=content_type,
            )
        except ComfyHTTPError as e:
            raise SmokeError(
                f"upload_audio failed for slot '{name}' ({path}): {e}"
            ) from e
        uploaded = resp.get("name") or path.name
        logger.info(
            "uploaded audio slot '%s': %s -> %s (%d bytes)",
            name,
            path,
            uploaded,
            len(data),
        )
        out[name] = uploaded
    return out


def _candidate_buckets_for_media(media: str) -> list[str]:
    """Map a manifest MIME to ComfyUI history bucket keys, in priority order.

    Different ComfyUI nodes use different keys for the same output kind:
    SaveImage uses ``images``; the legacy VHS_VideoCombine custom node
    emits MP4 / WebM under ``gifs`` (historical naming) and newer builds
    may also expose ``videos``. Audio nodes commonly use ``audio``.
    We try all plausible names per Modality so the smoke harness does
    not need to know which node authored the output.
    """
    if media.startswith("image/"):
        return ["images"]
    if media.startswith("video/"):
        return ["videos", "gifs", "files"]
    if media.startswith("audio/"):
        return ["audio", "files"]
    return ["files"]


def _redact_for_log(values: dict[str, Any]) -> dict[str, Any]:
    """Trim long text values for cleaner log lines."""
    out: dict[str, Any] = {}
    for k, v in values.items():
        if isinstance(v, str) and len(v) > 80:
            out[k] = v[:77] + "..."
        else:
            out[k] = v
    return out


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="v3_smoke",
        description="DisComfy v3 end-to-end smoke against a live ComfyUI",
    )
    p.add_argument("--manifest", required=True, help="Manifest id (filename stem)")
    p.add_argument(
        "--slot",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override one slot value. Repeatable.",
    )
    p.add_argument(
        "--url",
        default=os.environ.get("COMFYUI_URL", DEFAULT_COMFYUI_URL),
        help=f"ComfyUI base URL (default: $COMFYUI_URL or {DEFAULT_COMFYUI_URL})",
    )
    p.add_argument(
        "--manifests-dir",
        type=Path,
        default=DEFAULT_MANIFESTS_DIR,
        help="Directory of manifest YAMLs",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Where to write downloaded outputs",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Max wall-clock budget for the Run (seconds)",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="DEBUG-level logging",
    )
    return p


async def _async_main(argv: list[str]) -> int:
    args = _build_arg_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    slot_overrides = _parse_slot_pairs(args.slot)
    try:
        result = await run_smoke(
            manifest_id=args.manifest,
            slot_overrides=slot_overrides,
            base_url=args.url,
            manifests_dir=args.manifests_dir,
            output_dir=args.output_dir,
            timeout_seconds=args.timeout,
        )
    except SmokeError as e:
        print(f"SMOKE FAILED: {e}", file=sys.stderr)
        return 2
    print()
    print("=" * 70)
    print(f"SMOKE OK  manifest={result.manifest.id}")
    print(f"  prompt_id : {result.prompt_id}")
    print(f"  latency_s : {result.latency_seconds:.2f}")
    print(f"  total_bytes: {result.total_bytes}")
    for o in result.outputs:
        print(
            f"  output    : role={o.role.value} media={o.media} "
            f"path={o.path} bytes={o.size_bytes}"
        )
    print("=" * 70)
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return asyncio.run(_async_main(list(argv) if argv is not None else sys.argv[1:]))
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
