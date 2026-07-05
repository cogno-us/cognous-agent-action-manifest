# Security Policy

## Scope

Agent Action Manifest is a schema definition and validator library.

It is **not a security boundary**. It does not enforce runtime access control by itself.

Declaring an action in a manifest does not prevent that action from being executed. A manifest declares what an agent may propose; it does not enforce what the agent actually does at runtime.

## How to use this safely

Agent Action Manifest should be combined with:

- Application-level authorization and authentication controls
- Runtime policy gates that enforce the declared requirements
- Audit logging and monitoring
- Operational security controls appropriate to your environment

Do not treat a validated manifest as a substitute for runtime enforcement.

## Reporting a vulnerability

If you discover a security vulnerability in this repository, please report it by opening a GitHub Security Advisory or by emailing the repository owner directly.

Please include:

- A description of the vulnerability
- Steps to reproduce
- The potential impact

We will respond as quickly as possible and will credit responsible disclosures.

## Out of scope

- Issues in dependencies (please report to those projects directly)
- Issues in your own manifest declarations or integration code
