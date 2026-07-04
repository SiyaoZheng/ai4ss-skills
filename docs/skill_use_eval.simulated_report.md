# Simulated Skill-Use Evaluation

Status: non-blinded demonstration. Use `scripts/run_blind_skill_use_eval.py` for the condition-blinded packet protocol.

This deterministic simulation compares a careful generic agent with a skill-guided agent on four scholar-facing workbench tasks. It checks output structure, not model intelligence.

## Rubric

| dimension | weight | what it asks |
|---|---:|---|
| artifacts | 30 | Did the agent produce the canonical audit objects? |
| traceability | 20 | Can claims or rows be traced to sources, logs, or model objects? |
| boundary | 20 | Did the agent keep AI-use disclosure and direct-submission gates visible while avoiding unsafe scholarly moves? |
| validation | 15 | Did the agent name the relevant validator or gate? |
| author_decision | 15 | Did the agent surface human-accountability decisions? |

## Results

| case | scholar question | no_skill | skill_guided | delta |
|---|---|---:|---:|---:|
| `data_provenance` | 数据怎么来的，样本怎么变的？ | 46.0 | 100.0 | +54.0 |
| `literature_evidence` | 文献证据是不是一手来源？ | 48.0 | 95.0 | +47.0 |
| `claim_discipline` | 结果解释有没有说过头？ | 31.0 | 95.0 | +64.0 |
| `revision_trace` | 返修有没有证据链？ | 31.0 | 95.0 | +64.0 |

Average no_skill score: **39.0 / 100**
Average skill_guided score: **96.2 / 100**
Average gain: **+57.2 points**

## Interpretation

The simulated gain comes mostly from three changes: canonical artifacts appear, hidden-AI or direct-submission risks are penalized, and validation gates become explicit. The skill-guided condition is not more creative; it is more inspectable.

For teaching, this is the right claim: skills are useful only if they change the agent from answer production to inspectable, AI-disclosed research objects and working text.

## Case Details

### `data_provenance`

Task: Build a city-year analysis sample from raw panel, controls, and policy list.

| condition | artifacts | trace markers | risky moves | summary |
|---|---|---|---|---|
| `no_skill` (46.0) | analysis_panel.csv, loose summary statistics, .aiss row-loss checks, output/logs/build_panel.log | row counts, raw data untouched | omits a merge review declaration, variable construction is described only in prose | Returns a usable cleaned dataset and some row-count evidence, but merge ambiguity and variable provenance remain weak. |
| `skill_guided` (100.0) | .aiss row-loss checks, .aiss merge checks, .aiss variable-provenance observations, output/logs/build_panel.log | row counts, merge unmatched rows, variable construction rule, raw data untouched | none | Returns the derived data plus checked .aiss declarations that expose row loss and merge ambiguity. |

### `literature_evidence`

Task: Build a literature base for AI adoption and innovation outcomes before writing a review.

| condition | artifacts | trace markers | risky moves | summary |
|---|---|---|---|---|
| `no_skill` (48.0) | .aiss literature evidence declarations, loose literature notes | DOI or source URL, verification_level | mixes secondary summaries into synthesis | Returns rough source notes, but source locators and synthesis eligibility are not enforced. |
| `skill_guided` (95.0) | .aiss literature evidence declarations, .aiss screening decisions, .aiss source locators | DOI or source URL, claim_source_locator, verification_level | none | Returns checked source-evidence declarations that mostly separate verified primary sources from unverified or secondary-only evidence; synthesis eligibility still needs spot checking. |

### `claim_discipline`

Task: Prepare result-section support from table1, event-study figure, and research design notes.

| condition | artifacts | trace markers | risky moves | summary |
|---|---|---|---|---|
| `no_skill` (31.0) | result prose draft, loose claim notes | estimand, sample and N | hidden AI or direct-submission-ready prose, mechanism evidence is not separated from interpretation | Returns a plausible paragraph plus notes, but it lacks disclosure/direct-submission status and under-specifies claim strength. |
| `skill_guided` (95.0) | .aiss diagnostic checks, .aiss bounded claim declarations, .aiss author decision declarations | estimand, sample and N, support_level | none | Returns claim slots, risks, and visible AI-use/submission gate status; FE/cluster still need model-object confirmation. |

### `revision_trace`

Task: Process reviewer comments about identification, mechanism evidence, and literature coverage.

| condition | artifacts | trace markers | risky moves | summary |
|---|---|---|---|---|
| `no_skill` (31.0) | response letter draft, loose revision plan | comment_id, planned_action | hidden AI or direct-submission-ready prose, done evidence is missing for several promised changes | Returns a plausible response package, but it lacks a visible disclosure/direct-submission gate and done evidence for several promised changes. |
| `skill_guided` (95.0) | .aiss reviewer-request decisions, revision_trace/, .aiss open author decisions | comment_id, planned_action, confidentiality_status | none | Returns a response scaffold with evidence links and open decisions; done_evidence still depends on actual analysis completion. |
