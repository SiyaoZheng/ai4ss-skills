#!/usr/bin/env python3
"""AISS deterministic toolchain core.

This module implements the unified v0.4 source parser, canonical AST compiler,
lint/run/diff/write helpers, and code-manifest generation. It intentionally
does not call LLMs or consult network resources.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import hashlib
import json
import re
import sys

try:
    _CONTRACTS_ROOT = Path(__file__).resolve().parents[2] / "scripts"
    if str(_CONTRACTS_ROOT) not in sys.path:
        sys.path.insert(0, str(_CONTRACTS_ROOT))
    from ai4ss_factory_contracts.workflow import (  # type: ignore
        ALLOWED_NEXT_ROUTES as FACTORY_ALLOWED_NEXT_ROUTES,
        MIDA_COMPONENTS as FACTORY_MIDA_COMPONENTS,
        RESEARCH_FACTORY_SKILLS as FACTORY_RESEARCH_SKILLS,
    )
except Exception:  # pragma: no cover - fallback for standalone script copies.
    FACTORY_RESEARCH_SKILLS = (
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
    FACTORY_MIDA_COMPONENTS = {
        "model",
        "inquiry",
        "data_strategy",
        "answer_strategy",
        "diagnose",
        "redesign",
        "report_boundary",
    }
    FACTORY_ALLOWED_NEXT_ROUTES = {
        "route": set(FACTORY_RESEARCH_SKILLS) | {"did-expert", "none"},
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
        "event": set(FACTORY_RESEARCH_SKILLS)
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
    }


SCHEMA_VERSION = "0.4"
SUPPORTED_SCHEMA_VERSIONS = {"0.4"}
COMPILER_VERSION = "0.4.0"
UNIFIED_AST_SCHEMA = "aiss.unified_ast.v0.4"

SOURCE_DECLARATIONS = {
    "paper",
    "source",
    "span",
    "concept",
    "claim",
    "relation",
    "empirical",
    "observation",
    "coupling",
    "artifact",
    "adapter",
}

MODEL_DECLARATIONS = {
    "attribute",
    "causal",
    "bridge",
    "model",
    "edge",
    "check",
    "derive",
}

WORKFLOW_DECLARATIONS = {
    "route",
    "mida",
    "decision",
    "event",
}

ALL_DECLARATIONS = SOURCE_DECLARATIONS | MODEL_DECLARATIONS | WORKFLOW_DECLARATIONS

FORBIDDEN_DERIVED_DECLARATIONS = {
    "fact",
    "gap",
    "diagnostic",
    "support_score",
    "unsupported_claim",
    "overclaim",
    "next_action",
    "review_comment",
    "critique",
    "lint_result",
}

THEORY_KINDS = {"concept", "claim", "relation", "causal"}
EMPIRICAL_KINDS = {"empirical", "observation", "artifact"}
COUPLING_KINDS = {"coupling"}
MODEL_KINDS = {"attribute", "bridge", "edge", "model", "check", "derive"}
WORKFLOW_KINDS = {"route", "mida", "decision"}
MIDA_COMPONENTS = set(FACTORY_MIDA_COMPONENTS)
ROUTE_STATUSES = {"candidate", "selected", "rejected", "repair_and_continue"}
ALLOWED_NEXT_SKILL_ROUTES = set().union(*FACTORY_ALLOWED_NEXT_ROUTES.values())
ALLOWED_NEXT_SKILL_ROUTES.update(FACTORY_RESEARCH_SKILLS)
ALLOWED_NEXT_SKILL_ROUTES.update({"did-expert", "none"})
REPAIR_STATUS_DEFAULT_ROUTE = {
    "needs_data_check": "public-data-sources",
    "needs_literature_check": "literature-matrix",
    "needs_methods_review": "methods-reviewer",
    "repair_required": "methods-reviewer",
}
MACHINE_EVENT_TYPES = {
    "skill_started",
    "skill_completed",
    "skill_failed",
    "check_passed",
    "check_failed",
    "repair_required",
    "heartbeat_seen",
    "heartbeat_interrupted",
    "goal_blocked",
    "goal_completed",
}
DEFAULT_HEARTBEAT_STALE_SECONDS = 3600

REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "paper": ("title", "kind", "sources"),
    "source": ("kind", "uri", "media_type", "locator_scheme"),
    "span": ("source", "locator"),
    "concept": ("term", "spans"),
    "claim": ("kind", "text", "spans"),
    "relation": ("type", "from", "to", "spans"),
    "empirical": ("kind", "label", "spans"),
    "observation": ("kind", "text", "about", "spans"),
    "coupling": ("type", "theory", "empirical", "asserted_by", "spans"),
    "artifact": ("kind", "uri", "media_type"),
    "adapter": ("version", "consumes", "produces"),
    "attribute": ("domain", "values"),
    "causal": ("source", "target", "direction"),
    "edge": ("type", "source", "target"),
    "bridge": ("type",),
    "model": (),
    "check": ("type", "on"),
    "derive": ("type", "from"),
    "route": (
        "question",
        "status",
        "study_type",
        "unit_of_analysis",
        "inquiry",
        "data_strategy",
        "answer_strategy",
        "continuation_plan",
        "next_skill_route",
    ),
    "mida": ("route", "component", "text", "status"),
    "decision": ("route", "component", "decision", "status", "owner", "next_skill_route"),
    "event": ("type", "at"),
}

REFERENCE_FIELDS: dict[str, dict[str, str]] = {
    "paper": {"sources": "source"},
    "span": {"source": "source"},
    "attribute": {"spans": "span"},
    "concept": {"spans": "span", "attributes": "attribute", "parents": "attribute"},
    "claim": {
        "concepts": "concept",
        "spans": "span",
        "scope": "any",
        "subject": "concept",
        "object": "concept",
    },
    "relation": {"from": "theory", "to": "theory", "spans": "span"},
    "causal": {"source": "concept", "target": "concept", "claim": "claim", "spans": "span"},
    "edge": {"source": "any", "target": "any", "spans": "span"},
    "empirical": {"spans": "span", "artifacts": "artifact"},
    "observation": {"about": "empirical", "concepts": "concept", "spans": "span"},
    "coupling": {"theory": "theory", "empirical": "empirical", "spans": "span"},
    "bridge": {
        "concept": "concept",
        "implication": "causal",
        "coupling": "coupling",
        "empirical": "empirical",
        "spans": "span",
    },
    "model": {
        "attributes": "attribute",
        "concepts": "concept",
        "causal": "causal",
        "bridges": "bridge",
    },
    "check": {"on": "model"},
    "derive": {"from": "model"},
    "route": {
        "spans": "span",
        "candidate_concepts": "concept",
        "candidate_causal": "causal",
        "candidate_bridges": "bridge",
    },
    "mida": {
        "route": "route",
        "spans": "span",
        "concepts": "concept",
        "causal": "causal",
        "bridges": "bridge",
        "model": "model",
    },
    "decision": {
        "route": "route",
        "spans": "span",
        "concepts": "concept",
        "causal": "causal",
        "bridges": "bridge",
        "model": "model",
    },
    "event": {
        "route": "route",
        "mida": "mida",
        "decision": "decision",
        "artifact": "artifact",
        "check": "check",
        "model": "model",
    },
}

STRUCTURED_CLAIM_FIELDS = ("subject", "predicate", "object", "polarity")
ASSERTED_MODALITIES = {"", "asserted"}
CONTRADICTORY_POLARITY_PAIRS = {
    frozenset(("positive", "negative")),
    frozenset(("positive", "null")),
    frozenset(("negative", "null")),
    frozenset(("present", "absent")),
}


class AissError(Exception):
    """Deterministic AISS toolchain error."""


@dataclass(frozen=True)
class Token:
    typ: str
    value: Any
    line: int
    col: int


@dataclass(frozen=True)
class BaseDecl:
    id: str
    fields: dict[str, Any]
    line: int

    @property
    def kind(self) -> str:
        return str(self.fields.get("__unknown_kind__", "unknown"))


@dataclass(frozen=True)
class PaperDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "paper"


@dataclass(frozen=True)
class SourceDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "source"


@dataclass(frozen=True)
class SpanDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "span"


@dataclass(frozen=True)
class ConceptDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "concept"


@dataclass(frozen=True)
class ClaimDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "claim"


@dataclass(frozen=True)
class RelationDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "relation"


@dataclass(frozen=True)
class EmpiricalDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "empirical"


@dataclass(frozen=True)
class ObservationDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "observation"


@dataclass(frozen=True)
class CouplingDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "coupling"


@dataclass(frozen=True)
class ArtifactDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "artifact"


@dataclass(frozen=True)
class AdapterDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "adapter"


@dataclass(frozen=True)
class AttributeDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "attribute"


@dataclass(frozen=True)
class CausalDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "causal"


@dataclass(frozen=True)
class BridgeDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "bridge"


@dataclass(frozen=True)
class ModelDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "model"


@dataclass(frozen=True)
class EdgeDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "edge"


@dataclass(frozen=True)
class CheckDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "check"


@dataclass(frozen=True)
class DeriveDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "derive"


@dataclass(frozen=True)
class RouteDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "route"


@dataclass(frozen=True)
class MidaDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "mida"


@dataclass(frozen=True)
class DecisionDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "decision"


@dataclass(frozen=True)
class EventDecl(BaseDecl):
    @property
    def kind(self) -> str:
        return "event"


DECL_CLASSES = {
    "paper": PaperDecl,
    "source": SourceDecl,
    "span": SpanDecl,
    "concept": ConceptDecl,
    "claim": ClaimDecl,
    "relation": RelationDecl,
    "empirical": EmpiricalDecl,
    "observation": ObservationDecl,
    "coupling": CouplingDecl,
    "artifact": ArtifactDecl,
    "adapter": AdapterDecl,
    "attribute": AttributeDecl,
    "causal": CausalDecl,
    "bridge": BridgeDecl,
    "model": ModelDecl,
    "edge": EdgeDecl,
    "check": CheckDecl,
    "derive": DeriveDecl,
    "route": RouteDecl,
    "mida": MidaDecl,
    "decision": DecisionDecl,
    "event": EventDecl,
}


@dataclass(frozen=True)
class AissProgram:
    version: str
    declarations: tuple[BaseDecl, ...]
    source_text: str
    filename: str


class Lexer:
    def __init__(self, text: str, filename: str = "<input>"):
        self.text = text
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1

    def error(self, msg: str) -> None:
        raise AissError(f"{self.filename}:{self.line}:{self.col}: {msg}")

    def peek(self) -> str:
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def advance(self) -> str:
        if self.pos >= len(self.text):
            return ""
        ch = self.text[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_ws_and_comments(self) -> None:
        while self.pos < len(self.text):
            ch = self.peek()
            if ch in " \t\r\n":
                self.advance()
                continue
            if ch == "/" and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == "/":
                while self.pos < len(self.text) and self.peek() != "\n":
                    self.advance()
                continue
            if ch == "/" and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == "*":
                self.advance()
                self.advance()
                while self.pos < len(self.text):
                    if self.peek() == "*" and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == "/":
                        self.advance()
                        self.advance()
                        break
                    self.advance()
                continue
            break

    def next_token(self) -> Token:
        self.skip_ws_and_comments()
        start_line, start_col = self.line, self.col
        ch = self.peek()
        if not ch:
            return Token("EOF", "", start_line, start_col)
        if ch in "{}[]:,":
            self.advance()
            return Token(ch, ch, start_line, start_col)
        if ch == '"':
            return self.read_string()
        if ch.isdigit() or (ch == "-" and self.pos + 1 < len(self.text) and self.text[self.pos + 1].isdigit()):
            return self.read_number()
        if re.match(r"[A-Za-z_]", ch):
            return self.read_bare()
        self.error(f"unexpected character {ch!r}")
        return Token("EOF", "", start_line, start_col)

    def read_string(self) -> Token:
        start_line, start_col = self.line, self.col
        start = self.pos
        self.advance()
        escaped = False
        while self.pos < len(self.text):
            ch = self.advance()
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                raw = self.text[start:self.pos]
                try:
                    return Token("STRING", json.loads(raw), start_line, start_col)
                except json.JSONDecodeError as exc:
                    raise AissError(f"{self.filename}:{start_line}:{start_col}: invalid string: {exc}") from exc
        self.error("unterminated string")
        return Token("STRING", "", start_line, start_col)

    def read_number(self) -> Token:
        start_line, start_col = self.line, self.col
        chars = []
        if self.peek() == "-":
            chars.append(self.advance())
        while self.peek().isdigit():
            chars.append(self.advance())
        if self.peek() == ".":
            chars.append(self.advance())
            while self.peek().isdigit():
                chars.append(self.advance())
        raw = "".join(chars)
        value: int | float = float(raw) if "." in raw else int(raw)
        return Token("NUMBER", value, start_line, start_col)

    def read_bare(self) -> Token:
        start_line, start_col = self.line, self.col
        chars = []
        while self.pos < len(self.text) and re.match(r"[A-Za-z0-9_.-]", self.peek()):
            chars.append(self.advance())
        return Token("BARE", "".join(chars), start_line, start_col)


class Parser:
    def __init__(self, text: str, filename: str = "<input>"):
        self.filename = filename
        self.text = text
        self.lexer = Lexer(text, filename)
        self.tokens: list[Token] = []
        self.pos = 0
        while True:
            token = self.lexer.next_token()
            self.tokens.append(token)
            if token.typ == "EOF":
                break

    def current(self) -> Token:
        return self.tokens[self.pos]

    def error(self, msg: str) -> None:
        tok = self.current()
        raise AissError(f"{self.filename}:{tok.line}:{tok.col}: {msg}")

    def eat(self, typ: str | None = None, value: Any | None = None) -> Token:
        tok = self.current()
        if typ is not None and tok.typ != typ:
            self.error(f"expected {typ}, got {tok.typ} ({tok.value!r})")
        if value is not None and tok.value != value:
            self.error(f"expected {value!r}, got {tok.value!r}")
        self.pos += 1
        return tok

    def parse(self) -> AissProgram:
        self.eat("BARE", "aiss")
        self.eat("BARE", "version")
        version = self.eat("STRING").value
        if version not in SUPPORTED_SCHEMA_VERSIONS:
            self.error(
                f"expected aiss version in {sorted(SUPPORTED_SCHEMA_VERSIONS)!r}, got {version!r}"
            )

        declarations: list[BaseDecl] = []
        while self.current().typ != "EOF":
            declarations.append(self.parse_declaration())

        return AissProgram(
            version=version,
            declarations=tuple(declarations),
            source_text=self.text,
            filename=self.filename,
        )

    def parse_declaration(self) -> BaseDecl:
        kind_token = self.eat("BARE")
        kind = kind_token.value
        if kind in FORBIDDEN_DERIVED_DECLARATIONS:
            raise AissError(
                f"{self.filename}:{kind_token.line}:{kind_token.col}: "
                f"forbidden derived-output primitive {kind!r}"
            )
        decl_id = self.eat("BARE").value
        fields = self.parse_block()
        cls = DECL_CLASSES.get(kind)
        if cls is None:
            return BaseDecl(decl_id, {"__unknown_kind__": kind, **fields}, kind_token.line)
        return cls(decl_id, fields, kind_token.line)

    def parse_block(self) -> dict[str, Any]:
        self.eat("{")
        fields: dict[str, Any] = {}
        while self.current().typ != "}":
            if self.current().typ == ",":
                self.eat(",")
                continue
            key_token = self.current()
            if key_token.typ not in {"BARE", "STRING"}:
                self.error(f"expected field key, got {key_token.typ} ({key_token.value!r})")
            key = self.eat().value
            self.eat(":")
            fields[str(key)] = self.parse_value()
            if self.current().typ == ",":
                self.eat(",")
        self.eat("}")
        return fields

    def parse_value(self) -> Any:
        tok = self.current()
        if tok.typ == "STRING":
            return self.eat("STRING").value
        if tok.typ == "NUMBER":
            return self.eat("NUMBER").value
        if tok.typ == "BARE":
            value = self.eat("BARE").value
            if value == "true":
                return True
            if value == "false":
                return False
            if value == "null":
                return None
            return value
        if tok.typ == "[":
            return self.parse_list()
        if tok.typ == "{":
            return self.parse_map()
        self.error(f"unexpected value token {tok.typ} ({tok.value!r})")
        return None

    def parse_list(self) -> list[Any]:
        self.eat("[")
        values: list[Any] = []
        while self.current().typ != "]":
            if self.current().typ == ",":
                self.eat(",")
                continue
            values.append(self.parse_value())
            if self.current().typ == ",":
                self.eat(",")
        self.eat("]")
        return values

    def parse_map(self) -> dict[str, Any]:
        self.eat("{")
        values: dict[str, Any] = {}
        while self.current().typ != "}":
            if self.current().typ == ",":
                self.eat(",")
                continue
            key_token = self.current()
            if key_token.typ not in {"BARE", "STRING"}:
                self.error(f"expected map key, got {key_token.typ} ({key_token.value!r})")
            key = str(self.eat().value)
            self.eat(":")
            values[key] = self.parse_value()
            if self.current().typ == ",":
                self.eat(",")
        self.eat("}")
        return values


def parse_source(text: str, filename: str = "<input>") -> AissProgram:
    return Parser(text, filename).parse()


def parse_file(path: str | Path) -> AissProgram:
    source_path = Path(path)
    text = source_path.read_text(encoding="utf-8")
    return parse_source(text, str(source_path))


def compile_file(path: str | Path, *, strict: bool = False) -> dict[str, Any]:
    source_path = Path(path)
    program = parse_file(source_path)
    return compile_program(program, strict=strict)


def compile_program(program: AissProgram, *, strict: bool = False) -> dict[str, Any]:
    validate_program_shape(program)

    papers = [d for d in program.declarations if d.kind == "paper"]
    if len(papers) != 1:
        raise AissError(f"{program.filename}: expected exactly one paper declaration, found {len(papers)}")

    source_hash = sha256_text(normalize_source_for_hash(program.source_text))
    paper_decl = papers[0]
    paper = record_from_decl(paper_decl)

    sources = [record_from_decl(d) for d in program.declarations if d.kind == "source"]
    spans = [record_from_decl(d) for d in program.declarations if d.kind == "span"]
    object_kinds = {
        "concept",
        "claim",
        "empirical",
        "observation",
        "artifact",
        "adapter",
        "attribute",
    }
    relation_kinds = {"relation", "coupling", "causal", "bridge", "edge"}
    objects = [object_record(d) for d in program.declarations if d.kind in object_kinds]
    relations = [relation_record(d) for d in program.declarations if d.kind in relation_kinds]
    models = [record_from_decl(d) for d in program.declarations if d.kind == "model"]
    checks = [record_from_decl(d) for d in program.declarations if d.kind == "check"]
    derives = [record_from_decl(d) for d in program.declarations if d.kind == "derive"]
    routes = [record_from_decl(d) for d in program.declarations if d.kind == "route"]
    mida = [record_from_decl(d) for d in program.declarations if d.kind == "mida"]
    decisions = [record_from_decl(d) for d in program.declarations if d.kind == "decision"]
    events = [record_from_decl(d) for d in program.declarations if d.kind == "event"]

    ast: dict[str, Any] = {
        "schema": UNIFIED_AST_SCHEMA,
        "compiler": {
            "name": "aiss",
            "version": COMPILER_VERSION,
        },
        "input": {
            "source_hash": source_hash,
            "strict": strict,
        },
        "paper": paper,
        "sources": sorted_records(sources),
        "spans": sorted_records(spans),
        "objects": sorted_records(objects),
        "relations": sorted_records(relations),
        "workflow": {
            "routes": sorted_records(routes),
            "mida": sorted_records(mida),
            "decisions": sorted_records(decisions),
            "events": sorted_records(events),
        },
        "models": sorted_records(models),
        "checks": sorted_records(checks),
        "derives": sorted_records(derives),
        "indices": {
            "theory": sorted_ids(
                [d.id for d in program.declarations if d.kind in THEORY_KINDS]
            ),
            "empirical": sorted_ids(
                [d.id for d in program.declarations if d.kind in {"empirical", "observation", "artifact"}]
            ),
            "coupling": sorted_ids([d.id for d in program.declarations if d.kind in {"coupling", "bridge"}]),
            "model": sorted_ids(
                [d.id for d in program.declarations if d.kind in {"attribute", "model", "check", "derive"}]
            ),
            "workflow": sorted_ids(
                [d.id for d in program.declarations if d.kind in WORKFLOW_KINDS]
            ),
        },
    }
    ast_hash = sha256_text(canonical_json(ast))
    ast["hashes"] = {
        "ast_hash": ast_hash,
    }
    return canonicalize(ast)


def validate_program_shape(program: AissProgram) -> None:
    seen: dict[str, int] = {}
    for decl in program.declarations:
        kind = decl.kind
        if isinstance(decl, BaseDecl) and type(decl) is BaseDecl:
            unknown = decl.fields.get("__unknown_kind__", kind)
            raise AissError(f"{program.filename}:{decl.line}: unknown declaration kind {unknown!r}")
        if kind not in ALL_DECLARATIONS:
            raise AissError(f"{program.filename}:{decl.line}: unknown declaration kind {kind!r}")
        if decl.id in seen:
            raise AissError(
                f"{program.filename}:{decl.line}: duplicate id {decl.id!r}; first declared at line {seen[decl.id]}"
            )
        seen[decl.id] = decl.line
        for field in REQUIRED_FIELDS[kind]:
            if field not in decl.fields:
                raise AissError(f"{program.filename}:{decl.line}: {kind} {decl.id!r} missing field {field!r}")


def record_from_decl(decl: BaseDecl) -> dict[str, Any]:
    record = {
        "id": decl.id,
        "decl_type": decl.kind,
    }
    record.update(canonicalize(decl.fields))
    return record


def object_record(decl: BaseDecl) -> dict[str, Any]:
    record = record_from_decl(decl)
    if decl.kind in THEORY_KINDS:
        record["category"] = "theory"
    elif decl.kind in EMPIRICAL_KINDS:
        record["category"] = "empirical"
    elif decl.kind in MODEL_KINDS:
        record["category"] = "model"
    elif decl.kind in WORKFLOW_KINDS:
        record["category"] = "workflow"
    else:
        record["category"] = "tooling"
    return record


def relation_record(decl: BaseDecl) -> dict[str, Any]:
    record = record_from_decl(decl)
    if decl.kind in {"coupling", "bridge"}:
        record["category"] = "coupling"
    elif decl.kind in {"causal", "edge"}:
        record["category"] = "model"
    else:
        record["category"] = "theory"
    return record


def lint_ast(ast: dict[str, Any], *, strict: bool | None = None) -> dict[str, Any]:
    strict_mode = bool(ast.get("input", {}).get("strict")) if strict is None else strict
    diagnostics: list[dict[str, Any]] = []

    records = all_records(ast)
    id_kind = {r["id"]: record_decl_type(r) for r in records if "id" in r}
    id_record = {r["id"]: r for r in records if "id" in r}

    def diag(code: str, severity: str, primary_id: str, message: str, related_ids: list[str] | None = None) -> None:
        diagnostics.append({
            "code": code,
            "severity": severity,
            "primary_id": primary_id,
            "message": message,
            "related_ids": sorted_ids(related_ids or []),
        })

    for record in records:
        kind = record_decl_type(record)
        rid = record.get("id", "<unknown>")
        for field, expected in REFERENCE_FIELDS.get(kind, {}).items():
            if field not in record:
                continue
            for ref in coerce_list(record[field]):
                if not isinstance(ref, str):
                    continue
                if ref not in id_kind:
                    diag("AISS-REF-001", "error", rid, f"{kind} references missing id {ref!r} in field {field!r}")
                    continue
                if not reference_matches(expected, id_kind[ref]):
                    code = "AISS-COUP-001" if kind == "coupling" and field == "theory" else "AISS-COUP-002"
                    if kind != "coupling":
                        code = "AISS-REF-002"
                    diag(
                        code,
                        "error",
                        rid,
                        f"{kind} field {field!r} expects {expected}, got {id_kind[ref]} {ref!r}",
                        [ref],
                    )

    for record in records:
        kind = record_decl_type(record)
        rid = record.get("id", "<unknown>")
        if kind in {"concept", "claim", "relation", "empirical", "observation", "coupling", "route", "mida", "decision"}:
            if not record.get("spans"):
                diag("AISS-PROV-001", "error" if strict_mode else "warning", rid, f"{kind} lacks source spans")

    source_ids = {s["id"] for s in ast.get("sources", [])}
    for span in ast.get("spans", []):
        source_id = span.get("source")
        if source_id and source_id not in source_ids:
            diag("AISS-REF-001", "error", span["id"], f"span references missing source {source_id!r}")
        if strict_mode and not span.get("quote_hash"):
            diag("AISS-PROV-003", "warning", span["id"], "span lacks quote_hash in strict mode")

    for source in ast.get("sources", []):
        uri = str(source.get("uri", ""))
        if uri.startswith("/"):
            diag("AISS-FORMAL-002", "warning", source["id"], "source uri is an absolute local path")
        if strict_mode and not source.get("checksum"):
            diag("AISS-PROV-004", "warning", source["id"], "source lacks checksum in strict mode")

    for artifact in [r for r in records if record_decl_type(r) == "artifact"]:
        uri = str(artifact.get("uri", ""))
        if uri.startswith("/"):
            diag("AISS-FORMAL-002", "warning", artifact["id"], "artifact uri is an absolute local path")
        if strict_mode and not artifact.get("checksum"):
            diag("AISS-EMP-002", "error", artifact["id"], "runnable artifact lacks checksum in strict mode")

    concepts_by_term: dict[str, list[dict[str, Any]]] = {}
    for concept in [r for r in records if record_decl_type(r) == "concept"]:
        term = str(concept.get("term", "")).casefold()
        if term:
            concepts_by_term.setdefault(term, []).append(concept)
    for concepts in concepts_by_term.values():
        if len(concepts) > 1:
            ids = [c["id"] for c in concepts]
            diag("AISS-CONCEPT-001", "warning", ids[0], f"same concept term declared multiple times: {ids}", ids[1:])
            definitions = {c.get("definition") for c in concepts if c.get("definition")}
            if len(definitions) > 1:
                diag("AISS-CONCEPT-002", "warning", ids[0], f"same concept term has conflicting definitions: {ids}", ids[1:])

    for claim in [r for r in records if record_decl_type(r) == "claim"]:
        for concept_id in coerce_list(claim.get("concepts", [])):
            if concept_id in id_record:
                continue
            diag("AISS-CLAIM-001", "warning", claim["id"], f"claim references ungrounded concept {concept_id!r}")

    structured_claims: list[dict[str, Any]] = []
    for claim in [r for r in records if record_decl_type(r) == "claim"]:
        present_fields = [field for field in STRUCTURED_CLAIM_FIELDS if field in claim]
        if present_fields and len(present_fields) != len(STRUCTURED_CLAIM_FIELDS):
            missing = [field for field in STRUCTURED_CLAIM_FIELDS if field not in claim]
            diag(
                "AISS-CLAIM-002",
                "warning",
                claim["id"],
                f"structured claim is incomplete; missing fields: {', '.join(missing)}",
            )
            continue
        if len(present_fields) == len(STRUCTURED_CLAIM_FIELDS):
            polarity = str(claim.get("polarity", "")).casefold()
            if polarity not in {"positive", "negative", "null", "present", "absent"}:
                diag(
                    "AISS-CLAIM-003",
                    "warning",
                    claim["id"],
                    f"unknown structured claim polarity {claim.get('polarity')!r}",
                )
                continue
            modality = str(claim.get("modality", "")).casefold()
            if modality in ASSERTED_MODALITIES:
                structured_claims.append(claim)

    claims_by_signature: dict[tuple[str, str, str, tuple[str, ...]], list[dict[str, Any]]] = {}
    for claim in structured_claims:
        signature = structured_claim_signature(claim)
        claims_by_signature.setdefault(signature, []).append(claim)

    for grouped_claims in claims_by_signature.values():
        by_polarity: dict[str, list[dict[str, Any]]] = {}
        for claim in grouped_claims:
            by_polarity.setdefault(str(claim.get("polarity", "")).casefold(), []).append(claim)
        for polarity_a in sorted(by_polarity):
            for polarity_b in sorted(by_polarity):
                if polarity_a >= polarity_b:
                    continue
                if frozenset((polarity_a, polarity_b)) not in CONTRADICTORY_POLARITY_PAIRS:
                    continue
                primary = sorted(by_polarity[polarity_a] + by_polarity[polarity_b], key=lambda item: item["id"])[0]
                related = [
                    claim["id"]
                    for claim in sorted(by_polarity[polarity_a] + by_polarity[polarity_b], key=lambda item: item["id"])
                    if claim["id"] != primary["id"]
                ]
                subject, predicate, obj, scope = structured_claim_signature(primary)
                scope_label = ",".join(scope) if scope else "<global>"
                diag(
                    "AISS-CLAIM-010",
                    "error",
                    primary["id"],
                    (
                        "contradictory structured claims for "
                        f"({subject}, {predicate}, {obj}) in scope {scope_label}: "
                        f"{polarity_a} vs {polarity_b}"
                    ),
                    related,
                )

    for empirical in [r for r in records if record_decl_type(r) == "empirical"]:
        linked = any(
            empirical["id"] in coerce_list(r.get("about", [])) or empirical["id"] in coerce_list(r.get("empirical", []))
            for r in records
        )
        if not linked and not empirical.get("artifacts"):
            diag("AISS-EMP-001", "warning", empirical["id"], "empirical object has no artifact or observation linked to it")

    routes = [r for r in records if record_decl_type(r) == "route"]
    for route in routes:
        status = str(route.get("status", ""))
        if status not in ROUTE_STATUSES:
            diag("AISS-WF-001", "warning", route["id"], f"route status should be one of {sorted(ROUTE_STATUSES)}, got {status!r}")
        if status == "selected" and str(route.get("next_skill_route", "")).strip() in {"", "none"}:
            diag("AISS-WF-002", "warning", route["id"], "selected route lacks a downstream automation route")

    mida_by_route: dict[str, set[str]] = {}
    for row in [r for r in records if record_decl_type(r) == "mida"]:
        route_id = str(row.get("route", ""))
        component = str(row.get("component", ""))
        if component not in MIDA_COMPONENTS:
            diag("AISS-WF-003", "warning", row["id"], f"mida component should be one of {sorted(MIDA_COMPONENTS)}, got {component!r}")
        if route_id:
            mida_by_route.setdefault(route_id, set()).add(component)

    for route in routes:
        if route.get("status") != "selected":
            continue
        components = mida_by_route.get(route["id"], set())
        missing = sorted(MIDA_COMPONENTS - components)
        if missing:
            diag(
                "AISS-WF-004",
                "warning",
                route["id"],
                f"selected route lacks MIDA components: {', '.join(missing)}",
            )

    for event in [r for r in records if record_decl_type(r) == "event"]:
        event_type = str(event.get("type", "")).strip()
        if event_type not in MACHINE_EVENT_TYPES:
            diag("AISS-WF-010", "warning", event["id"], f"unknown state-machine event type {event_type!r}")
        event_at = str(event.get("at", "")).strip()
        if event_at and parse_iso_datetime(event_at) is None:
            diag("AISS-WF-011", "warning", event["id"], f"event has non-ISO timestamp {event_at!r}")
        next_route = str(event.get("next_skill_route", "")).strip()
        if next_route and next_route not in ALLOWED_NEXT_SKILL_ROUTES:
            diag("AISS-WF-012", "error", event["id"], f"event next_skill_route is not in the research-factory route table: {next_route!r}")
        skill = str(event.get("skill", "")).strip()
        if skill and skill not in ALLOWED_NEXT_SKILL_ROUTES:
            diag("AISS-WF-013", "warning", event["id"], f"event skill is not in the research-factory route table: {skill!r}")

    diagnostics = sorted(
        diagnostics,
        key=lambda d: (severity_rank(d["severity"]), d["code"], d["primary_id"], d["message"]),
    )
    return {
        "schema": "aiss.lint_report.v0.4",
        "ast_hash": ast_hash(ast),
        "diagnostics": diagnostics,
        "ok": not any(d["severity"] == "error" for d in diagnostics),
    }


def compute_model_diagnostics(ast: dict[str, Any]) -> dict[str, Any]:
    records = all_records(ast)
    causals = [r for r in records if record_decl_type(r) == "causal"]
    bridges = [r for r in records if record_decl_type(r) == "bridge"]
    models = [r for r in records if record_decl_type(r) == "model"]
    bridges_by_implication = {
        str(bridge.get("implication")): bridge
        for bridge in bridges
        if bridge.get("implication")
    }

    diagnosands: list[dict[str, Any]] = []
    for causal in causals:
        causal_id = causal["id"]
        bridge = bridges_by_implication.get(causal_id)
        support_text = " ".join(
            str(bridge.get(field, ""))
            for field in ("method", "validity", "estimand", "note")
            if bridge and bridge.get(field)
        )
        evidence_type = detect_evidence_type(support_text)
        evidence_score = {
            "experiment": 1.0,
            "quasi_experiment": 0.8,
            "observational": 0.4,
            "qualitative": 0.3,
            "unspecified": 0.1,
            "none": 0.0,
        }[evidence_type]
        has_mechanism = bool(causal.get("mechanism") and causal.get("mechanism") != "none")
        has_condition = bool(causal.get("condition") and causal.get("condition") != "none")
        has_estimand = bool(bridge and bridge.get("estimand") and bridge.get("estimand") != "none")
        has_bridge = bridge is not None
        score = evidence_score
        if has_mechanism:
            score += 0.10
        if has_condition:
            score += 0.05
        if has_estimand:
            score += 0.15
        if has_bridge:
            score += 0.10
        score = min(score, 1.0)

        declared = str(bridge.get("commensurability", "unchecked")) if bridge else "unchecked"
        gaps: list[str] = []
        if evidence_type == "none":
            gaps.append("no_evidence")
        if not has_mechanism:
            gaps.append("no_mechanism")
        if not has_bridge:
            gaps.append("no_bridge")
        if not has_estimand:
            gaps.append("no_estimand")
        if declared == "unchecked":
            gaps.append("declared_unchecked")
        elif declared == "weak" and evidence_score >= 0.8:
            gaps.append("declared_weak_but_evidence_is_strong")
        elif declared == "strong" and evidence_score < 0.4:
            gaps.append("declared_strong_but_evidence_is_weak")

        diagnosands.append({
            "causal_id": causal_id,
            "declared": declared,
            "evidence_type": evidence_type,
            "computed_score": round(score, 2),
            "gaps": sorted(gaps),
        })

    profiles: list[dict[str, Any]] = []
    for model in models:
        causal_ids = [str(item) for item in coerce_list(model.get("causal", []))]
        bridge_ids = [str(item) for item in coerce_list(model.get("bridges", []))]
        model_diags = [diag for diag in diagnosands if diag["causal_id"] in causal_ids]
        bridged = [diag for diag in model_diags if "no_bridge" not in diag["gaps"]]
        coverage = len(bridged) / max(len(causal_ids), 1)
        avg_score = sum(float(diag["computed_score"]) for diag in model_diags) / max(len(model_diags), 1)
        has_strong_bridge = any(
            str(bridge.get("id")) in bridge_ids and bridge.get("commensurability") == "strong"
            for bridge in bridges
        )
        if not causal_ids:
            contribution = "facts_only"
        elif has_strong_bridge:
            contribution = "full_study_with_strong_bridge"
        elif coverage > 0:
            contribution = "explanation_with_evidence"
        else:
            contribution = "explanation_without_evidence"
        gaps = []
        if causal_ids and coverage == 0:
            gaps.append(f"{len(causal_ids)} causal edges, 0 bridged to empirics")
        elif causal_ids and coverage < 1.0:
            gaps.append(f"{len(causal_ids) - len(bridged)}/{len(causal_ids)} edges lack bridges")
        unchecked = sum(1 for diag in model_diags if "declared_unchecked" in diag["gaps"])
        if unchecked:
            gaps.append(f"{unchecked} edges declared 'unchecked'")
        profiles.append({
            "model_id": model["id"],
            "contribution_type": contribution,
            "avg_score": round(avg_score, 2),
            "coverage": round(coverage, 2),
            "gaps": sorted(gaps),
        })

    return {
        "diagnosands": sorted(diagnosands, key=lambda item: item["causal_id"]),
        "ibe_profiles": sorted(profiles, key=lambda item: item["model_id"]),
    }


def detect_evidence_type(text: str) -> str:
    if not text or text == "none":
        return "none"
    text_lower = text.lower()
    patterns = [
        ("experiment", (r"experiment", r"randomi[sz]ed", r"random assignment", r"rct", r"field experiment")),
        ("quasi_experiment", (r"difference.in.difference", r"did", r"regression discontinuity", r"rdd", r"instrumental variable", r"\biv\b", r"natural experiment", r"synthetic control", r"fixed effects", r"panel")),
        ("observational", (r"regression", r"ols", r"logit", r"probit", r"correlation", r"association", r"survey")),
        ("qualitative", (r"ethnograph", r"fieldwork", r"case study", r"process tracing", r"interview")),
    ]
    for label, label_patterns in patterns:
        if any(re.search(pattern, text_lower) for pattern in label_patterns):
            return label
    return "unspecified"


def compute_workflow_diagnostics(ast: dict[str, Any]) -> dict[str, Any]:
    workflow = ast.get("workflow", {})
    if not isinstance(workflow, dict):
        workflow = {}
    routes = workflow.get("routes", []) if isinstance(workflow.get("routes", []), list) else []
    mida = workflow.get("mida", []) if isinstance(workflow.get("mida", []), list) else []
    decisions = workflow.get("decisions", []) if isinstance(workflow.get("decisions", []), list) else []

    mida_by_route: dict[str, set[str]] = {}
    for row in mida:
        route_id = str(row.get("route", ""))
        component = str(row.get("component", ""))
        if route_id:
            mida_by_route.setdefault(route_id, set()).add(component)

    route_profiles: list[dict[str, Any]] = []
    for route in routes:
        route_id = str(route.get("id", ""))
        components = mida_by_route.get(route_id, set())
        missing = sorted(MIDA_COMPONENTS - components)
        status = str(route.get("status", ""))
        if status == "selected" and not missing:
            readiness = "mida_declared"
        elif status == "selected":
            readiness = "mida_incomplete"
        elif status == "candidate":
            readiness = "route_candidate"
        else:
            readiness = status or "unknown"
        route_profiles.append({
            "route_id": route_id,
            "status": status,
            "study_type": route.get("study_type"),
            "next_skill_route": route.get("next_skill_route"),
            "mida_components": sorted(components),
            "missing_mida_components": missing,
            "readiness": readiness,
        })

    decision_counts: dict[str, int] = {}
    for decision in decisions:
        status = str(decision.get("status", ""))
        decision_counts[status] = decision_counts.get(status, 0) + 1

    selected_routes = sorted(
        str(route.get("id"))
        for route in routes
        if route.get("status") == "selected" and route.get("id")
    )
    return {
        "selected_routes": selected_routes,
        "route_profiles": sorted(route_profiles, key=lambda item: item["route_id"]),
        "decision_counts": canonicalize(decision_counts),
        "automation_decisions_open": sum(
            1
            for decision in decisions
            if str(decision.get("status", "")).casefold() not in {"auto_resolved", "resolved", "rejected"}
        ),
    }


def compute_machine_state(
    ast: dict[str, Any],
    *,
    now: str | None = None,
    heartbeat_stale_seconds: int = DEFAULT_HEARTBEAT_STALE_SECONDS,
) -> dict[str, Any]:
    """Project a deterministic research-factory state machine from a compiled AST."""
    now_dt = parse_iso_datetime(now) if now else None
    workflow = ast.get("workflow", {}) if isinstance(ast.get("workflow", {}), dict) else {}
    routes = workflow.get("routes", []) if isinstance(workflow.get("routes", []), list) else []
    mida = workflow.get("mida", []) if isinstance(workflow.get("mida", []), list) else []
    decisions = workflow.get("decisions", []) if isinstance(workflow.get("decisions", []), list) else []
    events = workflow.get("events", []) if isinstance(workflow.get("events", []), list) else []
    workflow_diagnostics = compute_workflow_diagnostics(ast)

    selected_routes = [route for route in routes if route.get("status") == "selected"]
    selected_route = selected_routes[0] if len(selected_routes) == 1 else None
    selected_route_id = str(selected_route.get("id", "")) if selected_route else None
    route_profile = next(
        (
            profile
            for profile in workflow_diagnostics.get("route_profiles", [])
            if selected_route_id and profile.get("route_id") == selected_route_id
        ),
        None,
    )

    initial_next_route = "research-starter"
    initial_phase = "route_selection_required"
    initial_status = "active"
    blockers: list[dict[str, Any]] = []
    if not selected_route:
        initial_status = "blocked"
        if selected_routes:
            blockers.append({
                "code": "multiple_selected_routes",
                "message": "Exactly one selected route is required before the state machine can dispatch skills.",
            })
        else:
            blockers.append({
                "code": "missing_selected_route",
                "message": "No selected route is available; route through research-starter or study-design-builder.",
            })
    else:
        initial_next_route = str(selected_route.get("next_skill_route", "none") or "none")
        initial_phase = str((route_profile or {}).get("readiness") or "route_selected")

    state: dict[str, Any] = {
        "schema": "aiss.machine_state.v0.4",
        "ast_hash": ast_hash(ast),
        "status": initial_status,
        "phase": initial_phase,
        "terminal": False,
        "selected_route": selected_route_id,
        "current_skill": None,
        "next_skill_route": initial_next_route,
        "readiness": (route_profile or {}).get("readiness"),
        "route_profile": route_profile,
        "completed_skills": [],
        "attempts": {},
        "blockers": blockers,
        "open_repair_routes": [],
        "open_decisions": workflow_diagnostics.get("automation_decisions_open", 0),
        "event_history_count": len(events),
        "skipped_event_count": 0,
        "last_event": None,
        "watchdog": {
            "status": "not_seen",
            "last_seen": None,
            "phase": None,
            "run_dir": None,
            "stale_seconds": heartbeat_stale_seconds,
            "age_seconds": None,
            "owner": "goal-cli",
        },
    }

    if selected_route_id:
        repair_rows = initial_repair_rows(selected_route_id, mida, decisions)
        if repair_rows:
            state["open_repair_routes"] = repair_rows
            first_route = repair_rows[0].get("next_skill_route")
            if first_route:
                state["next_skill_route"] = first_route
            state["phase"] = "repair_required"

    for event in sorted_machine_events(events):
        route_ref = str(event.get("route", "") or "")
        if selected_route_id and route_ref and route_ref != selected_route_id:
            state["skipped_event_count"] = int(state.get("skipped_event_count", 0)) + 1
            continue
        apply_machine_event(state, event)

    finalize_watchdog_state(state, now_dt=now_dt, heartbeat_stale_seconds=heartbeat_stale_seconds)
    state["enabled_events"] = enabled_machine_events(state)
    state["actions"] = machine_actions(state)
    return canonicalize(state)


def initial_repair_rows(
    selected_route_id: str,
    mida: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in [*mida, *decisions]:
        if str(record.get("route", "")) != selected_route_id:
            continue
        status = str(record.get("status", "")).strip()
        if status not in REPAIR_STATUS_DEFAULT_ROUTE:
            continue
        next_route = str(record.get("next_skill_route", "") or "").strip() or REPAIR_STATUS_DEFAULT_ROUTE[status]
        rows.append({
            "id": record.get("id"),
            "kind": record_decl_type(record),
            "component": record.get("component"),
            "status": status,
            "next_skill_route": next_route,
        })
    return sorted(rows, key=lambda row: (str(row.get("kind")), str(row.get("id"))))


def sorted_machine_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(events, key=machine_event_sort_key)


def machine_event_sort_key(event: dict[str, Any]) -> tuple[str, int, str]:
    at = str(event.get("at", "") or "")
    parsed = parse_iso_datetime(at)
    normalized_at = format_iso_datetime(parsed) if parsed else at
    sequence = event.get("sequence", 0)
    sequence_int = sequence if isinstance(sequence, int) else 0
    return (normalized_at, sequence_int, str(event.get("id", "")))


def apply_machine_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    event_type = str(event.get("type", ""))
    skill = str(event.get("skill", "") or state.get("next_skill_route") or "")
    next_route = str(event.get("next_skill_route", "") or "")
    state["last_event"] = compact_event(event)

    if event_type == "heartbeat_seen":
        update_watchdog_from_event(state, event)
        phase = str(event.get("phase", "") or "")
        if phase.endswith("_running") and skill:
            state["status"] = "active"
            state["phase"] = "skill_running"
            state["current_skill"] = skill
        return

    if event_type == "heartbeat_interrupted":
        update_watchdog_from_event(state, {**event, "phase": "interrupted"})
        state["status"] = "active"
        state["phase"] = "watchdog_interrupted"
        state["current_skill"] = None
        add_blocker(state, "heartbeat_interrupted", event.get("message") or "goal-cli heartbeat was interrupted")
        return

    if event_type == "skill_started":
        state["status"] = "active"
        state["phase"] = "skill_running"
        state["current_skill"] = skill or None
        if skill:
            attempts = dict(state.get("attempts", {}))
            attempts[skill] = int(attempts.get(skill, 0)) + 1
            state["attempts"] = attempts
        return

    if event_type == "skill_completed":
        completed = list(state.get("completed_skills", []))
        if skill and skill not in completed:
            completed.append(skill)
        state["completed_skills"] = completed
        state["current_skill"] = None
        if next_route and next_route != "none":
            state["status"] = "active"
            state["phase"] = "ready_for_skill"
            state["next_skill_route"] = next_route
        elif next_route == "none" or str(event.get("status", "")).strip() in {"completed", "done"}:
            state["status"] = "completed"
            state["phase"] = "completed"
            state["next_skill_route"] = "none"
            state["terminal"] = True
        else:
            state["status"] = "blocked"
            state["phase"] = "next_route_required"
            state["next_skill_route"] = "none"
            add_blocker(state, "missing_next_skill_route", "skill_completed event must declare next_skill_route or status completed")
        return

    if event_type in {"skill_failed", "check_failed", "repair_required"}:
        state["status"] = "active"
        state["phase"] = "repair_required"
        state["current_skill"] = None
        repair_route = next_route or repair_route_for_event(event)
        state["next_skill_route"] = repair_route
        repair_rows = list(state.get("open_repair_routes", []))
        repair_rows.append({
            "id": event.get("id"),
            "kind": "event",
            "status": str(event.get("status", "") or event_type),
            "next_skill_route": repair_route,
            "message": event.get("message"),
        })
        state["open_repair_routes"] = repair_rows
        add_blocker(state, event_type, event.get("message") or f"{event_type} requires repair")
        return

    if event_type == "check_passed":
        state["phase"] = "ready_for_skill" if state.get("next_skill_route") not in {"", "none"} else state.get("phase")
        return

    if event_type == "goal_blocked":
        state["status"] = "blocked"
        state["phase"] = "blocked"
        state["current_skill"] = None
        state["next_skill_route"] = "none"
        state["terminal"] = True
        add_blocker(state, "goal_blocked", event.get("message") or "goal marked blocked")
        return

    if event_type == "goal_completed":
        state["status"] = "completed"
        state["phase"] = "completed"
        state["current_skill"] = None
        state["next_skill_route"] = "none"
        state["terminal"] = True


def update_watchdog_from_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    watchdog = dict(state.get("watchdog", {}))
    watchdog["last_seen"] = event.get("last_seen") or event.get("at")
    watchdog["phase"] = event.get("phase")
    watchdog["run_dir"] = event.get("run_dir")
    watchdog["status"] = "observed"
    watchdog["owner"] = event.get("source") or "goal-cli"
    state["watchdog"] = watchdog


def finalize_watchdog_state(
    state: dict[str, Any],
    *,
    now_dt: datetime | None,
    heartbeat_stale_seconds: int,
) -> None:
    watchdog = dict(state.get("watchdog", {}))
    last_seen = str(watchdog.get("last_seen") or "")
    last_seen_dt = parse_iso_datetime(last_seen) if last_seen else None
    watchdog["stale_seconds"] = heartbeat_stale_seconds
    if not last_seen_dt:
        if watchdog.get("status") != "not_seen":
            watchdog["status"] = "freshness_unknown"
        watchdog["age_seconds"] = None
        state["watchdog"] = watchdog
        return
    if str(watchdog.get("phase")) == "interrupted":
        watchdog["status"] = "interrupted"
        watchdog["age_seconds"] = None
        state["watchdog"] = watchdog
        return
    if now_dt is None:
        watchdog["status"] = "observed"
        watchdog["age_seconds"] = None
        state["watchdog"] = watchdog
        return
    age_seconds = max(0, int((now_dt - last_seen_dt).total_seconds()))
    watchdog["age_seconds"] = age_seconds
    watchdog["status"] = "stale" if age_seconds > heartbeat_stale_seconds else "fresh"
    state["watchdog"] = watchdog


def add_blocker(state: dict[str, Any], code: str, message: Any) -> None:
    blockers = list(state.get("blockers", []))
    blockers.append({
        "code": code,
        "message": str(message or code),
    })
    state["blockers"] = blockers


def repair_route_for_event(event: dict[str, Any]) -> str:
    status = str(event.get("status", "") or "")
    if status in REPAIR_STATUS_DEFAULT_ROUTE:
        return REPAIR_STATUS_DEFAULT_ROUTE[status]
    event_type = str(event.get("type", "") or "")
    if event_type == "check_failed":
        return "methods-reviewer"
    if event_type == "skill_failed":
        return "methods-reviewer"
    return "methods-reviewer"


def compact_event(event: dict[str, Any]) -> dict[str, Any]:
    keys = ("id", "type", "at", "route", "skill", "status", "phase", "next_skill_route", "message")
    return {key: event[key] for key in keys if key in event}


def enabled_machine_events(state: dict[str, Any]) -> list[str]:
    if state.get("terminal"):
        return []
    phase = str(state.get("phase") or "")
    if phase == "skill_running":
        return ["heartbeat_seen", "heartbeat_interrupted", "skill_completed", "skill_failed"]
    if phase in {"blocked", "next_route_required"}:
        return ["repair_required", "goal_blocked"]
    return ["heartbeat_seen", "skill_started", "check_failed", "repair_required", "goal_blocked", "goal_completed"]


def machine_actions(state: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    watchdog_status = str(state.get("watchdog", {}).get("status") or "")
    if watchdog_status in {"stale", "interrupted"} and not state.get("terminal"):
        actions.append({
            "type": "watchdog_recover",
            "owner": "goal-cli",
            "reason": f"heartbeat is {watchdog_status}",
        })
    next_route = str(state.get("next_skill_route") or "")
    if (
        state.get("status") == "active"
        and not state.get("current_skill")
        and next_route
        and next_route != "none"
    ):
        actions.append({
            "type": "dispatch_skill",
            "skill": next_route,
            "route": state.get("selected_route"),
        })
    if state.get("phase") == "next_route_required":
        actions.append({
            "type": "declare_decision",
            "owner": "research-factory",
            "reason": "last completion event did not declare a downstream skill",
        })
    return actions


def transition_machine(
    ast: dict[str, Any],
    event: dict[str, Any],
    *,
    now: str | None = None,
    heartbeat_stale_seconds: int = DEFAULT_HEARTBEAT_STALE_SECONDS,
) -> dict[str, Any]:
    before = compute_machine_state(ast, now=now, heartbeat_stale_seconds=heartbeat_stale_seconds)
    normalized_event = normalize_machine_event(event, before=before, now=now)
    virtual_ast = ast_with_event(ast, normalized_event)
    after = compute_machine_state(virtual_ast, now=now, heartbeat_stale_seconds=heartbeat_stale_seconds)
    return canonicalize({
        "schema": "aiss.transition_report.v0.4",
        "ast_hash": ast_hash(ast),
        "event": normalized_event,
        "before": before,
        "after": after,
        "actions": after.get("actions", []),
    })


def normalize_machine_event(
    event: dict[str, Any],
    *,
    before: dict[str, Any],
    now: str | None = None,
) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise AissError("state-machine event must be a JSON object")
    normalized = dict(event)
    event_type = str(normalized.get("type", "")).strip()
    if not event_type:
        raise AissError("state-machine event missing required field 'type'")
    if event_type not in MACHINE_EVENT_TYPES:
        raise AissError(f"unknown state-machine event type {event_type!r}")
    event_at = str(normalized.get("at", "") or now or "").strip()
    if not event_at:
        raise AissError("state-machine event missing required field 'at'; pass it in --event or --now")
    event_dt = parse_iso_datetime(event_at)
    if event_dt is None:
        raise AissError(f"state-machine event has invalid ISO timestamp {event_at!r}")
    normalized["type"] = event_type
    normalized["at"] = format_iso_datetime(event_dt)
    if "route" not in normalized and before.get("selected_route"):
        normalized["route"] = before["selected_route"]
    if "skill" not in normalized and event_type.startswith("skill_"):
        next_route = str(before.get("next_skill_route") or "")
        if next_route and next_route != "none":
            normalized["skill"] = next_route
    if "id" not in normalized or not str(normalized.get("id", "")).strip():
        normalized["id"] = make_event_id(normalized, before=before)
    next_route = str(normalized.get("next_skill_route", "") or "")
    if next_route and next_route not in ALLOWED_NEXT_SKILL_ROUTES:
        raise AissError(f"event next_skill_route {next_route!r} is not in the research-factory route table")
    return canonicalize(normalized)


def make_event_id(event: dict[str, Any], *, before: dict[str, Any]) -> str:
    namespace_source = str(before.get("selected_route") or "aiss.machine")
    namespace = namespace_source.split(".", 1)[0] if "." in namespace_source else "aiss"
    timestamp = re.sub(r"[^0-9A-Za-z]+", "_", str(event.get("at", ""))).strip("_").lower()
    event_type = re.sub(r"[^0-9A-Za-z_]+", "_", str(event.get("type", "event"))).strip("_").lower()
    digest = hashlib.sha256(canonical_json({k: v for k, v in event.items() if k != "id"}).encode("utf-8")).hexdigest()[:10]
    return f"{namespace}.event_{timestamp}_{event_type}_{digest}"


def ast_with_event(ast: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    virtual_ast = json.loads(json.dumps(ast, ensure_ascii=False))
    workflow = virtual_ast.setdefault("workflow", {})
    if not isinstance(workflow, dict):
        workflow = {}
        virtual_ast["workflow"] = workflow
    events = workflow.setdefault("events", [])
    if not isinstance(events, list):
        events = []
        workflow["events"] = events
    events.append(event)
    virtual_ast.pop("hashes", None)
    return canonicalize(virtual_ast)


def load_event_payload(value: str) -> dict[str, Any]:
    stripped = value.strip()
    if stripped.startswith("{"):
        text = stripped
    else:
        candidate = Path(value)
        text = candidate.read_text(encoding="utf-8") if candidate.exists() else value
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AissError(f"could not parse event JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise AissError("event JSON must be an object")
    return payload


def append_event_to_source(path: Path, event: dict[str, Any], ast: dict[str, Any]) -> None:
    event_id = str(event.get("id", "") or "")
    if not event_id:
        raise AissError("cannot append event without id")
    existing_ids = {str(record.get("id")) for record in all_records(ast) if record.get("id")}
    if event_id in existing_ids:
        raise AissError(f"event id already exists in {path}: {event_id}")
    text = path.read_text(encoding="utf-8")
    path.write_text(text.rstrip() + "\n\n" + format_event_decl(event), encoding="utf-8")


def format_event_decl(event: dict[str, Any]) -> str:
    event_id = str(event["id"])
    ordered_keys = [
        "type",
        "at",
        "route",
        "skill",
        "status",
        "phase",
        "next_skill_route",
        "source",
        "message",
        "last_seen",
        "run_dir",
        "iteration",
        "mida",
        "decision",
        "artifact",
        "check",
        "model",
    ]
    keys = [key for key in ordered_keys if key in event]
    keys.extend(sorted(key for key in event if key not in set(keys) | {"id"}))
    lines = [f"event {event_id} {{"]
    for key in keys:
        lines.append(f"  {key}: {format_aiss_value(event[key])}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def format_aiss_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, dict)):
        return json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True)
    return json.dumps(str(value), ensure_ascii=False)


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_iso_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def run_ast(ast: dict[str, Any], *, adapter_lock_path: str | Path | None = None) -> dict[str, Any]:
    if adapter_lock_path:
        lock_bytes = Path(adapter_lock_path).read_bytes()
        adapter_lock_hash = sha256_bytes(lock_bytes)
    else:
        adapter_lock_hash = sha256_bytes(b"")

    declared_adapters = [r for r in ast.get("objects", []) if record_decl_type(r) == "adapter"]

    def adapter_for_coupling(coupling: dict[str, Any]) -> dict[str, Any] | None:
        coupling_type = str(coupling.get("type", ""))
        coupling_targets = {coupling["id"], record_decl_type(coupling), coupling_type}
        for adapter in sorted(declared_adapters, key=lambda item: item["id"]):
            consumes = {str(item) for item in coerce_list(adapter.get("consumes"))}
            produces = {str(item) for item in coerce_list(adapter.get("produces"))}
            can_consume = bool(consumes & coupling_targets)
            can_produce = bool(produces & {"assessment", "coupling_assessment", f"{coupling_type}_assessment"})
            if can_consume and can_produce:
                return adapter
        return None

    units = [
        {
            "adapter": adapter["id"],
            "version": adapter.get("version"),
            "status": "registered",
            "inputs": [],
            "outputs": [],
        }
        for adapter in declared_adapters
    ]

    coupling_assessments = []
    for coupling in ast.get("relations", []):
        if record_decl_type(coupling) != "coupling":
            continue
        adapter = adapter_for_coupling(coupling)
        if adapter:
            coupling_assessments.append({
                "coupling_id": coupling["id"],
                "status": "assessable_via_adapter",
                "rule": adapter["id"],
                "basis": sorted_ids(coerce_list(coupling.get("spans", []))),
                "message": "Declared adapter covers this coupling type.",
            })
        else:
            coupling_assessments.append({
                "coupling_id": coupling["id"],
                "status": "not_assessable",
                "rule": None,
                "basis": [],
                "message": "No deterministic adapter is available for this coupling type.",
            })

    return canonicalize({
        "schema": "aiss.run_report.v0.4",
        "ast_hash": ast_hash(ast),
        "adapter_lock_hash": adapter_lock_hash,
        "units": sorted(units, key=lambda unit: unit["adapter"]),
        "coupling_assessments": sorted(coupling_assessments, key=lambda item: item["coupling_id"]),
        "workflow_diagnostics": compute_workflow_diagnostics(ast),
        "machine_state": compute_machine_state(ast),
        "model_diagnostics": compute_model_diagnostics(ast),
    })


def emit_code_manifest(ast: dict[str, Any], *, target: str = "python") -> dict[str, Any]:
    skipped = [
        {
            "id": record["id"],
            "kind": record_decl_type(record),
            "reason": "no deterministic code adapter registered",
        }
        for record in ast.get("objects", [])
        if record_decl_type(record) in {"claim", "observation", "artifact"}
    ]
    return canonicalize({
        "schema": "aiss.code_manifest.v0.4",
        "ast_hash": ast_hash(ast),
        "target": target,
        "status": "skipped_no_adapter" if skipped else "no_code_units",
        "files": [],
        "skips": sorted(skipped, key=lambda item: (item["kind"], item["id"])),
    })


def diff_asts(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_norm = diff_normalize(left)
    right_norm = diff_normalize(right)
    operations: list[dict[str, Any]] = []
    collect_diff("/", left_norm, right_norm, operations)
    operations = sorted(operations, key=lambda op: (op["path"], op["op"], json.dumps(op, sort_keys=True, ensure_ascii=False)))
    return canonicalize({
        "schema": "aiss.diff_report.v0.4",
        "left_ast_hash": ast_hash(left),
        "right_ast_hash": ast_hash(right),
        "operations": operations,
    })


def render_template(ast: dict[str, Any], template: str) -> str:
    tokens = split_template(template)
    rendered, index = render_tokens(tokens, 0, {"ast": ast, **ast}, stop_tags=set())
    if index != len(tokens):
        raise AissError("template rendering stopped before consuming all tokens")
    return rendered


def canonical_json(data: Any) -> str:
    return json.dumps(canonicalize(data), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def load_ast_or_compile(path: str | Path, *, strict: bool = False) -> dict[str, Any]:
    source_path = Path(path)
    if source_path.suffix == ".json":
        return json.loads(source_path.read_text(encoding="utf-8"))
    return compile_file(source_path, strict=strict)


def write_json(path: str | Path, data: Any) -> None:
    Path(path).write_text(canonical_json(data), encoding="utf-8")


def canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): canonicalize(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    if isinstance(value, tuple):
        return [canonicalize(v) for v in value]
    return value


def sorted_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [canonicalize(r) for r in sorted(records, key=lambda r: r.get("id", ""))]


def sorted_ids(ids: list[str]) -> list[str]:
    return sorted(str(i) for i in ids)


def coerce_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def all_records(ast: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if ast.get("paper"):
        records.append(ast["paper"])
    records.extend(ast.get("sources", []))
    records.extend(ast.get("spans", []))
    records.extend(ast.get("objects", []))
    records.extend(ast.get("relations", []))
    workflow = ast.get("workflow", {})
    if isinstance(workflow, dict):
        records.extend(workflow.get("routes", []))
        records.extend(workflow.get("mida", []))
        records.extend(workflow.get("decisions", []))
        records.extend(workflow.get("events", []))
    records.extend(ast.get("models", []))
    records.extend(ast.get("checks", []))
    records.extend(ast.get("derives", []))
    return records


def record_decl_type(record: dict[str, Any]) -> str:
    return str(record.get("decl_type") or record.get("kind") or "")


def structured_claim_signature(claim: dict[str, Any]) -> tuple[str, str, str, tuple[str, ...]]:
    return (
        str(claim.get("subject")),
        str(claim.get("predicate", "")).strip().casefold(),
        str(claim.get("object")),
        tuple(sorted(str(item) for item in coerce_list(claim.get("scope", [])))),
    )


def reference_matches(expected: str, actual: str) -> bool:
    if expected == "any":
        return True
    if expected == "theory":
        return actual in THEORY_KINDS
    if expected == "empirical":
        return actual in EMPIRICAL_KINDS
    return actual == expected


def severity_rank(severity: str) -> int:
    return {"error": 0, "warning": 1, "info": 2}.get(severity, 3)


def ast_hash(ast: dict[str, Any]) -> str:
    if ast.get("hashes", {}).get("ast_hash"):
        return ast["hashes"]["ast_hash"]
    reduced = {k: v for k, v in ast.items() if k != "hashes"}
    return sha256_text(canonical_json(reduced))


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def normalize_source_for_hash(text: str) -> str:
    no_comments = strip_comments(text)
    return no_comments.replace("\r\n", "\n").replace("\r", "\n")


def strip_comments(text: str) -> str:
    result: list[str] = []
    i = 0
    in_string = False
    escaped = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_string:
            result.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            result.append(ch)
            i += 1
            continue
        if ch == "/" and nxt == "/":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                if text[i] == "\n":
                    result.append("\n")
                i += 1
            i += 2
            continue
        result.append(ch)
        i += 1
    return "".join(result)


def diff_normalize(ast: dict[str, Any]) -> dict[str, Any]:
    reduced = {
        k: v for k, v in ast.items()
        if k not in {"compiler", "input", "hashes"}
    }
    normalized = canonicalize(reduced)
    for key in ("sources", "spans", "objects", "relations", "models", "checks", "derives"):
        if key in normalized:
            normalized[key] = {record["id"]: record for record in normalized[key]}
    return normalized


def collect_diff(path: str, left: Any, right: Any, operations: list[dict[str, Any]]) -> None:
    if isinstance(left, dict) and isinstance(right, dict):
        for key in sorted(set(left) | set(right)):
            child_path = path.rstrip("/") + "/" + str(key)
            if key not in left:
                operations.append({"op": "added", "path": child_path, "right": right[key]})
            elif key not in right:
                operations.append({"op": "removed", "path": child_path, "left": left[key]})
            else:
                collect_diff(child_path, left[key], right[key], operations)
        return
    if isinstance(left, list) and isinstance(right, list):
        max_len = max(len(left), len(right))
        for idx in range(max_len):
            child_path = path.rstrip("/") + "/" + str(idx)
            if idx >= len(left):
                operations.append({"op": "added", "path": child_path, "right": right[idx]})
            elif idx >= len(right):
                operations.append({"op": "removed", "path": child_path, "left": left[idx]})
            else:
                collect_diff(child_path, left[idx], right[idx], operations)
        return
    if left != right:
        operations.append({"op": "changed", "path": path, "left": left, "right": right})


TemplateToken = tuple[str, str]


def split_template(template: str) -> list[TemplateToken]:
    pattern = re.compile(r"({{.*?}}|{%.*?%})", re.S)
    tokens: list[TemplateToken] = []
    pos = 0
    for match in pattern.finditer(template):
        if match.start() > pos:
            tokens.append(("text", template[pos:match.start()]))
        token = match.group(0)
        if token.startswith("{{"):
            tokens.append(("var", token[2:-2].strip()))
        else:
            tokens.append(("tag", token[2:-2].strip()))
        pos = match.end()
    if pos < len(template):
        tokens.append(("text", template[pos:]))
    return tokens


def render_tokens(
    tokens: list[TemplateToken],
    index: int,
    context: dict[str, Any],
    *,
    stop_tags: set[str],
) -> tuple[str, int]:
    output: list[str] = []
    while index < len(tokens):
        typ, value = tokens[index]
        if typ == "text":
            output.append(value)
            index += 1
            continue
        if typ == "var":
            output.append(stringify_template_value(resolve_path(context, value)))
            index += 1
            continue
        if typ == "tag":
            tag_name = value.split()[0] if value.split() else ""
            if tag_name in stop_tags or value in stop_tags:
                return "".join(output), index
            if value.startswith("for "):
                rendered, index = render_for(tokens, index, context, value)
                output.append(rendered)
                continue
            if value.startswith("if "):
                rendered, index = render_if(tokens, index, context, value)
                output.append(rendered)
                continue
            if value in {"endfor", "endif", "else"}:
                return "".join(output), index
            raise AissError(f"unsupported template tag: {value!r}")
    return "".join(output), index


def render_for(tokens: list[TemplateToken], index: int, context: dict[str, Any], tag: str) -> tuple[str, int]:
    match = re.fullmatch(r"for\s+([A-Za-z_][A-Za-z0-9_]*)\s+in\s+(.+)", tag)
    if not match:
        raise AissError(f"invalid for tag: {tag!r}")
    var_name, path = match.groups()
    body_start = index + 1
    body_end = find_matching_tag(tokens, body_start, "for", "endfor")
    body_tokens = tokens[body_start:body_end]
    items = resolve_path(context, path.strip())
    if items is None:
        items = []
    if not isinstance(items, list):
        raise AissError(f"for tag path {path!r} did not resolve to a list")
    rendered_parts: list[str] = []
    for item in items:
        child_context = dict(context)
        child_context[var_name] = item
        rendered, consumed = render_tokens(body_tokens, 0, child_context, stop_tags=set())
        if consumed != len(body_tokens):
            raise AissError("template for-body did not render completely")
        rendered_parts.append(rendered)
    return "".join(rendered_parts), body_end + 1


def render_if(tokens: list[TemplateToken], index: int, context: dict[str, Any], tag: str) -> tuple[str, int]:
    path = tag[3:].strip()
    body_start = index + 1
    body_end = find_matching_tag(tokens, body_start, "if", "endif")
    body_tokens = tokens[body_start:body_end]
    else_index = find_top_level_else(body_tokens)
    if else_index is None:
        true_tokens = body_tokens
        false_tokens: list[TemplateToken] = []
    else:
        true_tokens = body_tokens[:else_index]
        false_tokens = body_tokens[else_index + 1:]
    selected = true_tokens if resolve_path(context, path) else false_tokens
    rendered, consumed = render_tokens(selected, 0, context, stop_tags=set())
    if consumed != len(selected):
        raise AissError("template if-body did not render completely")
    return rendered, body_end + 1


def find_matching_tag(tokens: list[TemplateToken], start: int, open_tag: str, close_tag: str) -> int:
    depth = 1
    index = start
    while index < len(tokens):
        typ, value = tokens[index]
        if typ == "tag":
            if value.startswith(open_tag + " "):
                depth += 1
            elif value == close_tag:
                depth -= 1
                if depth == 0:
                    return index
        index += 1
    raise AissError(f"missing template tag {close_tag!r}")


def find_top_level_else(tokens: list[TemplateToken]) -> int | None:
    depth = 0
    for index, (typ, value) in enumerate(tokens):
        if typ != "tag":
            continue
        if value.startswith("if "):
            depth += 1
        elif value == "endif":
            depth -= 1
        elif value == "else" and depth == 0:
            return index
    return None


def resolve_path(context: dict[str, Any], path: str) -> Any:
    value: Any = context
    for part in path.split("."):
        part = part.strip()
        if not part:
            continue
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list) and part.isdigit():
            value = value[int(part)]
        else:
            return None
    return value


def stringify_template_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(canonicalize(value), ensure_ascii=False, sort_keys=True)
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aiss", description="AISS v0.4 unified deterministic toolchain")
    sub = parser.add_subparsers(dest="command", required=True)

    compile_p = sub.add_parser("compile")
    compile_p.add_argument("input")
    compile_p.add_argument("--strict", action="store_true")

    lint_p = sub.add_parser("lint")
    lint_p.add_argument("input")
    lint_p.add_argument("--strict", action="store_true")

    run_p = sub.add_parser("run")
    run_p.add_argument("input")
    run_p.add_argument("--adapters")

    state_p = sub.add_parser("state")
    state_p.add_argument("input")
    state_p.add_argument("--now", help="ISO timestamp used only for heartbeat freshness calculations.")
    state_p.add_argument("--heartbeat-stale-seconds", type=int, default=DEFAULT_HEARTBEAT_STALE_SECONDS)

    transition_p = sub.add_parser("transition")
    transition_p.add_argument("input")
    transition_p.add_argument("--event", required=True, help="Event JSON object or path to a JSON file.")
    transition_p.add_argument("--now", help="ISO timestamp used when the event omits `at` and for heartbeat freshness.")
    transition_p.add_argument("--heartbeat-stale-seconds", type=int, default=DEFAULT_HEARTBEAT_STALE_SECONDS)
    transition_p.add_argument("--write", action="store_true", help="Append the normalized event declaration to the .aiss source.")

    code_p = sub.add_parser("emit-code")
    code_p.add_argument("input")
    code_p.add_argument("--target", default="python")
    code_p.add_argument("--out")

    diff_p = sub.add_parser("diff")
    diff_p.add_argument("left")
    diff_p.add_argument("right")

    write_p = sub.add_parser("write")
    write_p.add_argument("input")
    write_p.add_argument("--template", required=True)

    args = parser.parse_args(argv)

    try:
        if args.command == "compile":
            print(canonical_json(compile_file(args.input, strict=args.strict)), end="")
        elif args.command == "lint":
            ast = load_ast_or_compile(args.input, strict=args.strict)
            print(canonical_json(lint_ast(ast, strict=args.strict)), end="")
        elif args.command == "run":
            ast = load_ast_or_compile(args.input)
            print(canonical_json(run_ast(ast, adapter_lock_path=args.adapters)), end="")
        elif args.command == "state":
            ast = load_ast_or_compile(args.input)
            print(canonical_json(compute_machine_state(
                ast,
                now=args.now,
                heartbeat_stale_seconds=args.heartbeat_stale_seconds,
            )), end="")
        elif args.command == "transition":
            ast = load_ast_or_compile(args.input)
            event_payload = load_event_payload(args.event)
            report = transition_machine(
                ast,
                event_payload,
                now=args.now,
                heartbeat_stale_seconds=args.heartbeat_stale_seconds,
            )
            if args.write:
                input_path = Path(args.input)
                if input_path.suffix != ".aiss":
                    raise AissError("--write requires a .aiss source file, not a compiled JSON AST")
                append_event_to_source(input_path, report["event"], ast)
                report = {
                    **report,
                    "write": {
                        "path": str(input_path),
                        "event_id": report["event"]["id"],
                        "status": "appended",
                    },
                }
            print(canonical_json(report), end="")
        elif args.command == "emit-code":
            ast = load_ast_or_compile(args.input)
            manifest = emit_code_manifest(ast, target=args.target)
            if args.out:
                out_dir = Path(args.out)
                out_dir.mkdir(parents=True, exist_ok=True)
                write_json(out_dir / "manifest.json", manifest)
            print(canonical_json(manifest), end="")
        elif args.command == "diff":
            left = load_ast_or_compile(args.left)
            right = load_ast_or_compile(args.right)
            print(canonical_json(diff_asts(left, right)), end="")
        elif args.command == "write":
            ast = load_ast_or_compile(args.input)
            template = Path(args.template).read_text(encoding="utf-8")
            print(render_template(ast, template), end="")
        return 0
    except AissError as exc:
        print(f"aiss: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
