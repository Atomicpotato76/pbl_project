# MC1-1 세분화 로드맵 — 작물 선정 실증 분석 (v2.9-lite)

> **상위 로드맵**: `pbl_roadmap_v1.md` v1.1의 MC1-1을 세분화
> **목적**: 기존 스크리닝 결과(D1~D5 점수)의 근거를 실증 데이터로 보강하되, 자동 retry max 2회 환경에 맞춰 조사 범위와 Gate fail 조건을 경량화하여 최종 작물 1개를 확정한다.
> **입력**: 기존 자료 4개 (체크리스트 Rev 3.2, 스크리닝 결과, 교차검증 수정, 기존 프롬프트) + 형주 Scope Lock 입력(선택)
> **출력**: 실증 근거가 뒷받침된 최종 작물 추천 + 발표 블록 1 brief + 형주 최종 lock용 체크포인트
> **v2.9-lite 변경**: v2.9의 FSM, JSON wrapper, `final_verdict`, rollback, cross_verification, State Invariants는 유지한다. 단, MC1-1a의 조사 범위를 `Tier A 심화 + Tier B 역전 스캔 + New Watchlist trigger`로 축소하고, retry를 탐색이 아니라 수리 용도로 제한한다. 형주 개입은 Scope Lock, Top 3 Lock, Final Crop Lock에 집중한다.

---

## 📌 [P0] 자동화 프로토콜

이 하네스는 **Claude↔GPT 교차검증 자동 루프**를 전제하되, v2.9-lite에서는 완전 자율주행이 아니라 **human-lock 운영**을 기본으로 한다. 사람(형주)은 모든 셀을 검토하지 않고, 자동화가 되돌리기 어려운 세 지점 — Scope Lock, Top 3 Lock, Final Crop Lock — 에서만 결정을 내린다.

### 0. v2.9-lite 운영 원칙

| 원칙 | 적용 규칙 |
|---|---|
| **Formal FSM 유지** | formal stage는 `MC1-1a`, `MC1-1b`, `MC1-1c` 3개만 유지한다. `MC1-1a-1` 같은 stage를 새로 만들지 않는다. |
| **조사 패킷 경량화** | MC1-1a 내부 작업만 `Scope Lock`, `Tier A 심화`, `Tier B 역전 스캔`, `New Watchlist trigger`, `Evidence gap 영향도`로 쪼갠다. |
| **자동 retry = 수리** | retry는 wrapper/schema 오류, P0 근거 누락, 명백한 contradiction 수리에만 사용한다. 새 탐색을 넓히기 위한 retry 금지. |
| **P0 엄격 / P1 carry-forward** | Tier A와 승격 후보의 P0는 100% 원문 확인을 목표로 한다. P1 부족은 Top 3 영향이 없으면 FAIL이 아니라 `CONDITIONAL + carry_forward`로 처리한다. |
| **D2/D4 deep-dive 금지** | MC1-1a에서는 D2/D4를 NCBI/Ensembl/문헌 확인 수준으로만 처리한다. genome spec deep-dive는 MC2-1로 넘긴다. |
| **형주 검증 비중** | 전체 운영 기준 자동화 약 70%, 형주 검증 약 30%. 형주는 모든 출처가 아니라 순위가 바뀌는 지점만 본다. |

---

### A. JSON Wrapper Schema

모든 sub-MC(MC1-1a, MC1-1b, MC1-1c)의 출력은 아래 wrapper로 감싼다. 이 wrapper가 있어야 다음 단계의 에이전트가 "어디서 온 결과인지, 현재 상태가 뭔지" 기계적으로 파악할 수 있다.

```json
{
  "harness_version": "2.9-lite",
  "stage": "MC1-1a | MC1-1b | MC1-1c",
  "stage_type": "SURVEY | EVALUATE | SYNTHESIS",
  "cycle": 1,
  "loop_count": 1,
  "timestamp": "ISO 8601",
  "state": {
    "TARGET_CROP": "TBD | SHORTLISTED | CONFIRMED",
    "DATA_SUFFICIENCY": "INCOMPLETE | GATE_READY | PASSED",
    "SCORING": "LEGACY | RESCORED | FINAL",
    "BLOCK1_BRIEF": "NOT_STARTED | DRAFT | FINAL"
  },
  "gate": {
    "conditions": [
      {"id": "#1", "description": "...", "met": true},
      {"id": "#2", "description": "...", "met": false, "reason": "..."}
    ],
    "verdict": "PASS | FAIL | CONDITIONAL",
    "conditional_detail": {
      "unmet_conditions": ["미충족 조건 목록 (CONDITIONAL일 때만)"],
      "next_action": "PROCEED_WITH_CARRY_FORWARD | HALT_HUMAN_CHECKPOINT | AUTO_REPAIR_AND_REJUDGE",
      "carry_forward": ["다음 stage로 넘기는 미결 항목"],
      "human_checkpoint_required": false
    },
    "retry_remaining": 2
  },
  "cross_verification": {
    "verifier": "GPT-5.4",
    "verdict": "PASS | FAIL | CONDITIONAL",
    "issues": [
      {
        "description": "이슈 설명",
        "issue_type": "schema_invalid | evidence_gap | contradiction | verifier_timeout | human_judgment_required",
        "severity": "P0 | P1 | P2"
      }
    ],
    "timestamp": "ISO 8601"
  },
  "final_verdict": "PASS | FAIL | CONDITIONAL (gate.verdict × cross_verification.verdict 병합 결과)",
  "final_action": "PROCEED | RETRY | HALT_HUMAN_CHECKPOINT (final_verdict에 따라 결정되는 최종 행동)",
  "human_lock": {
    "required": false,
    "lock_type": "NONE | SCOPE_LOCK | DATA_SCOPE_CHECK | TOP3_LOCK | FINAL_CROP_LOCK",
    "decision_required": "형주가 확인해야 하는 결정 지점",
    "resume_condition": "승인 후 어느 stage로 진행할지"
  },
  "carry_forward": ["final_verdict가 CONDITIONAL일 때 다음 stage로 넘기는 미결 항목 — gate.conditional_detail.carry_forward + cross_verification.issues 합산"],
  "rollback_state": {
    "TARGET_CROP": "FAIL 시 되돌아갈 상태값",
    "DATA_SUFFICIENCY": "FAIL 시 되돌아갈 상태값",
    "SCORING": "FAIL 시 되돌아갈 상태값",
    "BLOCK1_BRIEF": "FAIL 시 되돌아갈 상태값"
  },
  "unresolved": ["[미결] 항목 목록"],
  "checkpoint_summary": "사람이 읽을 수 있는 2-3문단 한국어 요약",
  "payload": "< 실제 stage 출력 (마크다운 본문) >"
}
```

> **wrapper 적용 규칙:**
> - `payload`에 실제 분석 결과(마크다운)를 담는다. wrapper의 나머지 필드는 메타데이터.
> - `state`는 **이 stage 완료 시점**의 상태를 반영한다 (다음 stage 시작 전 기준).
> - `cross_verification`은 **필수 필드**이다. 교차검증 미실시 시 wrapper가 불완전하므로 Gate 판정 불가. `issues` 배열의 각 항목은 `issue_type` enum을 포함해야 한다: `schema_invalid`(wrapper 구조 오류), `evidence_gap`(근거 불충분), `contradiction`(소스 간 모순), `verifier_timeout`(검증 시간 초과), `human_judgment_required`(사람 판단 필요).
> - `final_verdict`는 `gate.verdict`와 `cross_verification.verdict`를 **"F. verdict 병합 규칙"** 표에 따라 산출한 최종 판정이다.
> - **⚠️ 자동 루프의 유일한 진행 기준은 `final_verdict`이다.** `gate.verdict` 단독으로는 진행/재시도/중단을 결정하지 않는다:
>   - `final_verdict = PASS` → `final_action = PROCEED` → 다음 sub-MC로 자동 진행.
>   - `final_verdict = FAIL` → `final_action = RETRY` → **"E-2. FAIL 전이표"** 적용. `retry_remaining > 0`이면 자동 재시도, 0이면 중단 후 형주 알림.
>   - `final_verdict = CONDITIONAL` → `final_action`은 조건에 따라 결정:
>     - `PROCEED` (carry_forward 있음) → 다음 stage 조건부 진행. **"E-3. CONDITIONAL 전이표"** 참조.
>     - `HALT_HUMAN_CHECKPOINT` (human_checkpoint_required=true) → 형주 알림 후 대기.
>     - `AUTO_REPAIR_AND_REJUDGE` (경미한 미충족을 자동 보완 가능) → 보완 후 gate 재판정. retry_remaining 차감 없음. **이 경우 `final_action = PROCEED`로 기록** (자동 보완은 내부 처리이므로 RETRY/HALT가 아닌 PROCEED 경로로 취급. 단, 보완 후 재판정에서 다시 FAIL이 나오면 그 시점에서 RETRY로 전환).
> - `carry_forward` (top-level): `final_verdict = CONDITIONAL`일 때 다음 stage로 넘길 미결 항목의 합산 리스트. gate.conditional_detail.carry_forward + cross_verification의 CONDITIONAL issues를 합친다.
> - `human_lock`: v2.9-lite에서 추가된 운영 필드이다. Gate verdict 자체를 바꾸지 않고, 다음 stage 실행 전에 형주 승인이 필요한지 표시한다. `human_lock.required=true`이면 `final_action=PROCEED`여도 런타임은 다음 stage를 즉시 실행하지 않고 형주 승인 후 재개한다. 이는 FSM state 전이가 아니라 운영상 pause이다.
> - `rollback_state`: `final_verdict = FAIL`일 때 E-2 전이표에 따라 **4개 상태 변수 전체**의 롤백 목표값을 기록한다. PASS/CONDITIONAL 시에는 null.
> - `checkpoint_summary`는 형주가 읽는 용도이므로 **한국어, 전문용어 최소화, 핵심만**.

