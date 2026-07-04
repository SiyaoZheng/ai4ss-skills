# Worked Example: DID Result Deck Map

This example shows how to turn verified artifacts into slides without inventing conclusions.

## Inputs

| artifact | role |
|---|---|
| `docs/research_design.md` | design and estimand |
| `output/audit/.aiss row-loss checks` | sample and restrictions |
| `output/tables/table1_baseline.csv` | main estimate |
| `output/figures/event_study.svg` | diagnostic and dynamics |
| `output/tables/robustness.csv` | sensitivity |

## Presentation Declarations

| slide | role | claim/task | source | visual | risk |
|---|---|---|---|---|---|
| 1 | question | Ask whether policy pilot affected city innovation output | author note | title + setting | too broad if outcome hidden |
| 2 | data | Analysis sample is city-year panel for 2012-2023 | .aiss row-loss checks | row-loss table | missing row-loss explanation |
| 3 | design | Identification relies on treated vs untreated city-year comparison | research_design.md | design diagram | causal assumption must be explicit |
| 4 | result | Preferred specification reports positive post-adoption difference | table1_baseline.csv | coefficient card + mini table | needs units and uncertainty |
| 5 | diagnostic | Event-study plot checks pre-treatment pattern and dynamics | event_study.svg | figure | omitted period must be visible |
| 6 | robustness | Estimate is compared across alternative samples/specifications | robustness.csv | compact table | do not cherry-pick |
| 7 | boundary | Evidence supports a bounded claim, not broad policy success | design + diagnostics | checklist | must avoid policy overclaim |

## Good Slide Title Examples

- "The analysis sample loses 3% of rows after complete-control restriction"
- "The event-study baseline is year -1, with uncertainty shown for each lead and lag"
- "The preferred estimate is bounded to city-year patent outcomes"

## Bad Slide Title Examples

- "The policy worked"
- "AI proves the result"
- "Innovation capacity was transformed"

## Evidence-Gap List

The agent should flag:

- no mechanism table;
- no external validity evidence;
- no author-approved policy implication;
- pre-trend uncertainty needs visible labels;
- sample-flow row loss needs explanation.

## Classroom Debrief

What students should notice:

- Slides are generated from artifacts, not from imagination.
- Each claim has a source path.
- The deck includes limitations as part of the argument.
- The agent can format and audit, but the researcher owns interpretation.
