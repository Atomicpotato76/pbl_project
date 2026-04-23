from __future__ import annotations

from contracts.models import ExecutionResult, PlanBundle, ReviewReport
from core.prompting import compose_system_prompt
from services.reviewer.service import ReviewEnvelope, ReviewerService


class CrossVerifierService(ReviewerService):
    def review(self, *, execution_result: ExecutionResult, plan_bundle: PlanBundle) -> ReviewReport:
        if self.mode != "research":
            return super().review(execution_result=execution_result, plan_bundle=plan_bundle)

        system_prompt = compose_system_prompt(
            (
                "You are an independent cross-verifier in a multi-agent investigation pipeline. "
                "This stage happens after rescoring and before the final crop lock. "
                "Stress-test the evidence base, challenge the current ranking, and verify that the locked evidence "
                "is strong enough to carry forward into the final recommendation without introducing fresh sources later."
            ),
            self.guidance_prompt,
            section_name="independent cross-verification, evidence triangulation, and final-crop readiness",
        )
        user_prompt = (
            "Perform the external verification pass for this investigation.\n"
            "Your role is different from the normal reviewer:\n"
            "- independently re-check the top claims and cited evidence\n"
            "- confirm whether conflicts were actually resolved or are explicitly bounded\n"
            "- verify that source quality and traceability are strong enough to lock the evidence set\n"
            "- fail the stage when the cross-check is incomplete, weak, or unsupported\n"
            "- request human lock only for scope violations or locked-evidence violations\n"
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
            f"External verification result:\n{execution_result.model_dump_json(indent=2)}"
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
