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
    "manuscript-reviewer",
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
        "registration_status",
        "protocol_path",
        "analysis_plan_path",
        "deviation_log_status",
    ),
    "public-data-sources": (
        "research_model.aiss",
        "ai4ss_model_path",
        "source_access_status",
        "access_class",
        "official_docs_url",
        "request_template",
        "observed_data_only_status",
        "row_source_provenance",
        "source",
        "artifact",
        "check",
        "decision",
        "research-data-builder",
    ),
    "research-data-builder": (
        "research_model.aiss",
        "ai4ss_model_path",
        "source",
        "artifact",
        "empirical",
        "observation",
        "coupling",
        "bridge",
        "check",
        "decision",
        "codebook-parse",
        "cleaning-contract",
        "cleaning-execute",
        "materials_transparency_status",
        "source_access_status",
        "data_transparency_status",
        "fair_metadata_status",
        "replication_package_status",
        "observed_data_only_status",
        "row_source_provenance",
    ),
    "literature-matrix": (
        "research_model.aiss",
        "ai4ss_model_path",
        "paper",
        "source",
        "span",
        "claim",
        "relation",
        "concept_id",
        "causal",
        "bridge_id",
        "check",
        "decision",
    ),
    "research-analysis-runner": (
        "research_model.aiss",
        "ai4ss_model_path",
        "artifact",
        "adapter",
        "derive",
        "observation",
        "claim",
        "decision",
        "bridge_id",
        "readiness_status",
        "analysis_code_transparency_status",
        "computational_reproducibility_status",
        "replication_package_status",
        "deviation_log_status",
    ),
    "top-journal-figures": (
        "research_model.aiss",
        "ai4ss_model_path",
        "artifact",
        "derive",
        "observation",
        "claim",
        "decision",
        "figure_spec",
        "figure_path",
        "source_note",
        "caption",
        "helper_tools_used",
        "helper_tool_transparency_status",
        "style_profile_id",
        "style_source_path",
        "style_consistency_status",
        "style_exceptions",
        "ggplot_object",
        "ggsave_call",
        "visual_integrity_status",
        "vector_export_status",
        "black_white_status",
        "interpretation_boundary",
        "replication_package_status",
    ),
    "methods-reviewer": (
        "research_model.aiss",
        "ai4ss_model_path",
        "check",
        "decision",
        "commensurability_status",
        "computational_reproducibility_status",
        "deviation_log_status",
    ),
    "manuscript-reviewer": (
        "research_model.aiss",
        "ai4ss_model_path",
        "review_id",
        "manuscript_sha256",
        "checklist_sha256",
        "config_sha256",
        "check",
        "decision",
        "next_skill_route",
        "AutoChecklist",
    ),
    "academic-writing-scaffold": (
        "research_model.aiss",
        "ai4ss_model_path",
        "claim_id",
        "commensurability_status",
        "ai_contribution_disclosure",
        "human_accountability_status",
        "submission_policy_check_status",
        "direct_submission_status",
        "reporting_transparency_status",
        "top_disclosure_matrix",
        "manuscript_assembly_status",
        "replication_package_status",
    ),
    "research-slides-builder": (
        "research_model.aiss",
        "ai4ss_model_path",
        "claim_id",
        "privacy_status",
        "visual_object",
    ),
    "reviewer-response": (
        "research_model.aiss",
        "ai4ss_model_path",
        "comment_id",
        "mida_element_affected",
        "confidentiality_status",
        "revision_transparency_status",
        "deviation_log_status",
        "ai_contribution_disclosure",
        "human_accountability_status",
        "submission_policy_check_status",
        "direct_submission_status",
    ),
}

FORBIDDEN_WORKFLOW_TERMS = (
    "sidecar",
    "research_route_cards.csv",
    "study_design_declaration.csv",
    "design_decision_register.csv",
    "sample_flow.csv",
    "merge_audit.csv",
    "variable_provenance.csv",
    "literature_candidate_discovery.csv",
    "literature_matrix.csv",
    "literature_theory_synthesis.csv",
    "theory_rival_map.csv",
    "theory_scope_map.csv",
    "theory_evidence.md",
    "analysis_readiness_check.csv",
    "analysis_run_manifest.csv",
    "issue_table.csv",
    "claim_ledger.csv",
    "slide_map.csv",
    "revision_matrix.csv",
    "_packet.md",
    "_log.md",
    "_questions.md",
    "_plan.md",
    "_scaffold.md",
)

