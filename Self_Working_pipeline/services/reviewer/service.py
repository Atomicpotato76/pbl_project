from __future__ import annotations

from pydantic import BaseModel

from contracts.models import (
    ExecutionResult,
    PlanBundle,
    ReviewIssue,
    ReviewReport,
    VerificationAction,
    VerificationJudgment,
    VerificationVerdict,
)
from core.prompting import compose_system_prompt
from services.adapters.base import JsonModelAdapter


class ReviewEnvelope(BaseModel):
    report: ReviewReport


class ReviewerService:
    def __init__(self, adapter: JsonModelAdapter, *, guidance_prompt: str = "", mode: str = "code") -> None:
        self.adapter = adapter
        self.guidance_prompt = guidance_prompt
        self.mode = mode

    def review(self, *, execution_result: ExecutionResult, plan_bundle: PlanBundle) -> ReviewReport:
        if self.mode == "research":
            system_prompt = compose_system_prompt(
                (
                    "You are a fact-checker and quality reviewer in a multi-agent investigation pipeline. "
                    "Evaluate research findings for accuracy, source quality, completeness, "
                    "logical consistency, alignment with the investigation plan, and safeguard compliance."
                ),
                self.guidance_prompt,
                section_name="fact-checking, source verification, and research quality standards",
            )
            user_prompt = (
                "Review the investigation results against the plan bundle.\n"
                "Check for:\n"
                "- unsupported claims (claims without sources)\n"
                "- conflicting information not flagged by the researcher\n"
                "- missing coverage of required subtopics\n"
                "- logical gaps or non-sequiturs\n"
                "- source quality (prefer academic, official, and authoritative sources)\n"
                "- scope drift beyond the assigned MC1-1 stage\n"
                "- MC1-1c new-data or new-source violations when the final recommendation should only reuse locked evidence\n"
                "- whether human lock or external verification is required before proceeding\n"
                "Return a ReviewReport and populate report.judgment using these exact enum values:\n"
                "- final_verdict: pass | fail | escalate | block\n"
                "- final_action: proceed | retry_workstream | request_external_verification | request_human_lock\n"
                "- requires_human_lock\n"
                "- requires_external_verification\n"
                "- evidence_quality_fail\n"
                "- scope_violation\n"
                "- new_data_forbidden_violation\n"
                "- retry_recommended\n"
                "- rationale\n"
                "Set approved=true only when final_verdict=pass and final_action=proceed.\n"
                "Return JSON only.\n\n"
                f"Plan bundle:\n{plan_bundle.model_dump_json(indent=2)}\n\n"
                f"Research results:\n{execution_result.model_dump_json(indent=2)}"
            )
        else:
            system_prompt = compose_system_prompt(
                (
                    "You are Claude Code acting as a reviewer. Evaluate generated files for correctness, "
                    "scope control, maintainability, and alignment with the contract."
                ),
                self.guidance_prompt,
                section_name="review, testing discipline, repository expectations, and safety rules",
            )
            user_prompt = (
                "Review the implementation against the plan bundle.\n"
                "Return a ReviewReport and populate report.judgment using these exact enum values:\n"
                "- final_verdict: pass | fail | escalate | block\n"
                "- final_action: proceed | retry_workstream | request_external_verification | request_human_lock\n"
                "For code review, keep safeguard flags false unless there is a real scope or human-lock issue.\n"
                "Approve only when the workstream is complete, scoped correctly, and still follows any user additions in plan_bundle.change_log.\n"
                "Return JSON only.\n\n"
                f"Plan bundle:\n{plan_bundle.model_dump_json(indent=2)}\n\n"
                f"Execution result:\n{execution_result.model_dump_json(indent=2)}"
            )
        result = self.adapter.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ReviewEnvelope,
        )
        assert isinstance(result, ReviewEnvelope)
        return self._normalize_report(
            report=result.report,
            execution_result=execution_result,
            plan_bundle=plan_bundle,
        )

    def _normalize_report(
        self,
        *,
        report: ReviewReport,
        execution_result: ExecutionResult,
        plan_bundle: PlanBundle,
    ) -> ReviewReport:
        if self.mode == "research":
            judgment = self._normalize_research_judgment(
                report=report,
                execution_result=execution_result,
                plan_bundle=plan_bundle,
            )
        else:
            judgment = self._normalize_code_judgment(report=report)
        approved = self._is_approved(report=report, judgment=judgment)
        return report.model_copy(update={"approved": approved, "judgment": judgment})

    def _normalize_research_judgment(
        self,
        *,
        report: ReviewReport,
        execution_result: ExecutionResult,
        plan_bundle: PlanBundle,
    ) -> VerificationJudgment:
        existing = report.judgment
        research_report = execution_result.research_report
        workstream = next((item for item in plan_bundle.workstreams if item.id == execution_result.workstream_id), None)
        is_final_recommendation = self._is_final_recommendation(execution_result.workstream_id, workstream.objective if workstream else "")

        evidence_quality_fail = False
        scope_violation = self._issues_contain(
            report.issues,
            "scope drift",
            "out of scope",
            "out-of-scope",
            "beyond assigned",
            "outside assigned",
            "outside the assigned",
        )
        new_data_forbidden_violation = self._issues_contain(
            report.issues,
            "new data",
            "new source",
            "new evidence",
            "fresh data",
        )
        requires_external_verification = False
        requires_human_lock = False
        rationale_parts = [existing.rationale.strip(), report.summary.strip()]

        if research_report is None:
            evidence_quality_fail = True
            rationale_parts.append("Research report payload is missing.")
        else:
            source_ids = {source.source_id for source in research_report.sources}
            missing_source_links = any(
                self._claim_requires_source_link(claim) and (
                    not claim.source_ids or any(source_id not in source_ids for source_id in claim.source_ids)
                )
                for claim in research_report.claims
            )
            missing_source_metadata = any(
                (not any([source.url, source.doi, source.pmid, source.accession]))
                or not source.source_type.strip()
                or not source.tier.strip()
                for source in research_report.sources
            )
            unresolved_conflicts = any(not conflict.resolution.strip() for conflict in research_report.conflicts)
            contested_claims = any(
                self._claim_requires_external_verification(claim)
                for claim in research_report.claims
            )
            policy_violations = [item.strip().lower() for item in research_report.stage_envelope.policy_violations if item.strip()]
            carry_forward_ids = {
                item.strip().lower()
                for item in research_report.stage_envelope.carry_forward_source_ids
                if item.strip()
            }
            current_source_ids = {
                source.source_id.strip().lower()
                for source in research_report.sources
                if source.source_id.strip()
            }

            evidence_quality_fail = evidence_quality_fail or not research_report.claims or not research_report.sources
            evidence_quality_fail = evidence_quality_fail or missing_source_links or missing_source_metadata
            evidence_quality_fail = evidence_quality_fail or self._issues_contain(
                report.issues,
                "unsupported",
                "citation",
                "source",
                "evidence",
                "claim-source",
            )
            scope_violation = scope_violation or any("scope" in item for item in policy_violations)
            new_data_forbidden_violation = new_data_forbidden_violation or any(
                keyword in item
                for item in policy_violations
                for keyword in ("new_data", "new data", "new_source", "new source")
            )
            if is_final_recommendation and carry_forward_ids and not current_source_ids.issubset(carry_forward_ids):
                new_data_forbidden_violation = True
                rationale_parts.append("MC1-1c output introduced source_ids outside the declared carry-forward set.")
            requires_external_verification = requires_external_verification or contested_claims or unresolved_conflicts
            if missing_source_links:
                rationale_parts.append("At least one claim is missing source linkage.")
            if missing_source_metadata:
                rationale_parts.append("At least one source is missing identifiers, source_type, or tier.")
            if contested_claims or unresolved_conflicts:
                rationale_parts.append("Contested claims or unresolved conflicts require external verification.")

        if new_data_forbidden_violation or scope_violation:
            requires_human_lock = True

        final_verdict, final_action = self._resolve_research_outcome(
            report=report,
            evidence_quality_fail=evidence_quality_fail,
            scope_violation=scope_violation,
            new_data_forbidden_violation=new_data_forbidden_violation,
            requires_external_verification=requires_external_verification,
            requires_human_lock=requires_human_lock,
        )
        return existing.model_copy(
            update={
                "final_verdict": final_verdict,
                "final_action": final_action,
                "requires_human_lock": requires_human_lock,
                "requires_external_verification": requires_external_verification,
                "evidence_quality_fail": evidence_quality_fail,
                "scope_violation": scope_violation,
                "new_data_forbidden_violation": new_data_forbidden_violation,
                "retry_recommended": final_action == VerificationAction.retry_workstream,
                "rationale": self._join_parts(rationale_parts),
            }
        )

    def _normalize_code_judgment(self, *, report: ReviewReport) -> VerificationJudgment:
        existing = report.judgment
        scope_violation = existing.scope_violation or self._issues_contain(
            report.issues,
            "scope",
            "out of scope",
            "out-of-scope",
            "unrelated",
        )
        requires_human_lock = existing.requires_human_lock
        if scope_violation:
            final_verdict = VerificationVerdict.fail
            final_action = VerificationAction.retry_workstream
        elif requires_human_lock:
            final_verdict = VerificationVerdict.escalate
            final_action = VerificationAction.request_human_lock
        elif report.approved:
            final_verdict = VerificationVerdict.pass_
            final_action = VerificationAction.proceed
        else:
            final_verdict = VerificationVerdict.fail
            final_action = VerificationAction.retry_workstream
        return existing.model_copy(
            update={
                "final_verdict": final_verdict,
                "final_action": final_action,
                "scope_violation": scope_violation,
                "retry_recommended": final_action == VerificationAction.retry_workstream,
                "rationale": self._join_parts([existing.rationale.strip(), report.summary.strip()]),
            }
        )

    def _resolve_research_outcome(
        self,
        *,
        report: ReviewReport,
        evidence_quality_fail: bool,
        scope_violation: bool,
        new_data_forbidden_violation: bool,
        requires_external_verification: bool,
        requires_human_lock: bool,
    ) -> tuple[VerificationVerdict, VerificationAction]:
        if new_data_forbidden_violation or scope_violation:
            return VerificationVerdict.block, VerificationAction.request_human_lock
        if evidence_quality_fail:
            return VerificationVerdict.fail, VerificationAction.retry_workstream
        if requires_external_verification:
            return VerificationVerdict.escalate, VerificationAction.request_external_verification
        if requires_human_lock:
            return VerificationVerdict.escalate, VerificationAction.request_human_lock
        if report.approved:
            return VerificationVerdict.pass_, VerificationAction.proceed
        return VerificationVerdict.fail, VerificationAction.retry_workstream

    @staticmethod
    def _is_approved(*, report: ReviewReport, judgment: VerificationJudgment) -> bool:
        if judgment.final_verdict != VerificationVerdict.pass_:
            return False
        if judgment.final_action != VerificationAction.proceed:
            return False
        if judgment.requires_human_lock or judgment.requires_external_verification:
            return False
        if judgment.evidence_quality_fail or judgment.scope_violation or judgment.new_data_forbidden_violation:
            return False
        return report.approved or not report.issues

    @staticmethod
    def _issues_contain(issues: list[ReviewIssue], *keywords: str) -> bool:
        lowered_keywords = tuple(keyword.lower() for keyword in keywords)
        for issue in issues:
            haystack = " ".join(
                part.strip().lower()
                for part in (issue.description, issue.suggested_fix)
                if part
            )
            if any(keyword in haystack for keyword in lowered_keywords):
                return True
        return False

    @staticmethod
    def _claim_requires_source_link(claim) -> bool:
        return claim.status.strip().lower() not in {"uncertain", "gap", "open_question", "question"}

    @staticmethod
    def _claim_requires_external_verification(claim) -> bool:
        status = claim.status.strip().lower()
        if status in {"contested", "mixed"}:
            return True
        if status == "uncertain" and claim.source_ids:
            return True
        return False

    @staticmethod
    def _is_final_recommendation(workstream_id: str, objective: str) -> bool:
        haystack = f"{workstream_id} {objective}".lower()
        return "mc1_1c" in haystack or "final recommendation" in haystack or "without collecting new data" in haystack

    @staticmethod
    def _join_parts(parts: list[str]) -> str:
        ordered: list[str] = []
        for part in parts:
            cleaned = part.strip()
            if cleaned and cleaned not in ordered:
                ordered.append(cleaned)
        return " ".join(ordered)
