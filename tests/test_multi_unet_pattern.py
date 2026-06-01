"""Architectural test: the multi-UNET Manifest pattern (ADR-0001).

This is the golden test for the WAN 2.2 HIGH+LOW dual-UNET workflow.
Applying ``model_high`` and ``model_low`` Slot values must write into
TWO distinct ``UNETLoader`` nodes (different node IDs) - not collide
into the same node, not silently drop one of the two.

The seed slot, which uses ``targets: [...]``, exercises the same
multi-target mechanism for a single value landing on two nodes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.manifest import apply_slots, load_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def manifest():
    return load_manifest(REPO_ROOT / "workflows" / "manifests" / "wan22_i2v.yaml")


@pytest.fixture(scope="module")
def workflow() -> dict:
    return json.loads(
        (REPO_ROOT / "workflows" / "wan22_i2v.json").read_text(encoding="utf-8")
    )


def _high_low_unet_nodes(workflow: dict) -> tuple[str, str]:
    """Find the two UNETLoader nodes and label them HIGH/LOW by the file."""
    by_unet: dict[str, str] = {}
    for node_id, node in workflow.items():
        if node.get("class_type") == "UNETLoader":
            by_unet[node["inputs"]["unet_name"]] = node_id
    return (
        next(nid for name, nid in by_unet.items() if "FP8H" in name),
        next(nid for name, nid in by_unet.items() if "FP8L" in name),
    )


class TestMultiUnetMapping:
    def test_workflow_declares_two_distinct_unet_nodes(self, workflow) -> None:
        unet_nodes = [
            nid
            for nid, n in workflow.items()
            if n.get("class_type") == "UNETLoader"
        ]
        assert len(unet_nodes) == 2
        assert unet_nodes[0] != unet_nodes[1]

    def test_manifest_targets_two_distinct_unet_nodes(self, manifest) -> None:
        slots = manifest.slots_by_name()
        high_targets = [t.node for t in slots["model_high"].resolved_targets()]
        low_targets = [t.node for t in slots["model_low"].resolved_targets()]
        assert len(high_targets) == 1
        assert len(low_targets) == 1
        assert high_targets[0] != low_targets[0]

    def test_apply_slots_writes_both_unets(self, manifest, workflow) -> None:
        high_node, low_node = _high_low_unet_nodes(workflow)
        values = {
            "prompt": "camera pans right across a misty forest",
            "init_image": "src.png",
            "model_high": (
                "wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8H.safetensors"
            ),
            "model_low": (
                "wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8L.safetensors"
            ),
            "frame_count": 17,
            "seed": 12345,
            "cfg": 6.0,
            "steps_high": 4,
            "steps_low": 4,
        }
        applied = apply_slots(workflow, manifest, values)
        assert applied[high_node]["inputs"]["unet_name"].endswith("FP8H.safetensors")
        assert applied[low_node]["inputs"]["unet_name"].endswith("FP8L.safetensors")
        assert (
            applied[high_node]["inputs"]["unet_name"]
            != applied[low_node]["inputs"]["unet_name"]
        )

    def test_apply_slots_preserves_dual_lora_wiring(
        self, manifest, workflow
    ) -> None:
        """Each LoraLoaderModelOnly must stay wired to its matching UNET."""
        applied = apply_slots(
            workflow,
            manifest,
            {
                "prompt": "x",
                "init_image": "src.png",
                "model_high": (
                    "wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8H.safetensors"
                ),
                "model_low": (
                    "wan22EnhancedNSFWCameraPrompt_nsfwFASTMOVEV2FP8L.safetensors"
                ),
            },
        )
        high_node, low_node = _high_low_unet_nodes(workflow)
        loras = {
            nid: n
            for nid, n in applied.items()
            if n.get("class_type") == "LoraLoaderModelOnly"
        }
        assert len(loras) == 2
        upstream_unets = {nid: l["inputs"]["model"][0] for nid, l in loras.items()}
        assert set(upstream_unets.values()) == {high_node, low_node}
        for lora_id, lora in loras.items():
            upstream = lora["inputs"]["model"][0]
            if upstream == high_node:
                assert "HIGH" in lora["inputs"]["lora_name"]
            elif upstream == low_node:
                assert "LOW" in lora["inputs"]["lora_name"]

    def test_seed_value_lands_on_both_samplers(
        self, manifest, workflow
    ) -> None:
        """Multi-target slot (seed) demonstrates the same mechanism."""
        applied = apply_slots(
            workflow,
            manifest,
            {
                "prompt": "x",
                "init_image": "src.png",
                "seed": 987654321,
            },
        )
        sampler_ids = [
            nid
            for nid, n in applied.items()
            if n.get("class_type") == "KSampler"
        ]
        assert len(sampler_ids) == 2
        for sid in sampler_ids:
            assert applied[sid]["inputs"]["seed"] == 987654321

    def test_steps_high_and_low_target_distinct_samplers(
        self, manifest, workflow
    ) -> None:
        applied = apply_slots(
            workflow,
            manifest,
            {
                "prompt": "x",
                "init_image": "src.png",
                "steps_high": 7,
                "steps_low": 3,
            },
        )
        sampler_ids = sorted(
            nid
            for nid, n in applied.items()
            if n.get("class_type") == "KSampler"
        )
        steps_seen = sorted(
            applied[sid]["inputs"]["steps"] for sid in sampler_ids
        )
        assert steps_seen == [3, 7]
