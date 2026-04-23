from pathlib import Path
import zipfile

import pytest

from contracts.models import (
    ApiContract,
    ApprovalStage,
    ArchitectureSpec,
    ArtifactManifest,
    ExecutionResult,
    GeneratedFile,
    PlanBundle,
    ProjectBrief,
    ResearchClaim,
    ResearchReport,
    ResearchSource,
    ReviewReport,
    RunStatus,
    SupervisorDecision,
    SupervisorSession,
    TestReport as ValidationTestReport,
    TestResult as ValidationTestResult,
    VerificationAction,
    VerificationJudgment,
    VerificationVerdict,
    Workstream,
)
from tests.helpers import (
    FakeExecutor,
    FakeNotifier,
    FakePlanner,
    FakeReviewer,
    FakeSupervisor,
    build_orchestrator,
    failing_review,
    feature_files,
    passing_review,
    python_app_files,
    sample_plan_bundle,
)


def test_run_requires_plan_approval(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-app",
                name="Build app",
                layer="backend",
                objective="Create the Python app and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            )
        ]
    )
    orchestrator, _memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor({"ws-app": [ExecutionResult(workstream_id="ws-app", summary="done", files=python_app_files())]}),
        reviewer=FakeReviewer({"ws-app": [passing_review("ws-app")]}),
    )
    run = orchestrator.create_plan("build a tiny app")
    with pytest.raises(ValueError):
        orchestrator.run(run.run_id)


def test_happy_path_packages_artifacts(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-app",
                name="Build app",
                layer="backend",
                objective="Create the Python app and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            )
        ]
    )
    executor = FakeExecutor(
        {"ws-app": [ExecutionResult(workstream_id="ws-app", summary="done", files=python_app_files())]}
    )
    reviewer = FakeReviewer({"ws-app": [passing_review("ws-app")]})
    orchestrator, memory = build_orchestrator(tmp_path, planner=FakePlanner(plan), executor=executor, reviewer=reviewer)

    run = orchestrator.create_plan("build a tiny app")
    run = orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    run = orchestrator.run(run.run_id)
    assert run.stage.value == "testing"
    assert run.status.value == "waiting_approval"

    run = orchestrator.approve(run.run_id, stage=ApprovalStage.merge)
    run = orchestrator.run(run.run_id)
    assert run.stage.value == "completed"
    assert run.manifest_path is not None

    manifest_path = Path(run.manifest_path)
    assert manifest_path.exists()
    manifest = ArtifactManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    package_path = Path(manifest.package_path)
    assert package_path.exists()
    with zipfile.ZipFile(package_path) as bundle:
        assert "src/app.py" in bundle.namelist()
        assert "tests/test_app.py" in bundle.namelist()


def test_review_failure_retries_single_workstream(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-app",
                name="Build app",
                layer="backend",
                objective="Create the Python app and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            )
        ]
    )
    executor = FakeExecutor(
        {
            "ws-app": [
                ExecutionResult(workstream_id="ws-app", summary="first draft", files=python_app_files(return_value=0)),
                ExecutionResult(workstream_id="ws-app", summary="fixed", files=python_app_files(return_value=3)),
            ]
        }
    )
    reviewer = FakeReviewer(
        {
            "ws-app": [
                failing_review("ws-app", "Make add(1, 2) return 3."),
                passing_review("ws-app"),
            ]
        }
    )
    orchestrator, memory = build_orchestrator(tmp_path, planner=FakePlanner(plan), executor=executor, reviewer=reviewer)

    run = orchestrator.create_plan("build a tiny app")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    run = orchestrator.run(run.run_id)
    assert run.stage.value == "testing"
    assert run.status.value == "waiting_approval"
    workstream = memory.list_workstreams(run.run_id)[0]
    assert workstream["status"] == "completed"
    assert workstream["retry_count"] == 1
    assert executor.calls["ws-app"] == 2


def test_test_failure_retries_only_impacted_workstream(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-core",
                name="Build core",
                layer="foundation",
                objective="Create shared core utilities.",
                deliverables=["src/core.py"],
                acceptance_criteria=["Core utilities exist"],
            ),
            Workstream(
                id="ws-feature",
                name="Build feature",
                layer="feature",
                objective="Create feature logic and tests.",
                deliverables=["src/feature.py", "tests/test_feature.py"],
                acceptance_criteria=["pytest passes"],
                dependencies=["ws-core"],
            ),
        ]
    )
    executor = FakeExecutor(
        {
            "ws-core": [ExecutionResult(workstream_id="ws-core", summary="core done", files=[feature_files(False)[0]])],
            "ws-feature": [
                ExecutionResult(workstream_id="ws-feature", summary="broken feature", files=feature_files(True)[1:]),
                ExecutionResult(workstream_id="ws-feature", summary="fixed feature", files=feature_files(False)[1:]),
            ],
        }
    )
    reviewer = FakeReviewer(
        {
            "ws-core": [passing_review("ws-core")],
            "ws-feature": [passing_review("ws-feature"), passing_review("ws-feature")],
        }
    )
    orchestrator, memory = build_orchestrator(tmp_path, planner=FakePlanner(plan), executor=executor, reviewer=reviewer)

    run = orchestrator.create_plan("build a feature app")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    run = orchestrator.run(run.run_id)
    assert run.stage.value == "executing"
    assert run.status.value == "waiting_approval"
    run = orchestrator.approve(run.run_id, stage=ApprovalStage.checkpoint)
    run = orchestrator.run(run.run_id)
    assert run.stage.value == "executing"
    assert run.status.value == "waiting_approval"
    run = orchestrator.approve(run.run_id, stage=ApprovalStage.checkpoint)
    run = orchestrator.run(run.run_id)

    assert run.stage.value == "testing"
    assert run.status.value == "waiting_approval"
    assert executor.calls["ws-core"] == 1
    assert executor.calls["ws-feature"] == 2

    workstreams = {item["workstream_id"]: item for item in memory.list_workstreams(run.run_id)}
    assert workstreams["ws-core"]["retry_count"] == 0
    assert workstreams["ws-feature"]["retry_count"] == 0