### B. 상태전이 표

각 변수가 어떤 조건에서 다음 상태로 전이하는지 명시한다:

| 변수 | 초기값 | MC1-1a 완료 후 | 전이 조건 | MC1-1b 완료 후 | 전이 조건 | MC1-1c 완료 후 | 전이 조건 |
|------|--------|---------------|----------|---------------|----------|---------------|----------|
| TARGET_CROP | `TBD` | `TBD` | (데이터 수집 단계, 선정 안 함) | `SHORTLISTED` | Top 3 Gate PASS | `CONFIRMED` | 최종 Gate PASS |
| DATA_SUFFICIENCY | `INCOMPLETE` | `PASSED` 또는 `INCOMPLETE` | MC1-1a `final_verdict=PASS` 시 PASSED. GATE_READY는 gate.verdict 수준의 중간 상태로, final_verdict 산출 전까지만 유효 | `PASSED` | 유지 (MC1-1a에서 이미 PASSED 설정됨) | `PASSED` | 유지 |
| SCORING | `LEGACY` | `LEGACY` | (재채점 전) | `RESCORED` | 가중합 재산정 완료 | `FINAL` | 최종 확정 |
| BLOCK1_BRIEF | `NOT_STARTED` | `NOT_STARTED` | (brief 작성 전) | `NOT_STARTED` | (brief 작성 전) | `FINAL` | brief 작성 완료 |

> **역방향 전이**: `final_verdict = FAIL` 시 **4개 상태 변수 전체**가 E-2 표의 rollback_state로 복원된다. wrapper의 `rollback_state` 필드에 4개 변수의 목표값을 모두 기록한다. 예: MC1-1b FAIL(미결 셀) → TARGET_CROP → `TBD`, DATA_SUFFICIENCY → `INCOMPLETE`, SCORING → `LEGACY`, BLOCK1_BRIEF → `NOT_STARTED` → MC1-1a 보충 후 MC1-1b 재시도.

### C. 체크포인트 문서 템플릿

각 sub-MC 완료 시 아래 형식의 체크포인트 요약을 `checkpoint_summary` 필드에 담는다. 형주가 이것만 읽으면 현재 상황을 파악할 수 있어야 한다:

```markdown
## 체크포인트: [stage명] 완료

**시각**: [timestamp]
**사이클**: [cycle]회차, 재시도 [loop_count]회

### 지금까지 한 일
(2-3문장으로 이 단계에서 수행한 작업 요약)

### 핵심 발견
- (가장 중요한 발견 3-5개, 수치 포함)

### 상태 변화
| 변수 | 이전 | 현재 |
|------|------|------|
| TARGET_CROP | TBD | TBD |
| ... | ... | ... |

### Gate 판정
- ✅ 조건 #1: (설명)
- ❌ 조건 #3: (설명) → (재시도 계획)

### 미결 사항
- (있으면 나열, 없으면 "없음")

### 다음 단계
- (다음 sub-MC 또는 재시도 계획)
```

### D. 자동 루프 규칙

| 규칙 | 내용 |
|------|------|
| **루프 범위** | MC1-1 전체: `MC1-1a → Gate → 교차검증 → 병합 → MC1-1b → Gate → 교차검증 → 병합 → MC1-1c → Gate → 교차검증 → 병합`. Formal stage는 3개만 유지한다. |
| **Preflight: Scope Lock** | MC1-1a 실행 전 형주가 Tier A/B/New Watchlist 범위를 잠근다. 형주 입력이 없으면 기본값을 사용하되, wrapper의 `human_lock.lock_type = SCOPE_LOCK`에 기본값 사용 사실을 남긴다. |
| **자동 진행 조건** | `final_verdict = PASS`이고 `human_lock.required=false`이면 다음 sub-MC로 자동 진행한다. `human_lock.required=true`이면 형주 승인 후 재개한다. |
| **자동 재시도** | hard cap은 기존처럼 2회지만, 운영상 기본은 0~1회이다. P0 evidence gap·schema 오류·contradiction만 자동 retry 대상이다. P1 부족·Tier B 부족은 Top 3 영향이 없으면 retry하지 않고 carry-forward한다. |
| **조건부 진행** | `final_verdict = CONDITIONAL`이면 E-3 전이표에 따라 `PROCEED_WITH_CARRY_FORWARD`, `AUTO_REPAIR_AND_REJUDGE`, `HALT_HUMAN_CHECKPOINT`로 분기한다. |
| **중단 조건** | (1) retry 소진, (2) `human_judgment_required`, (3) 동점/순위 역전이 최종 1위 판단에 영향, (4) Tier B/New Watchlist가 실제 Top 3를 위협, (5) MC1-1c 최종 추천에 strong 반론 존재. |
| **형주 개입 시점** | **필수**: Scope Lock, Top 3 Lock(MC1-1b 후), Final Crop Lock(MC1-1c 후). **조건부**: MC1-1a 후 Tier 승격·P0 gap·순위 영향 미결 발생 시 Data Scope Check. |
| **재시작** | 형주가 체크포인트를 읽고 “여기부터 다시”라고 지정하면, 해당 sub-MC wrapper의 `state`, `carry_forward`, `rollback_state`, `human_lock`을 참조해 재시작한다. |
| **교차검증** | 각 sub-MC 출력 후 GPT에게 payload + gate 결과를 전달하여 독립 검증한다. 교차검증 완료 후 `final_verdict` 산출까지가 하나의 원자적 단위이다. |

### D-1. v2.9-lite retry budget

| 문제 유형 | 자동 retry | 형주 개입 |
|---|---:|---|
| wrapper/schema 오류 | 최대 2회 | 반복 실패 시 |
| verifier_timeout | retry 차감 없이 교차검증만 재시도 | 불필요 |
| Tier A 또는 승격 후보의 P0 근거 누락 | 최대 1회 | 1회 후 미해결이면 `HALT_HUMAN_CHECKPOINT` |
| P1 근거 부족 | 기본 0회, 순위 영향 있으면 1회 | 순위 영향 있으면 |
| Tier B 자료 부족 | 0회 | 역전 trigger가 있을 때만 |
| 핵심 contradiction | 1회 | 계속 상충하면 |
| Top 3 동점/역전 | 자동 확정 금지 | 즉시 |
| 최종 추천 strong 반론 | 자동 확정 금지 | 즉시 |

### E. Gate별 FAIL/CONDITIONAL 전이표

각 Gate verdict에 대해 **next action이 완전히 매핑**되어야 자동 루프가 상태기계로 동작할 수 있다. enum 값 → next action 매핑을 아래 표로 정의한다.

#### E-1. PASS 전이 (공통)

> **적용 조건**: `final_verdict = PASS`일 때만 이 표가 적용된다. `gate.verdict` 단독으로 적용하지 않는다.

| Gate | final_verdict | next_stage | state 변화 | Invariant 사후 검증 | human_lock |
|------|--------------|------------|-----------|-------------------|------------|
| MC1-1a Gate | PASS | MC1-1b 진입 | DATA_SUFFICIENCY → PASSED | DATA_SUFFICIENCY = PASSED 확인 | 보통 `NONE`; Tier 승격·P0 gap 영향 있으면 `DATA_SCOPE_CHECK` |
| MC1-1b Gate | PASS | **TOP3_LOCK → MC1-1c 진입** | TARGET_CROP → SHORTLISTED, SCORING → RESCORED, DATA_SUFFICIENCY → PASSED (유지) | TARGET_CROP = SHORTLISTED ∧ SCORING = RESCORED ∧ DATA_SUFFICIENCY = PASSED 확인 | `TOP3_LOCK` 필수 |
| MC1-1c Gate | PASS | **FINAL_CROP_LOCK → 루프 종료** | TARGET_CROP → CONFIRMED, SCORING → FINAL, BLOCK1_BRIEF → FINAL | 4변수 모두 최종 상태 확인 | `FINAL_CROP_LOCK` 필수 |

> **주의**: `TOP3_LOCK`과 `FINAL_CROP_LOCK`은 FSM stage가 아니다. wrapper state는 정상 전이하되, 런타임이 다음 stage 또는 MC2-1 진입을 형주 승인 전까지 보류하는 운영 pause이다.

#### E-2. FAIL 전이 (원인 기반 분기, v2.9-lite)

**원칙**: FAIL 시 retry target은 “문제의 원인이 있는 stage”로 돌아간다. 단, v2.9-lite에서 retry는 탐색 확대가 아니라 결함 수리 목적으로만 사용한다.

