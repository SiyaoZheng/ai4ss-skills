"""Shared workflow-routing interface for the AI4SS research factory."""

from __future__ import annotations


RESEARCH_FACTORY_SKILLS = (
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
)

STUDY_TYPES = {
    "descriptive",
    "causal",
    "prediction",
    "text_analysis",
    "case_comparison",
    "qualitative",
    "mixed_methods",
    "theory_mapping",
}

MIDA_COMPONENTS = {
    "model",
    "inquiry",
    "data_strategy",
    "answer_strategy",
    "diagnose",
    "redesign",
    "report_boundary",
}

MIDA_COMPONENTS_WITH_REPORT = MIDA_COMPONENTS | {"report"}

CORE_HANDOFF_FIELDS = (
    "route_id",
    "design_source",
    "target_inquiry",
    "registration_status",
    "protocol_path",
    "analysis_plan_path",
    "source_access_status",
    "observed_data_only_status",
    "row_source_provenance",
    "materials_transparency_status",
    "data_transparency_status",
    "analysis_code_transparency_status",
    "reporting_transparency_status",
    "replication_package_status",
    "fair_metadata_status",
    "deviation_log_status",
    "ai_contribution_disclosure",
    "human_accountability_status",
    "submission_policy_check_status",
    "direct_submission_status",
    "assumption_register",
    "validation_commands",
    "interpretation_boundary",
    "next_skill_route",
)

MODEL_LINK_FIELDS = (
    "ai4ss_model_path",
    "model_id",
    "concept_id",
    "causal_id",
    "bridge_id",
    "ai4ss_check_status",
)

ALLOWED_NEXT_ROUTES: dict[str, set[str]] = {
    "route": {
        "study-design-builder",
        "public-data-sources",
        "research-data-builder",
        "literature-matrix",
        "methods-reviewer",
        "academic-writing-scaffold",
        "top-journal-figures",
        "research-slides-builder",
        "reviewer-response",
        "did-expert",
        "none",
    },
    "mida": {
        "public-data-sources",
        "research-data-builder",
        "literature-matrix",
        "research-analysis-runner",
        "top-journal-figures",
        "methods-reviewer",
        "did-expert",
        "none",
    },
    "decision": {
        "public-data-sources",
        "research-data-builder",
        "literature-matrix",
        "research-analysis-runner",
        "top-journal-figures",
        "methods-reviewer",
        "did-expert",
        "none",
    },
    "event": set(RESEARCH_FACTORY_SKILLS)
    | {
        "analysis-explainer",
        "did-expert",
        "latex-tables",
        "manuscript-reviewer",
        "codebook-parse",
        "cleaning-contract",
        "cleaning-execute",
        "codex",
        "r-performance",
        "sjtu-hpc",
        "none",
    },
    "literature_evidence": {
        "study-design-builder",
        "academic-writing-scaffold",
        "methods-reviewer",
    },
    "rival_check": {
        "methods-reviewer",
        "study-design-builder",
        "academic-writing-scaffold",
    },
    "scope_check": {
        "methods-reviewer",
        "study-design-builder",
        "academic-writing-scaffold",
    },
    "analysis_check": {
        "research-analysis-runner",
        "public-data-sources",
        "research-data-builder",
        "study-design-builder",
        "methods-reviewer",
    },
    "analysis_artifact": {
        "methods-reviewer",
        "top-journal-figures",
        "academic-writing-scaffold",
        "research-slides-builder",
        "study-design-builder",
        "public-data-sources",
        "research-data-builder",
        "none",
    },
    "registration_plan": {
        "study-design-builder",
        "public-data-sources",
        "research-data-builder",
        "literature-matrix",
        "research-analysis-runner",
        "top-journal-figures",
        "methods-reviewer",
        "none",
    },
    "transparency_package": {
        "public-data-sources",
        "research-data-builder",
        "research-analysis-runner",
        "top-journal-figures",
        "methods-reviewer",
        "academic-writing-scaffold",
        "reviewer-response",
        "none",
    },
    "reporting_package": {
        "academic-writing-scaffold",
        "methods-reviewer",
        "top-journal-figures",
        "research-slides-builder",
        "reviewer-response",
        "none",
    },
    "revision_package": {
        "reviewer-response",
        "methods-reviewer",
        "top-journal-figures",
        "research-analysis-runner",
        "public-data-sources",
        "research-data-builder",
        "literature-matrix",
        "academic-writing-scaffold",
        "none",
    },
}


def allowed_routes(context: str) -> set[str]:
    try:
        return set(ALLOWED_NEXT_ROUTES[context])
    except KeyError as exc:
        raise KeyError(f"unknown AI4SS workflow context: {context}") from exc


def route_allowed(context: str, route: str) -> bool:
    return route in allowed_routes(context)


