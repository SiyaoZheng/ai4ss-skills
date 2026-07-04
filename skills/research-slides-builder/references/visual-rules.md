# Visual Rules

Use this reference when converting research evidence into slides.

## Tables

- Do not paste full regression tables if they are unreadable.
- Extract the 1-3 columns needed for the slide claim.
- Show dependent variable, sample, fixed effects, clustering, and N.
- Keep full table path available in speaker notes or source line when appropriate.

## Figures

- Keep axis labels, units, baseline periods, and uncertainty visible.
- For event-study plots, label treatment time, omitted period, and confidence bands.
- For coefficient plots, state model family and sample.
- Do not crop away legends needed to understand the claim.

## Layout

- Use stable dimensions for repeated cards, code blocks, and charts.
- Avoid text overlap and tiny labels.
- Use compact headers in dashboards or tool surfaces.
- Do not put a slide section inside a decorative card.
- Use visual hierarchy: title claim, evidence visual, source/limit.

## Evidence And Privacy Audit

Before final delivery:

- Every result claim points to a table, figure, or author note.
- Every evidence slide states `sample_or_scope`.
- Every evidence slide states `uncertainty_or_caveat`.
- Every evidence slide states `interpretation_boundary`.
- Every evidence slide records `privacy_status`.
- No API keys, emails, phone numbers, private file paths, or confidential rows appear.
- No institutional or personal identity appears unless explicitly requested.
- Claims do not exceed the study design.
- Exported file opens and key slides render correctly.

Validator-ready slide maps use:

```csv
slide_id,role,claim,source_artifact,sample_or_scope,uncertainty_or_caveat,visual,privacy_status,interpretation_boundary,risk,action
```