| Gate | FAIL 원인 분류 | retry_target | 자동 retry 한도 | rollback_state (4개 변수 전체) | 예시 |
|------|---------------|-------------|----------------|-------------------------------|------|
| MC1-1a Gate | Scope Lock 위반: Tier A > 5개, Tier B full deep-dive 수행, New Watchlist full scoring | `HALT_HUMAN_CHECKPOINT` | 0회 | TARGET_CROP → `TBD`, DATA_SUFFICIENCY → `INCOMPLETE`, SCORING → `LEGACY`, BLOCK1_BRIEF → `NOT_STARTED` | 조사 범위가 다시 9개×5축으로 팽창 |
| MC1-1a Gate | Tier A 또는 승격 후보의 P0 근거 누락 | MC1-1a 보충 | 1회 | TARGET_CROP → `TBD`, DATA_SUFFICIENCY → `INCOMPLETE`, SCORING → `LEGACY`, BLOCK1_BRIEF → `NOT_STARTED` | Top 3 후보의 D1 핵심 수치 원문 미확인 |
| MC1-1a Gate | P1 근거 부족이나 Top 3 영향 있음 | MC1-1a 보충 또는 `DATA_SCOPE_CHECK` | 1회 | TARGET_CROP → `TBD`, DATA_SUFFICIENCY → `INCOMPLETE`, SCORING → `LEGACY`, BLOCK1_BRIEF → `NOT_STARTED` | P1 미검증 셀이 3위/4위 경계에 영향 |
| MC1-1a Gate | Tier B 역전 trigger 미판정 | MC1-1a 보충 | 1회, 단 trigger 후보만 | TARGET_CROP → `TBD`, DATA_SUFFICIENCY → `INCOMPLETE`, SCORING → `LEGACY`, BLOCK1_BRIEF → `NOT_STARTED` | 참깨가 D5에서 Top 3를 위협하는데 스캔 누락 |
| MC1-1a Gate | cross_verification FAIL (`contradiction` 또는 P0 `evidence_gap`) | MC1-1a 보충 | 1회 | TARGET_CROP → `TBD`, DATA_SUFFICIENCY → `INCOMPLETE`, SCORING → `LEGACY`, BLOCK1_BRIEF → `NOT_STARTED` | FAOSTAT 수치와 payload 수치 불일치 |
| MC1-1b Gate | 채점 산식/schema 오류 | MC1-1b 재시도 | 최대 2회 | TARGET_CROP → `TBD`, DATA_SUFFICIENCY → `PASSED`, SCORING → `LEGACY`, BLOCK1_BRIEF → `NOT_STARTED` | weight 합계 오류, Score 산식 오류 |
| MC1-1b Gate | 동점 또는 미결 셀이 순위 결정에 영향 | `HALT_HUMAN_CHECKPOINT` 또는 MC1-1a 보충 | 자동 확정 금지 | TARGET_CROP → `TBD`, DATA_SUFFICIENCY → `PASSED` 또는 원인 stage가 MC1-1a이면 `INCOMPLETE`, SCORING → `LEGACY`, BLOCK1_BRIEF → `NOT_STARTED` | 3위/4위가 미결 셀 하나로 뒤집힘 |
| MC1-1b Gate | Sensitivity 역전 “높음” 2개 이상 | `TOP3_LOCK` 또는 MC1-1b 재시도 | 0~1회 | TARGET_CROP → `TBD`, DATA_SUFFICIENCY → `PASSED`, SCORING → `LEGACY`, BLOCK1_BRIEF → `NOT_STARTED` | D2 우선 시 최종 1위 역전 |
| MC1-1c Gate | brief 미완·Self-Check 경미 실패 | MC1-1c 자동 보완 | retry 차감 없음 또는 1회 | TARGET_CROP → `SHORTLISTED`, DATA_SUFFICIENCY → `PASSED`, SCORING → `RESCORED`, BLOCK1_BRIEF → `NOT_STARTED` | 5분 brief 분량 부족 |
| MC1-1c Gate | 최종 추천 strong 반론 또는 `human_judgment_required` | `FINAL_CROP_LOCK` | 자동 확정 금지 | TARGET_CROP → `SHORTLISTED`, DATA_SUFFICIENCY → `PASSED`, SCORING → `RESCORED`, BLOCK1_BRIEF → `NOT_STARTED` | 1위 추천이 발표 전략상 부적절할 수 있음 |

> **retry_remaining 차감 규칙**: 실제 sub-MC 재실행은 차감한다. `verifier_timeout`으로 교차검증만 재시도하는 경우와 MC1-1c 경미 보완 `AUTO_REPAIR_AND_REJUDGE`는 차감하지 않는다.
> **보충 모드 원칙**: MC1-1a로 rollback하더라도 전체 재조사가 아니라 미결 셀·trigger 후보만 대상으로 한다.

#### E-3. CONDITIONAL 전이 (Gate별 분기, v2.9-lite)

**정의**: CONDITIONAL = 대부분 충족했고 다음 stage에서 안전하게 해소 가능하거나, 형주 판단으로 빠르게 잠글 수 있는 상태.

| Gate | CONDITIONAL 조건 | next_action | human_checkpoint_required | 조건부 진행 시 carry_forward / human_lock |
|------|-----------------|-------------|--------------------------|------------------------------------------|
| MC1-1a Gate | Tier A P0는 충족, P1 60~79%이며 순위 영향 없음 | `PROCEED_WITH_CARRY_FORWARD` | false | 미검증 P1 셀을 MC1-1b `unresolved`에 기록. MC1-1b에서 보수/낙관 시나리오로 영향 확인 |
| MC1-1a Gate | Tier A `[미확보]` 셀이 기준보다 많지만 비관 처리해도 Top 3 후보군이 유지 | `PROCEED_WITH_CARRY_FORWARD` | false | 해당 셀은 MC1-1b에서 보수적 0 또는 기존 점수 유지로 처리 |
| MC1-1a Gate | Tier B 후보가 trigger 2개 중 1개만 충족 | `PROCEED_WITH_CARRY_FORWARD` | false | “역전 가능성 낮음”으로 appendix 기록, full scoring 금지 |
| MC1-1a Gate | Tier B/New Watchlist가 Top 3를 실제 위협하거나 승격 여부 애매 | `HALT_HUMAN_CHECKPOINT` | true | `human_lock.lock_type = DATA_SCOPE_CHECK`; 형주가 승격/제외 결정 |
| MC1-1b Gate | 미결 셀 1개가 있으나 비관/낙관 모두 Top 3 유지 | `PROCEED_WITH_CARRY_FORWARD` | false | MC1-1c 리스크 섹션에 명시. 단 `TOP3_LOCK`은 여전히 필수 |
| MC1-1b Gate | Sensitivity 역전 “높음” 1개만 존재 | `PROCEED_WITH_CARRY_FORWARD` | false | brief 반론 섹션에 해당 역전 시나리오 명시. `TOP3_LOCK`에서 형주 승인 필요 |
| MC1-1b Gate | 동점, 1위 역전 가능성, 미결 셀이 순위 결정에 영향 | `HALT_HUMAN_CHECKPOINT` | true | 형주에게 Top 3 후보와 민감도 표를 제시하고 결정 요청 |
| MC1-1c Gate | Self-Check (a)~(e) 중 1개 경미 미충족 | `AUTO_REPAIR_AND_REJUDGE` | false | 해당 항목만 보완 후 재판정. retry_remaining 차감 없음 |
| MC1-1c Gate | 최종 추천 반론 strong 또는 발표 서사가 약함 | `HALT_HUMAN_CHECKPOINT` | true | `FINAL_CROP_LOCK`; 형주가 최종 작물 승인/교체/brief 수정 지시 |

> **CONDITIONAL state 처리**: MC1-1a `final_verdict=CONDITIONAL`이라도 `final_action=PROCEED`이면 `DATA_SUFFICIENCY = PASSED`로 설정한다. 단, top-level `carry_forward`에 미결을 남기고 MC1-1b Self-Check에서 순위 영향이 없음을 재확인해야 한다.

### F. 교차검증 필드 및 verdict 병합 규칙

교차검증은 **필수**이다. 각 sub-MC 출력 후 반드시 GPT에게 payload + gate 결과를 전달하여 독립 검증을 수행하고, 결과를 wrapper에 기록한다.

```json
"cross_verification": {
  "verifier": "GPT-5.4",
  "verdict": "PASS | FAIL | CONDITIONAL",
  "issues": [
    {"description": "이슈 설명", "issue_type": "evidence_gap", "severity": "P0"},
    {"description": "이슈 설명", "issue_type": "contradiction", "severity": "P1"}
  ],
  "timestamp": "ISO 8601"
}
```

> **issue_type enum 정의:**
> - `schema_invalid`: wrapper 구조 오류 (필수 필드 누락, state 전이 위반 등)
> - `evidence_gap`: payload에서 주장의 근거(출처, 데이터)가 불충분
> - `contradiction`: 소스 간 또는 payload 내부 데이터 모순
> - `verifier_timeout`: 교차검증 시간 초과 (재시도 필요)
> - `human_judgment_required`: 자동 판정 불가, 사람 판단 필요
>
> **issue_type → FAIL 시 retry 매핑:**
> - `schema_invalid` → 같은 sub-MC 재시도 (wrapper 재생성)
> - `evidence_gap` → FAIL 원인이 이전 stage 데이터 범위이면 이전 stage로 rollback; 현재 stage에서 보완 가능하면 같은 sub-MC 재시도
> - `contradiction` → 같은 sub-MC 재시도 (모순 해소)
> - `verifier_timeout` → 교차검증만 재시도 (retry_remaining 차감 없음)
> - `human_judgment_required` → HALT_HUMAN_CHECKPOINT

**verdict 병합 규칙** (gate.verdict × cross_verification.verdict → final_verdict):

| gate.verdict | cross_verification.verdict | final_verdict | final_action | action |
|-------------|--------------------------|---------------|-------------|--------|
| PASS | PASS | **PASS** | `PROCEED` | 다음 stage 진행. carry_forward = [] |
| PASS | CONDITIONAL | **CONDITIONAL** | `PROCEED` | cross_verification.issues를 top-level carry_forward에 추가. 다음 stage에서 확인 |
| PASS | FAIL | **FAIL** | `RETRY` | cross_verification.issues의 issue_type별로 retry 매핑 적용. rollback_state 기록 |
| CONDITIONAL | PASS | **CONDITIONAL** | `PROCEED` | gate의 conditional_detail.carry_forward를 top-level carry_forward에 복사. 다음 stage 조건부 진행 |
| CONDITIONAL | CONDITIONAL | **CONDITIONAL** | `HALT_HUMAN_CHECKPOINT` | 양쪽 issues 합산. human_checkpoint_required = true (이중 조건부는 사람 확인) |
| CONDITIONAL | FAIL | **FAIL** | `RETRY` | FAIL 우선. cross_verification.issues의 issue_type별로 retry 매핑 적용. rollback_state 기록 |
| FAIL | * | **FAIL** | `RETRY` | gate FAIL 우선. E-2 FAIL 전이표 적용. rollback_state 기록 |

