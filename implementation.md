# Implementation and UAT guide

Brandon Candela · independent synthetic work sample · release 1

## Problem and decision
A fictional fintech wants fewer unnecessary alerts without silently removing review-worthy cases. This lab exposes that tradeoff. Success is not measured by alert reduction alone.

## Scope and assumptions
36 synthetic customers, one account per customer, 177 USD transactions on January 15, 2026. Each customer is assigned to exactly one evaluation scenario. Twelve cases are seeded review-worthy and 24 benign. All names, contexts and labels are fictional. The assignment simplifies evaluation; production systems would monitor multiple overlapping scenarios per customer and need deduplication and case linkage.

## Requirements and data mapping

| Requirement | Mapping / implementation | Acceptance evidence |
|---|---|---|
| Identify the customer | customers.customer_id → accounts.customer_id | Foreign-key test |
| Preserve transaction evidence | transactions.transaction_id; account_id; counterparty_id; direction; amount_cents; occurred_at; currency | Unique IDs, FK integrity, positive integer cents, UTC timestamps |
| Compare activity with CDD profile | expected_daily_cents and business_type | Indexed joins and outbound aggregation |
| Detect rapid movement | Same account, incoming ≥ $5,000, outbound within 90–110% of value, 1 second to selected minutes later | Boundary tests; not proof of fund continuity |
| Detect profile deviation | Daily outbound ≥ expected_daily_cents × selected multiplier | Exact threshold and next-day exclusion tests |
| Detect many-to-one | Distinct incoming counterparties ≥ selected minimum | Repeated sender does not inflate count |
| Evaluate tradeoffs | Customer–scenario unit, fixed authored labels | Baseline 18 alerts: 8 seeded positives, 10 seeded benign; 4 positives missed |
| Review documentation | Assessment, recommendation, threshold snapshot, evidence and history | Local save, QC validation, return/resubmit, export |

## UAT walkthrough
1. Baseline should show 18 alerts, 44% rounded precision, 67% rounded recall and 4 missed seeded cases.
2. Set rapid gap to 5, profile multiplier to 8 and sender minimum to 12. Expect 2 alerts, 0% recall and 12 seeded positives missed. A much smaller queue can be worse.
3. Reset. Open R01 and inspect the transaction IDs and SQL.
4. Attempt to save blank reasoning: validation should prevent submission.
5. Save a named analyst assessment. Attempt QC with the same name: reject it.
6. Accept using a different fictional name and meaningful feedback. Edit the assessment and resubmit: prior QC is superseded and the case returns to Awaiting QC.
7. Change thresholds while a saved case is selected: it must warn about the old configuration, and QC must require resubmission.
8. Reload: saved reviews remain only in this browser. Export a saved case: confirm evidence, query, configuration and history are included.

## Delivery and go-live checklist
- Run `python3 -m unittest discover -s tests` and `node --check dist/app.js`.
- Serve `dist` and exercise sliders, evidence, local persistence, QC and downloads.
- Confirm synthetic-data labels and limitations are visible at desktop and mobile sizes.
- Publish only reviewed source; verify the anonymous public URL loads the database and WASM.
- Rollback: deploy the preceding saved version if an asset or query regression appears.

## Analyst training
Review customer context before acting on a signal. Explain the concern and a plausible benign alternative. Cite transaction IDs. Record missing evidence. An escalation requests more review; it is not a declaration of wrongdoing. QC challenges whether the recommendation is supported and clearly documented.

## Production gaps
No real customer intake, authentication, shared cases, tamper-resistant audit trail, sanctions service, SAR filing, streaming monitoring or production rule calibration. Reviewer names simulate roles and do not prove separate users. Browser storage can be edited or cleared. Metrics depend on authored fixtures, with no claim of real-world predictive accuracy. Customer profile inputs are assumed rather than empirically calibrated. No identity or sanctions clearance is issued. SQL.js 1.13.0 is vendored with its license.

## Interview discussion
Explain why a broad threshold can produce justified business activity, why missing CDD matters, and how you would collect representative adjudicated data before recommending production changes. For a client implementation, discuss requirements discovery, mappings, reconciliation, UAT, analyst training, acceptance criteria, ownership and rollback. Estimate staffing or cost only with explicit handling-time and volume assumptions.