def test_checkpoint_approval_pauses_between_workstreams(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-one",
                name="Build first step",
                layer="foundation",
                objective="Create the first module.",
                deliverables=["src/core.py"],
                acceptance_criteria=["first file exists"],
            ),
            Workstream(
                id="ws-two",
                name="Build second step",
                layer="application",
                objective="Create the second module and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            ),
        ]
    )
    executor = FakeExecutor(
        {
            "ws-one": [ExecutionResult(workstream_id="ws-one", summary="first", files=[feature_files(False)[0]])],
            "ws-two": [ExecutionResult(workstream_id="ws-two", summary="second", files=python_app_files())],
        }
    )
    reviewer = FakeReviewer({"ws-one": [passing_review("ws-one")], "ws-two": [passing_review("ws-two")]})
    orchestrator, memory = build_orchestrator(tmp_path, planner=FakePlanner(plan), executor=executor, reviewer=reviewer)

    run = orchestrator.create_plan("build in two steps")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    run = orchestrator.run(run.run_id)

    assert run.stage.value == "executing"
    assert run.status.value == "waiting_approval"
    summary = memory.build_checkpoint_summary(run.run_id)
    latest_direction = memory.get_latest_direction(run.run_id)
    latest_stage_narrative = memory.get_latest_stage_narrative(run.run_id)
    assert summary.completed == ["Build first step"]
    assert "checkpoint approval" in summary.overview
    assert summary.latest_stage_name == "foundation"
    assert summary.latest_stage_summary is not None
    assert latest_direction is not None
    assert latest_direction.trigger_event == "stage_completed"
    assert latest_direction.completed_stage == "foundation"
    assert latest_direction.client_summary is not None
    assert latest_stage_narrative is not None
    assert latest_stage_narrative.stage_name == "foundation"

    narrative_path = Path(run.plan_path).parent / "stage_narratives" / "latest_stage.md"
    assert narrative_path.exists()
    assert "## 쉬운 설명" in narrative_path.read_text(encoding="utf-8")

    orchestrator.approve(run.run_id, stage=ApprovalStage.checkpoint)
    run = orchestrator.run(run.run_id)
    assert run.stage.value == "testing"
    assert run.status.value == "waiting_approval"
    latest_direction = memory.get_latest_direction(run.run_id)
    assert latest_direction is not None
    assert latest_direction.trigger_event == "tests_passed_waiting_merge"


def test_run_recovers_interrupted_in_progress_workstream(tmp_path: Path) -> None:
    class FlakyReviewer:
        def __init__(self) -> None:
            self.calls = 0

        def review(self, *, execution_result: ExecutionResult, plan_bundle: PlanBundle) -> ReviewReport:  # noqa: ARG002
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary review failure")
            return passing_review(execution_result.workstream_id)

    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-app",
                name="Build app",
                layer="backend",
                objective="Create the Python app and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            )
        ]
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor({"ws-app": [ExecutionResult(workstream_id="ws-app", summary="done", files=python_app_files())]}),
        reviewer=FlakyReviewer(),
    )

    run = orchestrator.create_plan("build a tiny app")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    with pytest.raises(RuntimeError, match="temporary review failure"):
        orchestrator.run(run.run_id)

    recovered = orchestrator.run(run.run_id)

    assert recovered.stage.value == "testing"
    assert recovered.status.value == "waiting_approval"
    workstream = memory.list_workstreams(recovered.run_id)[0]
    assert workstream["status"] == "completed"
    assert any(event.event_type == "workstream_requeued_after_interrupt" for event in memory.list_events(recovered.run_id, limit=20))


