from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from apps.cli import main as cli_main
from contracts.models import RunStage, RunStatus


runner = CliRunner()


def test_resolve_text_input_reads_markdown_file(tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.md"
    proposal.write_text("# Proposal\n\nBuild a simple tool.\n", encoding="utf-8")

    resolved = cli_main.resolve_text_input(
        None,
        file_path=proposal,
        field_name="request",
    )

    assert resolved == "# Proposal\n\nBuild a simple tool."


def test_plan_command_accepts_request_file(monkeypatch, tmp_path: Path) -> None:
    proposal = tmp_path / "proposal.md"
    proposal.write_text("# Proposal\n\nBuild a simple tool.\n", encoding="utf-8")
    captured: dict[str, str] = {}

    class DummyOrchestrator:
        def create_plan(self, request_text: str):
            captured["request_text"] = request_text
            return SimpleNamespace(
                run_id="run-123",
                stage=RunStage.planning,
                plan_path="plans/run-123/plan_bundle.json",
            )

    monkeypatch.setattr(cli_main, "build_orchestrator", lambda: DummyOrchestrator())

    result = runner.invoke(cli_main.app, ["plan", "--request-file", str(proposal)])

    assert result.exit_code == 0
    assert "run_id=run-123" in result.stdout
    assert captured["request_text"] == "# Proposal\n\nBuild a simple tool."


def test_feedback_command_accepts_comment_file(monkeypatch, tmp_path: Path) -> None:
    direction = tmp_path / "next-direction.md"
    direction.write_text("Keep the UX simple and beginner-friendly.\n", encoding="utf-8")
    captured: dict[str, str] = {}

    class DummyMemory:
        def append_plan_addition(self, run_id: str, addition: str, *, actor: str = "local-user") -> None:
            captured["run_id"] = run_id
            captured["addition"] = addition
            captured["actor"] = actor

        def get_run(self, run_id: str):
            return SimpleNamespace(
                run_id=run_id,
                stage=RunStage.planning,
                status=RunStatus.waiting_approval,
                plan_path="plans/run-123/plan_bundle.json",
            )

    monkeypatch.setattr(cli_main, "build_memory", lambda: DummyMemory())

    result = runner.invoke(
        cli_main.app,
        ["feedback", "run-123", "--comment-file", str(direction)],
    )

    assert result.exit_code == 0
    assert "run_id=run-123" in result.stdout
    assert captured["addition"] == "Keep the UX simple and beginner-friendly."


def test_summary_and_directions_commands_show_active_gate(monkeypatch) -> None:
    gate = SimpleNamespace(value="scope_lock")

    class DummyMemory:
        def build_checkpoint_summary(self, run_id: str):
            return SimpleNamespace(
                run_id=run_id,
                plan_version=2,
                active_gate=gate,
                overview="overview",
                completed=["scope"],
                in_progress=[],
                pending=["top3"],
                recent_changes=[],
                risks=[],
                next_step="approve scope lock",
                latest_stage_name="MC1-1a scope and evidence",
                latest_stage_summary="scope summary",
            )

        def get_latest_direction(self, run_id: str):
            return SimpleNamespace(
                run_id=run_id,
                sequence=1,
                trigger_event="stage_completed",
                active_gate=gate,
                headline="headline",
                summary="direction summary",
                recommendation="recommendation",
                options=["continue"],
                completed_stage="MC1-1a scope and evidence",
                client_summary="client summary",
                artifact_highlights=["reports/mc1_1a.md"],
            )

    monkeypatch.setattr(cli_main, "build_memory", lambda: DummyMemory())

    summary_result = runner.invoke(cli_main.app, ["summary", "run-123"])
    directions_result = runner.invoke(cli_main.app, ["directions", "run-123"])

    assert summary_result.exit_code == 0
    assert "active_gate=scope_lock" in summary_result.stdout
    assert directions_result.exit_code == 0
    assert "active_gate=scope_lock" in directions_result.stdout


def test_build_orchestrator_uses_gpt_mainline_and_claude_cross_verifier(monkeypatch, tmp_path: Path) -> None:
    class DummyOpenAIAdapter:
        def __init__(self, **kwargs) -> None:
            self.provider = "openai"
            self.kwargs = kwargs

    class DummyAnthropicAdapter:
        def __init__(self, **kwargs) -> None:
            self.provider = "anthropic"
            self.kwargs = kwargs

    monkeypatch.setattr(cli_main, "OpenAIJsonAdapter", DummyOpenAIAdapter)
    monkeypatch.setattr(cli_main, "AnthropicJsonAdapter", DummyAnthropicAdapter)
    monkeypatch.setattr(cli_main, "build_memory", lambda settings=None: SimpleNamespace())
    monkeypatch.setattr(cli_main, "build_notifier", lambda settings=None: SimpleNamespace())
    monkeypatch.setattr(cli_main, "load_guidance_prompt", lambda settings: "")

    settings = cli_main.Settings(
        workspace_root=tmp_path,
        pipeline_db_path="outputs/test.db",
        openai_api_key="test-openai",
        anthropic_api_key="test-anthropic",
    )

    orchestrator = cli_main.build_orchestrator(settings)

    assert orchestrator.planner.adapter.provider == "openai"
    assert orchestrator.executor.adapter.provider == "openai"
    assert orchestrator.reviewer.adapter.provider == "openai"
    assert orchestrator.cross_verifier.adapter.provider == "anthropic"


def test_build_orchestrator_can_run_all_roles_on_openai_without_anthropic_key(monkeypatch, tmp_path: Path) -> None:
    class DummyOpenAIAdapter:
        def __init__(self, **kwargs) -> None:
            self.provider = "openai"
            self.kwargs = kwargs

    monkeypatch.setattr(cli_main, "OpenAIJsonAdapter", DummyOpenAIAdapter)
    monkeypatch.setattr(cli_main, "build_memory", lambda settings=None: SimpleNamespace())
    monkeypatch.setattr(cli_main, "build_notifier", lambda settings=None: SimpleNamespace())
    monkeypatch.setattr(cli_main, "load_guidance_prompt", lambda settings: "")

    settings = cli_main.Settings(
        workspace_root=tmp_path,
        pipeline_db_path="outputs/test.db",
        openai_api_key="test-openai",
        anthropic_api_key=None,
        planner_provider="openai",
        executor_provider="openai",
        reviewer_provider="openai",
        cross_verifier_provider="openai",
        cross_verifier_model="gpt-5.4",
    )

    orchestrator = cli_main.build_orchestrator(settings)

    assert orchestrator.cross_verifier.adapter.provider == "openai"


def test_build_orchestrator_requires_anthropic_key_only_when_cross_verifier_uses_anthropic(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli_main, "build_memory", lambda settings=None: SimpleNamespace())
    monkeypatch.setattr(cli_main, "build_notifier", lambda settings=None: SimpleNamespace())
    monkeypatch.setattr(cli_main, "load_guidance_prompt", lambda settings: "")

    settings = cli_main.Settings(
        workspace_root=tmp_path,
        pipeline_db_path="outputs/test.db",
        openai_api_key="test-openai",
        anthropic_api_key=None,
        cross_verifier_provider="anthropic",
    )

    with pytest.raises(Exception, match="ANTHROPIC_API_KEY is required for cross_verifier"):
        cli_main.build_orchestrator(settings)
