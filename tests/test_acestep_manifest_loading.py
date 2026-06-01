"""Manifest-loading + requires-validation tests for ACE-Step 1.5.

The manifest is the architectural test of ADR-0007's audio_music
contract: one Modality, one Plugin, one workflow JSON whose every
target node ID has a slot pointing at it (no orphan slots, no
unmapped roles). Live ``/object_info`` was used to pick the
checkpoint filename and ACE-Step node graph; this test guards the
manifest against accidental schema regressions.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.comfyui.v3.capability import Inventory
from core.manifest import load_manifest
from core.manifest.roles import Modality, Role
from core.manifest.schema import SlotType
from core.modalities import default_registry
from core.modalities.audio_music.plugin import AudioMusicPlugin

MANIFEST_PATH = "workflows/manifests/audio_music_acestep.yaml"
WORKFLOW_PATH = Path("workflows/audio_music_acestep.json")


@pytest.fixture
def manifest():
    return load_manifest(MANIFEST_PATH)


@pytest.fixture
def workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def inventory() -> Inventory:
    """Inline Inventory that mirrors the live ComfyUI for ACE-Step.

    Mirrors the relevant slice of ``/object_info`` rather than
    extending the shared ``tests/fixtures/object_info_slim.json``: the
    ACE-Step nodes live under ``comfy_extras.nodes_ace`` and the
    checkpoint is in a directory the other slices don't touch.
    """
    return Inventory(
        {
            "CheckpointLoaderSimple": {
                "input": {
                    "required": {
                        "ckpt_name": [
                            [
                                "ace_step_1.5_turbo_aio.safetensors",
                                "ltx-2.3-22b-dev-fp8.safetensors",
                            ]
                        ]
                    }
                },
                "python_module": "nodes",
            },
            "EmptyAceStep1.5LatentAudio": {
                "input": {
                    "required": {
                        "seconds": ["FLOAT", {}],
                        "batch_size": ["INT", {}],
                    }
                },
                "python_module": "comfy_extras.nodes_ace",
            },
            "TextEncodeAceStepAudio1.5": {
                "input": {
                    "required": {
                        "clip": ["CLIP", {}],
                        "tags": ["STRING", {}],
                        "lyrics": ["STRING", {}],
                        "seed": ["INT", {}],
                        "bpm": ["INT", {}],
                        "duration": ["FLOAT", {}],
                        "timesignature": ["COMBO", {}],
                        "language": ["COMBO", {}],
                        "keyscale": ["COMBO", {}],
                        "generate_audio_codes": ["BOOLEAN", {}],
                        "cfg_scale": ["FLOAT", {}],
                        "temperature": ["FLOAT", {}],
                        "top_p": ["FLOAT", {}],
                        "top_k": ["INT", {}],
                        "min_p": ["FLOAT", {}],
                    }
                },
                "python_module": "comfy_extras.nodes_ace",
            },
            "KSampler": {
                "input": {
                    "required": {
                        "model": ["MODEL", {}],
                        "seed": ["INT", {}],
                        "steps": ["INT", {}],
                        "cfg": ["FLOAT", {}],
                        "sampler_name": [["euler", "dpmpp_2m"]],
                        "scheduler": [["simple", "normal"]],
                        "denoise": ["FLOAT", {}],
                        "positive": ["CONDITIONING", {}],
                        "negative": ["CONDITIONING", {}],
                        "latent_image": ["LATENT", {}],
                    }
                },
                "python_module": "nodes",
            },
            "VAEDecodeAudio": {
                "input": {
                    "required": {
                        "samples": ["LATENT", {}],
                        "vae": ["VAE", {}],
                    }
                },
                "python_module": "comfy_extras.nodes_ace",
            },
            "SaveAudioMP3": {
                "input": {
                    "required": {
                        "audio": ["AUDIO", {}],
                        "filename_prefix": ["STRING", {}],
                        "quality": ["COMBO", {}],
                    }
                },
                "python_module": "comfy_extras.nodes_audio",
            },
        }
    )


@pytest.fixture
def starved_inventory() -> Inventory:
    """An inventory that registers the ACE pack but lacks the checkpoint."""
    return Inventory(
        {
            "CheckpointLoaderSimple": {
                "input": {
                    "required": {
                        "ckpt_name": [["some_other_model.safetensors"]]
                    }
                },
                "python_module": "nodes",
            },
            "EmptyAceStep1.5LatentAudio": {
                "input": {"required": {}},
                "python_module": "comfy_extras.nodes_ace",
            },
        }
    )


class TestManifestShape:
    def test_id_and_modality(self, manifest) -> None:
        assert manifest.id == "audio_music_acestep"
        assert manifest.modality == Modality.AUDIO_MUSIC

    def test_output_is_audio_mpeg(self, manifest) -> None:
        assert len(manifest.outputs) == 1
        assert manifest.outputs[0].role == Role.OUTPUT_AUDIO
        assert manifest.outputs[0].media == "audio/mpeg"

    def test_no_actions(self, manifest) -> None:
        assert manifest.actions == []

    def test_requires_ace_pack(self, manifest) -> None:
        assert "comfy_extras.nodes_ace" in manifest.requires.packs

    def test_requires_aio_checkpoint(self, manifest) -> None:
        assert (
            "ace_step_1.5_turbo_aio.safetensors" in manifest.requires.checkpoints
        )

    def test_prompt_slot(self, manifest) -> None:
        slots = manifest.slots_by_name()
        assert "prompt" in slots
        assert slots["prompt"].type == SlotType.TEXT
        assert slots["prompt"].role == Role.PROMPT_POSITIVE
        assert slots["prompt"].ui.required is True

    def test_negative_prompt_slot(self, manifest) -> None:
        slots = manifest.slots_by_name()
        assert "negative_prompt" in slots
        assert slots["negative_prompt"].type == SlotType.TEXT
        assert slots["negative_prompt"].role == Role.PROMPT_NEGATIVE
        assert slots["negative_prompt"].ui.required is False

    def test_seconds_slot_uses_duration_role(self, manifest) -> None:
        slots = manifest.slots_by_name()
        assert "seconds" in slots
        assert slots["seconds"].type == SlotType.FLOAT
        assert slots["seconds"].role == Role.DURATION_SECONDS

    def test_seconds_targets_latent_and_both_encoders(self, manifest) -> None:
        seconds = manifest.slots_by_name()["seconds"]
        targets = seconds.resolved_targets()
        target_nodes = sorted(t.node for t in targets)
        assert target_nodes == ["2", "3", "4"]

    def test_seed_slot(self, manifest) -> None:
        slots = manifest.slots_by_name()
        assert "seed" in slots
        assert slots["seed"].type == SlotType.SEED
        assert slots["seed"].role == Role.SEED

    def test_seconds_validation_bounds(self, manifest) -> None:
        seconds = manifest.slots_by_name()["seconds"]
        assert seconds.validation is not None
        assert seconds.validation.min == 1
        assert seconds.validation.max == 240


class TestSlotToWorkflowMapping:
    """Every slot target must exist in the workflow JSON, no orphan slots."""

    def test_every_slot_target_node_exists(self, manifest, workflow) -> None:
        for slot in manifest.slots:
            for target in slot.resolved_targets():
                assert target.node in workflow, (
                    f"slot '{slot.name}' targets node '{target.node}' "
                    f"which is missing from workflow JSON"
                )
                node = workflow[target.node]
                assert target.field in node["inputs"], (
                    f"slot '{slot.name}' targets field '{target.field}' "
                    f"which is missing on node '{target.node}'"
                )

    def test_every_output_node_exists(self, manifest, workflow) -> None:
        for spec in manifest.outputs:
            assert spec.node in workflow, (
                f"output role '{spec.role.value}' references missing "
                f"node '{spec.node}'"
            )

    def test_workflow_uses_acestep_15_encoder(self, workflow) -> None:
        encoder_nodes = [
            n
            for n in workflow.values()
            if n.get("class_type") == "TextEncodeAceStepAudio1.5"
        ]
        assert len(encoder_nodes) == 2, (
            "ACE-Step graph should use one positive + one negative "
            "TextEncodeAceStepAudio1.5 encoder"
        )

    def test_workflow_uses_aio_checkpoint(self, workflow) -> None:
        ckpt_nodes = [
            n
            for n in workflow.values()
            if n.get("class_type") == "CheckpointLoaderSimple"
        ]
        assert len(ckpt_nodes) == 1
        assert (
            ckpt_nodes[0]["inputs"]["ckpt_name"]
            == "ace_step_1.5_turbo_aio.safetensors"
        )

    def test_workflow_terminates_in_save_audio_mp3(self, workflow) -> None:
        save_nodes = [
            n
            for n in workflow.values()
            if n.get("class_type") == "SaveAudioMP3"
        ]
        assert len(save_nodes) == 1

    def test_no_extra_unmapped_roles(self, manifest) -> None:
        """The four authored slots cover the manifest's role surface.

        Adding a Slot must be a deliberate manifest edit, not an
        accidental drift. This test pins the slot set.
        """
        slot_names = sorted(s.name for s in manifest.slots)
        assert slot_names == [
            "negative_prompt",
            "prompt",
            "seconds",
            "seed",
        ]


class TestRequiresValidationAgainstInventory:
    def test_fully_satisfied(self, manifest, inventory) -> None:
        missing = inventory.validate_requires(manifest.requires)
        assert missing == [], missing

    def test_missing_checkpoint_reports_it(
        self, manifest, starved_inventory
    ) -> None:
        missing = starved_inventory.validate_requires(manifest.requires)
        assert any(
            "ace_step_1.5_turbo_aio.safetensors" in m for m in missing
        ), missing


class TestRegistryWiring:
    def test_audio_music_modality_resolves_to_plugin(self, manifest) -> None:
        plugin = default_registry.get(manifest.modality)
        assert isinstance(plugin, AudioMusicPlugin)
        assert plugin.modality == Modality.AUDIO_MUSIC
