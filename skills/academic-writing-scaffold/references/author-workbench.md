# Writing Workbench

This workflow keeps AI support visible, auditable, and gated before submission.

## Boundary Model

Allowed agent outputs:

- map evidence;
- identify missing evidence;
- structure an argument;
- audit claims;
- flag causal-language risks;
- create paragraph skeletons;
- draft AI-assisted working paragraphs;
- prepare assumption and claim-boundary notes.

The only disallowed output:

- text presented as direct-submission ready or as having no AI involvement when
  AI contributed to it.
- claims not grounded in provided evidence.

## Three-Column Writing Workbench

Use this table as the default handoff:

| paragraph | evidence and claim slot | AI-assisted working text / next action |
|---|---|---|
| P1 | empirical problem; source path; allowed scope | draft or revise motivation; mark disclosure status |
| P2 | literature gap; matrix rows | select the best-supported debate foregrounding |
| P3 | design and data facts | include the technical detail needed for transparency |
| P4 | main result slot; table/figure path | write estimate and uncertainty accurately |
| P5 | contribution and boundary | state defensible claim strength |

The agent may draft working text. The package remains submission-ineligible
until disclosure, accountability, outlet policy, and direct-submission status
are explicit.

## Theory Workbench

When literature-to-theory .aiss projections are present, use
`references/author workbench declarations` as the author-facing review view. The agent may
fill evidence slots from `.aiss theory synthesis declarations`,
`.aiss rival-check declarations`, `.aiss scope-check declarations`, validated `.aiss` ids, and
methods issue rows. AI may draft working theory prose and select the strongest
defensible novelty, contribution, mechanism, scope, and rival framing while
recording assumptions and evidence needs.

Do not turn the workbench into no-AI or direct-submission-ready prose. If a row
cannot be grounded in validated evidence or an explicit premise, keep it as an
assumption to disclose or route it to evidence expansion.

## Evidence Map Procedure

1. List all evidence artifacts.
2. Assign each potential claim a claim type.
3. Link each claim to exact evidence.
4. Mark support level.
5. Identify missing citations or outputs.
6. Convert the map into paragraph skeletons or AI-assisted working prose.
7. Continue until direct-submission status is explicit and draft-PDF text is bounded.

## Automatic Claim-Boundary Choices

Resolve these when evidence does not determine the writing choice:

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
5. Suggest a revision strategy or replacement working paragraph with AI-use
   disclosure status.

## Risk Scale

| risk | meaning | action |
|---|---|---|
| P0 | hidden-AI or direct-submission gate crossed | refuse submission-ready/no-AI presentation; provide AI-disclosed working text and gate checklist |
| P1 | unsupported or false claim | flag and require evidence or deletion |
| P2 | overclaim or causal drift | soften by claim type or add diagnostics |
| P3 | unclear wording | suggest author revision target |

## Handoff Format

End with:

- AI-assisted working-text status;
- direct-submission status;
- evidence gaps;
- decision points;
- safe next action;
- AI-use ledger status when the scaffold supports a manuscript or shared artifact.
