from __future__ import annotations

import json

from pydantic import BaseModel

from contracts.models import ExecutionResult, PlanBundle, ResearchReport, TaskAssignment
from core.prompting import compose_system_prompt
from services.adapters.base import JsonModelAdapter


class ExecutionEnvelope(BaseModel):
    result: ExecutionResult


class ExecutorService:
    def __init__(self, adapter: JsonModelAdapter, *, guidance_prompt: str = "", mode: str = "code") -> None:
        self.adapter = adapter
        self.guidance_prompt = guidance_prompt
        self.mode = mode

    def execute(
        self,
        *,
        assignment: TaskAssignment,
        plan_bundle: PlanBundle,
        workspace_snapshot: str,
        review_feedback: list[str],
    ) -> ExecutionResult:
        feedback_text = "\n".join(f"- {item}" for item in review_feedback) or "- none"
        if self.mode == "research":
            system_prompt = compose_system_prompt(
                (
                    "You are a research agent in a multi-agent investigation pipeline. "
                    "Your job is to research the assigned topic thoroughly, cite sources, "
                    "and produce well-structured investigation results. "
                    "Return your findings as structured files (markdown reports)."
                ),
                self.guidance_prompt,
                section_name="research methodology, source verification, and output formatting",
            )
            user_prompt = (
                "Research the following topic and produce investigation results.\n"
                "Rules:\n"
                "- produce markdown report files at reports/<workstream_id>.md\n"
                "- return a structured ResearchReport in ExecutionResult.research_report\n"
                "- every substantive claim must include source_ids\n"
                "- every source_id used by claims must exist in ResearchReport.sources\n"
                "- use search tools to discover candidate sources, but do not treat search-result snippets as sole evidence for high-confidence claims\n"
                "- for source-backed claims, inspect the underlying source content directly (for example abstract text, fetched page content, or authoritative database output) before citing it as supported\n"
                "- unsupported/speculative/uncertain statements must be captured as gaps or low-confidence claims\n"
                "- when the source supports only an inference rather than the exact claim wording, mark that claim provisional and explain the inference boundary in notes\n"
                "- conflicting information must be listed in ResearchReport.conflicts\n"
                "- keep scope focused on the assigned workstream only\n\n"
                f"Task assignment:\n{assignment.model_dump_json(indent=2)}\n\n"
                f"Plan bundle:\n{plan_bundle.model_dump_json(indent=2)}\n\n"
                f"Current workspace snapshot:\n{workspace_snapshot or '[empty workspace]'}\n\n"
                f"Review feedback to address:\n{feedback_text}\n\n"
                "Return JSON only."
            )
        else:
            system_prompt = compose_system_prompt(
                (
                    "You are Codex acting as the implementation agent in a controlled delivery pipeline. "
                    "Write only the files needed for the assigned workstream and keep changes scoped."
                ),
                self.guidance_prompt,
                section_name="implementation, repository expectations, testing, reversibility, and workflow rules",
            )
            user_prompt = (
                "Create or update files for this workstream.\n"
                "Rules:\n"
                "- modify only files relevant to the workstream layer\n"
                "- include tests when the workstream implies behavior\n"
                "- keep dependencies minimal and use Python standard library when possible\n"
                "- honor any user additions recorded in plan_bundle.change_log\n"
                "- return relative file paths only\n\n"
                f"Task assignment:\n{assignment.model_dump_json(indent=2)}\n\n"
                f"Plan bundle:\n{plan_bundle.model_dump_json(indent=2)}\n\n"
                f"Current workspace snapshot:\n{workspace_snapshot or '[empty workspace]'}\n\n"
                f"Review feedback to address:\n{feedback_text}\n\n"
                "Return JSON only."
            )
        result = self.adapter.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ExecutionEnvelope,
        )
        assert isinstance(result, ExecutionEnvelope)
        if self.mode == "research":
            return self._normalize_research_result(
                result=result.result,
                assignment=assignment,
                plan_bundle=plan_bundle,
                workspace_snapshot=workspace_snapshot,
                review_feedback=review_feedback,
            )
        return result.result

    def _normalize_research_result(
        self,
        *,
        result: ExecutionResult,
        assignment: TaskAssignment,
        plan_bundle: PlanBundle,
        workspace_snapshot: str,
        review_feedback: list[str],
    ) -> ExecutionResult:
        if result.research_report is None:
            return result

        workstream = next((item for item in plan_bundle.workstreams if item.id == assignment.workstream_id), None)
        if workstream is None:
            return result

        prior_evidence = self._load_research_reports_from_snapshot(workspace_snapshot)
        existing_envelope = result.research_report.stage_envelope
        current_source_ids = [
            source.source_id.strip()
            for source in result.research_report.sources
            if source.source_id.strip()
        ]
        carry_forward_source_ids = list(existing_envelope.carry_forward_source_ids)
        if not carry_forward_source_ids and workstream.layer == "mc1_1c":
            carry_forward_source_ids = sorted(
                {
                    source.source_id.strip()
                    for path, report in prior_evidence
                    if report.workstream_id != result.workstream_id
                    for source in report.sources
                    if source.source_id.strip()
                }
            )

        policy_violations = self._dedupe_strings(
            [
                *existing_envelope.policy_violations,
                *self._infer_policy_violations(review_feedback=review_feedback),
            ]
        )
        if workstream.layer == "mc1_1c" and carry_forward_source_ids:
            carry_forward_set = {item.strip().lower() for item in carry_forward_source_ids if item.strip()}
            unexpected_source_ids = [
                source_id
                for source_id in current_source_ids
                if source_id.strip().lower() not in carry_forward_set
            ]
            if unexpected_source_ids:
                policy_violations = self._dedupe_strings(
                    [*policy_violations, "new_data_forbidden_violation", "new_source_detected"]
                )

        normalized_report = result.research_report.model_copy(
            update={
                "stage_envelope": existing_envelope.model_copy(
                    update={
                        "stage_name": existing_envelope.stage_name or workstream.layer,
                        "summary": existing_envelope.summary or result.summary or workstream.objective,
                        "artifact_paths": self._dedupe_strings(
                            [
                                *existing_envelope.artifact_paths,
                                *(generated_file.path for generated_file in result.files),
                            ]
                        ),
                        "source_paths": self._dedupe_strings(
                            [
                                *existing_envelope.source_paths,
                                *(path for path, _ in prior_evidence),
                            ]
                        ),
                        "claim_count": existing_envelope.claim_count or len(result.research_report.claims),
                        "carry_forward_source_ids": carry_forward_source_ids,
                        "policy_violations": policy_violations,
                    }
                )
            }
        )
        return result.model_copy(update={"research_report": normalized_report})

    @staticmethod
    def _dedupe_strings(values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            item = value.strip()
            if not item:
                continue
            lowered = item.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            normalized.append(item)
        return normalized

    @staticmethod
    def _infer_policy_violations(*, review_feedback: list[str]) -> list[str]:
        feedback_text = "\n".join(review_feedback).lower()
        normalized_feedback = feedback_text
        for benign_phrase in (
            "no scope drift",
            "no scope violation",
            "without scope violation",
            "scope boundaries are explicit",
        ):
            normalized_feedback = normalized_feedback.replace(benign_phrase, "")
        violations: list[str] = []
        if any(
            token in normalized_feedback
            for token in (
                "scope violation",
                "scope drift",
                "out of scope",
                "out-of-scope",
                "beyond assigned",
                "outside assigned",
                "outside the assigned",
            )
        ):
            violations.append("scope_violation")
        if any(token in feedback_text for token in ("new data", "new source", "new evidence", "fresh data")):
            violations.append("new_data_forbidden_violation")
        return violations

    @staticmethod
    def _load_research_reports_from_snapshot(workspace_snapshot: str) -> list[tuple[str, ResearchReport]]:
        if not workspace_snapshot.strip():
            return []

        reports: list[tuple[str, ResearchReport]] = []
        current_path: str | None = None
        body_lines: list[str] = []

        def flush() -> None:
            nonlocal current_path, body_lines
            if current_path is None or not current_path.startswith("research_evidence/") or not current_path.endswith(".json"):
                current_path = None
                body_lines = []
                return
            try:
                payload = json.loads("\n".join(body_lines))
                reports.append((current_path, ResearchReport.model_validate(payload)))
            except Exception:  # noqa: BLE001
                pass
            current_path = None
            body_lines = []

        for line in workspace_snapshot.splitlines():
            if line.startswith("## "):
                flush()
                current_path = line[3:].strip()
                continue
            body_lines.append(line)
        flush()
        return reports
