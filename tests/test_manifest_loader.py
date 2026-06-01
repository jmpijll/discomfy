"""Tests for core.manifest.loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.manifest.loader import (
    ManifestLoadError,
    load_manifest,
    load_manifest_directory,
)


VALID_YAML = """
schema_version: 1
id: minimal
name: "Minimal"
modality: image_t2i
workflow_file: workflows/minimal.json
outputs:
  - { role: output_image, node: "1", media: image/png }
slots: []
"""


class TestLoadManifest:
    def test_loads_valid_yaml(self, tmp_path: Path):
        p = tmp_path / "m.yaml"
        p.write_text(VALID_YAML)
        m = load_manifest(p)
        assert m.id == "minimal"
        assert m.outputs[0].node == "1"

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(ManifestLoadError) as exc:
            load_manifest(tmp_path / "nope.yaml")
        assert "not found" in str(exc.value)

    def test_empty_file_raises(self, tmp_path: Path):
        p = tmp_path / "empty.yaml"
        p.write_text("")
        with pytest.raises(ManifestLoadError) as exc:
            load_manifest(p)
        assert "empty" in str(exc.value).lower()

    def test_yaml_parse_error_raises(self, tmp_path: Path):
        p = tmp_path / "bad.yaml"
        p.write_text("{not: valid: yaml: at all")
        with pytest.raises(ManifestLoadError) as exc:
            load_manifest(p)
        assert "yaml parse error" in str(exc.value).lower()

    def test_non_mapping_top_level_raises(self, tmp_path: Path):
        p = tmp_path / "list.yaml"
        p.write_text("- one\n- two\n")
        with pytest.raises(ManifestLoadError) as exc:
            load_manifest(p)
        assert "mapping" in str(exc.value).lower()

    def test_schema_validation_error_wrapped(self, tmp_path: Path):
        p = tmp_path / "bad_schema.yaml"
        p.write_text("schema_version: 99\nid: x\nname: X\nmodality: image_t2i\nworkflow_file: w.json\noutputs: [{role: output_image, node: \"1\", media: image/png}]\n")
        with pytest.raises(ManifestLoadError) as exc:
            load_manifest(p)
        assert "validation" in str(exc.value).lower()


class TestLoadManifestDirectory:
    def test_loads_multiple_manifests(self, tmp_path: Path):
        for name in ("a", "b"):
            p = tmp_path / f"{name}.yaml"
            p.write_text(VALID_YAML.replace("minimal", name))
        loaded, errors = load_manifest_directory(tmp_path)
        assert {m.id for m in loaded} == {"a", "b"}
        assert errors == []

    def test_collects_errors_without_crashing(self, tmp_path: Path):
        good = tmp_path / "good.yaml"
        good.write_text(VALID_YAML.replace("minimal", "good"))
        bad = tmp_path / "bad.yaml"
        bad.write_text("schema_version: 99\n")
        loaded, errors = load_manifest_directory(tmp_path)
        assert {m.id for m in loaded} == {"good"}
        assert len(errors) == 1
        assert "bad.yaml" in str(errors[0])

    def test_duplicate_ids_one_loaded_one_errored(self, tmp_path: Path):
        for name in ("first", "second"):
            p = tmp_path / f"{name}.yaml"
            p.write_text(VALID_YAML)  # both have id=minimal
        loaded, errors = load_manifest_directory(tmp_path)
        assert len(loaded) == 1
        assert any("duplicate manifest id" in str(e) for e in errors)

    def test_missing_directory_raises(self, tmp_path: Path):
        with pytest.raises(ManifestLoadError):
            load_manifest_directory(tmp_path / "does-not-exist")

    def test_real_qwen_manifest_loads(self):
        m = load_manifest("workflows/manifests/qwen_image_2512.yaml")
        assert m.id == "qwen_image_2512"
        assert m.modality.value == "image_t2i"
        assert any(s.name == "prompt" for s in m.slots)
        assert any(s.name == "lora" for s in m.slots)
        seed = next(s for s in m.slots if s.name == "seed")
        assert len(seed.resolved_targets()) == 2
