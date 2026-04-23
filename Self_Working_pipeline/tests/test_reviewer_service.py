from __future__ import annotations

from contracts.models import (
    ApiContract,
    ArchitectureSpec,
    ExecutionResult,
    PlanBundle,
    ProjectBrief,
    ResearchClaim,
    ResearchReport,
    ResearchSource,
    ReviewIssue,
    ReviewReport,
    Workstream,
)
from services.reviewer.service import ReviewerService


class _UnusedAdapter:
    def generate_structured(self, **kwargs):  # pragma: no cover - tests call normalization directly
        raise AssertionError("Adapter should not be called in reviewer normalization tests.")


def _research_plan_bundle() -> PlanBundle:
    return PlanBundle(
        project_brief=ProjectBrief(
            title="Research plan",
            objective="Compare candidate crops.",
            audience="Researchers",
            scope=["MC1-1"],
            deliverables=["reports"],
            constraints=["authoritative sources"],
        ),
        architecture_spec=ArchitectureSpec(
            overview="overview",
            components=["reports", "evidence"],
            data_flow=["sources -> evidence -> review"],
            decisions=["structured outputs"],
        ),
        api_contract=ApiContract(interfaces=["CLI"]),
        workstreams=[
            Workstream(
                id="mc1_1a_scope_and_evidence",
                name="MC1-1a Scope And Evidence",
                layer="mc1_1a",
                objective="Lock scope and gather evidence.",
                deliverables=["reports/mc1_1a_scope_and_evidence.md"],
                acceptance_criteria=["scope locked"],
            )
        ],
        test_plan=["validate evidence"],
    )


def _reviewer_service() -> ReviewerService:
    return ReviewerService(_UnusedAdapter(), mode="research")


def test_research_reviewer_does_not_flag_scope_violation_from_file_path_only() -> None:
    service = _reviewer_service()
    plan_bundle = _research_plan_bundle()
    execution = ExecutionResult(
        workstream_id="mc1_1a_scope_and_evidence",
        summary="scope complete",
        files=[],
        research_report=ResearchReport(
            workstream_id="mc1_1a_scope_and_evidence",
            scope="scope",
            claims=[
                ResearchClaim(
                    claim_id="c1",
                    claim="Supported claim",
                    source_ids=["s1"],
                    confidence="high",
                    status="supported",
                )
            ],
            sources=[
                ResearchSource(
                    source_id="s1",
                    title="Authoritative source",
                    url="https://example.com/source",
                    source_type="official",
                    tier="primary",
                )
            ],
        ),
    )
    report = ReviewReport(
        workstream_id="mc1_1a_scope_and_evidence",
        approved=True,
        summary="Looks good overall.",
        issues=[
            ReviewIssue(
                severity="minor",
                description="Schema should be tightened before downstream consumption.",
                file_path="research_evidence/mc1_1a_scope_and_evidence.json",
                suggested_fix="Keep the current structure but clarify the contract.",
            )
        ],
    )

    normalized = service._normalize_report(
        report=report,
        execution_result=execution,
        plan_bundle=plan_bundle,
    )

    assert normalized.approved is True
    assert normalized.judgment.scope_violation is False
    assert normalized.judgment.requires_human_lock is False
    assert normalized.judgment.final_action.value == "proceed"


def test_research_reviewer_treats_uncertain_gap_claim_without_sources_as_gap_not_failure() -> None:
    service = _reviewer_service()
    plan_bundle = _research_plan_bundle()
    execution = ExecutionResult(
        workstream_id="mc1_1a_scope_and_evidence",
        summary="scope complete",
        files=[],
        research_report=ResearchReport(
            workstream_id="mc1_1a_scope_and_evidence",
            scope="scope",
            claims=[
                ResearchClaim(
                    claim_id="c1",
                    claim="Supported claim",
                    source_ids=["s1"],
                    confidence="high",
                    status="supported",
                ),
                ResearchClaim(
                    claim_id="c2",
                    claim="No direct benchmark was identified in this pass.",
                    source_ids=[],
                    confidence="low",
                    status="uncertain",
                    notes="Gap statement, not a positive evidence claim.",
                ),
            ],
            sources=[
                ResearchSource(
                    source_id="s1",
                    title="Authoritative source",
                    url="https://example.com/source",
                    source_type="official",
                    tier="primary",
                )
            ],
            gaps=["No direct benchmark identified."],
        ),
    )
    report = ReviewReport(
        workstream_id="mc1_1a_scope_and_evidence",
        approved=True,
        summary="Pass with explicit gap tracking.",
        issues=[],
    )

    normalized = service._normalize_report(
        report=report,
        execution_result=execution,
        plan_bundle=plan_bundle,
    )

    assert normalized.approved is True
    assert normalized.judgment.evidence_quality_fail is False
    assert normalized.judgment.requires_external_verification is False
    assert normalized.judgment.requires_human_lock is False
    assert normalized.judgment.final_action.value == "proceed"
