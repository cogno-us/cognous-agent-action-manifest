"""Tests for agent_action_manifest loader."""

import json
import pytest
from pathlib import Path

from agent_action_manifest.loader import (
    ManifestLoadError,
    dump_manifest,
    load_manifest,
    load_manifest_json,
)
from agent_action_manifest.models import AgentActionManifest


MINIMAL_DATA = {
    "manifest_version": "1.0",
    "manifest_id": "loader-test-001",
    "agent_name": "Loader Test Agent",
}


def _write_manifest(tmp_path: Path, data: dict, filename: str = "manifest.json") -> Path:
    path = tmp_path / filename
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class TestLoadManifest:
    def test_load_valid_manifest_from_file(self, tmp_path):
        path = _write_manifest(tmp_path, MINIMAL_DATA)
        manifest = load_manifest(path)
        assert manifest.manifest_id == "loader-test-001"
        assert manifest.agent_name == "Loader Test Agent"

    def test_load_from_string_path(self, tmp_path):
        path = _write_manifest(tmp_path, MINIMAL_DATA)
        manifest = load_manifest(str(path))
        assert manifest.manifest_id == "loader-test-001"

    def test_file_not_found_raises_manifest_load_error(self, tmp_path):
        with pytest.raises(ManifestLoadError, match="not found"):
            load_manifest(tmp_path / "nonexistent.json")

    def test_invalid_json_raises_manifest_load_error(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ManifestLoadError, match="Invalid JSON"):
            load_manifest(path)

    def test_model_validation_error_raises_manifest_load_error(self, tmp_path):
        bad_data = {"manifest_version": "1.0"}  # missing manifest_id and agent_name
        path = _write_manifest(tmp_path, bad_data)
        with pytest.raises(ManifestLoadError, match="schema validation"):
            load_manifest(path)


class TestLoadManifestJson:
    def test_loads_valid_dict(self):
        manifest = load_manifest_json(MINIMAL_DATA)
        assert isinstance(manifest, AgentActionManifest)
        assert manifest.manifest_id == "loader-test-001"

    def test_invalid_dict_raises_manifest_load_error(self):
        with pytest.raises(ManifestLoadError, match="schema validation"):
            load_manifest_json({"manifest_version": "1.0"})

    def test_non_dict_raises_manifest_load_error(self):
        with pytest.raises(ManifestLoadError):
            load_manifest_json([])  # type: ignore


class TestDumpManifest:
    def test_dump_writes_file(self, tmp_path):
        manifest = AgentActionManifest.model_validate(MINIMAL_DATA)
        out_path = tmp_path / "output.json"
        result = dump_manifest(manifest, out_path)
        assert result == out_path
        assert out_path.exists()

    def test_dump_is_valid_json(self, tmp_path):
        manifest = AgentActionManifest.model_validate(MINIMAL_DATA)
        out_path = tmp_path / "output.json"
        dump_manifest(manifest, out_path)
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["manifest_id"] == "loader-test-001"

    def test_dump_and_reload_roundtrip(self, tmp_path):
        manifest = AgentActionManifest.model_validate(
            {**MINIMAL_DATA, "environment": "staging", "owner": "test-team"}
        )
        out_path = tmp_path / "output.json"
        dump_manifest(manifest, out_path)
        reloaded = load_manifest(out_path)
        assert reloaded.manifest_id == manifest.manifest_id
        assert reloaded.environment == "staging"
        assert reloaded.owner == "test-team"

    def test_dump_creates_parent_directories(self, tmp_path):
        manifest = AgentActionManifest.model_validate(MINIMAL_DATA)
        out_path = tmp_path / "nested" / "dir" / "output.json"
        dump_manifest(manifest, out_path)
        assert out_path.exists()

    def test_dump_uses_indentation(self, tmp_path):
        manifest = AgentActionManifest.model_validate(MINIMAL_DATA)
        out_path = tmp_path / "output.json"
        dump_manifest(manifest, out_path)
        content = out_path.read_text(encoding="utf-8")
        assert "\n" in content