def test_research_review_external_verification_marks_stage_complete_and_waits_for_gate(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="mc1_1a_scope_and_evidence",
                name="MC1-1a Scope And Evidence",
                layer="mc1_1a",
                objective="Lock scope.",
                deliverables=["reports/mc1_1a_scope_and_evidence.md"],
                acceptance_criteria=["scope locked"],
            ),
            Workstream(
                id="mc1_1b_rescoring_and_top3",
                name="MC1-1b Rescoring And Top 3",
                layer="mc1_1b",
                objective="Rescore the top candidates.",
                deliverables=["reports/mc1_1b_rescoring_and_top3.md"],
                acceptance_criteria=["top3 ranked"],
                dependencies=["mc1_1a_scope_and_evidence"],
            ),
            Workstream(
                id="external_verification",
                name="External Verification",
                layer="external_verification",
                objective="Cross-check the top 3.",
                deliverables=["reports/external_verification.md"],
                acceptance_criteria=["cross-check complete"],
                dependencies=["mc1_1b_rescoring_and_top3"],
            ),
        ]
    )
    scope_execution = ExecutionResult(
        workstream_id="mc1_1a_scope_and_evidence",
        summary="scope locked",
        files=[GeneratedFile(path="reports/mc1_1a_scope_and_evidence.md", content="# scope")],
        research_report=ResearchReport(
            workstream_id="mc1_1a_scope_and_evidence",
            scope="scope",
            claims=[
                ResearchClaim(
                    claim_id="c0",
                    claim="Scope claim",
                    source_ids=["s0"],
                    confidence="high",
                    status="supported",
                )
            ],
            sources=[
                ResearchSource(
                    source_id="s0",
                    title="Scope source",
                    url="https://example.com/scope",
                    source_type="official",
                    tier="primary",
                )
            ],
        ),
    )
    execution = ExecutionResult(
        workstream_id="mc1_1b_rescoring_and_top3",
        summary="ranking complete",
        files=[GeneratedFile(path="reports/mc1_1b_rescoring_and_top3.md", content="# top3")],
        research_report=ResearchReport(
            workstream_id="mc1_1b_rescoring_and_top3",
            scope="scope",
            claims=[
                ResearchClaim(
                    claim_id="c1",
                    claim="Claim",
                    source_ids=["s1"],
                    confidence="high",
                    status="contested",
                )
            ],
            sources=[
                ResearchSource(
                    source_id="s1",
                    title="Source",
                    url="https://example.com/source",
                    source_type="official",
                    tier="primary",
                )
            ],
        ),
    )
    review = ReviewReport(
        workstream_id="mc1_1b_rescoring_and_top3",
        approved=False,
        summary="Needs downstream external verification.",
        issues=[],
        judgment=VerificationJudgment(
            final_verdict=VerificationVerdict.escalate,
            final_action=VerificationAction.request_external_verification,
            requires_external_verification=True,
            rationale="Cross-check should happen in the dedicated external verification stage.",
        ),
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor(
            {
                "mc1_1a_scope_and_evidence": [scope_execution],
                "mc1_1b_rescoring_and_top3": [execution],
            }
        ),
        reviewer=FakeReviewer(
            {
                "mc1_1a_scope_and_evidence": [passing_review("mc1_1a_scope_and_evidence")],
                "mc1_1b_rescoring_and_top3": [review],
            }
        ),
        pipeline_mode="research",
    )

    run = orchestrator.create_plan("research flow")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    paused = orchestrator.run(run.run_id)
    assert paused.status.value == "waiting_approval"
    orchestrator.approve(run.run_id, stage=ApprovalStage.checkpoint)
    paused = orchestrator.run(run.run_id)

    assert paused.stage.value == "executing"
    assert paused.status.value == "waiting_approval"
    workstreams = {item["workstream_id"]: item for item in memory.list_workstreams(run.run_id)}
    assert workstreams["mc1_1b_rescoring_and_top3"]["status"] == "completed"
    assert workstreams["external_verification"]["status"] == "pending"
    events = [event.event_type for event in memory.list_events(run.run_id, limit=20)]
    assert "external_verification_required" in events


def test_research_external_verification_stage_uses_cross_verifier(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="mc1_1a_scope_and_evidence",
                name="MC1-1a Scope And Evidence",
                layer="mc1_1a",
                objective="Lock scope.",
                deliverables=["reports/mc1_1a_scope_and_evidence.md"],
                acceptance_criteria=["scope locked"],
            ),
            Workstream(
                id="mc1_1b_rescoring_and_top3",
                name="MC1-1b Rescoring And Top 3",
                layer="mc1_1b",
                objective="Rescore the top candidates.",
                deliverables=["reports/mc1_1b_rescoring_and_top3.md"],
                acceptance_criteria=["top3 ranked"],
                dependencies=["mc1_1a_scope_and_evidence"],
            ),
            Workstream(
                id="external_verification",
                name="External Verification",
                layer="external_verification",
                objective="Cross-check the top 3.",
                deliverables=["reports/external_verification.md"],
                acceptance_criteria=["cross-check complete"],
                dependencies=["mc1_1b_rescoring_and_top3"],
            ),
            Workstream(
                id="mc1_1c_final_recommendation",
                name="MC1-1c Final Recommendation",
                layer="mc1_1c",
                objective="Produce the final recommendation.",
                deliverables=["reports/mc1_1c_final_recommendation.md"],
                acceptance_criteria=["final recommendation ready"],
                dependencies=["mc1_1b_rescoring_and_top3", "external_verification"],
            ),
        ]
    )

    def build_research_execution(workstream_id: str, report_path: str) -> ExecutionResult:
        return ExecutionResult(
            workstream_id=workstream_id,
            summary=f"{workstream_id} complete",
            files=[GeneratedFile(path=report_path, content=f"# {workstream_id}")],
            research_report=ResearchReport(
                workstream_id=workstream_id,
                scope="scope",
                claims=[
                    ResearchClaim(
                        claim_id=f"{workstream_id}-claim",
                        claim="Claim",
                        source_ids=["s1"],
                        confidence="high",
                        status="supported",
                    )
                ],
                sources=[
                    ResearchSource(
                        source_id="s1",
                        title="Source",
                        url="https://example.com/source",
                        source_type="official",
                        tier="primary",
                    )
                ],
            ),
        )

    reviewer = FakeReviewer(
        {
            "mc1_1a_scope_and_evidence": [passing_review("mc1_1a_scope_and_evidence")],
            "mc1_1b_rescoring_and_top3": [passing_review("mc1_1b_rescoring_and_top3")],
        }
    )
    cross_verifier = FakeReviewer({"external_verification": [passing_review("external_verification")]})
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor(
            {
                "mc1_1a_scope_and_evidence": [
                    build_research_execution("mc1_1a_scope_and_evidence", "reports/mc1_1a_scope_and_evidence.md")
                ],
                "mc1_1b_rescoring_and_top3": [
                    build_research_execution("mc1_1b_rescoring_and_top3", "reports/mc1_1b_rescoring_and_top3.md")
                ],
                "external_verification": [
                    build_research_execution("external_verification", "reports/external_verification.md")
                ],
            }
        ),
        reviewer=reviewer,
        cross_verifier=cross_verifier,
        pipeline_mode="research",
    )

    run = orchestrator.create_plan("research flow")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    paused = orchestrator.run(run.run_id)
    assert paused.status.value == "waiting_approval"
    orchestrator.approve(run.run_id, stage=ApprovalStage.checkpoint)
    paused = orchestrator.run(run.run_id)
    assert paused.status.value == "waiting_approval"
    orchestrator.approve(run.run_id, stage=ApprovalStage.checkpoint)
    paused = orchestrator.run(run.run_id)

    assert paused.stage.value == "executing"
    assert paused.status.value == "waiting_approval"
    assert cross_verifier.calls["external_verification"] == 1
    assert reviewer.calls.get("external_verification", 0) == 0
    events = [event.event_type for event in memory.list_events(run.run_id, limit=20)]
    assert "external_verification_completed" in events


