from __future__ import annotations

import json
import hashlib

from contracts.models import (
    ApprovalDecision,
    ApprovalStage,
    PlanBundle,
    ResearchGate,
    RunRecord,
    RunStage,
    RunStatus,
    SupervisorDecision,
    SupervisorSession,
    SupervisorTrace,
    TaskAssignment,
    TestReport,
    VerificationAction,
    WorkstreamStatus,
    utc_now,
)
from core.state_machine import HermesStateMachine
from services.cross_verifier.service import CrossVerifierService
from services.executor.service import ExecutorService
from services.memory.service import MemoryService
from services.notifier.service import NotificationService
from services.planner.service import PlannerService
from services.reviewer.service import ReviewerService
from services.supervisor.service import SupervisorService
from services.testing.service import TestRunnerService


class HermesOrchestrator:
    def __init__(
        self,
        *,
        planner: PlannerService,
        executor: ExecutorService,
        reviewer: ReviewerService,
        cross_verifier: ReviewerService | CrossVerifierService | None = None,
        tester: TestRunnerService,
        memory: MemoryService,
        notifier: NotificationService,
        state_machine: HermesStateMachine,
        max_retries_per_workstream: int = 2,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.reviewer = reviewer
        self.cross_verifier = cross_verifier or reviewer
        self.tester = tester
        self.memory = memory
        self.notifier = notifier
        self.state_machine = state_machine
        self.max_retries_per_workstream = max_retries_per_workstream

    def create_plan(self, request_text: str) -> RunRecord:
        run = self.memory.create_run(request_text)
        self.state_machine.ensure_transition(run.stage, RunStage.planning)
        plan_bundle = self.planner.create_plan(run.request)
        self.memory.save_plan_bundle(run.run_id, plan_bundle)
        self.memory.save_direction_snapshot(run.run_id, "plan_ready")
        created = self.memory.get_run(run.run_id)
        self._notify("plan_ready", created.run_id)
        return created

    def approve(self, run_id: str, *, stage: ApprovalStage, actor: str = "local-user", comment: str = "") -> RunRecord:
        run = self.memory.get_run(run_id)
        if stage == ApprovalStage.plan:
            self.state_machine.ensure_transition(run.stage, RunStage.plan_approved)
            if comment.strip():
                self.memory.append_plan_addition(run_id, comment.strip(), actor=actor)
                run = self.memory.get_run(run_id)
            decision = ApprovalDecision(run_id=run_id, stage=stage, approved=True, actor=actor, comment=comment)
            self.memory.record_approval(decision)
            approved = self.memory.update_run(run_id, stage=RunStage.plan_approved, status=RunStatus.pending)
            self._clear_supervisor_block(run_id, stage=stage, research_gate=None)
            self._notify("plan_approved", run_id)
            return approved
        if stage == ApprovalStage.checkpoint:
            # NOTE: checkpoint approval은 stage를 전이하지 않는다.
            # executing/reviewing stage 내에서 다음 workstream으로 계속 진행하기 위해
            # status만 pending으로 되돌린다. plan/merge approve와 달리
            # 새로운 RunStage로의 전이가 필요하지 않다.
            if run.stage not in {RunStage.executing, RunStage.reviewing} or run.status not in {
                RunStatus.waiting_approval,
                RunStatus.blocked,
            }:
                raise ValueError("Checkpoint approval is only valid when the run is paused during implementation.")
            research_gate = self._research_gate_for_run(run_id, run=run)
            latest_stage_narrative = self.memory.get_latest_stage_narrative(run_id)
            if comment.strip():
                self.memory.append_plan_addition(run_id, comment.strip(), actor=actor)
            decision = ApprovalDecision(run_id=run_id, stage=stage, approved=True, actor=actor, comment=comment)
            self.memory.record_approval(decision)
            approved = self.memory.update_run(run_id, status=RunStatus.pending, last_error=None)
            if research_gate is not None:
                self.memory.append_event(
                    run_id,
                    run.stage,
                    "research_gate_approved",
                    f"{research_gate.value} approved.",
                    payload={
                        "approval_stage": stage.value,
                        "research_gate": research_gate.value,
                        "completed_stage": latest_stage_narrative.stage_name if latest_stage_narrative else None,
                        "verification_phase": self.state_machine.is_research_verification_layer(
                            latest_stage_narrative.stage_name if latest_stage_narrative else None
                        ),
                    },
                )
            self._clear_supervisor_block(run_id, stage=stage, research_gate=research_gate)
            self._notify(
                f"{research_gate.value}_approved" if research_gate is not None else "checkpoint_approved",
                run_id,
            )
            return approved
        if run.stage != RunStage.testing:
            raise ValueError("Merge approval is only valid after successful testing.")
        latest_test = self.memory.load_latest_test_report(run_id)
        if latest_test is None or not latest_test.passed:
            raise ValueError("Cannot approve merge before tests pass.")
        self.state_machine.ensure_transition(run.stage, RunStage.merge_approved)
        decision = ApprovalDecision(run_id=run_id, stage=stage, approved=True, actor=actor, comment=comment)
        self.memory.record_approval(decision)
        approved = self.memory.update_run(run_id, stage=RunStage.merge_approved, status=RunStatus.pending)
        self._clear_supervisor_block(run_id, stage=stage, research_gate=None)
        self._notify("merge_approved", run_id)
        return approved

    def run(self, run_id: str) -> RunRecord:
        run = self.memory.get_run(run_id)
        if run.stage in {RunStage.executing, RunStage.reviewing} and run.status in {
            RunStatus.waiting_approval,
            RunStatus.blocked,
        }:
            raise ValueError(self._approval_required_message(run_id, run=run))
        if run.stage in {RunStage.plan_approved, RunStage.executing, RunStage.reviewing, RunStage.testing}:
            return self._execute_until_gate(run_id)
        if run.stage == RunStage.merge_approved:
            return self._package(run_id)
        if run.stage == RunStage.completed:
            return run
        raise ValueError(f"Run {run_id} is not executable from stage {run.stage.value}.")

    def supervise(
        self,
        run_id: str,
        *,
        supervisor: SupervisorService,
        actor: str = "direction-supervisor",
        max_cycles: int | None = None,
    ) -> RunRecord:
        session, resumed = self._load_or_create_supervisor_session(run_id, max_cycles=max_cycles)
        self.memory.save_supervisor_session(run_id, session)
        self.memory.append_event(
            run_id,
            self.memory.get_run(run_id).stage,
            "supervisor_session_resumed" if resumed else "supervisor_session_started",
            "Supervisor session resumed." if resumed else "Supervisor session started.",
            payload={
                "resumed": resumed,
                "max_cycles": session.max_cycles,
                "max_same_gate_repeats": session.max_same_gate_repeats,
                "max_supervisor_denials": session.max_supervisor_denials,
                "max_consecutive_failures": session.max_consecutive_failures,
                "max_plan_revisions": session.max_plan_revisions,
            },
        )
        while True:
            run = self.memory.get_run(run_id)
            if run.stage == RunStage.completed:
                session.status = "completed"
                session.current_gate = None
                session.current_agent_id = None
                self._stamp_session(session)
                self.memory.save_supervisor_session(run_id, session)
                self.memory.append_event(
                    run_id,
                    run.stage,
                    "supervisor_session_completed",
                    "Supervisor session completed the run.",
                    payload={"cycles_completed": session.cycles_completed},
                )
                return run
            if run.status in {RunStatus.failed, RunStatus.blocked}:
                session.status = "blocked"
                session.last_rationale = run.last_error
                session.current_gate = None
                session.current_agent_id = None
                self._stamp_session(session)
                self.memory.save_supervisor_session(run_id, session)
                return run

            approval_stage = self._pending_approval_stage(run)
            if approval_stage is not None:
                session.current_gate = approval_stage
                session.current_agent_id = supervisor.agent_for_stage(approval_stage).agent_id
                self._stamp_session(session)
                self.memory.save_supervisor_session(run_id, session)
                guard_issue = self._policy_guard(run_id, run=run, stage=approval_stage, session=session)
                if guard_issue is not None:
                    return self._block_run_for_supervisor(
                        run_id,
                        run=run,
                        session=session,
                        trace=guard_issue,
                        event_type="supervisor_policy_blocked",
                    )
                run = self._apply_supervisor_decision(
                    run_id,
                    supervisor=supervisor,
                    stage=approval_stage,
                    actor=actor,
                    session=session,
                )
                if run.status == RunStatus.blocked:
                    return run

            if session.cycles_completed >= session.max_cycles:
                trace = self._build_policy_trace(
                    run_id,
                    stage=approval_stage or self._infer_approval_stage_from_run(run),
                    session=session,
                    rationale=f"Supervisor reached the cycle limit of {session.max_cycles}.",
                    error_code="MAX_CYCLES",
                    risk_flags=["cycle_limit_reached"],
                )
                return self._block_run_for_supervisor(
                    run_id,
                    run=run,
                    session=session,
                    trace=trace,
                    event_type="supervisor_cycle_limit_reached",
                )

            try:
                run = self.run(run_id)
            except Exception as exc:
                session.consecutive_failures += 1
                session.last_rationale = str(exc)
                session.last_error_code = "RUN_EXCEPTION"
                self._stamp_session(session)
                self.memory.save_supervisor_session(run_id, session)
                self.memory.append_event(
                    run_id,
                    self.memory.get_run(run_id).stage,
                    "supervisor_run_error",
                    "Supervisor run step raised an exception.",
                    payload={
                        "error": str(exc),
                        "consecutive_failures": session.consecutive_failures,
                    },
                )
                if session.consecutive_failures >= session.max_consecutive_failures:
                    trace = self._build_policy_trace(
                        run_id,
                        stage=approval_stage or self._infer_approval_stage_from_run(run),
                        session=session,
                        rationale=(
                            f"Supervisor observed {session.consecutive_failures} consecutive run failures and stopped."
                        ),
                        error_code="MAX_CONSECUTIVE_FAILURES",
                        risk_flags=["consecutive_failures"],
                    )
                    return self._block_run_for_supervisor(
                        run_id,
                        run=self.memory.get_run(run_id),
                        session=session,
                        trace=trace,
                        event_type="supervisor_policy_blocked",
                    )
                continue

            session.cycles_completed += 1
            session.consecutive_failures = 0
            session.status = "running"
            session.current_gate = None
            session.current_agent_id = None
            self._stamp_session(session)
            self.memory.save_supervisor_session(run_id, session)

    @staticmethod
    def _infer_approval_stage_from_run(run: RunRecord) -> ApprovalStage:
        """Run의 현재 stage를 기반으로 가장 적절한 ApprovalStage를 추론한다."""
        if run.stage == RunStage.planning:
            return ApprovalStage.plan
        if run.stage == RunStage.testing:
            return ApprovalStage.merge
        return ApprovalStage.checkpoint

    def _execute_until_gate(self, run_id: str) -> RunRecord:
        run = self.memory.get_run(run_id)
        if run.stage == RunStage.plan_approved:
            self.state_machine.ensure_transition(run.stage, RunStage.executing)
            self.memory.update_run(run_id, stage=RunStage.executing, status=RunStatus.in_progress)

        plan_bundle = self.memory.load_plan_bundle(run_id)
        while True:
            workstreams = self.memory.list_workstreams(run_id)
            ready = self._select_ready_workstream(workstreams, plan_bundle)
            if ready is None:
                if self._recover_interrupted_workstream(run_id, workstreams):
                    continue
                if any(
                    item["status"] in {WorkstreamStatus.pending.value, WorkstreamStatus.retry_requested.value}
                    for item in workstreams
                ):
                    error = self._describe_workstream_block(workstreams) or (
                        "No dependency-ready workstream found. Possible cyclic or missing dependencies."
                    )
                    self.memory.update_run(run_id, stage=RunStage.executing, status=RunStatus.failed, last_error=error)
                    self.memory.append_event(run_id, RunStage.executing, "dependency_blocked", error)
                    raise RuntimeError(error)
                break

            active_stage_name = ready["layer"]
            workstream_completed = self._execute_workstream_until_approved(run_id, plan_bundle, ready["workstream_id"])
            if not workstream_completed:
                return self.memory.get_run(run_id)

            refreshed_workstreams = self.memory.list_workstreams(run_id)
            stage_has_more = any(
                item["layer"] == active_stage_name
                and item["status"] in {WorkstreamStatus.pending.value, WorkstreamStatus.retry_requested.value, WorkstreamStatus.in_progress.value}
                for item in refreshed_workstreams
            )
            if stage_has_more:
                continue

            has_more_workstreams = any(
                item["status"] in {WorkstreamStatus.pending.value, WorkstreamStatus.retry_requested.value}
                for item in refreshed_workstreams
            )
            self.memory.save_stage_narrative(run_id, active_stage_name)
            research_gate = self.state_machine.research_gate_for_layer(active_stage_name)
            # Always emit a confirmation that this stage/chunk is done, even when it's the final
            # stage. Previously only non-final stages fired a notification, so the last chunk
            # silently fell through into testing with no per-stage confirmation.
            self.memory.append_event(
                run_id,
                RunStage.executing,
                "stage_completed",
                f"Stage {active_stage_name} completed.",
                payload={
                    "completed_stage": active_stage_name,
                    "has_more_workstreams": has_more_workstreams,
                    "is_final_stage": not has_more_workstreams,
                },
            )
            if has_more_workstreams:
                self.memory.append_event(
                    run_id,
                    RunStage.executing,
                    "checkpoint_ready",
                    f"Checkpoint ready after completing stage {active_stage_name}.",
                    payload={
                        "completed_stage": active_stage_name,
                        "research_gate": research_gate.value if research_gate is not None else None,
                    },
                )
                if research_gate is not None:
                    self.memory.append_event(
                        run_id,
                        RunStage.executing,
                        "research_gate_ready",
                        f"{research_gate.value} is ready after completing stage {active_stage_name}.",
                        payload={
                            "completed_stage": active_stage_name,
                            "research_gate": research_gate.value,
                            "verification_phase": self.state_machine.is_research_verification_layer(active_stage_name),
                        },
                    )
                paused = self.memory.update_run(run_id, stage=RunStage.executing, status=RunStatus.waiting_approval)
                self.memory.save_direction_snapshot(run_id, "stage_completed")
                self._notify("stage_completed", run_id)
                return paused
            # Final stage: still fire the confirmation (no approval gate here — testing handles it).
            self.memory.save_direction_snapshot(run_id, "stage_completed")
            self._notify("stage_completed", run_id)

        current_stage = self.memory.get_run(run_id).stage
        self._ensure_research_flow_ready_for_testing(run_id)
        self.state_machine.ensure_transition(current_stage, RunStage.testing)
        self.memory.update_run(run_id, stage=RunStage.testing, status=RunStatus.in_progress)
        report = self.tester.run(self.memory.get_workspace_path(run_id))
        self.memory.save_test_report(run_id, report)
        if report.judgment.final_action in {
            VerificationAction.request_external_verification,
            VerificationAction.request_human_lock,
        }:
            return self._escalate_test_judgment(run_id, report=report)
        if report.passed:
            passed = self.memory.update_run(run_id, stage=RunStage.testing, status=RunStatus.waiting_approval)
            self.memory.save_direction_snapshot(run_id, "tests_passed_waiting_merge")
            self._notify("tests_passed_waiting_merge", run_id)
            return passed

        impacted = self.memory.infer_impacted_workstreams(run_id, report)
        if not impacted:
            self.memory.update_run(run_id, stage=RunStage.testing, status=RunStatus.failed, last_error="Tests failed with no impacted workstream match.")
            self.memory.save_direction_snapshot(run_id, "run_failed")
            self._notify("run_failed", run_id)
            raise RuntimeError("Tests failed and no impacted workstream could be selected for retry.")

        for item in self.memory.list_workstreams(run_id):
            if item["workstream_id"] in impacted:
                # test failure로 인한 retry는 review retry와 별도로 카운트한다.
                test_retry_count = sum(1 for fb in item["latest_feedback"] if fb.startswith("[test-failure]"))
                if test_retry_count >= self.max_retries_per_workstream:
                    self.memory.update_workstream(run_id, item["workstream_id"], status=WorkstreamStatus.failed)
                    self.memory.update_run(run_id, stage=RunStage.testing, status=RunStatus.failed, last_error="Tests failed after selective retries.")
                    self.memory.save_direction_snapshot(run_id, "run_failed")
                    self._notify("run_failed", run_id)
                    raise RuntimeError("Tests failed after selective retries.")
                self.memory.update_workstream(
                    run_id,
                    item["workstream_id"],
                    status=WorkstreamStatus.retry_requested,
                    latest_feedback=[f"[test-failure] {report.stderr or report.stdout or 'Fix failing tests.'}"],
                )
        self.state_machine.ensure_transition(RunStage.testing, RunStage.executing)
        self.memory.append_event(
            run_id,
            RunStage.testing,
            "checkpoint_ready",
            "Checkpoint ready after test failures were mapped to workstreams.",
            payload={"impacted_workstreams": impacted},
        )
        paused = self.memory.update_run(run_id, stage=RunStage.executing, status=RunStatus.waiting_approval)
        self.memory.save_direction_snapshot(run_id, "tests_need_changes")
        self._notify("tests_need_changes", run_id)
        return paused

    def _recover_interrupted_workstream(self, run_id: str, workstreams: list[dict[str, object]]) -> bool:
        interrupted = next(
            (
                item
                for item in workstreams
                if item["status"] == WorkstreamStatus.in_progress.value
            ),
            None,
        )
        if interrupted is None:
            return False

        workstream_id = str(interrupted["workstream_id"])
        latest_feedback = list(interrupted.get("latest_feedback", []))
        recovery_note = "[recovered] Re-queued after an interrupted execution/review step."
        if recovery_note not in latest_feedback:
            latest_feedback = [recovery_note, *latest_feedback]

        self.memory.update_workstream(
            run_id,
            workstream_id,
            status=WorkstreamStatus.retry_requested,
            latest_feedback=latest_feedback,
        )
        self.memory.update_run(
            run_id,
            stage=RunStage.executing,
            status=RunStatus.pending,
            last_error="Recovered interrupted workstream after a prior execution/review exception.",
        )
        self.memory.append_event(
            run_id,
            RunStage.executing,
            "workstream_requeued_after_interrupt",
            f"Re-queued {workstream_id} after an interrupted execution/review step.",
            payload={"workstream_id": workstream_id},
        )
        return True

    def _execute_workstream_until_approved(self, run_id: str, plan_bundle: PlanBundle, workstream_id: str) -> bool:
        workstream = next(item for item in plan_bundle.workstreams if item.id == workstream_id)
        is_verification_phase = (
            self.memory.settings.pipeline_mode == "research"
            and self.state_machine.is_research_verification_layer(workstream.layer)
        )
        is_final_recommendation = self.memory.settings.pipeline_mode == "research" and workstream.layer == "mc1_1c"
        while True:
            ready = next(item for item in self.memory.list_workstreams(run_id) if item["workstream_id"] == workstream_id)
            current_stage = self.memory.get_run(run_id).stage
            self.state_machine.ensure_transition(current_stage, RunStage.executing)
            self.memory.update_run(run_id, stage=RunStage.executing, status=RunStatus.in_progress)
            self.memory.update_workstream(run_id, workstream_id, status=WorkstreamStatus.in_progress)
            if is_verification_phase:
                self.memory.append_event(
                    run_id,
                    RunStage.executing,
                    "external_verification_started",
                    "External verification is running before the final crop lock.",
                    payload={"workstream_id": workstream_id, "retry_count": ready["retry_count"]},
                )
            assignment = TaskAssignment(
                run_id=run_id,
                workstream_id=workstream_id,
                agent_role="codex-executor",
                instructions=self._build_instructions(plan_bundle, workstream_id),
                context_paths=[self.memory.get_workspace_path(run_id).as_posix()],
                retry_count=ready["retry_count"],
            )
            execution = self.executor.execute(
                assignment=assignment,
                plan_bundle=plan_bundle,
                workspace_snapshot=self.memory.workspace_snapshot(run_id),
                review_feedback=ready["latest_feedback"],
            )
            self.memory.save_execution_result(run_id, execution)

            self.state_machine.ensure_transition(RunStage.executing, RunStage.reviewing)
            self.memory.update_run(run_id, stage=RunStage.reviewing, status=RunStatus.in_progress)
            review_service = self.cross_verifier if is_verification_phase else self.reviewer
            review = review_service.review(execution_result=execution, plan_bundle=plan_bundle)
            self.memory.save_review_report(run_id, review)

            if review.approved:
                self.memory.update_workstream(run_id, workstream_id, status=WorkstreamStatus.completed)
                if is_verification_phase:
                    self.memory.append_event(
                        run_id,
                        RunStage.reviewing,
                        "external_verification_completed",
                        "External verification completed and is ready for the final crop lock review.",
                        payload={"workstream_id": workstream_id},
                    )
                return True

            if (
                self.memory.settings.pipeline_mode == "research"
                and review.judgment.final_action == VerificationAction.request_external_verification
            ):
                if not is_verification_phase and not is_final_recommendation:
                    self.memory.update_workstream(run_id, workstream_id, status=WorkstreamStatus.completed)
                    self.memory.append_event(
                        run_id,
                        RunStage.reviewing,
                        "external_verification_required",
                        "Review accepted the stage output but requires the downstream external verification pass.",
                        payload={
                            "workstream_id": workstream_id,
                            "rationale": review.judgment.rationale,
                        },
                    )
                    return True
                self._pause_for_review_escalation(
                    run_id,
                    workstream_id=workstream_id,
                    review=review,
                    event_type="external_verification_required",
                    trigger_event="external_verification_required",
                )
                return False

            if review.judgment.final_action == VerificationAction.request_human_lock:
                self._pause_for_review_escalation(
                    run_id,
                    workstream_id=workstream_id,
                    review=review,
                    event_type="human_lock_required",
                    trigger_event="human_lock_required",
                )
                return False

            # review 결과 처리 직전에 최신 workstream 상태를 다시 읽어 stale read를 방지한다.
            fresh_ws = next(item for item in self.memory.list_workstreams(run_id) if item["workstream_id"] == workstream_id)
            retry_count = fresh_ws["retry_count"] + 1
            if retry_count > self.max_retries_per_workstream:
                self.memory.update_workstream(run_id, workstream_id, status=WorkstreamStatus.failed, retry_count=retry_count)
                self.memory.update_run(
                    run_id,
                    stage=RunStage.reviewing,
                    status=RunStatus.failed,
                    last_error=f"Review failed for {workstream_id} after retries.",
                )
                self.memory.save_direction_snapshot(run_id, "run_failed")
                self._notify("run_failed", run_id)
                raise RuntimeError(f"Review failed for {workstream_id} after retries.")

            feedback = [issue.suggested_fix for issue in review.issues]
            self.memory.update_workstream(
                run_id,
                workstream_id,
                status=WorkstreamStatus.retry_requested,
                retry_count=retry_count,
                latest_feedback=feedback,
            )
            self.memory.append_event(
                run_id,
                RunStage.reviewing,
                "verification_retry_requested" if is_verification_phase else "review_retry_requested",
                (
                    "External verification requested another pass before the final crop lock."
                    if is_verification_phase
                    else f"Internal retry requested after review feedback for {workstream_id}."
                ),
                payload={"feedback": feedback, "retry_count": retry_count},
            )
        return False

    def _build_instructions(self, plan_bundle: PlanBundle, workstream_id: str) -> str:
        workstream = next(item for item in plan_bundle.workstreams if item.id == workstream_id)
        return (
            f"Implement workstream {workstream.id} ({workstream.name}) for layer {workstream.layer}.\n"
            f"Objective: {workstream.objective}\n"
            f"Deliverables: {', '.join(workstream.deliverables)}\n"
            f"Acceptance: {', '.join(workstream.acceptance_criteria)}"
        )

    def _pause_for_review_escalation(
        self,
        run_id: str,
        *,
        workstream_id: str,
        review,
        event_type: str,
        trigger_event: str,
    ) -> None:
        feedback = [issue.suggested_fix for issue in review.issues if issue.suggested_fix.strip()]
        if review.judgment.rationale.strip():
            feedback.append(review.judgment.rationale.strip())
        feedback = feedback or [review.summary.strip() or "Review requested operator intervention."]
        self.memory.update_workstream(
            run_id,
            workstream_id,
            status=WorkstreamStatus.retry_requested,
            latest_feedback=feedback,
        )
        self.memory.update_run(
            run_id,
            stage=RunStage.reviewing,
            status=RunStatus.blocked,
            last_error=review.judgment.rationale or review.summary,
        )
        self.memory.append_event(
            run_id,
            RunStage.reviewing,
            event_type,
            review.judgment.rationale or review.summary or "Review escalated the workstream.",
            payload={
                "workstream_id": workstream_id,
                "final_action": review.judgment.final_action.value,
                "feedback": feedback,
            },
        )
        self.memory.save_direction_snapshot(run_id, trigger_event)
        self._notify(trigger_event, run_id)

    def _escalate_test_judgment(self, run_id: str, *, report: TestReport) -> RunRecord:
        impacted = self.memory.infer_impacted_workstreams(run_id, report)
        feedback_prefix = (
            "[external-verification]"
            if report.judgment.final_action == VerificationAction.request_external_verification
            else "[human-lock]"
        )
        feedback_message = report.judgment.rationale or "Validation requested operator intervention."
        for item in self.memory.list_workstreams(run_id):
            if item["workstream_id"] not in impacted:
                continue
            updated_feedback = [f"{feedback_prefix} {feedback_message}", *item["latest_feedback"]]
            self.memory.update_workstream(
                run_id,
                item["workstream_id"],
                status=WorkstreamStatus.retry_requested,
                latest_feedback=updated_feedback,
            )
        blocked = self.memory.update_run(
            run_id,
            stage=RunStage.executing,
            status=RunStatus.blocked,
            last_error=feedback_message,
        )
        event_type = (
            "external_verification_required"
            if report.judgment.final_action == VerificationAction.request_external_verification
            else "human_lock_required"
        )
        self.memory.append_event(
            run_id,
            RunStage.testing,
            event_type,
            feedback_message,
            payload={
                "impacted_workstreams": impacted,
                "final_action": report.judgment.final_action.value,
            },
        )
        self.memory.save_direction_snapshot(run_id, event_type)
        self._notify(event_type, run_id)
        return blocked

    def _package(self, run_id: str) -> RunRecord:
        run = self.memory.get_run(run_id)
        self.state_machine.ensure_transition(run.stage, RunStage.packaging)
        self.memory.update_run(run_id, stage=RunStage.packaging, status=RunStatus.in_progress)
        self.memory.package_workspace(run_id)
        self.state_machine.ensure_transition(RunStage.packaging, RunStage.completed)
        completed = self.memory.update_run(run_id, stage=RunStage.completed, status=RunStatus.completed)
        self.memory.save_direction_snapshot(run_id, "run_completed")
        self._notify("run_completed", run_id)
        return completed

    def record_feedback(self, run_id: str, comment: str, *, actor: str = "local-user") -> RunRecord:
        if not comment.strip():
            raise ValueError("Feedback comment cannot be empty.")
        self.memory.append_plan_addition(run_id, comment.strip(), actor=actor)
        updated = self.memory.get_run(run_id)
        self._notify("plan_updated", run_id)
        return updated

    def notify_status(self, run_id: str, *, event_name: str = "manual_status") -> RunRecord:
        run = self.memory.get_run(run_id)
        self._notify(event_name, run_id)
        return run

    def _notify(self, event_name: str, run_id: str) -> None:
        summary = self.memory.build_checkpoint_summary(run_id)
        self.notifier.publish(event_name=event_name, summary=summary)

    def _research_gate_for_run(self, run_id: str, *, run: RunRecord | None = None) -> ResearchGate | None:
        if self.memory.settings.pipeline_mode != "research":
            return None
        current_run = run or self.memory.get_run(run_id)
        if current_run.stage not in {RunStage.executing, RunStage.reviewing} or current_run.status not in {
            RunStatus.waiting_approval,
            RunStatus.blocked,
        }:
            return None
        latest_stage_narrative = self.memory.get_latest_stage_narrative(run_id)
        return self.state_machine.research_gate_for_layer(
            latest_stage_narrative.stage_name if latest_stage_narrative else None
        )

    def _approval_required_message(self, run_id: str, *, run: RunRecord | None = None) -> str:
        research_gate = self._research_gate_for_run(run_id, run=run)
        if research_gate is not None:
            return f"{research_gate.value} approval is required before continuing this research run."
        return "Checkpoint approval is required before continuing this run."

    def _approval_phase_key(
        self,
        run_id: str,
        *,
        stage: ApprovalStage,
        run: RunRecord | None = None,
    ) -> str:
        research_gate = self._research_gate_for_run(run_id, run=run)
        return self.state_machine.approval_phase_key(stage, research_gate)

    def _describe_workstream_block(self, workstreams: list[dict]) -> str | None:
        if self.memory.settings.pipeline_mode != "research":
            return None
        candidates = [
            item for item in workstreams if item["status"] in {WorkstreamStatus.pending.value, WorkstreamStatus.retry_requested.value}
        ]
        completed_layers = {item["layer"] for item in workstreams if item["status"] == WorkstreamStatus.completed.value}
        blocked_layers: list[str] = []
        for item in candidates:
            missing_layers = self.state_machine.missing_research_prerequisites(item["layer"], completed_layers)
            if missing_layers:
                blocked_layers.append(f"{item['layer']} waits on {', '.join(missing_layers)}")
        if not blocked_layers:
            return None
        return "Research stage order blocked: " + "; ".join(blocked_layers[:3]) + "."

    def _missing_research_layers(self, run_id: str) -> list[str]:
        if self.memory.settings.pipeline_mode != "research":
            return []
        completed_layers = {
            item["layer"]
            for item in self.memory.list_workstreams(run_id)
            if item["status"] == WorkstreamStatus.completed.value
        }
        return [
            layer
            for layer in self.state_machine.RESEARCH_LAYER_SEQUENCE
            if layer not in completed_layers
        ]

    def _ensure_research_flow_ready_for_testing(self, run_id: str) -> None:
        missing_layers = self._missing_research_layers(run_id)
        if not missing_layers:
            return
        error = (
            "Research workflow cannot enter validation before completing "
            + ", ".join(missing_layers)
            + "."
        )
        current_stage = self.memory.get_run(run_id).stage
        self.memory.update_run(run_id, stage=current_stage, status=RunStatus.failed, last_error=error)
        self.memory.append_event(
            run_id,
            current_stage,
            "research_flow_incomplete",
            error,
            payload={"missing_layers": missing_layers},
        )
        raise RuntimeError(error)

    @staticmethod
    def _pending_approval_stage(run: RunRecord) -> ApprovalStage | None:
        if run.stage == RunStage.planning and run.status == RunStatus.waiting_approval:
            return ApprovalStage.plan
        if run.stage in {RunStage.executing, RunStage.reviewing} and run.status == RunStatus.waiting_approval:
            return ApprovalStage.checkpoint
        if run.stage == RunStage.testing and run.status == RunStatus.waiting_approval:
            return ApprovalStage.merge
        return None

    def _select_ready_workstream(self, workstreams: list[dict], plan_bundle: PlanBundle) -> dict | None:
        candidates = [
            item for item in workstreams if item["status"] in {WorkstreamStatus.pending.value, WorkstreamStatus.retry_requested.value}
        ]
        if not candidates:
            return None
        status_map = {item["workstream_id"]: item["status"] for item in workstreams}
        plan_map = {workstream.id: workstream for workstream in plan_bundle.workstreams}
        ready_items: list[dict] = []
        for item in candidates:
            workstream = plan_map.get(item["workstream_id"])
            if workstream is None:
                continue
            if all(status_map.get(dep_id) == WorkstreamStatus.completed.value for dep_id in workstream.dependencies):
                ready_items.append(item)
        if not ready_items:
            return None
        if self.memory.settings.pipeline_mode != "research":
            return ready_items[0]
        completed_layers = {item["layer"] for item in workstreams if item["status"] == WorkstreamStatus.completed.value}
        ranked_items = sorted(
            ready_items,
            key=lambda item: (
                self.state_machine.research_layer_index(item["layer"])
                if self.state_machine.research_layer_index(item["layer"]) is not None
                else len(self.state_machine.RESEARCH_LAYER_SEQUENCE),
                item["workstream_id"],
            ),
        )
        for item in ranked_items:
            missing_layers = self.state_machine.missing_research_prerequisites(item["layer"], completed_layers)
            if not missing_layers:
                return item
        return None

    def _apply_supervisor_decision(
        self,
        run_id: str,
        *,
        supervisor: SupervisorService,
        stage: ApprovalStage,
        actor: str,
        session: SupervisorSession,
    ) -> RunRecord:
        current_run = self.memory.get_run(run_id)
        summary = self.memory.build_checkpoint_summary(run_id)
        direction = self.memory.get_latest_direction(run_id)
        research_gate = self._research_gate_for_run(run_id, run=current_run)
        approval_phase_key = self._approval_phase_key(run_id, stage=stage, run=current_run)
        plan_bundle = None
        if stage == ApprovalStage.plan or self.memory.settings.pipeline_mode == "research":
            plan_bundle = self.memory.load_plan_bundle(run_id)
        stage_narrative = self.memory.get_latest_stage_narrative(run_id)
        recent_events = [
            {
                "stage": event.stage.value,
                "type": event.event_type,
                "message": event.message,
            }
            for event in reversed(self.memory.list_events(run_id, limit=5))
        ]
        test_report = self.memory.load_latest_test_report(run_id) if stage == ApprovalStage.merge else None
        artifact_highlights = stage_narrative.artifact_highlights if stage_narrative is not None else []
        decision, trace = supervisor.evaluate(
            run_id=run_id,
            sequence=self.memory.get_supervisor_trace_count(run_id) + 1,
            stage=stage,
            summary=summary,
            direction=direction,
            plan_bundle=plan_bundle,
            stage_narrative=stage_narrative,
            recent_events=recent_events,
            test_report=test_report,
            artifact_highlights=artifact_highlights,
        )
        self.memory.save_supervisor_trace(run_id, trace)
        self.memory.append_event(
            run_id,
            summary.stage,
            "supervisor_agent_decision",
            f"Supervisor agent reviewed the {stage.value} gate.",
            payload={
                "stage": stage.value,
                "research_gate": research_gate.value if research_gate is not None else None,
                "approval_phase_key": approval_phase_key,
                "approved": decision.approved,
                "actor": actor,
                "rationale": decision.rationale,
                "agent_id": trace.agent_id,
                "decision_source": trace.decision_source,
                "risk_flags": decision.risk_flags,
                "requires_human": decision.requires_human,
            },
        )
        if not decision.approved:
            session.supervisor_denials += 1
            session.last_rationale = decision.rationale
            session.last_error_code = "SUPERVISOR_DENIED"
            self._stamp_session(session)
            self.memory.save_supervisor_session(run_id, session)
            return self._block_run_for_supervisor(
                run_id,
                run=self.memory.get_run(run_id),
                session=session,
                trace=trace,
                event_type="supervisor_blocked",
            )
        session.status = "running"
        session.last_rationale = decision.rationale
        session.last_error_code = None
        session.same_gate_repeats[approval_phase_key] = session.same_gate_repeats.get(approval_phase_key, 0) + 1
        self._stamp_session(session)
        self.memory.save_supervisor_session(run_id, session)
        return self.approve(run_id, stage=stage, actor=actor, comment="")

    def _load_or_create_supervisor_session(
        self,
        run_id: str,
        *,
        max_cycles: int | None,
    ) -> tuple[SupervisorSession, bool]:
        settings = self.memory.settings
        existing = self.memory.get_latest_supervisor_session(run_id)
        if existing is not None and existing.enabled and existing.status != "completed":
            session = existing.model_copy(deep=True)
            session.enabled = True
            session.max_cycles = max_cycles if max_cycles is not None else session.max_cycles
            session.max_same_gate_repeats = settings.supervisor_max_same_gate_repeats
            session.max_supervisor_denials = settings.supervisor_max_supervisor_denials
            session.max_consecutive_failures = settings.supervisor_max_consecutive_failures
            session.max_plan_revisions = settings.supervisor_max_plan_revisions
            if session.status != "blocked":
                session.status = "running"
                session.current_gate = None
                session.current_agent_id = None
            self._stamp_session(session)
            return session, True
        session = SupervisorSession(
            run_id=run_id,
            enabled=True,
            status="running",
            max_cycles=max_cycles if max_cycles is not None else settings.supervisor_max_cycles,
            max_same_gate_repeats=settings.supervisor_max_same_gate_repeats,
            max_supervisor_denials=settings.supervisor_max_supervisor_denials,
            max_consecutive_failures=settings.supervisor_max_consecutive_failures,
            max_plan_revisions=settings.supervisor_max_plan_revisions,
        )
        self._stamp_session(session)
        return session, False

    def _policy_guard(
        self,
        run_id: str,
        *,
        run: RunRecord,
        stage: ApprovalStage,
        session: SupervisorSession,
    ) -> SupervisorTrace | None:
        research_gate = self._research_gate_for_run(run_id, run=run)
        gate_label = research_gate.value if research_gate is not None else stage.value
        if run.status in {RunStatus.failed, RunStatus.blocked}:
            return self._build_policy_trace(
                run_id,
                stage=stage,
                session=session,
                rationale=f"Run is already {run.status.value} and cannot continue under supervisor mode.",
                error_code="RUN_NOT_CONTINUABLE",
                risk_flags=[run.status.value],
                research_gate=research_gate,
            )
        expected_stage = self._pending_approval_stage(run)
        if expected_stage != stage:
            return self._build_policy_trace(
                run_id,
                stage=stage,
                session=session,
                rationale=f"Expected {expected_stage.value if expected_stage else 'no'} approval gate, not {stage.value}.",
                error_code="INVALID_GATE_STATE",
                risk_flags=["invalid_gate_state"],
                research_gate=research_gate,
            )
        if stage == ApprovalStage.checkpoint and self.memory.settings.pipeline_mode == "research" and research_gate is None:
            return self._build_policy_trace(
                run_id,
                stage=stage,
                session=session,
                rationale=(
                    "Research mode checkpoint reached without a mapped scope_lock, top3_lock, or final_crop_lock gate."
                ),
                error_code="UNMAPPED_RESEARCH_GATE",
                risk_flags=["research_gate_unmapped"],
            )
        if stage == ApprovalStage.merge:
            latest_test = self.memory.load_latest_test_report(run_id)
            if latest_test is None or not latest_test.passed:
                return self._build_policy_trace(
                    run_id,
                    stage=stage,
                    session=session,
                    rationale="Merge gate requires a passing test report before supervisor approval.",
                    error_code="MISSING_PASSING_TEST_REPORT",
                    risk_flags=["tests_not_ready"],
                    research_gate=research_gate,
                )
            if self.memory.settings.pipeline_mode == "research":
                missing_layers = self._missing_research_layers(run_id)
                if missing_layers:
                    return self._build_policy_trace(
                        run_id,
                        stage=stage,
                        session=session,
                        rationale=(
                            "Research merge approval requires the full MC1-1 flow, including external_verification, "
                            "before packaging."
                        ),
                        error_code="INCOMPLETE_RESEARCH_FLOW",
                        risk_flags=["research_flow_incomplete", *missing_layers],
                    )
                latest_stage_narrative = self.memory.get_latest_stage_narrative(run_id)
                if latest_stage_narrative is None or latest_stage_narrative.stage_name != "mc1_1c":
                    return self._build_policy_trace(
                        run_id,
                        stage=stage,
                        session=session,
                        rationale="Research merge approval requires MC1-1c final recommendation output to be the latest completed stage.",
                        error_code="FINAL_RECOMMENDATION_NOT_READY",
                        risk_flags=["final_recommendation_not_ready"],
                    )
        if stage == ApprovalStage.plan:
            current_plan_version = self.memory.get_plan_version(run_id)
            if current_plan_version > session.max_plan_revisions:
                return self._build_policy_trace(
                    run_id,
                    stage=stage,
                    session=session,
                    rationale=(
                        f"Plan revision limit reached at v{current_plan_version:03d}; "
                        "human review is required before more automatic planning."
                    ),
                    error_code="MAX_PLAN_REVISIONS",
                    risk_flags=["plan_revision_limit"],
                    research_gate=research_gate,
                )
        gate_repeats = session.same_gate_repeats.get(
            self._approval_phase_key(run_id, stage=stage, run=run),
            0,
        )
        if gate_repeats >= session.max_same_gate_repeats:
            return self._build_policy_trace(
                run_id,
                stage=stage,
                session=session,
                rationale=f"Supervisor reached the repeat limit for the {gate_label} gate.",
                error_code="MAX_SAME_GATE_REPEATS",
                risk_flags=["same_gate_repeat_limit"],
                research_gate=research_gate,
            )
        if session.supervisor_denials >= session.max_supervisor_denials:
            return self._build_policy_trace(
                run_id,
                stage=stage,
                session=session,
                rationale="Supervisor denial limit reached; human confirmation is now required.",
                error_code="MAX_SUPERVISOR_DENIALS",
                risk_flags=["supervisor_denial_limit"],
                research_gate=research_gate,
            )
        if session.cycles_completed >= session.max_cycles:
            return self._build_policy_trace(
                run_id,
                stage=stage,
                session=session,
                rationale=f"Supervisor reached the cycle limit of {session.max_cycles}.",
                error_code="MAX_CYCLES",
                risk_flags=["cycle_limit_reached"],
                research_gate=research_gate,
            )
        return None

    def _build_policy_trace(
        self,
        run_id: str,
        *,
        stage: ApprovalStage,
        session: SupervisorSession,
        rationale: str,
        error_code: str,
        risk_flags: list[str],
        research_gate: ResearchGate | None = None,
    ) -> SupervisorTrace:
        payload = {
            "run_id": run_id,
            "stage": stage.value,
            "research_gate": research_gate.value if research_gate is not None else None,
            "approval_phase_key": self.state_machine.approval_phase_key(stage, research_gate),
            "cycles_completed": session.cycles_completed,
            "max_cycles": session.max_cycles,
            "same_gate_repeats": session.same_gate_repeats,
            "supervisor_denials": session.supervisor_denials,
            "consecutive_failures": session.consecutive_failures,
            "error_code": error_code,
        }
        return SupervisorTrace(
            run_id=run_id,
            sequence=self.memory.get_supervisor_trace_count(run_id) + 1,
            stage=stage,
            agent_id="policy_guard",
            decision_source="policy_guard",
            approved=False,
            rationale=rationale,
            risk_flags=risk_flags,
            requires_human=True,
            input_digest=hashlib.sha256(
                json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest(),
            latency_ms=0,
            model_name="deterministic",
            error_code=error_code,
        )

    def _block_run_for_supervisor(
        self,
        run_id: str,
        *,
        run: RunRecord,
        session: SupervisorSession,
        trace: SupervisorTrace,
        event_type: str,
    ) -> RunRecord:
        research_gate = self._research_gate_for_run(run_id, run=run)
        approval_phase_key = self._approval_phase_key(run_id, stage=trace.stage, run=run)
        self.memory.save_supervisor_trace(run_id, trace)
        blocked = self.memory.update_run(run_id, status=RunStatus.blocked, last_error=trace.rationale)
        session.status = "blocked"
        session.current_gate = trace.stage
        session.current_agent_id = trace.agent_id
        session.last_rationale = trace.rationale
        session.last_error_code = trace.error_code
        self._stamp_session(session)
        self.memory.save_supervisor_session(run_id, session)
        self.memory.append_event(
            run_id,
            blocked.stage,
            event_type,
            trace.rationale,
            payload={
                "stage": trace.stage.value,
                "research_gate": research_gate.value if research_gate is not None else None,
                "approval_phase_key": approval_phase_key,
                "agent_id": trace.agent_id,
                "decision_source": trace.decision_source,
                "error_code": trace.error_code,
                "risk_flags": trace.risk_flags,
            },
        )
        self.memory.save_direction_snapshot(run_id, "supervisor_blocked")
        self._notify("supervisor_blocked", run_id)
        return blocked

    def _clear_supervisor_block(
        self,
        run_id: str,
        *,
        stage: ApprovalStage,
        research_gate: ResearchGate | None,
    ) -> None:
        session = self.memory.get_latest_supervisor_session(run_id)
        if session is None or session.status != "blocked":
            return
        gate_label = research_gate.value if research_gate is not None else stage.value
        session.status = "manual_override"
        session.current_gate = None
        session.current_agent_id = None
        session.last_rationale = f"Human approved the {gate_label} gate after supervisor block."
        session.last_error_code = None
        self._stamp_session(session)
        self.memory.save_supervisor_session(run_id, session)
        self.memory.append_event(
            run_id,
            self.memory.get_run(run_id).stage,
            "supervisor_manual_override",
            f"Human approved the {gate_label} gate after supervisor block.",
            payload={
                "stage": stage.value,
                "research_gate": research_gate.value if research_gate is not None else None,
                "approval_phase_key": self.state_machine.approval_phase_key(stage, research_gate),
            },
        )

    @staticmethod
    def _stamp_session(session: SupervisorSession) -> None:
        session.updated_at = utc_now()
