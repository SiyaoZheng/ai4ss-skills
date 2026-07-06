#!/usr/bin/env python3
"""Interface tests for shared AI4SS factory contract modules."""

from __future__ import annotations

import os

from ai4ss_factory_contracts.latex_plugin import (
    DISABLE_ENV,
    LATEX_PLUGIN_SCRIPT_NAMES,
    LATEX_PLUGIN_SKILL_NAMES,
    bundled_latex_plugin_root,
    bundled_latex_plugin_skills,
)
from ai4ss_factory_contracts.workflow import (
    CORE_HANDOFF_FIELDS,
    MODEL_LINK_FIELDS,
    allowed_routes,
    status_route_errors,
)


def main() -> None:
    assert "target_inquiry" in CORE_HANDOFF_FIELDS
    assert "replication_package_status" in CORE_HANDOFF_FIELDS
    assert "ai_contribution_disclosure" in CORE_HANDOFF_FIELDS
    assert "direct_submission_status" in CORE_HANDOFF_FIELDS
    assert "assumption_register" in CORE_HANDOFF_FIELDS
    assert "ai4ss_model_path" in MODEL_LINK_FIELDS
    assert MODEL_LINK_FIELDS[-1] == "ai4ss_check_status"

    assert "study-design-builder" in allowed_routes("route")
    assert "public-data-sources" in allowed_routes("route")
    assert "top-journal-figures" in allowed_routes("analysis_artifact")
    assert status_route_errors("route", "handoff_ready", "none", "R1") == [
        "R1: handoff_ready requires a downstream next_skill_route"
    ]
    assert status_route_errors("mida", "needs_data_check", "literature-matrix", "D1") == [
        "D1: needs_data_check should route to one of ['public-data-sources', 'research-data-builder']"
    ]
    assert status_route_errors("analysis_check", "ready", "methods-reviewer", "C1") == [
        "C1: ready rows must route to research-analysis-runner"
    ]
    assert "research-analysis-runner" in allowed_routes("transparency_package")
    assert status_route_errors("transparency_package", "needs_code_statement", "research-data-builder", "T1") == [
        "T1: needs_code_statement should route to research-analysis-runner"
    ]
    assert status_route_errors("revision_package", "needs_new_analysis", "reviewer-response", "R2") == [
        "R2: needs_new_analysis should route to research-analysis-runner"
    ]
    assert status_route_errors("reporting_package", "submission_gate_incomplete", "research-slides-builder", "P1") == [
        "P1: submission_gate_incomplete should route to academic-writing-scaffold or methods-reviewer"
    ]
    assert status_route_errors("reporting_package", "needs_figure_package", "academic-writing-scaffold", "P2") == [
        "P2: needs_figure_package should route to top-journal-figures"
    ]
    assert status_route_errors("revision_package", "ready_for_ai_disclosed_response", "academic-writing-scaffold", "R3") == [
        "R3: ready_for_ai_disclosed_response should route to reviewer-response"
    ]

    latex_disabled = os.environ.get(DISABLE_ENV, "").strip().lower() in {"1", "true", "yes", "on"}
    latex_root = None if latex_disabled else bundled_latex_plugin_root()
    latex_skills = bundled_latex_plugin_skills()
    if latex_root is None or latex_disabled:
        assert latex_skills == []
    else:
        assert [skill.name for skill in latex_skills] == list(LATEX_PLUGIN_SKILL_NAMES)
        for skill in latex_skills:
            assert "AI4SS Harness Packaging Note" in skill.instructions
            assert set(LATEX_PLUGIN_SCRIPT_NAMES).issubset(skill.scripts)


if __name__ == "__main__":
    main()
