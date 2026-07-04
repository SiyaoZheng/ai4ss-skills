#!/usr/bin/env python3
"""
codebook_html.py — DDI metadata YAML → self-contained interactive HTML codebook.

Usage:
    python3 codebook_html.py ddi-metadata.yaml [output.html]

If output path is omitted, writes <stem>-codebook.html next to the YAML file.
No external dependencies beyond PyYAML (pip install pyyaml).

Design: "Audit Panel" — tech-minimalist, cold palette.
See DESIGN.md for full spec.
"""

import sys
import yaml
import json
import html as html_mod
from pathlib import Path
from datetime import datetime

# ── CSS (inline, all design tokens here) ─────────────────────────────────────
CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:          #ffffff;
  --surface:     #f8f9fa;
  --border:      #e2e8f0;
  --text:        #0f172a;
  --text-muted:  #64748b;
  --accent:      #2563eb;
  --warn:        #f59e0b;
  --ok:          #22c55e;
  --critical:    #ef4444;
  --code-bg:     #f1f5f9;
  --row-alt:     #fafafa;
  --warn-bg:     #fffbeb;
  --warn-border: #fde68a;
  --crit-bg:     #fff1f2;
  --crit-border: #fecaca;
  --ok-bg:       #f0fdf4;
  --ok-border:   #bbf7d0;
}

body {
  font-family: system-ui, -apple-system, 'Inter', sans-serif;
  font-size: 14px;
  color: var(--text);
  background: var(--bg);
  line-height: 1.5;
}

/* ── Top bar ── */
.topbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 48px;
  background: #0f172a;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
  z-index: 100;
}
.topbar-title {
  color: #94a3b8;
  font-size: 13px;
  letter-spacing: .02em;
}
.topbar-skill {
  color: var(--accent);
  font-weight: 600;
}
.topbar-sep { color: #334155; }
.topbar-ts {
  color: #64748b;
  font-size: 12px;
  margin-left: auto;
  font-family: 'JetBrains Mono', monospace;
}

/* ── Stat strip ── */
.stat-strip {
  margin-top: 48px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  gap: 0;
}
.stat-card {
  flex: 1;
  padding: 16px 24px;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-card:last-child { border-right: none; }
.stat-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}
.stat-num.accent  { color: var(--accent); }
.stat-num.warn    { color: var(--warn); }
.stat-num.critical { color: var(--critical); }
.stat-num.ok      { color: var(--ok); }
.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: .06em;
}

/* ── Layout ── */
.layout {
  display: flex;
  height: calc(100vh - 48px - 69px); /* full height minus topbar and stat strip */
  overflow: hidden;
}

/* ── Sidebar ── */
.sidebar {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-search {
  padding: 12px;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.search-input {
  width: 100%;
  padding: 7px 10px;
  min-height: 36px;
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 13px;
  font-family: inherit;
  color: var(--text);
  background: var(--bg);
  outline: none;
}
.search-input:focus { border-color: var(--accent); }
.filter-row {
  display: flex;
  gap: 4px;
}
.filter-btn {
  flex: 1;
  padding: 8px 0;
  min-height: 36px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  font-size: 11px;
  cursor: pointer;
  color: var(--text-muted);
  font-family: inherit;
  transition: all .15s;
}
.filter-btn:hover { border-color: var(--accent); color: var(--accent); }
.filter-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.var-list {
  overflow-y: auto;
  flex: 1;
}
.var-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background .1s;
}
.var-item:hover { background: #f1f5f9; }
.var-item.active {
  border-left-color: var(--accent);
  background: #eff6ff;
}
.var-item.hidden { display: none; }
.var-flag { font-size: 13px; width: 18px; flex-shrink: 0; }
.var-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.var-label-small {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Detail panel ── */
.detail {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}
.detail-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  font-size: 15px;
}
.var-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 6px;
}
.var-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
}
.var-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
}
.badge-ok       { background: var(--ok-bg);   color: #15803d; border: 1px solid var(--ok-border); }
.badge-warn     { background: var(--warn-bg);  color: #92400e; border: 1px solid var(--warn-border); }
.badge-critical { background: var(--crit-bg);  color: #991b1b; border: 1px solid var(--crit-border); }
.var-full-label { color: var(--text-muted); font-size: 14px; margin-bottom: 20px; }

.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}
.meta-cell {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px 12px;
}
.meta-key {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.meta-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: var(--text);
}

/* ── Alert box ── */
.alert {
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 20px;
  border-left: 4px solid;
}
.alert-warn     { background: var(--warn-bg);  border-color: var(--warn); }
.alert-critical { background: var(--crit-bg);  border-color: var(--critical); }
.alert-ok       { background: var(--ok-bg);    border-color: var(--ok); }
.alert-title {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 4px;
}
.alert-body { font-size: 13px; color: var(--text); }

/* ── Value labels table ── */
.section-title {
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-muted);
  margin-bottom: 10px;
  margin-top: 24px;
}
.val-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}
.val-table th {
  background: var(--surface);
  padding: 8px 12px;
  text-align: left;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}
