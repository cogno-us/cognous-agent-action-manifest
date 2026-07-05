# Concepts

This document defines the core concepts used in the Agent Action Manifest schema.

---

## AgentActionManifest

An **AgentActionManifest** is the top-level document. It describes a single AI agent: who owns it, what environment it operates in, what tools it may use, what actions it may propose, and what the default posture should be for any action not individually configured.

A manifest is a declaration, not an enforcement mechanism. It describes what the agent is expected to do so that governance tooling, reviewers, and runtime control systems can make informed decisions.

---

## ToolDefinition

A **ToolDefinition** declares a tool that the agent is permitted to call. Each tool has a name, an optional description, and an `allowed` flag. Tools that communicate with external systems should declare an `external_system` and a `data_classification`.

Tools do not define behavior — they define the inventory of callable capabilities.

---

## ToolAction

A **ToolAction** is a specific action the agent may propose. Each action references a declared tool, has an action type, and carries its own authority, review, reliance, and payload requirements.

Actions are the unit of governance in a manifest. The manifest's `default_action` applies to any action without its own `default_action` override.

---

## AuthorityRequirement

An **AuthorityRequirement** declares that a specific authority scope must be present before an action may be proposed or executed. It names the scope, optionally identifies its source, and marks whether it is strictly required.

Authority requirements are declarations. They do not enforce access control; they document what the agent or integrating system is expected to enforce.

---

## ReviewRequirement

A **ReviewRequirement** declares the review posture for an action. The `mode` field specifies one of:

- `none` — no review is required
- `human_review` — a human must review before execution
- `approval_required` — explicit approval is required; `reviewer_role` must be set
- `draft_first` — the action produces a draft that must be reviewed before sending or execution

---

## RelianceRequirement

A **RelianceRequirement** declares whether the action must record reliance evidence before execution. When `required` is true, the allowed source types must be specified.

Reliance requirements support traceability: they help runtime systems record what data or tool outputs the agent relied upon when proposing an action.

---

## PayloadPolicy

A **PayloadPolicy** declares the field-level rules for an action's input payload:

- `required_fields` — fields that must be present
- `optional_fields` — fields that may optionally be present
- `sensitive_fields` — fields that carry sensitive data and should be subject to access controls
- `forbidden_fields` — fields that must not appear

`forbidden_fields` must not overlap with `required_fields` or `optional_fields`. `sensitive_fields` should be a subset of `required_fields` or `optional_fields` when those lists are non-empty.

---

## RedactionHint

A **RedactionHint** marks a specific field that should be redacted when action records are exported. Each hint specifies a `field_path`, an optional `reason`, and a `replacement` value (default: `[REDACTED]`).

Redaction hints are advisory. They tell downstream export and audit systems which fields to sanitize.

---

## ValidationReport

A **ValidationReport** is returned by the `validate_manifest` function. It contains:

- `valid` — `True` only if no error-severity issues were found
- `manifest_id` — the manifest being reported on
- `issues` — a list of `ValidationIssue` objects, each with a `severity`, `code`, `message`, and optional `path`

Warnings do not make a report invalid. Only errors affect the `valid` flag.
