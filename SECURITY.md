# Security Policy

## Supported Versions

`goal-cli` is early local tooling. Security fixes target the current `master`
branch until the project starts publishing supported release lines.

## Reporting a Vulnerability

Please report security issues privately by opening a GitHub security advisory
for `SiyaoZheng/goal-cli` when available, or by contacting the maintainer
directly through the repository owner profile.

Do not include secrets, API keys, private artifacts, or private project data in
public issues.

## Trust Model

`goal.toml` is executable local project configuration. Producer and oracle
commands run on the local machine, and tok providers may run coding agents over
declared project scopes. Only run `goal-cli` against repositories and
configuration files you trust.

The runtime is designed to keep source edits, generated outputs, state, and the
final artifact separated, but those boundaries are defense in depth rather than
a sandbox for untrusted code.
