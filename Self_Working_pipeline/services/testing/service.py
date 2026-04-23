from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from contracts.models import (
    ResearchReport,
    ResearchSource,
    TestReport,
    TestResult,
    VerificationAction,
    VerificationJudgment,
    VerificationVerdict,
)


class TestRunnerService:
    def __init__(self, *, mode: str = "code", research_require_evidence_json: bool = True) -> None:
        self.mode = mode
        self.research_require_evidence_json = research_require_evidence_json

    def run(self, workspace_path: Path) -> TestReport:
        if self.mode == "research":
            return self._run_research_validation(workspace_path)
        return self._run_pytest(workspace_path)

    def _run_research_validation(self, workspace_path: Path) -> TestReport:
        """조사 결과물의 기본 품질 검증을 수행한다."""
        results: list[TestResult] = []

        md_files = list(workspace_path.rglob("*.md"))
        if not md_files:
            results.append(
                TestResult(
                    name="output_files_exist",
                    passed=False,
                    details="No markdown output files found in workspace.",
                )
            )
            judgment = self._build_research_judgment(evidence_reports=[], results=results)
            return TestReport(
                passed=False,
                command="research_validation",
                results=results,
                stderr=judgment.rationale or "No output files found.",
                judgment=judgment,
            )
        results.append(
            TestResult(
                name="output_files_exist",
                passed=True,
                details=f"Found {len(md_files)} markdown file(s).",
            )
        )

        empty_files = [f for f in md_files if f.stat().st_size < 100]
        has_content = len(empty_files) == 0
        results.append(
            TestResult(
                name="files_have_content",
                passed=has_content,
                details=f"{len(empty_files)} file(s) are nearly empty." if not has_content else "All files have content.",
            )
        )

        files_with_refs = 0
        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8", errors="ignore").lower()
            if any(marker in content for marker in ["http", "source:", "reference", "doi:", "출처", "참고"]):
                files_with_refs += 1
        has_refs = files_with_refs > 0
        results.append(
            TestResult(
                name="sources_cited",
                passed=has_refs,
                details=f"{files_with_refs}/{len(md_files)} file(s) contain source references.",
            )
        )

        evidence_paths = sorted((workspace_path / "research_evidence").glob("*.json"))
        evidence_required = self.research_require_evidence_json
        results.append(
            TestResult(
                name="evidence_json_exists",
                passed=bool(evidence_paths) if evidence_required else True,
                details=f"Found {len(evidence_paths)} evidence JSON file(s).",
            )
        )

        evidence_reports: list[ResearchReport] = []
        evidence_errors: list[str] = []
        for evidence_path in evidence_paths:
            try:
                payload = json.loads(evidence_path.read_text(encoding="utf-8"))
                evidence_reports.append(ResearchReport.model_validate(payload))
            except Exception as exc:  # noqa: BLE001
                evidence_errors.append(f"{evidence_path.name}: {exc}")
        results.append(
            TestResult(
                name="evidence_json_valid",
                passed=len(evidence_errors) == 0,
                details="; ".join(evidence_errors) if evidence_errors else "All evidence JSON parsed as ResearchReport.",
            )
        )

        all_claims = [claim for report in evidence_reports for claim in report.claims]
        results.append(
            TestResult(
                name="claims_have_sources",
                passed=all(len(claim.source_ids) > 0 for claim in all_claims),
                details=f"Validated {len(all_claims)} claim(s).",
            )
        )

        unresolved_claim_sources: list[str] = []
        for report in evidence_reports:
            source_ids = {source.source_id for source in report.sources}
            for claim in report.claims:
                missing = [source_id for source_id in claim.source_ids if source_id not in source_ids]
                if missing:
                    unresolved_claim_sources.append(f"{report.workstream_id}:{claim.claim_id}:{','.join(missing)}")
        results.append(
            TestResult(
                name="claim_sources_resolve",
                passed=len(unresolved_claim_sources) == 0,
                details="; ".join(unresolved_claim_sources) if unresolved_claim_sources else "All claim source_ids resolved.",
            )
        )

        missing_identifiers: list[str] = []
        missing_source_metadata: list[str] = []
        for report in evidence_reports:
            for source in report.sources:
                if not any([source.url, source.doi, source.pmid, source.accession]):
                    missing_identifiers.append(f"{report.workstream_id}:{source.source_id}")
                if not source.source_type.strip() or not source.tier.strip():
                    missing_source_metadata.append(f"{report.workstream_id}:{source.source_id}")
        results.append(
            TestResult(
                name="sources_have_identifiers",
                passed=len(missing_identifiers) == 0 and len(missing_source_metadata) == 0,
                details=(
                    f"missing_identifiers={missing_identifiers}; missing_type_or_tier={missing_source_metadata}"
                    if missing_identifiers or missing_source_metadata
                    else "All sources include identifiers, source_type, and tier."
                ),
            )
        )

        contested_without_conflict: list[str] = []
        for report in evidence_reports:
            has_contested_claim = any(claim.status == "contested" for claim in report.claims)
            if has_contested_claim and not report.conflicts:
                contested_without_conflict.append(report.workstream_id)
        results.append(
            TestResult(
                name="conflicts_recorded_or_declared_absent",
                passed=len(contested_without_conflict) == 0,
                details=(
                    "Contested claims with no conflicts: " + ", ".join(contested_without_conflict)
                    if contested_without_conflict
                    else "Conflicts recorded or no contested claims present."
                ),
            )
        )

        total_chars = sum(f.stat().st_size for f in md_files)
        min_chars = 500
        meets_length = total_chars >= min_chars
        results.append(
            TestResult(
                name="minimum_length",
                passed=meets_length,
                details=f"Total output: {total_chars} chars (minimum: {min_chars}).",
            )
        )

        judgment = self._build_research_judgment(evidence_reports=evidence_reports, results=results)
        passed = (
            all(result.passed for result in results)
            and judgment.final_verdict == VerificationVerdict.pass_
            and judgment.final_action == VerificationAction.proceed
        )
        return TestReport(
            passed=passed,
            command="research_validation",
            results=results,
            stdout=f"Validated {len(md_files)} file(s), {total_chars} total chars.",
            stderr="" if passed else judgment.rationale or "Some validation checks failed.",
            judgment=judgment,
        )

    def _run_pytest(self, workspace_path: Path) -> TestReport:
        """기존 pytest 실행 로직 (원래 코드 그대로)"""
        tests_dir = workspace_path / "tests"
        if not tests_dir.exists():
            judgment = VerificationJudgment(
                final_verdict=VerificationVerdict.fail,
                final_action=VerificationAction.retry_workstream,
                retry_recommended=True,
                rationale="No tests directory found.",
            )
            return TestReport(
                passed=False,
                command="pytest -q",
                results=[TestResult(name="tests_present", passed=False, details="No tests directory found.")],
                stderr="No tests directory found.",
                judgment=judgment,
            )

        command = [sys.executable, "-m", "pytest", "-q"]
        completed = subprocess.run(
            command,
            cwd=workspace_path,
            capture_output=True,
            text=True,
            check=False,
        )
        passed = completed.returncode == 0
        judgment = VerificationJudgment(
            final_verdict=VerificationVerdict.pass_ if passed else VerificationVerdict.fail,
            final_action=VerificationAction.proceed if passed else VerificationAction.retry_workstream,
            retry_recommended=not passed,
            rationale="pytest passed." if passed else f"pytest failed with exit_code={completed.returncode}.",
        )
        return TestReport(
            passed=passed,
            command=" ".join(command),
            results=[
                TestResult(
                    name="pytest",
                    passed=passed,
                    details=f"exit_code={completed.returncode}",
                )
            ],
            stdout=completed.stdout,
            stderr=completed.stderr,
            judgment=judgment,
        )

    def _build_research_judgment(
        self,
        *,
        evidence_reports: list[ResearchReport],
        results: list[TestResult],
    ) -> VerificationJudgment:
        failed_checks = {result.name for result in results if not result.passed}
        evidence_quality_fail = bool(
            failed_checks
            & {
                "output_files_exist",
                "files_have_content",
                "sources_cited",
                "evidence_json_exists",
                "evidence_json_valid",
                "claims_have_sources",
                "claim_sources_resolve",
                "sources_have_identifiers",
                "conflicts_recorded_or_declared_absent",
                "minimum_length",
            }
        )
        scope_violation = any(self._report_has_policy_violation(report, "scope") for report in evidence_reports)
        new_data_violations = self._detect_new_data_violations(evidence_reports)
        new_data_forbidden_violation = len(new_data_violations) > 0
        requires_external_verification = any(
            self._report_requires_external_verification(report) for report in evidence_reports
        )
        requires_human_lock = scope_violation or new_data_forbidden_violation

        if new_data_forbidden_violation or scope_violation:
            final_verdict = VerificationVerdict.block
            final_action = VerificationAction.request_human_lock
            requires_human_lock = True
        elif evidence_quality_fail:
            final_verdict = VerificationVerdict.fail
            final_action = VerificationAction.retry_workstream
        elif requires_external_verification:
            final_verdict = VerificationVerdict.escalate
            final_action = VerificationAction.request_external_verification
        else:
            final_verdict = VerificationVerdict.pass_
            final_action = VerificationAction.proceed

        rationale_parts: list[str] = []
        if failed_checks:
            rationale_parts.append(f"Failed checks: {', '.join(sorted(failed_checks))}.")
        if scope_violation:
            rationale_parts.append("Research stage envelope reported a scope policy violation.")
        if new_data_violations:
            rationale_parts.append("; ".join(new_data_violations))
        if requires_external_verification:
            rationale_parts.append("Contested claims or unresolved conflicts require external verification.")
        if not rationale_parts:
            rationale_parts.append("Research validation passed with no safeguard escalations.")

        return VerificationJudgment(
            final_verdict=final_verdict,
            final_action=final_action,
            requires_human_lock=requires_human_lock,
            requires_external_verification=requires_external_verification,
            evidence_quality_fail=evidence_quality_fail,
            scope_violation=scope_violation,
            new_data_forbidden_violation=new_data_forbidden_violation,
            retry_recommended=final_action == VerificationAction.retry_workstream,
            rationale=" ".join(rationale_parts),
        )

    @staticmethod
    def _report_requires_external_verification(report: ResearchReport) -> bool:
        contested_claims = any(
            claim.status.strip().lower() in {"contested", "uncertain", "mixed"}
            for claim in report.claims
        )
        unresolved_conflicts = any(not conflict.resolution.strip() for conflict in report.conflicts)
        return contested_claims or unresolved_conflicts

    @staticmethod
    def _report_has_policy_violation(report: ResearchReport, keyword: str) -> bool:
        lowered_keyword = keyword.lower()
        return any(lowered_keyword in item.strip().lower() for item in report.stage_envelope.policy_violations)

    def _detect_new_data_violations(self, evidence_reports: list[ResearchReport]) -> list[str]:
        baseline_fingerprints: set[str] = set()
        for report in evidence_reports:
            if self._is_final_stage_report(report):
                continue
            for source in report.sources:
                fingerprint = self._source_fingerprint(source)
                if fingerprint:
                    baseline_fingerprints.add(fingerprint)

        violations: list[str] = []
        for report in evidence_reports:
            if not self._is_final_stage_report(report):
                continue
            lowered_policy_violations = [
                item.strip().lower() for item in report.stage_envelope.policy_violations if item.strip()
            ]
            if any(
                token in item
                for item in lowered_policy_violations
                for token in ("new_data", "new data", "new_source", "new source")
            ):
                violations.append(f"{report.workstream_id}: explicit new-data policy violation recorded.")

            carry_forward_ids = {
                item.strip().lower()
                for item in report.stage_envelope.carry_forward_source_ids
                if item.strip()
            }
            if carry_forward_ids:
                unexpected_source_ids = sorted(
                    source.source_id
                    for source in report.sources
                    if source.source_id.strip() and source.source_id.strip().lower() not in carry_forward_ids
                )
                if unexpected_source_ids:
                    violations.append(
                        f"{report.workstream_id}: source_ids outside carry-forward set ({', '.join(unexpected_source_ids)})."
                    )

            if baseline_fingerprints:
                new_sources: list[str] = []
                for source in report.sources:
                    fingerprint = self._source_fingerprint(source)
                    if fingerprint and fingerprint not in baseline_fingerprints:
                        new_sources.append(self._source_label(source))
                if new_sources:
                    unique_sources = list(dict.fromkeys(new_sources))
                    violations.append(
                        f"{report.workstream_id}: new sources introduced in MC1-1c ({', '.join(unique_sources[:3])})."
                    )
        return violations

    @staticmethod
    def _is_final_stage_report(report: ResearchReport) -> bool:
        haystack = f"{report.workstream_id} {report.stage_envelope.stage_name}".lower()
        return "mc1_1c" in haystack or "final_recommendation" in haystack

    @staticmethod
    def _source_fingerprint(source: ResearchSource) -> str:
        if source.doi and source.doi.strip():
            return f"doi:{source.doi.strip().lower()}"
        if source.pmid and source.pmid.strip():
            return f"pmid:{source.pmid.strip().lower()}"
        if source.accession and source.accession.strip():
            return f"accession:{source.accession.strip().lower()}"
        if source.url and source.url.strip():
            parsed = urlsplit(source.url.strip())
            normalized_url = urlunsplit(
                (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), "", "")
            )
            return f"url:{normalized_url}"
        if source.title.strip():
            return f"title:{source.source_type.strip().lower()}:{source.title.strip().lower()}"
        return f"id:{source.source_id.strip().lower()}" if source.source_id.strip() else ""

    @staticmethod
    def _source_label(source: ResearchSource) -> str:
        for candidate in (source.doi, source.pmid, source.accession, source.url, source.title, source.source_id):
            if candidate and candidate.strip():
                return candidate.strip()
        return "unknown-source"
