"""Tests for agent_action_manifest validator."""

import pytest

from agent_action_manifest.models import (
    AgentActionManifest,
    AuthorityRequirement,
    DefaultAction,
    PayloadPolicy,
    RedactionHint,
    RelianceRequirement,
    ReviewRequirement,
    ToolAction,
    ToolDefinition,
    ValidationSeverity,
)
from agent_action_manifest.validator import validate_manifest


def _base_manifest(**overrides) -> AgentActionManifest:
    data = {
        "manifest_version": "1.0",
        "manifest_id": "validator-test-001",
        "agent_name": "Validator Test Agent",
        "owner": "test-team",
        **overrides,
    }
    return AgentActionManifest.model_validate(data)


def _make_action(
    name: str,
    tool: str,
    action_type: str = "read",
    default_action=None,
    authority=None,
    review=None,
    reliance=None,
    payload=None,
    redactions=None,
) -> ToolAction:
    data = {
        "action_name": name,
        "tool_name": tool,
        "action_type": action_type,
        "description": f"Test action {name}",
    }
    if default_action is not None:
        data["default_action"] = default_action
    if authority is not None:
        data["authority_required"] = authority
    if review is not None:
        data["review_requirement"] = review
    if reliance is not None:
        data["reliance_requirement"] = reliance
    if payload is not None:
        data["payload_policy"] = payload
    if redactions is not None:
        data["redaction_hints"] = redactions
    return ToolAction.model_validate(data)


def _tool(name: str, **kwargs) -> ToolDefinition:
    return ToolDefinition.model_validate({"tool_name": name, **kwargs})


def _authority(scope: str) -> dict:
    return {"scope": scope, "required": True}


def _approval_review() -> dict:
    return {"mode": "approval_required", "reviewer_role": "manager"}


def _human_review() -> dict:
    return {"mode": "human_review", "reviewer_role": "reviewer"}