def route_enum_error(context: str, row_label: str, route: str, field: str = "next_skill_route") -> str | None:
    if route_allowed(context, route):
        return None
    return f"{row_label}:{field}={route}"


def status_route_errors(
    context: str,
    status: str,
    route: str,
    row_label: str,
    *,
    field: str = "next_skill_route",
) -> list[str]:
    errors: list[str] = []
    if context == "route":
        if status == "handoff_ready" and route == "none":
            errors.append(f"{row_label}: handoff_ready requires a downstream next_skill_route")
    elif context == "mida":
        expected = {
            "needs_data_check": {"public-data-sources", "research-data-builder"},
            "needs_literature_check": {"literature-matrix"},
            "needs_methods_review": {"methods-reviewer", "did-expert"},
        }.get(status)
        if expected and route not in expected:
            if len(expected) == 1:
                target = next(iter(expected))
                errors.append(f"{row_label}: {status} should route to {target}")
            else:
                errors.append(f"{row_label}: {status} should route to one of {sorted(expected)}")
    elif context == "decision":
        if status == "ready_for_handoff" and route == "none":
            errors.append(f"{row_label}: ready_for_handoff requires a downstream skill")
        expected = {
            "needs_data_check": {"public-data-sources", "research-data-builder"},
            "needs_literature_check": {"literature-matrix"},
            "needs_methods_review": {"methods-reviewer", "did-expert"},
        }.get(status)
        if expected and route not in expected:
            if len(expected) == 1:
                target = next(iter(expected))
                errors.append(f"{row_label}: {status} should route to {target}")
            else:
                errors.append(f"{row_label}: {status} should route to one of {sorted(expected)}")
    elif context == "analysis_check":
        if status == "ready" and route != "research-analysis-runner":
            errors.append(f"{row_label}: ready rows must route to research-analysis-runner")
        if status == "warn" and route not in {"research-analysis-runner", "methods-reviewer"}:
            errors.append(f"{row_label}: warn rows must route to analysis or methods review")
        if status == "repair_required" and route == "research-analysis-runner":
            errors.append(f"{row_label}: repair_required rows must route to the repair owner before analysis")
    elif context == "analysis_artifact":
        if status in {"ready_for_review", "needs_review"} and route == "none":
            errors.append(f"{row_label}: reviewable outputs require a next_skill_route")
        if route in {"academic-writing-scaffold", "top-journal-figures"} and status != "ready_for_review":
            errors.append(f"{row_label}: writing or figure packaging requires ready_for_review status")
    elif context == "registration_plan":
        if status == "ready_for_registration" and route == "none":
            errors.append(f"{row_label}: ready_for_registration requires downstream transparency review")
        if status == "needs_analysis_plan" and route != "study-design-builder":
            errors.append(f"{row_label}: needs_analysis_plan should route to study-design-builder")
    elif context == "transparency_package":
        expected = {
            "needs_data_statement": {"public-data-sources", "research-data-builder"},
            "needs_code_statement": {"research-analysis-runner"},
            "needs_reporting_boundary": {"academic-writing-scaffold"},
            "needs_reproducibility_review": {"methods-reviewer"},
        }.get(status)
        if expected and route not in expected:
            if len(expected) == 1:
                target = next(iter(expected))
                errors.append(f"{row_label}: {status} should route to {target}")
            else:
                errors.append(f"{row_label}: {status} should route to one of {sorted(expected)}")
    elif context == "reporting_package":
        if status == "ready_for_ai_disclosed_draft" and route != "academic-writing-scaffold":
            errors.append(f"{row_label}: ready_for_ai_disclosed_draft should route to academic-writing-scaffold")
        if status == "submission_gate_incomplete" and route not in {"academic-writing-scaffold", "methods-reviewer"}:
            errors.append(
                f"{row_label}: submission_gate_incomplete should route to academic-writing-scaffold or methods-reviewer"
            )
        if status == "needs_methods_review" and route != "methods-reviewer":
            errors.append(f"{row_label}: needs_methods_review should route to methods-reviewer")
        if status == "needs_figure_package" and route != "top-journal-figures":
            errors.append(f"{row_label}: needs_figure_package should route to top-journal-figures")
    elif context == "revision_package":
        if status == "needs_new_analysis" and route != "research-analysis-runner":
            errors.append(f"{row_label}: needs_new_analysis should route to research-analysis-runner")
        if status == "needs_new_data" and route not in {"public-data-sources", "research-data-builder"}:
            errors.append(f"{row_label}: needs_new_data should route to public-data-sources or research-data-builder")
        if status == "ready_for_ai_disclosed_response" and route != "reviewer-response":
            errors.append(f"{row_label}: ready_for_ai_disclosed_response should route to reviewer-response")
    else:
        raise KeyError(f"unknown AI4SS workflow context: {context}")
    return errors
