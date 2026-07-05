"""
Loader for Agent Action Manifests.

Handles reading, parsing, and writing manifest files.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .models import AgentActionManifest


class ManifestLoadError(Exception):
    """Raised when a manifest cannot be loaded."""


def load_manifest(path: str | Path) -> AgentActionManifest:
    """Load and parse an AgentActionManifest from a JSON file.

    Raises:
        ManifestLoadError: if the file is not found, JSON is invalid, or the
            data does not conform to the AgentActionManifest schema.
    """
    path = Path(path)
    if not path.exists():
        raise ManifestLoadError(f"Manifest file not found: {path}")

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestLoadError(f"Could not read manifest file '{path}': {exc}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ManifestLoadError(
            f"Invalid JSON in manifest file '{path}': {exc}"
        ) from exc

    return load_manifest_json(payload)


def load_manifest_json(payload: dict) -> AgentActionManifest:
    """Parse and validate an AgentActionManifest from a dict.

    Raises:
        ManifestLoadError: if the data does not conform to the AgentActionManifest schema.
    """
    try:
        return AgentActionManifest.model_validate(payload)
    except ValidationError as exc:
        raise ManifestLoadError(
            f"Manifest data failed schema validation:\n{exc}"
        ) from exc


def dump_manifest(manifest: AgentActionManifest, path: str | Path) -> Path:
    """Serialize an AgentActionManifest to a JSON file.

    Returns:
        The resolved Path that was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = manifest.model_dump(mode="json")
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path
