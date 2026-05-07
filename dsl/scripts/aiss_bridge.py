#!/usr/bin/env python3
"""Computable Bridge — DeclareDesign-style diagnosand computation for commensurability.

Given a model (concepts + causal edges + bridges), compute:
  - Commensurability score per causal edge (0.0–1.0)
  - IBE profile (what does this model contribute?)
  - Missing bridge detection

Design principle (from DeclareDesign): the design IS data.
The bridge's commensurability can be COMPUTED from model properties,
not just asserted by a human.

Usage:
    python3 aiss_bridge.py model.aiss
    python3 aiss_bridge.py model.aiss --json
"""

from __future__ import annotations
from dataclasses import dataclass, field
import json
import sys
import re

from aiss_parser import Program, CausalNode, BridgeNode, parse_file


# ---------------------------------------------------------------------------
# Evidence strength heuristics
# ---------------------------------------------------------------------------

EVIDENCE_PATTERNS = {
    # Strong causal evidence
    "experiment": [
        r"experiment", r"randomi[sz]ed", r"random assignment",
        r"RCT", r"field experiment", r"survey experiment",
        r"vignette", r"conjoint",
    ],
    # Quasi-experimental
    "quasi_experiment": [
        r"difference.in.difference", r"DiD", r"diff.in.diff",
        r"regression discontinuity", r"RDD",
        r"instrumental variable", r"IV",
        r"natural experiment", r"exogenous",
        r"synthetic control", r"SCM",
        r"fixed effects", r"panel",
        r"matching", r"propensity score",
    ],
    # Observational
    "observational": [
        r"regression", r"OLS", r"logit", r"probit",
        r"correlation", r"association", r"control",
        r"adjust for", r"conditional on",
        r"survey", r"interview",
    ],
    # Qualitative/ethnographic
    "qualitative": [
        r"ethnograph", r"participant observation",
        r"fieldwork", r"case study", r"process tracing",
        r"interview", r"focus group",
    ],
}


def _detect_evidence_type(text: str | None) -> str:
    """Detect the strongest evidence type mentioned in a text."""
    if not text or text == "none":
        return "none"
    text_lower = text.lower()
    for level in ["experiment", "quasi_experiment", "observational", "qualitative"]:
        for pattern in EVIDENCE_PATTERNS[level]:
            if re.search(pattern, text_lower):
                return level
    return "unspecified"


EVIDENCE_SCORES = {
    "experiment": 1.0,
    "quasi_experiment": 0.8,
    "observational": 0.4,
    "qualitative": 0.3,
    "unspecified": 0.1,
    "none": 0.0,
}


# ---------------------------------------------------------------------------
# Commensurability computation
# ---------------------------------------------------------------------------

@dataclass
class BridgeDiagnosand:
    """Computable diagnosand for a single causal edge's bridge to empirics."""
    causal_id: str
    declared_commensurability: str
    evidence_type: str
    evidence_score: float
    has_mechanism: bool
    has_condition: bool
    has_estimand: bool
    has_bridge: bool
    computed_score: float
    gap_flags: list[str] = field(default_factory=list)


def compute_commensurability(prog: Program) -> list[BridgeDiagnosand]:
    """Compute commensurability diagnosands for all causal edges."""

    # Build bridge lookup
    bridge_for_implication: dict[str, BridgeNode] = {}
    for b in prog.bridges:
        if b.implication:
            bridge_for_implication[b.implication] = b

    results = []
    for c in prog.causals:
        has_mechanism = bool(c.mechanism and c.mechanism != "none")
        has_condition = bool(c.condition and c.condition != "none")
        bridged = c.id in bridge_for_implication
        bridge_obj = bridge_for_implication.get(c.id)
        declared = bridge_obj.commensurability if bridge_obj else "unchecked"
        support_text = _bridge_support_text(bridge_obj)
        evidence_type = _detect_evidence_type(support_text)
        evidence_score = EVIDENCE_SCORES[evidence_type]
        has_estimand = bool(bridge_obj and bridge_obj.estimand and bridge_obj.estimand != "none")

        # Computed commensurability score
        # Base = evidence quality (0-1)
        # Mechanism present = +0.1
        # Condition specified = +0.05
        # Estimand present = +0.15
        # Bridge present = +0.1
        score = evidence_score
        if has_mechanism:
            score += 0.10
        if has_condition:
            score += 0.05
        if has_estimand:
            score += 0.15
        if bridged:
            score += 0.10
        score = min(score, 1.0)

        # Gap flags
        gaps = []
        if evidence_type == "none":
            gaps.append("no_evidence")
        if not has_mechanism:
            gaps.append("no_mechanism")
        if not bridged:
            gaps.append("no_bridge")
        if not has_estimand:
            gaps.append("no_estimand")
        if declared == "unchecked":
            gaps.append("declared_unchecked")
        elif declared == "weak" and evidence_score >= 0.8:
            gaps.append("declared_weak_but_evidence_is_strong")
        elif declared == "strong" and evidence_score < 0.4:
            gaps.append("declared_strong_but_evidence_is_weak")

        results.append(BridgeDiagnosand(
            causal_id=c.id,
            declared_commensurability=declared,
            evidence_type=evidence_type,
            evidence_score=evidence_score,
            has_mechanism=has_mechanism,
            has_condition=has_condition,
            has_estimand=has_estimand,
            has_bridge=bridged,
            computed_score=score,
            gap_flags=gaps,
        ))

    return results


