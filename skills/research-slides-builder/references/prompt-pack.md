# Prompt Pack

Use these prompts for research presentations and teaching decks.

## Presentation Declarations First

```text
Use $research-slides-builder.

Task: plan a research presentation before editing slides.

Inputs:
- audience: [journal seminar / conference / class / methods workshop]
- time: [minutes]
- research design: [path]
- tables: [paths]
- figures: [paths]
- checked `.aiss` literature evidence declarations or source notes: [paths]
- existing deck: [path if any]

Output `.aiss` presentation artifact declarations:
- slide_id;
- role;
- one claim or task;
- source artifact;
- visual;
- risk;
- action.

Do not edit files yet.
```

## Convert Results To Slides

```text
Use $research-slides-builder to convert verified results into a .aiss presentation artifact declarations and author-fillable slide outline.

Requirements:
- one main claim slot per slide;
- every result claim points to a table, figure, log, or author note;
- preserve sample, FE, clustering, uncertainty, and limits;
- do not invent findings or policy implications;
- do not write final academic slide prose unless it is supplied by the author;
- include an evidence-gap list.
```

## Reveal.js Edit

```text
Use $research-slides-builder to edit this single-file reveal.js deck.

Deck: [path]
Design system: inspect existing CSS variables and components before editing.

Please:
1. keep each `<section>` as one slide;
2. avoid content overflow;
3. use existing classes when possible;
4. preserve Chinese style rules;
5. do not add personal info;
6. for academic research slides, preserve author-supplied wording or use author-fillable claim slots;
7. preview or inspect final HTML if feasible.
```

## Slide Audit

```text
Use $research-slides-builder to audit this deck.

Check:
- unsupported claims;
- one-claim-per-slide discipline;
- readability and overflow;
- table/figure labels;
- uncertainty and sample notes;
- privacy leaks;
- broken assets or CDN assumptions;
- consistency with project AGENTS.md.

Return findings first with slide ids.
```

## Teaching Demo Deck

```text
Use $research-slides-builder for an AI4SS teaching demo deck.

Show process, not only final outputs:
- user prompt;
- agent plan;
- tool/action trace;
- error or uncertainty;
- self-repair;
- output artifact;
- verification checkpoint;
- reusable student takeaway.
```

## Result Figure Slide

```text
Use $research-slides-builder to create a `.aiss` presentation artifact declaration and author-fillable slide outline around one figure.

Figure: [path]
Supporting table/log: [path]

Return:
- title claim slot, not final academic wording;
- figure treatment;
- source/limit line;
- notes on axes, units, baseline period, uncertainty;
- claims to avoid.
```

## Classroom Trace

```text
Bad prompt:
帮我做一个很有冲击力的研究汇报，结论写得强一点。

Improved prompt:
Use $research-slides-builder to create a .aiss presentation artifact declarations first. Every result slide must
point to a table, figure, log, `.aiss` source-evidence id, or author note. Route empirical
validity doubts to $methods-reviewer before editing the deck.

Expected behavior:
Inventory sources -> build presentation declarations -> mark unsupported claims as gaps -> validate
.aiss presentation artifact declarations -> edit only verified slide claims -> inspect the final deck for overflow
and privacy leaks.
```