def test_research_validation_human_lock_rolls_back_to_blocked_execution(tmp_path: Path) -> None:
    class FakeTester:
        def run(self, workspace_path: Path) -> ValidationTestReport:  # noqa: ARG002
            return ValidationTestReport(
                passed=False,
                command="research_validation",
                results=[ValidationTestResult(name="validation", passed=False, details="needs review")],
                stderr="Human lock required.",
                judgment=VerificationJudgment(
                    final_verdict=VerificationVerdict.block,
                    final_action=VerificationAction.request_human_lock,
                    requires_human_lock=True,
                    rationale="MC1-1c introduced a new source and needs human review.",
                ),
            )

    plan = PlanBundle(
        project_brief=ProjectBrief(
            title="Research plan",
            objective="Produce final recommendation.",
            audience="Researchers",
            scope=["MC1-1"],
            deliverables=["reports"],
        ),
        architecture_spec=ArchitectureSpec(
            overview="overview",
            components=["reports"],
            data_flow=["evidence -> recommendation"],
            decisions=["structured outputs"],
        ),
        api_contract=ApiContract(interfaces=["CLI"]),
        workstreams=[
            Workstream(
                id="mc1_1a_scope_and_evidence",
                name="MC1-1a Scope And Evidence",
                layer="mc1_1a",
                objective="Lock scope.",
                deliverables=["reports/mc1_1a_scope_and_evidence.md"],
                acceptance_criteria=["done"],
            ),
            Workstream(
                id="mc1_1b_rescoring_and_top3",
                name="MC1-1b Rescoring And Top 3",
                layer="mc1_1b",
                objective="Rescore top candidates.",
                deliverables=["reports/mc1_1b_rescoring_and_top3.md"],
                acceptance_criteria=["done"],
                dependencies=["mc1_1a_scope_and_evidence"],
            ),
            Workstream(
                id="external_verification",
                name="External Verification",
                layer="external_verification",
                objective="Cross-check top candidates.",
                deliverables=["reports/external_verification.md"],
                acceptance_criteria=["done"],
                dependencies=["mc1_1b_rescoring_and_top3"],
            ),
            Workstream(
                id="mc1_1c_final_recommendation",
                name="MC1-1c Final Recommendation",
                layer="mc1_1c",
                objective="Produce the final recommendation.",
                deliverables=["reports/mc1_1c_final_recommendation.md"],
                acceptance_criteria=["done"],
                dependencies=["mc1_1b_rescoring_and_top3", "external_verification"],
            )
        ],
        test_plan=["validate evidence"],
    )
    base_report = ResearchReport(
        workstream_id="ws",
        scope="scope",
        claims=[
            ResearchClaim(
                claim_id="c1",
                claim="Claim",
                source_ids=["s1"],
                confidence="high",
                status="supported",
            )
        ],
        sources=[
            ResearchSource(
                source_id="s1",
                title="Source",
                url="https://example.com/source",
                source_type="official",
                tier="primary",
            )
        ],
    )
    def build_research_execution(workstream_id: str, report_path: str) -> ExecutionResult:
        return ExecutionResult(
            workstream_id=workstream_id,
            summary=f"{workstream_id} complete",
            files=[GeneratedFile(path=report_path, content=f"# {workstream_id}")],
            research_report=base_report.model_copy(update={"workstream_id": workstream_id}),
        )

    execution = ExecutionResult(
        workstream_id="mc1_1c_final_recommendation",
        summary="final recommendation",
        files=[GeneratedFile(path="reports/mc1_1c_final_recommendation.md", content="# final recommendation")],
        research_report=ResearchReport(
            workstream_id="mc1_1c_final_recommendation",
            scope="scope",
            claims=[
                ResearchClaim(
                    claim_id="c1",
                    claim="Claim",
                    source_ids=["s1"],
                    confidence="high",
                    status="supported",
                )
            ],
            sources=[
                ResearchSource(
                    source_id="s1",
                    title="Source",
                    url="https://example.com/source",
                    source_type="official",
                    tier="primary",
                )
            ],
        ),
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor(
            {
                "mc1_1a_scope_and_evidence": [
                    build_research_execution("mc1_1a_scope_and_evidence", "reports/mc1_1a_scope_and_evidence.md")
                ],
                "mc1_1b_rescoring_and_top3": [
                    build_research_execution("mc1_1b_rescoring_and_top3", "reports/mc1_1b_rescoring_and_top3.md")
                ],
                "external_verification": [
                    build_research_execution("external_verification", "reports/external_verification.md")
                ],
                "mc1_1c_final_recommendation": [execution],
            }
        ),
        reviewer=FakeReviewer(
            {
                "mc1_1a_scope_and_evidence": [passing_review("mc1_1a_scope_and_evidence")],
                "mc1_1b_rescoring_and_top3": [passing_review("mc1_1b_rescoring_and_top3")],
                "external_verification": [passing_review("external_verification")],
                "mc1_1c_final_recommendation": [passing_review("mc1_1c_final_recommendation")],
            }
        ),
        pipeline_mode="research",
    )
    orchestrator.tester = FakeTester()

    run = orchestrator.create_plan("research flow")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    run = orchestrator.run(run.run_id)
    assert run.status.value == "waiting_approval"
    orchestrator.approve(run.run_id, stage=ApprovalStage.checkpoint)
    run = orchestrator.run(run.run_id)
    assert run.status.value == "waiting_approval"
    orchestrator.approve(run.run_id, stage=ApprovalStage.checkpoint)
    run = orchestrator.run(run.run_id)
    assert run.status.value == "waiting_approval"
    orchestrator.approve(run.run_id, stage=ApprovalStage.checkpoint)
    blocked = orchestrator.run(run.run_id)

    assert blocked.stage.value == "executing"
    assert blocked.status.value == "blocked"
    assert "human review" in (blocked.last_error or "").lower()
    workstream = next(
        item
        for item in memory.list_workstreams(run.run_id)
        if item["workstream_id"] == "mc1_1c_final_recommendation"
    )
    assert workstream["status"] == "retry_requested"
    assert any(item.startswith("[human-lock]") for item in workstream["latest_feedback"])


