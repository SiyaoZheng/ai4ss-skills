#!/usr/bin/env python3
"""Run deterministic cross-skill handoff audit fixtures."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable

from audit_skill_handoffs import audit_text


ROOT = Path(__file__).resolve().parents[1]
VALID_FIXTURE = ROOT / "docs" / "evals" / "factory-relay" / "fixtures" / "valid_relay.aiss"
DEFAULT_JSON = ROOT / "docs" / "evals" / "factory-relay" / "deterministic-handoff-audit.json"
DEFAULT_MD = ROOT / "docs" / "evals" / "factory-relay" / "deterministic-handoff-audit.md"


class FixtureCase:
    def __init__(
        self,
        *,
        case_id: str,
        expected_ok: bool,
        mutate: Callable[[str], tuple[str, dict[str, str]]],
        rationale: str,
    ) -> None:
        self.case_id = case_id
        self.expected_ok = expected_ok
        self.mutate = mutate
        self.rationale = rationale


def identity(text: str) -> tuple[str, dict[str, str]]:
    return text, {}


def remove_report_boundary(text: str) -> tuple[str, dict[str, str]]:
    mutated = re.sub(
        r"\n\nmida relay\.mida_r1_report_boundary \{.*?\n\}",
        "",
        text,
        count=1,
        flags=re.DOTALL,
    )
    return mutated, {}


def misroute_data_repair(text: str) -> tuple[str, dict[str, str]]:
    mutated = text.replace(
        "  status: needs_data_check\n  bridges: [relay.measurement_bridge_exposure]",
        "  status: needs_data_check\n  next_skill_route: research-analysis-runner\n  bridges: [relay.measurement_bridge_exposure]",
        1,
    )
    return mutated, {}


def sidecar_parallel_state(text: str) -> tuple[str, dict[str, str]]:
    return text, {
        "handoff_state.md": (
            "# Parallel Workflow State\n\n"
            "| route_decl_id | mida_id | decision_decl_id | next_skill_route |\n"
            "| --- | --- | --- | --- |\n"
            "| relay.route_r1 | relay.mida_r1_model | relay.decision_r1_identification | research-analysis-runner |\n"
        )
    }


def stop_selected_route(text: str) -> tuple[str, dict[str, str]]:
    mutated = text.replace("  next_skill_route: public-data-sources\n", "  next_skill_route: none\n", 1)
    return mutated, {}


def drop_empirical_artifact_link(text: str) -> tuple[str, dict[str, str]]:
    mutated = text.replace("  artifacts: [relay.artifact_data_inventory]\n", "", 1)
    return mutated, {}


def route_mida_to_wrong_route(text: str) -> tuple[str, dict[str, str]]:
    mutated = text.replace(
        "mida relay.mida_r1_answer_strategy {\n  route: relay.route_r1",
        "mida relay.mida_r1_answer_strategy {\n  route: relay.route_missing",
        1,
    )
    return mutated, {}


def fixture_cases() -> list[FixtureCase]:
    return [
        FixtureCase(
            case_id="valid_relay",
            expected_ok=True,
            mutate=identity,
            rationale="Full route/MIDA/decision/artifact/check/claim relay should pass.",
        ),
        FixtureCase(
            case_id="missing_report_boundary",
            expected_ok=False,
            mutate=remove_report_boundary,
            rationale="Downstream writing/review cannot consume a handoff that dropped report_boundary.",
        ),
        FixtureCase(
            case_id="data_repair_misrouted",
            expected_ok=False,
            mutate=misroute_data_repair,
            rationale="Data repair rows must route to public-data-sources or research-data-builder, not execution.",
        ),
        FixtureCase(
            case_id="parallel_markdown_state",
            expected_ok=False,
            mutate=sidecar_parallel_state,
            rationale="Workflow state in Markdown/CSV sidecars competes with `.aiss` as the only state.",
        ),
        FixtureCase(
            case_id="selected_route_lacks_consumer",
            expected_ok=False,
            mutate=stop_selected_route,
            rationale="A selected route must preserve a downstream next_skill_route.",
        ),
        FixtureCase(
            case_id="empirical_artifact_link_dropped",
            expected_ok=False,
            mutate=drop_empirical_artifact_link,
            rationale="Relay outputs must keep empirical records bound to artifact declarations.",
        ),
        FixtureCase(
            case_id="mida_route_drift",
            expected_ok=False,
            mutate=route_mida_to_wrong_route,
            rationale="MIDA rows that drift away from route_decl_id are not downstream-consumable.",
        ),
    ]


def summarize_findings(result: dict) -> list[str]:
    codes: list[str] = []
    for finding in result.get("findings", []):
        if finding.get("severity") != "error":
            continue
        code = str(finding.get("code", "unknown"))
        if code not in codes:
            codes.append(code)
    return codes


def render_markdown(payload: dict) -> str:
    lines = [
        "# Factory Relay Deterministic Handoff Audit",
        "",
        "This report checks whether `.aiss` remains the single workflow state across a multi-skill relay.",
        "",
        "| case | expected | actual | score | primary error codes |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for case in payload["cases"]:
        expected = "pass" if case["expected_ok"] else "fail"
        actual = "pass" if case["ok"] else "fail"
        codes = ", ".join(case["error_codes"]) or "-"
        lines.append(f"| `{case['case_id']}` | {expected} | {actual} | {case['score']:.4f} | {codes} |")
    lines.extend(
        [
            "",
            "## Dimensions",
            "",
            "- `handoff_preservation`: selected `route_decl_id`, seven MIDA rows, decision-route continuity, and valid `next_skill_route`.",
            "- `downstream_consumability`: strict `.aiss` lint, usable downstream route, automation decisions, and model/check availability.",
            "- `stage_ownership`: no sidecar workflow state and no direct-submission overclaim.",
            "- `repair_routing_quality`: repair/check rows route to the owning skill, not to execution.",
            "- `artifact_binding`: source/span/claim/check/artifact continuity and empirical artifact links.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=VALID_FIXTURE)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    fixture_text = args.fixture.read_text(encoding="utf-8")
    case_results: list[dict] = []
    mismatches: list[str] = []
    for case in fixture_cases():
        mutated_text, extra_files = case.mutate(fixture_text)
        result = audit_text(
            mutated_text,
            label=f"{case.case_id}.aiss",
            condition=case.case_id,
            require_artifact=True,
            extra_files=extra_files,
        )
        error_codes = summarize_findings(result)
        actual_ok = bool(result["ok"])
        if actual_ok != case.expected_ok:
            mismatches.append(case.case_id)
        case_results.append(
            {
                "case_id": case.case_id,
                "expected_ok": case.expected_ok,
                "ok": actual_ok,
                "score": float(result["score"]),
                "error_codes": error_codes,
                "rationale": case.rationale,
                "metrics": result.get("metrics", {}),
                "facts": result.get("facts", {}),
            }
        )

    payload = {
        "schema": "ai4ss.factory_relay_deterministic_audit.v1",
        "fixture": str(args.fixture),
        "ok": not mismatches,
        "mismatches": mismatches,
        "cases": case_results,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text(render_markdown(payload), encoding="utf-8")

    print(f"RESULT ok={payload['ok']} cases={len(case_results)} json={args.json_out} markdown={args.markdown_out}")
    for case in case_results:
        print(
            "CASE "
            f"{case['case_id']} expected={case['expected_ok']} actual={case['ok']} "
            f"score={case['score']:.4f} errors={','.join(case['error_codes']) or '-'}"
        )
    if mismatches:
        print(f"FAIL mismatched cases: {', '.join(mismatches)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
