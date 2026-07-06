---
name: inspect-agent-eval
description: >
  Build and run official Inspect AI / Inspect SWE agent-runtime harness
  evaluations. Use for "Inspect eval", "harness eval", "agent eval",
  "Inspect SWE", "codex_cli eval", "evaluate skills", Docker-sandboxed
  coding-agent evaluations, DeepSeek-backed Inspect runs, and requests to test
  whether Codex/Claude/Gemini skills actually work inside a live agent runtime.
---

# Inspect Agent Eval

Use this skill when the task is to evaluate an agent, a Codex skill, or an
agent-mediated workflow with Inspect AI. The default standard is a real Inspect
`Task` running a real CLI-agent solver inside a sandbox, with auditable logs and
scoring. A subprocess smoke test, unit test, or hand-written local harness is
not a substitute.

## Full-Auto Harness Contract

When invoked by an automatic harness, this skill must not pause for human choice
or return any terminal no-progress state. It must
build or repair the Inspect task, run structural checks, run the formal intended
eval without smoke-only substitution, and report log paths and scorer results.
For AI4SS research-factory evals, the scoring target is the produced
publication-level draft PDF when the eval is PDF-only.

## Non-Negotiable Rules

- Use the official Inspect shape: `Task(dataset=..., solver=..., scorer=..., sandbox=...)`.
- For coding agents, use Inspect SWE solvers such as `codex_cli()`, `claude_code()`, `gemini_cli()`, `opencode()`, or `mini_swe_agent()`.
- Put the challenge inputs in `Sample.input` and `Sample.files`; do not pre-run the answer outside the sandbox.
- Use a fresh Docker sandbox unless the task explicitly specifies another sandbox backend.
- Pass Agent Skills through the Inspect SWE solver's `skills=[...]` option when testing skills.
- Do not call a cancelled run, loader error, or `--limit 1` smoke run a completed eval round.
- Score artifacts produced inside the sandbox. Prefer deterministic scorers for code/data tasks; use model graders only when deterministic scoring is not appropriate.
- Report the Inspect log path, task name, model provider, sample count, score/accuracy, failed-sample explanations, and any run status such as `success`, `error`, or `cancelled`.

## Build Pattern

1. Confirm the current API if the local code or docs are ambiguous. Prefer
   official Inspect AI and Inspect SWE docs, then inspect local package source.
2. Create an `@task` function returning `inspect_ai.Task`.
3. Define a multi-sample dataset with `Sample` objects. Each sample should be a
   self-contained task fixture.
4. Use an Inspect SWE agent solver. For Codex CLI, the usual form is:

   ```python
   from inspect_swe import codex_cli

   solver = codex_cli(
       skills=[str(path_to_skill_dir)],
       web_search="disabled",
       goals=False,
       config_overrides={"approval_policy": "never"},
   )
   ```

5. Use `sandbox=("docker", "Dockerfile")` or an equivalent Docker config. The
   Docker image must contain every runtime dependency the evaluated agent needs.
6. Write a scorer that reopens the sandbox after the solver finishes, reruns or
   inspects the produced files, and returns `Score(value=..., explanation=...)`.
7. Run a load check before spending model tokens:

   ```bash
   python3 -m py_compile path/to/task.py scripts/run_eval.py
   inspect list tasks path/to/task.py
   ```

8. Run the formal eval without `--limit` unless deliberately doing smoke
   testing. If a run is interrupted, resume with `inspect eval-retry <log.eval>`
   rather than silently starting a different benchmark.

## DeepSeek Inspect Provider

For Adrian's current AI4SS harness work, default to DeepSeek V4 Pro through
Inspect's OpenAI-compatible provider:

```bash
export DEEPSEEK_BASE_URL=https://api.deepseek.com
export DEEPSEEK_API_KEY=...
inspect eval path/to/task.py \
  --model openai-api/deepseek/deepseek-v4-pro
```

If tool-calling or schema handling fails with an OpenAI-compatible provider,
test whether Inspect's model options support an emulation flag for the installed
version before changing the task semantics.

## Evidence Standard

The final answer for an eval task must distinguish:

- Structural validation: imports, task discovery, Docker build, and dry runs.
- Smoke evidence: one or a few samples used only to verify wiring.
- Formal evidence: the complete intended sample set, completed successfully,
  with Inspect logs and scorer results.
- Iteration evidence: concrete skill or task changes made because of failing
  samples, then a rerun showing whether the fix worked.

When evaluating Agent Skills, cite or record the skill directories used, the
exact Inspect SWE solver, and the final `.eval` log path. This is what makes the
result a harness eval rather than a local demonstration.
