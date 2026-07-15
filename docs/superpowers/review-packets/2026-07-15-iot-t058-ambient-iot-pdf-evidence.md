# IOT-T058 Ambient IoT PDF Evidence Packet

> Purpose: prepare reproducible PDF-level evidence for `ambient-iot-standardization-6g`. This packet is not a source audit, not a review record, and does not create `VERIFIED`, `HUMAN_APPROVED`, or any frontmatter status change.

## Scope

- Target content: `docs/connectivity/papers/ambient-iot-standardization-6g.md`
- Target claim from the IOT-T057 audit: `claim-ambient-iot-standardization-6g-standards-details`
- Current trust state before this packet: `source_status: PARTIAL`, `review_status: UNREVIEWED`
- Action taken here: read the arXiv abstract page and PDF, then extract evidence for a future claim-level source audit or human review.
- Action not taken here: no edits to article body, frontmatter, `data/source-audits/`, `data/review-records/`, or `data/trust-authorities.yml`.

## Source Snapshots

| Source | URI | Retrieved at | SHA-256 | Notes |
| --- | --- | --- | --- | --- |
| arXiv abstract page | `https://arxiv.org/abs/2412.12519` | `2026-07-15T03:01:23Z` | `4b01ca3a41809f7b06ca1177d3f0cd25185b666c72533fc8de960fd6a509b249` | Same hash as the IOT-T057 source audit reference. |
| arXiv PDF | `https://arxiv.org/pdf/2412.12519` | `2026-07-15T03:01:23Z` | `8c32932a83352482e2210b64bf86dbf08397ac426dd44a12c0fc57d79ba7e6b2` | `pdfinfo` reports 9 pages, PDF 1.5, file size 887537 bytes. |

Extraction method:

- `pdftotext -layout /tmp/iot-t058-ambient.pdf /tmp/iot-t058-ambient.txt`
- Page-specific extraction used `pdftotext -layout -f <page> -l <page>`.

The temporary PDF/text files were kept under `/tmp` and are not repository artifacts.

## Evidence Map

| Claim area | PDF evidence | Packet assessment |
| --- | --- | --- |
| Paper identity | Page 1 title is "Ambient IoT towards 6G: Standardization, Potentials, and Challenges"; authors match the card: Kan Zheng, Rongtao Xu, Jie Mei, Haojun Yang, Lei Lei, and Xianbin Wang. | Supports the existing identity claim. |
| Standardization framing | Page 1 abstract says the paper surveys current standardization efforts and gives an overview of ongoing 3GPP A-IoT initiatives. Page 2 states 3GPP has initiated systematic discussions and standardisation efforts. | Supports that the paper is a 3GPP standardization-oriented survey, not just a generic backscatter paper. |
| 3GPP study state | Page 2 Section II says the A-IoT study item in 3GPP has been finished, focuses on IoT technologies suitable for 6G, and that representative use cases, connectivity topologies and deployment scenarios are outlined in reference [14]. It also says open issues remain for the work item stage in reference [16]. | Supports the card's "standardization progress" framing. |
| Use case grouping | Page 2 says 3GPP established two grouping levels: Grouping A by deployment environment and Grouping B by function/application. Page 3 Table I lists eight representative use cases across inventory, sensor, positioning and command, split by indoor/outdoor. | Supports the claim that the paper enumerates 3GPP use-case structure. |
| Topology definitions | Page 3 Fig. 1 and surrounding text describe four typical connectivity topologies for A-IoT networks defined in 3GPP. The text introduces `Ua` as the newly designed A-IoT device link and `Uu` as the traditional UE-to-RAN air interface. | Supports the claim that the paper covers topology-level standardization details. |
| Device categories | Page 2 describes three device categories: Device A has no energy storage and no independent signal generation; Device B has energy storage but no independent signal generation; Device C has energy storage and independent signal generation. | Supports the card's note that device capability is a standardization/design boundary. |
| Key enabling technologies | Pages 4-6 discuss backscatter modulation, interference cancellation/avoidance, and multiple access. Page 5 states A-IoT is likely to use TDMA as primary multiple access while CBMA/NOMA-like methods may be explored. | Supports the card's "key enabling technologies" summary. |
| Demonstration platform | Pages 5-7 describe an A-IoT demonstration system with a BS and one tag/device. Page 6 Table III gives parameters: 925 MHz carrier, 1 MHz bandwidth, BPSK/OOK, 20 dBm BS transmit power, 5 dBi BS antenna gain, 2 dBi device antenna gain, 20 dB circulator isolation. | Supports the card's claim that the paper includes a practical prototype and measurable parameters. |
| Field experiment result | Page 7 explains measured BER/SNR versus distance. Page 9 conclusion states the system can support 1 Mbps at a distance of more than 10 meters. | Supports a bounded field-result claim, but only as reported by the paper; no independent reproduction was performed. |
| Open challenges | Pages 7-8 list open issues: multi-antenna transmission, multi-node joint transmission, coexistence with existing networks, device localization, spectrum allocation, radio resource management, and security. | Supports the card's "challenges" framing and gives concrete checklist items for a future audit. |
| 3GPP references | Page 9 references [14] `3GPP TR 38.848 V18.0.0, Study on ambient IoT ... in RAN (Release 18), Jun. 2023` and [16] `3GPP TR 38.769 V0.0.1, Study on solutions for ambient IoT ... RAN (Release 19), Feb. 2024`. | Supports that the paper names concrete 3GPP documents. This packet did not independently fetch those 3GPP documents. |

## Implications for the Existing Card

The existing card's high-level summary is broadly supported by the PDF:

- "3GPP standardization progress" is supported by Section II and references [14], [16].
- "representative use cases and topology" is supported by Table I and Fig. 1.
- "backscatter, energy, synchronization/access constraints" is supported by the key-technology discussion, especially modulation, interference and multiple access.
- "demonstration system and field experiment" is supported by Section IV, Table III and Fig. 3.

The most important correction for future wording is precision: the paper reports a prototype result and a field experiment, but this repository has not reproduced the experiment. Future content should say "the paper reports" rather than "the system proves" unless independent reproduction exists.

## Remaining Gaps

This packet should not be used by itself to promote the card to `VERIFIED`:

- No human `FACT_AUDITOR` performed the audit.
- No `CLAIM_VERIFICATION` source audit record was created or superseded.
- The PDF supports the paper's own claims, but this packet did not independently fetch 3GPP TR 38.848 or TR 38.769 from 3GPP.
- No figure/table screenshots or exact PDF offsets were stored as durable artifacts.
- No experiment reproduction, code review, or dataset validation was attempted.

## Suggested Next Audit Shape

For a future bounded source-audit goal, use this packet as input and choose one of these options:

1. Keep `PARTIAL` and supersede the IOT-T057 audit only if the schema allows a remaining uncovered claim, for example by splitting `standards-details` into narrower locked claims.
2. Ask a real human fact auditor to verify all locked critical claims and then create a schema-valid `VERIFIED` source audit.
3. Fetch the cited 3GPP TR 38.848 and TR 38.769 documents before attempting any claim that depends on standards documents rather than the arXiv paper alone.

Until then, the correct repository state remains `PARTIAL / UNREVIEWED`.