def test_research_mode_maps_checkpoint_to_scope_lock(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="mc1_1a_scope_and_evidence",
                name="MC1-1a Scope And Evidence",
                layer="mc1_1a",
                objective="Lock scope and gather evidence.",
                deliverables=["reports/mc1_1a_scope_and_evidence.md"],
                acceptance_criteria=["scope locked"],
            ),
            Workstream(
                id="mc1_1b_rescoring_and_top3",
                name="MC1-1b Rescoring And Top 3",
                layer="mc1_1b",
                objective="Rescore the Top 3.",
                deliverables=["reports/mc1_1b_rescoring_and_top3.md"],
                acceptance_criteria=["top 3 ranked"],
                dependencies=["mc1_1a_scope_and_evidence"],
            ),
        ]
    )
    executor = FakeExecutor(
        {
            "mc1_1a_scope_and_evidence": [
                ExecutionResult(
                    workstream_id="mc1_1a_scope_and_evidence",
                    summary="scope complete",
                    files=[feature_files(False)[0]],
                )
            ],
            "mc1_1b_rescoring_and_top3": [
                ExecutionResult(
                    workstream_id="mc1_1b_rescoring_and_top3",
                    summary="ranking complete",
                    files=[feature_files(False)[0]],
                )
            ],
        }
    )
    reviewer = FakeReviewer(
        {
            "mc1_1a_scope_and_evidence": [passing_review("mc1_1a_scope_and_evidence")],
            "mc1_1b_rescoring_and_top3": [passing_review("mc1_1b_rescoring_and_top3")],
        }
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=executor,
        reviewer=reviewer,
        pipeline_mode="research",
    )

    run = orchestrator.create_plan("run MC1-1 research")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    paused = orchestrator.run(run.run_id)

    assert paused.stage.value == "executing"
    assert paused.status.value == "waiting_approval"
    summary = memory.build_checkpoint_summary(run.run_id)
    direction = memory.get_latest_direction(run.run_id)

    assert summary.active_gate == "scope_lock"
    assert "scope_lock" in summary.overview
    assert direction is not None
    assert direction.active_gate == "scope_lock"
    assert "scope_lock" in direction.recommendation


def test_checkpoint_approval_can_resume_after_supervisor_block(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-one",
                name="Build first step",
                layer="foundation",
                objective="Create the first module.",
                deliverables=["src/core.py"],
                acceptance_criteria=["first file exists"],
            ),
            Workstream(
                id="ws-two",
                name="Build second step",
                layer="application",
                objective="Create the second module and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            ),
        ]
    )
    executor = FakeExecutor(
        {
            "ws-one": [ExecutionResult(workstream_id="ws-one", summary="first", files=[feature_files(False)[0]])],
            "ws-two": [ExecutionResult(workstream_id="ws-two", summary="second", files=python_app_files())],
        }
    )
    reviewer = FakeReviewer({"ws-one": [passing_review("ws-one")], "ws-two": [passing_review("ws-two")]})
    orchestrator, memory = build_orchestrator(tmp_path, planner=FakePlanner(plan), executor=executor, reviewer=reviewer)

    run = orchestrator.create_plan("build in two steps")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    run = orchestrator.run(run.run_id)
    assert run.stage.value == "executing"
    assert run.status.value == "waiting_approval"

    memory.update_run(run.run_id, status=RunStatus.blocked, last_error="Supervisor requested human approval.")
    memory.save_supervisor_session(
        run.run_id,
        SupervisorSession(
            run_id=run.run_id,
            enabled=True,
            status="blocked",
            current_gate=ApprovalStage.checkpoint,
            current_agent_id="policy_guard",
            last_rationale="Supervisor requested human approval.",
            last_error_code="MAX_SAME_GATE_REPEATS",
        ),
    )

    approved = orchestrator.approve(run.run_id, stage=ApprovalStage.checkpoint)
    assert approved.status == RunStatus.pending
    resumed = orchestrator.run(run.run_id)

    assert resumed.stage.value == "testing"
    assert resumed.status.value == "waiting_approval"
    latest_session = memory.get_latest_supervisor_session(run.run_id)
    assert latest_session is not None
    assert latest_session.status == "manual_override"
    assert latest_session.current_gate is None
    events = [event.event_type for event in memory.list_events(run.run_id, limit=20)]
    assert "supervisor_manual_override" in events


