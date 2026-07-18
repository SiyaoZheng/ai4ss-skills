"""Shared workflow-routing interface for the AI4SS research factory."""

from __future__ import annotations

from .sidecars import sidecar_field_group


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

CORE_HANDOFF_FIELDS = tuple(sidecar_field_group("core_handoff"))

MODEL_LINK_FIELDS = tuple(sidecar_field_group("model_link"))

TERMINAL_ROUTE = "last_skill"
"""Repair-loop route for returning control to the previous workflow layer.

`last_skill` means the current skill has reached a boundary it cannot
responsibly resolve by itself. The skill should return a bounded handoff for
the caller, controller, or previous skill to redesign, source-gate, data-gate,
or surface required gate handling. It is not a direct-query route, not a final
state, and not permission to produce final scholarly claims. A completed
harness run must loop through the handoff until it reaches a feasible current
inquiry and a bounded report artifact.
"""

COMPLETION_GATE_STATUSES = {"passed", "redesigned", "scoped_out"}
UPGRADE_GATE_STATUS = "queued"

FORBIDDEN_FALLBACK_ANALYSIS_TERMS = (
    "synthetic data",
    "simulated data",
    "toy data",
    "placeholder data",
    "demo analysis",
    "synthetic analysis",
    "simulation as analysis",
)


def forbidden_fallback_analysis_errors(text: str, row_label: str) -> list[str]:
    """Return errors for analysis fallbacks that pretend unavailable data exist."""

    lowered = text.lower()
    return [
        f"{row_label}: forbidden fallback analysis term `{term}`"
        for term in FORBIDDEN_FALLBACK_ANALYSIS_TERMS
        if term in lowered
    ]

ALLOWED_NEXT_ROUTES: dict[str, set[str]] = {
    "research_routes": {
        "study-design-builder",
        "public-data-sources",
        "research-data-builder",
        "literature-matrix",
        "methods-reviewer",
        "academic-writing-scaffold",
        "research-slides-builder",
        "reviewer-response",
        "did-expert",
        TERMINAL_ROUTE,
        "none",
    },
    "study_design_declaration": {
        "public-data-sources",
        "research-data-builder",
        "literature-matrix",
        "research-analysis-runner",
        "methods-reviewer",
        "did-expert",
        TERMINAL_ROUTE,
        "none",
    },
    "design_decisions": {
        "public-data-sources",
        "research-data-builder",
        "literature-matrix",
        "research-analysis-runner",
        "methods-reviewer",
        "did-expert",
        TERMINAL_ROUTE,
        "none",
    },
    "literature_theory_synthesis": {
        "study-design-builder",
        "academic-writing-scaffold",
        "methods-reviewer",
        TERMINAL_ROUTE,
    },
    "theory_rival_map": {
        "methods-reviewer",
        "study-design-builder",
        "academic-writing-scaffold",
        TERMINAL_ROUTE,
    },
    "theory_scope_map": {
        "methods-reviewer",
        "study-design-builder",
        "academic-writing-scaffold",
        TERMINAL_ROUTE,
    },
    "analysis_readiness": {
        "research-analysis-runner",
        "public-data-sources",
        "research-data-builder",
        "study-design-builder",
        "methods-reviewer",
        TERMINAL_ROUTE,
    },
    "analysis_manifest": {
        "methods-reviewer",
        "top-journal-figures",
        "academic-writing-scaffold",
        "research-slides-builder",
        "study-design-builder",
        "research-data-builder",
        TERMINAL_ROUTE,
        "none",
    },
    "event": set(RESEARCH_FACTORY_SKILLS)
    | {
        "analysis-explainer",
        "did-expert",
        "latex-tables",
        "codebook-parse",
        "cleaning-contract",
        "cleaning-execute",
        "codex",
        "r-performance",
        "sjtu-hpc",
        TERMINAL_ROUTE,
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
    if context == "research_routes":
        if status == "handoff_ready" and route in {"none", TERMINAL_ROUTE}:
            errors.append(f"{row_label}: handoff_ready requires a downstream next_skill_route")
    elif context == "study_design_declaration":
        expected = {
            "needs_redesign": {TERMINAL_ROUTE},
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
    elif context == "design_decisions":
        if status == "ready_for_handoff" and route in {"none", TERMINAL_ROUTE}:
            errors.append(f"{row_label}: ready_for_handoff requires a downstream skill")
        expected = {
            "needs_redesign": {TERMINAL_ROUTE},
            "needs_data_check": {"public-data-sources", "research-data-builder"},
            "needs_literature_check": {"literature-matrix"},
        }.get(status)
        if expected and route not in expected:
            if len(expected) == 1:
                target = next(iter(expected))
                errors.append(f"{row_label}: {status} should route to {target}")
            else:
                errors.append(f"{row_label}: {status} should route to one of {sorted(expected)}")
    elif context == "analysis_readiness":
        if status == "ready" and route != "research-analysis-runner":
            errors.append(f"{row_label}: ready rows must route to research-analysis-runner")
        if status == "warn" and route not in {"research-analysis-runner", "methods-reviewer"}:
            errors.append(f"{row_label}: warn rows must route to analysis or methods review")
        if status == "blocked" and route == "research-analysis-runner":
            errors.append(f"{row_label}: blocked rows cannot route to research-analysis-runner")
    elif context == "analysis_manifest":
        if status in {"ready_for_review", "needs_review"} and route == "none":
            errors.append(f"{row_label}: reviewable outputs require a next_skill_route")
        if route == "academic-writing-scaffold" and status != "ready_for_review":
            errors.append(f"{row_label}: writing scaffold requires ready_for_review status")
    elif context == "event":
        pass
    else:
        raise KeyError(f"unknown AI4SS workflow context: {context}")
    return errors
