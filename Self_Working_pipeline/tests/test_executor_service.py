from contracts.models import (
    ApiContract,
    ArchitectureSpec,
    ExecutionResult,
    GeneratedFile,
    PlanBundle,
    ProjectBrief,
    ResearchClaim,
    ResearchReport,
    ResearchSource,
    TaskAssignment,
    Workstream,
)
from services.executor.service import ExecutionEnvelope, ExecutorService


class FakeAdapter:
    def __init__(self, result: ExecutionResult) -> None:
        self._result = result

    def generate_structured(self, *, system_prompt, user_prompt, response_model):  # noqa: ANN001
        return ExecutionEnvelope(result=self._result)


class CapturingAdapter:
    def __init__(self, result: ExecutionResult) -> None:
        self._result = result
        self.system_prompt = ""
        self.user_prompt = ""

    def generate_structured(self, *, system_prompt, user_prompt, response_model):  # noqa: ANN001
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return ExecutionEnvelope(result=self._result)


def test_research_executor_populates_stage_envelope_and_carry_forward_sources() -> None:
    previous_report = ResearchReport(
        workstream_id="mc1_1b_rescoring_and_top3",
        scope="scope",
        claims=[
            ResearchClaim(
                claim_id="c-prev",
                claim="Previous claim",
                source_ids=["s-prev"],
                confidence="high",
                status="supported",
            )
        ],
        sources=[
            ResearchSource(
                source_id="s-prev",
                title="Previous source",
                url="https://example.com/prev",
                source_type="official",
                tier="primary",
            )
        ],
    )
    workspace_snapshot = "## research_evidence/mc1_1b_rescoring_and_top3.json\n" + previous_report.model_dump_json(indent=2)
    result = ExecutionResult(
        workstream_id="mc1_1c_final_recommendation",
        summary="final recommendation ready",
        files=[GeneratedFile(path="reports/mc1_1c_final_recommendation.md", content="# final")],
        research_report=ResearchReport(
            workstream_id="mc1_1c_final_recommendation",
            scope="final scope",
            claims=[
                ResearchClaim(
                    claim_id="c-final",
                    claim="Final claim",
                    source_ids=["s-prev"],
                    confidence="high",
                    status="supported",
                )
            ],
            sources=[
                ResearchSource(
                    source_id="s-prev",
                    title="Previous source",
                    url="https://example.com/prev",
                    source_type="official",
                    tier="primary",
                )
            ],
        ),
    )
    plan_bundle = PlanBundle(
        project_brief=ProjectBrief(
            title="Research plan",
            objective="Find the final crop recommendation.",
            audience="Researchers",
            scope=["MC1-1"],
            deliverables=["reports"],
        ),
        architecture_spec=ArchitectureSpec(
            overview="overview",
            components=["reports"],
            data_flow=["sources -> recommendation"],
            decisions=["keep it structured"],
        ),
        api_contract=ApiContract(interfaces=["CLI"]),
        workstreams=[
            Workstream(
                id="mc1_1c_final_recommendation",
                name="MC1-1c Final Recommendation",
                layer="mc1_1c",
                objective="Produce the final recommendation without new data.",
                deliverables=["reports/mc1_1c_final_recommendation.md"],
                acceptance_criteria=["ready"],
            )
        ],
        test_plan=["validate evidence"],
    )
    service = ExecutorService(adapter=FakeAdapter(result), mode="research")

    normalized = service.execute(
        assignment=TaskAssignment(
            run_id="run-1",
            workstream_id="mc1_1c_final_recommendation",
            agent_role="codex-executor",
            instructions="do the final stage",
        ),
        plan_bundle=plan_bundle,
        workspace_snapshot=workspace_snapshot,
        review_feedback=[],
    )

    assert normalized.research_report is not None
    envelope = normalized.research_report.stage_envelope
    assert envelope.stage_name == "mc1_1c"
    assert envelope.claim_count == 1
    assert envelope.carry_forward_source_ids == ["s-prev"]
    assert "reports/mc1_1c_final_recommendation.md" in envelope.artifact_paths
    assert "research_evidence/mc1_1b_rescoring_and_top3.json" in envelope.source_paths


def test_infer_policy_violations_ignores_benign_scope_language() -> None:
    violations = ExecutorService._infer_policy_violations(
        review_feedback=[
            "Scope boundaries are explicit and no scope drift was found.",
            "Keep the scope report readable for the next stage.",
        ]
    )

    assert violations == []


def test_infer_policy_violations_detects_real_scope_violation() -> None:
    violations = ExecutorService._infer_policy_violations(
        review_feedback=["A real scope violation was detected and the stage went out of scope."]
    )

    assert violations == ["scope_violation"]


def test_research_executor_prompt_forbids_snippet_only_evidence() -> None:
    result = ExecutionResult(
        workstream_id="mc1_1a_scope_and_evidence",
        summary="scope evidence ready",
        files=[GeneratedFile(path="reports/mc1_1a_scope_and_evidence.md", content="# scope")],
        research_report=ResearchReport(
            workstream_id="mc1_1a_scope_and_evidence",
            scope="scope",
            claims=[
                ResearchClaim(
                    claim_id="c1",
                    claim="Apple is diploid.",
                    source_ids=["s1"],
                    confidence="medium",
                    status="provisional",
                )
            ],
            sources=[
                ResearchSource(
                    source_id="s1",
                    title="Source",
                    url="https://example.com",
                    source_type="official",
                    tier="primary",
                )
            ],
        ),
    )
    adapter = CapturingAdapter(result)
    plan_bundle = PlanBundle(
        project_brief=ProjectBrief(
            title="Research plan",
            objective="Answer a small question.",
            audience="Researchers",
            scope=["single question"],
            deliverables=["reports"],
        ),
        architecture_spec=ArchitectureSpec(
            overview="overview",
            components=["reports"],
            data_flow=["sources -> report"],
            decisions=["keep it structured"],
        ),
        api_contract=ApiContract(interfaces=["CLI"]),
        workstreams=[
            Workstream(
                id="mc1_1a_scope_and_evidence",
                name="MC1-1a Scope And Evidence",
                layer="mc1_1a",
                objective="Lock scope and gather evidence.",
                deliverables=["reports/mc1_1a_scope_and_evidence.md"],
                acceptance_criteria=["ready"],
            )
        ],
        test_plan=["validate evidence"],
    )
    service = ExecutorService(adapter=adapter, mode="research")

    service.execute(
        assignment=TaskAssignment(
            run_id="run-1",
            workstream_id="mc1_1a_scope_and_evidence",
            agent_role="codex-executor",
            instructions="research the assigned question",
        ),
        plan_bundle=plan_bundle,
        workspace_snapshot="",
        review_feedback=[],
    )

    assert "do not treat search-result snippets as sole evidence" in adapter.user_prompt
    assert "inspect the underlying source content directly" in adapter.user_prompt
    assert "mark that claim provisional and explain the inference boundary" in adapter.user_prompt
