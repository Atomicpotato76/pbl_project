# Harness Mini Pipeline Design

## 목적
- `Self_Working_pipeline`의 기존 코드 자산을 재활용해, 현재 프로젝트 방향성에 맞는 작은 실행 파이프라인을 별도로 설계한다.
- 이 미니 파이프라인은 다음 5가지를 끝까지 연결하는 것을 목표로 한다.
  - 외부 API 호출
  - 하네스 규칙 적용
  - 에이전트 결과물 저장
  - 결과물 검증 전송
  - 완료 / 제한 도달 / 중단 시 사용자 보고
- GUI는 제외하고 `CLI + services + contracts + outputs`만 다룬다.

## 기준 문서
- 프로젝트 하네스:
  - `최신 상황/02_MC1-1_작물선정진행/02-01_기준하네스_작물선정라이트_v2.9.md`
  - `최신 상황/03_검증프롬프트와설정/03-01_검증배경_컨텍스트_v2.9.md`
- 엔지니어링 가이드:
  - `엔지니어링/INDEX.md`
  - `엔지니어링/prompt-engineering-guide.md`
  - `엔지니어링/meta-prompt-checklist-for-llm.md`
- 재활용 대상:
  - `Self_Working_pipeline/contracts/models.py`
  - `Self_Working_pipeline/services/adapters/*`
  - `Self_Working_pipeline/services/orchestrator/service.py`
  - `Self_Working_pipeline/services/memory/service.py`
  - `Self_Working_pipeline/services/reviewer/service.py`
  - `Self_Working_pipeline/services/testing/service.py`

## 한 줄 결론
이 미니 파이프라인 방향은 현재 프로젝트와 잘 맞는다. 다만 전제는 분명하다.
- 범용 멀티에이전트 엔진이 아니라 `하네스 집행기`로 설계할 것
- 자동화는 강하게 하되 최종 결정은 `human-lock`으로 남길 것
- retry는 탐색 확대가 아니라 `결함 수리`에만 쓸 것
- `MC1-1c`에서는 새 데이터 수집을 금지할 것

## 왜 별도 미니 파이프라인이 더 맞는가
기존 `Self_Working_pipeline`은 planner, executor, reviewer, tester, orchestrator가 잘 분리돼 있어서 뼈대는 좋다. 하지만 지금 구조는 범용 코드/리서치 파이프라인이라 현재 프로젝트의 lock semantics를 충분히 강제하지 못한다.

따라서 이번에는 기존 구조를 직접 뒤집기보다, 아래 원칙으로 "작은 전용 실행기"를 만드는 편이 더 적합하다.
- planner 자유도를 줄인다.
- 단계 수를 `MC1-1a / MC1-1b / MC1-1c / verification` 정도로 고정한다.
- 각 단계별 허용 도구와 금지 동작을 명시한다.
- 중간 결과는 항상 wrapper + artifact로 저장한다.
- 오케스트레이터는 "진행/정지/보고"만 정확히 수행한다.

## 미니 파이프라인 목표 흐름
```text
request intake
  -> scope lock
  -> MC1-1a research execution
  -> save artifacts
  -> verification
  -> branch by verdict
      -> proceed to MC1-1b
      -> retry same stage for repair
      -> halt and report
  -> top3 lock
  -> MC1-1b rescoring
  -> save artifacts
  -> verification
  -> branch by verdict
  -> final crop lock
  -> MC1-1c final synthesis
  -> save artifacts
  -> verification
  -> complete or halt
  -> user report
```

## 미니 파이프라인이 반드시 가져야 할 속성
1. API 호출은 모델 임의 텍스트가 아니라 앱 함수 또는 MCP tool schema를 통해서만 수행한다.
2. 각 단계 출력은 반드시 하네스 wrapper JSON과 markdown payload를 함께 남긴다.
3. 검증 결과는 단순 pass/fail이 아니라 `final_verdict`, `final_action`, `human_lock`, `carry_forward`를 포함해야 한다.
4. 사용자 보고는 "왜 멈췄는지 / 무엇이 완료됐는지 / 다음에 무엇을 확인하면 되는지"를 짧게 정리해야 한다.

## 추천 구조
새 디렉터리를 별도로 두는 것을 권장한다.

```text
Self_Working_pipeline/
  apps/
    mini_pipeline_cli/
  mini_pipeline/
    contracts.py
    settings.py
    harness.py
    api_registry.py
    executor.py
    verifier.py
    storage.py
    reporter.py
    orchestrator.py
```

기존 코드를 재활용하되 import만 받아오는 방식으로 시작한다.

## 모듈별 역할
### 1. `mini_pipeline/contracts.py`
미니 파이프라인 전용 계약 모델.

