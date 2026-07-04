#!/usr/bin/env python3
"""
generate_pdf_report.py — DDI metadata → human-readable PDF codebook.

Usage:
    python3 generate_pdf_report.py ddi-metadata.yaml [output.pdf]

If output path is omitted, writes <stem>-codebook.pdf next to the YAML file.
Requires: reportlab  (pip install reportlab)
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Colour palette (tech-minimalist, cold) ──────────────────────────────────
C_BLACK   = colors.HexColor("#111111")
C_WHITE   = colors.white
C_ACCENT  = colors.HexColor("#2563EB")   # saturated blue
C_GRAY1   = colors.HexColor("#F8F9FA")   # near-white row fill
C_GRAY2   = colors.HexColor("#E9ECEF")   # alternate row / rule
C_GRAY3   = colors.HexColor("#6C757D")   # muted text
C_GRAY4   = colors.HexColor("#343A40")   # section headers
C_FLAG    = colors.HexColor("#FFF3CD")   # flag highlight (amber-tint)
C_MISS    = colors.HexColor("#F8D7DA")   # missing code highlight (rose-tint)

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm

# ── Style helpers ────────────────────────────────────────────────────────────
def build_styles():
    base = getSampleStyleSheet()
    def S(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=base[parent], **kw)

    return {
        "title":    S("title",    fontSize=22, textColor=C_BLACK,
                       fontName="Helvetica-Bold", spaceAfter=4,
                       alignment=TA_LEFT),
        "subtitle": S("subtitle", fontSize=11, textColor=C_GRAY3,
                       fontName="Helvetica", spaceAfter=2),
        "h1":       S("h1",       fontSize=14, textColor=C_ACCENT,
                       fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=6,
                       borderPadding=(0,0,4,0)),
        "h2":       S("h2",       fontSize=11, textColor=C_GRAY4,
                       fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=4),
        "body":     S("body",     fontSize=9,  textColor=C_BLACK,
                       fontName="Helvetica", leading=13),
        "small":    S("small",    fontSize=8,  textColor=C_GRAY3,
                       fontName="Helvetica", leading=11),
        "mono":     S("mono",     fontSize=8,  textColor=C_BLACK,
                       fontName="Courier", leading=11),
        "flag":     S("flag",     fontSize=8,  textColor=colors.HexColor("#856404"),
                       fontName="Helvetica-Oblique", leading=11),
        "cell":     S("cell",     fontSize=8,  textColor=C_BLACK,
                       fontName="Helvetica", leading=11, wordWrap="CJK"),
        "cell_mono":S("cell_mono",fontSize=7.5,textColor=C_BLACK,
                       fontName="Courier", leading=11, wordWrap="CJK"),
    }


def header_footer(canvas, doc):
    """Running header/footer on every page."""
    canvas.saveState()
    w, h = A4
    # footer line
    canvas.setStrokeColor(C_GRAY2)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.5*cm, w - MARGIN, 1.5*cm)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(C_GRAY3)
    canvas.drawString(MARGIN, 1.1*cm, doc.study_name)
    canvas.drawRightString(w - MARGIN, 1.1*cm, f"Page {doc.page}")
    canvas.restoreState()


# ── Section builders ─────────────────────────────────────────────────────────

def title_block(doc_meta, styles, study):
    elems = []
    name = study.get("name") or "Survey Dataset"
    elems.append(Paragraph(name, styles["title"]))

    # subtitle row: analysis_unit · data_source
    parts = []
    if study.get("analysis_unit"):
        parts.append(f"Unit of analysis: {study['analysis_unit']}")
    if study.get("data_source"):
        src = Path(study["data_source"]).name
        parts.append(f"Source: {src}")
    if parts:
        elems.append(Paragraph("  ·  ".join(parts), styles["subtitle"]))

    elems.append(Paragraph(
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}  ·  codebook-parse v1.0",
        styles["small"]))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=C_ACCENT, spaceAfter=8))
    return elems


def kv_table(rows, styles):
    """Two-column key-value mini-table."""
    data = [[Paragraph(str(k), styles["small"]),
             Paragraph(str(v or "—"), styles["cell"])]
            for k, v in rows]
    t = Table(data, colWidths=[4*cm, PAGE_W - MARGIN*2 - 4*cm])
    t.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",   (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0), (-1,-1), 3),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[C_WHITE, C_GRAY1]),
    ]))
    return t


def study_section(doc, styles):
    study = doc.get("study") or {}
    ds    = doc.get("data_structure") or {}
    elems = []
    elems.append(Paragraph("Study Metadata", styles["h1"]))

    rows = [
        ("Study name",     study.get("name")),
        ("Analysis unit",  study.get("analysis_unit")),
        ("Data source",    study.get("data_source")),
        ("Observations",   ds.get("n_obs")),
        ("Variables",      ds.get("n_vars") or len(doc.get("variables") or [])),
        ("Weight variable",ds.get("weight_var")),
        ("Agency",         study.get("agency")),
        ("Universe",       study.get("universe")),
        ("Wave",           study.get("wave")),
    ]
    rows = [(k, v) for k, v in rows if v not in (None, "", "null")]
    elems.append(kv_table(rows, styles))
    return elems


def _fmt_codes(codes_dict, styles, max_items=8):
    """Render a codes dict as a compact Paragraph."""
    if not codes_dict:
        return Paragraph("—", styles["cell"])
    items = list(codes_dict.items())
    shown = items[:max_items]
    text = ";  ".join(f"{k}={v}" for k, v in shown)
    if len(items) > max_items:
        text += f"  … +{len(items)-max_items} more"
    return Paragraph(text, styles["cell_mono"])


def _fmt_missing(missing_block, styles):
    """Render missing block as compact text."""
    if not missing_block:
        return Paragraph("—", styles["cell"])
    parts = []
    codes = missing_block.get("codes") or {}
    for k, v in codes.items():
        t = v.get("type", "?") if isinstance(v, dict) else str(v)
        parts.append(f"{k}={t}")
    ranges = missing_block.get("ranges") or []
    for r in ranges:
        parts.append(f"[{r.get('min')},{r.get('max')}]={r.get('type','?')}")
    if missing_block.get("schema_ref"):
        parts.append(f"→{missing_block['schema_ref']}")
    return Paragraph(";  ".join(parts) or "—", styles["cell_mono"])


def variables_section(doc, styles):
    variables = doc.get("variables") or []
    elems = []
    elems.append(Paragraph("Variable Reference", styles["h1"]))
    elems.append(Paragraph(
        f"{len(variables)} variables  ·  coded in DDI representation types",
        styles["small"]))
    elems.append(Spacer(1, 6))

    # Table headers
    COL_W = [1.5*cm, 3*cm, 6.5*cm, 2*cm, 5*cm, 3.5*cm, 3*cm]
    total_w = sum(COL_W)
    # Recalculate to fit page
    avail = PAGE_W - MARGIN*2
    if total_w > avail:
        scale = avail / total_w
        COL_W = [w * scale for w in COL_W]

    def P(text, style="cell"):
        return Paragraph(str(text) if text else "—", styles[style])

    header = [P("ID","small"), P("Name","small"), P("Label","small"),
              P("Type","small"), P("Codes","small"),
              P("Missing","small"), P("Flags","small")]

    CHUNK = 40   # rows per page to avoid memory blow-up on large datasets
    row_data_all = []
    for v in variables:
        rep   = v.get("representation") or {}
        miss  = v.get("missing") or {}
        flags = v.get("_parse_flags") or []
        # category_scheme_ref overrides inline codes
        if rep.get("category_scheme_ref"):
            codes_cell = Paragraph(f"→ {rep['category_scheme_ref']}", styles["cell_mono"])
        else:
            codes_cell = _fmt_codes(rep.get("codes"), styles)

        flag_text = ", ".join(flags) if flags else "—"
        row_data_all.append([
            P(v.get("id")),
            P(v.get("name"), "cell_mono"),
            P(v.get("label")),
            P(rep.get("type")),
            codes_cell,
            _fmt_missing(miss, styles),
            Paragraph(flag_text, styles["flag"] if flags else styles["cell"]),
        ])

    # Build table in chunks so large datasets don't blow reportlab
    bg_cycle = [C_WHITE, C_GRAY1]
    full_data = [header] + row_data_all

    style_cmds = [
        ("BACKGROUND",  (0,0), (-1,0), C_GRAY4),
        ("TEXTCOLOR",   (0,0), (-1,0), C_WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",  (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING", (0,0), (-1,-1), 3),
        ("RIGHTPADDING",(0,0), (-1,-1), 3),
        ("GRID",        (0,0), (-1,-1), 0.25, C_GRAY2),
    ]
    for i, row in enumerate(row_data_all):
        bg = bg_cycle[i % 2]
        # flag rows get amber tint
        flags = variables[i].get("_parse_flags") or []
        if flags:
            bg = C_FLAG
        style_cmds.append(("BACKGROUND", (0, i+1), (-1, i+1), bg))

    t = Table(full_data, colWidths=COL_W, repeatRows=1)
    t.setStyle(TableStyle(style_cmds))
    elems.append(t)
    return elems


def shared_schemas_section(doc, styles):
    scs  = doc.get("shared_category_schemes") or {}
    sms  = doc.get("shared_missing_schemas") or {}
    if not scs and not sms:
        return []

    elems = []
    elems.append(PageBreak())
    elems.append(Paragraph("Shared Schemas", styles["h1"]))

    if scs:
        elems.append(Paragraph("Category Schemes", styles["h2"]))
        for name, scheme in scs.items():
            elems.append(Paragraph(f"<b>{name}</b>", styles["body"]))
            codes = scheme.get("codes") or {}
            text = "  ".join(f"{k} = {v}" for k, v in codes.items())
            elems.append(Paragraph(text, styles["mono"]))
            elems.append(Spacer(1, 4))

    if sms:
        elems.append(Paragraph("Missing Code Schemas", styles["h2"]))
        for name, schema in sms.items():
            elems.append(Paragraph(f"<b>{name}</b>", styles["body"]))
            codes = schema.get("codes") or {}
            parts = [f"{k} → {v.get('type','?') if isinstance(v,dict) else v}"
                     for k, v in codes.items()]
            ranges = schema.get("ranges") or []
            for r in ranges:
                parts.append(f"[{r.get('min')},{r.get('max')}] → {r.get('type','?')}")
            elems.append(Paragraph("  ·  ".join(parts), styles["mono"]))
            elems.append(Spacer(1, 4))

    return elems


def flags_summary_section(doc, styles):
    variables = doc.get("variables") or []
    flag_map = {}
    for v in variables:
        for f in (v.get("_parse_flags") or []):
            flag_map.setdefault(f, []).append(v.get("name", "?"))

    if not flag_map:
        return []

    elems = []
    elems.append(Paragraph("Parse Flags Summary", styles["h1"]))
    elems.append(Paragraph(
        "Flagged variables need manual review before running cleaning-contract.",
        styles["small"]))
    elems.append(Spacer(1, 6))

    FLAG_EXPLANATIONS = {
        "missing_codes_inferred": "Negative values assumed missing — not explicitly labelled in source. Verify.",
        "type_uncertain":         "Representation type ambiguous (numeric vs. ordinal code). Check.",
        "codes_incomplete":       "Observed values found with no corresponding label.",
        "label_truncated":        "Source variable label was truncated at 255 chars.",
        "no_concept":             "Could not map to a ConceptualVariable — fill concept + unit_type manually.",
    }

    for flag, var_names in sorted(flag_map.items()):
        expl = FLAG_EXPLANATIONS.get(flag, "")
        elems.append(KeepTogether([
            Paragraph(f"<b>{flag}</b>  ({len(var_names)} variables)", styles["h2"]),
            Paragraph(expl, styles["small"]) if expl else Spacer(1, 1),
            Paragraph(", ".join(var_names[:60]) +
                      (f"  … +{len(var_names)-60} more" if len(var_names)>60 else ""),
                      styles["cell_mono"]),
            Spacer(1, 6),
        ]))
    return elems


def processing_events_section(doc, styles):
    events = doc.get("processing_events") or []
    if not events:
        return []
    elems = []
    elems.append(Paragraph("Processing Events", styles["h1"]))
    for e in events:
        rows = [
            ("Event ID",   e.get("event_id")),
            ("Type",       e.get("type")),
            ("Timestamp",  e.get("timestamp")),
            ("Skill",      f"codebook-parse v{e.get('skill_version','')}"),
            ("Description",e.get("description")),
            ("Inputs",     ", ".join(e.get("inputs") or [])),
            ("Outputs",    ", ".join(e.get("outputs") or [])),
        ]
        rows = [(k, v) for k, v in rows if v]
        elems.append(kv_table(rows, styles))
        elems.append(Spacer(1, 8))
    return elems


# ── Main ─────────────────────────────────────────────────────────────────────

def generate_pdf(yaml_path: str, out_path: str | None = None):
    yaml_path = Path(yaml_path)
    if not yaml_path.exists():
        sys.exit(f"ERROR: {yaml_path} not found")

    with open(yaml_path) as f:
        doc = yaml.safe_load(f)

    if out_path is None:
        out_path = yaml_path.parent / (yaml_path.stem + "-codebook.pdf")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    study_name = (doc.get("study") or {}).get("name") or yaml_path.stem

    pdf = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=2.2*cm,
        title=study_name,
        author="codebook-parse",
    )
    pdf.study_name = study_name   # used by header_footer

    styles = build_styles()
    story  = []

    # ── Cover ──
    story += title_block(doc, styles, doc.get("study") or {})
    story.append(Spacer(1, 8))

    # quick stats row
    variables = doc.get("variables") or []
    ds = doc.get("data_structure") or {}
    n_obs  = ds.get("n_obs")
    n_flag = sum(1 for v in variables if v.get("_parse_flags"))
    type_counts = {}
    for v in variables:
        t = (v.get("representation") or {}).get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    type_str = "  ·  ".join(f"{cnt} {tp}" for tp, cnt in
                             sorted(type_counts.items(), key=lambda x: -x[1]))
    stats_lines = [f"{len(variables)} variables   {type_str}"]
    if n_obs:
        stats_lines.append(f"{n_obs:,} observations")
    if n_flag:
        stats_lines.append(f"{n_flag} flagged for review")
    story.append(Paragraph("  ·  ".join(stats_lines), styles["small"]))
    story.append(Spacer(1, 14))

    # ── Sections ──
    story += study_section(doc, styles)
    story.append(Spacer(1, 10))
    story.append(PageBreak())

    story += variables_section(doc, styles)

    story += shared_schemas_section(doc, styles)

    story.append(Spacer(1, 10))
    story += flags_summary_section(doc, styles)

    story += processing_events_section(doc, styles)

    pdf.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF written: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    generate_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
