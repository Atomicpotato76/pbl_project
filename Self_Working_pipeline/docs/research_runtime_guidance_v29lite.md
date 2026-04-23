## Research Runtime Guidance v2.9-lite

Purpose:
- This document bridges the local MC1-1 crop-selection methodology to the runtime schema used by `Self_Working_pipeline`.
- Treat the latest local methodology documents as the operating truth for research behavior.
- When methodology wording and runtime storage differ, keep the methodology semantics but emit data in the runtime schema defined by `contracts/models.py`.

### Fixed MC1-1 flow

Use the fixed four-workstream sequence below. Do not invent extra formal stages.

1. `mc1_1a_scope_and_evidence`
2. `mc1_1b_rescoring_and_top3`
3. `external_verification`
4. `mc1_1c_final_recommendation`

Human locks map to the following checkpoints:
- `scope_lock`: before or at the end of `mc1_1a_scope_and_evidence` when scope assumptions need confirmation
- `top3_lock`: after `mc1_1b_rescoring_and_top3` before final recommendation work proceeds
- `final_crop_lock`: after `mc1_1c_final_recommendation` before the recommendation is treated as final

### Evidence and source policy

- Use authoritative and primary sources first.
- Search tools may help discover candidate sources, but search-result snippets are never enough for high-confidence claims.
- Inspect the underlying source directly before claiming support.
- Every substantive claim must map to `ResearchClaim.source_ids`.
- Every cited `source_id` must resolve to an entry in `ResearchReport.sources`.
- Record gaps explicitly when direct support is missing.
- Record conflicts explicitly in `ResearchReport.conflicts`.
- Separate direct support from inference in claim wording or `notes`.

### Stage-specific constraints

- `mc1_1a_scope_and_evidence` locks scope boundaries, evidence collection rules, and open gaps.
- `mc1_1b_rescoring_and_top3` may compare, score, and rank candidates, but it must stay grounded in the locked evidence set plus any allowed follow-up verification work.
- `external_verification` stress-tests the Top 3 with independent cross-checking and surfaces contested claims.
- `mc1_1c_final_recommendation` must not collect new source material. It synthesizes from the locked evidence set and prior stage outputs only.

### Runtime contract mapping

Do not invent alternate wrapper schemas when returning structured data. Use the repository runtime models.

Required structured payloads:
- `ExecutionResult`
- `ResearchReport`
- `ResearchStageEnvelope`
- `ReviewReport`
- `VerificationJudgment`

Map methodology semantics into runtime fields as follows:
- stage label and stage type -> `ResearchStageEnvelope.stage_name` and `stage_type`
- concise checkpoint summary -> `ResearchStageEnvelope.summary`
- markdown outputs and generated artifacts -> `ResearchStageEnvelope.artifact_paths`
- prior evidence/report dependencies -> `ResearchStageEnvelope.source_paths`
- carry-forward evidence set -> `ResearchStageEnvelope.carry_forward_source_ids`
- unresolved evidence holes -> `ResearchStageEnvelope.known_gaps` and `ResearchReport.gaps`
- policy or guardrail breaks -> `ResearchStageEnvelope.policy_violations`
- final gate reasoning -> `ReviewReport.judgment`

### Review and gate semantics

- Reviews should decide whether the stage can proceed, retry, escalate, or stop for a human lock.
- Use `VerificationJudgment.final_verdict` and `final_action` as the actionable gate outcome.
- Set `requires_human_lock=true` whenever progression depends on `scope_lock`, `top3_lock`, or `final_crop_lock`.
- Set `requires_external_verification=true` when a contested claim or confidence gap must be checked independently.
- If `mc1_1c` introduces new sources, treat that as `new_data_forbidden_violation`.

### Output hygiene

- Write report files under `reports/<workstream_id>.md`.
- Write evidence JSON under `research_evidence/<workstream_id>.json`.
- Keep workstream scope narrow enough for one research session.
- Prefer explicit uncertainty over fabricated completeness.
