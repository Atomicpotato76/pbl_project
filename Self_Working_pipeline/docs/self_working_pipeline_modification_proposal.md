# Self_Working_pipeline 수정 제안서

## 문서 목적
- `Self_Working_pipeline`를 현재 프로젝트의 최신 방향성에 맞는 실행 엔진으로 전환하기 위한 수정 범위를 정리한다.
- 이 문서는 GUI가 아니라 `CLI / 상태기계 / 연구 모드 / 검증 로직 / 프롬프트 주입 방식`만 다룬다.
- 다음 세션에서는 이 문서를 기준으로 우선순위대로 수정 작업을 시작한다.

## 기준 문서
- 프로젝트 방향:
  - `최신 상황/02_MC1-1_작물선정진행/02-01_기준하네스_작물선정라이트_v2.9.md`
  - `최신 상황/03_검증프롬프트와설정/03-01_검증배경_컨텍스트_v2.9.md`
- 프롬프트/하네스 설계 기준:
  - `엔지니어링/meta-prompt-checklist-for-llm.md`
  - `엔지니어링/prompt-engineering-guide.md`

## 요약 결론
현재 파이프라인은 "범용 멀티 에이전트 연구/개발 엔진"으로는 구조가 좋다. 하지만 현재 프로젝트에 바로 쓰기에는 다음 문제가 있다.

1. 승인 게이트가 일반형 `plan / checkpoint / merge`에 머물러 있어 `Scope Lock / Top 3 Lock / Final Crop Lock`을 직접 표현하지 못한다.
2. 연구 도구 축이 `PubMed / abstract / reference genome` 중심이라 작물선정 하네스의 `Tier A 심화 / Tier B 역전 스캔 / New Watchlist trigger`를 충분히 지원하지 못한다.
3. 엔지니어링 폴더 기반 프롬프트 규칙이 기본 강제가 아니라 설정 옵션이라, 현재 프로젝트 규칙과 자동 정렬되지 않는다.
4. 검증은 claim-source linkage를 잘 보지만, 현재 하네스가 요구하는 `외부 교차검증`, `human-lock`, `판정 override`, `evidence tier fail`까지 상태기계로 강제하지는 않는다.

따라서 이 파이프라인을 버리는 것이 아니라, "현재 하네스 전용 실행기"로 좁혀서 수정하는 것이 적절하다.

## 수정 목표
다음 4가지를 만족하도록 수정한다.

1. `MC1-1a / MC1-1b / MC1-1c`를 first-class workflow로 다룬다.
2. 승인 게이트를 `Scope Lock / Top 3 Lock / Final Crop Lock` 중심으로 재구성한다.
3. 프롬프트 생성과 검증에 엔지니어링 폴더 문서를 기본 지침으로 강제 주입한다.
4. 연구 결과의 구조 검증뿐 아니라 `외부 교차검증 필요 여부`, `human_lock 필요 여부`, `evidence 품질 부족`까지 명시적으로 판정한다.

## 비목표
- GUI 개선
- 범용 소프트웨어 개발 파이프라인으로서의 모든 유연성 유지
- 완전 자율주행 supervisor 확대
- 내부 하네스 전체를 다시 설계하는 작업

## 현재 방향성과 맞춰야 할 불변 조건
아래 조건은 수정 중 바꾸지 않는다.

1. 최신 하네스의 핵심 흐름은 `MC1-1a -> MC1-1b -> MC1-1c`다.
2. `human-lock`이 기본 운영 방식이다.
3. `retry`는 탐색 확대가 아니라 오류 수리 목적이다.
4. `MC1-1c`에서는 새로운 데이터 수집을 금지한다.
5. 최종 진행 기준은 단순 단계 통과가 아니라 검증을 포함한 판정 결과여야 한다.
6. 프롬프트 작성/수정 시 엔지니어링 폴더를 먼저 참조해야 한다.

## 제안하는 수정 축

### 1. 상태기계와 게이트 재설계
현재:
- `intake -> planning -> plan_approved -> executing -> reviewing -> testing -> merge_approved -> packaging -> completed`
- 승인 단계는 `plan / checkpoint / merge`

목표:
- 파이프라인 모드가 `research`일 때는 현재 일반형 게이트 대신 프로젝트 전용 게이트를 사용한다.
- 최소 요구 게이트:
  - `scope_lock`
  - `top3_lock`
  - `final_crop_lock`
- 일반형 `checkpoint`는 제거하지 않아도 되지만, 프로젝트 모드에서는 내부적으로 위 3개 중 하나로 매핑되어야 한다.

핵심 수정 포인트:
- `contracts/models.py`
- `core/state_machine.py`
- `services/orchestrator/service.py`
- `services/supervisor/service.py`

권장 방식:
- 기존 `ApprovalStage`를 확장하거나 별도 `ResearchGate` enum을 도입한다.
- `pipeline_mode="research"`일 때 오케스트레이터가 `MC1-1a / MC1-1b / MC1-1c`와 해당 lock을 우선 사용하도록 분기한다.
- `merge approval`는 현재 프로젝트에서는 최종 작물 lock 이후 패키징/산출물 정리의 보조 게이트로만 남긴다.

