# QA Report — ai4ss-skills companion HTML reports
**Date:** 2026-04-28
**Branch:** main
**Scope:** Three companion HTML report generators added in commit `3094c96`

---

## Summary

| Component | File | Status | Issues Found |
|-----------|------|--------|--------------|
| Codebook Browser | `codebook-parse.skill/scripts/codebook_html.py` | ✅ PASS (after fix) | 1 HIGH |
| LaTeX Table Viewer | `latex-tables.skill/scripts/table_html.py` | ✅ PASS (after fix) | 1 HIGH, 1 LOW |
| Performance Report | `r-performance.skill/scripts/perf_html.py` | ✅ PASS | — |

**All HIGH issues resolved. 1 LOW issue deferred.**

---

## Issues

### ISSUE-001 — Codebook detail panel layout broken (HIGH) ✅ FIXED

**File:** `codebook-parse/scripts/codebook_html.py`
**Commit fixed:** `3e33d35`

**Symptom:** Clicking a variable in the sidebar rendered meta-grid and value-labels
table side-by-side in a horizontal row instead of stacking vertically.

**Root cause:** `#detail-content` div has the `detail-empty` CSS class which sets
`display: flex; align-items: center; justify-content: center` (for the empty-state
placeholder). `renderDetail()` set `innerHTML` without first removing this class,
causing all injected children to become flex items.

**Fix:**
```javascript
function renderDetail(v) {
  // Remove .detail-empty class so block layout is restored
  detail.className = '';
  // ...rest of function
}
```

**Verified:** Screenshot confirmed correct vertical stacking after fix.

---

### ISSUE-002 — LaTeX table parser drops column header and first data row (HIGH) ✅ FIXED

**File:** `latex-tables/scripts/table_html.py`
**Commit fixed:** `3e33d35`

**Symptom:** Rendered preview showed no column headers and the first data row
(e.g. "Education") was missing from the table.

**Root cause:** `parse_tabular()` split the tabular body by `\\` (LaTeX row
terminator), producing chunks like `\toprule\n & (1) & (2) & (3)`. The rule
detection regex `re.match(r'\\(top|mid|bottom)rule', line)` matched the entire
chunk (because the rule is at the start), causing both the rule AND the column
header on the next line of the same chunk to be discarded.

**Fix:** Two-level split — first `re.split(r'\\\\', body)` to get `\\`-terminated
chunks, then `chunk.split('\n')` to get individual lines. Each line is processed
independently so rules and data on adjacent lines in the same chunk are handled
correctly.

```python
chunks = re.split(r'\\\\', body)
lines: list[str] = []
for chunk in chunks:
    for line in chunk.split('\n'):
        line = line.strip()
        if line:
            lines.append(line)
```

**Verified:** Screenshot confirmed column header `(1) (2) (3)` and Education row
both present in rendered preview after fix.

---

### ISSUE-003 — Body `\midrule` not applied in CSS table (LOW) ⏳ DEFERRED

**File:** `latex-tables/scripts/table_html.py`

**Symptom:** Horizontal rule between body row groups (e.g. between OLS and
Logit panel) not rendered in the HTML preview table.

**Root cause:** `parse_tabular()` computes `midrule_after: set[int]` correctly
but it is a local variable — not returned from the function and not consumed by
`render_table()`.

**Fix required:**
```python
# parse_tabular should return midrule_after:
return headers, body_rows, notes, midrule_after

# render_table should accept and apply it:
def render_table(headers, body_rows, notes, midrule_after=None):
    ...
    for i, row in enumerate(body_rows):
        cls = 'midrule' if midrule_after and i in midrule_after else ''
        ...
```

**Status:** Deferred — cosmetic only, doesn't affect data display or correctness.
Tracked for next iteration.

---

## Feature Verification

### Codebook Browser
- [x] Click sidebar variable → detail panel updates
- [x] Search input filters variable list in real time
- [x] Filter buttons (All / ⚠ Flagged / 🔴 Critical / ✓ Clean) work
- [x] Stat strip shows correct counts (3 total, 2 ⚠, 0 🔴, 1 ✓)
- [x] Variable detail shows: title, badge, alert box (warn), meta grid, value labels table
- [x] First variable auto-selected on load
- [x] No JS errors in console

### LaTeX Table Viewer
- [x] Split panel renders (left: syntax-highlighted LaTeX, right: CSS booktabs)
- [x] Toggle buttons: Split / Code / Preview switch layout correctly
- [x] Column headers present
- [x] Data rows present
- [x] LaTeX commands highlighted in accent blue
- [x] Significance stars highlighted in warn amber

### Performance Report
- [x] Speedup banner renders (`12.4×` in 48px accent blue)
- [x] Runtime and Memory metric cards with before/after values and bar charts
- [x] Approach card renders
- [x] Side-by-side code diff with line numbers
- [x] Removed lines highlighted in red tint (#fff1f2)
- [x] Added lines highlighted in green tint (#f0fdf4)
- [x] No JS errors (68 elements, no crash)

---

## Test Artifacts

| File | Purpose |
|------|---------|
| `/tmp/ai4ss-work/test-ddi.yaml` | 3-variable DDI fixture (ok/warn/warn) |
| `/tmp/ai4ss-work/test-table.tex` | AEA-style LaTeX table fixture |
| `/tmp/ai4ss-work/before.R` + `after.R` | R performance comparison fixture |
| `/tmp/ai4ss-work/perf-summary.json` | Perf metrics JSON fixture |
| `/tmp/ai4ss-work/test-codebook.html` | Generated codebook report |
| `/tmp/ai4ss-work/test-table-preview.html` | Generated table preview |
| `/tmp/ai4ss-work/test-perf-report.html` | Generated performance report |

---

## Commits

| Hash | Message |
|------|---------|
| `3094c96` | feat: add companion HTML report generators to all three skills |
| `3e33d35` | fix(qa): ISSUE-001 detail panel flex bug, ISSUE-002 LaTeX parser drops header row |

---

*QA run by /qa skill (zstack). All HIGH issues resolved before ship.*
