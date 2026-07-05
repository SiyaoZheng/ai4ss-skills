#!/usr/bin/env python3
"""Audit cross-skill handoff continuity for AI4SS research-factory `.aiss` files.

The audit is intentionally deterministic. It compiles the `.aiss` file with the
local v0.4 DSL toolchain, reads the structured AST, and checks whether route,
MIDA, decision, provenance, artifact, check, and claim references remain
consumable by downstream skills.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai4ss_factory_contracts.workflow import (
    MIDA_COMPONENTS,
    route_enum_error,
    status_route_errors,
)


ROOT = Path(__file__).resolve().parents[1]
AISS = ROOT / "dsl" / "scripts" / "aiss.py"

ALTERNATIVE_STATE_MARKERS = (
    "route_decl_id",
    "mida_id",
    "decision_decl_id",
    "next_skill_route",
    "handoff_ready",
    "ready_for_handoff",
)
ALLOWED_LOG_FILES = {"stage_log.md", "handoff_audit.json", "audit.json"}
TEXT_STATE_SUFFIXES = {".md", ".csv", ".tsv", ".txt", ".json", ".yaml", ".yml"}
REPAIR_STATUSES = {
    "repair_required",
    "needs_data_check",
    "needs_literature_check",
    "needs_methods_review",
}
EXECUTION_ROUTES = {
    "research-analysis-runner",
    "top-journal-figures",
    "academic-writing-scaffold",
    "research-slides-builder",
    "reviewer-response",
}


@dataclass
class Finding:
    severity: str
    metric: str
    code: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "severity": self.severity,
            "metric": self.metric,
            "code": self.code,
            "message": self.message,
        }
        if self.evidence:
            payload["evidence"] = self.evidence
        return payload


@dataclass
class MetricBucket:
    name: str
    passed: int = 0
    total: int = 0

    def check(
        self,
        condition: bool,
        findings: list[Finding],
        *,
        code: str,
        message: str,
        severity: str = "error",
        evidence: dict[str, Any] | None = None,
    ) -> None:
        self.total += 1
        if condition:
            self.passed += 1
            return
        findings.append(
            Finding(
                severity=severity,
                metric=self.name,
                code=code,
                message=message,
                evidence=evidence or {},
            )
        )

    def to_json(self) -> dict[str, Any]:
        score = 1.0 if self.total == 0 else self.passed / self.total
        return {"passed": self.passed, "total": self.total, "score": round(score, 4)}


def run_aiss(command: str, path: Path) -> tuple[dict[str, Any] | None, str | None]:
    result = subprocess.run(
        [sys.executable, str(AISS), command, str(path), "--strict"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None, (result.stderr or result.stdout).strip()
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"could not parse `aiss {command}` JSON output: {exc}"


def coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def record_kind(record: dict[str, Any]) -> str:
    return str(record.get("decl_type") or record.get("kind") or "")


def ast_records(ast: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key in ("sources", "spans", "objects", "relations", "models", "checks", "derives"):
        value = ast.get(key, [])
        if isinstance(value, list):
            records.extend(item for item in value if isinstance(item, dict))
    workflow = ast.get("workflow", {})
    if isinstance(workflow, dict):
        for key in ("routes", "mida", "decisions", "events"):
            value = workflow.get(key, [])
            if isinstance(value, list):
                records.extend(item for item in value if isinstance(item, dict))
    return records


def records_by_kind(ast: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [record for record in ast_records(ast) if record_kind(record) == kind]


def record_ids(records: list[dict[str, Any]]) -> list[str]:
    return sorted(str(record.get("id")) for record in records if record.get("id"))


def add_warning(
    findings: list[Finding],
    *,
    metric: str,
    code: str,
    message: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    findings.append(
        Finding(
            severity="warning",
            metric=metric,
            code=code,
            message=message,
            evidence=evidence or {},
        )
    )


def status_route_finding(
    findings: list[Finding],
    *,
    metric: str,
    bucket: MetricBucket,
    context: str,
    row: dict[str, Any],
) -> None:
    route = str(row.get("next_skill_route", ""))
    if not route:
        return
    row_id = str(row.get("id", "<unknown>"))
    enum_error = route_enum_error(context, row_id, route)
    bucket.check(
        enum_error is None,
        findings,
        code="invalid_next_skill_route",
        message=enum_error or "next_skill_route is valid",
        evidence={"id": row_id, "next_skill_route": route, "context": context},
    )
    status_errors = status_route_errors(context, str(row.get("status", "")), route, row_id)
    for error in status_errors:
        bucket.check(
            False,
            findings,
            code="status_route_mismatch",
            message=error,
            evidence={
                "id": row_id,
                "status": row.get("status"),
                "next_skill_route": route,
                "context": context,
            },
        )


def text_has_direct_submission_overclaim(record: dict[str, Any]) -> bool:
    for key, value in record.items():
        if key != "direct_submission_status":
            continue
        normalized = str(value).strip().casefold().replace("-", "_")
        if normalized in {"ready", "submission_ready", "direct_submission_ready", "cleared"}:
            return True
    return False


def audit_alternative_state_files(
    extra_files: dict[str, str],
    metrics: dict[str, MetricBucket],
    findings: list[Finding],
) -> None:
    bucket = metrics["stage_ownership"]
    suspicious: list[str] = []
    for name, text in sorted(extra_files.items()):
        path = Path(name)
        if path.suffix.casefold() not in TEXT_STATE_SUFFIXES:
            continue
        if path.name in ALLOWED_LOG_FILES or path.suffix == ".aiss":
            continue
        marker_count = sum(1 for marker in ALTERNATIVE_STATE_MARKERS if marker in text)
        if marker_count >= 2:
            suspicious.append(name)
    bucket.check(
        not suspicious,
        findings,
        code="parallel_workflow_state",
        message="Markdown/CSV/JSON sidecar appears to define workflow state outside `.aiss`",
        evidence={"files": suspicious[:20]},
    )


def audit_ast(
    ast: dict[str, Any],
    *,
    lint_report: dict[str, Any] | None = None,
    condition: str = "unspecified",
    aiss_path: str = "<memory>",
    require_artifact: bool = False,
    extra_files: dict[str, str] | None = None,
) -> dict[str, Any]:
    findings: list[Finding] = []
    metrics = {
        name: MetricBucket(name)
        for name in (
            "handoff_preservation",
            "downstream_consumability",
            "stage_ownership",
            "repair_routing_quality",
            "artifact_binding",
        )
    }

    routes = records_by_kind(ast, "route")
    mida_rows = records_by_kind(ast, "mida")
    decisions = records_by_kind(ast, "decision")
    events = records_by_kind(ast, "event")
    sources = records_by_kind(ast, "source")
    spans = records_by_kind(ast, "span")
    claims = records_by_kind(ast, "claim")
    artifacts = records_by_kind(ast, "artifact")
    checks = records_by_kind(ast, "check")
    models = records_by_kind(ast, "model")
    empirical = records_by_kind(ast, "empirical")

    selected_routes = [route for route in routes if route.get("status") == "selected"]
    selected_route = selected_routes[0] if len(selected_routes) == 1 else None
    selected_route_id = str(selected_route.get("id", "")) if selected_route else ""

    lint_ok = True if lint_report is None else bool(lint_report.get("ok"))
    metrics["downstream_consumability"].check(
        lint_ok,
        findings,
        code="aiss_lint_failed",
        message="`.aiss` does not pass the local strict v0.4 linter",
        evidence={"diagnostics": (lint_report or {}).get("diagnostics", [])[:20]},
    )

    diagnostics = (lint_report or {}).get("diagnostics", [])
    if isinstance(diagnostics, list):
        for diagnostic in diagnostics:
            if not isinstance(diagnostic, dict):
                continue
            severity = str(diagnostic.get("severity", "warning"))
            if severity not in {"error", "warning"}:
                severity = "warning"
            findings.append(
                Finding(
                    severity=severity,
                    metric="downstream_consumability",
                    code=str(diagnostic.get("code", "aiss_diagnostic")),
                    message=str(diagnostic.get("message", "AISS diagnostic")),
                    evidence={
                        "primary_id": diagnostic.get("primary_id"),
                        "related_ids": diagnostic.get("related_ids", []),
                    },
                )
            )

    hp = metrics["handoff_preservation"]
    hp.check(
        len(selected_routes) == 1,
        findings,
        code="selected_route_cardinality",
        message="Expected exactly one selected route for downstream handoff",
        evidence={"selected_routes": record_ids(selected_routes)},
    )
    hp.check(
        bool(selected_route_id),
        findings,
        code="route_decl_id_missing",
        message="No route declaration can be promoted to route_decl_id",
    )

    mida_for_route = [row for row in mida_rows if str(row.get("route", "")) == selected_route_id]
    components = {str(row.get("component", "")) for row in mida_for_route}
    missing_components = sorted(MIDA_COMPONENTS - components) if selected_route_id else sorted(MIDA_COMPONENTS)
    hp.check(
        not missing_components,
        findings,
        code="mida_incomplete",
        message="Selected route does not preserve all seven MIDA declarations",
        evidence={"missing_mida_components": missing_components, "route_decl_id": selected_route_id},
    )
    hp.check(
        all(str(row.get("route", "")) == selected_route_id for row in mida_rows) if selected_route_id else False,
        findings,
        code="mida_route_mismatch",
        message="At least one MIDA row points away from the selected route",
        evidence={
            "selected_route": selected_route_id,
            "off_route_mida": [
                {"id": row.get("id"), "route": row.get("route")}
                for row in mida_rows
                if str(row.get("route", "")) != selected_route_id
            ][:20],
        },
    )
    hp.check(
        all(str(row.get("route", "")) == selected_route_id for row in decisions) if selected_route_id else False,
        findings,
        code="decision_route_mismatch",
        message="At least one decision row points away from the selected route",
        evidence={
            "selected_route": selected_route_id,
            "off_route_decisions": [
                {"id": row.get("id"), "route": row.get("route")}
                for row in decisions
                if str(row.get("route", "")) != selected_route_id
            ][:20],
        },
    )

    for route in routes:
        status_route_finding(findings, metric="handoff_preservation", bucket=hp, context="route", row=route)
    for row in mida_rows:
        status_route_finding(findings, metric="handoff_preservation", bucket=hp, context="mida", row=row)
    for decision in decisions:
        status_route_finding(findings, metric="handoff_preservation", bucket=hp, context="decision", row=decision)
    for event in events:
        status_route_finding(findings, metric="handoff_preservation", bucket=hp, context="event", row=event)

    dc = metrics["downstream_consumability"]
    selected_next_route = str(selected_route.get("next_skill_route", "")) if selected_route else ""
    dc.check(
        selected_next_route not in {"", "none"},
        findings,
        code="selected_route_has_no_downstream_consumer",
        message="Selected route must name the next downstream skill, not stop in prose",
        evidence={"route_decl_id": selected_route_id, "next_skill_route": selected_next_route},
    )
    dc.check(
        bool(decisions),
        findings,
        code="no_automation_decision_record",
        message="No first-class decision declaration is available for auto-selected assumptions and repairs",
    )
    dc.check(
        bool(models) and bool(checks),
        findings,
        code="model_checks_missing",
        message="Downstream skills need model/check declarations to consume analysis readiness",
        evidence={"models": record_ids(models), "checks": record_ids(checks)},
    )
    dc.check(
        bool(mida_for_route),
        findings,
        code="no_mida_for_selected_route",
        message="No MIDA rows are attached to the selected route",
    )

    so = metrics["stage_ownership"]
    so.check(
        any(row.get("component") == "report_boundary" for row in mida_for_route),
        findings,
        code="missing_report_boundary",
        message="The handoff lacks a report_boundary MIDA row",
    )
    so.check(
        not any(text_has_direct_submission_overclaim(record) for record in ast_records(ast)),
        findings,
        code="direct_submission_overclaim",
        message="A workflow record marks direct submission status ready/cleared without the explicit disclosure gate",
    )
    so.check(
        all(row.get("owner") != "author" for row in decisions),
        findings,
        code="manual_decision_owner_detected",
        message="Decision rows must be owned by the harness or a factory skill, not by an external gate",
        evidence={
            "bad_decisions": [
                {"id": row.get("id"), "owner": row.get("owner")}
                for row in decisions
                if row.get("owner") == "author"
            ][:20]
        },
    )
    if extra_files is not None:
        audit_alternative_state_files(extra_files, metrics, findings)

    bq = metrics["repair_routing_quality"]
    repair_rows = [
        row
        for row in [*routes, *mida_rows, *decisions]
        if str(row.get("status", "")) in REPAIR_STATUSES
    ]
    bq.check(
        bool(repair_rows),
        findings,
        code="no_repair_or_check_route",
        message="No auto-repair/check route is declared; downstream readiness is not auditable",
    )
    for row in repair_rows:
        status = str(row.get("status", ""))
        route = str(row.get("next_skill_route", ""))
        if status == "needs_data_check":
            allowed = route in {"", "public-data-sources", "research-data-builder"}
            bq.check(
                allowed,
                findings,
                code="data_repair_misrouted",
                message="needs_data_check must route to public-data-sources or research-data-builder if it declares a next route",
                evidence={"id": row.get("id"), "next_skill_route": route},
            )
        elif status == "needs_literature_check":
            bq.check(
                route in {"", "literature-matrix"},
                findings,
                code="literature_repair_misrouted",
                message="needs_literature_check must route to literature-matrix if it declares a next route",
                evidence={"id": row.get("id"), "next_skill_route": route},
            )
        elif status == "needs_methods_review":
            bq.check(
                route in {"", "methods-reviewer", "did-expert"},
                findings,
                code="methods_repair_misrouted",
                message="needs_methods_review must route to methods-reviewer or did-expert if it declares a next route",
                evidence={"id": row.get("id"), "next_skill_route": route},
            )
        elif status == "repair_required":
            bq.check(
                route not in EXECUTION_ROUTES,
                findings,
                code="repair_routed_to_execution",
                message="repair_required rows must route to a repair owner before analysis, writing, slides, or response execution",
                evidence={"id": row.get("id"), "next_skill_route": route},
            )

    ab = metrics["artifact_binding"]
    ab.check(bool(sources), findings, code="missing_sources", message="No source declarations are available")
    ab.check(bool(spans), findings, code="missing_spans", message="No source span declarations are available")
    ab.check(bool(claims), findings, code="missing_claims", message="No claim declarations are available")
    ab.check(bool(checks), findings, code="missing_checks", message="No check declarations are available")
    if require_artifact:
        ab.check(
            bool(artifacts),
            findings,
            code="missing_artifacts",
            message="No artifact declarations are available for multi-skill relay output",
        )
    elif not artifacts:
        add_warning(
            findings,
            metric="artifact_binding",
            code="artifact_not_required_missing",
            message="No artifact declarations found; pass --require-artifact for relay eval strictness",
        )
    span_bound_kinds = {"route", "mida", "decision", "claim", "empirical", "observation", "coupling"}
    spanless = [
        {"id": record.get("id"), "kind": record_kind(record)}
        for record in ast_records(ast)
        if record_kind(record) in span_bound_kinds and not record.get("spans")
    ]
    ab.check(
        not spanless,
        findings,
        code="spanless_core_records",
        message="Core workflow/evidence records must remain bound to source spans",
        evidence={"spanless": spanless[:20]},
    )
    empirical_without_artifact = [
        record.get("id")
        for record in empirical
        if require_artifact and not coerce_list(record.get("artifacts"))
    ]
    ab.check(
        not empirical_without_artifact,
        findings,
        code="empirical_without_artifact",
        message="Empirical records in relay output must reference artifact declarations",
        evidence={"empirical": empirical_without_artifact[:20]},
    )

    for artifact in artifacts:
        ab.check(
            bool(artifact.get("uri")) and bool(artifact.get("checksum")),
            findings,
            code="artifact_missing_uri_or_checksum",
            message="Artifact declarations require uri and checksum for reproducible downstream use",
            evidence={"artifact_id": artifact.get("id"), "uri": artifact.get("uri"), "checksum": artifact.get("checksum")},
        )

    metric_json = {name: bucket.to_json() for name, bucket in metrics.items()}
    overall = round(sum(metric["score"] for metric in metric_json.values()) / len(metric_json), 4)
    error_codes = {finding.code for finding in findings if finding.severity == "error"}
    hard_error_codes = {
        "aiss_lint_failed",
        "selected_route_cardinality",
        "route_decl_id_missing",
        "mida_incomplete",
        "mida_route_mismatch",
        "decision_route_mismatch",
        "selected_route_has_no_downstream_consumer",
        "manual_decision_owner_detected",
        "data_repair_misrouted",
        "literature_repair_misrouted",
        "methods_repair_misrouted",
        "repair_routed_to_execution",
        "parallel_workflow_state",
        "missing_artifacts",
        "empirical_without_artifact",
        "artifact_missing_uri_or_checksum",
        "invalid_next_skill_route",
        "status_route_mismatch",
    }

    facts = {
        "condition": condition,
        "route_decl_id": selected_route_id,
        "selected_next_skill_route": selected_next_route,
        "mida_ids": record_ids(mida_for_route),
        "mida_components": sorted(components),
        "missing_mida_components": missing_components,
        "decision_decl_ids": record_ids(decisions),
        "claim_ids": record_ids(claims),
        "artifact_ids": record_ids(artifacts),
        "check_ids": record_ids(checks),
        "source_ids": record_ids(sources),
        "span_ids": record_ids(spans),
    }
    return {
        "schema": "ai4ss.skill_handoff_audit.v1",
        "ok": overall >= 0.8 and not (error_codes & hard_error_codes),
        "score": overall,
        "condition": condition,
        "aiss_path": aiss_path,
        "metrics": metric_json,
        "facts": facts,
        "findings": [finding.to_json() for finding in sorted(findings, key=lambda item: (item.severity, item.metric, item.code, item.message))],
    }


def audit_file(
    path: Path,
    *,
    condition: str = "unspecified",
    require_artifact: bool = False,
    extra_files: dict[str, str] | None = None,
) -> dict[str, Any]:
    ast, compile_error = run_aiss("compile", path)
    if compile_error:
        return {
            "schema": "ai4ss.skill_handoff_audit.v1",
            "ok": False,
            "score": 0.0,
            "condition": condition,
            "aiss_path": str(path),
            "metrics": {},
            "facts": {},
            "findings": [
                Finding(
                    severity="error",
                    metric="downstream_consumability",
                    code="aiss_compile_failed",
                    message=compile_error,
                ).to_json()
            ],
        }
    lint_report, lint_error = run_aiss("lint", path)
    if lint_error:
        lint_report = {
            "ok": False,
            "diagnostics": [
                {
                    "severity": "error",
                    "code": "aiss_lint_invocation_failed",
                    "message": lint_error,
                    "primary_id": str(path),
                    "related_ids": [],
                }
            ],
        }
    assert ast is not None
    return audit_ast(
        ast,
        lint_report=lint_report,
        condition=condition,
        aiss_path=str(path),
        require_artifact=require_artifact,
        extra_files=extra_files,
    )


def audit_text(
    text: str,
    *,
    label: str = "research_model.aiss",
    condition: str = "unspecified",
    require_artifact: bool = False,
    extra_files: dict[str, str] | None = None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ai4ss-handoff-audit-") as tmpdir:
        path = Path(tmpdir) / "research_model.aiss"
        path.write_text(text, encoding="utf-8")
        result = audit_file(
            path,
            condition=condition,
            require_artifact=require_artifact,
            extra_files=extra_files,
        )
        result["aiss_path"] = label
        return result


def read_workspace_texts(workspace: Path, *, aiss_path: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    if not workspace.exists():
        return texts
    for path in sorted(workspace.rglob("*")):
        if not path.is_file():
            continue
        if path == aiss_path:
            continue
        if path.suffix.casefold() not in TEXT_STATE_SUFFIXES:
            continue
        try:
            relative = str(path.relative_to(workspace))
        except ValueError:
            relative = str(path)
        try:
            texts[relative] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if len(texts) >= 500:
            break
    return texts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("aiss_path", type=Path, help="Research-model `.aiss` file to audit.")
    parser.add_argument("--condition", default="unspecified", help="Condition label for JSON output.")
    parser.add_argument("--json-out", type=Path, help="Optional path to write full audit JSON.")
    parser.add_argument("--workspace", type=Path, help="Optional workspace to scan for sidecar workflow-state files.")
    parser.add_argument("--require-artifact", action="store_true", help="Require artifact declarations and empirical artifact links.")
    parser.add_argument("--require-ok", action="store_true", help="Exit non-zero when the audit is not ok.")
    args = parser.parse_args()

    extra_files = None
    if args.workspace:
        extra_files = read_workspace_texts(args.workspace, aiss_path=args.aiss_path)
    result = audit_file(
        args.aiss_path,
        condition=args.condition,
        require_artifact=args.require_artifact,
        extra_files=extra_files,
    )
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    status = "PASS" if result["ok"] else "FAIL"
    print(f"{status} score={result['score']} condition={result['condition']} path={result['aiss_path']}")
    for name, metric in result.get("metrics", {}).items():
        print(f"METRIC {name} {metric['passed']}/{metric['total']} score={metric['score']}")
    for finding in result.get("findings", [])[:40]:
        if finding.get("severity") == "warning":
            continue
        print(f"FINDING {finding['metric']} {finding['code']}: {finding['message']}")

    if args.require_ok and not result["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
