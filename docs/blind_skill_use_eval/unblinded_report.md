# Unblinded Skill-Use Evaluation Report

This report joins `llm_judge_scores.csv` to `private_mapping.csv` after scoring.

| packet | case | condition | LLM score | judge prompt |
|---|---|---|---:|---|
| P001 | `data_provenance` | `skill_guided` | - | `judge_prompts/P001.md` |
| P002 | `data_provenance` | `no_skill` | - | `judge_prompts/P002.md` |
| P003 | `literature_evidence` | `no_skill` | - | `judge_prompts/P003.md` |
| P004 | `literature_evidence` | `skill_guided` | - | `judge_prompts/P004.md` |
| P005 | `claim_discipline` | `skill_guided` | - | `judge_prompts/P005.md` |
| P006 | `claim_discipline` | `no_skill` | - | `judge_prompts/P006.md` |
| P007 | `revision_trace` | `skill_guided` | - | `judge_prompts/P007.md` |
| P008 | `revision_trace` | `no_skill` | - | `judge_prompts/P008.md` |

This package is ready for LLM-as-judge scoring. Do not report a skill-use gain until `llm_judge_scores.csv` has model judge scores.

Interpretation must remain narrow. This structural packet package can test whether outputs expose audit artifacts, validation gates, AI-use disclosure, and explicit assumption registers. It is not evidence that any particular live LLM will behave this way.
