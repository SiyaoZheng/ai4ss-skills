# Starter Workflow

The first research loop is a production workflow. Its job is to create a research object that can later be audited.

## Intake

Collect only four fields at the start:

| field | question |
|---|---|
| `rough_question` | What phenomenon, puzzle, or policy setting does the researcher care about? |
| `available_materials` | What files, notes, papers, links, datasets, interviews, or tables already exist? |
| `hard_boundaries` | What cannot be used, shared, claimed, scraped, or written by AI? |
| `desired_next_action` | What one small action does the researcher hope AI can do next? |

If one field is missing, continue with a smaller action unless the missing field affects confidentiality, data access, or authorship.

## Research Starter Packet

Write a one-page packet with these headings:

```markdown
# Research Starter Packet

## Research Question
One sentence, marked as provisional.

## Materials Inventory
Usable, uncertain, unavailable, and off-limits materials.

## Evidence Affordance
What the current materials can support, cannot support, and might support after one more action.

## Route Cards
Two to four candidate routes, or one selected route plus rejected alternatives.

## AISS Route Declarations
`research_model.aiss` route declarations when a durable workflow object is created; otherwise state `not_created:<reason>`.

## Minimum Viable Study
The smallest study that can produce one checkable observation.

## First Observation
Only if a source, file, table, or sample was actually inspected.

## Stop Reason
Why the agent stops here instead of continuing.

## Researcher Decision Needed
Author-only decisions before the next round.

## Handoff Prompt
A copy-ready prompt for the next agent turn.

## Next Skill Route
The downstream skill, or `none` when more author choice is needed.
```

## Stop Rules

Stop when any of these is true:

- The next step requires author judgment about novelty, theory, causal credibility, or public claim strength.
- The material path is unknown, inaccessible, confidential, or not yet approved for AI use.
- The proposed action would draft final manuscript prose.
- The route depends on data, variables, or sources that have not been verified.
- A downstream skill has a narrower responsibility and should take over.

## First-Loop Completion

The first loop is complete only when the researcher has:

- at least one feasible route;
- one minimum viable study;
- one next executable action;
- one stop reason;
- one author decision point;
- one handoff route or a clear reason not to continue.

If the loop is meant to continue across skills, it should also have either a
route-only `.aiss` artifact or a clear reason why no durable `.aiss` route was
created.
