# Unblinded Skill-Use Evaluation Report

This report joins `rule_based_scores_blinded.csv` to `private_mapping.csv` after scoring.

| packet | case | condition | total |
|---|---|---|---:|
| P001 | `data_provenance` | `skill_guided` | 100.0 |
| P002 | `data_provenance` | `no_skill` | 46.0 |
| P003 | `literature_evidence` | `no_skill` | 48.0 |
| P004 | `literature_evidence` | `skill_guided` | 95.0 |
| P005 | `claim_discipline` | `skill_guided` | 95.0 |
| P006 | `claim_discipline` | `no_skill` | 31.0 |
| P007 | `revision_trace` | `skill_guided` | 95.0 |
| P008 | `revision_trace` | `no_skill` | 31.0 |

Average `no_skill`: **39.0 / 100**
Average `skill_guided`: **96.2 / 100**
Average gain: **+57.2 points**

Interpretation: in this structural simulation, skill-guided packets score higher because they expose audit artifacts, validation gates, AI-use disclosure, and human-accountability decisions. This is not evidence that any particular LLM will behave this way in live use.