def _bridge_support_text(bridge: BridgeNode | None) -> str | None:
    """Concatenate bridge fields that describe the empirical warrant."""
    if bridge is None:
        return None
    parts = [
        bridge.method,
        bridge.validity,
        bridge.estimand,
        bridge.note,
    ]
    return " ".join(str(p) for p in parts if p and p != "none")


# ---------------------------------------------------------------------------
# IBE profile
# ---------------------------------------------------------------------------

@dataclass
class IBEProfile:
    """Computable IBE profile for a model."""
    model_id: str
    n_concepts: int
    n_causal_edges: int
    n_bridges: int
    has_explanations: bool
    has_facts: bool
    has_strong_bridge: bool
    commensurability_coverage: float   # proportion of causal edges with bridges
    avg_commensurability_score: float
    contribution_type: str
    gap_summary: list[str]


def compute_ibe_profile(prog: Program) -> list[IBEProfile]:
    """Compute IBE profiles for all models."""
    results = []
    diagnosands = compute_commensurability(prog)

    for m in prog.models:
        n_causal = len(m.causal)
        n_bridges = len(m.bridges)

        # Filter diagnosands to this model's causal edges
        m_diags = [d for d in diagnosands if d.causal_id in m.causal]

        has_explanations = n_causal > 0
        has_facts = len(m.concepts) > 0
        has_strong_bridge = any(
            b.commensurability == "strong"
            for b in prog.bridges
            if b.id in m.bridges
        )

        coverage = len([d for d in m_diags if d.has_bridge]) / max(n_causal, 1)
        avg_score = sum(d.computed_score for d in m_diags) / max(len(m_diags), 1)

        # Classify contribution type
        if not has_explanations and has_facts:
            contribution = "facts_only"
        elif has_explanations and not has_facts:
            contribution = "explanation_only"
        elif has_strong_bridge:
            contribution = "full_study_with_strong_bridge"
        elif coverage > 0:
            contribution = "explanation_with_evidence"
        else:
            contribution = "explanation_without_evidence"

        # Gap summary
        gap_summary = []
        if n_causal == 0:
            gap_summary.append("no causal claims (descriptive only)")
        if coverage == 0 and n_causal > 0:
            gap_summary.append(f"{n_causal} causal edges, 0 bridged to empirics")
        if coverage < 1.0 and n_causal > 0:
            unbridged = n_causal - len([d for d in m_diags if d.has_bridge])
            gap_summary.append(f"{unbridged}/{n_causal} edges lack bridges")
        unchecked = len([d for d in m_diags if "declared_unchecked" in d.gap_flags])
        if unchecked:
            gap_summary.append(f"{unchecked} edges declared 'unchecked'")

        results.append(IBEProfile(
            model_id=m.id,
            n_concepts=len(m.concepts),
            n_causal_edges=n_causal,
            n_bridges=n_bridges,
            has_explanations=has_explanations,
            has_facts=has_facts,
            has_strong_bridge=has_strong_bridge,
            commensurability_coverage=coverage,
            avg_commensurability_score=avg_score,
            contribution_type=contribution,
            gap_summary=gap_summary,
        ))

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 aiss_bridge.py <file.aiss> [--json]", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    output_json = "--json" in sys.argv
    prog = parse_file(filepath)

    diagnosands = compute_commensurability(prog)
    profiles = compute_ibe_profile(prog)

    if output_json:
        print(json.dumps({
            "diagnosands": [
                {
                    "causal_id": d.causal_id,
                    "declared": d.declared_commensurability,
                    "evidence_type": d.evidence_type,
                    "computed_score": round(d.computed_score, 2),
                    "gaps": d.gap_flags,
                }
                for d in diagnosands
            ],
            "ibe_profiles": [
                {
                    "model_id": p.model_id,
                    "contribution_type": p.contribution_type,
                    "avg_score": round(p.avg_commensurability_score, 2),
                    "coverage": round(p.commensurability_coverage, 2),
                    "gaps": p.gap_summary,
                }
                for p in profiles
            ],
        }, indent=2))
    else:
        print("Commensurability Diagnosands:")
        for d in diagnosands:
            print(f"  {d.causal_id}:")
            print(f"    declared={d.declared_commensurability}, "
                  f"evidence={d.evidence_type}({d.evidence_score:.1f}), "
                  f"computed={d.computed_score:.2f}")
            if d.gap_flags:
                print(f"    gaps: {', '.join(d.gap_flags)}")
        print()
        print("IBE Profiles:")
        for p in profiles:
            print(f"  {p.model_id}:")
            print(f"    contribution: {p.contribution_type}")
            print(f"    avg commensurability: {p.avg_commensurability_score:.2f}")
            print(f"    bridge coverage: {p.commensurability_coverage:.0%}")
            if p.gap_summary:
                for g in p.gap_summary:
                    print(f"    ⚠️  {g}")


if __name__ == "__main__":
    main()
