# Prompt Pack

Use these prompts for R&R planning and AI-disclosed response working text.

## Intake

```text
Use $reviewer-response.

Inputs:
- editor letter: [path]
- reviewer reports: [path]
- manuscript: [path]
- appendix/tables/figures: [paths]

Task:
1. preserve reviewer numbering;
2. split compound comments into atomic requests;
3. classify each request;
4. assign status;
5. identify evidence needed;
6. list revision choices and assumptions to disclose.

Do not present any AI-assisted response text as direct-submission ready or
no-AI. Keep confidentiality, evidence, disclosure, and direct-submission status
visible.
```

## Reviewer-Request Declarations

```text
Use $reviewer-response to build `.aiss` reviewer-request decisions.

For each comment, include:
- comment_id;
- reviewer_text;
- request_type;
- severity;
- status;
- planned_action;
- evidence_needed;
- file_or_section;
- owner;
- done_evidence;
- response_summary;
- revision_choice_status;
- confidentiality_status;
- assumptions_to_disclose.

Record any scope-changing request as a revision choice before drafting.
```

## Evidence Check

```text
Use $reviewer-response to check whether our planned responses are supported.

Inputs:
- `.aiss` reviewer-request decisions: [path]
- revised manuscript: [path]
- new tables/figures/appendices: [paths]

For each reviewer-request decision, check:
- does the promised change exist?
- is table/figure number current?
- does response logic match evidence?
- are unsupported claims present?
- is any item still missing a revision choice?
```

## Response Working Draft

```text
Use $reviewer-response to create AI-disclosed response working drafts.

For each comment, output:
- reviewer concern;
- revision position slot;
- action taken slot;
- evidence/location slot;
- boundary or limitation slot;
- risk note;
- suggested tone;
- AI-assisted working response text;
- disclosure/direct-submission status.
```

## Decline Or Partial Response

```text
Use $reviewer-response for a partial/declined reviewer request.

Request: [paste]
Why it may not be feasible: [reason]
Evidence: [paths]

Return:
- whether this is partial, rebut, cannot_do, or revise_scope;
- what manuscript clarification is needed;
- what evidence supports the boundary;
- AI-disclosed response working draft or scaffold.

Do not mark direct-submission status ready until the revision position,
disclosure, accountability, confidentiality, and policy checks are explicit.
```

## Final Pre-Submission Audit

```text
Use $reviewer-response to audit the response package before submission.

Check:
- every reviewer comment has a matrix row;
- every accept/partial row has done evidence;
- every rebut/cannot_do row has a boundary explanation;
- every row has confidentiality_status before external tool use;
- response scaffolds match revised manuscript;
- no promised analysis is missing;
- any AI-assisted response text is labeled as working text with disclosure,
  accountability, confidentiality, policy, and direct-submission status.
```
