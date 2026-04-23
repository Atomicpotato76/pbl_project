# Multi-Agent Design Adoption Guide

## Purpose

This document distills the architecture patterns worth borrowing from a large
agent runtime such as Claude Code into a form that fits `Self_Working_pipeline`.
It is a design reference, not a copy plan.

Use this guide when we ask Codex or another LLM to design the next iteration of
Hermes. The target is a stronger control plane for research and implementation
pipelines, while keeping the codebase small enough to evolve safely.

## Design Position

We should borrow control-plane ideas, not product surface.

That means:

- Prefer explicit contracts over implicit prompt behavior.
- Prefer stage policies over broad autonomy.
- Prefer artifact-first execution over chat-first execution.
- Prefer a slim coordinator and a few specialist roles over open-ended swarms.
- Prefer design patterns that fit the current staged workflow over full runtime
  replacement.

## What To Borrow Now

### 1. Execution Context

Introduce a single structured execution context object that follows every stage.

Recommended fields:

- `run_id`
- `pipeline_mode`
- `current_stage`
- `workspace_root`
- `outputs_root`
- `allowed_tool_families`
- `forbidden_actions`
- `harness_contract`
- `evidence_policy`
- `retry_budget`
- `requires_human_lock`
- `plan_version`
- `active_gate`

Why this matters:

- Current state is spread across contracts, orchestrator logic, and stored
  artifacts.
- A single context object reduces hidden coupling between planner, executor,
  reviewer, cross verifier, tester, and supervisor.

### 2. Stage Policy Registry

Move stage rules out of prompt prose and into code-backed policy.

Each stage should declare:

- allowed actions
- forbidden actions
- required artifacts
- required verification checks
- escalation conditions
- retry eligibility
- human-lock conditions

This is the highest-value idea to borrow. It turns "please do not do X" into a
deterministic system rule.

### 3. Stage Envelope And Verification Envelope

Every stage should emit two things:

- a machine-readable stage envelope
- a human-readable report or summary

Recommended stage envelope fields:

- `stage_name`
- `stage_type`
- `status`
- `summary`
- `artifact_paths`
- `source_paths`
- `claim_count`
- `carry_forward`
- `known_gaps`
- `policy_violations`

Recommended verification envelope fields:

- `final_verdict`
- `final_action`
- `requires_human_lock`
- `requires_external_verification`
- `scope_violation`
- `new_data_forbidden_violation`
- `evidence_quality_fail`
- `retry_recommended`
- `rationale`

Pass or fail is too small for the decisions this pipeline needs to make.

### 4. Agent Profile Registry

Define explicit profiles for the main roles instead of letting role behavior
live only inside prompts.

Recommended initial profiles:

- `planner`
- `executor`
- `reviewer`
- `cross_verifier`
- `reporter`
- `supervisor`

Each profile should specify:

- responsibility
- output contract
- preferred model family
- reasoning effort
- allowed tool families
- forbidden actions
- failure handoff behavior

This gives us a stable control layer even if models change later.

### 5. Prompt Composition Layers

Prompts should be built from layers in a fixed order:

1. repository safety rules
2. pipeline-mode rules
3. stage policy
4. task-specific request digest
5. current artifacts and evidence
6. output schema

This fits the current direction of `core/prompting.py`, which already composes
repository guidance, but it needs to become more stage-aware.

### 6. Artifact-First Storage

Every non-trivial stage should leave durable outputs that another agent can
consume without replaying the whole session.

Artifact-first means:

- stage outputs are durable
- verification is durable
- summaries are durable
- direction snapshots are durable
- a later agent can resume from artifacts instead of from chat memory alone

This is already a strength of Hermes. Keep it and make the contracts stricter.

### 7. Slim Coordinator-Worker Pattern

Keep orchestration small and legible.

Recommended operating model:

- one lead orchestrator
- one planner
- one executor
- one reviewer
- one dedicated external cross verifier

Do not optimize for arbitrary agent fan-out yet. Optimize for trust, replay,
and stage discipline.

## Borrow Later, In Reduced Form

These are useful, but should stay small at first.

### 1. Small Skills Or Playbooks Registry

Good use:

- repeatable research recipes
- standard verification recipes
- report-format templates

Bad use:

- full plugin marketplace
- dynamic discovery-heavy runtime

### 2. Scoped Memory

Useful memory types:

- failure memory
- reusable evidence heuristics
- project conventions

Avoid background autonomous consolidation at this stage. Keep memory explicit
and scoped.

### 3. Tool Registry Or MCP Layer

Only worth expanding when we have several stable external tools that need
uniform access control and shared contracts.

Before that, a lightweight registry plus stage allowlists is enough.

## What Not To Borrow

These add more operational surface than value for the current project.

- remote bridge or mobile control layers
- full MCP transport and auth runtime
- dynamic plugin loaders
- background "dream" or autonomous memory consolidation
- novelty product features
- broad feature-flag infrastructure
- open-ended nested agent swarms

## How This Maps To The Current Codebase

Current anchors:

- `services/orchestrator/service.py` is the right place to remain the lead
  control plane.
- `services/planner/service.py` already understands harness-specific request
  condensation and research presets.
- `services/reviewer/service.py` already separates review behavior by mode.
- `services/cross_verifier/service.py` is the natural place for independent
  external-verification prompts and policy handoff.
- `contracts/models.py` is the natural place to evolve envelopes and policy
  contracts.
- `core/prompting.py` is the right place for layered prompt composition.
- `services/memory/service.py` already supports artifact-first state and should
  remain the persistence anchor.
- `docs/harness_mini_pipeline_design.md` already points toward policy-backed
  verification and stage rules.

## Recommended Future Module Targets

If we implement these ideas, prefer small additions over large rewrites.

Suggested module targets:

- `mini_pipeline/agent_context.py`
- `mini_pipeline/stage_policy.py`
- `mini_pipeline/agent_profiles.py`
- `mini_pipeline/stage_envelopes.py`
- `mini_pipeline/prompt_composer.py`
- `mini_pipeline/verification_policy.py`

These names are suggestions, not mandatory filenames. The main goal is to make
control-plane concerns explicit.

## Recommended LLM Deliverables

When assigning design work to Codex or another LLM, require all of the
following:

1. architecture summary
2. proposed module tree
3. contract additions and schema changes
4. integration points with current files
5. migration plan in phases
6. risks and anti-goals
7. open questions that actually block implementation

## Review Checklist

Before accepting a design proposal, confirm:

- It preserves the current staged workflow.
- It strengthens explicit contracts instead of hiding more logic in prompts.
- It does not import a huge runtime surface.
- It explains what remains human-gated.
- It defines machine-readable outputs for each important stage.
- It keeps verification independent from generation.
- It leaves room for research mode and code mode to diverge cleanly.

## Bottom Line

The right lesson from a large agent runtime is not "build the whole thing."
The right lesson is "make the control plane explicit."

For Hermes, the highest-value design targets are:

- execution context
- stage policy
- stage and verification envelopes
- agent profiles
- layered prompt composition
- artifact-first execution

Everything else is optional until these foundations are in place.
