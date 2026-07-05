# Example Manifests

This repository includes four example manifests that demonstrate common agent scenarios. All examples validate with no errors and no warnings.

---

## 1. Customer Service Agent

**File:** `examples/customer_service_agent.manifest.json`

**Scenario:** A customer service agent that reads CRM records, searches customer notes, drafts emails for review, and sends approved emails to customers.

**Actions:**

| Action | Tool | Type | Authority | Review |
|---|---|---|---|---|
| `crm_read` | `crm_tool` | `read` | none | none |
| `notes_search` | `notes_tool` | `read` | none | none |
| `email_draft` | `email_tool` | `write` | none (blocked) | `draft_first` |
| `email_send` | `email_tool` | `external_send` | `email.send.customer` | `approval_required` |

**Key design decisions:**
- `email_draft` is blocked by default; it requires the `draft_first` review mode to produce a draft for review.
- `email_send` requires authority and supervisor approval.
- Both email actions have sensitive field declarations and redaction hints for `to`, `body`, and `customer_id`.

---

## 2. Internal Research Agent

**File:** `examples/internal_research_agent.manifest.json`

**Scenario:** A research agent that searches internal documents, reads files, generates summaries, and exports approved reports.

**Actions:**

| Action | Tool | Type | Authority | Review |
|---|---|---|---|---|
| `document_search` | `document_search_tool` | `read` | none | none |
| `file_read` | `file_read_tool` | `read` | none | none |
| `summary_generate` | `summary_tool` | `write` | `research.summary.write` | `human_review` |
| `report_export` | `export_tool` | `export` | `research.report.export` | `approval_required` |

**Key design decisions:**
- Read actions require reliance recording but no authority.
- Summary generation requires authority and human review by the research lead.
- Report export requires authority and director approval.

---

## 3. Procurement Agent

**File:** `examples/procurement_agent.manifest.json`

**Scenario:** A procurement agent that researches vendors, compares quotes, drafts purchase recommendations, creates approved purchase orders, and sends vendor notifications.

**Actions:**

| Action | Tool | Type | Authority | Review |
|---|---|---|---|---|
| `vendor_lookup` | `vendor_db_tool` | `read` | none | none |
| `quote_compare` | `quote_tool` | `read` | none | none |
| `purchase_recommendation` | `recommendation_tool` | `write` | `procurement.recommendation.write` | `human_review` |
| `purchase_order_create` | `purchase_order_tool` | `purchase` | two scopes | `approval_required` |
| `vendor_email_send` | `vendor_email_tool` | `external_send` | `procurement.vendor.email` | `approval_required` |

**Key design decisions:**
- Purchase order creation requires two authority scopes: procurement and finance.
- Purchase orders declare `unit_price` as sensitive with a redaction hint.
- Vendor emails require authority and manager approval.

---

## 4. Finance Workflow Agent

**File:** `examples/finance_workflow_agent.manifest.json`

**Scenario:** A finance agent that reads invoice records, drafts payment recommendations, approves payments with dual-control authority, and exports audit records.

**Actions:**

| Action | Tool | Type | Authority | Review |
|---|---|---|---|---|
| `invoice_read` | `invoice_tool` | `read` | none | none |
| `payment_recommendation` | `payment_tool` | `write` | `finance.payment.recommend` | `human_review` |
| `payment_approve` | `payment_tool` | `approve` | two scopes | `approval_required` |
| `audit_export` | `audit_tool` | `export` | `finance.audit.export` | `approval_required` |

**Key design decisions:**
- Payment approval requires dual-control authority (two separate authority scopes).
- Payment amounts are marked as sensitive with redaction hints.
- Audit export requires reliance recording across all workflow steps.
- Invoice identifiers are redacted in exported records.
