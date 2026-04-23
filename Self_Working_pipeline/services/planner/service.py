from __future__ import annotations

import re

from contracts.models import ApiContract, PlanBundle, UserRequest, Workstream
from core.prompting import compose_system_prompt
from services.adapters.base import JsonModelAdapter


class PlannerService:
    PRIORITY_KEYWORDS: tuple[tuple[str, ...], ...] = (
        ("goal", "summary", "objective", "overview"),
        ("scope", "out of scope", "deliverable", "outcome"),
        ("rule", "constraint", "guardrail", "absolute"),
        ("architecture", "environment", "directory", "stack"),
        ("roadmap", "phase", "milestone"),
        ("success", "metric", "quality"),
        ("instruction", "checklist", "first", "day 1"),
    )
    HARNESS_KEYWORDS: tuple[str, ...] = (
        "harness",
        "contract",
        "non-negotiable",
        "invariant",
        "source policy",
        "evidence policy",
        "output contract",
        "validation checklist",
        "scope boundary",
    )
    RESEARCH_PRESET_WORKSTREAMS: tuple[dict[str, object], ...] = (
        {
            "id": "mc1_1a_scope_and_evidence",
            "name": "MC1-1a Scope And Evidence",
            "layer": "mc1_1a",
            "objective": (
                "Lock the investigation scope, gather source-backed evidence, and produce the initial "
                "scope/evidence report for crop selection."
            ),
            "deliverables": [
                "reports/mc1_1a_scope_and_evidence.md",
                "research_evidence/mc1_1a_scope_and_evidence.json",
            ],
            "acceptance_criteria": [
                "Scope boundaries are explicit.",
                "Evidence JSON resolves every claim to sources.",
                "Open questions and missing evidence are stated.",
            ],
        },
        {
            "id": "mc1_1b_rescoring_and_top3",
            "name": "MC1-1b Rescoring And Top 3",
            "layer": "mc1_1b",
            "objective": (
                "Rescore the shortlisted options, compare tradeoffs, and produce a defendable Top 3 ranking."
            ),
            "deliverables": [
                "reports/mc1_1b_rescoring_and_top3.md",
                "research_evidence/mc1_1b_rescoring_and_top3.json",
            ],
            "dependencies": ["mc1_1a_scope_and_evidence"],
            "acceptance_criteria": [
                "Top 3 candidates are ranked with explicit criteria.",
                "Each ranking decision cites supporting evidence.",
                "Uncertainty and conflicts are called out.",
            ],
        },
        {
            "id": "external_verification",
            "name": "External Verification",
            "layer": "external_verification",
            "objective": (
                "Cross-check the Top 3 recommendation set with an external verification pass before the final crop lock."
            ),
            "deliverables": [
                "reports/external_verification.md",
                "research_evidence/external_verification.json",
            ],
            "dependencies": ["mc1_1b_rescoring_and_top3"],
            "acceptance_criteria": [
                "Independent cross-check confirms or challenges the Top 3.",
                "Any contested claims are surfaced explicitly.",
                "Human-lock escalation triggers are documented when needed.",
            ],
        },
        {
            "id": "mc1_1c_final_recommendation",
            "name": "MC1-1c Final Recommendation",
            "layer": "mc1_1c",
            "objective": (
                "Produce the final crop recommendation package using the locked evidence set without collecting new data."
            ),
            "deliverables": [
                "reports/mc1_1c_final_recommendation.md",
                "research_evidence/mc1_1c_final_recommendation.json",
            ],
            "dependencies": ["mc1_1b_rescoring_and_top3", "external_verification"],
            "acceptance_criteria": [
                "Final recommendation is consistent with the locked Top 3.",
                "No new data collection is introduced in MC1-1c.",
                "The output is ready for the final crop lock decision.",
            ],
        },
    )
    RESEARCH_API_INTERFACES: tuple[str, ...] = (
        (
            "ResearchSource(source_id, title, url|doi|pmid|accession, source_type, tier, "
            "retrieved_at, notes)"
        ),
        "ResearchClaim(claim_id, claim, source_ids, confidence, status, notes)",
        "ResearchConflict(conflict_id, topic, source_ids, description, resolution)",
        (
            "ResearchStageEnvelope(stage_name, stage_type, status, summary, artifact_paths, "
            "source_paths, claim_count, carry_forward_source_ids, known_gaps, policy_violations)"
        ),
        (
            "ResearchReport(workstream_id, scope, claims, sources, conflicts, gaps, "
            "confidence_summary, stage_envelope)"
        ),
        "ExecutionResult(workstream_id, summary, files, notes, research_report)",
        "ReviewIssue(severity, description, file_path, suggested_fix)",
        (
            "VerificationJudgment(final_verdict, final_action, requires_human_lock, "
            "requires_external_verification, evidence_quality_fail, scope_violation, "
            "new_data_forbidden_violation, retry_recommended, rationale)"
        ),
        "ReviewReport(workstream_id, approved, summary, issues, judgment)",
    )
    RESEARCH_API_EVENTS: tuple[str, ...] = (
        "scope_lock",
        "top3_lock",
        "final_crop_lock",
        "execution_saved",
        "review_saved",
        "approval_recorded",
    )
    RESEARCH_API_STORAGE: tuple[str, ...] = (
        "plans/<yyyy-mm-dd>/<run_id>/plan_bundle.json",
        "plans/<yyyy-mm-dd>/<run_id>/directions/latest_direction.json",
        "plans/<yyyy-mm-dd>/<run_id>/versions/v###_plan_bundle.json",
        "outputs/<yyyy-mm-dd>/<run_id>/workspace/reports/<workstream_id>.md",
        "outputs/<yyyy-mm-dd>/<run_id>/workspace/research_evidence/<workstream_id>.json",
        "outputs/<yyyy-mm-dd>/<run_id>/executions/<workstream_id>.json",
        "outputs/<yyyy-mm-dd>/<run_id>/reviews/<workstream_id>.json",
        "outputs/pipeline.db",
    )

    def __init__(
        self,
        adapter: JsonModelAdapter,
        *,
        guidance_prompt: str = "",
        request_digest_chars: int = 4000,
        mode: str = "code",
    ) -> None:
        self.adapter = adapter
        self.guidance_prompt = guidance_prompt
        self.request_digest_chars = request_digest_chars
        self.mode = mode

    def _split_markdown_sections(self, text: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
        preamble: list[str] = []
        sections: list[tuple[str, list[str]]] = []
        current_heading: str | None = None
        current_lines: list[str] = []

        for line in text.splitlines():
            if re.match(r"^\s{0,3}#{1,6}\s+", line):
                if current_heading is None:
                    if current_lines:
                        preamble.extend(current_lines)
                else:
                    sections.append((current_heading, current_lines[:]))
                current_heading = line.strip()
                current_lines = []
                continue
            current_lines.append(line)

        if current_heading is None:
            if current_lines:
                preamble.extend(current_lines)
        else:
            sections.append((current_heading, current_lines[:]))
        return preamble, sections

    def _section_priority(self, heading: str) -> int:
        lowered = heading.lower()
        for index, keywords in enumerate(self.PRIORITY_KEYWORDS):
            if any(keyword in lowered for keyword in keywords):
                return index
        return len(self.PRIORITY_KEYWORDS)

    def _trim_section_body(self, lines: list[str], *, max_chars: int) -> str:
        kept: list[str] = []
        total = 0
        for raw_line in lines:
            line = raw_line.rstrip()
            if not line and (not kept or not kept[-1]):
                continue
            candidate = line[:240]
            projected = total + len(candidate) + 1
            if kept and projected > max_chars:
                break
            if not kept and projected > max_chars:
                kept.append(candidate[: max_chars - 3].rstrip() + "...")
                return "\n".join(kept)
            kept.append(candidate)
            total = projected
        return "\n".join(kept).strip()

    def _extract_preserved_sections(self, sections: list[tuple[str, list[str]]]) -> list[tuple[str, str]]:
        preserved: list[tuple[str, str]] = []
        for heading, body_lines in sections:
            if any(keyword in heading.lower() for keyword in self.HARNESS_KEYWORDS):
                preserved.append((heading, "\n".join(body_lines).strip()))
        return preserved

    def condense_request(self, raw_request: str) -> str:
        text = raw_request.strip()
        if len(text) <= self.request_digest_chars:
            return text

        preamble, sections = self._split_markdown_sections(text)
        preserved_sections = self._extract_preserved_sections(sections)
        if not sections:
            head = text[: self.request_digest_chars // 2].rstrip()
            tail = text[-(self.request_digest_chars // 3) :].lstrip()
            digest = (
                "Condensed request digest:\n"
                f"{head}\n\n"
                "[...]\n\n"
                f"{tail}"
            )
            return digest[: self.request_digest_chars].rstrip()

        preamble_text = self._trim_section_body(preamble, max_chars=500)
        ordered_sections = sorted(
            enumerate(sections),
            key=lambda item: (self._section_priority(item[1][0]), item[0]),
        )

        lines = [
            f"Condensed planning digest from a longer request ({len(text)} chars).",
            "Preserve the original intent, rules, and milestones while keeping the plan compact.",
        ]
        if preserved_sections:
            lines.append("")
            lines.append("## Non-Negotiable Harness Sections")
            for heading, section_text in preserved_sections:
                lines.extend(["", heading, section_text])
        if preamble_text:
            lines.extend(["", "## Request Overview", preamble_text])

        remaining = max(self.request_digest_chars - len("\n".join(lines)) - 1, 600)
        for _, (heading, body_lines) in ordered_sections:
            if remaining <= 160:
                break
            body_budget = min(remaining - len(heading) - 8, 520)
            if body_budget < 80:
                break
            trimmed_body = self._trim_section_body(body_lines, max_chars=body_budget)
            if not trimmed_body:
                continue
            block = f"\n\n{heading}\n{trimmed_body}"
            if len("\n".join(lines)) + len(block) > self.request_digest_chars:
                continue
            lines.append("")
            lines.append(heading)
            lines.append(trimmed_body)
            remaining = self.request_digest_chars - len("\n".join(lines))

        digest = "\n".join(lines).strip()
        if len(digest) > self.request_digest_chars:
            return digest[: self.request_digest_chars].rstrip()
        return digest

    def create_plan(self, user_request: UserRequest) -> PlanBundle:
        planning_request = self.condense_request(user_request.raw_request)
        request_label = "Planning digest" if planning_request != user_request.raw_request else "User request"
        if self.mode == "research":
            system_prompt = compose_system_prompt(
                (
                    "You are a research planning agent for a multi-agent investigation pipeline. "
                    "Decompose the investigation request into focused research workstreams. "
                    "This repository expects the MC1-1 crop-selection workflow to remain first-class."
                ),
                self.guidance_prompt,
                section_name="research planning, topic decomposition, and investigation methodology",
            )
            user_prompt = (
                "Create a research plan bundle for the following investigation request.\n"
                "Requirements:\n"
                "- use the fixed MC1-1 workflow structure: mc1_1a_scope_and_evidence, "
                "mc1_1b_rescoring_and_top3, external_verification, mc1_1c_final_recommendation\n"
                "- each workstream should have clear deliverables (markdown reports plus evidence JSON)\n"
                "- include verification and human-lock semantics in the plan\n"
                "- prioritize authoritative and primary sources\n"
                "- keep workstreams small enough to be completed in one research session\n\n"
                "- HarnessContract fields are non-negotiable and must be filled when present in the request\n\n"
                f"{request_label}:\n{planning_request}\n\n"
                "Return JSON only."
            )
        else:
            system_prompt = compose_system_prompt(
                (
                    "You are Claude Code acting as the architecture and planning lead for a multi-agent "
                    "software delivery pipeline. Produce a compact but implementation-ready plan bundle."
                ),
                self.guidance_prompt,
                section_name="planning, specification, workflow rules, and repository expectations",
            )
            user_prompt = (
                "Create a plan bundle for the following natural language request.\n"
                "Requirements:\n"
                "- produce project brief, architecture spec, API contract, workstreams, and test plan\n"
                "- keep workstreams small and verifiable\n"
                "- make deliverables concrete enough for a coding agent to execute\n"
                "- prefer a Python-first local MVP if the request does not force another stack\n\n"
                f"{request_label}:\n{planning_request}\n\n"
                "Return JSON only."
            )
        result = self.adapter.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=PlanBundle,
        )
        assert isinstance(result, PlanBundle)
        if self.mode == "research":
            result = self._apply_research_preset(result)
        return result

    def _apply_research_preset(self, plan_bundle: PlanBundle) -> PlanBundle:
        workstreams = [
            Workstream(
                id=str(spec["id"]),
                name=str(spec["name"]),
                layer=str(spec["layer"]),
                objective=str(spec["objective"]),
                deliverables=list(spec["deliverables"]),
                dependencies=list(spec.get("dependencies", [])),
                acceptance_criteria=list(spec["acceptance_criteria"]),
            )
            for spec in self.RESEARCH_PRESET_WORKSTREAMS
        ]

        deliverables = list(plan_bundle.project_brief.deliverables)
        for item in [
            "Structured markdown reports for each MC1-1 stage",
            "Evidence JSON for each MC1-1 stage",
            "Gate-ready review package for scope_lock, top3_lock, and final_crop_lock",
        ]:
            if item not in deliverables:
                deliverables.append(item)

        test_plan = list(plan_bundle.test_plan)
        for item in [
            "Validate reports and evidence JSON for every MC1-1 stage",
            "Require scope_lock, top3_lock, and final_crop_lock before advancing",
            "Reject MC1-1c outputs that introduce new data collection",
        ]:
            if item not in test_plan:
                test_plan.append(item)

        plan_bundle.api_contract = self._build_research_api_contract()
        plan_bundle.project_brief.deliverables = deliverables
        plan_bundle.workstreams = workstreams
        plan_bundle.test_plan = test_plan
        return plan_bundle

    def _build_research_api_contract(self) -> ApiContract:
        return ApiContract(
            interfaces=list(self.RESEARCH_API_INTERFACES),
            endpoints=[],
            events=list(self.RESEARCH_API_EVENTS),
            storage=list(self.RESEARCH_API_STORAGE),
        )
