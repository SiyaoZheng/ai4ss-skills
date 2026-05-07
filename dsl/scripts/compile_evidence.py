#!/usr/bin/env python3
"""Evidence Table → .aiss 机械编译器。

确定性翻译：同样的证据表 → 同样的 .aiss 输出。
Agent 填表时有自由裁量权，但编译步骤是纯机械的。

证据表格式：结构化 Markdown，用 ##/###/| 分隔 sections。

Usage:
    python3 compile_evidence.py evidence.md > output.aiss
"""

from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Parser for structured evidence markdown
# ---------------------------------------------------------------------------

SECTION_RE = re.compile(r"^## (.+)$")
SUBSECTION_RE = re.compile(r"^### (.+)$")
TABLE_ROW_RE = re.compile(r"^\| (.+) \|$")
KV_RE = re.compile(r"^- \*\*(.+?)\*\*:\s*(.+)$")


def parse_evidence_table(text: str) -> dict[str, Any]:
    """Parse a structured evidence markdown file into a dict.

    Returns:
      {
        "author": "ding",
        "attributes": [{"id": ..., "domain": ..., "values": [...], "description": ..., "source": ...}],
        "concepts": [{"id": ..., "parents": [...], "theta_rows": [...], "rule": ..., ...}],
        "causals": [{"id": ..., "source": ..., "target": ..., ...}],
        "edges": [{"relation": ..., "source": ..., "target": ..., ...}],
        "bridges": [{"id": ..., "type": ..., ...}],
        "model": {"id": ..., "attributes": [...], "concepts": [...], ...},
      }
    """
    lines = text.strip().split("\n")
    result: dict[str, Any] = {
        "author": "",
        "attributes": [],
        "concepts": [],
        "causals": [],
        "edges": [],
        "bridges": [],
        "model": None,
    }

    current_section: str | None = None
    current_entity: dict[str, Any] | None = None
    current_table: dict[str, list[str]] | None = None  # headers → rows of cells
    collecting_table = False

    for line in lines:
        line = line.rstrip()

        # Skip blank lines (but end table collection)
        if not line.strip():
            if collecting_table and current_entity is not None and current_table:
                _finalize_table(current_entity, current_table)
            collecting_table = False
            current_table = None
            continue

        # Section header
        m = SECTION_RE.match(line)
        if m:
            section_name = m.group(1).strip()
            current_section = section_name
            current_entity = None
            collecting_table = False
            continue

        # Sub-section header (starts a new entity)
        m = SUBSECTION_RE.match(line)
        if m:
            entity_name = m.group(1).strip()
            if current_section == "Attributes":
                current_entity = {"id": "", "domain": "", "values": [], "description": "", "source": ""}
                current_entity["id"] = _extract_id(entity_name)
                result["attributes"].append(current_entity)
            elif current_section == "Concepts":
                current_entity = {"id": "", "parents": [], "theta_rows": [], "rule": "undecomposed",
                                  "description": "", "source": "", "operationalization": "", "elsst_label": ""}
                current_entity["id"] = _extract_id(entity_name)
                result["concepts"].append(current_entity)
            elif current_section == "Causal Relations":
                current_entity = {"id": "", "source": "", "target": "", "direction": "positive",
                                  "condition": "none", "mechanism": "",
                                  "textual_support": "EXTRACTED"}
                current_entity["id"] = _extract_id(entity_name)
                result["causals"].append(current_entity)
            elif current_section == "Edges":
                current_entity = {"relation": "", "source": "", "target": "", "confidence": "EXTRACTED", "source": ""}
                result["edges"].append(current_entity)
            elif current_section == "Bridges":
                current_entity = {"id": "", "type": "", "concept": None, "implication": None,
                                  "method": "", "validity": "", "estimand": "none",
                                  "commensurability": "strong", "note": ""}
                current_entity["id"] = _extract_id(entity_name)
                result["bridges"].append(current_entity)
            elif current_section == "Model":
                result["model"] = {"id": _extract_id(entity_name), "attributes": [], "concepts": [],
                                   "causal": [], "bridges": []}
                current_entity = result["model"]
            collecting_table = False
            current_table = None
            continue

        # KV line (under an entity)
        m = KV_RE.match(line)
        if m and current_section == "Paper Metadata":
            key = m.group(1).strip()
            value = m.group(2).strip()
            if key == "author":
                result["author"] = value
            continue
        if m and current_entity is not None:
            key = m.group(1).strip()
            value = m.group(2).strip()
            _set_field(current_entity, key, value)
            continue

        # Table row
        m = TABLE_ROW_RE.match(line)
        if m and current_entity is not None:
            cells = [c.strip() for c in m.group(1).split("|")]
            if not collecting_table:
                # This is the header row
                current_table = {"headers": cells, "rows": []}
                collecting_table = True
            else:
                current_table["rows"].append(cells)
            continue

    # Finalize any remaining table
    if collecting_table and current_entity is not None and current_table:
        _finalize_table(current_entity, current_table)

    return result