class TestErrorValidation:
    def test_empty_manifest_version_is_error(self):
        manifest = _base_manifest(manifest_version="")
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E001" in codes
        assert report.valid is False

    def test_empty_manifest_id_is_error(self):
        manifest = _base_manifest(manifest_id="")
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E002" in codes
        assert report.valid is False

    def test_empty_agent_name_is_error(self):
        manifest = _base_manifest(agent_name="")
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E003" in codes

    def test_duplicate_action_names_is_error(self):
        tool = _tool("my_tool")
        action1 = _make_action("same_name", "my_tool")
        action2 = _make_action("same_name", "my_tool")
        manifest = _base_manifest()
        manifest = AgentActionManifest.model_validate(
            manifest.model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action1.model_dump(), action2.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E004" in codes
        aliases = [i.alias for i in report.issues if i.code == "E004"]
        assert "duplicate_action_name" in aliases

    def test_duplicate_tool_names_is_error(self):
        tool1 = _tool("dup_tool")
        tool2 = _tool("dup_tool")
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool1.model_dump(), tool2.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E005" in codes
        aliases = [i.alias for i in report.issues if i.code == "E005"]
        assert "duplicate_tool_name" in aliases

    def test_action_referencing_unknown_tool_is_error(self):
        action = _make_action("act1", "nonexistent_tool")
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E006" in codes
        aliases = [i.alias for i in report.issues if i.code == "E006"]
        assert "unknown_tool_reference" in aliases

    def test_action_referencing_disallowed_tool_is_error(self):
        tool = _tool("disabled_tool", allowed=False)
        action = _make_action("act1", "disabled_tool", default_action="escalate")
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        issues = [i for i in report.issues if i.code == "E015"]
        assert len(issues) == 1
        assert issues[0].alias == "disallowed_tool_reference"

    def test_blocked_action_referencing_disallowed_tool_has_no_e015(self):
        tool = _tool("disabled_tool", allowed=False)
        action = _make_action("act1", "disabled_tool", default_action="block")
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E015" not in codes

    def test_manifest_blocked_action_referencing_disallowed_tool_has_no_e015(self):
        tool = _tool("disabled_tool", allowed=False)
        action = _make_action("act1", "disabled_tool")
        manifest = AgentActionManifest.model_validate(
            _base_manifest(default_action="block").model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E015" not in codes

    def test_external_send_without_authority_is_error(self):
        tool = _tool("ext_tool")
        action = _make_action("send_action", "ext_tool", action_type="external_send")
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E007" in codes
        aliases = [i.alias for i in report.issues if i.code == "E007"]
        assert "external_send_missing_authority" in aliases

    def test_external_send_blocked_no_authority_required_passes_e007(self):
        tool = _tool("ext_tool")
        action = _make_action("send_action", "ext_tool", action_type="external_send", default_action="block")
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E007" not in codes

    @pytest.mark.parametrize("action_type", ["write", "delete", "purchase", "approve"])
    def test_high_risk_action_without_authority_is_error(self, action_type):
        tool = _tool("my_tool")
        action = _make_action("risky_act", "my_tool", action_type=action_type)
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E008" in codes
        issues = [i for i in report.issues if i.code == "E008"]
        assert len(issues) == 1
        assert issues[0].alias == "privileged_action_missing_authority"

    @pytest.mark.parametrize("action_type", ["write", "delete", "purchase", "approve"])
    def test_high_risk_action_blocked_no_authority_passes_e008(self, action_type):
        tool = _tool("my_tool")
        action = _make_action("risky_act", "my_tool", action_type=action_type, default_action="block")
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E008" not in codes

    def test_forbidden_field_overlap_required_is_error(self):
        tool = _tool("my_tool")
        action = _make_action(
            "overlap_act",
            "my_tool",
            action_type="write",
            authority=[_authority("w.write")],
            review=_approval_review(),
            payload={
                "required_fields": ["field_a"],
                "optional_fields": [],
                "sensitive_fields": ["field_a"],
                "forbidden_fields": ["field_a"],
            },
        )
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E009" in codes

    def test_forbidden_field_overlap_optional_is_error(self):
        tool = _tool("my_tool")
        action = _make_action(
            "overlap_act",
            "my_tool",
            action_type="write",
            authority=[_authority("w.write")],
            review=_approval_review(),
            payload={
                "required_fields": [],
                "optional_fields": ["field_b"],
                "sensitive_fields": [],
                "forbidden_fields": ["field_b"],
            },
        )
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E010" in codes

    def test_approval_required_without_reviewer_role_is_error(self):
        tool = _tool("my_tool")
        action = _make_action(
            "appr_act",
            "my_tool",
            action_type="approve",
            authority=[_authority("approve.do")],
            review={"mode": "approval_required"},  # no reviewer_role
        )
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E013" in codes
        aliases = [i.alias for i in report.issues if i.code == "E013"]
        assert "approval_missing_reviewer_role" in aliases

    def test_allow_on_high_risk_without_authority_and_review_is_error(self):
        tool = _tool("ext_tool")
        action = _make_action(
            "risky_allow",
            "ext_tool",
            action_type="external_send",
            default_action="allow",
        )
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.error]
        assert "E014" in codes
        aliases = [i.alias for i in report.issues if i.code == "E014"]
        assert "high_risk_action_missing_authority" in aliases


class TestWarningValidation:
    def test_no_actions_is_warning(self):
        manifest = _base_manifest()
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.warning]
        assert "W001" in codes
        assert report.valid is True

    def test_no_tools_is_warning(self):
        manifest = _base_manifest()
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.warning]
        assert "W002" in codes

    def test_default_allow_manifest_is_warning(self):
        manifest = _base_manifest(default_action="allow")
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.warning]
        assert "W003" in codes
        assert report.valid is True

    def test_warnings_do_not_make_report_invalid(self):
        manifest = _base_manifest()
        report = validate_manifest(manifest)
        has_warnings = any(i.severity == ValidationSeverity.warning for i in report.issues)
        assert has_warnings
        assert report.valid is True

    def test_errors_make_report_invalid(self):
        manifest = _base_manifest(manifest_version="")
        report = validate_manifest(manifest)
        assert report.valid is False

    def test_missing_owner_is_warning(self):
        data = {
            "manifest_version": "1.0",
            "manifest_id": "no-owner-001",
            "agent_name": "No Owner Agent",
        }
        manifest = AgentActionManifest.model_validate(data)
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.warning]
        assert "W010" in codes

    def test_sensitive_fields_without_redaction_is_warning(self):
        tool = _tool("my_tool")
        action = _make_action(
            "sensitive_act",
            "my_tool",
            action_type="write",
            authority=[_authority("w.write")],
            review=_approval_review(),
            payload={
                "required_fields": ["email"],
                "optional_fields": [],
                "sensitive_fields": ["email"],
                "forbidden_fields": [],
            },
            redactions=[],
        )
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.warning]
        assert "W007" in codes

    def test_external_tool_missing_data_classification_is_warning(self):
        tool = _tool("ext_tool", external_system="some.system")
        action = _make_action(
            "send",
            "ext_tool",
            action_type="external_send",
            authority=[_authority("ext.send")],
            review=_approval_review(),
        )
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        codes = [i.code for i in report.issues if i.severity == ValidationSeverity.warning]
        assert "W008" in codes


class TestValidManifest:
    def test_valid_full_manifest_no_errors(self):
        tool = _tool("crm_tool")
        action = _make_action(
            "crm_read",
            "crm_tool",
            action_type="read",
            reliance={"required": True, "allowed_source_types": ["database"]},
            payload={
                "required_fields": ["id"],
                "optional_fields": [],
                "sensitive_fields": ["id"],
                "forbidden_fields": [],
            },
            redactions=[{"field_path": "id", "reason": "PII"}],
        )
        manifest = AgentActionManifest.model_validate(
            _base_manifest().model_dump(mode="json")
            | {"tools": [tool.model_dump()], "actions": [action.model_dump()]}
        )
        report = validate_manifest(manifest)
        errors = [i for i in report.issues if i.severity == ValidationSeverity.error]
        assert errors == []
        assert report.valid is True
