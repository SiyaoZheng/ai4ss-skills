# Quality Gates

Use these gates to decide whether a data pipeline can proceed.

## Contents

- Gate 0: Project Boundary
- Gate 1: Unit Of Observation
- Gate 2: Merge Integrity
- Gate 3: Variable Construction
- Gate 4: Text Extraction And Human Review
- Gate 5: Sample Flow
- Gate 6: Reproducibility
- Gate 7: Handoff Readiness

## Gate 0: Project Boundary

PASS when:

- Raw data directories are identified and protected.
- Output directories are identified.
- Credentials, private folders, and sensitive files are excluded.
- The user request is compatible with project instructions.

FAIL when:

- The task requires editing `data/raw/`.
- A script reads `.env`, credentials, or private folders without explicit need.
- The project has conflicting instructions about source of truth.

Action on FAIL: stop and ask for a boundary decision.

## Gate 1: Unit Of Observation

PASS when:

- Unit is stated in research design and confirmed in data.
- Key columns uniquely identify rows or duplicate keys are explained.
- Panel balance or imbalance is reported when relevant.

WARN when:

- Duplicate keys exist but can be explained by sub-units.
- Unit changed across pipeline stages.

FAIL when:

- The claimed unit cannot be reconstructed.
- Duplicates are silently dropped.

Minimum evidence:

- duplicate-key table;
- row counts by unit/time;
- sample of duplicate rows.

## Gate 2: Merge Integrity

PASS when:

- All merge keys have type and format harmonized.
- Match rate is reported.
- Left-only and right-only records are written to review files.
- Many-to-many merges are either avoided or justified.

WARN when:

- Match rate is low but expected.
- Some unmatched records are outside the study period.

FAIL when:

- A many-to-many merge increases rows unexpectedly.
- Matching uses names without a manual review stage.
- Unmatched treated units are dropped without explanation.

Minimum evidence:

- `.aiss merge checks`;
- unmatched files;
- duplicate-key diagnostics.

## Gate 3: Variable Construction

PASS when:

- Each constructed variable has source variables and a rule.
- Treatment timing and post indicators are checked against original sources.
- Transformations handle zero, negative, and missing values explicitly.

WARN when:

- Some variables depend on imputation or ambiguous text extraction.
- Rules differ across data sources.

FAIL when:

- Treatment variables are inferred from outcome changes.
- Post-treatment controls are added without design justification.
- Low-confidence extracted values enter the main sample.

Minimum evidence:

- `.aiss variable-provenance observations`;
- cross-tab for treatment and timing;
- range and missingness checks.

## Gate 4: Sample Flow

PASS when:

- Every row-changing step has before/after counts.
- Restrictions are named and reproducible.
- Core-variable missingness is reported before deletion.

WARN when:

- Row loss is large but explainable.
- Deletions concentrate in a subgroup that needs sensitivity checks.

FAIL when:

- Final N cannot be traced from raw input.
- Filters are embedded in code without labels.

Minimum evidence:

- `.aiss row-loss checks`;
- missingness report;
- restriction flags retained at least in interim data.

## Gate 5: Reproducibility

PASS when:

- Scripts run in order from a clean state.
- Commands and logs are saved.
- Outputs have stable paths.
- Random steps use seeds.

WARN when:

- Some proprietary inputs cannot be redistributed but paths and hashes are documented.
- Manual review is required for a small subset.

FAIL when:

- Results exist only in chat.
- Scripts depend on absolute local paths without configuration.
- Running the pipeline changes raw data.

Minimum evidence:

- run log;
- changelog;
- output inventory.

## Common Failure Modes

| failure | symptom | likely cause | response |
|---|---|---|---|
| silent row explosion | N increases after merge | duplicate keys or many-to-many join | stop, create duplicate audit, aggregate or disambiguate |
| fake balanced panel | rows missing but filled by expand grid | accidental zero-fill | keep missing explicit, never zero-fill unless substantively justified |
| treatment leakage | treatment uses post-outcome information | constructing policy from outcome data | rebuild treatment from source list |
| lost raw provenance | final data has no source columns | over-cleaned pipeline | add source ids and `.aiss` provenance observations |
| ambiguous IDs | `city_id` and `city_code` mixed | inconsistent naming | harmonize once and document mapping |
| text hallucination | extracted values not in source snippets | LLM free extraction | require snippets and manual review flags |
