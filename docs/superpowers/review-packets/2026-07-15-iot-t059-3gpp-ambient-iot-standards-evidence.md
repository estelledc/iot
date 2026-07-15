# IOT-T059 3GPP Ambient IoT Standards Evidence Packet

> Purpose: prepare reproducible standards-source evidence for `ambient-iot-standardization-6g`. This packet is not a source audit, not a review record, and does not create `VERIFIED`, `HUMAN_APPROVED`, or any frontmatter status change.

## Scope

- Target content: `docs/connectivity/papers/ambient-iot-standardization-6g.md`
- Prior packet: `docs/superpowers/review-packets/2026-07-15-iot-t058-ambient-iot-pdf-evidence.md`
- Target claim family: `claim-ambient-iot-standardization-6g-standards-details`
- Current trust state before this packet: `source_status: PARTIAL`, `review_status: UNREVIEWED`
- Action taken here: fetch the cited 3GPP TR files and extract standards-level evidence for a future claim-level source audit or human review.
- Action not taken here: no edits to article body, frontmatter, `data/source-audits/`, `data/review-records/`, or `data/trust-authorities.yml`.

## Source Snapshots

The first direct `curl` attempt without a browser user agent returned HTML 403 responses, so the successful fetch used:

```bash
curl -L -sS -A 'Mozilla/5.0' <3gpp-zip-url>
```

| Source | URI | Retrieved at | SHA-256 | Notes |
| --- | --- | --- | --- | --- |
| TR 38.848 ZIP | `https://www.3gpp.org/ftp/Specs/archive/38_series/38.848/38848-i00.zip` | `2026-07-15T03:37:14Z` | `1e18743a6243818c17aa4b3078d247fc04883773c7a23ea5b43e2c8002d896f3` | Official 3GPP archive ZIP, HTTP 200 with browser UA. |
| TR 38.848 DOCX | inside `38848-i00.zip`, file `38848-i00.docx` | `2026-07-15T03:37:14Z` | `1c88d845e085e801749339f09de42c260cb8861d9da3d6753919e97f1d4f88ea` | `textutil` extraction produced 723 lines. |
| TR 38.848 text extraction | local conversion from DOCX | `2026-07-15T03:37:14Z` | `3adbea91bfad4696fd5e2eea7a5edc499c3e8a16e416c3d7fa8170073a17edda` | Temporary file only; not a repository artifact. |
| TR 38.769 ZIP | `https://www.3gpp.org/ftp/Specs/archive/38_series/38.769/38769-001.zip` | `2026-07-15T03:37:14Z` | `94913673161189504784baae614651d1cfbd424296f970bd098bfdacc0fafe47` | Official 3GPP archive ZIP, HTTP 200 with browser UA. |
| TR 38.769 DOCX | inside `38769-001.zip`, file `38769-001.docx` | `2026-07-15T03:37:14Z` | `21cd1c3fcdf7fa3137da2610a4a8fc23b387a4b5fc75211df14256700df404f9` | `textutil` extraction produced 197 lines. |
| TR 38.769 text extraction | local conversion from DOCX | `2026-07-15T03:37:14Z` | `28d5d298b1ebcd48ad6b9a0ce807029280d680aa93257abaa0208f86e504124a` | Temporary file only; not a repository artifact. |

Extraction method:

- `unzip -q <zip> -d /tmp/<target-dir>`
- `textutil -convert txt -output <target.txt> <target.docx>`

The temporary ZIP/DOCX/TXT files were kept under `/tmp` and are not repository artifacts.

## Evidence Map

