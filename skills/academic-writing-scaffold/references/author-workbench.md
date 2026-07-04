# Author Workbench

This workflow keeps AI support on the safe side of academic authorship.

## Boundary Model

Allowed agent outputs:

- map evidence;
- identify missing evidence;
- structure an argument;
- audit claims;
- flag causal-language risks;
- create paragraph skeletons;
- prepare author decision questions.

Disallowed agent outputs:

- final manuscript paragraphs;
- polished introduction or literature review prose;
- abstract or conclusion text for submission;
- final reviewer-response prose;
- claims not grounded in provided evidence.

## Three-Column Writing Workbench

Use this table as the default handoff to the author:

| paragraph | evidence and claim slot | author task |
|---|---|---|
| P1 | empirical problem; source path; allowed scope | write motivation in own voice |
| P2 | literature gap; matrix rows | decide which debate to foreground |
| P3 | design and data facts | choose how much technical detail belongs here |
| P4 | main result slot; table/figure path | write estimate and uncertainty accurately |
| P5 | contribution and boundary | decide claim strength |

The agent may fill the middle column; the author writes the final text.

## Theory Workbench

When literature-to-theory sidecars are present, use
`references/theory_workbench.md` as the author-facing review view. The agent may
fill evidence slots from `literature_theory_synthesis.csv`,
`theory_rival_map.csv`, `theory_scope_map.csv`, validated `.aiss` ids, and
methods issue rows. The author writes final theory prose and decides novelty,
theoretical contribution, mechanism strength, scope framing, and rival
prioritization.

Do not turn the workbench into final literature review, final theory prose, or
polished contribution language. If a row cannot be grounded in validated
evidence or an explicit author premise, keep it as a decision question.

## Evidence Map Procedure

1. List all evidence artifacts.
2. Assign each potential claim a claim type.
3. Link each claim to exact evidence.
4. Mark support level.
5. Identify missing citations or outputs.
6. Convert the map into paragraph skeletons.
7. Stop before final prose.

## Author Decision Questions

Ask these when evidence does not determine the writing choice:

- Which literature audience is primary?
- Should the paper foreground method, data, or substantive contribution?
- How strong should causal language be?
- Is the mechanism a framing hypothesis, tested implication, or theoretical
  contribution?
- Which rival explanation should remain visible in the theory section?
- Is the scope condition a substantive boundary or only a data availability
  limit?
- Which limitations should be in the main text rather than appendix?
- What is the preferred estimand wording?
- Which null or fragile findings should be acknowledged?

## Draft Audit Procedure

When the user provides their own draft:

1. Preserve the author's voice.
2. Flag issues by sentence or claim.
3. Explain why the issue matters.
4. Point to evidence or missing evidence.
5. Suggest a revision strategy, not a replacement paragraph.

## Risk Scale

| risk | meaning | action |
|---|---|---|
| P0 | academic-integrity boundary crossed | refuse direct drafting; provide scaffold instead |
| P1 | unsupported or false claim | flag and require evidence or deletion |
| P2 | overclaim or causal drift | soften by claim type or add diagnostics |
| P3 | unclear wording | suggest author revision target |

## Handoff Format

End with:

- "Author must write final prose."
- evidence gaps;
- decision points;
- safe next action;
- AI-use ledger status when the scaffold supports a manuscript or shared artifact.
