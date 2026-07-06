# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog, and this project uses semantic versioning
while the public interface remains unstable.

## Unreleased

### Added

- Runtime tok mutation audit that records direct artifact mutation.
- Runtime tok mutation audit that records changes outside declared source,
  runtime, and goal state scopes.
- Focused regression coverage for tok artifact and generated-output boundary
  enforcement.
- MIT license, security policy, CI workflow, and package metadata for public
  repository hygiene.

### Changed

- `tok` passes are expected to leave the configured artifact untouched; the
  producer remains responsible for rebuilding the artifact on the next
  heartbeat, and goal-cli records violations as audit evidence instead of
  treating them as terminal runtime gates.

## 0.1.0 - 2026-07-05

### Added

- Initial artifact-centered heartbeat runtime.
- Producer, tik, and tok flow with schema-checked tok reports.
- Codex and Claude Code tok providers.
- Oracle, Codex file, Claude Code file, and API tik providers.
- Local state, run records, cleanup, doctor checks, and system heartbeat
  helpers.
