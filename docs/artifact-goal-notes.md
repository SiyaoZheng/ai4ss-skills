# Thing-Centered Goal Notes

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
loop: modify a controlled source surface, run a fixed producer/tik, keep
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
controlled mutable surface, fixed budget, and machine-checkable evaluation.

## `goal-cli` Design Consequence

A `goal-cli` goal must be centered on one finished thing. The thing can
be a PDF, report, benchmark result, package, site, model checkpoint, dataset, or
other project product. The runtime exists to improve that artifact until the
tik says it satisfies the goal.

This thing-centered rule is the local sharpening of the FullMD protocol:
the state machine does not merely ask whether "work happened"; it asks whether
the finished thing produced from source passes the configured tik.

This means a goal is not:

- A todo list.
- A chat thread memory.
- A generic agent work queue.
- A request for approval.
- A claim that the tok succeeded.

The outer goal is artifact-level. Each tok pass is an internal Codex `/goal`.
It treats itself as the last tok: read `tik.md`, make runtime-audited source
changes, leave source ready for the next artifact to answer tik's blocking
objections, and stop. Tok never completes the artifact-level goal.

After the producer, the runtime has exactly two sequential roles:

- Tik: judges the finished thing and writes `tik.md`. Public tik modes are
  `oracle` for deterministic scripts, tests, metrics, or other machine
  evaluators; `checklist` for command-backed checklist review providers;
  `api` for API-backed file-upload evaluation with optional
  `tik.skill` expansion; `codex_file` for Codex evaluation of a local artifact
  copy in an ephemeral read-only workspace; and `claude_code_file` for Claude
  Code evaluation of a local artifact copy with write tools disallowed. A tik
  phase may fan out to multiple configured providers in parallel; the runtime
  waits for all provider verdicts, writes provider-specific ledgers, and hands
  tok one aggregate `tik.md`. If any tik provider fails, returns unparseable
  output, or reports a stale artifact hash, the heartbeat blocks before tok.
- Tok: reads `tik.md` and changes allowed source so the next artifact can
  answer the blocking objections. Public tok modes are `codex_goal` for
  `codex exec` with `/goal`, `codex_app_server` for
  `codex app-server --stdio` with a real app-server thread goal, and
  `claude_code_goal` for the same source-fixing pass through Claude Code.

## Core Runtime Shape

1. Load curated state from files.
2. Acquire the run lock and write heartbeat liveness.
3. Prepare the no-mistakes Git gate when enabled.
4. Run the producer command.
5. Verify that the finished thing exists.
6. Run tik provider(s) against the artifact and write aggregate `tik.md`.
7. Reject stale or unparseable tik output before tok.
8. If the tik passes, run the completion gate and mark the goal complete.
9. If the tik fails, launch one tok pass against validated source boundaries.
10. Record the runtime-owned tok audit report plus source-diff evidence in
    files.
11. Exit with file state ready for the next heartbeat.

In short: `producer -> tik -> tok` when tik fails, or `producer -> tik` when tik
passes. Tok is not asked to report artifact success.

Heartbeat is the unit of autonomous work. A run contains exactly one heartbeat,
then exits. The next run continues from file state and may rebuild the artifact
and run tik again. Budget exhaustion is recoverable: a later run can continue
from file state.

## Current Module Boundaries

- Git Checkpoint: `NoMistakesCheckpoint` is the only place that knows how to prepare a clean
  Git checkpoint, preserve the current mainline branch, choose no-mistakes skip
  presets, honor run budgets, and invoke or skip `no-mistakes axi run` according
  to branch constraints.
- Lifecycle: `lifecycle.py` owns machine state names and clock abstractions for
  active, healthy, blocked, stopped, due, running, succeeded, failed, and
  cancelled calls.
- Heartbeat State: `HeartbeatRecorder` owns state/history/heartbeat writes
  and transition recording. The runner orchestrates producer, tik, and tok; it
  does not hand-edit heartbeat JSON.
- Capability Lease: `lease.py` owns exact and glob authorization for create,
  modify, delete, and rename operations. Deny rules override allow rules, and a
  rejected mutation batch applies nothing.
- Isolated Execution: `isolation.py` owns dirty/untracked baselines, isolated
  producer and command-tik workspaces, finalization, and symlink escape
  rejection before canonical files are touched.
- Transactions: `transaction.py` owns durable staging, journal states,
  repository serialization, drift conflicts, checkpointing, and restart
  recovery for leased multi-file mutations.
- Provider Contract: `provider_contract.py` owns shared preflight and writable
  root policy for Codex exec, Codex app-server, Claude Code, and command-backed
  providers.
- Attempt Supervisor: `supervisor.py` owns bounded recent attempt evidence,
  deterministic outcome aggregation, immutable goal/lease binding, and
  substantive reframe angle selection.
- Tok Execution: `tok_execution` owns the Codex `/goal`, Codex app-server, and
  Claude Code tok commands, prompt files, attachment integrity check, and
  runtime-owned audit `TokExecutionResult`.
- Setup Readiness and Telemetry: doctor uses the same tok smoke path and
  `TelemetryExportPlan` that runtime uses, so readiness checks do not describe
  a separate imaginary path.

## Runtime Prompt Constraint

Runtime prompts are closed-system prompts. They may refer to:

- The finished thing.
- The producer command.
- The tik ledger.
- The current state budget.
- The writable source scopes.
- Operational impossibilities such as build failure, missing evidence, invalid
  outputs, or repeated identical blockers.
- Prior directions tried, when needed to enforce direction diversity.
- The fact that the tok is an internal Codex `/goal` with completion limited
  to source changes.

Runtime prompts must not mention a person who can decide, approve, rescue,
clarify, or arbitrate the work. Human-facing concepts belong only in outer
documentation and configuration comments for maintainers, never in prompts sent
to tik or tok agents.

## State Names Should Reflect Machines, Not People

Prefer terminal or blocked states such as:

- `complete`
- `blocked_invalid_review_evidence`

Avoid state names that imply a user, author, maintainer, approver, or human
decision is part of the runtime loop.

Repeated objections, no source changes, tok provider failures, and no-mistakes
failures are intentionally not blocked states. They are recorded as machine
evidence while the heartbeat remains active.
