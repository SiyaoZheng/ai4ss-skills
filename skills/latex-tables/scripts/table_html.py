#!/usr/bin/env python3
"""
table_html.py — LaTeX booktabs table → self-contained split-panel HTML preview.

Usage:
    python3 table_html.py table.tex [output.html]

If output path is omitted, writes <stem>-preview.html next to the .tex file.
No external dependencies.

Design: "Audit Panel" — split view, left = syntax-highlighted LaTeX, right = CSS booktabs.
"""

import sys
import re
import html as html_mod
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
  --code-bg:    #f1f5f9;
  --row-alt:    #fafafa;
  --rule-heavy: 2px solid #0f172a;
  --rule-light: 1px solid #0f172a;
}
body {
  font-family: system-ui, -apple-system, 'Inter', sans-serif;
  font-size: 14px;
  color: var(--text);
  background: var(--bg);
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.topbar {
  height: 48px;
  flex-shrink: 0;
  background: #0f172a;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
}
.topbar-title { color: #94a3b8; font-size: 13px; }
.topbar-skill { color: var(--accent); font-weight: 600; }
.topbar-ts { color: #64748b; font-size: 12px; margin-left: auto; font-family: 'JetBrains Mono', monospace; }

.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
.toolbar-label { font-size: 13px; color: var(--text-muted); margin-right: auto; }
.toggle-btn {
  padding: 5px 12px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg);
  font-size: 12px;
  cursor: pointer;
  color: var(--text-muted);
  font-family: inherit;
  transition: all .15s;
}
.toggle-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.toggle-btn:hover:not(.active) { border-color: var(--accent); color: var(--accent); }

.panels {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}
.panels.code-only .panel-preview { display: none; }
.panels.code-only .panel-code { flex: 1; }
.panels.preview-only .panel-code { display: none; }
.panels.preview-only .panel-preview { flex: 1; }

.panel-code {
  flex: 1;
  overflow-y: auto;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
}
.panel-header {
  padding: 10px 16px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--text-muted);
  font-weight: 600;
}
.code-block {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--code-bg);
}
.code-block pre {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12.5px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-all;
}