| Claim area | 3GPP evidence | Packet assessment |
| --- | --- | --- |
| TR 38.848 identity | Header states `3GPP TR 38.848 V18.0.0 (2023-09)`, `Study on Ambient IoT (Internet of Things) in RAN`, `Release 18`. | Directly confirms the arXiv paper's reference [14]. |
| TR 38.848 scope | Section 1 says the report studies feasibility of design targets for a new 3GPP IoT technology relying on ultra-low complexity and ultra-low power devices, including pure batteryless devices and devices with limited energy storage. | Supports the card's statement that Ambient IoT is framed as a 3GPP IoT technology for ultra-low-power devices. |
| Representative use cases | Section 4.1.1 defines Grouping A by environment and Grouping B by functionality/application. It forms eight rUCs: indoor/outdoor inventory, sensors, positioning and command. | Directly supports the rUC structure summarized by the arXiv paper and the existing card. |
| Connectivity topologies | Section 4.2.1 defines four topologies: BS to Ambient IoT device; BS to intermediate node to device; BS to assisting node to device to BS; UE to Ambient IoT device. | Directly supports the topology claim. |
| Deployment scenarios | Section 4.2.2 defines five scenarios by indoor/outdoor device and basestation or UE-based reader. | Supports that deployment scenarios are explicitly part of 3GPP's study framing. |
| Device categorization | Section 4.3 defines Device A as no energy storage and no independent signal generation/amplification; Device B as energy storage without independent signal generation; Device C as energy storage plus independent signal generation. | Directly supports the device A/B/C categorization in the arXiv paper. |
| RAN design targets | Section 5 records targets for power, complexity, coverage, data rate, message size, latency, positioning, density and moving speed. Examples include 10-50 m indoor and 50-500 m outdoor maximum-distance ranges, at least 0.1 kbps minimum user-experienced rate, and about 1000-bit message size. | Supports that TR 38.848 is not just taxonomy; it also frames design targets. |
| Required RAN functionalities | Section 6.2 lists potential RAN functions for power/complexity, coverage, data rate, latency, positioning, connection density, device management, security, mobility, interference/coexistence, CN connectivity and topology compatibility. | Supports the "open system issues" framing and gives concrete audit targets. |
| TR 38.848 recommendation | Section 7.2 concludes Ambient IoT is feasible and beneficial at TSG-RAN preliminary feasibility level, and recommends further WG-level study before normative work. | Supports the card's distinction between standardization progress and still-open engineering work. |
| TR 38.769 identity | Header states `3GPP TR 38.769 V0.0.1 (2024-02)`, `Study on solutions for ambient IoT (Internet of Things)`, `Release 19`. | Directly confirms the arXiv paper's reference [16], with an important caveat that this is version 0.0.1. |
| TR 38.769 relation to TR 38.848 | Introduction says TSG RAN completed the Rel-18 RAN-level SI, producing TR 38.848, and that TR 38.848 defined rUCs, deployment scenarios, connectivity topologies, Ambient IoT devices, design targets, required functionalities, and a preliminary feasibility assessment. | Confirms TR 38.769 builds on TR 38.848. |
| TR 38.769 scope | Section 1 says the SI studies harmonized air-interface design for two device types: about 1 micro-watt peak power with external carrier backscatter, and up to a few hundred micro-watts with energy storage and possible DL/UL amplification. | Supports that TR 38.769 is solution-oriented rather than only a taxonomy document. |
| TR 38.769 scenario narrowing | Section 1 focuses on deployment scenario 1 with Topology 1 and deployment scenario 2 with Topology 2. It considers FR1 licensed spectrum in FDD, in-band to NR, guard-band to NR, or standalone bands. Traffic types are DO-DTT and DT, focused on indoor inventory and indoor command; DO-A is also assessed. | Useful for narrowing future source-audit claims. |
| TR 38.769 maturity caveat | Contents and sections 4-8 are mostly headings/editor notes in V0.0.1. For example, solution sections cover physical layer, protocol stack, CN-RAN interface, architecture, coexistence, RF requirements, carrier-wave waveform, and locating devices, but much of the extracted text is placeholder-like. | Do not use this version as proof of completed solutions. It is evidence of the work-item scope and direction. |

## Implications for the Existing Card

The IOT-T058 arXiv PDF evidence said the paper names concrete 3GPP documents but did not fetch them. This packet closes that specific source gap:

- TR 38.848 V18.0.0 is a direct primary source for the eight rUCs, four topologies, five deployment scenarios, device A/B/C categorization, RAN design targets and required RAN functionalities.
- TR 38.769 V0.0.1 is a direct primary source showing the transition from Rel-18 feasibility/scoping to Rel-19 solution study.
- The current card should continue to avoid wording that implies final normative standardization. TR 38.848 itself recommends further WG-level study before normative work, and TR 38.769 V0.0.1 is early.

## Remaining Gaps

This packet should not be used by itself to promote the card to `VERIFIED`:

- No human `FACT_AUDITOR` performed the audit.
- No `CLAIM_VERIFICATION` source audit record was created or superseded.
- TR 38.769 was checked only at V0.0.1 because that is the version cited by the paper; later versions may contain materially more complete solution content.
- The packet records extracted sections and hash evidence, but no durable copies of the 3GPP ZIP/DOCX files are stored in the repository.
- No independent comparison against 3GPP meeting TDocs such as RP-231627 or RP-231559 was performed.

## Suggested Next Audit Shape

For a future bounded source-audit or human-review goal:

1. Split `claim-ambient-iot-standardization-6g-standards-details` into narrower locked claims if agent-level `PARTIAL` supersession is desired.
2. Use TR 38.848 as the primary evidence for rUCs, topology, deployment scenario, device category and RAN design target claims.
3. Use TR 38.769 V0.0.1 only for Rel-19 solution-study scope and direction, not as evidence of mature or finalized solutions.
4. Ask a real human fact auditor before any `VERIFIED` source audit is created.

Until then, the correct repository state remains `PARTIAL / UNREVIEWED`.
