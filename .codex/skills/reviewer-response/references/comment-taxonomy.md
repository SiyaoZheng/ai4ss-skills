# Comment Taxonomy

Use this taxonomy to decompose reviewer reports into atomic requests.

## Comment Types

| type | what reviewer asks | typical evidence |
|---|---|---|
| contribution | clarify novelty, audience, theory, or positioning | introduction, literature matrix |
| identification | justify assumptions or comparison | design note, diagnostics, robustness |
| data | explain source, sample, variable construction, missingness | data audit, variable provenance |
| measurement | validate construct, coding, or extraction | validation table, source snippets |
| model | change specification, FE, controls, estimator | scripts, model outputs |
| inference | standard errors, clustering, multiple testing, weak IV, power | scripts, robustness outputs |
| robustness | add checks, placebo, sensitivity, alternative samples | robustness plan/output |
| heterogeneity | subgroup or mechanism requests | design and power assessment |
| literature | cite or engage missing literature | literature matrix |
| writing | clarify, reorganize, shorten, tone down | author draft |
| scope | requests beyond study design | author decision |
| formatting | tables, figures, appendix, journal style | manuscript files |

## Hidden Requests

Reviewer text often bundles requests. Split them.

Example:

```text
The authors should better justify the DID design and show the results are not driven by treated cities adopting earlier.
```

Atomic requests:

1. State identifying assumption.
2. Explain adoption timing.
3. Add or point to pre-treatment comparison.
4. Add timing robustness or cohort sensitivity if feasible.

## Status Logic

Use:

- `accept`: feasible and strengthens manuscript.
- `partial`: concern valid, requested implementation not fully feasible.
- `clarify`: manuscript already did the work but text was unclear.
- `rebut`: request would be misleading or change the estimand.
- `cannot_do`: data/design/access prevents it.
- `needs_author`: strategic or substantive decision.

## Scope Boundary Tests

Mark `needs_author` when:

- request changes the paper's main estimand;
- request requires new data collection;
- request would reposition the contribution;
- request requires dropping main analysis;
- request asks for claims stronger than evidence.

## Evidence Needed By Type

| type | minimum evidence before response scaffold |
|---|---|
| identification | design note, diagnostic table/figure, assumption wording |
| data | sample flow, variable provenance, missingness report |
| model | script path, output table, model notes |
| inference | clustering/SE code, sensitivity output |
| literature | verified matrix row or source |
| writing | revised section location and author decision |
| formatting | updated file/page/table number |

## Red Flags

- One response addresses multiple requests without tracking each.
- Response promises a table that does not exist.
- "We agree" concedes a point that changes the design.
- A rebuttal lacks manuscript clarification.
- The author decision is hidden as an agent decision.
