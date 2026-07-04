# Prompt Pack

Use these prompts to support writing without outsourcing authorship.

## Evidence Map

```text
Use $academic-writing-scaffold.

Task: build an evidence map for [section name].

Inputs:
- research design: [path]
- tables: [paths]
- figures: [paths]
- `.aiss` literature evidence declarations: [path]
- author notes: [path]

Hard boundary:
- do not write final manuscript prose;
- do not write paragraphs for insertion into the paper.

Output:
1. evidence inventory;
2. `.aiss` bounded claim declarations;
3. which claims are supported, partial, weak, or missing;
4. author decisions needed before writing.
```

## Section Scaffold

```text
Use $academic-writing-scaffold to prepare a section scaffold.

Target section: [introduction / literature review / empirical strategy / results / mechanisms / conclusion]
Audience or journal style: [if known]
Length target: [if known]

Return a table with:
- paragraph number;
- paragraph purpose;
- claim slot;
- evidence to use;
- citation or source path;
- risks to avoid;
- author decision.

Do not fill the paragraph with final prose.
```

## Table-To-Claim Audit

```text
Use $academic-writing-scaffold to audit which claims can be made from this table.

Table: [path]
Design notes: [path]

Return:
- dependent variable;
- treatment/exposure;
- preferred model column;
- sample and N;
- FE and clustering;
- magnitude and uncertainty;
- allowed claim;
- disallowed overclaim;
- missing information.
```

## User Draft Audit

```text
Use $academic-writing-scaffold to audit my draft text.

Draft: [paste or path]
Evidence files: [paths]

Please flag:
- unsupported claims;
- missing citations;
- causal language that exceeds design;
- mechanism claims without evidence;
- estimand drift;
- vague or promotional phrasing;
- places where the author must decide.

Do not rewrite the section. Provide issue-by-issue notes and optional micro-level wording warnings only.
```

## Literature Review Scaffold

```text
Use $academic-writing-scaffold with these checked `.aiss` literature evidence declarations.

Goal: prepare an author-facing literature review structure.

Do not write review prose.

Output:
1. clusters of papers;
2. debate or mechanism each cluster addresses;
3. what each cluster supports;
4. what it does not support;
5. how the current project can be positioned;
6. citation gaps and verification gaps.
```

## Results Section Workbench

```text
Use $academic-writing-scaffold to prepare a results-writing workbench.

Inputs:
- main table: [path]
- event-study figure: [path]
- robustness table: [path]
- sample-flow audit: [path]

Return:
- result claim slots;
- evidence path for each slot;
- units and uncertainty to report;
- diagnostics to mention;
- boundaries the author must state;
- claims to avoid.

No final result prose.
```

## Classroom Trace

```text
Bad prompt:
请直接写一版结果段落，语气像顶刊论文。

Improved prompt:
Use $academic-writing-scaffold to build a results workbench only. Return claim slots,
evidence paths, risk labels, revision targets, and author decision questions.
Do not provide replacement wording or final manuscript prose.

Expected behavior:
Inventory tables and figures -> create bounded claim declarations -> validate the .aiss declaration set ->
flag unsupported mechanism claims -> stop at author-facing scaffold.
```
