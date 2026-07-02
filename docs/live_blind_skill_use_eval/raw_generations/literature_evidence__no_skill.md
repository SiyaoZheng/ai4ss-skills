Adrian, here is the deliverable I would give the researcher.

**Purpose**

Build a verified literature base before drafting any review prose. The first output should be a set of auditable artifacts, not a narrative: search log, screening sheet, source-status ledger, extraction matrix, and evidence-gap memo.

**Search Scope**

Core queries, run in Google Scholar, Web of Science/Scopus if available, EconLit, SSRN/NBER, OECD, World Bank, and Chinese databases if China is in scope:

1. `"artificial intelligence" AND firm innovation AND patents`
2. `"AI adoption" AND firm growth AND product innovation`
3. `"digital government" AND firm innovation`
4. `"e-government" AND firm innovation`
5. `"digital government" AND public sector productivity`
6. `"AI" AND public sector productivity AND government`
7. `"digital government" AND regional innovation AND difference-in-differences`
8. 中文补充：`数字政府 企业创新`、`政务服务数字化 企业创新`、`数字政府 公共部门效率`、`人工智能 企业创新 专利`

**Initial Seed Sources To Retrieve And Verify**

| strand | seed source | why it matters | verification status |
|---|---|---|---|
| AI adoption and firm innovation | Babina, Fedyk, He, Hodson, “Artificial Intelligence, Firm Growth, and Product Innovation” ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3651052); replication record [Mendeley Data](https://data.mendeley.com/datasets/s26kxvspn7/2)) | Firm-level AI investment measure; links AI investment to growth and product innovation | retrieve published version and PDF; verify final citation from journal page |
| AI and labor/organizational adjustment | Acemoglu, Autor, Hazell, Restrepo, “AI and Jobs: Evidence from Online Vacancies” ([NBER](https://www.nber.org/papers/w28257); journal page [Chicago](https://www.journals.uchicago.edu/doi/abs/10.1086/718327)) | Establishment-level AI exposure/adoption proxy; useful for mechanism and workforce-channel controls | verify final version, data window, and outcome definitions |
| AI as invention technology | Cockburn, Henderson, Stern, “The Impact of Artificial Intelligence on Innovation” ([NBER conference PDF](https://conference.nber.org/confer/2017/AIf17/Cockburn_Henderson_Stern.pdf)) | Conceptual mechanism: AI as a general-purpose “method of invention” | use as theory/background only unless empirical claims are directly supported |
| Digital government and firm innovation | “Digital government and firm innovation: evidence from textual analysis of annual reports” ([Taylor & Francis](https://www.tandfonline.com/doi/abs/10.1080/13504851.2025.2530151)) | Directly matches digital government to firm innovation | retrieve abstract, PDF if accessible, data/method details |
| Digital government and regional innovation | “Study on the impact of digital government development on regional innovation efficiency” ([Springer](https://link.springer.com/article/10.1186/s43093-026-00837-2)) | Quasi-experimental China setting; regional innovation efficiency outcome | open-access source; verify policy timing and DID specification |
| Digital government and collaborative innovation | “Does digital government promote collaborative innovation...” ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12517533/)) | Patent-collaboration mechanism; city-level innovation networks | verify journal, sample, patent-collaboration construction |
| AI and public-sector productivity | OECD, “Governing with Artificial Intelligence” chapters on digital government and service delivery ([OECD](https://www.oecd.org/en/publications/2025/06/governing-with-artificial-intelligence_398fa287/full-report.html)) | Policy synthesis; clarifies productivity, responsiveness, accountability mechanisms | use as institutional framing, not causal evidence |
| GenAI productivity benchmark | Brynjolfsson, Li, Raymond, “Generative AI at Work” ([QJE](https://academic.oup.com/qje/article/140/2/889/7990658)) | Worker-productivity benchmark; not public sector but strong design | use cautiously as adjacent evidence |
| Public-sector measurement caution | Ada Lovelace Institute, “Measuring up” ([Ada Lovelace](https://www.adalovelaceinstitute.org/policy-briefing/measuring-up/)) | Flags measurement problems in AI/public-sector productivity claims | classify as policy/measurement source, not academic causal evidence |

**Screening Rules**

Include studies if they meet all three: identifiable source record, clear unit of analysis, and explicit AI/digital-government exposure plus innovation/productivity outcome.

Prioritize: peer-reviewed articles, NBER/SSRN working papers with full PDFs, official OECD/World Bank reports, studies with datasets, policy timing, or reproducible measures.

Exclude or quarantine: blog summaries, vendor-sponsored claims without methods, papers without accessible metadata, sources that only discuss “digital transformation” generically, and studies where innovation is only rhetorical.

**Source-Status Ledger**

Each candidate gets one status:

- `verified_pdf`: PDF obtained; title/authors/year/source checked.
- `metadata_only`: reliable record exists, PDF not yet retrieved.
- `working_paper`: cite only with version date.
- `policy_report`: usable for context, not causal identification unless methods support it.
- `uncertain`: cannot verify source, version, authorship, or claims.
- `exclude`: out of scope or unverifiable.

Uncertain sources stay out of the review base until resolved. They can appear only in a separate “pending verification” tab.

**Extraction Matrix Columns**

`source_id`, `full_citation_checked`, `source_type`, `country_region`, `period`, `unit_of_analysis`, `treatment_or_exposure`, `outcome`, `mechanism`, `identification_strategy`, `controls`, `data_sources`, `main_result_as_reported`, `limitations_as_reported`, `relevance_to_ai_adoption`, `relevance_to_digital_government`, `relevance_to_firm_innovation`, `relevance_to_public_sector_productivity`, `pdf_verified`, `notes_for_author`.

**Author Decision Questions**

1. Is the paper mainly about firms, local governments, or the interface between the two?
2. Should “innovation” mean patents, patent quality, product innovation, collaboration networks, TFP, or green innovation?
3. Is digital government a treatment, an institutional moderator, or background infrastructure?
4. Will public-sector productivity be measured directly, or treated as a mechanism through service quality, administrative efficiency, or reduced transaction costs?
5. Should China evidence be central, comparative, or only illustrative?
