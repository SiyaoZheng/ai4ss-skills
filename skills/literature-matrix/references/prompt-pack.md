# Prompt Pack

Use these prompts to keep literature work structured and verifiable.

## Scope And Query Plan

```text
Use $literature-matrix.

Research question: [question]
Population/setting: [setting]
Treatment/exposure: [policy, shock, institution, technology]
Outcomes: [outcomes]
Methods of interest: [DID, IV, RD, synthetic control, qualitative, mixed]
Period/language limits: [limits]

Do not present any literature-review working text as no-AI or direct-submission
ready.

First produce:
1. inclusion criteria;
2. exclusion criteria;
3. search strata;
4. exact search queries;
5. source hierarchy;
6. `.aiss` source-evidence fields you will fill.
```

## Search And Screen

```text
Use $literature-matrix to search and screen sources.

Run searches for:
- [concept query]
- [method query]
- [known author or anchor paper]
- [setting query]

For each candidate, record:
- title;
- authors;
- year;
- source URL or DOI;
- publication status;
- include/exclude/maybe/duplicate/unverified;
- reason.

Do not summarize findings yet.
```

## Candidate Discovery First

```text
Use $literature-matrix for an open-ended literature base.

Do not jump directly to synthesis. Any review prose must remain AI-disclosed
working text with source locators.
First produce `.aiss source-discovery declarations` with:
- search_stratum;
- exact query_or_seed;
- title, authors, year when visible;
- source_type;
- source_url_or_path;
- source_status;
- reason;
- next_action;
- relevance_axis;
- found_from;
- access_date.

Include concept, method, outcome, setting, seed-source, and snowballing strata.
Separate empirical evidence candidates from background/measurement sources.
Only after candidate discovery, identify which rows are ready for extraction.
```

## Extract From PDFs Or Zotero Export

```text
Use $literature-matrix to extract `.aiss` source-evidence declarations from the supplied PDFs/Zotero export.

For each paper, extract only what is visible in the source:
- verification_level;
- research question;
- setting and sample;
- data sources;
- treatment or exposure;
- outcomes;
- identification strategy;
- fixed effects, controls, and clustering when visible;
- validation checks;
- main finding in neutral language;
- claim_source_section;
- claim_source_locator;
- limitations;
- relevance to my project;
- open questions.

Mark unclear fields as `unclear from available source`.
Do not set `included_in_synthesis` to `true` for secondary_only or unverified rows.
```

## Deduplicate

```text
Use $literature-matrix to deduplicate this candidate list.

Rules:
- match by title, authors, year, DOI, and working-paper version;
- preserve the most authoritative source URL;
- keep alternate versions in `version_notes`;
- do not merge items with similar titles unless authors and source identity match.

Return a dedupe log with merge decisions and confidence.
```

## Evidence Cluster Outline

```text
Use $literature-matrix to turn verified `.aiss` source-evidence declarations into evidence clusters.

If you draft literature-review working prose, mark it as AI-assisted, keep
source locators visible, and set direct-submission status to not ready until
disclosure and policy checks pass.

Output:
1. clusters by research question, method, setting, mechanism, or disagreement;
2. papers in each cluster;
3. what each cluster can support;
4. what each cluster cannot support;
5. citation gaps;
6. assumptions and source gaps to disclose before writing.
```

## Compile Evidence To AI4SS

```text
Use $literature-matrix to compile verified source evidence into a `.aiss` fragment.

Inputs:
- .aiss literature evidence declarations: [path]
- source row ids: [paper_id list]
- .ai4ss/research_model.aiss if present: [path]

Do not present review prose as no-AI or direct-submission ready.
For each model-affecting source row:
1. update `paper`, `source`, `span`, `claim`, `relation`, `concept`, `causal`, `bridge`, `check`, or `decision` declarations in `.aiss`;
2. preserve source locators and unresolved assumptions;
3. run `python3 scripts/validate_ai4ss_model.py .ai4ss/research_model.aiss`.

If the source is verified but not enough to update a model fragment, set `evidence_compile_status=needs_source_expansion` inside `.aiss` metadata and state the source gap or assumption to disclose.
```

## Refresh Existing Evidence Declarations

```text
Use $literature-matrix to refresh these existing `.aiss` source-evidence declarations.

Inputs:
- existing .ai4ss/research_model.aiss: [path]
- search window: [date range or recent years]
- target journals/working paper series: [list]

Preserve existing rows.
Add new candidates with `added_at`, `source_query`, and canonical `verification_level`.
Flag rows whose publication status may have changed.
```

## Classroom Trace

```text
Bad prompt:
写一段 AI 与科研创新的文献综述，引用最近论文。

Improved prompt:
Use $literature-matrix to search and extract validator-ready `.aiss` literature
evidence declarations first. If working prose is drafted, mark it AI-assisted.
For each row include verification_level, claim_source_section,
claim_source_locator, access_date, version_used, and included_in_synthesis.

Expected behavior:
Plan search strata -> verify primary or local sources -> extract rows -> mark secondary_only
as not synthesis-ready -> run validate_ai4ss_model.py -> return evidence clusters,
assumptions to disclose, and AI-disclosure/direct-submission status for any working text.
```
