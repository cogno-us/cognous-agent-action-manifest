"""Tests for example manifests — all must load and validate with no errors."""

import glob
from pathlib import Path

import pytest

from agent_action_manifest.loader import load_manifest
from agent_action_manifest.models import ValidationSeverity
from agent_action_manifest.validator import validate_manifest


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def _example_paths():
    return sorted(EXAMPLES_DIR.glob("*.manifest.json"))


@pytest.mark.parametrize("path", _example_paths(), ids=lambda p: p.name)
def test_example_loads(path):
    manifest = load_manifest(path)
    assert manifest.manifest_id


@pytest.mark.parametrize("path", _example_paths(), ids=lambda p: p.name)
def test_example_validates_no_errors(path):
    manifest = load_manifest(path)
    report = validate_manifest(manifest)
    errors = [i for i in report.issues if i.severity == ValidationSeverity.error]
    assert errors == [], f"Example {path.name} has validation errors: {errors}"
    assert report.valid is True


@pytest.mark.parametrize("path", _example_paths(), ids=lambda p: p.name)
def test_example_validates_no_warnings(path):
    manifest = load_manifest(path)
    report = validate_manifest(manifest)
    warnings = [i for i in report.issues if i.severity == ValidationSeverity.warning]
    assert warnings == [], f"Example {path.name} has warnings: {[w.message for w in warnings]}"


def test_all_expected_examples_exist():
    expected = [
        "customer_service_agent.manifest.json",
        "internal_research_agent.manifest.json",
        "procurement_agent.manifest.json",
        "finance_workflow_agent.manifest.json",
    ]
    for name in expected:
        path = EXAMPLES_DIR / name
        assert path.exists(), f"Expected example not found: {name}"