> **원칙**: FAIL은 항상 우선한다. CONDITIONAL×CONDITIONAL은 불확실성이 누적되므로 형주 체크포인트로 격상한다.
>
> **final_action 정제 규칙** (CONDITIONAL 행에 적용):
> - F 표의 `final_action`은 **기본값**이다. `final_verdict = CONDITIONAL`인 경우, E-3 전이표의 `conditional_detail.next_action`이 `final_action`을 정제한다:
>   - `next_action = PROCEED_WITH_CARRY_FORWARD` → `final_action = PROCEED`
>   - `next_action = HALT_HUMAN_CHECKPOINT` → `final_action = HALT_HUMAN_CHECKPOINT`
>   - `next_action = AUTO_REPAIR_AND_REJUDGE` → `final_action = PROCEED` (자동 보완은 내부 처리. 보완 후 재판정에서 FAIL 시 RETRY로 전환)
> - **`issue_type = human_judgment_required` override**: `cross_verification.issues`에 `issue_type: "human_judgment_required"` 항목이 1개라도 존재하면, F 표의 기본 `final_action`과 무관하게 **`final_action = HALT_HUMAN_CHECKPOINT`로 override**된다. 이는 PASS×FAIL 행의 RETRY 기본값도 override한다.

---

## 📌 [P0] 3축 태그 시스템

모든 정량 셀에 아래 3축 태그를 병기한다. 하네스 전체에서 이 enum만 사용하며, 이 목록에 없는 태그를 생성하지 마라.

| 축 | 태그 | 의미 |
|---|---|---|
| **Type** (데이터 출처 유형) | `[실측]` | FAOSTAT/UN Comtrade 등 공식 통계 |
| | `[시장추정]` | 시장보고서(ISF, MarketsandMarkets 등) 기반 추정 |
| | `[전문가추론]` | LLM 도메인 추론 또는 전문가 의견 |
| | `[미확보]` | 데이터 없음 |
| | `[문헌확인]` | MC1-1a 범위 밖 항목을 기존 문헌·DB(NCBI, Ensembl 등)로 확인 |
| **Verification** (검증 상태) | `[원문확인]` | 원문/원본 데이터에서 직접 확인 |
| | `[미검증]` | 아직 원문 대조 안 됨 |
| | `[시차 주의]` | latest_available_year 기준 3년 초과 데이터 |
| | `[부분근거]` | 일부 국가/기간만 데이터 있음, 전체 커버 아님 |
| | `[미결]` | 교차확인 결과 불일치 또는 판단 보류 — 형주 결정 필요 |
| **Argument** (논증 건강성) | `[체인확인]` | 인과 체인(A→B)의 근거가 확인됨 |
| | `[체인 미검증]` | 인과 주장의 화살표 근거 미확보 |
| | `[반례 발견]` | 결론에 대한 반증 조건이 실현될 가능성 발견 |
| | `[상충]` | 소스 간 데이터/주장 불일치 — 양쪽 인용 후 보수적 판정 |

> **사용 예시:** `"비둘기콩 재배면적 CAGR 1.8% (FAOSTAT, {latest_available_year-4}~{latest_available_year}) [실측] [원문확인] [체인확인]"`
> **복합 사용:** `"India 종자시장 $120M [시장추정] [부분근거] [상충]"` — 시장보고서 기반이나 인도만 커버, 소스 간 수치 불일치

---

## 📌 [P0] 5축 → D1~D5 매핑 테이블

MC1-1a의 5축 조사 결과가 MC1-1b의 D점수 재채점에 어떻게 연결되는지 사전 정의한다.

| D항목 | 정의 | 1차 증거 축 | 2차 증거 축 | 커버 안 되는 영역 (MC1-1a 한계) |
|---|---|---|---|---|
| D1 (시장 매력도) | 종자 매출 잠재력 | 축1 (시장 데이터) | 축2 (소비구조) | — |
| D2 (유전체 신규성) | 기존 reference 대비 추가 가치 | — | — | **MC1-1a 범위 밖.** 기존 Rev 3.2 + NCBI/Ensembl Plants DB 교차확인으로 보완. MC1-1b에서 "기존 점수 유지 + DB/문헌 인용"으로 처리. 교차확인 불가 시 `[미결]` 태그 |
| D3 (사업 실행 가능성) | N사의 delivery 역량 | 축3 (지정학) | 축4 (사회문화) | 부분 커버. N사 내부 역량은 가정 기반 |
| D4 (기술 장벽) | 시퀀싱/조립 난이도 | — | — | **MC1-1a 범위 밖.** 기존 Rev 3.2 점수 유지 + NCBI Genome/Ensembl Plants에서 기존 assembly 현황 교차확인. 교차확인 불가 시 `[미결]` 태그. MC2-1에서 상세 검증 |
| D5 (전략적 타이밍) | 시장 진입 적기 | 축5 (정책동향) | 축1 (시장 트렌드) | — |

> **규칙**: MC1-1a가 커버하지 못하는 D2, D4는 MC1-1b에서 "데이터 미확보 — 기존 점수 유지, NCBI/Ensembl Plants 교차확인"으로 처리. 교차확인 결과 기존 점수와 불일치 시 `[미결]` 태그 후 형주 판단. 근거 없이 변경 금지.

---

## 📌 [P0] D점수 0/1/2 판정 루브릭

MC1-1b 재채점 시 모든 셀에 적용하는 판정 기준:

| 점수 | D1 (시장 매력도) | D2 (유전체 신규성) | D3 (사업 실행 가능성) | D4 (기술 장벽) | D5 (전략적 타이밍) |
|---|---|---|---|---|---|
| **2** | 글로벌 종자시장 ≥$500M **또는** CAGR ≥3% **또는** hybrid 비중 ≥30% (셋 중 하나 이상) | 고품질 reference 없음 또는 pan-genome 필요성 명확 | N사 기존 인프라로 delivery 가능 **그리고** IP 보호 확보 (둘 다 충족) | genome <2Gb **그리고** ploidy ≤2x **그리고** contig N50 선례 있음 (셋 다 충족) | VACS 포함 **그리고** CGIAR 우선 **그리고** 시장 window 3년 내 (셋 다 충족) |
| **1** | 종자시장 $100-500M **또는** CAGR 1-3% **또는** hybrid 가능 (셋 중 하나 이상) | reference 있으나 품종/계통 특이적 re-sequencing 가치 | 파트너십 필요하나 경로 존재 | genome 2-5Gb **또는** polyploid (기술적으로 가능하나 난이도 중간) | 일부 정책 지원 **또는** 시장 window 3-5년 |
| **0** | 종자시장 <$100M **그리고** hybrid 불가/미미 (둘 다 해당) | 최근 고품질 reference + pan-genome 완비 | 현지 파트너 미확보 **또는** 규제 장벽 높음 | genome >5Gb **또는** 고배체 **또는** 반복서열 과다 (하나라도 해당) | 정책 지원 없음 **그리고** 시장 포화/하락 |

> **적용 규칙**: 정량 기준에 해당하면 해당 점수. 기준 경계에 있으면 보수적(낮은 점수) 판정. 실증 데이터 없으면 기존 점수 유지 + `[미확보]` 태그.
> **AND/OR 명시**: 복수 조건이 있는 셀은 **그리고**(AND) / **또는**(OR) 연산자를 명시했다. 판정 시 해당 논리를 정확히 적용하라.

---

## 📌 [P0] Soft Score 가중합 산식

```
정규화 Score = (Σ(Di × Wi) / 2.000) × 100

여기서:
  Di = D점수 (0, 1, 2)
  Wi = AHP weight
    W1 = 0.363 (시장 매력도)
    W2 = 0.219 (유전체 신규성)  
    W3 = 0.219 (사업 실행 가능성)
    W4 = 0.092 (기술 장벽)
    W5 = 0.107 (전략적 타이밍)
  
  ΣWi = 1.000
  만점 = (2×1.000 / 2.000)×100 = 100.00
  최저 = (0×1.000 / 2.000)×100 = 0.00
```

> **검증**: 비둘기콩 기존 = (2×0.363 + 2×0.219 + 2×0.219 + 1×0.092 + 1×0.107) / 2.000 × 100 = (0.726+0.438+0.438+0.092+0.107)/2.000 × 100 = 1.801/2.000 × 100 = **90.05** (기존 90.08과 근사 — 반올림 차이)
> **주의**: 이전 버전의 `Soft Score = Σ(Di×Wi)×50+50` 중간 산식은 삭제됨. 정규화 Score만 사용한다.

---

## 📌 [P0] 시간 앵커

이 하네스의 모든 "최근 N년" 참조는 **데이터 수집 시점의 latest_available_year를 기준**으로 한다:

- "최근 5년" = `(latest_available_year − 4) ~ latest_available_year`
- "3년 초과" = `latest_available_year − 3` 이전
- 예시: FAOSTAT에서 2023년이 최신이면 최근 5년 = 2019-2023. 2024년 데이터가 나오면 2020-2024.
- 각 데이터 셀에 실제 사용한 연도 범위를 명기하라.
- **Few-shot 예시나 검증값에도 고정 연도를 쓰지 않는다.** `{latest_available_year}` 표기를 사용하라.

---

## 📌 [P0] 검증 중단 규칙

