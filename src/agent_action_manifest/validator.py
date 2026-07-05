"""
Validator for Agent Action Manifests.

Implements all validation rules and returns a ValidationReport.
"""

from __future__ import annotations

from .models import (
    ActionType,
    AgentActionManifest,
    DefaultAction,
    ReviewMode,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
)


def _error(
    code: str,
    message: str,
    path: str | None = None,
    alias: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        severity=ValidationSeverity.error,
        code=code,
        alias=alias,
        message=message,
        path=path,
    )


def _warning(
    code: str,
    message: str,
    path: str | None = None,
    alias: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        severity=ValidationSeverity.warning,
        code=code,
        alias=alias,
        message=message,
        path=path,
    )


def validate_manifest(manifest: AgentActionManifest) -> ValidationReport:
    """Validate an AgentActionManifest and return a ValidationReport."""
    issues: list[ValidationIssue] = []

    # --- Errors ---

    # 1. manifest_version must be non-empty
    if not manifest.manifest_version or not manifest.manifest_version.strip():
        issues.append(_error("E001", "manifest_version must be non-empty.", "manifest_version"))

    # 2. manifest_id must be non-empty
    if not manifest.manifest_id or not manifest.manifest_id.strip():
        issues.append(_error("E002", "manifest_id must be non-empty.", "manifest_id"))

    # 3. agent_name must be non-empty
    if not manifest.agent_name or not manifest.agent_name.strip():
        issues.append(_error("E003", "agent_name must be non-empty.", "agent_name"))

    # 4. action_name values must be unique
    action_names: list[str] = [a.action_name for a in manifest.actions]
    seen_action_names: set[str] = set()
    for name in action_names:
        if name in seen_action_names:
            issues.append(
                _error(
                    "E004",
                    f"Duplicate action_name: '{name}'.",
                    "actions",
                    alias="duplicate_action_name",
                )
            )
        seen_action_names.add(name)

    # 5. tool_name values in tools must be unique
    tool_names: list[str] = [t.tool_name for t in manifest.tools]
    seen_tool_names: set[str] = set()
    for name in tool_names:
        if name in seen_tool_names:
            issues.append(
                _error(
                    "E005",
                    f"Duplicate tool_name in tools: '{name}'.",
                    "tools",
                    alias="duplicate_tool_name",
                )
            )
        seen_tool_names.add(name)

    declared_tool_names: set[str] = {t.tool_name for t in manifest.tools}
    tools_by_name = {tool.tool_name: tool for tool in manifest.tools}

    for i, action in enumerate(manifest.actions):
        path_prefix = f"actions[{i}]({action.action_name})"

        # Determine effective default_action for this action
        effective_default = action.default_action or manifest.default_action

        # 6. every ToolAction.tool_name must reference a declared ToolDefinition.tool_name
        if action.tool_name not in declared_tool_names:
            issues.append(
                _error(
                    "E006",
                    f"Action '{action.action_name}' references undeclared tool '{action.tool_name}'.",
                    f"{path_prefix}.tool_name",
                    alias="unknown_tool_reference",
                )
            )
        elif (
            not tools_by_name[action.tool_name].allowed
            and effective_default != DefaultAction.block
        ):
            issues.append(
                _error(
                    "E015",
                    f"Action '{action.action_name}' references tool '{action.tool_name}', "
                    "but that tool is marked not allowed. Block the action by default or "
                    "reference an allowed tool.",
                    f"{path_prefix}.tool_name",
                    alias="disallowed_tool_reference",
                )
            )

        # 7. external_send must have authority unless blocked
        if (
            action.action_type == ActionType.external_send
            and not action.authority_required
            and effective_default != DefaultAction.block
        ):
            issues.append(
                _error(
                    "E007",
                    f"Action '{action.action_name}' has action_type 'external_send' but no "
                    "authority_required entries (and is not blocked by default).",
                    f"{path_prefix}.authority_required",
                    alias="external_send_missing_authority",
                )
            )

        # 8. write/delete/purchase/approve must have authority unless blocked
        if (
            action.action_type in {ActionType.write, ActionType.delete, ActionType.purchase, ActionType.approve}
            and not action.authority_required
            and effective_default != DefaultAction.block
        ):
            issues.append(
                _error(
                    "E008",
                    f"Action '{action.action_name}' has action_type '{action.action_type.value}' but "
                    "no authority_required entries (and is not blocked by default).",
                    f"{path_prefix}.authority_required",
                )
            )

        # 9 & 10. PayloadPolicy forbidden field overlaps
        if action.payload_policy is not None:
            pp = action.payload_policy
            forbidden_set = set(pp.forbidden_fields)
            required_set = set(pp.required_fields)
            optional_set = set(pp.optional_fields)

            overlap_required = forbidden_set & required_set
            if overlap_required:
                issues.append(
                    _error(
                        "E009",
                        f"Action '{action.action_name}' payload_policy has forbidden_fields that "
                        f"overlap with required_fields: {sorted(overlap_required)}.",
                        f"{path_prefix}.payload_policy",
                    )
                )

            overlap_optional = forbidden_set & optional_set
            if overlap_optional:
                issues.append(
                    _error(
                        "E010",
                        f"Action '{action.action_name}' payload_policy has forbidden_fields that "
                        f"overlap with optional_fields: {sorted(overlap_optional)}.",
                        f"{path_prefix}.payload_policy",
                    )
                )

            # 11. sensitive_fields should refer to required or optional fields
            if pp.required_fields or pp.optional_fields:
                allowed_fields = required_set | optional_set
                unknown_sensitive = set(pp.sensitive_fields) - allowed_fields
                if unknown_sensitive:
                    issues.append(
                        _error(
                            "E011",
                            f"Action '{action.action_name}' payload_policy has sensitive_fields "
                            f"not listed in required_fields or optional_fields: {sorted(unknown_sensitive)}.",
                            f"{path_prefix}.payload_policy.sensitive_fields",
                        )
                    )

        # 12. RedactionHint.field_path must be non-empty
        for j, hint in enumerate(action.redaction_hints):
            if not hint.field_path or not hint.field_path.strip():
                issues.append(
                    _error(
                        "E012",
                        f"Action '{action.action_name}' has a RedactionHint with an empty field_path.",
                        f"{path_prefix}.redaction_hints[{j}].field_path",
                    )
                )

        # 13. approval_required requires reviewer_role
        if action.review_requirement is not None:
            if (
                action.review_requirement.mode == ReviewMode.approval_required
                and not action.review_requirement.reviewer_role
            ):
                issues.append(
                    _error(
                        "E013",
                        f"Action '{action.action_name}' has review_requirement.mode "
                        "'approval_required' but reviewer_role is not set.",
                        f"{path_prefix}.review_requirement.reviewer_role",
                        alias="approval_missing_reviewer_role",
                    )
                )

        # 14. default_action "allow" for high-risk types requires authority and non-none review
        high_risk_types = {ActionType.external_send, ActionType.delete, ActionType.purchase, ActionType.approve}
        if (
            effective_default == DefaultAction.allow
            and action.action_type in high_risk_types
        ):
            missing_authority = not action.authority_required
            review_mode = (
                action.review_requirement.mode
                if action.review_requirement
                else ReviewMode.none
            )
            missing_review = review_mode == ReviewMode.none
            if missing_authority or missing_review:
                parts = []
                if missing_authority:
                    parts.append("authority_required")
                if missing_review:
                    parts.append("review_requirement.mode != 'none'")
                issues.append(
                    _error(
                        "E014",
                        f"Action '{action.action_name}' has default_action 'allow' for "
                        f"high-risk action_type '{action.action_type.value}' but is missing: "
                        + ", ".join(parts) + ".",
                        path_prefix,
                        alias="high_risk_action_missing_authority",
                    )
                )

    # --- Warnings ---

    # W001. manifest has no actions
    if not manifest.actions:
        issues.append(_warning("W001", "Manifest has no actions.", "actions"))

    # W002. manifest has no tools
    if not manifest.tools:
        issues.append(_warning("W002", "Manifest has no tools.", "tools"))

    # W003. default_action is "allow"
    if manifest.default_action == DefaultAction.allow:
        issues.append(
            _warning("W003", "Manifest default_action is 'allow'.", "default_action")
        )

    # W010. owner is missing
    if not manifest.owner:
        issues.append(_warning("W010", "Manifest owner is not set.", "owner"))

    for i, action in enumerate(manifest.actions):
        path_prefix = f"actions[{i}]({action.action_name})"
        effective_default = action.default_action or manifest.default_action

        # W004. action default_action is "allow" for write or external_send
        if (
            effective_default == DefaultAction.allow
            and action.action_type in {ActionType.write, ActionType.external_send}
        ):
            issues.append(
                _warning(
                    "W004",
                    f"Action '{action.action_name}' has effective default_action 'allow' "
                    f"for action_type '{action.action_type.value}'.",
                    path_prefix,
                )
            )

        # W005. reliance_requirement missing for read, export, external_send
        if (
            action.action_type in {ActionType.read, ActionType.export, ActionType.external_send}
            and action.reliance_requirement is None
        ):
            issues.append(
                _warning(
                    "W005",
                    f"Action '{action.action_name}' has action_type '{action.action_type.value}' "
                    "but no reliance_requirement is declared.",
                    f"{path_prefix}.reliance_requirement",
                )
            )

        # W006. payload_policy missing for write, external_send, delete, export, purchase, approve
        high_payload_types = {
            ActionType.write,
            ActionType.external_send,
            ActionType.delete,
            ActionType.export,
            ActionType.purchase,
            ActionType.approve,
        }
        if action.action_type in high_payload_types and action.payload_policy is None:
            issues.append(
                _warning(
                    "W006",
                    f"Action '{action.action_name}' has action_type '{action.action_type.value}' "
                    "but no payload_policy is declared.",
                    f"{path_prefix}.payload_policy",
                )
            )

        # W007. sensitive_fields present but redaction_hints empty
        if (
            action.payload_policy is not None
            and action.payload_policy.sensitive_fields
            and not action.redaction_hints
        ):
            issues.append(
                _warning(
                    "W007",
                    f"Action '{action.action_name}' has sensitive_fields but no redaction_hints.",
                    f"{path_prefix}.redaction_hints",
                )
            )

        # W009. action has no description
        if not action.description:
            issues.append(
                _warning(
                    "W009",
                    f"Action '{action.action_name}' has no description.",
                    f"{path_prefix}.description",
                )
            )

    # W008. tool data_classification missing for external_system tools
    for j, tool in enumerate(manifest.tools):
        if tool.external_system and not tool.data_classification:
            issues.append(
                _warning(
                    "W008",
                    f"Tool '{tool.tool_name}' has an external_system but no data_classification.",
                    f"tools[{j}]({tool.tool_name}).data_classification",
                )
            )

    has_errors = any(i.severity == ValidationSeverity.error for i in issues)
    return ValidationReport(
        valid=not has_errors,
        manifest_id=manifest.manifest_id if manifest.manifest_id else None,
        issues=issues,
    )
