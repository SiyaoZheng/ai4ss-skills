# Literature Evidence Declaration Pattern

Use this schema for empirical social-science literature.

## Core Fields

| column | meaning |
|---|---|
| `route_id` | Route/design id this row serves |
| `design_source` | Path to the design brief or MIDA declaration |
| `target_inquiry` | Estimand, descriptive quantity, measurement target, classification target, process-tracing claim, or synthesis question |
| `paper_id` | Stable short id, e.g. `smith_2024_city_pilots` |
| `citation` | Author-year-title short citation |
| `authors` | Full author list as available |
| `year` | Publication or working-paper year |
| `status` | journal_article, accepted, working_paper, preprint, conference_paper, book_chapter, report, unverified |
| `venue_or_series` | Journal, NBER, arXiv, SSRN, etc. |
| `doi` | DOI, or `no_doi: reason` |
| `url` | Stable source URL |
| `verification_level` | verified_primary, verified_local, secondary_only, unverified |
| `research_question` | What the paper asks |
| `setting_sample` | Country/region, units, period, sample |
| `treatment_or_exposure` | Policy, shock, intervention, or variable of interest |
| `outcomes` | Main outcomes |
| `data_sources` | Datasets used |
| `identification_strategy` | DID, IV, RD, RCT, synthetic control, structural, descriptive, qualitative, etc. |
| `fixed_effects_controls` | FE, controls, clustering, if reported |
| `validation_checks` | Event study, placebo, balance, robustness, sensitivity, etc. |
| `main_findings` | Neutral summary tied to the paper |
| `claim_source_section` | abstract_only, introduction, theory, data, methods, table_figure, results, conclusion, appendix, secondary_summary |
| `claim_source_locator` | Page, table, figure, section, paragraph, or local note locator |
| `limitations` | Stated or visible limitations |
| `relevance_to_project` | Why it matters for the user's project |
| `open_questions` | What requires human judgment |
| `verified_from` | PDF path, DOI page, journal page, or user-provided source |
| `access_date` | YYYY-MM-DD date for web or database access |
| `version_used` | Published version, working-paper version, preprint version, or local PDF date |
| `included_in_synthesis` | true, false, or needs_author |
| `ai4ss_model_path` | Path to `.aiss` model, or `not_applicable:<reason>` |
| `model_id` | DSL model id supported or challenged by this source row, or `not_applicable:<reason>` |
| `concept_id` | DSL concept id supported or challenged by this source row, or `not_applicable:<reason>` |
| `causal_id` | DSL causal implication id supported or challenged by this source row, or `not_applicable:<reason>` |
| `bridge_id` | DSL empirical bridge id supported or challenged by this source row, or `not_applicable:<reason>` |
| `ai4ss_check_status` | `pass`, `warn`, `not_run`, or `not_applicable` |
| `source_artifact_path` | PDF, DOI page, repository page, source note, table, figure, or log referenced by the `.aiss` declaration |
| `evidence_compile_status` | `declared`, `needs_review`, `blocked`, or `not_applicable` |
| `evidence_validation_command` | Exact `.aiss` validation command, or `not_run_reason:<reason>` |

## Extraction Rules

- Use exact variable names only when visible in the source.
- Use neutral phrasing for findings: "reports a positive association", "estimates an increase", "finds no robust effect".
- If methods are unclear, write `unclear from available source`.
- If a claim comes from an abstract only, set `claim_source_section` to `abstract_only`.
- Do not infer fixed effects or clustering from method labels.
- Do not set `included_in_synthesis` to `true` unless `verification_level` is `verified_primary` or `verified_local`.
- Use `needs_author` when a row is verified but its relevance or version choice requires researcher judgment.
- If `ai4ss_model_path` is not `not_applicable:<reason>`, it must end with `.aiss`.
- Source rows can support, challenge, or qualify a model element; they must not rewrite `.aiss` concepts or bridges silently.
- Synthesis-ready rows that affect `.aiss` concepts, causal implications, or bridges should update checked `.aiss` declarations or state a concrete review/blocking reason.
- Model-affecting source evidence must validate through `scripts/validate_ai4ss_model.py <research_model.aiss>`.

## Evidence To Author Hand-Off

Only after source-evidence review, group papers by:

- Research question.
- Identification strategy.
- Data or institutional setting.
- Mechanism.
- Relevance to the user's design.

Keep disagreements visible. Do not smooth them into a single narrative unless the evidence supports it.
