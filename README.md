# Agent Action Manifest

**Declare what actions an AI agent may propose before runtime execution.**

Agent Action Manifest is a lightweight public schema and validator for describing the actions an AI agent may propose, the tools it may use, the authority each action requires, the review posture that applies, the reliance evidence expected, and the payload fields that may require redaction.

It is designed for teams moving from agent demos to governed deployment.

It helps answer a simple question:

> What is this agent allowed to propose?

---

This repository is intentionally narrow. It is not an agent framework, not a model runtime, not a policy engine, and not a runtime security boundary. It is a reference format for action inventory and governance preparation.

---

## What it is

Agent Action Manifest is a:

- **Schema** — a structured JSON format for declaring agent actions and their requirements
- **Validator** — a Python library and CLI that validates a manifest against a set of governance rules
- **Reference implementation** — a set of example manifests for common enterprise agent scenarios

It produces a `ValidationReport` that surfaces errors and warnings without executing any code. Each issue keeps its stable numeric code and may also include an optional semantic `alias` for integrations that prefer descriptive identifiers.

---

## Why it matters

Agent teams need to know — before deployment:

- What actions can this agent propose?
- Which tools can it call?
- Which actions require authority?
- Which actions require human review?
- Which actions require reliance records?
- Which payload fields may be sensitive?
- Which fields should be redacted in exported evidence?
- What should happen by default: allow, block, or escalate?

Without a manifest, these questions are answered by reading code, asking developers, or discovering failures in production. A manifest makes the action inventory explicit and auditable before the agent runs.

---

## What a manifest declares

1. The agent being described
2. The tools it may use
3. The actions it may propose
4. Each action's type (read, write, external send, delete, export, purchase, approve, escalate)
5. The authority required for each action
6. Whether review is required (none, human review, approval required, draft first)
7. Whether reliance must be recorded
8. Which payload fields are sensitive
9. Which fields should be redacted in exported records
10. Whether the action is blocked, escalated, or allowed by default

---

## Quickstart

```bash
pip install -e ".[dev]"
pytest
aam validate examples/customer_service_agent.manifest.json
aam summarize examples/customer_service_agent.manifest.json
aam list-actions examples/customer_service_agent.manifest.json
```

---

## Example manifest

```json
{
  "manifest_version": "1.0",
  "manifest_id": "customer-service-agent-v1",
  "agent_name": "Customer Service Agent",
  "owner": "customer-experience-team",
  "environment": "production",
  "default_action": "escalate",
  "tools": [
    {
      "tool_name": "email_tool",
      "description": "Drafts and sends emails to customers.",
      "external_system": "smtp.internal",
      "data_classification": "confidential"
    }
  ],
  "actions": [
    {
      "action_name": "email_send",
      "tool_name": "email_tool",
      "action_type": "external_send",
      "description": "Send an approved email to a customer.",
      "authority_required": [
        {
          "scope": "email.send.customer",
          "description": "Permission to send outbound emails to customers.",
          "required": true
        }
      ],
      "review_requirement": {
        "mode": "approval_required",
        "reviewer_role": "customer-service-supervisor",
        "reason": "All outbound customer emails require supervisor approval."
      },
      "payload_policy": {
        "required_fields": ["to", "subject", "body"],
        "sensitive_fields": ["to", "body"],
        "forbidden_fields": ["bcc"]
      },
      "redaction_hints": [
        {
          "field_path": "to",
          "reason": "Recipient email address must be redacted in exported records."
        }
      ]
    }
  ]
}
```

---

## CLI

```
aam validate examples/customer_service_agent.manifest.json
aam summarize examples/customer_service_agent.manifest.json
aam list-actions examples/customer_service_agent.manifest.json
aam check-examples
```

| Command | Exit code | Description |
|---|---|---|
| `validate` | 0 = valid, 1 = invalid, 2 = error | Validate a manifest and print issues |
| `summarize` | 0 = success | Print a compact summary of the manifest |
| `list-actions` | 0 = success | List all actions with type, posture, authority, and review |
| `check-examples` | 0 = all valid | Validate all `examples/*.manifest.json` files |

