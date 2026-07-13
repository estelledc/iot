# IOT-T051 Human Review Packet

> Purpose: hand off the minimum evidence needed for a real human review. This packet is not itself a review record and does not create `HUMAN_APPROVED`, `VERIFIED`, `PARTIAL`, or `CLAIM_VERIFICATION` state.

## Current M2 State

M2 is parked at `PARKED_HUMAN_EVIDENCE`.

Already completed:

- Progression contract supports non-article goals.
- 29 current valid `STRUCTURAL` source audit records are projected into the inventory.
- Pages acceptance evidence is recorded for the deployed SHA in `data/deploy-acceptance.yml`.

Still missing:

- `CONTENT_AUTHOR` authority for at least one current content item.
- Locked `critical_claim_ids` for the selected content item.
- Independent `FACT_AUDITOR` authority.
- A valid `CLAIM_VERIFICATION` source audit bound to the current body hash.
- Independent `HUMAN` approver authority and a review record linked to active factual audit evidence.

## Reviewer Intake Checklist

The human reviewer should confirm these inputs before review starts:

| Item | Required Evidence | Current State |
| --- | --- | --- |
| Target content item | Repository path and current body hash | Not selected |
| Author authority | `CONTENT_AUTHOR` actor in `data/trust-authorities.yml` | Missing |
| Critical claims | Locked claim IDs and exact claim text | Missing |
| Fact auditor | Independent `FACT_AUDITOR` actor | Missing |
| Factual audit | `CLAIM_VERIFICATION` source audit linked to sources | Missing |
| Human approver | Independent `HUMAN` approver actor | Missing |
| Review record | Schema-valid review record linked to active audit IDs | Missing |

## Minimum Review Flow

1. Select one content item for the first factual review sample.
2. Freeze its current `body_sha256`.
3. Add or verify authority entries for the content author, fact auditor, and human approver.
4. Lock the critical claims before fact checking starts.
5. Create a `CLAIM_VERIFICATION` source audit for the selected claims.
6. Run repository validators and confirm the source projection is `PARTIAL` or `VERIFIED` only when validator output proves it.
7. Ask an independent human approver to review the active audit evidence.
8. Create a review record only after the human approver completes the review.
9. Re-run trust validation and accept `HUMAN_APPROVED` only if the validator projects it from evidence.

## Non-Goals

- Do not use this packet as a review record.
- Do not use agent advisory review as human approval.
- Do not edit article body or frontmatter as part of this preparation packet.
- Do not modify `data/source-audits/`, `data/review-records/`, or `data/trust-authorities.yml` until a separate bounded goal selects the target content and evidence.
- Do not publish v0.3.0 from this packet.

## Handoff Prompt for a Human Reviewer

Use the following prompt after the missing inputs above are available:

```text
Please review the selected IoT Reading Station content item as an independent human approver.

Confirm:
- your reviewer identity and authority are recorded as a HUMAN approver;
- you are independent from the content author and FACT_AUDITOR;
- the linked CLAIM_VERIFICATION audit IDs are active and bind the same current body hash;
- all review checks pass or you are requesting changes with specific reasons.

Do not approve if the factual audit is missing, stale, revoked, superseded, or not linked to the current body hash.
```

## Expected Validator Evidence After Real Review

Before any status promotion is accepted, the repository should show:

- `validate_source_audits.py --all` passes with the new factual audit active.
- `validate_review_records.py --all` passes with the new human review record active.
- `validate_trust_state.py --all --baseline-mode` projects the expected status from evidence.
- `content_inventory.py --check` remains current.

If any validator fails, keep M2 parked and do not publish v0.3.0.