def test_feedback_creates_new_plan_version(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-app",
                name="Build app",
                layer="backend",
                objective="Create the Python app and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            )
        ]
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor({"ws-app": [ExecutionResult(workstream_id="ws-app", summary="done", files=python_app_files())]}),
        reviewer=FakeReviewer({"ws-app": [passing_review("ws-app")]}),
    )

    run = orchestrator.create_plan("build a tiny app")
    orchestrator.record_feedback(run.run_id, "Add a simple CSV export option for future users.")

    latest_plan = memory.load_plan_bundle(run.run_id)
    assert len(latest_plan.change_log) == 1
    assert latest_plan.change_log[0].additions == ["Add a simple CSV export option for future users."]
    assert memory.get_plan_version(run.run_id) == 2
    summary_text = Path(run.plan_path).parent.joinpath("summary.md").read_text(encoding="utf-8")
    assert "추가된 방향" in summary_text
    assert "Add a simple CSV export option for future users." in summary_text


def test_dependency_ready_workstream_selected_before_list_order(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-feature",
                name="Feature",
                layer="feature",
                objective="Depends on core.",
                deliverables=["src/feature.py"],
                dependencies=["ws-core"],
                acceptance_criteria=["done"],
            ),
            Workstream(
                id="ws-core",
                name="Core",
                layer="foundation",
                objective="Core first.",
                deliverables=["src/core.py"],
                acceptance_criteria=["done"],
            ),
        ]
    )
    executor = FakeExecutor(
        {
            "ws-core": [ExecutionResult(workstream_id="ws-core", summary="core", files=[feature_files(False)[0]])],
            "ws-feature": [ExecutionResult(workstream_id="ws-feature", summary="feature", files=[feature_files(False)[1]])],
        }
    )
    reviewer = FakeReviewer({"ws-core": [passing_review("ws-core")], "ws-feature": [passing_review("ws-feature")]})
    orchestrator, _memory = build_orchestrator(tmp_path, planner=FakePlanner(plan), executor=executor, reviewer=reviewer)

    run = orchestrator.create_plan("dependency order")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    run = orchestrator.run(run.run_id)

    assert run.stage.value == "executing"
    assert run.status.value == "waiting_approval"
    assert executor.calls["ws-core"] == 1
    assert executor.calls["ws-feature"] == 0


def test_dependency_cycle_or_missing_fails_clearly(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-a",
                name="A",
                layer="foundation",
                objective="Depends on missing workstream.",
                deliverables=["src/a.py"],
                dependencies=["ws-missing"],
                acceptance_criteria=["done"],
            )
        ]
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor({"ws-a": [ExecutionResult(workstream_id="ws-a", summary="a", files=[feature_files(False)[0]])]}),
        reviewer=FakeReviewer({"ws-a": [passing_review("ws-a")]}),
    )
    run = orchestrator.create_plan("dependency broken")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)

    with pytest.raises(RuntimeError, match="dependency-ready workstream"):
        orchestrator.run(run.run_id)

    failed = memory.get_run(run.run_id)
    assert failed.status == RunStatus.failed


def test_notifier_receives_checkpoint_and_manual_status(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-one",
                name="Build first step",
                layer="foundation",
                objective="Create the first module.",
                deliverables=["src/core.py"],
                acceptance_criteria=["first file exists"],
            ),
            Workstream(
                id="ws-two",
                name="Build second step",
                layer="application",
                objective="Create the second module and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            ),
        ]
    )
    notifier = FakeNotifier()
    orchestrator, _memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor(
            {
                "ws-one": [ExecutionResult(workstream_id="ws-one", summary="first", files=[feature_files(False)[0]])],
                "ws-two": [ExecutionResult(workstream_id="ws-two", summary="second", files=python_app_files())],
            }
        ),
        reviewer=FakeReviewer({"ws-one": [passing_review("ws-one")], "ws-two": [passing_review("ws-two")]}),
        notifier=notifier,
    )

    run = orchestrator.create_plan("build in two steps")
    assert notifier.messages[0] == ("plan_ready", run.run_id)
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    run = orchestrator.run(run.run_id)
    assert ("stage_completed", run.run_id) in notifier.messages
    orchestrator.notify_status(run.run_id)
    assert notifier.messages[-1] == ("manual_status", run.run_id)


