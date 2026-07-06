# Unblinded Factory-Level AI4SS Workflow Evaluation Report

This report joins `llm_judge_scores.csv` to `_private/private_mapping.csv` after LLM-as-judge scoring.

Randomization seed: `20260701`

## Packet Judge Prompts

| packet | case | condition | judge prompt | LLM score |
|---|---|---|---|---:|
| P001 | `city_platform_green_patents` | `generic_agent` | `judge_prompts/P001.md` | - |
| P002 | `city_platform_green_patents` | `ai4ss_factory` | `judge_prompts/P002.md` | - |
| P003 | `platform_theory_mapping` | `ai4ss_factory` | `judge_prompts/P003.md` | - |
| P004 | `platform_theory_mapping` | `generic_agent` | `judge_prompts/P004.md` | - |

## Interpretation

This package is ready for LLM-as-judge scoring. Do not report a factory gain until `llm_judge_scores.csv` has been filled by a model judge.

The appropriate claim is narrow. This package verifies that the local workflow now has an evaluable factory-level contract and a reproducible scoring harness. It does not prove that live agents will always use the factory correctly, that empirical claims are true, or that `.aiss` checker success establishes identification validity.
