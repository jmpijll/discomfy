"""PROTOTYPE - delete after Phase 1 of v3 redesign.

Probes a ComfyUI instance for capabilities relevant to DisComfy v3:
- /system_stats: ComfyUI version, GPU/RAM info
- /object_info: every node class registered (-> derives custom-node packs installed)
- /embeddings: embeddings available for prompting
- /queue: current queue state (sanity check the API is alive)

Categorises installed custom nodes into modality buckets so we know what
v3 modality plugins (image / video / audio) are actually feasible on this
machine.

Usage:
    python scripts/discover_comfyui.py [--url http://host:8188] [--out docs/v3/discovery.md]

Reads COMFYUI_URL from .env if --url not given. Falls back to config.json.

Throwaway. No tests. No abstractions. The artifact is docs/v3/discovery.md.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiohttp

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


# Heuristic node-name patterns -> modality bucket. Conservative: if a node
# clearly signals a modality, label it; otherwise it goes to "other".
MODALITY_PATTERNS: dict[str, list[str]] = {
    "image_t2i": ["KSampler", "EmptyLatentImage", "FluxGuidance", "ModelSamplingFlux", "DyPE_FLUX", "HiDream"],
    "image_edit": ["Kontext", "QwenImageEdit", "InstructPix2Pix", "ImageEditor"],
    "image_upscale": ["Upscale", "RealESRGAN", "UltimateSDUpscale", "NMKD"],
    "video": ["VHS_", "VideoHelper", "AnimateDiff", "Wan", "Hunyuan", "LTX", "VACE", "Mochi", "CogVideo", "Cosmos"],
    "audio_tts": ["F5TTS", "ChatterboxTTS", "TTS", "VoiceClone", "WhisperTTS", "Piper"],
    "audio_music": ["ACE_Step", "ACEStep", "StableAudio", "MusicGen", "AudioCraft", "AudioGenerate"],
    "vision": ["Florence", "QwenVL", "Llava", "BLIP", "WD14", "Caption"],
    "lora": ["LoraLoader", "LoRA"],
}


def bucket_for_node(node_name: str) -> str:
    for bucket, patterns in MODALITY_PATTERNS.items():
        for pat in patterns:
            if pat.lower() in node_name.lower():
                return bucket
    return "other"


def resolve_url(cli_url: str | None) -> str:
    if cli_url:
        return cli_url.rstrip("/")
    env_url = os.environ.get("COMFYUI_URL")
    if env_url:
        return env_url.rstrip("/")
    config_path = Path("config.json")
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())["comfyui"]["url"].rstrip("/")
        except Exception:
            pass
    return "http://localhost:8188"


async def fetch_json(session: aiohttp.ClientSession, url: str, timeout: float = 30.0) -> Any:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
        r.raise_for_status()
        return await r.json()


async def probe(url: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "url": url,
        "probed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reachable": False,
        "errors": [],
    }
    timeout = aiohttp.ClientTimeout(total=10, connect=5)
    connector = aiohttp.TCPConnector(limit=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            try:
                out["system_stats"] = await fetch_json(session, f"{url}/system_stats", timeout=8)
                out["reachable"] = True
            except Exception as e:
                out["errors"].append(f"/system_stats: {e!r}")
                return out
            for endpoint, key in [
                ("/object_info", "object_info"),
                ("/embeddings", "embeddings"),
                ("/queue", "queue"),
            ]:
                try:
                    out[key] = await fetch_json(session, f"{url}{endpoint}", timeout=60)
                except Exception as e:
                    out["errors"].append(f"{endpoint}: {e!r}")
    except Exception as e:
        out["errors"].append(f"session: {e!r}")
    return out


def summarise(probe_result: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {"reachable": probe_result["reachable"]}
    if not probe_result["reachable"]:
        return summary

    obj_info = probe_result.get("object_info", {}) or {}
    summary["total_nodes"] = len(obj_info)

    by_bucket: dict[str, list[str]] = defaultdict(list)
    by_module: dict[str, int] = defaultdict(int)
    for node_name, node_data in obj_info.items():
        by_bucket[bucket_for_node(node_name)].append(node_name)
        module = (node_data or {}).get("python_module", "?")
        by_module[module] += 1
    summary["by_bucket_counts"] = {k: len(v) for k, v in by_bucket.items()}
    summary["by_bucket_samples"] = {k: sorted(v)[:25] for k, v in by_bucket.items()}
    summary["by_module"] = dict(sorted(by_module.items(), key=lambda kv: -kv[1])[:40])

    samp = obj_info.get("KSampler", {})
    sampler_inputs = (samp.get("input", {}) or {}).get("required", {}) or {}
    summary["samplers"] = (sampler_inputs.get("sampler_name") or [[]])[0]
    summary["schedulers"] = (sampler_inputs.get("scheduler") or [[]])[0]

    ckpt = obj_info.get("CheckpointLoaderSimple", {})
    ckpt_inputs = (ckpt.get("input", {}) or {}).get("required", {}) or {}
    summary["checkpoints"] = (ckpt_inputs.get("ckpt_name") or [[]])[0]

    lora = obj_info.get("LoraLoader", {})
    lora_inputs = (lora.get("input", {}) or {}).get("required", {}) or {}
    summary["loras"] = (lora_inputs.get("lora_name") or [[]])[0]

    summary["embeddings"] = probe_result.get("embeddings", []) or []
    summary["queue"] = probe_result.get("queue", {})
    summary["system_stats"] = probe_result.get("system_stats", {})
    return summary


def render_markdown(probe_result: dict[str, Any], summary: dict[str, Any], url: str) -> str:
    now = probe_result["probed_at"]
    lines = [
        "# DisComfy v3 - ComfyUI Discovery Report",
        "",
        f"- **Probed:** {now}",
        f"- **URL:** `{url}`",
        f"- **Reachable:** {summary['reachable']}",
        "",
    ]
    if not summary["reachable"]:
        lines += [
            "## Status: NOT REACHABLE",
            "",
            "ComfyUI did not respond to `/system_stats` within the timeout.",
            "",
            "**Errors:**",
            "",
        ]
        for e in probe_result.get("errors", []):
            lines.append(f"- `{e}`")
        lines += [
            "",
            "## Re-run when ComfyUI is up",
            "",
            "```bash",
            "source venv/bin/activate",
            f"python scripts/discover_comfyui.py --url {url}",
            "```",
            "",
            "Or set `COMFYUI_URL` in `.env` and run with no args.",
            "",
            "Until this report has a successful probe, Phase 2 ADR-007 (audio modality)",
            "and the parts of ADR-001 that depend on real node names (`node_map` examples)",
            "will be written against assumed node names and revisited after discovery.",
            "",
        ]
        return "\n".join(lines) + "\n"

    sysinfo = summary.get("system_stats", {})
    lines += [
        "## System",
        "",
        f"```json\n{json.dumps(sysinfo, indent=2)[:2000]}\n```",
        "",
        f"## Nodes registered: {summary['total_nodes']}",
        "",
        "### By modality bucket (heuristic)",
        "",
        "| Bucket | Count |",
        "| --- | ---: |",
    ]
    for bucket, count in sorted(summary["by_bucket_counts"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{bucket}` | {count} |")

    lines += ["", "### Sample nodes per bucket (up to 25)", ""]
    for bucket, sample in summary["by_bucket_samples"].items():
        if not sample:
            continue
        lines.append(f"**`{bucket}`** ({len(sample)} shown):")
        lines.append("")
        for n in sample:
            lines.append(f"- `{n}`")
        lines.append("")

    lines += ["### Top python_modules (custom node packs)", ""]
    lines += ["| python_module | nodes |", "| --- | ---: |"]
    for mod, count in summary["by_module"].items():
        lines.append(f"| `{mod}` | {count} |")
    lines.append("")

    samplers = summary.get("samplers", [])
    schedulers = summary.get("schedulers", [])
    if samplers:
        lines += ["### Samplers / schedulers (KSampler)", "", f"- samplers: {samplers}", f"- schedulers: {schedulers}", ""]

    ckpts = summary.get("checkpoints", [])
    if ckpts:
        lines += [f"### Checkpoints ({len(ckpts)})", ""]
        for c in ckpts[:50]:
            lines.append(f"- `{c}`")
        if len(ckpts) > 50:
            lines.append(f"- ... and {len(ckpts) - 50} more")
        lines.append("")

    loras = summary.get("loras", [])
    if loras:
        lines += [f"### LoRAs ({len(loras)})", ""]
        for l in loras[:50]:
            lines.append(f"- `{l}`")
        if len(loras) > 50:
            lines.append(f"- ... and {len(loras) - 50} more")
        lines.append("")

    embeddings = summary.get("embeddings", [])
    if embeddings:
        lines += [f"### Embeddings ({len(embeddings)})", ""]
        for e in embeddings[:30]:
            lines.append(f"- `{e}`")
        lines.append("")

    lines += [
        "## v3 viability per modality (preliminary)",
        "",
        "Read the bucket counts above. Heuristics:",
        "",
        "- **image_t2i** present if `KSampler` + a Flux/HiDream/Qwen sampler/loader exist.",
        "- **image_edit** present if `Kontext` or `QwenImageEdit` nodes exist.",
        "- **image_upscale** present if any `Upscale`/`RealESRGAN`/`UltimateSDUpscale` exist.",
        "- **video** present if `VHS_` (Video Helper Suite) or `Wan/Hunyuan/LTX/VACE/Mochi` exist.",
        "- **audio_tts** present if `F5TTS`/`ChatterboxTTS`/`TTS` nodes exist.",
        "- **audio_music** present if `ACE_Step`/`StableAudio`/`MusicGen` nodes exist.",
        "",
        "If a target modality is missing, ADR-007 must propose either",
        "a) installing the required custom node pack on the ComfyUI server, or",
        "b) deferring that modality to a later v3.x.",
        "",
        f"_Generated by `scripts/discover_comfyui.py` at {now}._",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="ComfyUI base URL; default reads COMFYUI_URL env or config.json")
    parser.add_argument("--out", default="docs/v3/discovery.md", help="output markdown path")
    parser.add_argument("--raw", default="docs/v3/discovery.raw.json", help="raw JSON dump path")
    args = parser.parse_args()

    url = resolve_url(args.url)
    print(f"[discover] probing {url}", file=sys.stderr)
    result = asyncio.run(probe(url))
    summary = summarise(result)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown(result, summary, url))
    print(f"[discover] wrote {out_path}", file=sys.stderr)

    raw_path = Path(args.raw)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"[discover] wrote {raw_path} ({raw_path.stat().st_size} bytes)", file=sys.stderr)

    if not result["reachable"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