### 2. Workstream를 하네스 단계 중심으로 고정
현재:
- planner가 일반적인 연구/개발 workstream를 생성한다.
- layer 단위 완료 후 checkpoint를 만든다.

목표:
- 현재 프로젝트 모드에서는 planner가 아래 구조를 기본으로 생성해야 한다.
  - `mc1_1a_scope_and_evidence`
  - `mc1_1b_rescoring_and_top3`
  - `mc1_1c_final_recommendation`
  - `external_verification` 또는 단계별 verification workstream

핵심 수정 포인트:
- `services/planner/service.py`
- 필요 시 project preset 파일 추가

권장 방식:
- planner에 "project preset" 개념을 넣는다.
- 현재 프로젝트에서는 자유 생성 대신 "하네스 템플릿 기반 생성"을 우선한다.
- request digest가 길어져도 `HarnessContract`와 lock semantics가 절대 빠지지 않게 한다.

### 3. 엔지니어링 폴더 가이드를 기본 주입으로 변경
현재:
- `default_guidance_prompt_path` 기본값이 없다.
- 설정하지 않으면 엔지니어링 가이드가 프롬프트에 자동 주입되지 않는다.

목표:
- 이 프로젝트에서는 기본적으로 엔지니어링 폴더의 가이드를 프롬프트 지침으로 주입한다.
- 특히 아래 문서를 우선 반영한다.
  - `meta-prompt-checklist-for-llm.md`
  - `prompt-engineering-guide.md`

핵심 수정 포인트:
- `core/settings.py`
- `core/prompting.py`
- 필요한 경우 guidance composition helper 추가

권장 방식:
- 기본 guidance path를 단일 파일이 아니라 "조합 문서"로 만들고, 프로젝트용 compiled guidance를 읽게 한다.
- 설정이 비어 있어도 현재 프로젝트 루트 기준 기본 guidance 파일을 자동 탐색하게 한다.

### 4. 연구 도구 축 확장
현재:
- OpenAI adapter 도구는 `web_search`, `code_interpreter`, `search_pubmed`, `fetch_abstract`, `check_reference_genome`
- 현재 프로젝트의 시장/수요/작물선정 조사 범위에 비해 소스 축이 좁다.

목표:
- 작물선정 하네스가 실제로 요구하는 근거 수집을 지원할 수 있도록 조사 도구 계층을 확장한다.

우선순위:
1. 기존 `web_search`를 적극 활용하도록 research prompt 개선
2. source typing 강화
3. 필요 시 도메인별 함수 도구 추가

후보 도구:
- source normalization utility
- DOI/PMID/accession 외 시장 통계 source identifier 지원
- 작물/품목명 canonicalization helper

주의:
- 이번 수정에서 도구를 과도하게 늘리기보다, 먼저 prompt와 evidence schema를 넓혀 `web_search + 구조화 저장`으로 커버 가능한지 본다.

### 5. 검증 계층 강화
현재:
- reviewer는 프롬프트 수준에서 source quality를 본다.
- tester는 파일 존재, 출처 표기, claim-source 연결, source identifiers 등을 본다.
- 하지만 `외부 교차검증`, `human_judgment_required`, `evidence tier fail`, `lock required`는 구조적으로 강제되지 않는다.

목표:
- 검증 결과가 단순 pass/fail이 아니라 현재 하네스와 같은 운영 판단으로 이어지게 만든다.

추가할 판정 축:
- `requires_external_verification`
- `requires_human_lock`
- `evidence_quality_fail`
- `scope_violation`
- `new_data_forbidden_violation`

핵심 수정 포인트:
- `contracts/models.py`
- `services/reviewer/service.py`
- `services/cross_verifier/service.py`
- `services/testing/service.py`
- `services/orchestrator/service.py`

권장 방식:
- `ReviewReport` 또는 별도 `ResearchGateReport`에 위 필드를 추가한다.
- testing 단계는 구조 검증만 하고, reviewer 또는 dedicated verifier가 운영 판정을 내리게 분리해도 된다.
- 최소한 `MC1-1c`에서는 새 source 추가가 발견되면 fail 또는 human-lock escalation이 나와야 한다.

### 6. 외부 교차검증 인터페이스 확보
현재:
- reviewer는 Anthropic 계열, executor는 OpenAI 계열이다.
- 외부 교차검증은 `cross_verifier` 역할과 `external_verification` 단계로 명시적으로 분리하는 방향이 맞다.

목표:
- 생성 모델과 검증 모델의 역할 분리를 더 명시한다.

권장 방식:
- 기본 생성:
  - planner = Claude
  - executor = GPT
  - reviewer = Claude
  - cross_verifier = Claude
- 프로젝트 모드 추가:
  - `cross_verifier` 역할을 명시적으로 도입
  - 또는 reviewer를 2단계로 나누어 `reviewer`와 `cross_verifier`를 분리

