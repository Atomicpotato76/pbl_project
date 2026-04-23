from __future__ import annotations

from contracts.models import ApprovalStage, ResearchGate, RunStage


class InvalidStageTransition(ValueError):
    """Raised when the orchestrator attempts an invalid stage change."""


class HermesStateMachine:
    RESEARCH_LAYER_SEQUENCE: tuple[str, ...] = (
        "mc1_1a",
        "mc1_1b",
        "external_verification",
        "mc1_1c",
    )
    RESEARCH_GATE_BY_LAYER: dict[str, ResearchGate] = {
        "mc1_1a": ResearchGate.scope_lock,
        "mc1_1b": ResearchGate.top3_lock,
        "external_verification": ResearchGate.final_crop_lock,
    }
    RESEARCH_VERIFICATION_LAYERS: frozenset[str] = frozenset({"external_verification"})
    allowed_transitions: dict[RunStage, set[RunStage]] = {
        RunStage.intake: {RunStage.planning},
        RunStage.planning: {RunStage.plan_approved},
        RunStage.plan_approved: {RunStage.executing},
        RunStage.executing: {RunStage.reviewing, RunStage.testing},
        RunStage.reviewing: {RunStage.executing, RunStage.testing},
        RunStage.testing: {RunStage.executing, RunStage.merge_approved},
        RunStage.merge_approved: {RunStage.packaging},
        RunStage.packaging: {RunStage.completed},
        RunStage.completed: set(),
    }

    @classmethod
    def research_gate_for_layer(cls, layer: str | None) -> ResearchGate | None:
        if layer is None:
            return None
        return cls.RESEARCH_GATE_BY_LAYER.get(layer)

    @classmethod
    def research_layer_index(cls, layer: str | None) -> int | None:
        if layer is None:
            return None
        try:
            return cls.RESEARCH_LAYER_SEQUENCE.index(layer)
        except ValueError:
            return None

    @classmethod
    def missing_research_prerequisites(cls, layer: str | None, completed_layers: set[str]) -> list[str]:
        layer_index = cls.research_layer_index(layer)
        if layer_index is None or layer_index == 0:
            return []
        return [
            candidate
            for candidate in cls.RESEARCH_LAYER_SEQUENCE[:layer_index]
            if candidate not in completed_layers
        ]

    @classmethod
    def is_research_verification_layer(cls, layer: str | None) -> bool:
        return layer in cls.RESEARCH_VERIFICATION_LAYERS

    @classmethod
    def approval_phase_key(cls, stage: ApprovalStage, research_gate: ResearchGate | None = None) -> str:
        if stage == ApprovalStage.checkpoint and research_gate is not None:
            return f"{stage.value}:{research_gate.value}"
        return stage.value

    def ensure_transition(self, current: RunStage, target: RunStage) -> None:
        if current == target:
            return
        if target not in self.allowed_transitions[current]:
            raise InvalidStageTransition(f"Cannot move from {current} to {target}.")
