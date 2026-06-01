"""Tests for core.manifest.schema - the executable form of ADR-0001."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.manifest.roles import Modality, Role
from core.manifest.schema import (
    Action,
    ActionMap,
    Manifest,
    Output,
    Requires,
    Slot,
    SlotType,
    SlotUI,
    SlotValidation,
    Target,
    UIHint,
)


def _ok_slot(name: str = "prompt", role: Role = Role.PROMPT_POSITIVE) -> Slot:
    return Slot(
        name=name,
        type=SlotType.TEXT,
        role=role,
        target=Target(node="18", field="text"),
        ui=SlotUI(hint=UIHint.LONG_TEXT, label="Prompt"),
    )


def _ok_output() -> Output:
    return Output(role=Role.OUTPUT_IMAGE, node="13", media="image/png")


def _ok_manifest(**overrides) -> Manifest:
    base = dict(
        schema_version=1,
        id="qwen_image_2512",
        name="Qwen-Image 2512",
        modality=Modality.IMAGE_T2I,
        workflow_file="workflows/qwen_image_2512_lora.json",
        slots=[_ok_slot()],
        outputs=[_ok_output()],
    )
    base.update(overrides)
    return Manifest.model_validate(base)


class TestManifest:
    def test_minimal_valid_manifest(self):
        m = _ok_manifest()
        assert m.id == "qwen_image_2512"
        assert m.modality == Modality.IMAGE_T2I
        assert len(m.slots) == 1
        assert len(m.outputs) == 1

    def test_unsupported_schema_version(self):
        with pytest.raises(ValidationError) as exc:
            _ok_manifest(schema_version=99)
        assert "schema_version" in str(exc.value).lower()

    def test_extra_top_level_fields_rejected(self):
        with pytest.raises(ValidationError):
            Manifest.model_validate(
                {
                    "schema_version": 1,
                    "id": "x",
                    "name": "X",
                    "modality": "image_t2i",
                    "workflow_file": "w.json",
                    "outputs": [_ok_output().model_dump()],
                    "extra_field": "nope",
                }
            )

    def test_id_must_be_snake_case(self):
        with pytest.raises(ValidationError):
            _ok_manifest(id="Qwen-Image-2512")
        with pytest.raises(ValidationError):
            _ok_manifest(id="2512_qwen")

    def test_outputs_required(self):
        with pytest.raises(ValidationError):
            _ok_manifest(outputs=[])

    def test_duplicate_slot_names_rejected(self):
        s1 = _ok_slot("prompt")
        s2 = _ok_slot("prompt")
        with pytest.raises(ValidationError) as exc:
            _ok_manifest(slots=[s1, s2])
        assert "duplicate slot name" in str(exc.value).lower()

    def test_duplicate_action_ids_rejected(self):
        a = Action(id="upscale", label="Up", target_workflow="up", map=[])
        b = Action(id="upscale", label="Up2", target_workflow="up", map=[])
        with pytest.raises(ValidationError) as exc:
            _ok_manifest(actions=[a, b])
        assert "duplicate action id" in str(exc.value).lower()

    def test_slots_by_name(self):
        m = _ok_manifest(
            slots=[_ok_slot("prompt"), _ok_slot("seed", role=Role.SEED)]
        )
        d = m.slots_by_name()
        assert set(d) == {"prompt", "seed"}


class TestSlot:
    def test_slot_must_have_target_or_targets(self):
        with pytest.raises(ValidationError) as exc:
            Slot(
                name="x",
                type=SlotType.TEXT,
                role=Role.PROMPT_POSITIVE,
                ui=SlotUI(hint=UIHint.LONG_TEXT, label="X"),
            )
        assert "target" in str(exc.value).lower()

    def test_slot_target_and_targets_mutually_exclusive(self):
        with pytest.raises(ValidationError):
            Slot(
                name="x",
                type=SlotType.TEXT,
                role=Role.PROMPT_POSITIVE,
                target=Target(node="1", field="a"),
                targets=[Target(node="2", field="b")],
                ui=SlotUI(hint=UIHint.LONG_TEXT, label="X"),
            )

    def test_enum_dynamic_requires_options_from(self):
        with pytest.raises(ValidationError):
            Slot(
                name="lora",
                type=SlotType.ENUM_DYNAMIC,
                role=Role.LORA,
                target=Target(node="122", field="lora_name"),
                ui=SlotUI(hint=UIHint.SELECT, label="LoRA"),
            )

    def test_enum_static_requires_options(self):
        with pytest.raises(ValidationError):
            Slot(
                name="kind",
                type=SlotType.ENUM_STATIC,
                role=Role.SAMPLER_NAME,
                target=Target(node="8", field="sampler_name"),
                ui=SlotUI(hint=UIHint.SELECT_STATIC, label="Sampler"),
            )

    def test_resolved_targets_handles_both_forms(self):
        single = Slot(
            name="a",
            type=SlotType.TEXT,
            role=Role.PROMPT_POSITIVE,
            target=Target(node="1", field="text"),
            ui=SlotUI(hint=UIHint.LONG_TEXT, label="X"),
        )
        multi = Slot(
            name="b",
            type=SlotType.SEED,
            role=Role.SEED,
            targets=[Target(node="8", field="seed"), Target(node="14", field="seed")],
            ui=SlotUI(hint=UIHint.SEED, label="Seed"),
        )
        assert [t.node for t in single.resolved_targets()] == ["1"]
        assert [t.node for t in multi.resolved_targets()] == ["8", "14"]


class TestRequires:
    def test_requires_defaults_empty_lists(self):
        r = Requires()
        assert r.unets == [] == r.vaes == r.clips == r.loras
        assert r.packs == [] == r.checkpoints == r.upscale_models

    def test_requires_extra_keys_rejected(self):
        with pytest.raises(ValidationError):
            Requires.model_validate({"unets": [], "wat": []})


class TestAction:
    def test_action_with_map(self):
        a = Action(
            id="upscale",
            label="Upscale",
            target_workflow="image_upscale_latent",
            map=[ActionMap(from_output=Role.OUTPUT_IMAGE, to_slot="source_image")],
        )
        assert a.id == "upscale"
        assert a.map[0].to_slot == "source_image"
