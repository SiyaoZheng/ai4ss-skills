#!/usr/bin/env python3
"""Shared AI4SS research workspace contract constants.

Keep this module in sync with docs/research_workspace_contract.md. Skill files
should reference that document instead of repeating the full directory tree.
"""

from __future__ import annotations


CONTRACT_DOC = "docs/research_workspace_contract.md"
CANONICAL_STATE_PATH = ".ai4ss/research_model.aiss"

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

CONTRACT_TERMS = (
    "/workspace/",
    "Makefile",
    ".ai4ss/",
    CANONICAL_STATE_PATH,
    "data/raw/",
    "data/intermediate/",
    "data/processed/",
    "scripts/",
    "output/tables/",
    "output/figures/",
    "output/models/",
    "output/logs/",
    "paper/",
    "make all",
)

GENERATED_PATH_PREFIXES = (
    "data/intermediate/",
    "data/processed/",
    "output/tables/",
    "output/figures/",
    "output/models/",
    "output/logs/",
)

LEGACY_PATH_PREFIXES = (
    "outputs/",
    "output/audit/",
    "data/interim/",
    "data/analysis/",
)

PROTECTED_PATH_PREFIXES = GENERATED_PATH_PREFIXES + LEGACY_PATH_PREFIXES

FORBIDDEN_LEGACY_TERMS = (
    "docs/research_model.aiss",
    "`research_model.aiss` at the workspace root",
    "root-level `research_model.aiss`",
    "outputs/",
    "output/audit/",
    "data/interim/",
    "data/analysis/",
)

PAPER_GENERATED_SUFFIXES = (
    ".aux",
    ".bbl",
    ".bcf",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".out",
    ".pdf",
    ".run.xml",
    ".synctex.gz",
    ".toc",
)

WORKFLOW_STAGE_SCRIPT_STEMS = (
    "build_data",
    "run_analysis",
    "build_tables",
    "build_figures",
    "build_paper",
    "compile_paper",
)

SCAFFOLD_DIRS = (
    ".ai4ss",
    ".ai4ss/checks",
    ".ai4ss/handoffs",
    ".ai4ss/scratch",
    "data/raw",
    "data/intermediate",
    "data/processed",
    "scripts",
    "output/tables",
    "output/figures",
    "output/models",
    "output/logs",
    "paper",
)