비고:
- 이번 세션에서는 API 통합까지 강제하지 않고, 계약과 인터페이스부터 만들면 충분하다.

### 7. 방향 제안과 요약 문구의 프로젝트화
현재:
- `build_checkpoint_summary`, `build_direction_snapshot`는 범용 개발 파이프라인 표현이 많다.
- 한글 요약 일부는 인코딩 문제도 보인다.

목표:
- 현재 프로젝트에서 사람이 읽는 문구가 `작물선정`, `Top 3`, `Final Crop` 같은 실제 용어를 사용해야 한다.
- 파일 저장과 요약 렌더링은 UTF-8 기준으로 안정화한다.

핵심 수정 포인트:
- `services/memory/service.py`

권장 방식:
- 프로젝트 모드 전용 summary builder를 만들거나, 템플릿 문자열을 모듈로 분리한다.
- 인코딩 깨짐이 있는 문자열은 전부 정리한다.

## 구현 우선순위

### Phase 1. 프로젝트 정렬에 필요한 최소 수정
목표:
- 현재 프로젝트를 이 파이프라인 위에서 실행 가능한 형태로 만든다.

작업:
1. 기본 guidance 자동 연결
2. research preset planner 도입
3. approval gate를 `scope_lock / top3_lock / final_crop_lock` 중심으로 매핑
4. checkpoint summary 문구 정리

대상 파일:
- `core/settings.py`
- `core/prompting.py`
- `services/planner/service.py`
- `contracts/models.py`
- `services/orchestrator/service.py`
- `services/memory/service.py`

### Phase 2. 하네스 준수 강화
목표:
- 연구 결과가 하네스 위반 없이 흐르도록 만든다.

작업:
1. `MC1-1c` 새 데이터 금지 판정 추가
2. scope violation 판정 추가
3. `requires_human_lock` / `requires_external_verification` 추가
4. reviewer/tester 책임 분리

대상 파일:
- `contracts/models.py`
- `services/reviewer/service.py`
- `services/testing/service.py`
- `services/orchestrator/service.py`

### Phase 3. 외부 검증과 도구 보강
목표:
- 실제 교차검증과 소스 범위 부족 문제를 줄인다.

작업:
1. cross verifier 인터페이스 도입
2. 연구 evidence schema 확장
3. 필요 시 도메인 도구 보강

대상 파일:
- `services/adapters/*`
- `services/reviewer/service.py`
- `services/cross_verifier/service.py`
- `contracts/models.py`

## 완료 기준
다음이 만족되면 현재 프로젝트용 1차 전환이 완료된 것으로 본다.

1. `plan -> scope_lock -> mc1_1a -> top3_lock -> mc1_1b -> final_crop_lock -> mc1_1c` 수준의 흐름이 코드에서 표현된다.
2. 프롬프트 생성/검증 시 엔지니어링 폴더 guidance가 기본으로 주입된다.
3. `research mode`에서 결과물이 `reports + evidence json + gate-ready review` 구조를 가진다.
4. `external_verification` 단계가 전용 `cross_verifier` 경로를 통해 검토된다.
5. `MC1-1c`에서 새 데이터가 들어오면 자동 승인되지 않는다.
6. 사람이 읽는 상태 요약에서 프로젝트 용어가 정확히 나온다.
7. 기존 핵심 테스트는 유지되거나 프로젝트 모드 테스트로 대체된다.

## 권장 테스트 추가
기존 테스트는 많이 통과하지만, 현재 프로젝트용 커버리지는 별도 추가가 필요하다.

추가할 테스트:
- project preset planner가 `MC1-1a/b/c` workstream를 생성하는지
- `scope_lock` 없이는 실행이 멈추는지
- `top3_lock` 전에는 `mc1_1c`로 넘어가지 않는지
- `final_crop_lock` 없이는 완료 처리되지 않는지
- `MC1-1c`에서 새 source가 감지되면 fail 또는 block 되는지
- guidance path가 비어 있어도 엔지니어링 기본 guidance가 주입되는지

## 세션 인수인계용 권장 순서
다음 수정 세션에서는 아래 순서로 작업하는 것을 권장한다.

1. `contracts/models.py`
   - gate enum, review 판정 필드, project preset 관련 계약 추가
2. `core/settings.py` + `core/prompting.py`
   - 기본 guidance 연결
3. `services/planner/service.py`
   - project preset planner 도입
4. `services/orchestrator/service.py`
   - 연구 모드 전용 gate 흐름 적용
5. `services/reviewer/service.py` + `services/testing/service.py`
   - 하네스 위반 판정 강화
6. `services/cross_verifier/service.py`
   - 외부 교차검증 전용 판정 경로 분리
7. `services/memory/service.py`
   - 요약/방향 문구와 인코딩 정리
8. 테스트 추가

## 메모
- GUI는 현재 우선순위가 아니다.
- 범용 개발 파이프라인 기능은 유지하되, 현재 프로젝트 모드가 최우선이다.
- 이번 문서는 "수정 방향 고정" 문서이며, 세부 설계는 실제 코드 수정 중 조정 가능하다.