def _extract_id(text: str) -> str:
    """Extract an aiss ID from a section header like 'ding.state_capacity' or 'State Capacity (ding.state_capacity)'."""
    # Try to find an explicit ID in parens
    m = re.search(r"\(([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)\)", text)
    if m:
        return m.group(1)
    # Try to find a bare qualified ID
    m = re.search(r"([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)", text)
    if m:
        return m.group(1)
    # Fallback: slugify
    return re.sub(r"[^a-z0-9_]", "_", text.lower().strip())


def _set_field(entity: dict, key: str, value: str):
    """Set a field on an entity dict, mapping evidence-table keys to entity fields."""
    mapping = {
        "id": "id",
        "domain": "domain",
        "values": "values",
        "description": "description",
        "source": "source",
        "parents": "parents",
        "rule": "rule",
        "operationalization": "operationalization",
        "elsst_label": "elsst_label",
        "direction": "direction",
        "condition": "condition",
        "mechanism": "mechanism",
        "textual_support": "textual_support",
        "confidence": "textual_support",
        "evidence": "evidence",
        "commensurability": "commensurability",
        "relation": "relation",
        "type": "type",
        "concept": "concept",
        "implication": "implication",
        "method": "method",
        "validity": "validity",
        "estimand": "estimand",
        "note": "note",
    }
    field = mapping.get(key, key)
    if field == "parents" or field == "values":
        # Parse list: "state_capacity, public_scrutiny" → ["state_capacity", "public_scrutiny"]
        entity[field] = [v.strip() for v in value.split(",") if v.strip()]
    elif field == "source" and "relation" in entity and entity.get("source"):
        entity["source_location"] = value
    else:
        entity[field] = value


def _finalize_table(entity: dict, table: dict):
    """Process a collected markdown table into the entity."""
    headers = [h.lower().strip() for h in table["headers"]]
    rows = table["rows"]

    # θ table for concepts
    if "θ value" in " ".join(headers) or "outcome" in headers:
        theta_rows = []
        for row in rows:
            row_dict = {}
            for i, h in enumerate(headers):
                if i < len(row):
                    row_dict[h] = row[i]
            theta_rows.append(row_dict)
        entity["theta_rows"] = theta_rows


# ---------------------------------------------------------------------------
# Compiler: evidence dict → .aiss source
# ---------------------------------------------------------------------------

VALID_DOMAINS = {"binary", "ordinal", "categorical", "continuous"}
VALID_RULES = {"definitional", "necessary_conjunction", "sufficient_conjunction",
               "aggregative", "threshold", "family_resemblance", "undecomposed",
               "exhaustive_typology"}
VALID_DIRECTIONS = {"positive", "negative", "null", "nonlinear"}
VALID_COMMENSURABILITY = {"strong", "weak", "unchecked"}
VALID_CONFIDENCE = {"EXTRACTED", "INFERRED", "AMBIGUOUS"}
VALID_RELATIONS = {"broader", "narrower", "contrastsWith", "related"}


