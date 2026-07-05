---
name: public-data-sources
description: >
  Public social-science data source routing skill. Use when an agent needs to
  choose, verify, or call free or free-registration APIs and downloadable public
  datasets for comparative politics, political economy, demography, news events,
  trade, macroeconomics, bibliometrics, or survey-data discovery. Triggers:
  "public data API", "free data source", "World Bank API", "OECD API",
  "Eurostat API", "Census API", "FRED API", "IPUMS API", "GDELT",
  "OpenAlex", "UCDP", "WHO GHO", "ILOSTAT", "UNHCR", "OWID",
  "Voteview", "ParlGov", "source acquisition", "data acquisition",
  "dataset discovery", "data repository", "research data repository",
  "Zenodo", "DataCite", "Dataverse", "Figshare", "Dryad",
  "country-year panel", "global country-year panel",
  "国家-年份面板", "全球国家年度面板", "国家年度面板",
  "China city-year panel", "China prefecture panel", "中国地级市面板",
  "中国城市统计年鉴", "数据获取", "数据源获取", "公共数据",
  "免费数据接口", "社会科学数据源".
---

# Public Data Sources

Route social-science data requests to public data sources without confusing
"free" with "unlimited", "no authentication", or "redistributable".

## Core Rule

Before calling a source, classify its access path as `public_no_secret`,
`free_key_required`, or `download_ingest_only`. Respect rate limits, cache
responses for repeated agent work, and never commit API keys or downloaded
restricted microdata.

## Real Observed Data Only

This skill is the acquisition gate for empirical data in the research factory.
Every empirical row, cell, document code, event, unit, outcome, treatment,
covariate, table value, or estimate handed downstream must come from a real
observed public or authorized source.

Synthetic, simulated, hypothetical, illustrative, generated, DGP-created,
random-draw, benchmark-calibrated, or literature-parameter-imputed data are not
valid substitutes for unavailable empirical data. Published coefficients,
parameter benchmarks, and literature summaries may guide theory or measurement
but must not be converted into analysis rows or empirical estimates.

## Full-Auto Harness Contract

Do not block for user choice. Rank feasible source routes, choose the strongest
route automatically, and set `next_skill_route` to the next executable skill. If
the best source fails access, license, coverage, or measurement checks, switch
automatically to another real observed public or authorized source, unit,
geography, period, measure, or design route. If no observed-data route supports
the selected design, route to `study-design-builder` for automatic redesign.

## Methodology Foundation

This skill supports the Data strategy layer of MIDA. It selects and verifies
real observed sources for sampling, measurement, source selection, live access,
license/terms, and provenance before `research-data-builder` turns acquired
source artifacts into an auditable analysis sample.

## AI4SS Runtime Gate

For full-auto harness work, this skill must run after a selected route and MIDA
data strategy exist and before `research-data-builder` constructs the analysis
sample, unless the workspace already contains a verified real observed source
artifact with row-level provenance.

## Workspace Contract

Follow `docs/research_workspace_contract.md`. Durable workflow state belongs in
`.ai4ss/research_model.aiss`.

## .aiss State Machine

When `.ai4ss/research_model.aiss` exists, run
`python3 dsl/scripts/aiss.py state .ai4ss/research_model.aiss` before deciding
the next route. When this skill starts, completes, fails, or observes a
watchdog heartbeat in an automatic harness, record that runtime fact as an
`.aiss` `event` declaration or return a deterministic
`aiss.py transition --event ...` fragment for merge. Events do not replace
semantic updates: if the skill resolves a repair/check status, update the
relevant `route`, `mida`, `decision`, `check`, `artifact`, or claim-support
declaration too.

Write source artifacts, cached bounded pulls, checksums, and request logs under
the project workspace using stable paths. Use source/artifact/check/decision
declarations rather than detached Markdown/CSV/JSON workflow-state files.

## Workflow Contract

- Upstream inputs: `.ai4ss/research_model.aiss`, selected `route` declarations, MIDA
  `data_strategy` declarations, source need notes, target unit and period,
  desired variables, country or region scope, and any known source constraints.
- Produces: ranked real observed source routes, selected source, access class,
  authentication requirements, official documentation links, live-access result,
  safe request template, rate-limit notes, license/terms notes, cached bounded
  source artifacts when access succeeds, and source/access/check/decision
  declarations for `.ai4ss/research_model.aiss`.
- Handoff fields: `route_id`, `mida_id`, `design_source`, `target_inquiry`,
  `source_name`, `source_access_status`, `access_class`, `auth_env_var`,
  `official_docs_url`, `request_template`, `source_artifact_path`,
  `source_artifact_checksum`, `rate_limit_note`, `license_or_terms_note`,
  `observed_data_only_status`, `row_source_provenance`, `provenance_note`,
  `ai4ss_model_path`, `validation_commands`, and `next_skill_route`.
