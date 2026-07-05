# Roadmap

This roadmap outlines the planned direction for Agent Action Manifest.

---

## Near-term

- **Richer action categories** — additional action types for common enterprise scenarios (e.g. `notify`, `schedule`, `query`)
- **Optional manifest-to-policy-config converter** — utility to convert a manifest into configuration for common policy frameworks
- **Manifest diffing** — tooling to compare two versions of a manifest and surface changes in authority, review, or redaction requirements
- **Manifest risk summary** — a risk-profile summary based on action types, authority requirements, and review postures declared in the manifest
- **OpenAPI / tool-schema mapping examples** — examples showing how to align an Agent Action Manifest with OpenAPI specs or LLM tool-call schemas
- **Conformance test suite** — a formal suite of test cases that any validator implementation must pass

---

## Long-term

- **UI editor** — a browser-based editor for creating and editing manifests
- **Registry pattern** — a design for a manifest registry that teams can use to publish and discover agent manifests
- **Integration examples** — end-to-end examples showing how to integrate manifest validation into agent frameworks and deployment pipelines
- **Enterprise governance workflows** — patterns for using manifests in approval workflows, change management, and audit processes

---

## Out of scope

The following are intentionally out of scope for this repository:

- A hosted service or cloud product
- A policy engine or runtime access control system
- An agent framework or model runtime
- A dashboard or reporting UI
- Integration with any specific cloud provider or identity system