def compile_to_aiss(evidence: dict) -> str:
    """Compile parsed evidence dict into .aiss source code."""
    lines: list[str] = []
    author = evidence.get("author", "unknown")
    _emit = lines.append

    _emit(f"// Generated from evidence table — author: {author}")
    _emit("")

    # Attributes
    _emit("// ---- Attributes ----")
    _emit("")
    for attr in evidence.get("attributes", []):
        _emit(f"attribute {attr['id']} {{")
        domain = attr.get("domain", "binary")
        if domain not in VALID_DOMAINS:
            domain = "binary"
        _emit(f"  domain: {domain}")
        vals = attr.get("values", [])
        if isinstance(vals, str):
            vals = [v.strip() for v in vals.split(",")]
        if vals:
            _emit(f"  values: {json.dumps(vals)}")
        if attr.get("description"):
            _emit(f"  description: {_quote(attr['description'])}")
        if attr.get("source"):
            _emit(f"  source: {_quote(attr['source'])}")
        _emit("}")
        _emit("")

    # Concepts
    _emit("// ---- Concepts ----")
    _emit("")
    for c in evidence.get("concepts", []):
        _emit(f"concept {c['id']} {{")
        parents = c.get("parents", [])
        if isinstance(parents, str):
            parents = [p.strip() for p in parents.split(",") if p.strip()]
        _emit(f"  parents: {json.dumps(parents)}")

        # Build θ from theta_rows
        theta_rows = c.get("theta_rows", [])
        if theta_rows:
            _emit("  theta: {")
            for row in theta_rows:
                # Find the key columns and value column
                value = "0"
                key_parts = []
                for k, v in row.items():
                    kl = k.lower()
                    if "value" in kl or "outcome" in kl or kl == "c" or kl == "output":
                        value = v
                    elif kl != "evidence" and kl != "confidence" and kl != "source" and kl != "quote":
                        key_parts.append(v)
                key_str = json.dumps(key_parts)
                _emit(f"    {json.dumps(key_str)}: {value}")
            _emit("  }")
        else:
            _emit('  theta: {"none": 1}')

        rule = c.get("rule", "undecomposed")
        if rule not in VALID_RULES:
            rule = "undecomposed"
        _emit(f"  rule: {rule}")
        if c.get("description"):
            _emit(f"  description: {_quote(c['description'])}")
        if c.get("source"):
            _emit(f"  source: {_quote(c['source'])}")
        if c.get("operationalization"):
            _emit(f"  operationalization: {_quote(c['operationalization'])}")
        if c.get("elsst_label"):
            _emit(f"  elsst_label: {_quote(c['elsst_label'])}")
        _emit("}")
        _emit("")

    # Causal relations
    if evidence.get("causals"):
        _emit("// ---- Causal Relations ----")
        _emit("")
        for c in evidence["causals"]:
            _emit(f"causal {c['id']} {{")
            _emit(f"  source: {c.get('source', '')}")
            _emit(f"  target: {c.get('target', '')}")
            direction = c.get("direction", "positive")
            if direction not in VALID_DIRECTIONS:
                direction = "positive"
            _emit(f"  direction: {direction}")
            cond = c.get("condition", "none")
            _emit(f"  condition: {cond if cond else 'none'}")
            mech = c.get("mechanism", "")
            _emit(f"  mechanism: {_quote(mech) if mech else 'none'}")
            conf = c.get("textual_support") or c.get("confidence", "EXTRACTED")
            if conf not in VALID_CONFIDENCE:
                conf = "EXTRACTED"
            _emit(f"  textual_support: {conf}")
            _emit("}")
            _emit("")

    # Edges
    if evidence.get("edges"):
        _emit("// ---- Edges ----")
        _emit("")
        for e in evidence["edges"]:
            rel = e.get("relation", "related")
            if rel not in VALID_RELATIONS:
                rel = "related"
            src = e.get("source", "")
            tgt = e.get("target", "")
            conf = e.get("confidence", "EXTRACTED")
            if conf not in VALID_CONFIDENCE:
                conf = "EXTRACTED"
            src_loc = e.get("source_location", "")
            _emit(f"edge {rel}: {src} -> {tgt} {{")
            _emit(f"  confidence: {conf}")
            if src_loc and src_loc != src:
                _emit(f"  source: {_quote(src_loc)}")
            _emit("}")
            _emit("")

    # Bridges
    if evidence.get("bridges"):
        _emit("// ---- Bridges ----")
        _emit("")
        for b in evidence["bridges"]:
            _emit(f"bridge {b['id']} {{")
            btype = b.get("type", "measurement")
            _emit(f"  type: {btype}")
            if btype == "measurement":
                if b.get("concept"):
                    _emit(f"  concept: {b['concept']}")
                if b.get("method"):
                    _emit(f"  method: {b['method']}")
                if b.get("validity"):
                    _emit(f"  validity: {_quote(b['validity'])}")
            else:
                if b.get("implication"):
                    _emit(f"  implication: {b['implication']}")
                _emit(f"  estimand: {b.get('estimand', 'none')}")
            comm = b.get("commensurability", "strong")
            if comm not in VALID_COMMENSURABILITY:
                comm = "strong"
            _emit(f"  commensurability: {comm}")
            if b.get("note"):
                _emit(f"  note: {_quote(b['note'])}")
            _emit("}")
            _emit("")

    # Model
    model = evidence.get("model")
    if model:
        _emit("// ---- Model ----")
        _emit("")
        _emit(f"model {model['id']} {{")
        for key in ["attributes", "concepts", "causal", "bridges"]:
            items = model.get(key, [])
            if isinstance(items, str):
                items = [i.strip() for i in items.split(",") if i.strip()]
            if items:
                _emit(f"  {key}: [")
                for item in items:
                    _emit(f"    {item}")
                _emit("  ]")
        _emit("}")
        _emit("")

    # Verification commands
    if model:
        _emit("// ---- Verification ----")
        _emit("")
        _emit(f"check theta_completeness on {model['id']}")
        _emit(f"check rule_consistency on {model['id']}")
        _emit(f"check reference_integrity on {model['id']}")
        _emit(f"derive implications from {model['id']}")
        _emit(f"derive ibe_profile from {model['id']}")

    return "\n".join(lines) + "\n"


