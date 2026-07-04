# Worked Example: R&R Decomposition

This example shows response planning with AI-disclosed response working text.

## Reviewer Comment

```text
R2.3: The paper relies heavily on a DID design, but the parallel trends assumption is not sufficiently justified. The authors should add an event-study figure, discuss whether early adopting cities were already on different trajectories, and clarify why standard errors are clustered at the city level.
```

## Atomic Requests

| comment_id | request | type | severity | status |
|---|---|---|---|---|
| R2.3a | justify parallel trends | identification | high | accept |
| R2.3b | add event-study figure | robustness | high | accept |
| R2.3c | discuss early adopters | identification | medium | partial |
| R2.3d | clarify city clustering | inference | medium | clarify |

## Evidence Needed

| comment_id | evidence |
|---|---|
| R2.3a | revised empirical strategy paragraph; event-study diagnostic |
| R2.3b | `output/figures/event_study.svg`; script path |
| R2.3c | cohort timing table; pre-treatment outcome comparison |
| R2.3d | model script and table note |

## AI-Disclosed Response Working Draft

### R2.3a

| slot | content to fill |
|---|---|
| reviewer concern | parallel trends not sufficiently justified |
| author position | [author states agreement level] |
| action taken | [what text/analysis was added] |
| evidence/location | [section/table/figure path] |
| boundary | [what the diagnostic can and cannot prove] |
| risk note | do not claim pre-trend test proves parallel trends |
| working response text | [AI-assisted working text; not direct-submission ready until gate passes] |

### R2.3c

| slot | content to fill |
|---|---|
| reviewer concern | early adopters may differ |
| author position | [author states how seriously this affects design] |
| action taken | [cohort timing table / sensitivity / textual limitation] |
| evidence/location | [appendix or main table] |
| boundary | [remaining selection concern] |
| risk note | avoid dismissing the concern if only partially tested |
| working response text | [AI-assisted working text; not direct-submission ready until gate passes] |

## Done-Evidence Audit

Before direct-submission status is marked ready:

- event-study figure exists and opens;
- omitted period and confidence bands are visible;
- table note states city clustering;
- revised manuscript actually discusses early adopters;
- response scaffold does not promise stronger evidence than the diagnostics provide.
- AI contribution disclosure, human accountability, confidentiality, and
  outlet-policy status are explicit.

## Validator-Ready Matrix Row

```csv
comment_id,reviewer_text,request_type,mida_element_affected,severity,status,planned_action,evidence_needed,file_or_section,owner,done_evidence,response_summary,author_position_status,confidentiality_status,open_question
R2.3b,add event-study figure,robustness,diagnose,high,accept,produce event-study figure and update caption,output/figures/event_study.svg,appendix figure A2,agent,output/figures/event_study.svg; manuscript appendix A2,author will state what the diagnostic shows without claiming proof of parallel trends,author_decided,redacted,none
```

## Classroom Debrief

What students should notice:

- The agent splits one paragraph into four tasks.
- The agent may draft working response text, but it is labeled AI-assisted and
  gated before direct submission.
- The author decides the strategic stance.
- Every response slot points to evidence or a manuscript location.