- Downstream routes: `research-data-builder` when source artifacts are ready for
  sample construction; `study-design-builder` when the design must be redesigned
  to match an observed-data route; `literature-matrix` when source choice needs
  theory or evidence grounding; `research-analysis-runner` only when an acquired
  source artifact is already analysis-ready; `methods-reviewer` for source/design
  validity audits.

## Routing Boundaries

Use this skill to choose and safely call public data sources. Do not use it to
build the final analysis sample, clean raw files, run statistical models, or
certify identification. Hand those tasks to downstream research-factory skills.
Do not hand off to `research-data-builder` until a real observed source route is
selected and either a source artifact exists or a live, reproducible acquisition
command is declared.

## Workflow

```text
Step 0: Classify the data need
-> Identify topic, unit, geography, period, granularity, and whether microdata
   or aggregate time series are needed.
-> Read `.ai4ss/research_model.aiss` when present and preserve route/MIDA/decision IDs.

Step 1: Read the registry
-> Open references/source-registry.md.
-> When the request is about finding possible datasets or repository platforms
   rather than a named statistical source, also open
   references/discovery-platforms.md and use only sources with live verified
   no-secret machine-readable search endpoints.
-> Select sources by fit and access class, not by popularity alone.
-> Reject any path that would require synthetic, simulated, hypothetical,
   illustrative, generated, DGP-created, random-draw, benchmark-calibrated, or
   literature-parameter-imputed empirical data.

Step 2: Verify live access when results will be used
-> Use official docs or current live endpoints before writing claims about
   current availability, limits, or authentication.
-> Prefer bounded test calls and small samples before bulk collection.
-> Record source_access_status, observed_data_only_status, and validation
   command evidence.

Step 3: Call safely
-> Use no-secret endpoints first when adequate.
-> Use environment variables for free keys when required.
-> Add throttling, retries for 429/5xx, request logging, and source timestamps.
-> Save bounded source artifacts with checksums when the harness needs an
   analysis sample.

Step 4: Hand off
-> Pass selected source, access evidence, artifact path, provenance, limitations,
   validation command, and next_skill_route to the downstream skill.
-> Route to `research-data-builder` when data need to become analysis-ready.
-> Route to `study-design-builder` when only a redesigned real-data inquiry is
   feasible.
```

## Default Outputs

- A short source recommendation with access class and why it fits the research
  need.
- A selected best route plus ranked alternatives, with no human choice required.
- A safe request template, package recommendation, or cached bounded source
  artifact with checksum.
- Official documentation link and access-limit note.
- `source_access_status`, `observed_data_only_status`, `row_source_provenance`,
  and `next_skill_route`.
- A downstream handoff to `research-data-builder` when the task needs derived
  data, sample-flow evidence, or `.aiss` source declarations.

## Script Utilities

- `scripts/build_seed_store.py` builds a local SQLite seed store for
  no-secret and directly downloadable public sources. It writes generated files
  under `tmp/public-data-sources/` by default, records provenance and SHA256
  hashes, and records key/form-required sources as queue rows instead of
  pretending they can be called freely. GDELT is skipped unless
  `--include-gdelt` is explicitly passed. Large China city-year archives,
  including the XMU 2004-2020 China City Statistical Yearbook panel RAR, are
  skipped unless `--include-large-china-city-archives` is explicitly passed.
  Global country-year download panels include Penn World Table 11.0, Maddison
  Project Database 2023, UNDP HDR composite-index time series, and Correlates
  of War National Material Capabilities.

Example:

```bash
python3 skills/public-data-sources/scripts/build_seed_store.py --include-qog-standard --parse-vdem
python3 skills/public-data-sources/scripts/build_seed_store.py --include-large-china-city-archives
```

- `scripts/discover_fetchable_sources.py` searches the verified no-secret
  discovery platforms listed in `references/discovery-platforms.md`, normalizes
  metadata, and records public file URLs only when the platform exposes them
  directly. It caps file metadata per record and does not download files by
  default.

Example:

```bash
python3 skills/public-data-sources/scripts/discover_fetchable_sources.py "political economy" --limit 3
```

## Reference Files

| File | Content | Read when |
|---|---|---|
| [source-registry.md](references/source-registry.md) | Free and free-registration social-science data sources, access classes, request patterns, packages, and caveats | Every time this skill is invoked |
| [discovery-platforms.md](references/discovery-platforms.md) | Live-verified agent-fetchable dataset discovery platforms and exclusion rules | When the request asks where to search for datasets, replication packages, or repository-hosted data |