핵심 모델:
- `MiniRunStage`
- `MiniRunStatus`
- `HarnessStageResult`
- `VerificationResult`
- `MiniRunRecord`
- `UserReport`

최소 필드 예시:
- `stage`
- `stage_type`
- `retry_remaining`
- `final_verdict`
- `final_action`
- `human_lock_required`
- `halt_reason`
- `report_paths`

### 2. `mini_pipeline/settings.py`
하네스 실행기용 설정.

필수 설정:
- `planner_model`
- `executor_model`
- `verifier_model`
- `workspace_root`
- `outputs_root`
- `default_guidance_paths`
- `max_retry_per_stage`
- `api_registry_config`
- `verification_mode`

이 파일에서 `엔지니어링` 문서 참조를 기본값으로 강제한다.

### 3. `mini_pipeline/harness.py`
현재 하네스를 코드 레벨 규칙으로 변환한다.

이 모듈이 담당할 것:
- stage enum: `scope_lock`, `mc1_1a`, `top3_lock`, `mc1_1b`, `final_crop_lock`, `mc1_1c`, `verification`, `completed`, `halted`
- stage별 허용 도구
- stage별 금지 행동
- retry 가능 여부
- human-lock required 조건
- `MC1-1c` 신규 데이터 수집 금지

즉 하네스를 프롬프트에만 넣지 말고, 코드 조건문으로도 다시 묶는다.

### 4. `mini_pipeline/api_registry.py`
외부 API 호출을 등록형으로 관리한다.

예시 인터페이스:
- `call_tool(name: str, args: dict) -> dict`
- `allowed_tools_for_stage(stage) -> list[str]`

권장 규칙:
- stage별로 tool allowlist를 둔다.
- API 응답은 원문 + 정규화본을 같이 저장한다.
- 모델은 임의 URL 호출을 하지 않고 등록된 도구만 사용한다.

이 레이어를 두면 나중에 함수 기반, MCP 기반, 대시보드 내부 API 기반 중 어느 방식으로도 바꿀 수 있다.

### 5. `mini_pipeline/executor.py`
실제 조사/재채점/최종요약 수행기.

재활용 대상:
- `services/adapters/openai_adapter.py`
- `services/adapters/anthropic_adapter.py`
- `core/prompting.py`

실행 원칙:
- `MC1-1a`: 조사와 근거 수집
- `MC1-1b`: 기존 근거 기반 재채점과 Top 3 안정성 판단
- `MC1-1c`: 기존 결과만 이용한 최종 추천과 발표용 brief

### 6. `mini_pipeline/verifier.py`
검증 전용 모듈.

역할:
- wrapper 구조 검증
- claim-source linkage 검증
- 허용/금지 규칙 위반 검출
- `final_verdict` 계산
- `final_action` 계산

중요한 점:
- verifier는 executor와 역할을 분리한다.
- 가능하면 생성 모델과 다른 모델 또는 다른 provider를 쓴다.
- 단, 외부 검증 모델이 없더라도 최소 구조 검증은 로컬에서 수행한다.

### 7. `mini_pipeline/storage.py`
결과물 저장소.

권장 출력 구조:
```text
outputs/mini_pipeline/<run_id>/
  state/
    run.json
  stage_results/
    mc1_1a.wrapper.json
    mc1_1a.payload.md
    mc1_1b.wrapper.json
    mc1_1b.payload.md
    mc1_1c.wrapper.json
    mc1_1c.payload.md
  verification/
    mc1_1a.verification.json
    mc1_1b.verification.json
    mc1_1c.verification.json
  raw_api/
    <tool_name>__<timestamp>.json
  reports/
    latest_user_report.md
```

### 8. `mini_pipeline/reporter.py`
사용자 보고 전용 요약기.

보고 시점:
- stage 완료
- retry 진입
- halt
- completed

사용자에게 보여줄 핵심:
- 지금 단계
- verdict
- 왜 멈췄는지
- 무엇이 저장됐는지
- 다음 확인 포인트

### 9. `mini_pipeline/orchestrator.py`
전체 흐름 제어.

담당:
- 다음 stage 결정
- retry 예산 관리
- halt 조건 판단
- report 호출

이 모듈은 "생성"보다 "분기"가 더 중요하다.

## 단계별 허용 동작
### Scope Lock
- 허용: 초기 설정 입력, stage policy 확정
- 금지: 광범위 조사 시작
- 출력: `scope_lock_decision.json`

### MC1-1a
- 허용: API 호출, 근거 수집, wrapper 작성
- 금지: 최종 작물 확정
- 검증 포인트: Tier A / Tier B / watchlist 규칙, evidence gap

### Top 3 Lock
- 허용: 상위 후보군 확인 요청
- 금지: 새 데이터 수집

