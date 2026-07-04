"""Shared workflow-routing interface for the AI4SS research factory."""

from __future__ import annotations


RESEARCH_FACTORY_SKILLS = (
    "research-starter",
    "study-design-builder",
    "research-data-builder",
    "literature-matrix",
    "research-analysis-runner",
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
    "author_decisions",
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
        "research-data-builder",
        "literature-matrix",
        "methods-reviewer",
        "academic-writing-scaffold",
        "research-slides-builder",
        "reviewer-response",
        "did-expert",
        "ask_author",
        "none",
    },
    "mida": {
        "research-data-builder",
        "literature-matrix",
        "research-analysis-runner",
        "methods-reviewer",
        "did-expert",
        "ask_author",
        "none",
    },
    "decision": {
        "research-data-builder",
        "literature-matrix",
        "research-analysis-runner",
        "methods-reviewer",
        "did-expert",
        "ask_author",
        "none",
    },
    "literature_evidence": {
        "study-design-builder",
        "academic-writing-scaffold",
        "methods-reviewer",
        "ask_author",
    },
    "rival_check": {
        "methods-reviewer",
        "study-design-builder",
        "academic-writing-scaffold",
        "ask_author",
    },
    "scope_check": {
        "methods-reviewer",
        "study-design-builder",
        "academic-writing-scaffold",
        "ask_author",
    },
    "analysis_check": {
        "research-analysis-runner",
        "research-data-builder",
        "study-design-builder",
        "methods-reviewer",
        "ask_author",
    },
    "analysis_artifact": {
        "methods-reviewer",
        "academic-writing-scaffold",
        "research-slides-builder",
        "study-design-builder",
        "research-data-builder",
        "ask_author",
        "none",
    },
    "registration_plan": {
        "study-design-builder",
        "research-data-builder",
        "literature-matrix",
        "research-analysis-runner",
        "methods-reviewer",
        "ask_author",
        "none",
    },
    "transparency_package": {
        "research-data-builder",
        "research-analysis-runner",
        "methods-reviewer",
        "academic-writing-scaffold",
        "reviewer-response",
        "ask_author",
        "none",
    },
    "reporting_package": {
        "academic-writing-scaffold",
        "methods-reviewer",
        "research-slides-builder",
        "reviewer-response",
        "ask_author",
        "none",
    },
    "revision_package": {
        "reviewer-response",
        "methods-reviewer",
        "research-analysis-runner",
        "research-data-builder",
        "literature-matrix",
        "academic-writing-scaffold",
        "ask_author",
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
        if status == "handoff_ready" and route in {"none", "ask_author"}:
            errors.append(f"{row_label}: handoff_ready requires a downstream next_skill_route")
    elif context == "mida":
        expected = {
            "needs_author_decision": {"ask_author"},
            "needs_data_check": {"research-data-builder"},
            "needs_literature_check": {"literature-matrix"},
            "needs_methods_review": {"methods-reviewer", "did-expert"},
        }.get(status)
        if expected and route not in expected:
            if len(expected) == 1:
                target = next(iter(expected))
                errors.append(f"{row_label}: {status} should route to {target}")
            else:
                errors.append(f"{row_label}: {status} should route to methods-reviewer or did-expert")
    elif context == "decision":
        if status == "ready_for_handoff" and route in {"none", "ask_author"}:
            errors.append(f"{row_label}: ready_for_handoff requires a downstream skill")
        expected = {
            "needs_author_decision": {"ask_author"},
            "needs_data_check": {"research-data-builder"},
            "needs_literature_check": {"literature-matrix"},
        }.get(status)
        if expected and route not in expected:
            target = next(iter(expected))
            errors.append(f"{row_label}: {status} should route to {target}")
    elif context == "analysis_check":
        if status == "ready" and route != "research-analysis-runner":
            errors.append(f"{row_label}: ready rows must route to research-analysis-runner")
        if status == "warn" and route not in {"research-analysis-runner", "methods-reviewer"}:
            errors.append(f"{row_label}: warn rows must route to analysis or methods review")
        if status == "blocked" and route == "research-analysis-runner":
            errors.append(f"{row_label}: blocked rows cannot route to research-analysis-runner")
    elif context == "analysis_artifact":
        if status in {"ready_for_review", "needs_review"} and route == "none":
            errors.append(f"{row_label}: reviewable outputs require a next_skill_route")
        if route == "academic-writing-scaffold" and status != "ready_for_review":
            errors.append(f"{row_label}: writing scaffold requires ready_for_review status")
    elif context == "registration_plan":
        if status == "ready_for_registration" and route in {"none"}:
            errors.append(f"{row_label}: ready_for_registration requires author or downstream transparency review")
        if status == "needs_author_decision" and route != "ask_author":
            errors.append(f"{row_label}: needs_author_decision should route to ask_author")
        if status == "needs_analysis_plan" and route != "study-design-builder":
            errors.append(f"{row_label}: needs_analysis_plan should route to study-design-builder")
    elif context == "transparency_package":
        expected = {
            "needs_data_statement": {"research-data-builder"},
            "needs_code_statement": {"research-analysis-runner"},
            "needs_reporting_boundary": {"academic-writing-scaffold"},
            "needs_reproducibility_review": {"methods-reviewer"},
        }.get(status)
        if expected and route not in expected:
            target = next(iter(expected))
            errors.append(f"{row_label}: {status} should route to {target}")
    elif context == "reporting_package":
        if status == "ready_for_ai_disclosed_draft" and route not in {"academic-writing-scaffold", "ask_author"}:
            errors.append(f"{row_label}: ready_for_ai_disclosed_draft should route to academic-writing-scaffold or ask_author")
        if status == "submission_gate_incomplete" and route not in {"academic-writing-scaffold", "methods-reviewer", "ask_author"}:
            errors.append(
                f"{row_label}: submission_gate_incomplete should route to academic-writing-scaffold, methods-reviewer, or ask_author"
            )
        if status == "needs_methods_review" and route != "methods-reviewer":
            errors.append(f"{row_label}: needs_methods_review should route to methods-reviewer")
    elif context == "revision_package":
        if status == "needs_new_analysis" and route != "research-analysis-runner":
            errors.append(f"{row_label}: needs_new_analysis should route to research-analysis-runner")
        if status == "needs_new_data" and route != "research-data-builder":
            errors.append(f"{row_label}: needs_new_data should route to research-data-builder")
        if status == "ready_for_ai_disclosed_response" and route != "reviewer-response":
            errors.append(f"{row_label}: ready_for_ai_disclosed_response should route to reviewer-response")
    else:
        raise KeyError(f"unknown AI4SS workflow context: {context}")
    return errors
