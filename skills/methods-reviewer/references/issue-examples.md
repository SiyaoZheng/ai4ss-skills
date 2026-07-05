# Issue Examples

Use these examples to calibrate severity and avoid vague reviews.

## Severity Scale

| severity | meaning | action |
|---|---|---|
| P0 | result likely invalid or unreproducible | fix before using output |
| P1 | serious risk affecting interpretation | address before submission |
| P2 | reporting or robustness gap | fix or disclose |
| P3 | clarity, labeling, or style issue | improve if time allows |

## Example Findings

### P0: Many-To-Many Merge

| field | value |
|---|---|
| issue | `scripts/30_merge.R` joins city controls to firm-year data by `city_id` only, causing row multiplication |
| evidence | N increases from 120,000 to 1,440,000 after merge; controls have 12 years per city |
| why_it_matters | estimates use duplicated firm rows and invalid standard errors |
| next_action | merge by `city_id, year`; regenerate `.aiss` row-loss checks |
| status | confirmed_bug |

### P1: Wrong Clustering Level

| field | value |
|---|---|
| issue | standard errors clustered by firm, but treatment varies at city level |
| evidence | model script uses `cluster = firm_id`; treatment assigned by `city_id` |
| why_it_matters | inference may be too optimistic |
| next_action | run city-clustered and possibly two-way clustered SE sensitivity |
| status | serious_risk |

### P1: Event-Study Baseline Missing

| field | value |
|---|---|
| issue | event-study figure does not state omitted period |
| evidence | figure and caption lack baseline; script drops `event_time == -1` |
| why_it_matters | coefficients cannot be interpreted by readers |
| next_action | update caption and axis annotation |
| status | reporting_gap |

### P2: Unsupported Mechanism Claim

| field | value |
|---|---|
| issue | slide says "R&D channel explains the effect" but no mechanism model is shown |
| evidence | only baseline table and event-study figure present |
| why_it_matters | mechanism claim exceeds evidence |
| next_action | remove mechanism language or add mechanism analysis |
| status | overclaim |

### P3: Table Note Too Sparse

| field | value |
|---|---|
| issue | regression table does not list controls |
| evidence | table note says "controls included" only |
| why_it_matters | readers cannot evaluate specification |
| next_action | list control groups or refer to appendix table |
| status | reporting_gap |

## False-Positive Controls

Before reporting an issue:

- Verify whether the table note, appendix, or script already handles it.
- Distinguish "not visible in table" from "not done".
- Do not require every possible robustness check.
- Do not treat a limitation as a bug when it is clearly disclosed.
- Do not enforce DID-specific standards on descriptive designs.

## Review Output Discipline

Lead with issues, not compliments. For each issue include:

- `route_id`, `design_source`, `target_inquiry`, and affected `mida_component`;
- exact file or output;
- observed evidence;
- why the issue matters;
- minimal next action;
- whether it is confirmed, likely, or needs claim narrowing/evidence expansion.

Validator-ready issue tables use:

```csv
route_id,design_source,target_inquiry,mida_component,severity,issue,evidence,why_it_matters,next_action,status
```
