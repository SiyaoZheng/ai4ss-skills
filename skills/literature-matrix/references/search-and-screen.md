# Search And Screen Workflow

Use this reference when a literature task requires search, screening, or updating.

## 1. Build Search Strata

Create separate searches for:

- Core concept terms.
- Method terms.
- Outcome terms.
- Geography or institutional context.
- Known author or seminal-paper anchors.

For open-ended topics, create `literature_candidate_discovery.csv` using `candidate-discovery.md` before extracting the matrix.

Example:

```text
("place-based policy" OR "pilot policy" OR "policy pilot")
AND (innovation OR patents OR R&D)
AND (difference-in-differences OR event study OR staggered adoption)
```

Record every query that changes the candidate set.

## 2. Source Hierarchy

Prefer sources in this order:

1. Journal or publisher page.
2. DOI registry or official working-paper repository.
3. Author personal page or institutional page.
4. Preprint server.
5. Citation index or abstracting service.
6. News, blog, or course notes only as pointers, not evidence.

If only a secondary source is available, mark the item `needs_primary_source`.

## 3. Screening Log

For each candidate, record:

- `candidate_id`
- `title`
- `authors`
- `year`
- `source_url`
- `status`: include, exclude, maybe, duplicate, unverified
- `reason`
- `screened_by`
- `screened_at`

Keep excluded but related papers; they are useful for explaining scope.

Do not collapse candidate discovery into screening. Discovery records how a source was found and what still needs verification; screening records whether it belongs in scope after source identity is established.

## 4. Verification Pass

Before treating a paper as evidence:

- Open the primary source or PDF.
- Check title, authors, year, and publication status.
- Confirm the paper actually studies the claimed treatment/exposure and outcome.
- Confirm the identification strategy from methods text, not just abstract keywords.
- Preserve DOI or stable URL.

## 5. Synthesis Boundary

The matrix can state:

- What the paper studies.
- What design and data it uses.
- What result direction it reports.
- What limitation or identification concern is visible.

The matrix should not state:

- "The literature proves..."
- "There is consensus..." unless the user supplies or you verify a review article supporting that claim.
- Unsupported policy implications.
