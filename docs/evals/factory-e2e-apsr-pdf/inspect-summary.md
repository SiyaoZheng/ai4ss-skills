# Factory E2E Data-Backed APSR PDF Inspect Eval

Model: `openai-api/deepseek/deepseek-v4-pro`

Input shown to the agent:

```text
Idea: Does neighborhood service-center exposure change resident civic trust?
```

Only scored file: `paper/full_draft.pdf`.

The PDF must visibly document public data discovery, data construction, empirical analysis, and limitations; intermediate files are not scoring evidence.

| condition | status | score_100 | log |
| --- | --- | ---: | --- |
| `full_research_factory_skills` | success | 55.0 | `/tmp/ai4ss-apsr-pdf-logs/2026-07-05T06-39-29-00-00_factory-e2e-apsr-pdf_52UvYjwpD7k8s9pFnKTdmo.eval` |

## Sample Details

| condition | pdf bytes | text chars | judge note |
| --- | ---: | ---: | --- |
| `full_research_factory_skills` | 255979 | 36485 | SCORE: 55 REASON: The manuscript addresses a clear, well-motivated research question and provides a well-structured theoretical framework, analysis design, and transparent limitations. However, all empirical results are based on synthetic d |

## Marginal Gain

- `full_vs_no_skills`: -
- `full_research_factory_skills_score`: 55.0
- `no_skills_score`: -