def _quote(s: str) -> str:
    """JSON-quote a string for .aiss."""
    return json.dumps(s, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Evidence table template (for agents to fill)
# ---------------------------------------------------------------------------

EVIDENCE_TEMPLATE = """## Paper Metadata
- **author**: {author}

## Attributes
### {author}.attr_name
- **domain**: binary | ordinal | categorical | continuous
- **values**: val1, val2, ...
- **description**: ...
- **source**: §N, p.NN

## Concepts
### {author}.concept_name
- **parents**: {author}.attr1, {author}.attr2
- **rule**: definitional | necessary_conjunction | ... | undecomposed
- **description**: ...
- **source**: §N, p.NN
- **operationalization**: ...
- **elsst_label**: ...

| attr1 | attr2 | outcome | evidence (quote) | confidence |
|-------|-------|---------|-------------------|------------|
| low   | high  | 1       | "text quote" (p.N) | EXTRACTED  |

## Causal Relations
### {author}.causal_id
- **source**: {author}.concept_a
- **target**: {author}.concept_b
- **direction**: positive | negative | null | nonlinear
- **condition**: none or "..."
- **mechanism**: ...
- **textual_support**: EXTRACTED | INFERRED | AMBIGUOUS

## Edges
### {author}.edge
- **relation**: broader | narrower | contrastsWith | related
- **source**: {author}.concept_a
- **target**: {author}.concept_b
- **confidence**: EXTRACTED
- **source**: §N

## Bridges
### {author}.bridge_id
- **type**: measurement | causal
- **concept**: {author}.concept_name  (for measurement)
- **implication**: {author}.causal_id  (for causal)
- **method**: ...  (for measurement)
- **validity**: ...  (for measurement)
- **estimand**: none or "..."  (for causal)
- **commensurability**: strong | weak | unchecked
- **note**: ...

## Model
### {author}.model_id
- **attributes**: {author}.attr1, {author}.attr2
- **concepts**: {author}.c1, {author}.c2, ...
- **causal**: {author}.causal1, ...
- **bridges**: {author}.bridge1, ...
"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 compile_evidence.py <evidence.md> [--template]", file=sys.stderr)
        print("       python3 compile_evidence.py --template", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--template":
        print(EVIDENCE_TEMPLATE.format(author="author"))
        return

    filepath = sys.argv[1]
    text = Path(filepath).read_text(encoding="utf-8")
    evidence = parse_evidence_table(text)
    aiss_source = compile_to_aiss(evidence)
    print(aiss_source, end="")


if __name__ == "__main__":
    main()