def test_single_stage_runs_all_workstreams_before_pausing(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-one",
                name="Build first step",
                layer="foundation",
                objective="Create the first module.",
                deliverables=["src/core.py"],
                acceptance_criteria=["first file exists"],
            ),
            Workstream(
                id="ws-two",
                name="Build second step",
                layer="foundation",
                objective="Create the second module and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            ),
            Workstream(
                id="ws-three",
                name="Build third step",
                layer="application",
                objective="Create the third module.",
                deliverables=["src/feature.py"],
                acceptance_criteria=["feature exists"],
            ),
        ]
    )
    executor = FakeExecutor(
        {
            "ws-one": [ExecutionResult(workstream_id="ws-one", summary="first", files=[feature_files(False)[0]])],
            "ws-two": [ExecutionResult(workstream_id="ws-two", summary="second", files=python_app_files())],
            "ws-three": [ExecutionResult(workstream_id="ws-three", summary="third", files=[feature_files(False)[1]])],
        }
    )
    reviewer = FakeReviewer(
        {
            "ws-one": [passing_review("ws-one")],
            "ws-two": [passing_review("ws-two")],
            "ws-three": [passing_review("ws-three")],
        }
    )
    orchestrator, memory = build_orchestrator(tmp_path, planner=FakePlanner(plan), executor=executor, reviewer=reviewer)

    run = orchestrator.create_plan("build in stage groups")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    run = orchestrator.run(run.run_id)

    assert run.stage.value == "executing"
    assert run.status.value == "waiting_approval"
    assert executor.calls["ws-one"] == 1
    assert executor.calls["ws-two"] == 1
    assert executor.calls["ws-three"] == 0

    workstreams = {item["workstream_id"]: item for item in memory.list_workstreams(run.run_id)}
    assert workstreams["ws-one"]["status"] == "completed"
    assert workstreams["ws-two"]["status"] == "completed"
    assert workstreams["ws-three"]["status"] == "pending"


def test_final_stage_emits_stage_completed_notification(tmp_path: Path) -> None:
    # Single-stage plan: when everything finishes, the pipeline falls through to testing.
    # It should still emit a per-chunk confirmation for that final stage before moving on.
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-app",
                name="Build app",
                layer="backend",
                objective="Create the Python app and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            )
        ]
    )
    notifier = FakeNotifier()
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor(
            {"ws-app": [ExecutionResult(workstream_id="ws-app", summary="done", files=python_app_files())]}
        ),
        reviewer=FakeReviewer({"ws-app": [passing_review("ws-app")]}),
        notifier=notifier,
    )

    run = orchestrator.create_plan("build a tiny app")
    orchestrator.approve(run.run_id, stage=ApprovalStage.plan)
    run = orchestrator.run(run.run_id)

    # The run proceeds to testing (single stage = no checkpoint pause),
    # but we still need a confirmation that the final stage/chunk is done.
    assert run.stage.value == "testing"
    event_names = [name for name, _run_id in notifier.messages]
    assert "stage_completed" in event_names, (
        f"expected stage_completed before testing, got: {event_names}"
    )
    # And the narrative itself must have been saved so downstream UI can render it.
    narrative = memory.get_latest_stage_narrative(run.run_id)
    assert narrative is not None
    assert narrative.stage_name == "backend"


def test_discord_notifier_includes_stage_narrative_highlight() -> None:
    from contracts.models import CheckpointSummary, RunStage, RunStatus
    from services.notifier.service import DiscordWebhookNotificationService

    service = DiscordWebhookNotificationService(webhook_url="http://unused.invalid/")
    summary = CheckpointSummary(
        run_id="abc123",
        stage=RunStage.executing,
        status=RunStatus.waiting_approval,
        plan_version=1,
        overview="foundation 단계 이후 체크포인트에서 검토 대기 중입니다.",
        completed=["Build first step"],
        in_progress=[],
        pending=["Build second step"],
        next_step="승인 후 계속 진행하세요.",
        latest_stage_name="foundation",
        latest_stage_summary="foundation 단계가 끝났고 src/core.py가 생성되었습니다.",
    )

    rendered = service._render_message(event_name="stage_completed", summary=summary)

    assert "방금 완료된 단계" in rendered
    assert "foundation" in rendered
    assert "src/core.py" in rendered


def test_supervisor_can_auto_approve_run_to_completion(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-one",
                name="Build first step",
                layer="foundation",
                objective="Create the first module.",
                deliverables=["src/core.py"],
                acceptance_criteria=["first file exists"],
            ),
            Workstream(
                id="ws-two",
                name="Build second step",
                layer="application",
                objective="Create the second module and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            ),
        ]
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor(
            {
                "ws-one": [ExecutionResult(workstream_id="ws-one", summary="first", files=[feature_files(False)[0]])],
                "ws-two": [ExecutionResult(workstream_id="ws-two", summary="second", files=python_app_files())],
            }
        ),
        reviewer=FakeReviewer({"ws-one": [passing_review("ws-one")], "ws-two": [passing_review("ws-two")]}),
    )
    supervisor = FakeSupervisor(
        {
            ApprovalStage.plan: [SupervisorDecision(stage=ApprovalStage.plan, approved=True, rationale="Plan is coherent.")],
            ApprovalStage.checkpoint: [
                SupervisorDecision(stage=ApprovalStage.checkpoint, approved=True, rationale="Checkpoint direction is clear.")
            ],
            ApprovalStage.merge: [SupervisorDecision(stage=ApprovalStage.merge, approved=True, rationale="Tests passed cleanly.")],
        }
    )

    run = orchestrator.create_plan("build in two steps")
    run = orchestrator.supervise(run.run_id, supervisor=supervisor)

    assert run.stage.value == "completed"
    assert run.status.value == "completed"
    assert run.manifest_path is not None
    assert memory.get_latest_direction(run.run_id) is not None
    assert memory.get_latest_supervisor_session(run.run_id) is not None
    assert memory.get_latest_supervisor_trace(run.run_id) is not None
    events = [event.event_type for event in memory.list_events(run.run_id, limit=50)]
    assert "supervisor_agent_decision" in events
    assert "supervisor_session_completed" in events


