"""Tests for the FLUX 2 Klein 9B image_t2i Manifest (Slice 2, issue #4).

These tests exercise:

- Loading the new ``flux2_klein`` Manifest cleanly through the v3 schema.
- The new Workflow JSON's NodeMap: every Slot target resolves to a real
  ``(node, field)`` pair, and ``apply_slots`` writes user values through
  to the expected nodes.
- Multi-manifest behaviour: loading the manifests directory yields BOTH
  ``qwen_image_2512`` and ``flux2_klein`` under the same
  :class:`~core.manifest.roles.Modality` (``IMAGE_T2I``), proving the
  registry doesn't collapse them.
- The single :class:`~core.modalities.image_t2i.plugin.ImageT2IPlugin`
  validates and renders for both manifests with no per-model branching.
- The Inventory's ``validate_requires`` is satisfied for the live model
  inventory captured in ``tests/fixtures/object_info_slim.json``.

No live ComfyUI; no Discord runtime. The live smoke for the manifest
lives in ``scripts/v3_smoke.py`` and is invoked manually for the PR.
"""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from pathlib import Path

import pytest

from bot.setup.builder import (
    MAX_MODAL_TEXT_INPUTS,
    MAX_SELECT_OPTIONS,
    SetupBuilder,
)
from core.comfyui.v3.capability import Inventory
from core.manifest import (
    apply_slots,
    load_manifest,
    load_manifest_directory,
)
from core.manifest.roles import Modality, Role
from core.manifest.schema import SlotType
from core.modalities import default_registry
from core.modalities.base import SlotValueValidationError
from core.modalities.image_t2i.plugin import ImageT2IPlugin
from core.run import Output, Run, RunStatus

MANIFEST_PATH = Path("workflows/manifests/flux2_klein.yaml")
WORKFLOW_PATH = Path("workflows/flux2_klein_t2i.json")
FIXTURE_PATH = Path("tests/fixtures/object_info_slim.json")


@pytest.fixture
def manifest():
    return load_manifest(MANIFEST_PATH)


