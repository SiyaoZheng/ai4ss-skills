# Response Workflow

Use this reference for journal R&R planning, response scaffolds, and
AI-disclosed response working text. Do not present AI-assisted response text as
direct-submission ready or no-AI until the disclosure/submission gate passes.

## 1. Comment Decomposition

Split compound comments. A paragraph can contain multiple requests:

- Explain a theoretical mechanism.
- Add a robustness check.
- Cite a missing paper.
- Clarify a variable.
- Tone down a causal claim.

Each request needs its own status and action.

## 2. Confidentiality Check

Before using external tools, mark the material:

- `cleared`: author has approved use as-is.
- `redacted`: identifying or confidential details removed.
- `needs_approval`: do not send externally yet.
- `do_not_share`: keep local only.

Reviewer reports and editor letters default to `needs_approval` unless the project instructions explicitly clear them.

## 3. Status Decisions

Use these statuses:

- `accept`: make the requested change.
- `partial`: address the underlying concern but not every requested item.
- `clarify`: text was unclear; no new analysis needed.
- `rebut`: respectfully disagree with reason and evidence.
- `cannot_do`: data, ethics, access, or design makes it infeasible.
- `needs_author`: requires a substantive author decision.

## 4. Response Scaffold Patterns

Use these as structures for the author to complete, not as final copy.

### Accept Scaffold

```text
Reviewer concern:
Author position:
Change made:
Manuscript location:
Evidence/output:
Boundary to state:
```

### Partial Scaffold

```text
Reviewer concern:
Part accepted:
Part not adopted:
Reason/boundary:
Alternative evidence or clarification:
Manuscript location:
```

### Rebut Scaffold

```text
Reviewer concern:
Why the requested change is not adopted:
Design/data boundary:
Clarification added:
Evidence location:
Risk if stated too strongly:
```

### Cannot Do Scaffold

```text
Requested item:
Reason infeasible:
Limitation to acknowledge:
Alternative check, if any:
Manuscript location:
```

## 5. Evidence Check

Before finalizing:

- Does the manuscript location exist?
- Does the new analysis output exist?
- Does the response match the actual sign, magnitude, and sample?
- Is the planned response consistent with revised manuscript wording?
- Are appendix/table/figure numbers current?
- Is `confidentiality_status` compatible with the planned tool or sharing context?

## 6. Tone

Use firm, specific language. Avoid:

- Over-apologizing.
- Claiming the reviewer is wrong in broad terms.
- Promising future work as a substitute for current evidence.
- Saying "we believe" when a table or design fact can be cited.