검증 루프의 수확 체감을 방지하기 위한 중단 기준:

| 조건 | 행동 |
|---|---|
| 동일 셀에 대해 3회 추가 검색 후에도 P0/P1 검증이 진전되지 않음 | 해당 셀을 `[미확보]`로 확정하고 다음 셀로 이동 |
| P0 셀 100% + P1 셀 80% 검증 달성 | Gate 충족 → Stage 진행 |
| 전체 검증 소요가 Stage 예상 시간의 2배 초과 | 현재 상태로 Self-Check 수행 후 Gate 판정 |

---

## 📌 [P0] 공통 앵커 블록

아래 블록은 **모든 sub-MC(MC1-1a, MC1-1b, MC1-1c)**의 stage_0_command에 포함되어야 한다. 각 sub-MC 섹션에서 이 블록을 참조한다.

```
[불변 앵커]
"교수님이 '레퍼런스는?' 하면 답할 수 있는가?" — 이 질문에 답할 수 없는 데이터는 의사결정 근거로 사용 금지.

[시간 앵커]
모든 "최근 N년" 참조는 데이터 수집 시점의 latest_available_year를 기준으로 한다. 고정 연도 범위(예: "2019-2023")를 사용하지 말고, 실제 수집한 데이터의 최신 연도를 명기하라.

[출처 규칙 — 금지사항]
- 정량 데이터마다 출처(URL, DOI, DB명+경로) + 데이터 연도를 명시하라.
- 출처 없는 정량 데이터는 [미검증]으로 태그하라.
- 인과 주장(A→B)의 화살표 근거를 명시하라. 근거 없으면 [체인 미검증].
- latest_available_year 기준 3년 초과 데이터는 [시차 주의] 태그.
- 결론마다 반증 조건 1개: "이 결론이 틀리려면 ___이어야 한다."
- D등급 출처(개인 블로그, AI 단독 생성, 비공식 소스)는 의사결정 근거 사용 금지.

[출력 계약]
모든 정량 셀에 3축 태그를 병기한다 — 이 문서 상단 "3축 태그 시스템" 섹션의 enum만 사용.

[검증 우선순위]
- P0(필수): 핵심 셀 → 원문 출처 필수
- P1(필수): 순위 역전 가능 셀 → 원문 출처 필수
- P2(선택): B등급 의존 셀 → 교차검증 1회
- P3(생략 가능): A등급 + 순위 무관 → 출처 표기만

[검증 중단 규칙]
이 문서 상단 "검증 중단 규칙" 섹션 참조.

[Correctness Gate 사전 고지]
이 Stage의 출력은 해당 Decision Gate의 조건을 충족해야 다음 Stage로 진행된다. Gate 조건은 각 sub-MC 하단에 명시되어 있다.

[Wrapper 출력 규칙]
출력 완료 후 반드시 JSON wrapper로 감싸서 출력하라. wrapper schema는 이 문서 상단 "자동화 프로토콜 > A. JSON Wrapper Schema" 참조. state 필드는 이 stage 완료 시점의 상태를 반영하고, checkpoint_summary는 한국어로 작성하라.
```

---

## 왜 세분화하고, 왜 경량화하는가?

기존 MC1-1은 “19개 재검증 + Top 3 선정”을 한 사이클에 담았다. v2.9는 이를 3개 sub-MC로 나누면서 근거 품질과 rollback 안전성은 좋아졌지만, MC1-1a가 `Shortlist 9개 × 5축` deep 조사로 커져 자동 retry max 2회 운영에는 과부하가 생겼다.

따라서 v2.9-lite는 **상태기계는 유지하고 조사면만 줄인다.** 3개 formal stage는 그대로 두되, MC1-1a 내부를 작은 work packet으로 운영한다.

| 작업 패킷 | 목적 | formal stage 추가 여부 |
|---|---|---|
| Scope Lock | Tier A/B/New Watchlist 범위 잠금 | 추가 안 함 |
| Tier A 심화 | 실제 Top 3 후보군의 D1/D3/D5 근거 확보 | 추가 안 함 |
| Tier B 역전 스캔 | Top 3를 뒤집을 후보만 승격 | 추가 안 함 |
| New Watchlist trigger | 새 후보를 appendix 또는 승격 후보로 분류 | 추가 안 함 |
| Evidence gap 영향도 | 미결 셀이 순위를 흔드는지 판정 | 추가 안 함 |

---

## MC1-1a: Scope-Locked 실증 조사 🔍

- **유형:** SURVEY (실증 데이터 수집)
- **조사 범위:** Scope Lock된 Tier A 최대 5개 심화 + Tier B 역전 가능성 스캔 + New Watchlist 2~3개 trigger triage
- **깊이:** Tier A는 deep, Tier B는 scan, New Watchlist는 3줄 trigger 평가
- **선행:** 없음. 단, 실행 직전 Scope Lock 필요
- **산출물:**
  - Scope Lock 표: Tier A / Tier B / New Watchlist
  - Tier A D1/D3/D5 evidence matrix
  - Tier B 역전 스캔 표
  - New Watchlist trigger 표
  - D2/D4 DB 확인 요약
  - Evidence gap 영향도 판정
- **PBL 학습목표 연결:** 학습목표 1 (식물종 유전체 구조 — 작물 선정의 맥락 이해)
- **완료 시 상태전이:** `DATA_SUFFICIENCY: INCOMPLETE → PASSED` (`final_verdict=PASS` 또는 `CONDITIONAL + PROCEED`일 때. carry_forward는 별도 기록)

<stage_0_command>
[Role] 너는 종자산업 시장분석 리서처이다. FAOSTAT·UN Comtrade·ISF 등 공식 통계와 공개 DB를 기반으로 작물별 시장·지정학·소비 데이터를 수집하고, 근거 기반 보고서를 작성하는 것이 역할이다. 추정은 반드시 근거와 분리하라.

[공통 앵커 블록 적용] — 이 문서 상단 “공통 앵커 블록” 전체를 이 위치에서 적용한다.

[Scope Lock — 실행 전 필수]
이 stage는 formal FSM stage를 늘리지 않고, MC1-1a 내부 work packet으로만 범위를 제한한다.

1. 형주가 Tier 표를 제공한 경우 그 범위를 사용한다.
2. 형주 입력이 없으면 아래 기본값을 사용한다. 단, checkpoint_summary에 “기본 Scope Lock 사용”이라고 명시한다.

| 구분 | 기본 범위 | 처리 |
|---|---|---|
| **Tier A** | 비둘기콩, 고추, 배추, 시금치, 들깨 | D1/D3/D5 심화 조사. D2/D4는 DB 확인만 |
| **Tier B** | 참깨, 녹두, 알팔파, 라이그라스 + 기존 자료의 나머지 후보 | full scoring 금지. Top 3 역전 가능성만 스캔 |
| **New Watchlist** | 2024~2026에 새로 주목받은 후보 2~3개 | 3줄 trigger 평가. 승격 조건 충족 시에만 Tier A 승격 요청 |

[범위 금지]
- Tier B에 대해 5축 deep-dive를 수행하지 마라.
- New Watchlist를 즉시 full scoring하지 마라.
- D2/D4 genome deep-dive를 MC1-1a에서 수행하지 마라. MC2-1로 넘겨라.
- Scope Lock을 벗어난 추가 후보 탐색은 appendix 후보명 수준으로만 남겨라.

[배경]
N사(국내 본사 대기업급 종자회사)의 표준유전체 해독 프로젝트 대상 작물 선정 중이다. 본사 소재지는 국내이나, 작물·시장·파트너십의 지리적 범위는 글로벌로 본다. 기존 스크리닝에서 19개 후보와 Shortlist가 있고, AHP 기반 D1~D5 점수가 있다. MC1-1a의 목적은 모든 후보를 다시 백서화하는 것이 아니라, MC1-1b 재채점에 필요한 실증 근거를 확보하는 것이다.

[기존 Shortlist — 참조]

| 작물 | D1 | D2 | D3 | D4 | D5 | Score |
|---|---|---|---|---|---|---|
| 비둘기콩 (India Hybrid F1) | 2 | 2 | 2 | 1 | 1 | 90.05 |
| 고추 (Global Hybrid F1) | 2 | 1 | 2 | 2 | 2 | 89.05 |
| 배추 (Kimchi + Asia) | 2 | 1 | 2 | 2 | 2 | 89.05 |
| 시금치 (Global Baby Leaf) | 2 | 2 | 1 | 1 | 1 | 79.12 |
| 들깨 (Korea Omega-3) | 1 | 2 | 2 | 1 | 2 | 77.26 |
| 참깨 (Africa VACS) | 1 | 2 | 1 | 1 | 1 | 60.97 |
| 녹두 | 1 | 2 | 2 | 1 | 1 | — |
| 알팔파 | 2 | 1 | 1 | 0 | 1 | — |
| 라이그라스(2종) | 1 | 2 | 1 | 0 | 1 | — |

[작업 패킷]

### A0. Scope Lock 기록
- Tier A/B/New Watchlist 표를 출력한다.
- Tier A가 5개를 초과하면 실행하지 말고 `human_lock.lock_type = SCOPE_LOCK`으로 중단한다.

### A1. Tier A 심화 조사
Tier A 각 작물에 대해 MC1-1b 재채점에 필요한 범위만 조사한다.

**D1 시장 매력도용**
- FAOSTAT 최근 5년(latest_available_year 기준) 생산량/재배면적 추세, 가능하면 CAGR
- 상위 생산국 5개와 점유율
- 상업 종자시장 규모 또는 hybrid seed 비중(가능한 경우)
- UN Comtrade 수출입 흐름은 순위 판단에 영향 있을 때만

