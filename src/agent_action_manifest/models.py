"""
Pydantic models for the Agent Action Manifest schema.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    read = "read"
    write = "write"
    external_send = "external_send"
    delete = "delete"
    export = "export"
    purchase = "purchase"
    approve = "approve"
    escalate = "escalate"
    other = "other"


class DefaultAction(str, Enum):
    allow = "allow"
    block = "block"
    escalate = "escalate"


class ReviewMode(str, Enum):
    none = "none"
    human_review = "human_review"
    approval_required = "approval_required"
    draft_first = "draft_first"


class RelianceType(str, Enum):
    tool = "tool"
    database = "database"
    file = "file"
    api = "api"
    user_input = "user_input"
    model_output = "model_output"
    other = "other"


class ValidationSeverity(str, Enum):
    error = "error"
    warning = "warning"


class AuthorityRequirement(BaseModel):
    scope: str = Field(description="The authority scope required for this action.")
    description: str | None = Field(
        default=None, description="Human-readable description of the authority requirement."
    )
    required: bool = Field(
        default=True, description="Whether this authority scope is strictly required."
    )
    source: str | None = Field(
        default=None, description="Origin or governing system for the authority scope."
    )


class ReviewRequirement(BaseModel):
    mode: ReviewMode = Field(
        default=ReviewMode.none,
        description="The review posture required before this action may be executed.",
    )
    reviewer_role: str | None = Field(
        default=None,
        description="The role responsible for review when mode is human_review or approval_required.",
    )
    reason: str | None = Field(
        default=None, description="Reason why this review requirement exists."
    )


class RelianceRequirement(BaseModel):
    required: bool = Field(
        default=False,
        description="Whether reliance evidence must be recorded before this action is executed.",
    )
    allowed_source_types: list[RelianceType] = Field(
        default_factory=list,
        description="The types of sources whose outputs may be relied upon for this action.",
    )
    description: str | None = Field(
        default=None, description="Description of the reliance requirement."
    )


class PayloadPolicy(BaseModel):
    required_fields: list[str] = Field(
        default_factory=list, description="Fields that must be present in the action payload."
    )
    optional_fields: list[str] = Field(
        default_factory=list, description="Fields that may optionally appear in the action payload."
    )
    sensitive_fields: list[str] = Field(
        default_factory=list,
        description="Fields considered sensitive and subject to access controls or redaction.",
    )
    forbidden_fields: list[str] = Field(
        default_factory=list,
        description="Fields that must not appear in the action payload.",
    )


class RedactionHint(BaseModel):
    field_path: str = Field(
        description="JSON path or field name to be redacted in exported records."
    )
    reason: str | None = Field(
        default=None, description="Reason for redacting this field."
    )
    replacement: str = Field(
        default="[REDACTED]", description="Replacement value used in redacted output."
    )


class ToolDefinition(BaseModel):
    tool_name: str = Field(description="Unique name identifying this tool.")
    description: str | None = Field(
        default=None, description="Human-readable description of the tool."
    )
    allowed: bool = Field(
        default=True, description="Whether the agent is permitted to call this tool."
    )
    external_system: str | None = Field(
        default=None, description="External system or service that this tool communicates with."
    )
    data_classification: str | None = Field(
        default=None,
        description="Data classification level for data handled or returned by this tool.",
    )


class ToolAction(BaseModel):
    action_name: str = Field(description="Unique name identifying this action.")
    tool_name: str = Field(description="The tool that executes this action.")
    action_type: ActionType = Field(description="The category of action being performed.")
    description: str | None = Field(
        default=None, description="Human-readable description of this action."
    )
    default_action: DefaultAction | None = Field(
        default=None,
        description="Action-level override for the manifest default posture (allow, block, or escalate).",
    )
    authority_required: list[AuthorityRequirement] = Field(
        default_factory=list,
        description="Authority scopes required before this action may be proposed.",
    )
    review_requirement: ReviewRequirement | None = Field(
        default=None,
        description="Review posture required before this action may be executed.",
    )
    reliance_requirement: RelianceRequirement | None = Field(
        default=None,
        description="Reliance evidence requirements for this action.",
    )
    payload_policy: PayloadPolicy | None = Field(
        default=None,
        description="Field-level payload policy for this action's input payload.",
    )
    redaction_hints: list[RedactionHint] = Field(
        default_factory=list,
        description="Fields to be redacted in exported records for this action.",
    )
    tags: list[str] = Field(
        default_factory=list, description="Optional tags for categorising or filtering actions."
    )
    metadata: dict = Field(
        default_factory=dict, description="Arbitrary metadata for this action."
    )


class AgentActionManifest(BaseModel):
    manifest_version: str = Field(description="Schema version for this manifest.")
    manifest_id: str = Field(description="Unique identifier for this manifest instance.")
    agent_name: str = Field(description="Name of the agent described by this manifest.")
    agent_description: str | None = Field(
        default=None, description="Human-readable description of the agent."
    )
    owner: str | None = Field(
        default=None,
        description="Team or individual responsible for this agent manifest.",
    )
    environment: str = Field(
        default="development",
        description="Deployment environment this manifest applies to (e.g. development, staging, production).",
    )
    default_action: DefaultAction = Field(
        default=DefaultAction.escalate,
        description="Manifest-level default posture applied to any action not individually overridden.",
    )
    tools: list[ToolDefinition] = Field(
        default_factory=list,
        description="Tools the agent is permitted to call.",
    )
    actions: list[ToolAction] = Field(
        default_factory=list,
        description="Actions the agent may propose.",
    )
    metadata: dict = Field(
        default_factory=dict, description="Arbitrary metadata for this manifest."
    )


class ValidationIssue(BaseModel):
    severity: ValidationSeverity = Field(
        description="Severity level of this validation issue."
    )
    code: str = Field(description="Stable code string identifying this validation rule.")
    message: str = Field(description="Human-readable description of the validation issue.")
    path: str | None = Field(
        default=None, description="JSON-path-style location of the issue within the manifest."
    )


class ValidationReport(BaseModel):
    valid: bool = Field(
        description="True only when no error-severity issues were found."
    )
    manifest_id: str | None = Field(
        default=None, description="manifest_id of the validated manifest."
    )
    issues: list[ValidationIssue] = Field(
        default_factory=list, description="List of validation issues found."
    )
