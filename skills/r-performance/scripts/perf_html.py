#!/usr/bin/env python3
"""
perf_html.py — Before/after R code + optional perf metrics → self-contained HTML report.

Usage:
    python3 perf_html.py before.R after.R [perf-summary.json] [output.html]

perf-summary.json format (optional, all fields optional):
    {
      "runtime_before": "4.2s",
      "runtime_after":  "0.34s",
      "speedup":        "12.4",
      "memory_before":  "812 MB",
      "memory_after":   "94 MB",
      "mem_reduction":  "88",
      "note":           "Vectorized inner loop; eliminated redundant join"
    }

If output path is omitted, writes perf-report.html in the current directory.
No external dependencies.

Design: "Audit Panel" — speedup banner, metric cards, code diff.
"""

import sys
import json
import html as html_mod
import difflib
from pathlib import Path
from datetime import datetime

CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg:         #ffffff;
  --surface:    #f8f9fa;
  --border:     #e2e8f0;
  --text:       #0f172a;
  --text-muted: #64748b;
  --accent:     #2563eb;
  --ok:         #22c55e;
  --warn:       #f59e0b;
  --code-bg:    #f1f5f9;
  --del-bg:     #fff1f2;
  --del-line:   #fecaca;
  --add-bg:     #f0fdf4;
  --add-line:   #bbf7d0;
}
body {
  font-family: system-ui, -apple-system, 'Inter', sans-serif;
  font-size: 14px;
  color: var(--text);
  background: var(--bg);
  line-height: 1.5;
}
.topbar {
  height: 48px;
  background: #0f172a;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
}
.topbar-title { color: #94a3b8; font-size: 13px; }
.topbar-skill { color: var(--accent); font-weight: 600; }
.topbar-ts { color: #64748b; font-size: 12px; margin-left: auto; font-family: 'JetBrains Mono', monospace; }

/* ── Speedup banner ── */
.banner {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  border-bottom: 1px solid #bfdbfe;
  padding: 24px 40px;
  display: flex;
  align-items: center;
  gap: 32px;
}
.banner-speedup {
  font-family: 'JetBrains Mono', monospace;
  font-size: 52px;
  font-weight: 700;
  color: var(--accent);
  line-height: 1;
}
.banner-sub {
  font-size: 14px;
  color: #1d4ed8;
  margin-top: 4px;
}
.banner-note {
  flex: 1;
  font-size: 13px;
  color: #1e40af;
  background: rgba(255,255,255,.6);
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  padding: 12px 16px;
  font-style: italic;
}

/* ── Metric cards ── */
.metrics {
  display: flex;
  gap: 16px;
  padding: 24px 40px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.metric-card {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 20px;
}
.metric-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-muted);
  margin-bottom: 12px;
}
.metric-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 10px;
}
.metric-before {
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  color: var(--text-muted);
  text-decoration: line-through;
}
.metric-arrow { color: var(--text-muted); font-size: 14px; }
.metric-after {
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px;
  font-weight: 700;
  color: var(--accent);
}
.metric-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 28px;
  margin-top: 8px;
}
.bar {
  border-radius: 2px 2px 0 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  font-size: 9px;
  color: #fff;
  padding-bottom: 2px;
  min-width: 32px;
  min-height: 8px;
  transition: all .3s;
}
.bar-before { background: #94a3b8; }
.bar-after  { background: var(--accent); }

/* ── Code diff ── */
.diff-section {
  padding: 24px 40px 40px;
  max-width: 1400px;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-muted);
  margin-bottom: 16px;
}
.diff-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.diff-panel {
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
.diff-panel-header {
  padding: 8px 14px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-muted);
  font-weight: 600;
}
.diff-code {
  overflow-x: auto;
}
.diff-code table {
  width: 100%;
  border-collapse: collapse;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12.5px;
  line-height: 1.55;
}
.diff-code td { padding: 1px 0; white-space: pre; }
.diff-code td.ln {
  width: 40px;
  text-align: right;
  padding-right: 12px;
  color: var(--text-muted);
  user-select: none;
  font-size: 11px;
  border-right: 1px solid var(--border);
  background: var(--surface);
}
.diff-code td.code { padding-left: 12px; }
.diff-del { background: var(--del-bg); }
.diff-del td.ln { background: #fee2e2; }
.diff-add { background: var(--add-bg); }
.diff-add td.ln { background: #dcfce7; }

.footer {
  height: 36px;
  background: var(--surface);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 40px;
  font-size: 12px;
  color: var(--text-muted);
}
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

@media (max-width: 768px) {
  .banner { flex-direction: column; gap: 16px; padding: 20px 24px; }
  .banner-speedup { font-size: 40px; }
  .metrics { flex-direction: column; padding: 16px 24px; }
  .diff-panels { grid-template-columns: 1fr; }
  .diff-section { padding: 16px 24px 32px; }
}
"""


def render_code_panel(lines: list[str], diff_marks: list[str], kind: str) -> str:
    rows = []
    for i, (line, mark) in enumerate(zip(lines, diff_marks), start=1):
        if kind == "before":
            cls = "diff-del" if mark in ("-",) else ""
        else:
            cls = "diff-add" if mark in ("+",) else ""
        escaped = html_mod.escape(line.rstrip("\n"))
        rows.append(f'<tr class="{cls}"><td class="ln">{i}</td><td class="code">{escaped}</td></tr>')
    return "<table>" + "".join(rows) + "</table>"


def compute_diff_marks(before_lines: list[str], after_lines: list[str]):
    """Return (before_marks, after_marks) aligned to each file's lines."""
    matcher = difflib.SequenceMatcher(None, before_lines, after_lines)
    before_marks = [""] * len(before_lines)
    after_marks = [""] * len(after_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag in ("replace", "delete"):
            for k in range(i1, i2):
                before_marks[k] = "-"
        if tag in ("replace", "insert"):
            for k in range(j1, j2):
                after_marks[k] = "+"
    return before_marks, after_marks


def bar_chart_svg(before_val: float, after_val: float, max_val: float) -> str:
    h = 28
    bh = int((before_val / max_val) * h) if max_val else h
    ah = int((after_val / max_val) * h) if max_val else 4
    return f"""<div class="bar-chart">
      <div class="bar bar-before" style="height:{bh}px" title="Before"></div>
      <div class="bar bar-after"  style="height:{ah}px" title="After"></div>
    </div>"""


def metric_card(title: str, before: str, after: str, reduction: str, bar_html: str) -> str:
    return f"""<div class="metric-card">
  <div class="metric-title">{html_mod.escape(title)}</div>
  <div class="metric-row">
    <span class="metric-before">{html_mod.escape(before)}</span>
    <span class="metric-arrow">→</span>
    <span class="metric-after">{html_mod.escape(after)}</span>
  </div>
  {('<span class="metric-badge">-' + html_mod.escape(reduction) + '% reduction</span>') if reduction else ''}
  {bar_html}
</div>"""


def generate_html(
    before_path: str,
    after_path: str,
    perf_json_path: str | None = None,
    output_path: str | None = None,
) -> None:
    before_src = Path(before_path)
    after_src = Path(after_path)
    for p in [before_src, after_src]:
        if not p.exists():
            sys.exit(f"Error: file not found: {p}")

    before_lines = before_src.read_text(encoding="utf-8").splitlines(keepends=True)
    after_lines = after_src.read_text(encoding="utf-8").splitlines(keepends=True)

    perf = {}
    if perf_json_path and Path(perf_json_path).exists():
        perf = json.loads(Path(perf_json_path).read_text(encoding="utf-8"))

    if output_path is None:
        output_path = "perf-report.html"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Banner
    speedup = perf.get("speedup", "")
    speedup_txt = f"{speedup}×" if speedup else "—"
    banner_sub = "faster than baseline · bottleneck eliminated" if speedup else "Performance comparison"
    note_txt = perf.get("note", "")
    banner_note = f'<div class="banner-note">{html_mod.escape(note_txt)}</div>' if note_txt else ""

    # ── Metric cards
    def parse_float(s: str) -> float:
        m_val = ""
        for c in s:
            if c.isdigit() or c == '.':
                m_val += c
        return float(m_val) if m_val else 0.0

    rt_b = perf.get("runtime_before", "—")
    rt_a = perf.get("runtime_after", "—")
    rt_bv, rt_av = parse_float(rt_b), parse_float(rt_a)
    rt_max = max(rt_bv, rt_av) or 1
    rt_red = str(round((1 - rt_av / rt_bv) * 100)) if rt_bv > 0 and rt_av > 0 else ""

    mem_b = perf.get("memory_before", "—")
    mem_a = perf.get("memory_after", "—")
    mem_bv, mem_av = parse_float(mem_b), parse_float(mem_a)
    mem_max = max(mem_bv, mem_av) or 1
    mem_red = perf.get("mem_reduction", "")
    if not mem_red and mem_bv > 0 and mem_av > 0:
        mem_red = str(round((1 - mem_av / mem_bv) * 100))

    card1 = metric_card("Runtime", rt_b, rt_a, rt_red, bar_chart_svg(rt_bv, rt_av, rt_max))
    card2 = metric_card("Memory", mem_b, mem_a, str(mem_red), bar_chart_svg(mem_bv, mem_av, mem_max))
    card3_note = perf.get("approach", "Optimized implementation")
    card3 = f"""<div class="metric-card">
  <div class="metric-title">Approach</div>
  <div style="font-size:13px;color:var(--text);line-height:1.6;margin-top:4px">{html_mod.escape(card3_note)}</div>
</div>"""

    # ── Code diff
    before_marks, after_marks = compute_diff_marks(
        [l.rstrip("\n") for l in before_lines],
        [l.rstrip("\n") for l in after_lines],
    )
    before_panel = render_code_panel(before_lines, before_marks, "before")
    after_panel = render_code_panel(after_lines, after_marks, "after")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>r-performance — Report</title>
<style>{CSS}</style>
</head>
<body>

<div class="topbar">
  <span class="topbar-title">ai4ss-skills · <span class="topbar-skill">r-performance</span></span>
  <span class="topbar-ts">{ts}</span>
</div>

<div class="banner">
  <div>
    <div class="banner-speedup">{html_mod.escape(speedup_txt)}</div>
    <div class="banner-sub">{html_mod.escape(banner_sub)}</div>
  </div>
  {banner_note}
</div>

<div class="metrics">
  {card1}
  {card2}
  {card3}
</div>

<div class="diff-section">
  <div class="section-title">Code Changes</div>
  <div class="diff-panels">
    <div class="diff-panel">
      <div class="diff-panel-header">Before — {html_mod.escape(before_src.name)}</div>
      <div class="diff-code">{before_panel}</div>
    </div>
    <div class="diff-panel">
      <div class="diff-panel-header">After — {html_mod.escape(after_src.name)}</div>
      <div class="diff-code">{after_panel}</div>
    </div>
  </div>
</div>

<div class="footer">
  Generated by ai4ss-skills r-performance · {ts}
</div>

</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"Written: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 perf_html.py before.R after.R [perf-summary.json] [output.html]")
        sys.exit(1)
    args = sys.argv[1:]
    before = args[0]
    after = args[1]
    perf_json = None
    out = None
    if len(args) >= 3:
        if args[2].endswith(".json"):
            perf_json = args[2]
            out = args[3] if len(args) >= 4 else None
        else:
            out = args[2]
    generate_html(before, after, perf_json, out)
