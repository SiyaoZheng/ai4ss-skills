# Live Unblinded Skill-Use Evaluation Report

This report joins frozen blinded grades to `_private/private_mapping.csv`.

## Result Summary

- Average `no_skill`: **84.4 / 100**
- Average `skill_guided`: **94.1 / 100**
- Average paired gain: **9.8 points**

- Randomization seed, disclosed after grading: `20260625`

## Packet Scores

| packet | case | condition | graders | mean | min | max |
|---|---|---|---:|---:|---:|---:|
| P001 | `data_provenance` | `skill_guided` | 2 | 97.0 | 97.0 | 97.0 |
| P002 | `data_provenance` | `no_skill` | 2 | 81.5 | 80.0 | 83.0 |
| P003 | `literature_evidence` | `no_skill` | 2 | 90.0 | 89.0 | 91.0 |
| P004 | `literature_evidence` | `skill_guided` | 2 | 88.5 | 88.0 | 89.0 |
| P005 | `claim_discipline` | `skill_guided` | 2 | 96.0 | 96.0 | 96.0 |
| P006 | `claim_discipline` | `no_skill` | 2 | 81.5 | 79.0 | 84.0 |
| P007 | `revision_trace` | `skill_guided` | 2 | 95.0 | 94.0 | 96.0 |
| P008 | `revision_trace` | `no_skill` | 2 | 84.5 | 84.0 | 85.0 |

## Paired Case Differences

| case | no_skill | skill_guided | difference |
|---|---:|---:|---:|
| `data_provenance` | 81.5 | 97.0 | 15.5 |
| `literature_evidence` | 90.0 | 88.5 | -1.5 |
| `claim_discipline` | 81.5 | 96.0 | 14.5 |
| `revision_trace` | 84.5 | 95.0 | 10.5 |

## Agreement Check

- `grader_a` vs `grader_b`: Pearson r = 0.965; mean absolute difference = 1.8

## Interpretation

This evaluation supports a narrow claim: in these four live generated tasks,
skill-guided outputs were more useful when usefulness is defined as producing
inspectable research artifacts, traceability markers, explicit authorship
boundaries, validation gates, AI-use disclosure, and human-accountability decision points.

The aggregate advantage is not uniform. Skill-guided output scored lower in `literature_evidence`; inspect the paired packets before treating the skill as generally better for that workbench.

Follow-up improvement: `literature-matrix` now requires a candidate-discovery ledger for open-ended search tasks, plus a validator for search strata, source-status labels, next verification actions, and snowballing coverage. This targets the observed weakness in the literature case: schema discipline alone did not beat a generic agent that produced richer seed-source discovery.

It does not show that skill-guided agents are always better, that the artifacts
are empirically correct, or that scholarly claims have completed
human-accountability review. Those require source/data inspection.

## Limits

- Generation was not blind to condition.
- Graders were condition-blinded but may infer style from packet contents.
- Agent graders are not independent human experts.
- Cases are controlled scenarios, not full field deployments.
- The rubric favors traceable research workflow behavior by design; it should not
  be used to rank direct-submission prose readiness.