def test_supervisor_blocks_run_when_direction_is_not_ready(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-app",
                name="Build app",
                layer="backend",
                objective="Create the Python app and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            )
        ]
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor({"ws-app": [ExecutionResult(workstream_id="ws-app", summary="done", files=python_app_files())]}),
        reviewer=FakeReviewer({"ws-app": [passing_review("ws-app")]}),
    )
    supervisor = FakeSupervisor(
        {
            ApprovalStage.plan: [
                SupervisorDecision(
                    stage=ApprovalStage.plan,
                    approved=False,
                    rationale="User should confirm the direction before coding starts.",
                )
            ]
        }
    )

    run = orchestrator.create_plan("build a tiny app")
    run = orchestrator.supervise(run.run_id, supervisor=supervisor)

    assert run.stage.value == "planning"
    assert run.status.value == "blocked"
    assert run.last_error == "User should confirm the direction before coding starts."
    summary = memory.build_checkpoint_summary(run.run_id)
    assert "waiting for a human decision" in summary.overview
    trace = memory.get_latest_supervisor_trace(run.run_id)
    assert trace is not None
    assert trace.agent_id == "plan_gate_agent"


def test_supervisor_policy_guard_blocks_when_cycle_limit_is_zero(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-app",
                name="Build app",
                layer="backend",
                objective="Create the Python app and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            )
        ]
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor({"ws-app": [ExecutionResult(workstream_id="ws-app", summary="done", files=python_app_files())]}),
        reviewer=FakeReviewer({"ws-app": [passing_review("ws-app")]}),
    )
    supervisor = FakeSupervisor({ApprovalStage.plan: [SupervisorDecision(stage=ApprovalStage.plan, approved=True, rationale="unused")]})

    run = orchestrator.create_plan("build a tiny app")
    run = orchestrator.supervise(run.run_id, supervisor=supervisor, max_cycles=0)

    assert run.status.value == "blocked"
    trace = memory.get_latest_supervisor_trace(run.run_id)
    assert trace is not None
    assert trace.agent_id == "policy_guard"
    assert trace.error_code == "MAX_CYCLES"


def test_supervisor_blocks_when_same_gate_repeat_limit_is_reached(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id=f"ws-{index}",
                name=f"Build step {index}",
                layer=f"layer-{index}",
                objective=f"Create module {index}.",
                deliverables=[f"src/module_{index}.py"],
                acceptance_criteria=["file exists"],
            )
            for index in range(1, 6)
        ]
    )
    executor = FakeExecutor(
        {
            f"ws-{index}": [
                ExecutionResult(
                    workstream_id=f"ws-{index}",
                    summary=f"step {index}",
                    files=[feature_files(False)[0]],
                )
            ]
            for index in range(1, 6)
        }
    )
    reviewer = FakeReviewer({f"ws-{index}": [passing_review(f"ws-{index}")] for index in range(1, 6)})
    orchestrator, memory = build_orchestrator(tmp_path, planner=FakePlanner(plan), executor=executor, reviewer=reviewer)
    supervisor = FakeSupervisor(
        {
            ApprovalStage.plan: [SupervisorDecision(stage=ApprovalStage.plan, approved=True, rationale="ok")],
            ApprovalStage.checkpoint: [
                SupervisorDecision(stage=ApprovalStage.checkpoint, approved=True, rationale="ok")
                for _ in range(4)
            ],
            ApprovalStage.merge: [SupervisorDecision(stage=ApprovalStage.merge, approved=True, rationale="ok")],
        }
    )

    run = orchestrator.create_plan("many checkpoint gates")
    run = orchestrator.supervise(run.run_id, supervisor=supervisor, max_cycles=10)

    assert run.status.value == "blocked"
    trace = memory.get_latest_supervisor_trace(run.run_id)
    assert trace is not None
    assert trace.error_code == "MAX_SAME_GATE_REPEATS"


def test_supervisor_blocks_when_plan_revision_limit_is_reached(tmp_path: Path) -> None:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-app",
                name="Build app",
                layer="backend",
                objective="Create the Python app and tests.",
                deliverables=["src/app.py", "tests/test_app.py"],
                acceptance_criteria=["pytest passes"],
            )
        ]
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor({"ws-app": [ExecutionResult(workstream_id="ws-app", summary="done", files=python_app_files())]}),
        reviewer=FakeReviewer({"ws-app": [passing_review("ws-app")]}),
    )
    memory.settings.supervisor_max_plan_revisions = 2
    supervisor = FakeSupervisor(
        {
            ApprovalStage.plan: [SupervisorDecision(stage=ApprovalStage.plan, approved=True, rationale="unused")],
        }
    )

    run = orchestrator.create_plan("build a tiny app")
    memory.append_plan_addition(run.run_id, "Narrow the scope to a first MVP.")
    memory.append_plan_addition(run.run_id, "Add a second planning clarification.")

    run = orchestrator.supervise(run.run_id, supervisor=supervisor)

    assert run.stage.value == "planning"
    assert run.status.value == "blocked"
    assert supervisor.calls[ApprovalStage.plan] == 0
    trace = memory.get_latest_supervisor_trace(run.run_id)
    assert trace is not None
    assert trace.agent_id == "policy_guard"
    assert trace.error_code == "MAX_PLAN_REVISIONS"
