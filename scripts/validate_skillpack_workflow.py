#!/usr/bin/env python3
"""Validate local AI4SS skillpack workflow consistency."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SKILLS = [
    "research-starter",
    "study-design-builder",
    "public-data-sources",
    "research-data-builder",
    "literature-matrix",
    "research-analysis-runner",
    "top-journal-figures",
    "methods-reviewer",
    "academic-writing-scaffold",
    "research-slides-builder",
    "reviewer-response",
]

REQUIRED_SECTIONS = [
    "## Methodology Foundation",
    "## Workflow Contract",
    "## Routing Boundaries",
    "## Script Utilities",
    "## Reference Files",
]

OUTPUT_SECTION_RE = re.compile(r"^## (Default Outputs|Required Outputs|Output Shape)$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\n(?P<body>.*?)\n---", re.DOTALL)
AI4SS_REQUIRED_SKILL_TERMS = {
    "research-starter": ("research_model.aiss", "route_decl_id", "aiss_check_status"),
    "study-design-builder": (
        "research_model.aiss",
        "route_decl_id",
        "mida_id",
        "decision_decl_id",
        "ai4ss_model_path",
        "ai4ss_check_status",
    ),
    "public-data-sources": (
        "research_model.aiss",
        "source_artifact_path",
        "source_access_status",
        "observed_data_only_status",
        "public_no_secret",
        "download_ingest_only",
    ),
    "research-data-builder": ("research_model.aiss", "ai4ss_model_path", "codebook-parse", "cleaning-contract", "cleaning-execute"),
    "literature-matrix": (
        "research_model.aiss",
        "ai4ss_model_path",
        "concept_id",
        "bridge_id",
        "evidence_table_path",
        "compiled_ai4ss_path",
        "evidence_compile_status",
    ),
    "research-analysis-runner": (
        "research_model.aiss",
        "ai4ss_model_path",
        "bridge_id",
        "analysis_readiness_check.csv",
        "readiness_status",
    ),
    "top-journal-figures": (
        "research_model.aiss",
        "ai4ss_model_path",
        "figure_path",
        "ggplot",
        "visual_integrity_status",
    ),
    "methods-reviewer": ("research_model.aiss", "ai4ss_model_path", "commensurability_status"),
    "academic-writing-scaffold": ("research_model.aiss", "ai4ss_model_path", "commensurability_status"),
    "research-slides-builder": ("research_model.aiss", "ai4ss_model_path"),
    "reviewer-response": ("research_model.aiss", "ai4ss_model_path"),
}

FORBIDDEN_SKILL_TERMS = (
    "Terminal route: use `last_skill`",
    "Author Decision Points",
    "Author decision points",
    "author_decision",
    "author_decisions",
    "ask_author",
    "needs_author",
    "needs_author_decision",
)

DOC_CONTENT_REQUIREMENTS = {
    "ai4ss_dsl_factory_integration.md": (
        ".aiss",
        "research_model.aiss",
        "aiss.py compile",
        "aiss.py lint",
        "aiss.py run",
        "aiss.unified_ast.v0.4",
        "codebook-parse",
        "cleaning-contract",
        "cleaning-execute",
        "analysis_readiness_check.csv",
        "compile_evidence.py",
        "MIDA",
        "run_factory_level_eval.py",
        "docs/factory_level_eval/",
        "run_skill_handoff_audit_fixtures.py",
        "valid_relay.aiss",
    ),
    "skillpack_workflow_contract.md": (
        "research_model.aiss",
        "ai4ss_model_path",
        "ai4ss_check_status",
        "analysis_readiness_check.csv",
        "No-Dead-End Completion Invariant",
        "current_run_gate",
        "upgrade_gate",
        "Fabricated, simulation-only, toy, placeholder, or demo-only material",
        "working article/PDF",
        "artifact has been produced",
        "public-data-sources",
        "observed public-source acquisition",
        "source_artifact_path",
        "State Machine Contract",
        "audit_skill_handoffs.py",
        "run_skill_handoff_audit_fixtures.py",
        "valid_relay.aiss",
        "synthetic/demo fallback",
    ),
    "scholar_workbenches.md": (
        ".aiss",
        "MIDA",
        "route declarations",
        "mida",
        "decision",
        "analysis_readiness_check.csv",
        "run_factory_level_eval.py",
    ),
    "methodology_foundations.md": (".aiss", "MIDA", "route_decl_id", "mida_id", "decision_decl_id"),
}


def fail(message: str) -> int:
    print(f"FAIL {message}")
    return 1


def parse_frontmatter(text: str, path: Path) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{path}: missing YAML frontmatter")
    values: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"')
    return values


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir.name}: missing SKILL.md"]

    text = skill_md.read_text(encoding="utf-8")
    try:
        frontmatter = parse_frontmatter(text, skill_md)
    except ValueError as exc:
        errors.append(str(exc))
        frontmatter = {}

    if frontmatter.get("name") != skill_dir.name:
        errors.append(f"{skill_dir.name}: frontmatter name must match folder")
    if "description" not in frontmatter:
        errors.append(f"{skill_dir.name}: missing description")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"{skill_dir.name}: missing {section}")
    if not OUTPUT_SECTION_RE.search(text):
        errors.append(f"{skill_dir.name}: missing output section")

    for term in AI4SS_REQUIRED_SKILL_TERMS.get(skill_dir.name, ()):
        if term not in text:
            errors.append(f"{skill_dir.name}: missing AI4SS DSL term `{term}`")

    for term in FORBIDDEN_SKILL_TERMS:
        if term in text:
            errors.append(f"{skill_dir.name}: forbidden legacy workflow term `{term}`")

    if skill_dir.name == "research-analysis-runner":
        required_ban = "Do not fabricate analysis material"
        if required_ban not in text:
            errors.append(f"{skill_dir.name}: missing fabricated fallback analysis ban")

    contract_start = text.find("## Workflow Contract")
    if contract_start >= 0:
        next_heading = text.find("\n## ", contract_start + 1)
        contract = text[contract_start : next_heading if next_heading >= 0 else len(text)]
        for required_term in ("Upstream inputs", "Produces", "Handoff fields", "Downstream routes"):
            if required_term not in contract:
                errors.append(f"{skill_dir.name}: workflow contract missing {required_term}")
        if "next_skill_route" not in contract:
            errors.append(f"{skill_dir.name}: workflow contract must mention next_skill_route")
        if "Repair route: use `last_skill` only to return control" not in contract:
            errors.append(f"{skill_dir.name}: workflow contract missing hardened last_skill repair route")
        if "It is not a final state" not in contract:
            errors.append(f"{skill_dir.name}: workflow contract must reject last_skill as final state")

    methodology_start = text.find("## Methodology Foundation")
    if methodology_start >= 0:
        next_heading = text.find("\n## ", methodology_start + 1)
        methodology = text[methodology_start : next_heading if next_heading >= 0 else len(text)]
        if "MIDA" not in methodology:
            errors.append(f"{skill_dir.name}: methodology foundation must mention MIDA")
        if not re.search(r"Model|Inquiry|Data strategy|Answer strategy|Diagnose|Redesign|Report", methodology):
            errors.append(f"{skill_dir.name}: methodology foundation must name a framework component")

    agents_yaml = skill_dir / "agents" / "openai.yaml"
    if not agents_yaml.exists():
        errors.append(f"{skill_dir.name}: missing agents/openai.yaml")

    references = skill_dir / "references"
    if not references.exists() or not any(references.glob("*.md")):
        errors.append(f"{skill_dir.name}: missing reference markdown files")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills-dir", type=Path, default=Path("skills"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()

    errors: list[str] = []
    for skill_name in REQUIRED_SKILLS:
        skill_dir = args.skills_dir / skill_name
        if not skill_dir.exists():
            errors.append(f"missing required skill: {skill_name}")
            continue
        errors.extend(validate_skill(skill_dir))

    doc_names = (
        "skillpack_workflow_contract.md",
        "skillpack_gap_map.md",
        "scholar_workbenches.md",
        "ai4ss_dsl_factory_integration.md",
        "methodology_foundations.md",
        "methodology_source_matrix.csv",
    )
    for doc_name in doc_names:
        doc_path = args.docs_dir / doc_name
        if not doc_path.exists():
            errors.append(f"missing workflow doc: {doc_name}")
            continue
        if doc_name.endswith(".md"):
            text = doc_path.read_text(encoding="utf-8")
            for term in DOC_CONTENT_REQUIREMENTS.get(doc_name, ()):
                if term not in text:
                    errors.append(f"{doc_name}: missing `{term}`")
            forbidden_terms = ("research_model.ai4ss", ".ai4ss")
            for forbidden in forbidden_terms:
                if forbidden in text:
                    errors.append(f"{doc_name}: forbidden legacy artifact term `{forbidden}`")

    if not Path("scripts/validate_ai4ss_model.py").exists():
        errors.append("missing scripts/validate_ai4ss_model.py")
    if not Path("scripts/validate_analysis_readiness.py").exists():
        errors.append("missing scripts/validate_analysis_readiness.py")
    if not Path("scripts/validate_literature_evidence_compile.py").exists():
        errors.append("missing scripts/validate_literature_evidence_compile.py")
    if not Path("scripts/run_factory_level_eval.py").exists():
        errors.append("missing scripts/run_factory_level_eval.py")
    for required_state_machine_path in (
        Path("scripts/ai4ss_factory_contracts/workflow.py"),
        Path("scripts/ai4ss_factory_contracts/sidecars.py"),
        Path("scripts/audit_skill_handoffs.py"),
        Path("scripts/run_skill_handoff_audit_fixtures.py"),
        args.docs_dir / "evals" / "factory-relay" / "fixtures" / "valid_relay.aiss",
    ):
        if not required_state_machine_path.exists():
            errors.append(f"missing research-factory state-machine artifact: {required_state_machine_path}")
    if not (args.docs_dir / "examples" / "research_model.aiss").exists():
        errors.append("missing docs/examples/research_model.aiss")
    for required_eval_path in (
        args.docs_dir / "factory_level_eval" / "protocol.md",
        args.docs_dir / "factory_level_eval" / "grader_brief.md",
        args.docs_dir / "factory_level_eval" / "packets" / "P001.md",
        args.docs_dir / "factory_level_eval" / "packets" / "P002.md",
        args.docs_dir / "factory_level_eval" / "gate_matrix_blinded.csv",
        args.docs_dir / "factory_level_eval" / "rule_based_scores_blinded.csv",
        args.docs_dir / "factory_level_eval" / "human_grading_sheet.csv",
        args.docs_dir / "factory_level_eval" / "unblinded_report.md",
        args.docs_dir / "factory_level_eval" / "_private" / "private_mapping.csv",
    ):
        if not required_eval_path.exists():
            errors.append(f"missing factory-level evaluation artifact: {required_eval_path}")

    if errors:
        return fail("; ".join(errors))

    print(f"PASS skillpack workflow: {len(REQUIRED_SKILLS)} skills checked")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