RUNTIME_REFERENCE_FORBIDDEN_TERMS = FORBIDDEN_WORKFLOW_TERMS + (
    "literature matrix",
    "ordinary literature matrix",
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
        "compile_evidence.py",
        "MIDA",
        "run_factory_level_eval.py",
        "docs/factory_level_eval/",
    ),
    "skillpack_workflow_contract.md": (
        "research_model.aiss",
        "ai4ss_model_path",
        "ai4ss_check_status",
        "public-data-sources",
        "source_access_status",
        "observed_data_only_status",
        "row_source_provenance",
        "replication_package_status",
    ),
    "scholar_workbenches.md": (
        ".aiss",
        "MIDA",
        "route declarations",
        "mida",
        "decision",
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
    lowered = text.lower()
    for forbidden in FORBIDDEN_WORKFLOW_TERMS:
        if forbidden.lower() in lowered:
            errors.append(f"{skill_dir.name}: forbidden legacy workflow artifact `{forbidden}`")

    contract_start = text.find("## Workflow Contract")
    if contract_start >= 0:
        next_heading = text.find("\n## ", contract_start + 1)
        contract = text[contract_start : next_heading if next_heading >= 0 else len(text)]
        for required_term in ("Upstream inputs", "Produces", "Handoff fields", "Downstream routes"):
            if required_term not in contract:
                errors.append(f"{skill_dir.name}: workflow contract missing {required_term}")
        if "next_skill_route" not in contract:
            errors.append(f"{skill_dir.name}: workflow contract must mention next_skill_route")

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
    else:
        for reference_path in sorted(references.glob("*.md")):
            try:
                reference_text = reference_path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                errors.append(f"{skill_dir.name}: cannot read {reference_path.relative_to(skill_dir)}: {exc}")
                continue
            reference_lowered = reference_text.lower()
            for forbidden in RUNTIME_REFERENCE_FORBIDDEN_TERMS:
                if forbidden.lower() in reference_lowered:
                    relative_path = reference_path.relative_to(skill_dir)
                    errors.append(
                        f"{skill_dir.name}: {relative_path} uses forbidden legacy workflow artifact `{forbidden}`"
                    )

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
            for forbidden in forbidden_terms + FORBIDDEN_WORKFLOW_TERMS:
                if forbidden in text:
                    errors.append(f"{doc_name}: forbidden legacy artifact term `{forbidden}`")

    if not Path("scripts/validate_ai4ss_model.py").exists():
        errors.append("missing scripts/validate_ai4ss_model.py")
    if not Path("scripts/run_factory_level_eval.py").exists():
        errors.append("missing scripts/run_factory_level_eval.py")
    if not (args.docs_dir / "examples" / "research_model.aiss").exists():
        errors.append("missing docs/examples/research_model.aiss")
    for required_eval_path in (
        args.docs_dir / "factory_level_eval" / "protocol.md",
        args.docs_dir / "factory_level_eval" / "grader_brief.md",
        args.docs_dir / "factory_level_eval" / "packets" / "P001.md",
        args.docs_dir / "factory_level_eval" / "packets" / "P002.md",
        args.docs_dir / "factory_level_eval" / "judge_prompts" / "P001.md",
        args.docs_dir / "factory_level_eval" / "gate_matrix_blinded.csv",
        args.docs_dir / "factory_level_eval" / "llm_judge_scores.csv",
        args.docs_dir / "factory_level_eval" / "human_grading_sheet.csv",
        args.docs_dir / "factory_level_eval" / "unblinded_report.md",
        args.docs_dir / "factory_level_eval" / "_private" / "private_mapping.csv",
    ):
        if not required_eval_path.exists():
            errors.append(f"missing factory-level evaluation artifact: {required_eval_path}")

    harness_agents = Path("evals/factory_e2e_apsr_pdf/scaffold/AGENTS.md")
    if not harness_agents.exists():
        errors.append(f"missing APSR PDF harness instruction file: {harness_agents}")
    else:
        harness_agents_text = harness_agents.read_text(encoding="utf-8")
        for term in (
            "Skill Routing Table",
            "public-data-sources",
            "research-data-builder",
            "paper/full_draft.pdf",
            "real observed",
            "Synthetic",
            "next_skill_route",
        ):
            if term not in harness_agents_text:
                errors.append(f"{harness_agents}: missing `{term}`")
        if "| `inspect-agent-eval` |" in harness_agents_text:
            errors.append(f"{harness_agents}: inspect-agent-eval must not be in the production harness route table")

    root_agents = Path("AGENTS.md")
    if root_agents.exists():
        root_agents_text = root_agents.read_text(encoding="utf-8")
        if "| `inspect-agent-eval` |" in root_agents_text:
            errors.append(f"{root_agents}: inspect-agent-eval must not be in the production harness route table")

    apsr_task = Path("evals/factory_e2e_apsr_pdf/task.py")
    if apsr_task.exists():
        apsr_task_text = apsr_task.read_text(encoding="utf-8")
        for term in (
            "AGENTS_PATH",
            "/workspace/AGENTS.md",
            "FORBIDDEN_SYNTHETIC_DATA_PATTERNS",
            "synthetic_data_violation",
            "public-data-sources",
            "real observed",
        ):
            if term not in apsr_task_text:
                errors.append(f"{apsr_task}: missing `{term}`")

    if errors:
        return fail("; ".join(errors))

    print(f"PASS skillpack workflow: {len(REQUIRED_SKILLS)} skills checked")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        sys.exit(1)
