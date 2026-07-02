#!/usr/bin/env python3
"""Conformance tests for the AISS v0.3 deterministic toolchain."""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys

from aiss_v03 import (
    AissError,
    canonical_json,
    compile_file,
    diff_asts,
    emit_code_manifest,
    lint_ast,
    render_template,
    run_ast,
)


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "test_fixtures" / "v03"
PLATO = FIXTURES / "plato_sectionless.aiss"
EXAMPLE = FIXTURES / "example_coupling.aiss"
VARIANT = FIXTURES / "example_coupling_variant.aiss"
BAD_FORBIDDEN = FIXTURES / "bad_forbidden.aiss"
BAD_REFS = FIXTURES / "bad_refs.aiss"
BAD_THEORY = FIXTURES / "bad_theory_incoherence.aiss"
TEMPLATE = FIXTURES / "report_template.md"
CLI = ROOT / "aiss.py"


def assert_raises_aiss_error(path: Path, needle: str) -> None:
    try:
        compile_file(path)
    except AissError as exc:
        assert needle in str(exc), str(exc)
    else:
        raise AssertionError(f"expected AissError containing {needle!r}")


def main() -> None:
    # Sectionless text compiles without any article-section assumptions.
    plato_ast = compile_file(PLATO, strict=True)
    assert plato_ast["schema"] == "aiss.paper_ast.v0.3"
    assert plato_ast["paper"]["kind"] == "dialogue"
    assert plato_ast["spans"][0]["locator"].startswith("stephanus:")

    # Canonical JSON is stable across repeated compilation.
    example_ast_1 = compile_file(EXAMPLE, strict=True)
    example_ast_2 = compile_file(EXAMPLE, strict=True)
    assert canonical_json(example_ast_1) == canonical_json(example_ast_2)
    assert example_ast_1["indices"]["theory"] == [
        "example.claim_scrutiny_changes_behavior",
        "example.concept_public_scrutiny",
    ]
    assert example_ast_1["indices"]["coupling"] == ["example.coup_case_supports_claim"]

    # Derived-output source primitives are rejected at compile time.
    assert_raises_aiss_error(BAD_FORBIDDEN, "forbidden derived-output primitive")

    # Lint catches unresolved references and invalid coupling endpoints with stable codes.
    bad_ast = compile_file(BAD_REFS)
    bad_report = lint_ast(bad_ast)
    codes = [d["code"] for d in bad_report["diagnostics"]]
    assert "AISS-REF-001" in codes
    assert "AISS-COUP-001" in codes
    assert "AISS-COUP-002" in codes
    assert not bad_report["ok"]
    assert canonical_json(bad_report) == canonical_json(lint_ast(bad_ast))

    # Theory Linter v1 catches explicit structured-claim contradictions.
    bad_theory_ast = compile_file(BAD_THEORY)
    bad_theory_report = lint_ast(bad_theory_ast)
    theory_codes = [d["code"] for d in bad_theory_report["diagnostics"]]
    assert "AISS-CLAIM-010" in theory_codes
    theory_conflict = next(d for d in bad_theory_report["diagnostics"] if d["code"] == "AISS-CLAIM-010")
    assert theory_conflict["severity"] == "error"
    assert "positive" in theory_conflict["message"]
    assert "null" in theory_conflict["message"]
    assert not bad_theory_report["ok"]

    # Run emits not_assessable rather than guessing support.
    run_report = run_ast(example_ast_1)
    assert run_report["schema"] == "aiss.run_report.v0.3"
    assert run_report["coupling_assessments"] == [
        {
            "basis": [],
            "coupling_id": "example.coup_case_supports_claim",
            "message": "No deterministic adapter is available for this coupling type.",
            "rule": None,
            "status": "not_assessable",
        }
    ]

    # Diff reports structural add/change operations deterministically.
    variant_ast = compile_file(VARIANT, strict=True)
    diff_report = diff_asts(example_ast_1, variant_ast)
    ops = diff_report["operations"]
    assert any(op["op"] == "added" and "example.concept_visible_action" in op["path"] for op in ops)
    assert any(op["op"] == "changed" and op["path"].endswith("/text") for op in ops)
    assert canonical_json(diff_report) == canonical_json(diff_asts(example_ast_1, variant_ast))

    # Deterministic writer renders byte-stable output from AST + template.
    template = TEMPLATE.read_text(encoding="utf-8")
    written_1 = render_template(example_ast_1, template)
    written_2 = render_template(example_ast_1, template)
    assert written_1 == written_2
    assert "# Example Paper" in written_1
    assert "example.coup_case_supports_claim" in written_1

    # emit-code starts with a deterministic manifest when no adapter can emit code.
    manifest = emit_code_manifest(example_ast_1, target="python")
    assert manifest["schema"] == "aiss.code_manifest.v0.3"
    assert manifest["status"] == "skipped_no_adapter"

    # Unified CLI smoke test.
    proc = subprocess.run(
        [sys.executable, str(CLI), "compile", str(EXAMPLE), "--strict"],
        check=True,
        capture_output=True,
        text=True,
    )
    cli_ast = json.loads(proc.stdout)
    assert cli_ast["schema"] == "aiss.paper_ast.v0.3"
    assert canonical_json(cli_ast) == canonical_json(example_ast_1)


if __name__ == "__main__":
    main()
