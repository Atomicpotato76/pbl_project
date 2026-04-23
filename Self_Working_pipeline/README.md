# Hermes MC1-1 Harness Pipeline

CLI-first multi-agent pipeline for two modes:

- `code`: the original plan -> execution -> review -> test -> package loop
- `research`: an MC1-1 crop-selection harness flow with explicit human gates

In research mode, the pipeline stages a fixed MC1-1 sequence:

1. `mc1_1a_scope_and_evidence`
2. `mc1_1b_rescoring_and_top3`
3. `external_verification`
4. `mc1_1c_final_recommendation`

Research-mode role split is fixed as well:

- `planner`: defaults to GPT for plan creation
- `reviewer`: defaults to GPT for `mc1_1a`, `mc1_1b`, and `mc1_1c`
- `cross_verifier`: dedicated Claude review for `external_verification`
- `tester`: structural validation of evidence artifacts before merge approval

## Gate Model

The core approval API still uses the generic state-machine names:

- `plan`
- `checkpoint`
- `merge`

In `PIPELINE_MODE=research`, `checkpoint` maps to the current research gate:

- after `mc1_1a`: `scope_lock`
- after `mc1_1b`: `top3_lock`
- after `external_verification`: `final_crop_lock`

`status`, `summary`, `directions`, and the GUI overview surface the active research gate so the operator can see which decision is pending.

## Quick Start

From the repo root:

```powershell
$env:PIPELINE_MODE="research"
python -m apps.cli.main plan --request-file .\proposal.md
python -m apps.cli.main approve <run-id> --stage plan
python -m apps.cli.main run <run-id>
python -m apps.cli.main status <run-id>
python -m apps.cli.main summary <run-id>
```

If the package entrypoint is installed, the equivalent `hermes-pipeline ...` commands work too.

## Commands

```bash
hermes-pipeline plan "build a todo CLI"
hermes-pipeline plan --request-file .\proposal.md
hermes-pipeline approve <run-id> --stage plan
hermes-pipeline approve <run-id> --stage checkpoint --comment-file .\next-direction.md
hermes-pipeline run <run-id>
hermes-pipeline status <run-id>
hermes-pipeline summary <run-id>
hermes-pipeline directions <run-id>
hermes-pipeline watch <run-id>
hermes-pipeline notify <run-id>
hermes-pipeline feedback <run-id> --comment-file .\next-direction.md
hermes-pipeline approve <run-id> --stage merge
hermes-pipeline run <run-id>
hermes-pipeline artifacts <run-id>
hermes-pipeline doctor
```

## Research Outputs

Research mode expects each completed workstream to emit both:

- markdown reports under `outputs/<run-id>/workspace/reports/`
- structured evidence JSON under `outputs/<run-id>/workspace/research_evidence/`

The testing stage validates the research evidence package for claim-to-source linkage and source identifiers before merge approval.

## Proposal And Direction Files

- `plan "..."` is fine for short requests
- `plan --request-file .\proposal.md` is the preferred path for long research briefs
- if the request is long, the planner first builds a digest before planning
- `feedback <run-id> "..."` or `feedback <run-id> --comment-file .\next-direction.md` appends a new operator direction
- `approve <run-id> --stage checkpoint --comment-file .\approval-notes.md` records the gate approval note that justified the next transition

## Artifact Layout

- `plans/<run-id>/plan_bundle.json`: current plan bundle
- `plans/<run-id>/summary.md`: planner-facing summary
- `plans/<run-id>/versions/`: saved plan revisions
- `plans/<run-id>/directions/`: direction snapshots and latest recommendation pointers
- `outputs/<run-id>/workspace/`: generated worktree
- `outputs/<run-id>/workspace/reports/`: research markdown outputs
- `outputs/<run-id>/workspace/research_evidence/`: structured evidence JSON
- `outputs/<run-id>/executions/`: executor traces and stage outputs
- `outputs/<run-id>/reviews/`: review reports
- `outputs/<run-id>/tests/`: validation reports and logs
- `outputs/<run-id>/package/`: final packaged bundle and manifest

## Surfaces

- `apps/cli`: Typer CLI for planning, gate approval, status, and packaging
- `apps/gui`: local desktop GUI with overview, direction, artifacts, and gate controls
- `contracts/`: shared Pydantic contracts
- `services/`: adapters, orchestration, persistence, testing, and supervisor logic
- `tests/`: unit and integration coverage

## Secret Handling

- keep real API keys in OS-level environment variables, not in workspace files
- `.env.example` is a template only
- PowerShell example:

```powershell
setx ANTHROPIC_API_KEY "your-new-key"
setx OPENAI_API_KEY "your-new-key"
```

- open a new terminal after `setx`, then run `hermes-pipeline doctor`
- optional Discord notifications use `DISCORD_WEBHOOK_URL` and `DISCORD_WEBHOOK_USERNAME`
- optional research-model split uses `REVIEWER_MODEL` and `CROSS_VERIFIER_MODEL`

## Discord Notifications

If Discord webhook settings are present, Hermes sends plain-language updates when:

- the plan is ready
- a checkpoint or research gate is waiting
- validation is waiting for merge approval
- the run fails
- packaging is complete
