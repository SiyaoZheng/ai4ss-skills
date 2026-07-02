# Prompt Pack

## Intake

```text
Use $research-starter.

Rough question or phenomenon:
<one sentence>

Available materials:
<files, notes, links, seed papers, datasets, or "none yet">

Hard boundaries:
<confidentiality, no final prose, no scraping, no personal data, no invented sources>

Desired next action:
<one small action you want the agent to attempt>

Return a research_starter_packet.md with route cards, a minimum viable study, stop reason, researcher decision needed, handoff prompt, and next_skill_route.
```

## Route Cards

```text
Given this rough topic and materials, produce 2-4 research route cards.

For each route, include research_question, study_type, unit_of_analysis, materials_available, materials_gap, first_action, expected_first_output, failure_signal, feasibility_status, stop_reason, researcher_decision_needed, and next_skill_route.

Do not write final paper prose. Do not invent data availability or citations.
```

## Minimum Viable Study

```text
Choose the smallest viable study among these route cards.

Explain why it can be attempted first, what it can teach us, what it cannot claim, and what one action should happen next.

Stop before robustness checks, final claims, or manuscript prose.
```

## First Action

```text
Run only the first safe action for the selected route.

Inputs:
<file paths or source links>

Action:
<inspect file tree / read variable dictionary / sample sources / build table shell / create extraction schema / draft code skeleton>

Return the first observation, failure signal if any, and the next handoff prompt.
```

## Handoff

```text
Based on this starter packet, hand off to <downstream skill>.

Carry forward only verified materials, known gaps, route_id, stop_reason, researcher_decision_needed, and the selected next action.

Do not expand claims beyond the starter packet.
```