### MC1-1b
- 허용: 기존 자료 기반 재채점, 민감도 검토
- 금지: 조사 범위 확장

### Final Crop Lock
- 허용: 최종 판단 확인 요청
- 금지: 새 조사

### MC1-1c
- 허용: brief 작성, 최종 합성
- 금지: 새 데이터 수집
- 검증 포인트: new_data_forbidden 위반 여부

## 권장 판정 로직
### Proceed
- `final_verdict == PASS`
- `human_lock_required == false`

### Retry
- `final_verdict == FAIL`
- 같은 stage에서 repair 가능
- retry budget 남아 있음

### Halt
- retry 예산 소진
- `human_judgment_required`
- Top 3 또는 최종 추천에 직접 영향 주는 unresolved contradiction
- stage policy 위반
- `MC1-1c` 신규 데이터 수집 위반

## 추천 보고 포맷
```markdown
# Mini Pipeline Report

- Run ID: <run_id>
- Current stage: <stage>
- Status: completed | waiting_human_lock | retrying | halted
- Final verdict: PASS | FAIL | CONDITIONAL
- Final action: PROCEED | RETRY | HALT_HUMAN_CHECKPOINT

## What happened
<2-4 sentence summary>

## Saved artifacts
- <path>
- <path>

## Why this matters
<top risk or completion meaning>

## Next check
- <one or two concrete checks for the user>
```

## 기존 코드 재활용 계획
### 그대로 재사용 가능한 것
- OpenAI/Anthropic adapter 기본 구조
- outputs/plans 저장 패턴
- orchestration skeleton
- review/test persistence 흐름

### 얇게 복사 또는 래핑할 것
- `compose_system_prompt`
- `MemoryService` 일부 저장 유틸
- CLI 패턴

### 새로 만드는 편이 나은 것
- 하네스 stage policy
- verification verdict merger
- stage별 tool allowlist
- user-facing halt report

## 최소 구현 순서
### Phase 1. 실행 가능한 최소본
- `mini_pipeline/contracts.py`
- `mini_pipeline/harness.py`
- `mini_pipeline/storage.py`
- `mini_pipeline/reporter.py`
- `mini_pipeline/orchestrator.py`
- 단일 stage `MC1-1a`만 먼저 실행

### Phase 2. API 호출 연결
- `api_registry.py` 추가
- 형주가 만든 외부 API wrapper 연결
- raw response 저장

### Phase 3. verifier 연결
- 구조 검증
- 하네스 위반 검출
- retry/halt 분기

### Phase 4. 전체 stage 확장
- `top3_lock`
- `MC1-1b`
- `final_crop_lock`
- `MC1-1c`

## 이 방향이 현재 프로젝트와 맞는가
맞는다. 오히려 현재 프로젝트에는 이 방식이 더 적합하다.

이유는 세 가지다.
- 첫째, 현재 하네스는 자유 탐색형 에이전트보다 `범위 제한 + 잠금 + 검증` 구조에 가깝다.
- 둘째, 형주가 이미 외부 API 호출용 도구를 갖고 있으므로 "도구 연결형 오케스트레이터"가 실용적이다.
- 셋째, 기존 Hermes 전체를 프로젝트 전용으로 무겁게 바꾸는 것보다, 작은 전용 실행기를 만드는 편이 위험이 낮고 반복 속도가 빠르다.

단, 아래 조건을 지키지 않으면 방향성이 틀어진다.
- planner가 stage를 마음대로 늘리지 않을 것
- retry를 탐색 확대 수단으로 쓰지 않을 것
- lock 단계 없이 자동 확정하지 않을 것
- verifier를 단순 형식 검사기로 축소하지 않을 것

## 추천 파일 착수 순서
1. `Self_Working_pipeline/mini_pipeline/contracts.py`
2. `Self_Working_pipeline/mini_pipeline/harness.py`
3. `Self_Working_pipeline/mini_pipeline/storage.py`
4. `Self_Working_pipeline/mini_pipeline/reporter.py`
5. `Self_Working_pipeline/mini_pipeline/orchestrator.py`
6. `Self_Working_pipeline/mini_pipeline/api_registry.py`
7. `Self_Working_pipeline/apps/mini_pipeline_cli/main.py`

## 다음 세션용 작업 지시문 초안
다음 세션에서는 기존 `Self_Working_pipeline`의 범용 planner 흐름을 건드리기보다, `mini_pipeline/` 디렉터리를 새로 만들고 현재 문서 기준으로 최소 동작 버전을 구현한다. 목표는 `MC1-1a` 한 단계에 대해 외부 API 호출 -> wrapper 저장 -> verification -> report까지 끝나는 것이다. GUI는 무시하고 CLI만 만든다. 프롬프트 작성 시 `엔지니어링` 폴더 문서를 기본 guidance로 사용한다.
