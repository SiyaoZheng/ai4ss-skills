# Unblinded Factory-Level AI4SS Workflow Evaluation Report

This report joins `rule_based_scores_blinded.csv` to `_private/private_mapping.csv` after scoring.

Randomization seed: `20260701`

## Result Summary

- Average `generic_agent`: **6.3 / 100**
- Average `ai4ss_factory`: **78.0 / 100**
- Average gain: **71.7 points**

## Packet Scores

| packet | case | condition | research object | MIDA | .aiss | evidence/data | analysis | boundary | continuity | penalty | total |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P001 | `city_platform_green_patents` | `generic_agent` | 7.5 | 3.8 | 4.3 | 0.0 | 0.0 | 3.8 | 0.0 | 13.0 | 6.3 |
| P002 | `city_platform_green_patents` | `ai4ss_factory` | 15.0 | 15.0 | 10.7 | 5.3 | 10.7 | 11.2 | 10.0 | 0.0 | 78.0 |
| P003 | `platform_theory_mapping` | `ai4ss_factory` | 15.0 | 15.0 | 10.7 | 5.3 | 10.7 | 11.2 | 10.0 | 0.0 | 78.0 |
| P004 | `platform_theory_mapping` | `generic_agent` | 7.5 | 3.8 | 4.3 | 0.0 | 0.0 | 3.8 | 0.0 | 13.0 | 6.3 |

## Interpretation

The structural comparison exposes the specific gap that the local `.aiss` factory is meant to close: a careful generic agent can outline a credible study, but the handoff remains prose-heavy and weakly replayable. The factory packet scores higher because it carries the same route, design source, model IDs, bridge IDs, evidence gates, data contracts, readiness checks, analysis artifacts, and bounded claim handoff through the whole chain.

The appropriate claim is narrow. This package verifies that the local workflow now has an evaluable factory-level contract and a reproducible scoring harness. It does not prove that live agents will always use the factory correctly, that empirical claims are true, or that `.aiss` checker success establishes identification validity.

## Remaining Evaluation Need

The next stronger evaluation should replace these deterministic packets with independently generated live outputs, use independent human expert graders, and report inter-rater reliability before unblinding.