**D3 사업 실행 가능성용**
- 주요 target 시장의 종자 수출입 규제, ABS/Nagoya 경로, IP 보호 가능성
- farmer-saved seed 또는 상업종자 침투 가능성
- N사 delivery 가능성에 영향을 주는 현지 파트너십/경쟁 구조

**D5 전략적 타이밍용**
- VACS/CGIAR/국가 정책/ODA 또는 국제 펀딩 신호
- 시장 window 3년 내 여부

**D2/D4 확인용**
- NCBI Genome, Ensembl Plants, 대표 논문에서 reference/pangenome 존재 여부만 확인한다.
- genome size/ploidy/repeat 등 상세 난이도는 MC2-1로 넘긴다.

[ReAct-lite 패턴]
각 핵심 셀은 아래 루프를 따른다.
1. **Search**: 공식 통계/DB/논문/기관 문서 검색
2. **Observe**: 연도·출처·신뢰등급·태그 확인
3. **Decide**: 충분하면 기록, 부족하면 대안 소스 검색, 3회 후 부족하면 `[미확보]` 확정

### A2. Tier B 역전 가능성 스캔
Tier B는 아래 두 질문만 답한다.

1. **시장/수요 trigger**: Tier A 3위 후보보다 D1 또는 D5에서 강하게 뒤집을 근거가 있는가?
2. **유전체/기획 trigger**: D2 또는 발표 기획 가치가 Tier A 3위 후보보다 명확히 강한가?

판정:
- trigger 2개 모두 강함 → “승격 후보”로 표시하고 `DATA_SCOPE_CHECK` 또는 Tier A 보충 조사 요청
- trigger 1개만 강함 → appendix/watchlist, full scoring 금지
- trigger 0개 → 제외

### A3. New Watchlist trigger triage
새 후보 2~3개를 찾되, full scoring하지 않는다. 각 후보는 아래 4개 trigger만 기록한다.

| trigger | 기준 |
|---|---|
| 수요 증가 | 최근 수요/시장/정책 신호가 명확한가 |
| 유전체 공백 | reference/pangenome 공백 또는 품종특이 reference 가치가 있는가 |
| N사 적합성 | hybrid F1/B2B genomics/글로벌 파트너십과 맞는가 |
| 5주 발표 가능성 | 학부 3학년 팀의 5주 기획안으로 설명 가능한가 |

4개 중 3개 이상이면 승격 후보. 2개 이하이면 appendix.

### A4. Evidence gap 영향도 판정
모든 `[미확보]`, `[미검증]`, `[미결]`, `[상충]` 셀을 아래로 분류한다.

| 등급 | 의미 | 처리 |
|---|---|---|
| Rank-critical | Top 3 또는 최종 1위를 뒤집을 수 있음 | 자동 retry 1회 또는 형주 체크포인트 |
| Rank-relevant | 리스크 설명에는 필요하지만 Top 3는 유지 | carry_forward |
| Appendix-only | 순위와 무관 | appendix 기록 후 진행 |

[Few-shot 예시 — Tier A 셀 작성 예시]

> **비둘기콩 — D1 시장 데이터 예시:**
> | 지표 | 값 | 태그 | 출처 | D1 영향 |
> |---|---|---|---|---|
> | 글로벌 생산량 ({latest_available_year}) | X.XX M 톤 | [실측] [원문확인] [체인확인] | FAOSTAT Production/Crops, item=Pigeon peas, year={latest_available_year} | D1 2 유지/조정 근거 |
> | 재배면적 CAGR ({latest_available_year-4}~{latest_available_year}) | +X.X% | [실측] [원문확인] [체인확인] | FAOSTAT 연도별 area harvested에서 산출 | D1 성장성 근거 |
> | hybrid 비중 | <X% 또는 자료 없음 | [전문가추론] [미검증] [체인 미검증] | 문헌 기반 추론, 직접 수치 없으면 명시 | D1/D3 불확실성 |
>
> 수치 X는 placeholder이다. 실제 실행 시 latest_available_year 기준으로 채워라. 고정 연도 금지.

[출력 형태]
- Scope Lock 표
- Tier A evidence matrix: 작물 × D1/D3/D5, 각 셀 핵심 수치 1~2개 + 출처 + 3축 태그
- D2/D4 DB 확인 요약표: 작물, reference/pangenome 상태, 확인 DB/논문, MC2-1로 넘길 질문
- Tier B 역전 스캔 표: 시장/수요 trigger, 유전체/기획 trigger, 승격 여부
- New Watchlist trigger 표: 후보별 4 trigger, 승격 여부
- Evidence gap 영향도 표
- 데이터 출처 목록

[자기 검증 — Observation]
출력 완료 후 아래에 답하라.
(a) Tier A가 5개 이하인가? Tier B full deep-dive를 하지 않았는가?
(b) Tier A의 P0 핵심 셀은 원문/공식 DB에서 확인했는가?
(c) P1 또는 Tier B 미확보가 Top 3를 흔드는가, 아니면 carry_forward 가능한가?
(d) D2/D4는 MC1-1a 범위를 넘지 않고 DB 확인 수준으로만 처리했는가?
(e) 승격 후보가 있다면 왜 자동 확정하지 않고 형주 판단으로 보냈는가?
“🔍 Self-Check”로 출력.

[Wrapper 출력]
위 출력 전체를 JSON wrapper의 payload에 담고, state/gate/checkpoint_summary를 채워서 최종 출력하라. `human_lock`이 필요한 경우 반드시 기록하라.
</stage_0_command>

**예상 소요:** 하네스 1사이클 35~55분 (Tier A 최대 5개 기준)
**Owner:** 자동 (Claude/GPT) + Scope Lock은 형주

🚦 **Decision Gate: 데이터 충분성 검증** (MC1-1a → MC1-1b 진입 조건)

| # | 조건 | 통과 기준 | 미통과 시 |
|---|---|---|---|
| 1 | Scope 준수 | Tier A ≤ 5, Tier B full deep-dive 없음, New Watchlist full scoring 없음 | Scope Lock 재확인, `HALT_HUMAN_CHECKPOINT` |
| 2 | Tier A D1/D3/D5 evidence 커버리지 | Tier A × D1/D3/D5 중 Rank-critical `[미확보]` 0개, 전체 `[미확보]` ≤ 3개 | Rank-critical은 1회 보충, 비핵심은 carry_forward |
| 3 | P0 원문 검증 | Tier A 및 승격 후보의 P0 셀 100% 원문/공식 DB 확인 | 1회 자동 보충 후 미해결 시 형주 |
| 4 | P1 처리 | P1 ≥ 60% 이상 확인. 80% 미달이어도 순위 영향 없으면 carry_forward 가능 | 순위 영향 있으면 보충 또는 형주 |
| 5 | Tier B 역전 스캔 | Tier B 전 후보에 대해 trigger 2개 판정 완료 | trigger 미판정 후보만 보충 |
| 6 | New Watchlist triage | 2~3개 후보에 대해 4 trigger 판정. 승격 후보는 자동 확정하지 않음 | 승격 애매하면 형주 |
| 7 | D2/D4 범위 준수 | DB/문헌 확인 수준으로만 처리하고 deep-dive는 MC2-1로 이월 | 범위 초과 내용은 appendix로 이동 |
| 8 | D등급 배제 및 체인 건강성 | D등급 출처가 의사결정 근거에 없고, 최종 결론의 인과 체인이 확인됨 | 대체 출처 확보 또는 결론에서 분리 |

> **Gate 판정 → wrapper 반영**: gate.verdict를 `PASS`/`FAIL`/`CONDITIONAL`로 기록한다. 이후 교차검증을 필수 실시하고, F 규칙에 따라 `final_verdict`를 산출한다.
> - `final_verdict = PASS` → `final_action = PROCEED` → MC1-1b 진행.
> - `final_verdict = CONDITIONAL` + 순위 영향 없음 → `final_action = PROCEED`, `DATA_SUFFICIENCY = PASSED`, `carry_forward` 기록.
> - `final_verdict = FAIL` 또는 승격/순위 영향 판단 필요 → `final_action = RETRY` 또는 `HALT_HUMAN_CHECKPOINT`.

---

## MC1-1b: 실증 데이터 기반 D점수 재채점 ⚖️

- **유형:** EVALUATE
- **조사 범위:** MC1-1a-lite 데이터를 기반으로 Tier A + 승격 후보만 D1~D5 재채점. 비승격 Tier B와 New Watchlist는 appendix 처리
- **깊이:** standard
- **선행:** MC1-1a (`DATA_SUFFICIENCY = PASSED`, carry_forward 허용)
- **산출물:**
  - 재채점된 정규화 Score 순위표
  - 기존 점수 vs 재채점 비교표
  - Sensitivity analysis 결과
  - Top 3 확정안
  - 형주 Top 3 Lock용 결정 카드
- **PBL 학습목표 연결:** 학습목표 1
- **완료 시 상태전이:** `TARGET_CROP: TBD → SHORTLISTED`, `SCORING: LEGACY → RESCORED`
- **human_lock:** `TOP3_LOCK` 필수. PASS여도 MC1-1c 실행 전 형주 승인 필요

<stage_0_command>
[Role] 너는 다기준 의사결정 분석가이다. AHP 가중합 기반 스코어링과 sensitivity analysis를 수행하고, 점수 변동의 근거를 추적하는 것이 역할이다. 판정 루브릭을 정확히 적용하되, AND/OR 조건을 혼동하지 마라.

MC1-1a-lite의 실증 데이터를 기반으로 Tier A 및 승격 후보의 D1~D5 점수를 재채점하라.

[공통 앵커 블록 적용] — 이 문서 상단 “공통 앵커 블록” 전체를 이 위치에서 적용한다.

