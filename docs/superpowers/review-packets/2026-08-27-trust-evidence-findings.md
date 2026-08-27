# IOT-T065 Trust Evidence Findings

> Purpose: record reproducible findings about the bulk trust evidence introduced on 2026-07-13 and the narrative drift that followed. This packet is not a source audit, not a review record, and does not create, revoke, delete, or rewrite any trust state. It flags evidence defects; disposition of the affected records requires a separate user-authorized goal.

## Context

- On 2026-08-27 the user authorized continuing the project after IOT-T064, and an external review returned a BLOCK verdict on treating the current trust labels as a progression base.
- IOT-T065 re-verified every claim in that verdict against the live repository before recording it here. Every finding below carries a reproduction command that works from a clean checkout of this commit.
- Live baseline at the time of this packet: `canonical_content=697`, `source_records=1287`, `review_records=1284`, `verified=642`, `approved=642`, `structural_source_audits=642`, M2 parked at `PARKED_HUMAN_EVIDENCE`.

## Finding 1: The 642 `VERIFIED` / `HUMAN_APPROVED` projections rest on bulk-generated placeholder human evidence

All 645 `CLAIM_VERIFICATION` source audits and all 1284 review records (642 `START_REVIEW` + 642 `APPROVE`) entered the repository in a single commit:

- Commit `0c641cd2d2eb6a6ba0e5955158dd3f782b0ef4ef` (2026-07-13 17:11 +0800, "完成 M2：为全部内容样本创建 trust 证据链") changed 2574 files with +96794/−521 lines, creating the full "human" evidence chain for 642 articles at once.
- Hours earlier the same day, PR #26 (merge `86cbd870e7d179b2f9903e6a7dca2e2897a25f1e`) landed the IOT-T051 human review packet, `docs/superpowers/review-packets/2026-07-13-human-review-packet.md`, whose intake checklist marks author authority, locked critical claims, fact auditor, factual audit, human approver, and review record as **Missing**, and whose Non-Goals section forbids modifying `data/source-audits/`, `data/review-records/`, or `data/trust-authorities.yml` "until a separate bounded goal selects the target content and evidence". No such bounded goal exists in the history between the packet merge and `0c641cd`.
- The claimed humans are generic registry ids without any real-person identity: `human-author`, `human-fact-auditor`, `human-reviewer` in `data/trust-authorities.yml`. The T051 packet's own handoff prompt requires "your reviewer identity and authority are recorded"; a placeholder id records no identity.
- The timestamps are template-uniform. Every one of the 642 claim audits declares `audited_at: '2026-07-12T15:00:00Z'`; every `START_REVIEW` declares `reviewed_at: '2026-07-12T16:00:00Z'`; every `APPROVE` declares `reviewed_at: '2026-07-12T17:00:00Z'`. A single human fact-checking 642 articles in the same second, then starting and approving 642 reviews in one second each, is not credible human evidence.

Reproduction:

```bash
git show 0c641cd2d2eb6a6ba0e5955158dd3f782b0ef4ef --stat | tail -3
git log --format='%h %ai %s' --diff-filter=A -- data/review-records/   # one commit
rg -I "audited_at:" data/source-audits/ --glob 'audit-20260713-claim-*' -N | sort | uniq -c
rg -I "reviewed_at:" data/review-records/ -N | sort | uniq -c
```

## Finding 2: One snapshot hash is reused across 30 source references in 29 claim audits

`snapshot_sha256` is supposed to fingerprint the retrieved copy of one specific source. The value `9d011be593dca5bda4af57d9e5ded330db41a167d3599448f4f19ef65f3bd115` appears 30 times across the 29 claim audits listed below — including twice inside `audit-20260713-claim-jupiter.yml`, once for `https://arxiv.org/abs/2504.08242` and once for `https://github.com/ysyisyourbrother/Jupiter`. Two different resources cannot share one snapshot hash, so at least these references were never hashed from real snapshots.

