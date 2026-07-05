# Integration with Agent Control Plane

## Overview

Agent Action Manifest and Agent Control Plane are complementary but separate concerns.

**Agent Action Manifest** declares what an agent may propose: the tools it may use, the actions it may propose, the authority each action requires, the review posture that applies, the reliance evidence expected, and the payload fields that may require redaction.

**Agent Control Plane** records what the agent actually proposes at runtime, how policy decisions were made, and produces evidence that supports governance and audit workflows.

This repository implements only the manifest format. It does not implement or depend on Agent Control Plane.

---

## Conceptual flow

```
Agent Action Manifest
  └─ Declares: tools, actions, authority, review, reliance, redaction

  → Agent runtime
      └─ Agent proposes actions within the declared inventory

  → Agent Control Plane
      └─ Records: action proposals, policy decisions, review outcomes

  → Run Record
      └─ Per-execution record of what was proposed and decided

  → Replay Bundle
      └─ Package of run records and supporting evidence

  → Governance Evidence Pack
      └─ Compiled evidence for audit, compliance, or review workflows
```

---

## How a manifest supports runtime governance

At the point where an agent proposes an action:

1. The runtime or control plane can verify that the action is declared in the manifest.
2. The authority requirements can be checked against available authority grants.
3. The review requirement can be enforced: requiring human review, queuing for approval, or producing a draft.
4. The reliance requirement can be satisfied by recording the sources the agent relied upon.
5. The payload policy can be validated before the action proceeds.
6. The redaction hints can be applied when exporting records.

None of this enforcement is implemented in this repository. This repository provides the declaration format so that an integrating system can implement enforcement.

---

## What this repository does not do

- It does not enforce authority at runtime.
- It does not record action proposals or run records.
- It does not communicate with any external system.
- It does not provide a policy engine.
- It does not provide a dashboard or UI.

---

## Integration pattern

A typical integration:

1. Load the manifest at agent startup using `load_manifest`.
2. Validate the manifest using `validate_manifest` to ensure it is well-formed.
3. At runtime, look up the relevant `ToolAction` for each proposed action.
4. Use the `authority_required`, `review_requirement`, `reliance_requirement`, and `payload_policy` fields to drive enforcement in your control plane.
5. Apply `redaction_hints` when exporting records.

The manifest is a starting point for governance — not a substitute for it.
