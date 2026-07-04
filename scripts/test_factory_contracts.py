#!/usr/bin/env python3
"""Interface tests for shared AI4SS factory contract modules."""

from __future__ import annotations

from ai4ss_factory_contracts.workflow import (
    CORE_HANDOFF_FIELDS,
    MODEL_LINK_FIELDS,
    allowed_routes,
    status_route_errors,
)


def main() -> None:
    assert "target_inquiry" in CORE_HANDOFF_FIELDS
    assert "ai4ss_model_path" in MODEL_LINK_FIELDS
    assert MODEL_LINK_FIELDS[-1] == "ai4ss_check_status"

    assert "study-design-builder" in allowed_routes("route")
    assert status_route_errors("route", "handoff_ready", "none", "R1") == [
        "R1: handoff_ready requires a downstream next_skill_route"
    ]
    assert status_route_errors("mida", "needs_data_check", "literature-matrix", "D1") == [
        "D1: needs_data_check should route to research-data-builder"
    ]
    assert status_route_errors("analysis_check", "ready", "methods-reviewer", "C1") == [
        "C1: ready rows must route to research-analysis-runner"
    ]


if __name__ == "__main__":
    main()
