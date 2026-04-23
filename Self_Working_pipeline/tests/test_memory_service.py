from pathlib import Path

import pytest

from contracts.models import ExecutionResult, GeneratedFile, ResearchClaim, ResearchReport, ResearchSource, RunStage, RunStatus, Workstream, WorkstreamStatus
from core.settings import Settings
from services.memory.db import create_session_factory
from services.memory.service import MemoryService
from tests.helpers import build_orchestrator, sample_plan_bundle, FakeExecutor, FakePlanner, FakeReviewer, passing_review


def _prepare_run(tmp_path: Path) -> tuple[str, object]:
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-memory",
                name="Memory test",
                layer="foundation",
                objective="Test memory save behavior.",
                deliverables=["reports/ws-memory.md"],
                acceptance_criteria=["saved"],
            )
        ]
    )
    orchestrator, memory = build_orchestrator(
        tmp_path,
        planner=FakePlanner(plan),
        executor=FakeExecutor({"ws-memory": [ExecutionResult(workstream_id="ws-memory", summary="ok", files=[])]}),
        reviewer=FakeReviewer({"ws-memory": [passing_review("ws-memory")]}),
    )
    run = orchestrator.create_plan("test")
    return run.run_id, memory


def test_save_execution_result_rejects_parent_traversal(tmp_path: Path) -> None:
    run_id, memory = _prepare_run(tmp_path)
    result = ExecutionResult(
        workstream_id="ws-memory",
        summary="bad",
        files=[GeneratedFile(path="../escape.txt", content="x")],
    )
    with pytest.raises(ValueError):
        memory.save_execution_result(run_id, result)


def test_save_execution_result_rejects_absolute_path(tmp_path: Path) -> None:
    run_id, memory = _prepare_run(tmp_path)
    result = ExecutionResult(
        workstream_id="ws-memory",
        summary="bad",
        files=[GeneratedFile(path="/tmp/escape.txt", content="x")],
    )
    with pytest.raises(ValueError):
        memory.save_execution_result(run_id, result)


def test_save_execution_result_accepts_workspace_relative_path_and_writes_evidence(tmp_path: Path) -> None:
    run_id, memory = _prepare_run(tmp_path)
    report = ResearchReport(
        workstream_id="ws-memory",
        scope="scope",
        claims=[
            ResearchClaim(
                claim_id="c1",
                claim="claim",
                source_ids=["s1"],
                confidence="high",
                status="supported",
            )
        ],
        sources=[ResearchSource(source_id="s1", source_type="official", tier="primary", url="https://example.com")],
    )
    result = ExecutionResult(
        workstream_id="ws-memory",
        summary="ok",
        files=[GeneratedFile(path="reports/ok.md", content="# ok")],
        research_report=report,
    )

    memory.save_execution_result(run_id, result)

    workspace = memory.get_workspace_path(run_id)
    assert (workspace / "reports/ok.md").exists()
    evidence_path = workspace / "research_evidence/ws-memory.json"
    assert evidence_path.exists()
    changed_files = memory.list_workstreams(run_id)[0]["changed_files"]
    assert "reports/ok.md" in changed_files
    assert "research_evidence/ws-memory.json" in changed_files


def test_research_stage_narrative_uses_human_labels_and_keeps_gate_mapping(tmp_path: Path) -> None:
    settings = Settings(
        workspace_root=tmp_path,
        pipeline_db_path="outputs/test.db",
        anthropic_api_key="test-anthropic",
        openai_api_key="test-openai",
        pipeline_mode="research",
    )
    memory = MemoryService(settings=settings, session_factory=create_session_factory(settings))
    run = memory.create_run("research request")
    plan = sample_plan_bundle(
        [
            Workstream(
                id="ws-scope",
                name="Scope and evidence",
                layer="mc1_1a",
                objective="Lock the admissible scope and evidence.",
                deliverables=["reports/mc1_1a.md"],
                acceptance_criteria=["scope is locked"],
            ),
            Workstream(
                id="ws-top3",
                name="Rescore top candidates",
                layer="mc1_1b",
                objective="Rescore the candidate set and keep the top 3.",
                deliverables=["reports/mc1_1b.md"],
                acceptance_criteria=["top 3 is fixed"],
            ),
        ]
    )
    memory.save_plan_bundle(run.run_id, plan)
    memory.update_workstream(
        run.run_id,
        "ws-scope",
        status=WorkstreamStatus.completed,
        changed_files=["reports/mc1_1a.md"],
    )
    memory.update_run(run.run_id, stage=RunStage.executing, status=RunStatus.waiting_approval)

    narrative = memory.save_stage_narrative(run.run_id, "mc1_1a")
    summary = memory.build_checkpoint_summary(run.run_id)
    direction = memory.build_direction_snapshot(run.run_id, trigger_event="stage_completed")

    assert narrative.stage_name == "MC1-1a scope and evidence"
    assert narrative.client_summary.startswith("MC1-1a scope and evidence")
    assert narrative.next_focus == "MC1-1b rescoring and Top 3"
    assert summary.latest_stage_name == "MC1-1a scope and evidence"
    assert summary.active_gate == "scope_lock"
    assert direction.active_gate == "scope_lock"
    assert direction.completed_stage == "MC1-1a scope and evidence"