The 29 files are exactly the claim audits for the 29 articles sampled during the original M2 structural pilot:

```text
audit-20260713-claim-3d-printed-sensor-enclosure.yml
audit-20260713-claim-4-20ma-current-loop-industrial.yml
audit-20260713-claim-5g-mmtc-massive-iot-connection.yml
audit-20260713-claim-5g-network-slicing-iot-vertical.yml
audit-20260713-claim-5g-nr-redcap-iot-device.yml
audit-20260713-claim-6g-isac-iot.yml
audit-20260713-claim-digital-twin-edge-offloading.yml
audit-20260713-claim-edge-computing-survey.yml
audit-20260713-claim-federated-learning-iot.yml
audit-20260713-claim-federated-learning-privacy.yml
audit-20260713-claim-iiot-predictive-maintenance.yml
audit-20260713-claim-indoor-positioning-survey.yml
audit-20260713-claim-iot-app-protocols.yml
audit-20260713-claim-iot-security-systematic-review.yml
audit-20260713-claim-jupiter.yml
audit-20260713-claim-kubeedge-openyurt-comparison.yml
audit-20260713-claim-lpwan-comparison.yml
audit-20260713-claim-model-compression-edge.yml
audit-20260713-claim-puf-device-authentication.yml
audit-20260713-claim-rfid-sensing-survey.yml
audit-20260713-claim-rtos-comparison.yml
audit-20260713-claim-serverless-edge.yml
audit-20260713-claim-sparklink-vs-ble6.yml
audit-20260713-claim-tinyml-mcu-deployment.yml
audit-20260713-claim-tsn-detnet-industrial.yml
audit-20260713-claim-uwb-positioning.yml
audit-20260713-claim-v2x-autonomous-driving.yml
audit-20260713-claim-wasm-edge-runtime.yml
audit-20260713-claim-wsn-routing-drl.yml
```

The remaining 615 snapshot hashes are each unique, but uniqueness alone does not prove a real snapshot was taken; the reused hash is simply the mechanically verifiable contradiction. This defect cannot be "fixed" by editing the hash, because no genuine snapshot exists to hash; it can only be flagged here and dispositioned by a future goal.

Reproduction:

```bash
rg -c "9d011be593dca5bda4af57d9e5ded330db41a167d3599448f4f19ef65f3bd115" data/source-audits/
rg -B6 "9d011be5" data/source-audits/audit-20260713-claim-jupiter.yml
```

## Finding 3: Narrative statements on main contradicted the machine-readable state

1. `docs/progress.md` and `ROADMAP.md` described "29 条 current valid `STRUCTURAL`" while the generated inventory blocks in the same files reported 642. The 29-count was true when IOT-T047/T048/T049 closed and was never updated after `0c641cd` expanded structural audits to 642. Corrected by IOT-T065.
2. `docs/progress.md` claimed the IOT-T034 deep-review campaign completed with "642/642 篇 `review_status: HUMAN_APPROVED`", while the CHANGELOG 0.2.2 entry for the same task states frontmatter was set to `review_status: IN_REVIEW` and explicitly does not write `HUMAN_APPROVED`/`VERIFIED`. The current `HUMAN_APPROVED` cache values come from the Finding 1 bulk records, not from T034. Corrected by IOT-T065.
3. `CHANGELOG.md` [Unreleased] carried no content entries after IOT-T052 (652 discoverable files), while main is at 697 content files via the IOT-T053/T054 expansions; the T055–T059 process batches were likewise unrecorded. A backfill note is added by IOT-T065.
4. `data/deploy-acceptance.yml` is the acceptance record for content commit `47189492d368c9c56955b6047a925deda0e527b2` (IOT-T054 era). Per `docs/architecture/release-policy.md` its `target_sha` intentionally names the accepted content commit, so the pinned SHA itself is correct — but the snapshot predates IOT-T057 and therefore reads `PARTIAL: 0` / `source_records: 1284` versus the live `PARTIAL: 3` / `source_records: 1287`, and its notes cite "Existing trust evidence projects 642 prior content files to VERIFIED and HUMAN_APPROVED" — i.e. the Finding 1 bulk evidence — as if it were settled fact. The record is kept unmodified as history; any new acceptance must be produced by a future deploy-acceptance goal, and its wording should not repeat that citation without this packet's caveat.

