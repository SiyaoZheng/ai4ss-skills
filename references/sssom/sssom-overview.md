# SSSOM (Simple Standard for Sharing Ontological Mappings)

> Source: https://mapping-commons.github.io/sssom/
> Paper: https://arxiv.org/abs/2112.07051 (Database, Oxford Academic, 2022)
> Fetched: 2026-04-30

## Summary

SSSOM is a community-driven standard for exchanging **semantic entity mappings** —
a machine-readable format for describing that "entity A in vocabulary X means the
same thing as entity B in vocabulary Y." Designed for ontology alignment but the
pattern generalizes to any crosswalk/mapping scenario.

## Core Data Model

### Mapping class (one row = one mapping record)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `subject_id` | CURIE/URI | Core | Source entity ID |
| `subject_label` | string | Recommended | Human-readable label |
| `subject_source` | URI | Recommended | Source vocabulary |
| `predicate_id` | CURIE | **Required** | Relationship type (e.g. `skos:exactMatch`) |
| `object_id` | CURIE/URI | Core | Target entity ID |
| `object_label` | string | Recommended | Human-readable label |
| `object_source` | URI | Recommended | Target vocabulary |
| `mapping_justification` | CURIE | **Required** | How mapping was determined (e.g. `semapv:ManualMappingCuration`) |
| `confidence` | float 0-1 | Optional | Confidence score |
| `author_id` | CURIE | Optional | Who made the mapping |
| `mapping_date` | date | Optional | When asserted |
| `comment` | string | Optional | Free-text notes |

### MappingSet class (container for a set of mappings)

- `mapping_set_id` — unique identifier
- `creator_id`, `license`, `mapping_date` — set-level metadata
- `curie_map` — prefix→IRI resolution dictionary
- **Propagatable slots** — set-level values that cascade to all mappings
  (e.g. `mapping_tool`, `subject_source`, `object_source`)

### Required fields for any mapping

Only TWO fields are strictly required: `predicate_id` and `mapping_justification`.
The standard posits: "there can be no mapping without some form of justification."

## Mapping Predicates (common)

| Predicate | Meaning |
|-----------|---------|
| `skos:exactMatch` | High-confidence interchangeability |
| `skos:closeMatch` | Sufficiently similar for some applications |
| `skos:broadMatch` | Object is broader than subject |
| `skos:narrowMatch` | Object is narrower than subject |
| `skos:relatedMatch` | Unspecified association |
| `owl:sameAs` | Same individual |
| `owl:equivalentClass` | Same class |

## Mapping Justifications (from SEMAPV vocabulary)

| Justification | Meaning |
|--------------|---------|
| `semapv:ManualMappingCuration` | Human-curated |
| `semapv:LexicalMatching` | String/label-based |
| `semapv:LogicalMatching` | Logic-based |
| `semapv:SemanticSimilarityThresholdMatching` | Embedding similarity |
| `semapv:CompositeMatching` | Multiple methods combined |

## TSV Format

```
# YAML metadata block (lines starting with #)
#curie_map:
#  FOODON: http://purl.obolibrary.org/obo/FOODON_
#mapping_set_id: https://example.org/my-mappings.sssom.tsv
subject_id	subject_label	predicate_id	object_id	object_label	mapping_justification	author_id	confidence
KF_FOOD:F001	apple	skos:exactMatch	FOODON:00002473	apple (whole)	semapv:ManualMappingCuration	orcid:0000-0002-7356-1779	0.95
```

## Key Design Patterns

1. **Subject→Predicate→Object triple** — universal mapping structure
2. **Justification is mandatory** — no mapping without provenance
3. **Confidence scoring** — 0-1 float, enables automated filtering
4. **Propagatable slots** — set-level defaults reduce repetition
5. **CURIE identifiers** — compact, unambiguous, resolvable
6. **Literal mappings** — can map to/from plain strings (not just ontology terms)
7. **Extension mechanism** — `ext_` prefixed custom slots for domain-specific needs
8. **Canonical format** — strict serialization rules for diffability

## Version

- Current: 1.0 (2022)
- Dev: 1.1 (added `similarity_measure` to MappingSet, `sssom_version` slot)

## License

CC-BY 4.0
