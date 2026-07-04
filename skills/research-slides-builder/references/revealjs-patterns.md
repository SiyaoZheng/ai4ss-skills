# Reveal.js Patterns

Use this reference when editing single-file reveal.js decks.

## File Discipline

- Inspect the existing HTML before editing.
- Keep one `<section>` per slide.
- Use existing CSS variables and classes.
- Avoid adding external dependencies unless already used or explicitly needed.
- Keep CDN assumptions visible if the deck is not fully offline.

## Slide Anatomy

Recommended structure:

```html
<section data-module="m2">
  <p class="section-title">M2 · 数据与分析</p>
  <h2>One concrete claim</h2>
  <div class="grid-2">
    ...
  </div>
  <p class="source">Source or boundary note.</p>
</section>
```

## Research Evidence Slide

Include:

- title claim;
- visual evidence;
- method/sample note;
- source or output path;
- limitation if central.

Avoid:

- unreadable full tables;
- decorative cards around every section;
- claims unsupported by visible evidence;
- huge code blocks that crowd out interpretation.

## Agentic Teaching Slide

For AI4SS, show the agent loop:

1. task prompt;
2. plan;
3. tool/action;
4. observation;
5. error or uncertainty;
6. repair;
7. output;
8. verification.

The main subject should be agent behavior, not just the statistical result.

## Layout Checks

Before final:

- no text overflow in 16:9 viewport;
- code blocks fit;
- table labels readable;
- figures not clipped;
- source notes visible but not dominant;
- no overlapping nav or footer elements.

## Privacy Checks

Remove unless explicitly approved:

- author real name;
- institution;
- email;
- phone;
- API keys;
- exact confidential file paths;
- screenshots with private account info.

## Local Preview

For single-file CDN reveal.js decks, opening the HTML directly is usually enough. If local browser inspection is available, check:

- first slide loads;
- keyboard navigation works;
- CSS and reveal.js assets load;
- representative dense slides fit.
