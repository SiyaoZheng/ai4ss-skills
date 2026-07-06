# Revision Matrix

Use this schema to make an R&R traceable.

| column | meaning |
|---|---|
| `comment_id` | Reviewer and item id, e.g. `R2.3a` |
| `reviewer_text` | Short quote or paraphrase |
| `request_type` | contribution, conceptual, identification, data, measurement, model, inference, methods, robustness, heterogeneity, literature, writing, formatting, scope |
| `mida_element_affected` | `model`, `inquiry`, `data_strategy`, `answer_strategy`, `diagnose`, `redesign`, `report`, or `not_applicable` |
| `severity` | high, medium, low |
| `status` | accept, partial, clarify, rebut, cannot_do, revise_scope |
| `planned_action` | What will change or be checked |
| `evidence_needed` | Table, figure, source, analysis, or manuscript note |
| `file_or_section` | Manuscript section, appendix, script, table, or figure |
| `owner` | `local_agent` or `project`; writing and manuscript/response text actions must preserve AI disclosure and accountability language |
| `done_evidence` | Output path or manuscript location proving completion |
| `response_summary` | One-sentence reply logic |
| `revision_choice_status` | selected, assumption_disclosed, not_applicable |
| `confidentiality_status` | cleared, redacted, needs_approval, do_not_share; agent-owned or external-tool actions require cleared or redacted |
| `assumptions_to_disclose` | Assumption or boundary still visible in the response |

## Priority

Handle first:

1. Identification threats.
2. Data validity and sample construction.
3. Main-result robustness.
4. Missing literature central to contribution.
5. Wording, organization, and formatting.

## Final Audit

Every `accept` or `partial` item must have `done_evidence`.
Every `rebut` or `cannot_do` item must have a concise reason and, where possible, a manuscript clarification.
Every `revise_scope` item must have a recorded revision choice and manuscript
location before direct-submission status can be marked ready.
Every item using reviewer reports, editor letters, confidential manuscripts, or collaborator comments must have `confidentiality_status` before any external tool use. Rows marked `needs_approval` or `do_not_share` cannot be agent-owned and cannot request external tools.
Every substantive request must map to a MIDA element so revisions do not change the design silently.
