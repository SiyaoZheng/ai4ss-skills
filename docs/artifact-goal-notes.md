# Artifact-Centered Goal Notes

## Sources Checked

- `Deli_AutoResearch` framework page, especially `framework.html#fullmd`, checked on 2026-07-04.
- OpenAI Codex manual, Goal mode section, fetched with the local OpenAI docs helper on 2026-07-04.
- OpenAI Codex manual, `/goal` command sections for the Codex app and CLI.
- `karpathy/autoresearch` README at commit `228791fb499afffb54b46200aca536f79142f117`.
- `karpathy/autoresearch` `program.md` at the same repository head.

## Source Priority

The primary inspiration is `Deli_AutoResearch`'s full Markdown protocol. Codex
`/goal` and `karpathy/autoresearch` are secondary inspirations:

- `Deli_AutoResearch` supplies the long-horizon operational protocol:
  zero-interaction, state files, stall detection, heartbeat watchdogs,
  guardian/tok separation, fresh-session execution, and direction diversity.
- Codex `/goal` supplies the idea of a persistent objective with explicit
  completion criteria.
- `karpathy/autoresearch` supplies a compact artifact-and-metric experiment
  loop: modify a bounded source surface, run a fixed producer/tik, keep
  progress only when the metric improves.

`goal-cli` should be a reusable implementation of the parts of this protocol
that can be made project-local and shareable.

## What FullMD Provides

The FullMD framework is a protocol for long-horizon autonomous tasks. Its core
claim is that failures usually come from missing engineering scaffolding rather
than missing model capability.

The mechanisms that matter most for `goal-cli` are:

- Zero interaction during a run. Ambiguity is resolved inside the loop and
  logged as a decision; the loop does not stop to ask.
- Ready means execute. Preparation exists so the next operational step can be
  performed without confirmation.
- State belongs in files, not conversation memory. Each iteration should be
  reconstructible from curated state.
- Execution and evaluation are separated. The tok does not judge its own
  success.
- Guardian and tok roles are separated. A heartbeat layer checks liveness and
  may restart or nudge, but it should not silently mutate another task's state.
- Stalls require structural pivots. Repeating the same direction is a failure
  mode; after repeated stale iterations, the next direction should differ at the
  level of framing or constraints, not just parameters.
- Validation runs between iterations.

The framework also includes outer operational escalation such as reports and
notifications for unresolvable external dependencies. For `goal-cli`, those
belong outside runtime prompts. The runtime itself still cannot ask for
approval, clarification, or judgment.

## What Codex Goal Mode Provides

Codex Goal mode is a persistent objective inside a Codex session. The goal text
acts as the starting prompt and the completion criteria. Good goals need a
specific outcome, measurable target, or test criteria so Codex can decide
whether it has succeeded.

For `goal-cli`, this is a useful ancestor but not the whole design. Goal mode
keeps the agent oriented; it does not by itself define a project-local artifact,
a reproducible producer command, a blind tik, an tok write scope, a
state file, a lock, or a guardian heartbeat contract.

## What Autoresearch Provides

`karpathy/autoresearch` is not a general todo runner. It is a tight experiment
loop:

- A small project with one primary editable source file.
- A fixed producer/tik path: modify code, train for a fixed 5-minute
  budget, evaluate `val_bpb`.
- A clear keep-or-discard rule from the evaluation result.
- A narrow editable scope so the agent's changes remain reviewable.
- Logs of experiments instead of conversational supervision during the loop.

The durable design lesson is not "research agents can edit code overnight"; it
is that autonomy becomes tractable when the loop has a concrete product,
bounded mutable surface, fixed budget, and machine-checkable evaluation.

## `goal-cli` Design Consequence

A `goal-cli` goal must be centered on one canonical artifact. The artifact can
be a PDF, report, benchmark result, package, site, model checkpoint, dataset, or
other project product. The runtime exists to improve that artifact until the
tik says it satisfies the goal.

This artifact-centered rule is the local sharpening of the FullMD protocol:
the state machine does not merely ask whether "work happened"; it asks whether
the reproduced artifact passes the configured tik.

