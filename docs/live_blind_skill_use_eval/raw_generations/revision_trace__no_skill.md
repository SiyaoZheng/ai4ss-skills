Adrian, below is the planning deliverable I would give the researcher, not final response-letter prose.

## Revision Trace Plan

| Item | Core Risk | Evidence / Action Needed | Response Artifact |
|---|---|---|---|
| R1.1 Pre-trend credibility | DID claim is weak if treated and control cities were already diverging. | Re-run event-study with all available pre-treatment leads; report lead coefficients, confidence intervals, and joint test. Add visual raw-trend plot by treatment status. Check sensitivity to city-specific trends or alternative pre-period windows if feasible. | Pre-trend appendix figure, joint-test table, short limitation note if power is low. |
| R1.2 R&D subsidies as mechanism | Current wording may overstate mediation if subsidies are only correlated with treatment or innovation. | Establish timing: policy/treatment → subsidy receipt/amount → innovation outcome. Test whether treatment predicts R&D subsidies. Then test whether subsidy changes align with innovation changes, clearly separating channel evidence from causal mediation. | Mechanism table with timing, first-stage subsidy test, and cautious interpretation label: “consistent with a subsidy channel,” not “proves mechanism,” unless identification supports it. |
| R2.1 Missing 2012 controls | Exclusion/imputation could change sample composition and treatment-control balance. | Create missingness audit: number of cities dropped, treatment share among dropped cities, baseline differences between retained and excluded cities, reason for missingness if known. Run sensitivity checks: complete-case baseline, imputed controls, and possibly missingness indicators. | Sample-flow table, balance table, robustness table, author decision on preferred specification. |
| R2.2 Newer literature | Literature review may look stale, especially around AI-enabled digital government and public-sector innovation. | Add a bounded literature update focused on AI/digital-government adoption, administrative capacity, data governance, and innovation outcomes. Avoid padding with generic AI claims. | Literature-update memo plus 4-8 candidate sources, with exact placement in manuscript. |
| Editor policy tone | Recommendations may exceed empirical design. | Audit conclusion for verbs like “must,” “should,” “prove,” “policy makers need to.” Replace with conditional, scope-limited implications tied to sample and identification. | Claim-tone ledger: original claim, evidence basis, revised claim level, author approval. |

## Immediate Evidence Checks

1. Confirm treatment timing and whether 2012 controls are pre-treatment for all cities.
2. Reconstruct the analysis sample before and after missing-control handling.
3. Save all confidential reviewer comments in restricted project storage; use paraphrased issue IDs in working files.
4. Separate three categories in the response matrix: completed analysis, planned manuscript edit, and author judgment still needed.

## Literature Update Targets

Use recent sources selectively rather than building a broad AI literature review. Candidate anchors:

- OECD, [Governing with Artificial Intelligence](https://www.oecd.org/en/publications/2025/06/governing-with-artificial-intelligence_398fa287.html), for public-sector AI opportunities and governance risks.
- OECD, [Digital Government Outlook 2026](https://www.oecd.org/en/publications/2026/06/digital-government-outlook_4585678e/full-report/adopting-and-governing-ai-in-government_7ef312a9.html), for uneven government AI adoption and implementation conditions.
- OECD, [How artificial intelligence is accelerating the digital government journey](https://www.oecd.org/en/publications/2025/06/governing-with-artificial-intelligence_398fa287/full-report/how-artificial-intelligence-is-accelerating-the-digital-government-journey_d9552dc7.html), for productivity, responsiveness, accountability, and data-management prerequisites.
- “Expanding AI adoption in public sector organizations,” [Transforming Government: People, Process and Policy](https://www.emerald.com/tg/article/20/2/165/1300122/Expanding-AI-adoption-in-public-sector), for organizational practices in public-sector AI adoption.
- “AI-Driven Innovation and Collaboration in Public Services,” [DGO 2025 Proceedings](https://proceedings.open.tudelft.nl/DGO2025/article/view/950), for public-service AI use cases and innovation framing.

## Author Decision Questions

- Are we willing to describe R&D subsidies only as “suggestive channel evidence” if timing or identification is insufficient?
- Should the preferred sample be complete-case, imputed, or complete-case with imputation only as robustness?
- What is the minimum pre-trend evidence we consider credible: visual similarity, insignificant leads, joint test, or equivalence-style bounds?
- Which policy claims are directly supported by the city sample and which should be moved to limitations or future research?

## Recommended Revision Order

1. Missing-data audit first, because it affects all downstream estimates.
2. Pre-trend and main DID robustness second.
3. Mechanism analysis third, after sample/specification is fixed.
4. Literature update and conclusion tone audit last, so the prose follows the evidence rather than leading it.