/* Syntax highlight classes */
.kw  { color: var(--accent); }          /* backslash commands */
.num { color: #0369a1; }                /* numbers */
.str { color: #059669; }                /* string args */
.cmt { color: var(--text-muted); }      /* % comments */
.star { color: #d97706; font-weight: 600; } /* * ** *** */

.panel-preview {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.preview-body {
  flex: 1;
  overflow-y: auto;
  padding: 32px 40px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

/* ── CSS booktabs ── */
.booktabs-table {
  border-collapse: collapse;
  font-size: 13.5px;
  font-family: 'JetBrains Mono', monospace;
  min-width: 400px;
}
.booktabs-table thead tr:first-child { border-top: var(--rule-heavy); }
.booktabs-table thead tr:last-child  { border-bottom: var(--rule-light); }
.booktabs-table tbody tr:last-child  { border-bottom: var(--rule-heavy); }
.booktabs-table th, .booktabs-table td {
  padding: 5px 16px;
  text-align: right;
  white-space: nowrap;
}
.booktabs-table th:first-child,
.booktabs-table td:first-child { text-align: left; }
.booktabs-table thead th {
  font-weight: 600;
  font-family: system-ui, sans-serif;
  font-size: 13px;
}
.midrule { border-top: var(--rule-light); }
.booktabs-table tr:nth-child(even) td { background: var(--row-alt); }
.table-notes {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
  max-width: 640px;
}

.footer {
  height: 36px;
  flex-shrink: 0;
  background: var(--surface);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 20px;
  font-size: 12px;
  color: var(--text-muted);
}
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

@media (max-width: 768px) {
  .panels { flex-direction: column; }
  .panel-code { border-right: none; border-bottom: 1px solid var(--border); max-height: 45vh; }
  .panels.code-only .panel-code { max-height: none; }
}
"""

JS = r"""
const panels = document.getElementById('panels');
document.querySelectorAll('.toggle-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    panels.className = 'panels ' + btn.dataset.mode;
  });
});
"""


def highlight_latex(src: str) -> str:
    """Apply syntax highlighting classes to LaTeX source."""
    result = []
    i = 0
    while i < len(src):
        c = src[i]
        if c == '%':
            # comment to end of line
            end = src.find('\n', i)
            end = end if end != -1 else len(src)
            snippet = html_mod.escape(src[i:end])
            result.append(f'<span class="cmt">{snippet}</span>')
            i = end
        elif c == '\\':
            # LaTeX command
            j = i + 1
            while j < len(src) and (src[j].isalpha() or src[j] == '@'):
                j += 1
            cmd = html_mod.escape(src[i:j])
            result.append(f'<span class="kw">{cmd}</span>')
            i = j
        elif c == '$':
            # math mode — just color until closing $
            j = i + 1
            while j < len(src) and src[j] != '$':
                j += 1
            snippet = html_mod.escape(src[i:j+1])
            result.append(f'<span class="num">{snippet}</span>')
            i = j + 1
        else:
            # check for significance stars
            if c == '*':
                j = i
                while j < len(src) and src[j] == '*':
                    j += 1
                stars = html_mod.escape(src[i:j])
                result.append(f'<span class="star">{stars}</span>')
                i = j
            else:
                result.append(html_mod.escape(c))
                i += 1
    return ''.join(result)


def parse_tabular(tex: str):
    """
    Extract rows from a tabular environment.
    Returns (headers, body_rows, notes) where each row is a list of cell strings.
    """
    # Find tabular body
    m = re.search(r'\\begin\{tabular\}[^}]*\}(.*?)\\end\{tabular\}', tex, re.DOTALL)
    if not m:
        return [], [], ""
    body = m.group(1)

    # Extract notes (content after \end{tabular} or in \footnotesize etc.)
    notes_m = re.search(r'\\footnotesize\{([^}]+)\}|\\emph\{([^}]+)\}', tex[m.end():])
    notes = ""
    if notes_m:
        notes = notes_m.group(1) or notes_m.group(2) or ""

    # Build a flat list of logical lines by splitting on \\ then re-splitting
    # each chunk into individual lines.  This prevents rules and data rows that
    # share the same \\ segment from being processed as a single unit.
    chunks = re.split(r'\\\\', body)
    lines: list[str] = []
    for chunk in chunks:
        for line in chunk.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)

    headers: list[list[str]] = []
    body_rows: list[list[str]] = []
    in_header = True
    midrule_after: set[int] = set()

    for line in lines:
        if re.match(r'\\(top|mid|bottom)rule', line) or line.startswith('\\hline'):
            if line.startswith('\\midrule') and body_rows:
                midrule_after.add(len(body_rows) - 1)
            if line.startswith('\\toprule'):
                in_header = True
            elif line.startswith('\\midrule'):
                in_header = False
            continue
        # Skip pure-LaTeX control lines (begin/end tabular etc.)
        if re.match(r'\\(begin|end)\{', line):
            continue
        # Split cells on &
        cells = [re.sub(r'\s+', ' ', c.strip()) for c in line.split('&')]
        cells = [re.sub(r'\\.*?\{([^}]*)\}', r'\1', c) for c in cells]  # strip simple cmds
        cells = [c.strip() for c in cells]
        if not any(c for c in cells):
            continue
        if in_header and not body_rows:
            headers.append(cells)
            in_header = False
        else:
            body_rows.append(cells)

    return headers, body_rows, notes


def render_table(headers, body_rows, notes) -> str:
    if not headers and not body_rows:
        return '<p style="color:#64748b;padding:16px">Could not parse table structure from LaTeX source.</p>'

    thead = ""
    if headers:
        for row in headers:
            cells = "".join(f"<th>{html_mod.escape(c)}</th>" for c in row)
            thead += f"<tr>{cells}</tr>"

    tbody = ""
    for i, row in enumerate(body_rows):
        cls = ""
        cells = "".join(f"<td>{html_mod.escape(c)}</td>" for c in row)
        tbody += f"<tr class='{cls}'>{cells}</tr>"

    notes_html = f'<div class="table-notes">{html_mod.escape(notes)}</div>' if notes else ""

    return f"""<table class="booktabs-table">
  <thead>{thead}</thead>
  <tbody>{tbody}</tbody>
</table>
{notes_html}"""


def generate_html(input_path: str, output_path: str | None = None) -> None:
    src = Path(input_path)
    if not src.exists():
        sys.exit(f"Error: file not found: {input_path}")
    if output_path is None:
        output_path = str(src.parent / (src.stem + "-preview.html"))

    tex_src = src.read_text(encoding="utf-8")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    stem = src.stem

    highlighted_code = highlight_latex(tex_src)
    headers, body_rows, notes = parse_tabular(tex_src)
    table_html = render_table(headers, body_rows, notes)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html_mod.escape(stem)} — LaTeX Preview</title>
<style>{CSS}</style>
</head>
<body>

<div class="topbar">
  <span class="topbar-title">ai4ss-skills · <span class="topbar-skill">latex-tables</span></span>
  <span class="topbar-title" style="color:#64748b">·</span>
  <span class="topbar-title">{html_mod.escape(stem)}</span>
  <span class="topbar-ts">{ts}</span>
</div>

<div class="toolbar">
  <span class="toolbar-label">{html_mod.escape(src.name)}</span>
  <button class="toggle-btn active" data-mode="split">⇄ Split</button>
  <button class="toggle-btn" data-mode="code-only">◀ Code</button>
  <button class="toggle-btn" data-mode="preview-only">▶ Preview</button>
</div>

<div class="panels split" id="panels">

  <div class="panel-code">
    <div class="panel-header">Raw LaTeX</div>
    <div class="code-block">
      <pre>{highlighted_code}</pre>
    </div>
  </div>

  <div class="panel-preview">
    <div class="panel-header">Rendered Preview (CSS booktabs)</div>
    <div class="preview-body">
      {table_html}
    </div>
  </div>

</div>

<div class="footer">
  Generated by ai4ss-skills latex-tables · {ts}
</div>

<script>{JS}</script>
</body>
</html>"""

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"Written: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 table_html.py table.tex [output.html]")
        sys.exit(1)
    generate_html(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
