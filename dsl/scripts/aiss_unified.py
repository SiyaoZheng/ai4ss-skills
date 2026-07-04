#!/usr/bin/env python3
"""AISS deterministic toolchain core.

This module implements the unified v0.4 source parser, canonical AST compiler,
lint/run/diff/write helpers, and code-manifest generation. It intentionally
does not call LLMs or consult network resources.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import argparse
import hashlib
import json
import re
import sys


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
MIDA_COMPONENTS = {
    "model",
    "inquiry",
    "data_strategy",
    "answer_strategy",
    "diagnose",
    "redesign",
    "report_boundary",
}
ROUTE_STATUSES = {"candidate", "selected", "rejected", "blocked"}

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
        "stop_reason",
        "next_skill_route",
    ),
    "mida": ("route", "component", "text", "status"),
    "decision": ("route", "component", "decision", "status", "owner", "next_skill_route"),
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
        if status == "selected" and route.get("next_skill_route") == "ask_author":
            diag("AISS-WF-002", "warning", route["id"], "selected route still routes to ask_author")

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
        "author_decisions_open": sum(
            1
            for decision in decisions
            if str(decision.get("owner", "")).casefold() == "author"
            and str(decision.get("status", "")).casefold() not in {"resolved", "rejected"}
        ),
    }


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