.val-table td {
  padding: 7px 12px;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}
.val-table tr:last-child td { border-bottom: none; }
.val-table tr:nth-child(even) td { background: var(--row-alt); }
.code-val {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--accent);
  white-space: nowrap;
}
.miss-badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  background: var(--crit-bg);
  color: #991b1b;
  border: 1px solid var(--crit-border);
}
.valid-badge {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  background: var(--ok-bg);
  color: #15803d;
  border: 1px solid var(--ok-border);
}

/* ── Footer ── */
.footer {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: 36px;
  background: var(--surface);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 20px;
  font-size: 12px;
  color: var(--text-muted);
  z-index: 100;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

@media print {
  .topbar, .footer { display: none; }
  .layout { height: auto; overflow: visible; }
  .sidebar { display: none; }
}

@media (max-width: 768px) {
  .layout { flex-direction: column; height: auto; }
  .sidebar { width: 100%; border-right: none; border-bottom: 1px solid var(--border); max-height: 40vh; }
  .stat-strip { flex-wrap: wrap; }
  .stat-card { flex: 0 0 50%; border-right: none; border-bottom: 1px solid var(--border); }
  .detail { padding: 16px 20px; }
  .meta-grid { grid-template-columns: repeat(2, 1fr); }
}
"""

JS = r"""
const vars = JSON.parse(document.getElementById('var-data').textContent);
const items = document.querySelectorAll('.var-item');
const detail = document.getElementById('detail-content');
const searchInput = document.getElementById('search-input');
let activeFilter = 'all';
let activeIdx = -1;

function flagFor(v) {
  const flags = v._parse_flags || [];
  if (flags.some(f => f.includes('missing_codes_inferred') || f.includes('type_uncertain'))) return 'warn';
  if (flags.some(f => f.includes('critical') || f.includes('inapplicable_structural'))) return 'critical';
  return 'ok';
}

function renderDetail(v) {
  // Remove .detail-empty class so block layout is restored (flex was for the placeholder)
  detail.className = '';
  const flag = flagFor(v);
  const flags = v._parse_flags || [];
  const codes = (v.representation && v.representation.codes) || {};
  const missCodes = (v.missing && v.missing.codes) || {};

  let alertHtml = '';
  if (flag === 'warn') {
    alertHtml = `<div class="alert alert-warn">
      <div class="alert-title">⚠️ Positive-Missing Trap</div>
      <div class="alert-body">val_labels() shows this variable may contain valid codes that resemble missing codes.
        Verify each code individually before recoding. Flags: ${flags.join(', ') || '(none)'}</div>
    </div>`;
  } else if (flag === 'critical') {
    alertHtml = `<div class="alert alert-critical">
      <div class="alert-title">🔴 Critical — Review Required</div>
      <div class="alert-body">Flags: ${flags.join(', ') || '(none)'}</div>
    </div>`;
  }

  const metaFields = [
    ['Type', (v.representation && v.representation.type) || '—'],
    ['Storage', (v.representation && v.representation.storage_type) || '—'],
    ['Concept', v.concept || '—'],
    ['Unit', v.unit_type || '—'],
    ['Temporal', v.is_temporal ? 'Yes' : 'No'],
    ['Geographic', v.is_geographic ? 'Yes' : 'No'],
    ['Weight var', v.is_weight ? 'Yes' : 'No'],
  ];
  const metaHtml = metaFields.map(([k, val]) =>
    `<div class="meta-cell"><div class="meta-key">${k}</div><div class="meta-val">${esc(String(val))}</div></div>`
  ).join('');

  // Value labels table
  let valRows = '';
  const allCodes = {...codes};
  Object.entries(missCodes).forEach(([k, v2]) => {
    allCodes[k] = allCodes[k] || (v2.label || String(k));
  });

  for (const [code, label] of Object.entries(allCodes)) {
    const isMiss = Object.prototype.hasOwnProperty.call(missCodes, code);
    const badge = isMiss
      ? `<span class="miss-badge">missing</span>`
      : `<span class="valid-badge">valid</span>`;
    valRows += `<tr>
      <td class="code-val">${esc(String(code))}</td>
      <td>${esc(String(label))}</td>
      <td>${badge}</td>
    </tr>`;
  }

  const valTable = valRows ? `
    <div class="section-title">Value Labels</div>
    <table class="val-table">
      <thead><tr><th>Code</th><th>Label</th><th>Classification</th></tr></thead>
      <tbody>${valRows}</tbody>
    </table>` : '';

  const badgeClass = flag === 'ok' ? 'badge-ok' : flag === 'warn' ? 'badge-warn' : 'badge-critical';
  const badgeText = flag === 'ok' ? '✓ Clean' : flag === 'warn' ? '⚠ Review' : '🔴 Critical';

  detail.innerHTML = `
    <div class="var-header">
      <div class="var-title">${esc(v.name || v.id || '?')}</div>
      <span class="var-badge ${badgeClass}">${badgeText}</span>
    </div>
    <div class="var-full-label">${esc(v.label || '(no label)')}</div>
    ${alertHtml}
    <div class="meta-grid">${metaHtml}</div>
    ${valTable}
  `;
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function matchesFilter(v, f) {
  if (f === 'all') return true;
  const flag = flagFor(v);
  return flag === f;
}

function updateList() {
  const q = searchInput.value.toLowerCase();
  items.forEach((el, i) => {
    const v = vars[i];
    const name = (v.name || v.id || '').toLowerCase();
    const label = (v.label || '').toLowerCase();
    const visible = matchesFilter(v, activeFilter) && (!q || name.includes(q) || label.includes(q));
    el.classList.toggle('hidden', !visible);
  });
}

items.forEach((el, i) => {
  el.addEventListener('click', () => {
    items.forEach(x => x.classList.remove('active'));
    el.classList.add('active');
    activeIdx = i;
    renderDetail(vars[i]);
  });
});

searchInput.addEventListener('input', updateList);

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    updateList();
  });
});

