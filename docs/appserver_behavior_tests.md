# Codex Appserver Behavior Tests

Date: 2026-07-02

Purpose: check whether `research-starter` and `study-design-builder` behave as
one staged `.aiss` workflow when the user has not started a paper and only has a
vague social-science topic.

## Harness

- Command: `codex app-server --stdio`
- Thread mode: ephemeral
- Cwd: `/Users/siyaozheng/Documents/ai4ss-skills`
- Sandbox: read-only, network disabled
- Approval policy: never
- Turn effort: low
- Output: JSON schema requiring `entry_skill`, `blank_slate_fit`,
  `primary_outputs`, `.aiss` behavior, MIDA behavior, stopping point, and notes
- Scenario: "Does urban renewal change residents trust in local government?"
- File writes, shell calls, MCP calls, and dynamic tool calls: none observed

The first manual TTY probe confirmed the protocol but was not used as evidence
because TTY echo made event parsing noisy. The evidence run used a non-TTY
JSON-RPC controller and reconstructed final messages from
`item/agentMessage/delta` events.

## Results

| skill | thread id | turn status | tool/file events | observed behavior |
|---|---|---|---|---|
| `research-starter` | `019f2084-51b7-72d3-86cc-71f2e356ce9f` | completed | none | Good blank-slate fit. Produces route cards, a minimum viable study, stop reason, researcher decision, and next skill route. `.aiss` is optional at this stage; if durable state is useful, it should be route-only candidate declarations, not a final model layer. |
| `study-design-builder` | `019f2084-b08a-7381-8aa1-0f5acbd86fe4` | completed | none | Poor first entry point for a blank-slate user. It expects a selected route, starter packet, route cards, route-only `.aiss`, data affordances, or author decisions. Normal behavior is to promote one route to selected, add exactly seven MIDA declarations, record decisions, and then add model-layer declarations when warranted. |

## Boundary Confirmed

`research-starter` is the zero-to-one entry skill. It may create candidate
`.aiss` `route` declarations but should not declare full MIDA or stable model
objects.

`study-design-builder` is the route-to-design skill. It should not pretend that
a vague topic is already a selected route. Its correct blank-slate behavior is
to stop or route back to `research-starter` / `ask_author`.

## Implication For The Unified DSL

The two skills are not contradictory. They are sequential writers to the same
`.aiss` v0.4 research object:

```text
vague topic -> candidate .aiss route declarations ->
selected .aiss route + seven mida declarations + decisions ->
model/check declarations when design structure warrants them
```

CSV files and derived Markdown notes are source artifacts only. They must not
mirror or replace workflow state; handoff state belongs in checked `.aiss`
declarations with `route_decl_id`, `mida_id`, or `decision_decl_id` when needed.