@pytest.fixture
def workflow() -> dict:
    return json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def inventory() -> Inventory:
    return Inventory(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


class TestManifestShape:
    """The YAML loads, declares the right Modality, and exposes the
    expected slot set in declaration order."""

    def test_loads_with_schema_v1(self, manifest) -> None:
        assert manifest.schema_version == 1
        assert manifest.id == "flux2_klein"
        assert manifest.modality == Modality.IMAGE_T2I

    def test_slot_set_matches_spec(self, manifest) -> None:
        assert [s.name for s in manifest.slots] == [
            "prompt",
            "negative_prompt",
            "width",
            "height",
            "seed",
            "lora",
            "lora_strength",
            "unet",
        ]

    def test_slot_types_and_roles(self, manifest) -> None:
        by_name = manifest.slots_by_name()
        assert by_name["prompt"].type == SlotType.TEXT
        assert by_name["prompt"].role == Role.PROMPT_POSITIVE
        assert by_name["negative_prompt"].role == Role.PROMPT_NEGATIVE
        assert by_name["width"].type == SlotType.INT
        assert by_name["height"].type == SlotType.INT
        assert by_name["seed"].type == SlotType.SEED
        assert by_name["lora"].type == SlotType.ENUM_DYNAMIC
        assert by_name["lora"].options_from == "comfyui.loras"
        assert by_name["lora_strength"].type == SlotType.FLOAT
        assert by_name["unet"].type == SlotType.ENUM_STATIC
        assert by_name["unet"].role == Role.MODEL

    def test_unet_static_options(self, manifest) -> None:
        unet = manifest.slots_by_name()["unet"]
        assert unet.options == [
            "flux-2-klein-9b.safetensors",
            "darkBeastMar2126Latest_dbkleinv2BFS.safetensors",
        ]
        assert unet.ui.default == "flux-2-klein-9b.safetensors"

    def test_outputs_are_png(self, manifest) -> None:
        assert len(manifest.outputs) == 1
        assert manifest.outputs[0].role == Role.OUTPUT_IMAGE
        assert manifest.outputs[0].media == "image/png"

    def test_actions_declared(self, manifest) -> None:
        assert [a.id for a in manifest.actions] == ["upscale", "animate", "edit"]


class TestNodeMap:
    """Every Slot target lands on a real (node, field) in the Workflow JSON,
    and apply_slots writes values through end-to-end."""

    def test_every_target_resolves(self, manifest, workflow) -> None:
        for slot in manifest.slots:
            for target in slot.resolved_targets():
                node = workflow.get(target.node)
                assert node is not None, (
                    f"slot '{slot.name}' -> missing node {target.node}"
                )
                assert target.field in node["inputs"], (
                    f"slot '{slot.name}' -> node {target.node} has no field "
                    f"{target.field!r}; available={list(node['inputs'])}"
                )

    def test_output_node_is_save_image(self, manifest, workflow) -> None:
        out = manifest.outputs[0]
        node = workflow[out.node]
        assert node["class_type"] == "SaveImage"

    def test_apply_slots_writes_everything(self, manifest, workflow) -> None:
        applied = apply_slots(
            workflow,
            manifest,
            {
                "prompt": "a single red panda eating bamboo",
                "negative_prompt": "low quality, blurry",
                "width": 1024,
                "height": 1024,
                "seed": 4242,
                "lora": "Klein-consistency.safetensors",
                "lora_strength": 0.8,
                "unet": "flux-2-klein-9b.safetensors",
            },
        )
        assert applied["5"]["inputs"]["text"] == "a single red panda eating bamboo"
        assert applied["6"]["inputs"]["text"] == "low quality, blurry"
        assert applied["7"]["inputs"]["width"] == 1024
        assert applied["7"]["inputs"]["height"] == 1024
        assert applied["8"]["inputs"]["seed"] == 4242
        assert applied["4"]["inputs"]["lora_name"] == "Klein-consistency.safetensors"
        assert applied["4"]["inputs"]["strength_model"] == 0.8
        assert applied["1"]["inputs"]["unet_name"] == "flux-2-klein-9b.safetensors"

    def test_apply_slots_supports_dbklein_variant(
        self, manifest, workflow
    ) -> None:
        applied = apply_slots(
            workflow,
            manifest,
            {
                "prompt": "x",
                "unet": "darkBeastMar2126Latest_dbkleinv2BFS.safetensors",
            },
        )
        assert (
            applied["1"]["inputs"]["unet_name"]
            == "darkBeastMar2126Latest_dbkleinv2BFS.safetensors"
        )


class TestInventoryRequires:
    """`Inventory.validate_requires` accepts the manifest's requires block
    against the fixture inventory (no missing UNET/VAE/CLIP)."""

    def test_no_unmet_requires(self, manifest, inventory) -> None:
        problems = inventory.validate_requires(manifest.requires)
        assert problems == [], problems


class TestMultiManifestRegistry:
    """Loading the manifests directory yields BOTH qwen_image_2512 and
    flux2_klein under Modality.IMAGE_T2I - the core promise of Slice 2.

    No manifest collapses or shadows another; both surface to the bot
    layer for the `/image` workflow picker described in ADR-0003.
    """

    def test_both_image_t2i_manifests_load(self) -> None:
        loaded, errors = load_manifest_directory("workflows/manifests")
        assert errors == [], [str(e) for e in errors]
        by_id = {m.id: m for m in loaded}
        assert "qwen_image_2512" in by_id
        assert "flux2_klein" in by_id

    def test_both_register_under_image_t2i_modality(self) -> None:
        loaded, _ = load_manifest_directory("workflows/manifests")
        by_modality: dict[Modality, list[str]] = defaultdict(list)
        for m in loaded:
            by_modality[m.modality].append(m.id)
        assert sorted(by_modality[Modality.IMAGE_T2I]) == sorted(
            ["flux2_klein", "qwen_image_2512"]
        )

    def test_single_plugin_serves_both(self) -> None:
        plugin = default_registry.get(Modality.IMAGE_T2I)
        loaded, _ = load_manifest_directory("workflows/manifests")
        for m in loaded:
            if m.modality == Modality.IMAGE_T2I:
                assert plugin.default_post_actions(m) == list(m.actions)

    def test_no_id_collision(self) -> None:
        loaded, _ = load_manifest_directory("workflows/manifests")
        ids = [m.id for m in loaded]
        assert len(ids) == len(set(ids)), f"duplicate manifest ids: {ids}"


class TestPluginAgainstManifest:
    """The single ImageT2IPlugin coerces + validates slot values against the
    FLUX 2 Klein manifest just as cleanly as against the Qwen one - proving
    there's no per-model branching (ADR-0002)."""

    @pytest.fixture
    def plugin(self) -> ImageT2IPlugin:
        return ImageT2IPlugin()

    @pytest.mark.asyncio
    async def test_coerces_str_int_to_int(self, plugin, manifest) -> None:
        out = await plugin.validate_slot_values(
            manifest,
            {"prompt": "x", "width": "1024", "height": "1024"},
        )
        assert out["width"] == 1024
        assert out["height"] == 1024

    @pytest.mark.asyncio
    async def test_enforces_max_dimension(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest, {"prompt": "x", "width": "4096"}
            )

    @pytest.mark.asyncio
    async def test_enforces_multiple_of_64(self, plugin, manifest) -> None:
        with pytest.raises(SlotValueValidationError):
            await plugin.validate_slot_values(
                manifest, {"prompt": "x", "width": "1000"}
            )

    @pytest.mark.asyncio
    async def test_seed_random_resolves_to_int(self, plugin, manifest) -> None:
        out = await plugin.validate_slot_values(
            manifest, {"prompt": "x", "seed": "random"}
        )
        assert isinstance(out["seed"], int)

    @pytest.mark.asyncio
    async def test_render_outputs_includes_lora_field(
        self, plugin, manifest, tmp_path: Path
    ) -> None:
        png_bytes = b"\x89PNG\r\n\x1a\nfake-flux2-pixels"
        out_path = tmp_path / "flux2_klein_00001_.png"
        out_path.write_bytes(png_bytes)
        run = Run(
            id=uuid.uuid4().hex,
            manifest_id=manifest.id,
            prompt_id="prompt-id-123",
            slot_values={
                "prompt": "a red panda",
                "width": 1024,
                "height": 1024,
                "seed": 42,
                "lora": "Klein-consistency.safetensors",
            },
            status=RunStatus.COMPLETE,
        )
        output = Output(
            role=Role.OUTPUT_IMAGE,
            media="image/png",
            path=out_path,
            bytes_read=png_bytes,
        )
        payload = await plugin.render_outputs(run, [output])
        names = [f["name"] for f in payload.embed["fields"]]
        assert "Prompt" in names
        assert "Size" in names
        assert "Seed" in names
        assert "LoRA" in names
        assert payload.files[0].filename == "flux2_klein_00001_.png"


class TestSetupBuilderForFlux2Klein:
    """The shared :class:`SetupBuilder` plans a legal Discord UI for the
    FLUX 2 Klein manifest. This is the proof that ADR-0003's UI
    generation is manifest-driven, not per-model.
    """

    def test_modal_holds_five_text_slots(self, manifest, inventory) -> None:
        plan = SetupBuilder(manifest, inventory).build()
        assert len(plan.binning.modal_text) == MAX_MODAL_TEXT_INPUTS
        assert [s.name for s in plan.binning.modal_text] == [
            "prompt",
            "negative_prompt",
            "width",
            "height",
            "seed",
        ]

    def test_lora_strength_overflows_to_second_modal(
        self, manifest, inventory
    ) -> None:
        plan = SetupBuilder(manifest, inventory).build()
        assert plan.binning.has_overflow
        assert [s.name for s in plan.binning.overflow_text] == ["lora_strength"]

    def test_lora_and_unet_become_selects(self, manifest, inventory) -> None:
        plan = SetupBuilder(manifest, inventory).build()
        assert [s.name for s in plan.binning.selects] == ["lora", "unet"]

    def test_lora_select_options_resolve_from_inventory(
        self, manifest, inventory
    ) -> None:
        plan = SetupBuilder(manifest, inventory).build()
        opts = plan.select_options["lora"]
        assert "Klein-consistency.safetensors" in opts
        assert len(opts) <= MAX_SELECT_OPTIONS

    def test_unet_static_select_lists_both_klein_variants(
        self, manifest, inventory
    ) -> None:
        plan = SetupBuilder(manifest, inventory).build()
        opts = plan.select_options["unet"]
        assert opts == [
            "flux-2-klein-9b.safetensors",
            "darkBeastMar2126Latest_dbkleinv2BFS.safetensors",
        ]
