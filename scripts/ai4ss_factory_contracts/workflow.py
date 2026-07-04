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
    else:
        raise KeyError(f"unknown AI4SS workflow context: {context}")
    return errors