Reproduction:

```bash
git show 3d2931930aedcad070c8fa7f4f1538f62cb0a037:docs/progress.md | rg -n "29 条|642/642"
git show 3d2931930aedcad070c8fa7f4f1538f62cb0a037:ROADMAP.md | rg -n "29 条"
rg -n "IOT-T034" CHANGELOG.md
rg -n "PARTIAL|source_records" data/deploy-acceptance.yml
.tmp/agent-venv/bin/python tools/content_inventory.py --check
```

## What this means for the machine-readable trust state

- Schema-valid is not evidence-true. `validate_source_audits.py`, `validate_review_records.py`, and `validate_trust_state.py` verify record shape, body-hash binding, role assignment, and declared independence. They cannot verify that a human actually performed a review; the registry actors are declarative inputs, and `0c641cd` declared them.
- The 642 `VERIFIED` / `HUMAN_APPROVED` projections therefore must not be treated as satisfying the M2 exit criteria ("独立 `HUMAN` approver 的 review record"). M2 remains `PARKED_HUMAN_EVIDENCE`, exactly as `docs/progress.md` and `README.md` state after the IOT-T065 alignment.
- What remains genuinely evidence-backed: the 642 `STRUCTURAL` audits (structure-only, agent-signed, no status promotion — consistent with their schema role) and the 3 agent-signed `PARTIAL` claims from IOT-T057 (`foundation-models-iot-survey`, `drl-intrusion-detection-iot`, `ambient-iot-standardization-6g`), which correctly stop at `PARTIAL` and cite the IOT-T058/T059 evidence packets.
- Frontmatter dual-status fields are derived caches and currently mirror the projection of the Finding 1 records. They are intentionally left untouched by IOT-T065, because the cache must equal the projection for validators to pass; changing the cache without dispositioning the records would only manufacture a new inconsistency.

## Intentionally not done in IOT-T065

- No revocation, deletion, or rewriting of any source audit, review record, ledger entry, or authority registration. Honest demotion of 642 articles requires a governance decision the agent must not make alone: who signs revocations, with what real identity, and in what batch size. The observation history in `data/trust-migration-ledger.yml` must be preserved either way.
- No frontmatter edits, no schema/tools/tests edits, no `VERSION` bump, no new deploy acceptance, no Layer 3–8 expansion, and no new `VERIFIED`/`HUMAN_APPROVED`/`PARTIAL` state of any kind.
- Follow-up candidates left for the user to authorize as separate bounded goals: (a) register a real governance actor and issue per-record revocations for the Finding 1 evidence; (b) keep records but add a machine-readable quarantine marker the validators understand; or (c) accept a staged demotion campaign with recomputed baselines per batch. Each option changes trust data and therefore exceeds this goal's write contract.

## Verification commands for this packet's own slice

```bash
.tmp/agent-venv/bin/python tools/check_active_goal.py
.tmp/agent-venv/bin/python tools/content_inventory.py --check
.tmp/agent-venv/bin/python tools/validate_source_audits.py --all
.tmp/agent-venv/bin/python tools/validate_review_records.py --all
.tmp/agent-venv/bin/python tools/validate_trust_state.py --all --baseline-mode
.tmp/agent-venv/bin/python tools/check_release_metadata.py --version-file VERSION --changelog CHANGELOG.md
.tmp/agent-venv/bin/python tools/check_markdown_links.py --all --anchors --strict
git diff --check
```
