from contracts.models import UserRequest, Workstream
from services.planner.service import PlannerService
from tests.helpers import sample_plan_bundle


def test_condense_request_keeps_short_text() -> None:
    planner = PlannerService(object(), request_digest_chars=200)

    raw = "Build a small Python CLI with tests."

    assert planner.condense_request(raw) == raw


def test_condense_request_prioritizes_key_sections() -> None:
    planner = PlannerService(object(), request_digest_chars=700)
    raw = "\n".join(
        [
            "# Big Proposal",
            "",
            "Intro line " * 20,
            "",
            "## Reference Links",
            "- filler " * 40,
            "",
            "## Project Goal",
            "- build the core pipeline",
            "- keep approvals in the loop",
            "",
            "## Absolute Rules",
            "- do not modify legacy files",
            "- always add tests",
            "",
            "## First Milestone",
            "- create API contract",
            "- create router v5 plan",
        ]
    )

    digest = planner.condense_request(raw)

    assert "Condensed planning digest" in digest
    assert "## Project Goal" in digest
    assert "## Absolute Rules" in digest
    assert "## First Milestone" in digest
    assert len(digest) <= 700


def test_create_plan_uses_digest_for_long_requests() -> None:
    plan_bundle = sample_plan_bundle(
        [
            Workstream(
                id="WS1",
                name="Foundation",
                layer="infrastructure",
                objective="Build the first slice.",
                deliverables=["router_v5.py"],
                acceptance_criteria=["pytest passes"],
            )
        ]
    )
    captured: dict[str, str] = {}

    class CapturingAdapter:
        def generate_structured(self, *, system_prompt: str, user_prompt: str, response_model):
            captured["system_prompt"] = system_prompt
            captured["user_prompt"] = user_prompt
            return plan_bundle

    planner = PlannerService(CapturingAdapter(), request_digest_chars=500)
    raw_request = "# Project Goal\n" + ("Build a long request.\n" * 120)

    result = planner.create_plan(UserRequest(raw_request=raw_request))

    assert result == plan_bundle
    assert "Planning digest:" in captured["user_prompt"]
    assert "Condensed planning digest" in captured["user_prompt"]


def test_condense_request_preserves_harness_sections() -> None:
    planner = PlannerService(object(), request_digest_chars=550)
    raw = "\n".join(
        [
            "# Proposal",
            "intro " * 100,
            "## Harness Contract",
            "- invariant: never modify scope",
            "- output contract: include evidence",
            "## Background",
            "filler " * 300,
        ]
    )

    digest = planner.condense_request(raw)

    assert "## Non-Negotiable Harness Sections" in digest
    assert "## Harness Contract" in digest
    assert "invariant: never modify scope" in digest


def test_research_mode_applies_mc1_1_preset_workstreams() -> None:
    plan_bundle = sample_plan_bundle(
        [
            Workstream(
                id="freeform",
                name="Freeform Research",
                layer="research",
                objective="This should be replaced by the preset.",
                deliverables=["reports/freeform.md"],
                acceptance_criteria=["placeholder"],
            )
        ]
    )

    class StaticAdapter:
        def generate_structured(self, *, system_prompt: str, user_prompt: str, response_model):
            return plan_bundle

    planner = PlannerService(StaticAdapter(), mode="research")

    result = planner.create_plan(UserRequest(raw_request="Plan MC1-1 crop selection research"))

    assert [item.id for item in result.workstreams] == [
        "mc1_1a_scope_and_evidence",
        "mc1_1b_rescoring_and_top3",
        "external_verification",
        "mc1_1c_final_recommendation",
    ]
    assert result.workstreams[-1].dependencies == ["mc1_1b_rescoring_and_top3", "external_verification"]
    assert "Gate-ready review package for scope_lock, top3_lock, and final_crop_lock" in result.project_brief.deliverables


def test_research_mode_overwrites_api_contract_with_runtime_schema() -> None:
    plan_bundle = sample_plan_bundle(
        [
            Workstream(
                id="freeform",
                name="Freeform Research",
                layer="research",
                objective="This should be replaced by the preset.",
                deliverables=["reports/freeform.md"],
                acceptance_criteria=["placeholder"],
            )
        ]
    )
    plan_bundle.api_contract.interfaces = ["EvidenceRecord", "ScoreEntry"]
    plan_bundle.api_contract.endpoints = []
    plan_bundle.api_contract.events = ["fake_event"]
    plan_bundle.api_contract.storage = ["outputs/freeform.json"]

    class StaticAdapter:
        def generate_structured(self, *, system_prompt: str, user_prompt: str, response_model):
            return plan_bundle

    planner = PlannerService(StaticAdapter(), mode="research")

    result = planner.create_plan(UserRequest(raw_request="Plan MC1-1 crop selection research"))

    assert result.api_contract.endpoints == []
    assert "EvidenceRecord" not in result.api_contract.interfaces
    assert "ScoreEntry" not in result.api_contract.interfaces
    assert any(item.startswith("ResearchReport(") for item in result.api_contract.interfaces)
    assert any(item.startswith("VerificationJudgment(") for item in result.api_contract.interfaces)
    assert result.api_contract.events[:3] == ["scope_lock", "top3_lock", "final_crop_lock"]
    assert "outputs/<yyyy-mm-dd>/<run_id>/workspace/research_evidence/<workstream_id>.json" in result.api_contract.storage
