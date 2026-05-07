#!/usr/bin/env python3
"""aiss DSL parser — .aiss text → typed AST.

Recursive descent, no external dependencies.
Usage:
    python3 aiss_parser.py model.aiss          # parse and print AST
    python3 aiss_parser.py model.aiss --json   # parse and output JSON
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import re
import sys


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

class TokenType(Enum):
    KEYWORD = "KEYWORD"
    ID = "ID"
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOL = "BOOL"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    COLON = "COLON"
    COMMA = "COMMA"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    ARROW = "ARROW"
    COMMENT = "COMMENT"
    EOF = "EOF"


KEYWORDS = {
    "attribute", "concept", "causal", "bridge", "model", "edge",
    "fact", "check", "derive",
    "binary", "ordinal", "categorical", "continuous",
    "definitional", "necessary_conjunction", "sufficient_conjunction",
    "aggregative", "threshold", "family_resemblance", "undecomposed",
    "exhaustive_typology",
    "positive", "negative", "null", "nonlinear",
    "strong", "weak", "unchecked",
    "EXTRACTED", "INFERRED", "AMBIGUOUS",
    "theta_domain", "textual_support",
    "measurement", "causal",
    "none",
    "all", "where", "no", "and", "or", "not", "in",
    "product", "typeof", "is", "matches",
    "on", "from", "implications", "transitive_closure", "ibe_profile",
    "theta_completeness", "rule_consistency", "reference_integrity",
    "no_self_loop", "hasAttribute_domain", "causes_domain",
    "id_format", "no_orphan_concepts",
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

class Lexer:
    def __init__(self, text: str, filename: str = "<input>"):
        self.text = text
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1

    def error(self, msg: str):
        raise SyntaxError(f"{self.filename}:{self.line}:{self.col}: {msg}")

    def peek(self) -> str:
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def skip_whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos] in " \t\r\n":
            self.advance()

    def read_string(self) -> Token:
        start_line, start_col = self.line, self.col
        self.advance()  # opening "
        chars = []
        while self.pos < len(self.text):
            ch = self.peek()
            if ch == '"':
                self.advance()
                return Token(TokenType.STRING, "".join(chars), start_line, start_col)
            if ch == "\\":
                self.advance()
                if self.pos < len(self.text):
                    chars.append(self.advance())
            else:
                chars.append(self.advance())
        self.error("unterminated string")

    def read_number(self, first: str) -> Token:
        start_line, start_col = self.line, self.col
        # first was peeked but not consumed — advance past it
        self.advance()
        chars = [first]
        while self.pos < len(self.text) and self.peek().isdigit():
            chars.append(self.advance())
        if self.peek() == ".":
            chars.append(self.advance())
            while self.pos < len(self.text) and self.peek().isdigit():
                chars.append(self.advance())
        return Token(TokenType.NUMBER, "".join(chars), start_line, start_col)

    def read_id_or_keyword(self, first: str) -> Token:
        start_line, start_col = self.line, self.col
        # first was peeked but not consumed — advance past it
        self.advance()
        chars = [first]
        while self.pos < len(self.text) and re.match(r"[a-zA-Z0-9_.]", self.peek()):
            chars.append(self.advance())
        value = "".join(chars)
        # Trailing dots are not valid (e.g. "ding." — must have something after)
        if value.endswith("."):
            while value.endswith("."):
                value = value[:-1]
                self.pos -= 1
                self.col -= 1
        if value in KEYWORDS:
            return Token(TokenType.KEYWORD, value, start_line, start_col)
        return Token(TokenType.ID, value, start_line, start_col)

    def next_token(self) -> Token:
        while self.pos < len(self.text):
            self.skip_whitespace()
            if self.pos >= len(self.text):
                break

            ch = self.peek()

            # Comments
            if ch == "/" and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == "/":
                start_line = self.line
                while self.pos < len(self.text) and self.peek() != "\n":
                    self.advance()
                return Token(TokenType.COMMENT, "", start_line, 0)

            # Block comments /* ... */
            if ch == "/" and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == "*":
                self.advance(); self.advance()
                while self.pos < len(self.text):
                    if self.peek() == "*" and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == "/":
                        self.advance(); self.advance()
                        break
                    self.advance()
                continue

            # Strings
            if ch == '"':
                return self.read_string()

            # Numbers
            if ch.isdigit():
                return self.read_number(ch)

            # Arrow ->
            if ch == "-" and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == ">":
                start_line, start_col = self.line, self.col
                self.advance(); self.advance()
                return Token(TokenType.ARROW, "->", start_line, start_col)

            # Single-char tokens
            if ch == "{":
                return Token(TokenType.LBRACE, self.advance(), self.line, self.col - 1)
            if ch == "}":
                return Token(TokenType.RBRACE, self.advance(), self.line, self.col - 1)
            if ch == ":":
                return Token(TokenType.COLON, self.advance(), self.line, self.col - 1)
            if ch == ",":
                return Token(TokenType.COMMA, self.advance(), self.line, self.col - 1)
            if ch == "[":
                return Token(TokenType.LBRACKET, self.advance(), self.line, self.col - 1)
            if ch == "]":
                return Token(TokenType.RBRACKET, self.advance(), self.line, self.col - 1)

            # Identifiers or keywords
            if ch.isalpha() or ch == "_":
                return self.read_id_or_keyword(ch)

            self.error(f"unexpected character: {ch!r}")

        return Token(TokenType.EOF, "", self.line, self.col)


# ---------------------------------------------------------------------------
# AST nodes
# ---------------------------------------------------------------------------

@dataclass
class AttributeNode:
    id: str
    domain: str
    values: list[str]
    description: str | None = None
    source: str | None = None
    line: int = 0

@dataclass
class ConceptNode:
    id: str
    parents: list[str]
    theta: dict[str, str | int]
    theta_domain: str = "binary"   # binary | categorical | continuous
    rule: str = "undecomposed"
    description: str | None = None
    source: str | None = None
    operationalization: str | None = None
    elsst_label: str | None = None
    line: int = 0

@dataclass
class CausalNode:
    """A theoretical causal claim. What the theory asserts — NOT what the empirics identify."""
    id: str
    source: str
    target: str
    direction: str                     # positive | negative | null | nonlinear
    condition: str | None = None       # scope condition
    mechanism: str | None = None       # causal pathway (theoretical)
    textual_support: str = "EXTRACTED" # EXTRACTED | INFERRED | AMBIGUOUS — how clear is this claim in the text?
    line: int = 0

@dataclass
class BridgeNode:
    id: str
    bridge_type: str
    concept: str | None = None
    method: str | None = None
    validity: str | None = None
    implication: str | None = None
    estimand: str | None = None
    commensurability: str = "strong"
    note: str | None = None
    line: int = 0

@dataclass
class EdgeNode:
    relation: str
    source: str
    target: str
    confidence: str = "EXTRACTED"
    source_location: str | None = None
    line: int = 0

@dataclass
class ModelNode:
    id: str
    attributes: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    causal: list[str] = field(default_factory=list)
    bridges: list[str] = field(default_factory=list)
    line: int = 0

@dataclass
class FactNode:
    name: str
    body: str
    line: int = 0

@dataclass
class CheckNode:
    fact_name: str
    model_id: str
    line: int = 0

@dataclass
class DeriveNode:
    what: str
    model_id: str
    line: int = 0

@dataclass
class Program:
    attributes: list[AttributeNode] = field(default_factory=list)
    concepts: list[ConceptNode] = field(default_factory=list)
    causals: list[CausalNode] = field(default_factory=list)
    bridges: list[BridgeNode] = field(default_factory=list)
    models: list[ModelNode] = field(default_factory=list)
    edges: list[EdgeNode] = field(default_factory=list)
    facts: list[FactNode] = field(default_factory=list)
    checks: list[CheckNode] = field(default_factory=list)
    derives: list[DeriveNode] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class Parser:
    def __init__(self, text: str, filename: str = "<input>"):
        self.lexer = Lexer(text, filename)
        self.tokens: list[Token] = []
        self.pos = 0
        self._tokenize()

    def _tokenize(self):
        while True:
            tok = self.lexer.next_token()
            if tok.type != TokenType.COMMENT:
                self.tokens.append(tok)
            if tok.type == TokenType.EOF:
                break

    def error(self, msg: str):
        tok = self.current()
        raise SyntaxError(f"{self.lexer.filename}:{tok.line}:{tok.col}: {msg}")

    def current(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def peek_type(self) -> TokenType:
        return self.current().type

    def peek_value(self) -> str:
        return self.current().value

    def eat(self, expected_type: TokenType | None = None, expected_value: str | None = None):
        tok = self.current()
        if expected_type and tok.type != expected_type:
            self.error(f"expected {expected_type.value}, got {tok.type.value} ({tok.value!r})")
        if expected_value and tok.value != expected_value:
            self.error(f"expected {expected_value!r}, got {tok.value!r}")
        self.pos += 1
        return tok

    def skip_newlines(self):
        """For lists inside [] — skip commas and newlines between items."""
        pass  # handled by the lexer already (whitespace is skipped)

    # ---- core helpers ----

    def parse_block(self) -> dict[str, str | int | None]:
        """Parse { key: value, ... } returning a dict. Values: ID, STRING, NUMBER, BOOL, KEYWORD (none)."""
        self.eat(TokenType.LBRACE)
        fields: dict[str, str | int | None] = {}
        while self.peek_type() != TokenType.RBRACE:
            tok = self.current()
            if tok.type in (TokenType.ID, TokenType.KEYWORD):
                key = self.eat().value
            else:
                self.error(f"expected ID or KEYWORD for block key, got {tok.type.value} ({tok.value!r})")
            self.eat(TokenType.COLON)
            if self.peek_type() == TokenType.ID:
                fields[key] = self.eat().value
            elif self.peek_type() == TokenType.KEYWORD:
                fields[key] = self.eat().value
            elif self.peek_type() == TokenType.STRING:
                fields[key] = self.eat().value
            elif self.peek_type() == TokenType.NUMBER:
                fields[key] = float(self.eat().value) if "." in self.current().value else int(self.eat().value)
            elif self.peek_type() == TokenType.BOOL:
                fields[key] = int(self.eat().value)
            elif self.peek_type() == TokenType.LBRACKET:
                fields[key] = self.parse_string_list()
            elif self.peek_type() == TokenType.LBRACE:
                fields[key] = self.parse_theta_map()
            else:
                self.error(f"unexpected token in block field value: {self.current().type.value} ({self.current().value!r})")
            # Optional trailing comma/newline — just continue
        self.eat(TokenType.RBRACE)
        return fields

    def parse_string_list(self) -> list[str]:
        """Parse ["a", "b", "c"]"""
        self.eat(TokenType.LBRACKET)
        items: list[str] = []
        while self.peek_type() != TokenType.RBRACKET:
            if self.peek_type() == TokenType.COMMA:
                self.eat()
                continue
            items.append(self.eat(TokenType.STRING, None).value if self.peek_type() == TokenType.STRING else self.eat(TokenType.ID, None).value)
        self.eat(TokenType.RBRACKET)
        return items

    def parse_id_list(self) -> list[str]:
        """Parse [id1, id2, ...]"""
        self.eat(TokenType.LBRACKET)
        items: list[str] = []
        while self.peek_type() != TokenType.RBRACKET:
            if self.peek_type() == TokenType.COMMA:
                self.eat()
                continue
            items.append(self.eat(TokenType.ID).value)
        self.eat(TokenType.RBRACKET)
        return items

    def parse_theta_map(self) -> dict[str, str | int]:
        """Parse { "key": value, ... } where value is STRING, NUMBER, or BOOL."""
        self.eat(TokenType.LBRACE)
        result: dict[str, str | int] = {}
        while self.peek_type() != TokenType.RBRACE:
            key = self.eat(TokenType.STRING).value
            self.eat(TokenType.COLON)
            if self.peek_type() == TokenType.STRING:
                result[key] = self.eat().value
            elif self.peek_type() == TokenType.NUMBER:
                tok = self.eat()
                result[key] = float(tok.value) if "." in tok.value else int(tok.value)
            elif self.peek_type() == TokenType.BOOL:
                result[key] = int(self.eat().value)
            elif self.peek_type() in (TokenType.ID, TokenType.KEYWORD):
                result[key] = self.eat().value
            else:
                self.error(f"unexpected theta value type: {self.current().type.value}")
        self.eat(TokenType.RBRACE)
        return result

    # ---- top-level constructs ----

    def parse_attribute(self) -> AttributeNode:
        line = self.current().line
        self.eat(TokenType.KEYWORD, "attribute")
        attr_id = self.eat(TokenType.ID).value
        fields = self.parse_block()
        return AttributeNode(
            id=attr_id,
            domain=fields.get("domain", "binary"),
            values=fields.get("values", []),
            description=fields.get("description"),
            source=fields.get("source"),
            line=line,
        )

    def parse_concept(self) -> ConceptNode:
        line = self.current().line
        self.eat(TokenType.KEYWORD, "concept")
        concept_id = self.eat(TokenType.ID).value
        fields = self.parse_block()
        theta = _normalize_theta_map(fields.get("theta", {}))
        # Auto-infer theta_domain from values unless the model states it.
        theta_domain = fields.get("theta_domain") or fields.get("domain")
        if not theta_domain:
            theta_domain = _infer_theta_domain(theta, fields.get("rule", "undecomposed"))
        return ConceptNode(
            id=concept_id,
            parents=fields.get("parents", []),
            theta=theta,
            theta_domain=theta_domain,
            rule=fields.get("rule", "undecomposed"),
            description=fields.get("description"),
            source=fields.get("source"),
            operationalization=fields.get("operationalization"),
            elsst_label=fields.get("elsst_label"),
            line=line,
        )

    def parse_causal(self) -> CausalNode:
        line = self.current().line
        self.eat(TokenType.KEYWORD, "causal")
        causal_id = self.eat(TokenType.ID).value
        fields = self.parse_block()
        return CausalNode(
            id=causal_id,
            source=fields.get("source", ""),
            target=fields.get("target", ""),
            direction=fields.get("direction", "positive"),
            condition=fields.get("condition"),
            mechanism=fields.get("mechanism"),
            textual_support=fields.get("textual_support") or fields.get("confidence", "EXTRACTED"),
            line=line,
        )

    def parse_bridge(self) -> BridgeNode:
        line = self.current().line
        self.eat(TokenType.KEYWORD, "bridge")
        bridge_id = self.eat(TokenType.ID).value
        fields = self.parse_block()
        return BridgeNode(
            id=bridge_id,
            bridge_type=fields.get("type", "measurement"),
            concept=fields.get("concept"),
            method=fields.get("method"),
            validity=fields.get("validity"),
            implication=fields.get("implication"),
            estimand=fields.get("estimand"),
            commensurability=fields.get("commensurability", "strong"),
            note=fields.get("note"),
            line=line,
        )

    def parse_model(self) -> ModelNode:
        line = self.current().line
        self.eat(TokenType.KEYWORD, "model")
        model_id = self.eat(TokenType.ID).value
        fields = self.parse_block()
        return ModelNode(
            id=model_id,
            attributes=fields.get("attributes", []),
            concepts=fields.get("concepts", []),
            causal=fields.get("causal", []),
            bridges=fields.get("bridges", []),
            line=line,
        )

    def parse_edge(self) -> EdgeNode:
        line = self.current().line
        self.eat(TokenType.KEYWORD, "edge")
        tok = self.current()
        if tok.type in (TokenType.ID, TokenType.KEYWORD):
            relation = self.eat().value
        else:
            self.error(f"expected relation name, got {tok.type.value}")
        self.eat(TokenType.COLON)
        source = self.eat_identifier()
        self.eat(TokenType.ARROW)
        target = self.eat_identifier()
        fields = self.parse_block() if self.peek_type() == TokenType.LBRACE else {}
        return EdgeNode(
            relation=relation,
            source=source,
            target=target,
            confidence=fields.get("confidence", "EXTRACTED"),
            source_location=fields.get("source"),
            line=line,
        )

    def eat_identifier(self) -> str:
        """Eat an ID or KEYWORD as an identifier, return its value."""
        tok = self.current()
        if tok.type in (TokenType.ID, TokenType.KEYWORD):
            return self.eat().value
        self.error(f"expected identifier, got {tok.type.value} ({tok.value!r})")

    def parse_fact(self) -> FactNode:
        line = self.current().line
        self.eat(TokenType.KEYWORD, "fact")
        name = self.eat_identifier()
        self.eat(TokenType.LBRACE)
        # Capture the body text verbatim between braces
        body_parts = []
        brace_depth = 1
        while brace_depth > 0:
            if self.peek_type() == TokenType.LBRACE:
                brace_depth += 1
                body_parts.append(self.eat().value)
            elif self.peek_type() == TokenType.RBRACE:
                brace_depth -= 1
                if brace_depth > 0:
                    body_parts.append(self.eat().value)
            elif self.peek_type() == TokenType.EOF:
                self.error("unterminated fact body")
            else:
                body_parts.append(self.eat().value)
        return FactNode(name=name, body=" ".join(body_parts), line=line)

    def parse_check(self) -> CheckNode:
        line = self.current().line
        self.eat(TokenType.KEYWORD, "check")
        fact_name = self.eat_identifier()
        self.eat(TokenType.KEYWORD, "on")
        model_id = self.eat_identifier()
        return CheckNode(fact_name=fact_name, model_id=model_id, line=line)

    def parse_derive(self) -> DeriveNode:
        line = self.current().line
        self.eat(TokenType.KEYWORD, "derive")
        what = self.eat_identifier()
        self.eat(TokenType.KEYWORD, "from")
        model_id = self.eat_identifier()
        return DeriveNode(what=what, model_id=model_id, line=line)

    # ---- main ----

    def parse_program(self) -> Program:
        prog = Program()
        while self.peek_type() != TokenType.EOF:
            tok = self.current()
            if tok.type != TokenType.KEYWORD:
                self.error(f"expected keyword at top level, got {tok.type.value} ({tok.value!r})")

            kw = tok.value
            if kw == "attribute":
                prog.attributes.append(self.parse_attribute())
            elif kw == "concept":
                prog.concepts.append(self.parse_concept())
            elif kw == "causal":
                prog.causals.append(self.parse_causal())
            elif kw == "bridge":
                prog.bridges.append(self.parse_bridge())
            elif kw == "model":
                prog.models.append(self.parse_model())
            elif kw == "edge":
                prog.edges.append(self.parse_edge())
            elif kw == "fact":
                prog.facts.append(self.parse_fact())
            elif kw == "check":
                prog.checks.append(self.parse_check())
            elif kw == "derive":
                prog.derives.append(self.parse_derive())
            else:
                self.error(f"unexpected keyword at top level: {kw!r}")

        return prog


def _infer_theta_domain(theta: dict, rule: str) -> str:
    """Infer theta domain from values: binary (0/1), categorical (strings), continuous (numbers)."""
    if not theta:
        return "binary"
    values = list(theta.values())
    if rule == "exhaustive_typology":
        return "categorical"
    # Check if all values are 0/1
    if all(v in (0, 1, "0", "1") for v in values):
        return "binary"
    # Check if values are strings
    if all(isinstance(v, str) for v in values):
        return "categorical"
    # Check if values are numeric
    if all(isinstance(v, (int, float)) for v in values):
        return "continuous"
    return "binary"


def _normalize_theta_map(theta: dict) -> dict:
    """Normalize theta keys so equivalent JSON-array strings compare equal."""
    normalized = {}
    for key, value in theta.items():
        if key == "none":
            normalized[key] = value
            continue
        try:
            parsed = json.loads(key)
        except json.JSONDecodeError:
            normalized[key] = value
            continue
        if isinstance(parsed, list):
            normalized[json.dumps(parsed)] = value
        else:
            normalized[key] = value
    return normalized


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_file(filepath: str) -> Program:
    text = Path(filepath).read_text(encoding="utf-8")
    parser = Parser(text, filepath)
    return parser.parse_program()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 aiss_parser.py <file.aiss> [--json]", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    output_json = "--json" in sys.argv

    prog = parse_file(filepath)

    if output_json:
        from dataclasses import asdict
        print(json.dumps(asdict(prog), indent=2, default=str))
    else:
        print(f"Parsed {filepath} successfully.")
        print(f"  attributes: {len(prog.attributes)}")
        print(f"  concepts:   {len(prog.concepts)}")
        print(f"  causals:    {len(prog.causals)}")
        print(f"  bridges:    {len(prog.bridges)}")
        print(f"  models:     {len(prog.models)}")
        print(f"  edges:      {len(prog.edges)}")
        print(f"  facts:      {len(prog.facts)}")
        print(f"  checks:     {len(prog.checks)}")
        print(f"  derives:    {len(prog.derives)}")


if __name__ == "__main__":
    main()
