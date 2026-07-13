# IOT-T051 Agent Advisory Review

> Scope: M2 human review preparation. This document is an agent advisory review only. It is not a `HUMAN_APPROVED` review record, does not prove factual correctness, and must not be used to promote `source_status` or `review_status`.

## Decision

No blocking findings for preparing a human review packet.

The current M2 state is correctly parked at `PARKED_HUMAN_EVIDENCE`: structural coverage and deployed-site acceptance are documented, while factual claim verification and independent human approval remain missing.

## Evidence Checked

- `README.md` and `ROADMAP.md` state that AI assistance cannot grant `VERIFIED` or `HUMAN_APPROVED`.
- `docs/progress.md` states that M2 remains blocked on `CONTENT_AUTHOR`, `FACT_AUDITOR`, locked `critical_claim_ids`, `CLAIM_VERIFICATION`, and independent human approver evidence.
- `data/content-inventory.json` reports `source_audited_files=0`, `PARTIAL=0`, and `VERIFIED=0`.
- `data/deploy-acceptance.yml` records Pages acceptance for the earlier deployed SHA, but explicitly keeps trust counts at zero.
- `data/trust-authorities.yml` contains structural-auditor authority only; it does not authorize a content author, fact auditor, or human approver.

## Boundary Findings

1. Agent review cannot substitute for human review.
   - Required next evidence: a real human reviewer identity in the authority registry and an independent review record that binds the current body hash.

2. Structural audits cannot substitute for claim verification.
   - Required next evidence: at least one `CLAIM_VERIFICATION` source audit covering locked critical claims.

3. `IN_REVIEW` legacy state cannot substitute for approval.
   - Required next evidence: an evidence-bound review record; current `review_records=0`.

## Recommended Human Review Gate

A human reviewer should only approve after all of the following are true:

- A target content item is selected and its current `body_sha256` is frozen.
- `CONTENT_AUTHOR` authority exists for the content item.
- `critical_claim_ids` are locked before fact review starts.
- A `FACT_AUDITOR` independently verifies the selected claims through `CLAIM_VERIFICATION`.
- A separate `HUMAN` approver reviews the verified evidence and writes a review record that references the active audit IDs.

Until those conditions exist, M2 should remain `PARKED_HUMAN_EVIDENCE`.