---

## Validation rules

### Errors

| Code | Rule |
|---|---|
| E001 | `manifest_version` must be non-empty |
| E002 | `manifest_id` must be non-empty |
| E003 | `agent_name` must be non-empty |
| E004 | `action_name` values must be unique |
| E005 | `tool_name` values in `tools` must be unique |
| E006 | Every action `tool_name` must reference a declared tool |
| E007 | `external_send` actions must have at least one authority requirement unless blocked |
| E008 | `write`, `delete`, `purchase`, and `approve` actions must have authority unless blocked |
| E009 | `forbidden_fields` must not overlap with `required_fields` |
| E010 | `forbidden_fields` must not overlap with `optional_fields` |
| E011 | `sensitive_fields` must reference fields in `required_fields` or `optional_fields` when those lists are non-empty |
| E012 | `RedactionHint.field_path` must be non-empty |
| E013 | `approval_required` mode requires `reviewer_role` to be set |
| E014 | `default_action: allow` for high-risk action types requires authority and non-none review |
| E015 | An action cannot reference a tool marked `allowed: false` unless the action's effective `default_action` is `block` |

Example aliases emitted in `ValidationIssue.alias` include `duplicate_action_name`, `duplicate_tool_name`, `unknown_tool_reference`, `external_send_missing_authority`, `high_risk_action_missing_authority`, `approval_missing_reviewer_role`, and `disallowed_tool_reference`.

### Warnings

| Code | Rule |
|---|---|
| W001 | Manifest has no actions |
| W002 | Manifest has no tools |
| W003 | Manifest `default_action` is `allow` |
| W004 | Action effective `default_action` is `allow` for `write` or `external_send` |
| W005 | `reliance_requirement` missing for `read`, `export`, or `external_send` actions |
| W006 | `payload_policy` missing for `write`, `external_send`, `delete`, `export`, `purchase`, or `approve` actions |
| W007 | `sensitive_fields` are declared but no `redaction_hints` are present |
| W008 | Tool has `external_system` but no `data_classification` |
| W009 | Action has no `description` |
| W010 | Manifest `owner` is not set |

Warnings do not make a manifest invalid. Errors do.

---

## Relationship to Agent Control Plane

Agent Action Manifest declares what an agent may propose.
Agent Control Plane records what the agent actually proposes and how policy decisions were made at runtime.

A manifest is a starting point for governance. It does not replace runtime enforcement, audit logging, or access control.

See [docs/integration_with_agent_control_plane.md](docs/integration_with_agent_control_plane.md) for details.

---

## JSON schemas

JSON Schema Draft 2020-12 schemas are in the `schemas/` directory:

| Schema | Description |
|---|---|
| `agent_action_manifest.schema.json` | Top-level manifest schema |
| `tool_action.schema.json` | Individual action schema |
| `authority_requirement.schema.json` | Authority scope requirement |
| `review_requirement.schema.json` | Review posture requirement |
| `reliance_requirement.schema.json` | Reliance evidence requirement |
| `payload_policy.schema.json` | Field-level payload policy |
| `redaction_hint.schema.json` | Field redaction hint |
| `validation_report.schema.json` | Validation report output |

---

## Examples

Four example manifests are in `examples/`:

| File | Scenario |
|---|---|
| `customer_service_agent.manifest.json` | CRM reads, notes search, email draft and send |
| `internal_research_agent.manifest.json` | Document search, file read, summary, report export |
| `procurement_agent.manifest.json` | Vendor lookup, quote comparison, purchase order, vendor email |
| `finance_workflow_agent.manifest.json` | Invoice read, payment recommendation, payment approval, audit export |

All examples validate with no errors and no warnings.

See [docs/examples.md](docs/examples.md) for details.

---

## Security and scope

This is a schema and validator. It is not a security boundary. It does not enforce runtime access control by itself.

See [SECURITY.md](SECURITY.md) for the full security scope statement.

---

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).

---

## License

Apache 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
