# Prompt Pack

Use these prompts to support AI-disclosed manuscript work.

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

Single boundary:
- any drafted prose is AI-assisted working text;
- do not mark it direct-submission ready or no-AI until disclosure,
  accountability, outlet-policy, and direct-submission status are explicit.

Output:
1. evidence inventory;
2. `.aiss` bounded claim declarations;
3. which claims are supported, partial, weak, or missing;
4. assumptions and claim-boundary choices needed before draft-PDF assembly.
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
- assumption or claim-boundary choice.

Optionally include AI-assisted working text for each paragraph and mark
direct_submission_status as not_ready until the gate is complete.
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
- places where assumptions must be disclosed or claims narrowed.

You may provide replacement working wording when useful. Mark it as AI-assisted
working text and list the disclosure/submission gate still required.
```

## Literature Review Scaffold

```text
Use $academic-writing-scaffold with these checked `.aiss` literature evidence declarations.

Goal: prepare an author-facing literature review structure.

If you draft review prose, keep source locators visible and mark it as
AI-assisted working text, not direct-submission ready.

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
- boundaries the draft must state;
- claims to avoid.

Optional result prose must be labeled AI-assisted working text and tied to
claim slots, uncertainty, and disclosure status.
```

## Classroom Trace

```text
Bad prompt:
请直接写一版可以不加说明就投稿的结果段落，语气像顶刊论文。

Improved prompt:
Use $academic-writing-scaffold to build a results workbench and AI-assisted
working paragraph draft. Return claim slots, evidence paths, risk labels,
revision targets, assumptions to disclose, and disclosure/direct-submission
status.

Expected behavior:
Inventory tables and figures -> create bounded claim declarations -> validate the .aiss declaration set ->
flag unsupported mechanism claims -> draft only AI-disclosed working text ->
continue until draft-PDF text has explicit disclosure and direct-submission status.
```
