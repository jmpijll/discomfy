"""Load Manifest YAML files from disk.

Validation lives in `schema.py`; this module is just `path -> Manifest`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import ValidationError

from core.manifest.schema import Manifest

logger = logging.getLogger(__name__)


class ManifestLoadError(Exception):
    """A manifest file failed to load. Wraps the underlying cause."""

    def __init__(self, path: Path, message: str, cause: Exception | None = None):
        self.path = path
        self.cause = cause
        super().__init__(f"{path}: {message}")


def load_manifest(path: str | Path) -> Manifest:
    """Read a single manifest YAML, validate it, return a Manifest.

    Raises ManifestLoadError on file/parse/validation errors.
    """
    p = Path(path)
    if not p.is_file():
        raise ManifestLoadError(p, "file not found")
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as e:
        raise ManifestLoadError(p, "could not read", e) from e
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ManifestLoadError(p, f"YAML parse error: {e}", e) from e
    if data is None:
        raise ManifestLoadError(p, "manifest is empty")
    if not isinstance(data, dict):
        raise ManifestLoadError(
            p, f"top-level must be a mapping, got {type(data).__name__}"
        )
    try:
        return Manifest.model_validate(data)
    except ValidationError as e:
        raise ManifestLoadError(p, f"schema validation failed: {e}", e) from e


def load_manifest_directory(directory: str | Path) -> tuple[list[Manifest], list[ManifestLoadError]]:
    """Load every `*.yaml` / `*.yml` under `directory`.

    Returns (loaded_manifests, errors). A manifest that fails to load
    appears in `errors` and not in `loaded_manifests`; the bot should
    log each error and disable the affected manifest.
    """
    d = Path(directory)
    if not d.is_dir():
        raise ManifestLoadError(d, "manifests directory not found")
    paths = sorted(p for p in d.iterdir() if p.suffix in (".yaml", ".yml"))
    loaded: list[Manifest] = []
    errors: list[ManifestLoadError] = []
    for path in paths:
        try:
            loaded.append(load_manifest(path))
        except ManifestLoadError as e:
            logger.warning("manifest disabled: %s", e)
            errors.append(e)
    ids: dict[str, Path] = {}
    deduped: list[Manifest] = []
    for m in loaded:
        if m.id in ids:
            errors.append(
                ManifestLoadError(
                    d / f"{m.id}.yaml",
                    f"duplicate manifest id '{m.id}' (already loaded from {ids[m.id]})",
                )
            )
            continue
        ids[m.id] = d / f"{m.id}.yaml"
        deduped.append(m)
    return deduped, errors


__all__ = ["ManifestLoadError", "load_manifest", "load_manifest_directory"]