[입력]
- MC1-1a wrapper payload
- MC1-1a `carry_forward` 및 `unresolved` 목록
- Scope Lock 표: Tier A / Tier B / New Watchlist
- 기존 AHP weight: D1(0.363) > D2(0.219) = D3(0.219) > D5(0.107) > D4(0.092)
- 기존 점수표: MC1-1a 참조
- 판정 기준: 이 문서 상단 “D점수 0/1/2 판정 루브릭”
- 산식: 이 문서 상단 “Soft Score 가중합 산식”

[후보 집합 규칙]
1. 재채점 대상은 Tier A + MC1-1a에서 승격된 Tier B/New Watchlist 후보로 제한한다.
2. 비승격 Tier B는 full scoring하지 않고 appendix에 “역전 가능성 낮음/보류”로 기록한다.
3. carry_forward 셀은 보수/기준/낙관 3가지로 sensitivity에 반영한다.

[재채점 규칙]
1. D1/D3/D5는 MC1-1a의 실증 데이터를 직접 인용해 판정한다.
2. D2/D4는 기존 점수 유지가 기본이다. NCBI/Ensembl/논문 확인 결과 기존 점수와 명확히 충돌할 때만 `[미결]`로 표시하고 형주 판단으로 보낸다.
3. 기존 점수와 달라지는 셀은 변경 전/후, 변경 근거, 순위 영향도를 반드시 기록한다.
4. 근거가 부분적이면 보수적 판정 + `[부분근거]`; 출처 상충이면 양쪽 인용 + `[상충]`.

[가중합 계산]
- 정규화 Score = (Σ(Di × Wi) / 2.000) × 100
- 모든 재채점 대상에 대해 계산. 소수점 2자리.
- weight 합계 = 1.000 확인 필수.

[Sensitivity Analysis — 필수]
- D1 weight ±20%
- D2 > D1 역전 시나리오
- D3/D4/D5 weight ±20% 중 Top 3 변동 여부
- carry_forward 셀을 보수(0), 기준(기존/부분근거), 낙관(2)으로 처리했을 때 Top 3 변동 여부
- 1위 추천이 단일 가정에 과의존하는지 점검

[출력 형태]
- 재채점 정규화 Score 순위표
- 기존 vs 재채점 비교표
- Sensitivity matrix
- Top 3 확정안: 각 후보 2줄 근거 + 가장 큰 리스크 1줄
- Top 3 Lock 결정 카드:
  - “이 Top 3를 승인해도 되는 이유”
  - “형주가 바꿔야 할 수 있는 조건”
  - “MC1-1c로 넘길 carry_forward”
- 미결 셀 목록

[자기 검증 — Observation]
(a) 재채점 대상이 Tier A + 승격 후보로 제한되었는가?
(b) D점수 변경 근거가 MC1-1a payload 또는 DB 확인에서 직접 왔는가?
(c) Sensitivity에서 Top 3 또는 1위가 뒤집히는가? 뒤집히면 현실적 trigger가 있는가?
(d) carry_forward를 비관 처리해도 Top 3가 유지되는가?
(e) 형주가 3분 안에 Top 3를 승인/수정할 수 있도록 결정 카드가 충분히 명확한가?
“🔍 Self-Check”로 출력.

[Wrapper 출력]
위 출력 전체를 JSON wrapper의 payload에 담고, state/gate/checkpoint_summary를 채워서 최종 출력하라. `final_verdict=PASS`여도 `human_lock.required=true`, `human_lock.lock_type=TOP3_LOCK`으로 기록하라.
</stage_0_command>

**예상 소요:** 하네스 1사이클 25~40분
**Owner:** 자동 (Claude/GPT) + Top 3 Lock은 형주

🚦 **Decision Gate: Top 3 확정**

| # | 확정 기준 | 미충족 시 |
|---|---|---|
| 1 | 후보 집합 준수 | 비승격 Tier B/New Watchlist를 full scoring했으면 MC1-1b 재실행 |
| 2 | 점수 상위 3개 산출 | 산식/schema 오류면 MC1-1b 재시도 |
| 3 | 동점 처리 | D1 점수 우선 → D3 점수 우선. 여전히 동점이면 형주 판단 |
| 4 | 미결 셀 영향 | 비관 시나리오에서도 Top 3 유지 시 포함 가능. 3위/4위가 바뀌면 형주 판단 |
| 5 | Sensitivity 역전 | “높음” 2개 이상이면 자동 확정 금지, 형주 Top 3 Lock |
| 6 | 결정 카드 | 형주가 승인/수정할 수 있는 요약이 없으면 MC1-1b 보완 |

**📐 Sensitivity 역전 판정 규칙**

역전이 발생한 각 시나리오에 대해 아래 3개 기준을 [높음/중간/낮음]으로 평가한다.

| 기준 | 높음 | 중간 | 낮음 |
|---|---|---|---|
| ① Weight 변동의 현실적 trigger | N사 전략 변경, 규제 환경 변화 등 구체적 사유 존재 | 가능하지만 개연성 낮음 | 해당 weight 역전 시나리오가 N사 맥락에서 비현실적 |
| ② ±20% 범위 내 발생 여부 | ±10% 이내에서 역전 | ±10~20%에서 역전 | ±20% 초과해야 역전 |
| ③ 역전 후 score margin | 새 1위가 5점 이상 차이 또는 기존 1위와 0.5점 이내 동점권 | 1~5점 차이 | 0.5점 이내 경계선 노이즈 |

> **판정**: 3개 기준 중 2개 이상 “높음”이면 자동 확정하지 말고 형주 Top 3 Lock으로 보낸다.

> **Gate 판정 → wrapper 반영**:
> - `final_verdict = PASS` → `final_action = PROCEED`, 단 `human_lock = TOP3_LOCK`으로 MC1-1c 실행 전 형주 승인 필요.
> - `final_verdict = CONDITIONAL` → Top 3 안정이면 carry_forward + Top 3 Lock, 불안정하면 `HALT_HUMAN_CHECKPOINT`.
> - `final_verdict = FAIL` → E-2 FAIL 전이 적용.

---

## MC1-1c: 최종 작물 선정 + 블록 1 Brief 📊

- **유형:** SYNTHESIS
- **조사 범위:** 형주가 Top 3 Lock에서 승인한 후보만 비교 → 최종 1개 추천 → 발표 블록 1 brief 작성
- **깊이:** standard
- **선행:** MC1-1b + 형주 `TOP3_LOCK` 승인
- **산출물:**
  - Top 3 심층 비교
  - 최종 1개 추천 + 선정 이유 서사
  - 발표 블록 1 brief
  - 부록용 작물 선정 과정 요약
  - Final Crop Lock 결정 카드
- **PBL 학습목표 연결:** 학습목표 1 + 6 (의사소통 — brief 포맷)
- **완료 시 상태전이:** `TARGET_CROP: SHORTLISTED → CONFIRMED`, `SCORING: RESCORED → FINAL`, `BLOCK1_BRIEF: NOT_STARTED → FINAL`
- **주의:** `TARGET_CROP=CONFIRMED`는 AI-confirmed recommendation이다. PBL 최종 작물 lock은 형주 `FINAL_CROP_LOCK` 승인 후 완료된다.

<stage_0_command>
[Role] 너는 전략 컨설턴트 겸 발표 코치이다. 데이터 기반 의사결정을 명쾌하게 전달하는 것이 전문이다.

[공통 앵커 블록]
> - **범위 제한**: MC1-1c의 조사 범위를 벗어난 새로운 데이터 수집 금지. MC1-1a 데이터와 MC1-1b Top 3 Lock에서 승인된 결과만 사용.
> - **출처 규칙**: 정량 수치에 반드시 출처(DB명 + 접근 시점)를 병기한다. 출처 없는 수치는 `[미확보]` 태그.
> - **반증 조건**: 최종 추천 작물의 반증 조건을 명시한다.
> - **PBL 맥락**: N사는 국내 본사 종자회사이나, 작물·시장·파트너십은 글로벌 범위로 본다. 학부 3학년 팀의 5주 PBL 기획안이며, 실험 수행이 아니라 연구수행 전략 설계가 목적이다.
> - **시간 앵커**: 최신 데이터 기준 `{latest_available_year}`. 데이터 연도 명시.
> - **마이크로사이클 인식**: 이 stage는 MC1-1c (3/3)이다. 결론의 근거는 반드시 이전 stage payload에서 직접 인용한다.

[Top 3 심층 비교]
형주가 승인한 Top 3를 아래 4항목으로 비교하라.
1. **유전체 기술 가치** — reference genome 또는 품종특이 reference가 N사에 주는 전략적 가치
2. **사업 시너지** — N사 사업모델과의 연계, 매출/파트너십 잠재력
3. **기술적 실현 가능성** — D4는 MC1-1 수준의 DB 확인만 사용하고, deep-dive 질문은 MC2-1로 넘김
4. **리스크 요인** — carry_forward, 미결 셀, sensitivity 역전 시나리오

[Part A: 최종 추천 논거 구축]
- 1위 작물이 왜 2·3위보다 나은지 정량/정성 근거로 논증
- 이 작물을 선정하지 않았을 때의 기회비용
- 교수님이 흥미를 느낄 학습 포인트
- MC2-1로 이어지는 유전체 질문

[Part B: 최종 1개 추천]
- 추천 작물 + 핵심 근거 3줄
- 기각된 2개 후보의 기각 사유 각 1줄
- 최대 반론 1개 + 대응
- 반증 조건: “이 추천이 틀리려면 ___이어야 한다”

