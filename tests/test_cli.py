"""Tests for agent_action_manifest CLI."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
VALID_EXAMPLE = str(EXAMPLES_DIR / "customer_service_agent.manifest.json")


def _run_aam(*args, cwd=None):
    result = subprocess.run(
        ["aam", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result


def _write_manifest(tmp_path: Path, data: dict, filename: str = "manifest.json") -> Path:
    path = tmp_path / filename
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class TestValidateCommand:
    def test_valid_example_returns_exit_0(self):
        result = _run_aam("validate", VALID_EXAMPLE)
        assert result.returncode == 0
        assert "VALID" in result.stdout

    def test_invalid_manifest_returns_exit_1(self, tmp_path):
        bad_data = {
            "manifest_version": "1.0",
            "manifest_id": "bad-001",
            "agent_name": "Bad Agent",
            "tools": [],
            "actions": [
                {
                    "action_name": "send",
                    "tool_name": "unknown_tool",
                    "action_type": "external_send",
                    "description": "Sends something.",
                }
            ],
        }
        path = _write_manifest(tmp_path, bad_data)
        result = _run_aam("validate", str(path))
        assert result.returncode == 1
        assert "INVALID" in result.stdout

    def test_file_not_found_returns_exit_2(self):
        result = _run_aam("validate", "/nonexistent/path/manifest.json")
        assert result.returncode == 2

    def test_usage_error_no_args_returns_exit_2(self):
        result = _run_aam("validate")
        assert result.returncode == 2

    def test_invalid_json_returns_exit_2(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{bad json", encoding="utf-8")
        result = _run_aam("validate", str(path))
        assert result.returncode == 2


class TestSummarizeCommand:
    def test_valid_example_returns_exit_0(self):
        result = _run_aam("summarize", VALID_EXAMPLE)
        assert result.returncode == 0

    def test_summarize_shows_manifest_id(self):
        result = _run_aam("summarize", VALID_EXAMPLE)
        assert "customer-service-agent-v1" in result.stdout

    def test_summarize_shows_tool_count(self):
        result = _run_aam("summarize", VALID_EXAMPLE)
        assert "3" in result.stdout  # 3 tools in customer_service_agent

    def test_file_not_found_returns_exit_2(self):
        result = _run_aam("summarize", "/nonexistent/path.json")
        assert result.returncode == 2

    def test_usage_error_no_args_returns_exit_2(self):
        result = _run_aam("summarize")
        assert result.returncode == 2


class TestListActionsCommand:
    def test_valid_example_returns_exit_0(self):
        result = _run_aam("list-actions", VALID_EXAMPLE)
        assert result.returncode == 0

    def test_list_actions_shows_action_names(self):
        result = _run_aam("list-actions", VALID_EXAMPLE)
        assert "crm_read" in result.stdout
        assert "email_send" in result.stdout

    def test_list_actions_shows_action_types(self):
        result = _run_aam("list-actions", VALID_EXAMPLE)
        assert "read" in result.stdout
        assert "external_send" in result.stdout

    def test_file_not_found_returns_exit_2(self):
        result = _run_aam("list-actions", "/nonexistent/path.json")
        assert result.returncode == 2

    def test_usage_error_no_args_returns_exit_2(self):
        result = _run_aam("list-actions")
        assert result.returncode == 2


class TestCheckExamplesCommand:
    def test_check_examples_returns_exit_0(self):
        result = _run_aam("check-examples", cwd=str(EXAMPLES_DIR.parent))
        assert result.returncode == 0

    def test_check_examples_shows_valid_for_all(self):
        result = _run_aam("check-examples", cwd=str(EXAMPLES_DIR.parent))
        assert "VALID" in result.stdout


class TestUnknownCommand:
    def test_unknown_command_returns_exit_2(self):
        result = _run_aam("unknown-command")
        assert result.returncode == 2
