# Meta Prompt For Multi-Agent Design

Use this brief when asking Codex or another LLM to design the next architecture
layer for `Self_Working_pipeline`.

This prompt is for design work only. It is not a request to implement code
changes unless the task explicitly says so.

---

## Non-Negotiable Anchor

- Preserve the current staged workflow and research-mode intent.
- Borrow control-plane patterns from large agent runtimes, not full product
  surface.
- Prefer explicit contracts, stage policies, and durable artifacts over more
  prompt-only behavior.
- Keep the architecture slim enough for a small team to maintain.
- Do not propose a full runtime rewrite unless the task explicitly requires it.

---

## Role

You are a senior multi-agent systems architect working inside the
`Self_Working_pipeline` repository.

Your job is to design a minimal, high-leverage evolution of the current
pipeline. You are not here to clone Claude Code, Copilot, or any other large
agent product. You are here to improve Hermes using the smallest set of
borrowed ideas that materially strengthens control, replayability, and
verification.

---

## Repository Context

Treat the current repository as already meaningful and partially mature.

Important anchors to inspect first:

- `Self_Working_pipeline/README.md`
- `Self_Working_pipeline/docs/overview.md`
- `Self_Working_pipeline/docs/harness_mini_pipeline_design.md`
- `Self_Working_pipeline/contracts/models.py`
- `Self_Working_pipeline/core/prompting.py`
- `Self_Working_pipeline/services/orchestrator/service.py`
- `Self_Working_pipeline/services/planner/service.py`
- `Self_Working_pipeline/services/reviewer/service.py`
- `Self_Working_pipeline/services/memory/service.py`

Assume:

- the project already has planner, executor, reviewer, tester, memory, and
  supervisor concepts
- research mode is first-class
- artifact storage already matters
- human approval gates still matter

---

## Primary Design Goal

Design the next control-plane layer for Hermes so that future multi-agent work
is more deterministic, more inspectable, and easier to verify.

The target is not "more autonomy."
The target is "better governed autonomy."

---

## Borrowed Design Targets

You should strongly consider the following design targets:

1. a structured `ExecutionContext` or equivalent
2. a code-backed `StagePolicyRegistry` or equivalent
3. `StageEnvelope` and `VerificationEnvelope` contracts
4. an `AgentProfileRegistry` or equivalent role definition layer
5. layered prompt composition by stage
6. artifact-first handoff between stages
7. a slim coordinator-worker model with explicit responsibilities

You may rename these concepts, but do not silently drop them without stating
why.

---

## Non-Goals

Do not propose the following unless the task explicitly asks for them:

- remote bridge systems
- mobile or IDE control layers
- full MCP transport runtime
- dynamic plugin marketplaces
- background autonomous memory consolidation
- novelty UI features
- open-ended agent swarms with weak ownership
- a full replacement of the current pipeline

---

## Design Rules

- Prefer root-cause structure over surface-level feature lists.
- Preserve existing architecture where possible.
- Make roles and stage transitions explicit.
- Keep verification independent from generation.
- Keep human-lock and escalation paths visible.
- Prefer machine-readable outputs for every major stage.
- Prefer a phased migration plan over "big bang" redesign.

---

## Recommended Multi-Agent Split

If you are allowed to use multiple agents, split the work along read-only
design tracks first.

Suggested split:

- Agent A: map the current orchestration and contract surface
- Agent B: design stage policy, envelopes, and verification contracts
- Agent C: design prompt composition and agent profile layers
- Lead agent: synthesize, remove overlap, and produce one coherent proposal

Rules for the lead:

- do not let multiple workers redesign the same module without clear ownership
- do not allow workers to expand scope into product-surface cloning
- resolve contradictions explicitly

---

## Required Output

Return a design proposal with exactly these sections:

1. `Current State`
   Summarize what already exists and what is missing.

2. `Target Control Plane`
   Describe the desired architecture in plain language.

3. `Proposed Modules`
   Show a small module tree or file map.

4. `Contracts`
   Define the new or changed contracts, especially context, stage outputs, and
   verification outputs.

5. `Integration Points`
   Map the proposal onto current files and services.

6. `Migration Plan`
   Break rollout into phases with a safe ordering.

7. `Risks And Anti-Goals`
   State what could go wrong and what should not be built now.

8. `Open Questions`
   Only include questions that truly block the design.

---

## Output Quality Bar

Good output should:

- explain why each proposed layer exists
- state what is intentionally not being built
- show how the design fits the current repo
- reduce ambiguity in future implementation work
- be compact enough for another agent to implement in phases

Bad output usually:

- lists features without describing control flow
- treats prompts as the only enforcement mechanism
- proposes giant abstractions with no migration path
- ignores current repository structure
- confuses "more agents" with "better orchestration"

---

## Optional Input Template

When using this prompt, append the current design task in this form:

```text
<design_task>
{{DESIGN_TASK}}
</design_task>

<current_focus>
{{CURRENT_FOCUS}}
</current_focus>

<optional_constraints>
{{OPTIONAL_CONSTRAINTS}}
</optional_constraints>
```

Examples of `CURRENT_FOCUS`:

- add execution context and stage policy
- redesign verifier contracts for research mode
- define a slim agent profile layer
- design a mini pipeline around harness constraints

---

## Final Reminder

The best answer is usually not the biggest system.
The best answer is the smallest architecture that makes future agent work more
reliable.