[Part C: 발표 블록 1 Brief]
아래 구조로 한국어 brief를 작성하라.
1. 도입 — 왜 N사가 표준유전체 프로젝트를 하는가
2. 선정 과정 요약 — 후보군 → Hard Filter → AHP Soft Score → Top 3 → 최종 추천
3. 최종 작물 소개 — 무엇이고, 왜 이 작물인가
4. 선정 근거 핵심 수치 3개
5. 다음 단계 예고 — 유전체 스펙 분석 → 시퀀싱 전략

[출력 형태]
- Top 3 비교표
- 최종 추천 + 기각 사유
- 블록 1 brief
- 부록용 선정 과정 1페이지 요약
- Final Crop Lock 결정 카드:
  - 승인 권고
  - 교체를 고려해야 할 조건
  - MC2-1에서 반드시 확인할 질문 3개

[자기 검증 — Observation]
(a) 최종 추천이 MC1-1b의 점수 순위와 일치하는가? 불일치하면 이유가 설명되어 있는가?
(b) brief가 5분 발표에 맞게 압축되어 있는가?
(c) “왜 이 작물인가”가 MC1-1a/1b의 실증 데이터에 근거하는가?
(d) 정량 수치에 출처가 병기되어 있는가?
(e) 반증 조건과 MC2-1 이월 질문이 명시되어 있는가?
“🔍 Self-Check”로 출력.

[Wrapper 출력]
위 출력 전체를 JSON wrapper의 payload에 담고, state/gate/checkpoint_summary를 채워서 최종 출력하라. `final_verdict=PASS`여도 `human_lock.required=true`, `human_lock.lock_type=FINAL_CROP_LOCK`으로 기록하라.
</stage_0_command>

**예상 소요:** 하네스 1사이클 25~35분
**Owner:** 자동 (Claude/GPT) + Final Crop Lock은 형주

🚦 **Decision Gate:** AI 최종 추천 → 형주 Final Crop Lock → MC2-1 진행

| # | 확정 기준 | 미충족 시 |
|---|---|---|
| 1 | TARGET_CROP = `CONFIRMED` | wrapper state 확인 |
| 2 | BLOCK1_BRIEF = `FINAL` | brief 미작성 시 재시도 |
| 3 | Self-Check (a)~(e) 전항 충족 | 경미 미충족은 AUTO_REPAIR, 핵심 미충족은 형주 |
| 4 | strong 반론 없음 | strong 반론 있으면 `FINAL_CROP_LOCK`에서 형주 결정 |
| 5 | MC2-1 이월 질문 3개 명시 | 누락 시 brief 보완 |

> **Gate 판정 → wrapper 반영**:
> - `final_verdict = PASS` → `final_action = PROCEED`, `human_lock = FINAL_CROP_LOCK`. 형주 승인 후 MC1-1 완료 및 MC2-1 진입.
> - `final_verdict = CONDITIONAL` → 경미 미충족은 자동 보완, strong 반론은 형주 체크포인트.
> - `final_verdict = FAIL` → E-2 FAIL 전이 적용.

---

### G. State Invariants (상태 불변 조건)

각 상태전이의 사전/사후 조건을 정의하여 FSM이 유효한 상태만 유지하도록 보장한다. 자동 루프는 각 전이 후 아래 invariant를 검증하고, 위반 시 `schema_invalid` issue로 처리한다.

| 변수 | 불변 조건 | 위반 시 처리 |
|------|---------|------------|
| TARGET_CROP | `CONFIRMED`는 MC1-1c `final_verdict=PASS` 후에만 도달 가능. `SHORTLISTED`는 MC1-1b `final_verdict=PASS` 후에만 도달 가능. 역방향 전이는 FAIL rollback으로만 가능 | `schema_invalid` → 같은 sub-MC 재시도 |
| DATA_SUFFICIENCY | **Enum ordinal: INCOMPLETE(0) < GATE_READY(1) < PASSED(2)**. `≥` 비교는 이 서수 기준. `PASSED`는 MC1-1a `final_verdict=PASS` 시 설정 (GATE_READY는 gate.verdict 수준 중간 상태). `PASSED` 이후 `INCOMPLETE`로 돌아가는 경로는 FAIL rollback뿐 | `schema_invalid` → wrapper 재생성 |
| SCORING | `RESCORED` → `LEGACY` 역전이는 FAIL rollback으로만 가능. `FINAL`은 MC1-1c `final_verdict=PASS` 후에만 도달 | `schema_invalid` → 같은 sub-MC 재시도 |
| BLOCK1_BRIEF | `FINAL`은 MC1-1c `final_verdict=PASS` 후에만 도달. 다른 stage에서는 항상 `NOT_STARTED` | `schema_invalid` → wrapper 재생성 |
| **교차 변수** | MC1-1b 진입 시 `DATA_SUFFICIENCY = PASSED` 필수 (ordinal ≥ 2). MC1-1c 진입 시 `TARGET_CROP = SHORTLISTED ∧ SCORING = RESCORED ∧ DATA_SUFFICIENCY = PASSED` 필수 | 사전 조건 미충족 → 이전 stage FAIL 처리 |
| **wrapper** | `final_verdict` 없이 `final_action` 설정 불가. `cross_verification` 없이 `final_verdict` 산출 불가. `rollback_state`는 `final_verdict=FAIL`일 때만 non-null | `schema_invalid` → wrapper 재생성 |
| **human_lock** | `human_lock.required=true`는 state 값을 되돌리지 않는다. 단, 런타임은 `resume_condition` 충족 전 다음 stage를 실행할 수 없다. MC1-1b PASS 후 `TOP3_LOCK`, MC1-1c PASS 후 `FINAL_CROP_LOCK`은 필수 | 승인 누락 상태로 다음 stage 실행 시 `schema_invalid` → 실행 중단 |

> **Invariant 검증 시점**: 각 sub-MC wrapper 출력 직후, 교차검증 전에 1차 검증. 교차검증 후 final_verdict 산출 직후 2차 검증. 위반 발견 시 `cross_verification.issues`에 `issue_type: "schema_invalid"` 항목 추가.

---

## 전체 흐름

```
Preflight
Scope Lock (형주)
   │
   ▼
MC1-1a-lite (SURVEY)
Tier A 심화 + Tier B 역전 스캔 + New Watchlist trigger
   │
   ├─ PASS / CONDITIONAL(PROCEED) ─▶ MC1-1b
   ├─ DATA_SCOPE_CHECK 필요 ──────▶ 형주 판단 후 재개
   └─ FAIL ───────────────────────▶ 보충 모드 retry(max hard 2, 운영상 0~1)

MC1-1b (EVALUATE)
재채점 + sensitivity + Top 3 확정안
   │
   ├─ PASS / stable CONDITIONAL ─▶ TOP3_LOCK (형주) ─▶ MC1-1c
   ├─ 동점/역전/순위 영향 미결 ─▶ 형주 판단
   └─ FAIL ─────────────────────▶ MC1-1b 또는 MC1-1a 보충

MC1-1c (SYNTHESIS)
최종 추천 + 블록 1 brief
   │
   ├─ PASS ─▶ FINAL_CROP_LOCK (형주) ─▶ MC1-1 완료 → MC2-1
   ├─ 경미 미충족 ─▶ AUTO_REPAIR_AND_REJUDGE
   └─ strong 반론 ─▶ 형주 판단
```

**Gate 3개:** 데이터 충분성 → Top 3 확정 → AI 최종 추천
**Human lock 3개:** Scope Lock → Top 3 Lock → Final Crop Lock
**운영 비중:** 자동화 약 70%, 형주 검증 약 30%
**총 예상 소요:** 자동 하네스 약 85~130분 + 형주 lock 검토 15~25분. 기존 v2.9의 3~4시간짜리 조사 모드를 줄인 운영형 버전이다.

### 🕐 GPT 검증 폴링 전략

GPT Pro Thinking 검증 프롬프트의 응답 대기 시 아래 간격으로 폴링한다.

| 체크 순서 | 전송 후 경과 시간 |
|---|---|
| 1차 | 4분 |
| 2차 | 7분 |
| 3차 | 10분 |
| 4차~ | 이후 3분 간격 반복 |

> `verifier_timeout`은 sub-MC retry로 보지 않고 교차검증만 재시도한다.

---

## 변경 이력

| 항목 | v2.9까지 | v2.9-lite (이 버전) |
|---|---|---|
| FSM / wrapper / final_verdict | v2.9 유지 | 유지. 단 `human_lock` 운영 필드 추가 |
| 자동 루프 기준 | `final_verdict` 유일 기준 | 유지 |
| retry policy | hard cap 2회 | hard cap 2회 유지, 운영상 0~1회 중심. retry는 탐색이 아니라 수리 |
| MC1-1a 조사범위 | Shortlist 9개 × 5축, Tier A/B 구분 | Scope Lock 도입. Tier A 최대 5개 심화, Tier B 역전 스캔, New Watchlist trigger triage |
| P0/P1 Gate | P0 100%, P1 ≥80% 기준 | Tier A/승격 후보 P0는 엄격 유지. P1은 순위 영향 없으면 carry-forward |
| D2/D4 | MC1-1a 범위 밖, DB/문헌 확인 | 유지. deep-dive는 MC2-1로 명시 이월 |
| 형주 개입 | 완료 후 체크포인트 중심 | Scope Lock, Top 3 Lock, Final Crop Lock으로 전진 배치 |
| State Invariants | DATA_SUFFICIENCY ordinal 등 v2.9 유지 | 유지 + human_lock invariant 추가 |
| 총 운영 모드 | 3~4시간 자동 조사 모드 | 자동 70% / 형주 30%의 운영형 경량 모드 |

*MC1-1 Detailed Roadmap v2.9-lite · 2026-04-20 · v2.9 FSM 유지 + Scope Lock/Tier A 경량화 + human-lock 운영 + retry budget 수리형 전환*
