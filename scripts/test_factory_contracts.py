#!/usr/bin/env python3
"""Interface tests for shared AI4SS factory contract modules."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

from ai4ss_factory_contracts.sidecars import (
    ai4ss_model_path_error,
    blank_required_cells,
    duplicate_values,
    exact_field_error,
    load_rows,
    sidecar_field_group,
    sidecar_fields,
)
from ai4ss_factory_contracts.workflow import (
    CORE_HANDOFF_FIELDS,
    allowed_routes,
    status_route_errors,
)


def main() -> None:
    fields = sidecar_fields("research_routes")
    assert fields[0] == "route_id"
    assert fields[-1] == "next_skill_route"
    assert "ai4ss_model_path" in sidecar_fields("analysis_manifest")
    assert sidecar_field_group("model_link")[-1] == "ai4ss_check_status"
    assert "target_inquiry" in CORE_HANDOFF_FIELDS

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "routes.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fields)
            writer.writerow(["R1"] + ["x"] * (len(fields) - 1))
        loaded_fields, rows = load_rows(path)
        assert exact_field_error(path, loaded_fields, fields) is None
        assert rows[0]["route_id"] == "R1"
        assert not blank_required_cells(rows, fields, lambda row, i: row["route_id"])
        assert not duplicate_values(rows, "route_id")

    assert ai4ss_model_path_error("docs/research_model.aiss", "R1") is None
    assert ai4ss_model_path_error("not_applicable:no model", "R1") is None
    assert ai4ss_model_path_error("docs/research_model.json", "R1") == "R1: ai4ss_model_path must end with .aiss"

    assert "study-design-builder" in allowed_routes("research_routes")
    assert status_route_errors("research_routes", "handoff_ready", "none", "R1") == [
        "R1: handoff_ready requires a downstream next_skill_route"
    ]
    assert status_route_errors("study_design_declaration", "needs_data_check", "literature-matrix", "D1") == [
        "D1: needs_data_check should route to research-data-builder"
    ]
    assert status_route_errors("analysis_readiness", "ready", "methods-reviewer", "C1") == [
        "C1: ready rows must route to research-analysis-runner"
    ]


if __name__ == "__main__":
    main()