This means a goal is not:

- A todo list.
- A chat thread memory.
- A generic agent work queue.
- A request for approval.
- A claim that the tok succeeded.

The outer runtime goal is artifact-level. Each tok pass is also a real internal
Codex `/goal`: a bounded source-revision goal whose completion criteria are
scoped to making one source change that can improve the next canonical
artifact. Tik writes `tik.md`, a Markdown ledger containing the artifact
critique. Tok consumes that ledger as a whole; it does not require issue IDs,
categories, or one-to-one bookkeeping. The tok writes a schema-checked JSON
report; it never completes the artifact-level goal directly. A tok can only
change allowed sources so that a later cycle can reproduce the artifact and
the tik can judge it.

After the producer, the runtime has exactly two sequential roles:

- Tik: judges the canonical artifact and writes `tik.md`. Public tik modes are only
  `oracle` for deterministic scripts, tests, metrics, or other machine
  evaluators; and `agent` for model-based evaluation.
- Tok: performs the next bounded source change. The default tok mode
  is `codex_goal`, an internal Codex `/goal` scoped to the tik ledger and
  validated writable scopes.

## Core Runtime Shape

1. Load curated state from files.
2. Acquire the run lock and write heartbeat liveness.
3. Run the producer command.
4. Verify that the canonical artifact exists.
5. Run tik against the artifact and write `tik.md`.
6. If the tik passes, mark the goal complete.
7. If the tik fails, launch one bounded Codex `/goal` tok pass against
   validated writable scopes.
8. Record the schema-checked tok report in files.
9. Start another cycle when run budget remains; otherwise exit with file state
   ready for the next run.

In short: `producer -> tik -> tok -> reproduce -> tik`. The
`reproduce -> tik` part happens at the start of the following cycle, so
the tok's own report is never accepted as artifact success.

Heartbeat is not the unit of work. A heartbeat is a liveness/progress marker
written while a run is active. A cycle is the unit of work. A run may contain
multiple cycles until completion, blocking, stall/pivot policy, cycle budget, or
wall-clock budget stops that invocation. Budget exhaustion is recoverable: a
later run can continue from file state.

## Current Module Boundaries

- Git Gate: `NoMistakesGate` is the only place that knows how to prepare a clean
  Git checkpoint, move off a default branch, choose no-mistakes skip presets,
  and invoke `no-mistakes axi run`.
- Artifact Cycle: `ArtifactCycleRecorder` owns state/history/heartbeat writes
  and transition recording. The runner orchestrates producer, tik, and tok; it
  does not hand-edit heartbeat JSON.
- Tok Execution: `tok_execution` owns the Codex `/goal` command, schema, prompt
  files, report parsing, validation log, and structured `TokExecutionResult`.
- Setup Readiness and Telemetry: doctor uses the same tok smoke path and
  `TelemetryExportPlan` that runtime uses, so readiness checks do not describe
  a separate imaginary path.

## Runtime Prompt Constraint

Runtime prompts are closed-system prompts. They may refer to:

- The canonical artifact.
- The producer command.
- The tik ledger.
- The current state budget.
- The writable source scopes.
- Operational impossibilities such as build failure, missing evidence, invalid
  outputs, repeated identical blockers, or no source change possible.
- Prior directions tried, when needed to enforce direction diversity.
- The fact that the tok is an internal Codex `/goal` with completion limited
  to a bounded source revision.

Runtime prompts must not mention a person who can decide, approve, rescue,
clarify, or arbitrate the work. Human-facing concepts belong only in outer
documentation and configuration comments for maintainers, never in prompts sent
to tik or tok agents.

## State Names Should Reflect Machines, Not People

Prefer terminal or blocked states such as:

- `complete`
- `blocked_producer_failed`
- `blocked_artifact_missing`
- `blocked_tik_failed`
- `blocked_unparseable_tik`
- `blocked_repeated_same_objection`
- `blocked_no_source_change_possible`

Avoid state names that imply a user, author, maintainer, approver, or human
decision is part of the runtime loop.