// Select first visible on load
if (items.length > 0) { items[0].click(); }
"""


def flag_for(var: dict) -> str:
    flags = var.get("_parse_flags", []) or []
    if any("critical" in f or "inapplicable_structural" in f for f in flags):
        return "critical"
    if any("missing_codes_inferred" in f or "type_uncertain" in f or "codes_incomplete" in f for f in flags):
        return "warn"
    return "ok"


FLAG_ICON = {"ok": "✓", "warn": "⚠️", "critical": "🔴"}


def build_sidebar_items(variables: list) -> str:
    rows = []
    for v in variables:
        flag = flag_for(v)
        name = html_mod.escape(v.get("name") or v.get("id") or "?")
        label = html_mod.escape(v.get("label") or "")
        icon = FLAG_ICON[flag]
        rows.append(
            f'<div class="var-item" data-flag="{flag}">'
            f'<span class="var-flag">{icon}</span>'
            f'<div><div class="var-name">{name}</div>'
            f'<div class="var-label-small">{label}</div></div>'
            f'</div>'
        )
    return "\n".join(rows)


def generate_html(input_path: str, output_path: str | None = None) -> None:
    src = Path(input_path)
    if not src.exists():
        sys.exit(f"Error: file not found: {input_path}")

    with src.open(encoding="utf-8") as f:
        meta = yaml.safe_load(f) or {}

    if output_path is None:
        output_path = str(src.parent / (src.stem + "-codebook.html"))

    variables = meta.get("variables") or []
    study = meta.get("study") or {}
    study_name = study.get("name") or src.stem
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    n_total = len(variables)
    n_warn = sum(1 for v in variables if flag_for(v) == "warn")
    n_critical = sum(1 for v in variables if flag_for(v) == "critical")
    n_ok = n_total - n_warn - n_critical

    sidebar_items = build_sidebar_items(variables)
    var_json = json.dumps(variables, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html_mod.escape(study_name)} — Codebook</title>
<style>{CSS}</style>
</head>
<body>

<div class="topbar">
  <span class="topbar-title">ai4ss-skills · <span class="topbar-skill">codebook-parse</span></span>
  <span class="topbar-sep">·</span>
  <span class="topbar-title">{html_mod.escape(study_name)}</span>
  <span class="topbar-ts">{ts}</span>
</div>

<div class="stat-strip">
  <div class="stat-card">
    <div class="stat-num accent">{n_total}</div>
    <div class="stat-label">Variables</div>
  </div>
  <div class="stat-card">
    <div class="stat-num warn">{n_warn}</div>
    <div class="stat-label">⚠ Flagged</div>
  </div>
  <div class="stat-card">
    <div class="stat-num critical">{n_critical}</div>
    <div class="stat-label">🔴 Critical</div>
  </div>
  <div class="stat-card">
    <div class="stat-num ok">{n_ok}</div>
    <div class="stat-label">✓ Clean</div>
  </div>
</div>

<div class="layout">
  <div class="sidebar">
    <div class="sidebar-search">
      <input type="search" class="search-input" id="search-input" placeholder="Search variables…">
      <div class="filter-row">
        <button class="filter-btn active" data-filter="all">All</button>
        <button class="filter-btn" data-filter="warn">⚠ Flagged</button>
        <button class="filter-btn" data-filter="critical">🔴 Critical</button>
        <button class="filter-btn" data-filter="ok">✓ Clean</button>
      </div>
    </div>
    <div class="var-list" id="var-list">
      {sidebar_items}
    </div>
  </div>

  <div class="detail" id="detail-panel">
    <div class="detail-empty" id="detail-content">
      Select a variable to view details.
    </div>
  </div>
</div>

<div class="footer">
  Generated by ai4ss-skills codebook-parse · {ts} · {n_total} variables · {n_warn} flagged · {n_critical} critical
</div>

<script id="var-data" type="application/json">{var_json}</script>
<script>{JS}</script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"Written: {output_path}")
    print(f"  {n_total} variables | {n_warn} ⚠ flagged | {n_critical} 🔴 critical | {n_ok} ✓ clean")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 codebook_html.py ddi-metadata.yaml [output.html]")
        sys.exit(1)
    generate_html(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
