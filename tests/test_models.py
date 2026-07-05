"""Tests for agent_action_manifest models."""

import pytest
from pydantic import ValidationError

from agent_action_manifest.models import (
    ActionType,
    AgentActionManifest,
    AuthorityRequirement,
    DefaultAction,
    PayloadPolicy,
    RedactionHint,
    RelianceRequirement,
    RelianceType,
    ReviewMode,
    ReviewRequirement,
    ToolAction,
    ToolDefinition,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
)


def _minimal_manifest() -> dict:
    return {
        "manifest_version": "1.0",
        "manifest_id": "test-manifest-001",
        "agent_name": "Test Agent",
    }


def _full_action() -> dict:
    return {
        "action_name": "do_thing",
        "tool_name": "some_tool",
        "action_type": "read",
        "description": "Does a thing.",
        "authority_required": [
            {"scope": "thing.read", "description": "Read scope", "required": True}
        ],
        "review_requirement": {"mode": "human_review", "reviewer_role": "admin"},
        "reliance_requirement": {
            "required": True,
            "allowed_source_types": ["database"],
        },
        "payload_policy": {
            "required_fields": ["id"],
            "optional_fields": ["extra"],
            "sensitive_fields": ["id"],
            "forbidden_fields": [],
        },
        "redaction_hints": [
            {"field_path": "id", "reason": "Sensitive", "replacement": "[REDACTED]"}
        ],
        "tags": ["read"],
        "metadata": {"custom": "value"},
    }


class TestMinimalManifest:
    def test_loads_successfully(self):
        manifest = AgentActionManifest.model_validate(_minimal_manifest())
        assert manifest.manifest_version == "1.0"
        assert manifest.manifest_id == "test-manifest-001"
        assert manifest.agent_name == "Test Agent"

    def test_default_values(self):
        manifest = AgentActionManifest.model_validate(_minimal_manifest())
        assert manifest.default_action == DefaultAction.escalate
        assert manifest.environment == "development"
        assert manifest.tools == []
        assert manifest.actions == []
        assert manifest.metadata == {}
        assert manifest.owner is None
        assert manifest.agent_description is None

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            AgentActionManifest.model_validate({"manifest_version": "1.0", "agent_name": "X"})

    def test_missing_agent_name_raises(self):
        with pytest.raises(ValidationError):
            AgentActionManifest.model_validate(
                {"manifest_version": "1.0", "manifest_id": "x"}
            )


class TestFullManifest:
    def test_loads_with_tools_and_actions(self):
        data = _minimal_manifest()
        data["tools"] = [{"tool_name": "some_tool", "description": "A tool"}]
        data["actions"] = [_full_action()]
        manifest = AgentActionManifest.model_validate(data)
        assert len(manifest.tools) == 1
        assert len(manifest.actions) == 1
        assert manifest.actions[0].action_name == "do_thing"

    def test_tool_definition_defaults(self):
        tool = ToolDefinition.model_validate({"tool_name": "my_tool"})
        assert tool.allowed is True
        assert tool.external_system is None
        assert tool.data_classification is None

    def test_tool_action_defaults(self):
        action = ToolAction.model_validate(
            {"action_name": "act", "tool_name": "t", "action_type": "read"}
        )
        assert action.authority_required == []
        assert action.redaction_hints == []
        assert action.tags == []
        assert action.metadata == {}
        assert action.default_action is None

    def test_full_action_loads(self):
        action = ToolAction.model_validate(_full_action())
        assert action.action_type == ActionType.read
        assert len(action.authority_required) == 1
        assert action.review_requirement is not None
        assert action.review_requirement.mode == ReviewMode.human_review
        assert action.reliance_requirement is not None
        assert action.payload_policy is not None


class TestEnumValidation:
    def test_valid_action_types(self):
        for value in ["read", "write", "external_send", "delete", "export", "purchase", "approve", "escalate", "other"]:
            a = ToolAction.model_validate(
                {"action_name": "x", "tool_name": "t", "action_type": value}
            )
            assert a.action_type.value == value

    def test_invalid_action_type_raises(self):
        with pytest.raises(ValidationError):
            ToolAction.model_validate(
                {"action_name": "x", "tool_name": "t", "action_type": "invalid_type"}
            )

    def test_valid_default_actions(self):
        for value in ["allow", "block", "escalate"]:
            m = AgentActionManifest.model_validate(
                {**_minimal_manifest(), "default_action": value}
            )
            assert m.default_action.value == value

    def test_valid_review_modes(self):
        for mode in ["none", "human_review", "approval_required", "draft_first"]:
            r = ReviewRequirement.model_validate({"mode": mode})
            assert r.mode.value == mode

    def test_valid_reliance_types(self):
        for rt in ["tool", "database", "file", "api", "user_input", "model_output", "other"]:
            req = RelianceRequirement.model_validate({"allowed_source_types": [rt]})
            assert req.allowed_source_types[0].value == rt

    def test_valid_validation_severities(self):
        for sev in ["error", "warning"]:
            issue = ValidationIssue.model_validate(
                {"severity": sev, "code": "X001", "message": "test"}
            )
            assert issue.severity.value == sev

    def test_validation_issue_alias_defaults_to_none(self):
        issue = ValidationIssue.model_validate(
            {"severity": "error", "code": "X001", "message": "test"}
        )
        assert issue.alias is None


class TestValidationReportModel:
    def test_valid_report(self):
        report = ValidationReport.model_validate(
            {"valid": True, "manifest_id": "x", "issues": []}
        )
        assert report.valid is True
        assert report.issues == []

    def test_report_with_issues(self):
        report = ValidationReport.model_validate(
            {
                "valid": False,
                "manifest_id": "x",
                "issues": [
                    {
                        "severity": "error",
                        "code": "E001",
                        "alias": "manifest_version_missing",
                        "message": "problem",
                        "path": "field",
                    }
                ],
            }
        )
        assert report.valid is False
        assert len(report.issues) == 1
        assert report.issues[0].code == "E001"
        assert report.issues[0].alias == "manifest_version_missing"
