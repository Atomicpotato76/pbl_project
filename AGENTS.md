# AGENTS.md — AI 와 유전체학 프로젝트 운영 규칙

## 최상위 하드 룰

- 모든 세션은 시작 즉시 반드시 `AGENTS.md`를 먼저 읽고, 그 규칙을 확인한 뒤에만 작업을 시작한다.
- 이 규칙은 예외 없는 하드 룰이며, 다른 작업 지시보다 먼저 적용한다.
- 사용자가 먼저 요청하지 않은 한, 에이전트는 `원하신다면 ~을 조사해 드리겠습니다`, `필요하시면 제가 더 찾아보겠습니다`처럼 추가 조사·탐색·확장 작업을 선제 제안하지 않는다.
- 위 항목은 단순 권장사항이 아니라 하드 룰이다. 사용자의 명시적 요청이 있기 전에는 관련 제안을 먼저 꺼내지 않는다.

---

이 파일은 이 프로젝트에서 에이전트가 작업할 때 따라야 하는 상시 규칙을 정리한 루트 지침이다.

---

## 1. 기본 원칙

- 이 프로젝트는 `scenario-first`, `artifact-first`, `verification-first`로 운영한다.
- 결론을 먼저 닫지 말고, 질문·근거·판정 순서를 지킨다.
- `최종 확정`과 `working / provisional selection`을 항상 분리해서 쓴다.
- 문서와 답변에서 영어 용어를 쓸 때는 첫 등장 시 한국어 설명을 바로 옆에 붙인다. 다만 파일명, 코드, 공식 고유명사 원문, 법령/논문 제목은 예외로 둘 수 있다.

---

## 2. 에이전트 운영 규칙

- 에이전트 프롬프트를 작성할 때는 항상 아래 문서를 먼저 참조한다.
  - `Self_Working_pipeline/docs/multi_agent_design_adoption_guide.md`
  - `엔지니어링/meta-prompt-multi-agent-design-brief.md`

- 이 프로젝트에서는 원칙적으로 언제나 멀티 에이전트를 사용한다.
  - 기본 운영 방식은 `slim coordinator + explicit worker ownership`이다.
  - 먼저 `read-only 분업`으로 쪼개고, 이후 coordinator가 결과를 합친다.
  - 서로 다른 에이전트가 같은 쓰기 범위를 동시에 다시 설계하지 않게 owner를 분리한다.

- 에이전트 프롬프트에는 아래 요소를 명시적으로 넣는다.
  - 현재 단계(stage)
  - in-scope / out-of-scope
  - 읽어야 할 파일 순서
  - 출력 계약(output contract)
  - 금지사항
  - 다른 에이전트와의 역할 분리

---

## 3. 프롬프트 작성 규칙

- 질문 프롬프트, 검증 프롬프트, GPT/Claude 실행 프롬프트를 작성할 때는 항상 아래 문서를 먼저 참조한다.
  - `엔지니어링/prompt-engineering-guide.md`
  - `엔지니어링/prompt-engineering-tiers.md`
  - `엔지니어링/meta-prompt-checklist-for-llm.md`

- 프롬프트를 쓸 때는 아래 원칙을 우선 적용한다.
  - 역할(role)과 임무(task)를 맨 앞에 둔다.
  - 현재 단계와 범위를 먼저 잠근다.
  - 원하는 출력 형식을 명시한다.
  - `do_not_do`와 anti-pattern을 분리해서 적는다.
  - 사실, 추론, 가설, unknown을 섞지 않게 한다.
  - 필요한 경우에만 아주 짧은 output example을 넣고, 과도한 few-shot은 피한다.
  - 과도한 디테일 집착을 피하고, 현재 판정이나 선택을 실제로 바꾸는 정보만 추가로 요구한다.
  - 동일한 질문을 표현만 바꿔 반복하거나, 같은 근거를 형식만 바꿔 다시 정리하는 작업은 금지한다.
  - 새 근거, 새 충돌, methodological blocker가 없는 상태에서 재탐색·재서술·재채점 루프에 들어가지 않는다.
  - `good enough to decide` 상태에 도달하면 우선 provisional selection을 고정하고, 남은 불확실성은 `decision-changing unknown`만 남긴다.

- 최신 프로젝트 프롬프트를 만들거나 수정할 때는 아래 폴더의 최신 문서를 우선 기준으로 삼는다.
  - `최신 상황/03_검증프롬프트와설정`

---

## 4. 검증 실행 규칙

- 새 프롬프트를 작성한 뒤에는 아래를 확인한다.
  - 현재 live scope가 맞는가
  - old memo와 latest handoff가 충돌하지 않는가
  - 출력 블록이 실제로 파싱 가능한가
  - 질문-결론 순서 역전이 다시 생기지 않는가

- 검증 문구에서는 아래를 구분한다.
  - `methodological blocker`
  - `search debt`
  - `investigated unknown`
  - `direct conflict`

- `country-level relevance`를 `scenario-level absorbability`로 과잉 일반화하지 않는다.
- `public demand exists`를 `exact buyer lock exists`로 과잉 해석하지 않는다.

---

## 5. 패키지/복사 규칙

- 실행용 패키지나 `복사파일 임시폴더`를 구성할 때는 항상 최신 코어 문서만 넣는다.
- 구버전 프롬프트(`old brief`, `old GPT prompt`, `old Claude prompt`)는 새 run 패키지에서 제거한다.
- 패키지에는 항상 다음 셋을 우선 포함한다.
  - 최신 handoff
  - 최신 기준 문서
  - 최신 실행 프롬프트

---

## 6. 세션 handoff 규칙

- 사용자가 `새 세션 시작한다`고 말하면, 현재 세션이 끝나기 전에 최신 handoff용 `.md` 파일을 반드시 남긴다.
- handoff 파일의 기본 저장 위치는 `운영지원_통합/02_작업기록/종자선정/`이다.
- handoff 파일명은 기본적으로 `next_session_handoff_YYYY-MM-DD_<핵심주제>.md` 형식을 따른다.
- handoff 문서에는 최소 아래 3개 섹션을 반드시 넣는다.
  - `현재까지 진행 방향`
  - `현 세션 내용`
  - `향후 진행 방향`
- 필요하면 아래 섹션을 추가해서 다음 세션의 진입 비용을 낮춘다.
  - `즉시 읽어야 할 파일`
  - `열린 질문`
  - `하지 말아야 할 것`
- 새 세션이 시작되면 에이전트는 작업 시작 전에 `운영지원_통합/02_작업기록/종자선정/` 아래의 최신 `next_session_handoff_*.md`를 자동으로 먼저 읽고 상황을 파악한다.
- 최신 handoff와 오래된 메모가 충돌하면, 우선 최신 handoff를 기준으로 읽고 충돌 사실을 명시한다.

---

## 7. 우선 참조 파일

- `운영지원_통합/02_작업기록/종자선정/` 안의 최신 `next_session_handoff_*.md`
- `운영지원_통합/02_작업기록/종자선정/next_session_handoff_2026-04-22_축개정반영.md`
- `최신 상황/01_프로젝트기반과활성기준/01-04_활성기준_시나리오선정기준_v1.2.md`
- `최신 상황/03_검증프롬프트와설정/03-22_팀질문_축결정과가중치선택_2026-04-22.md`
- `엔지니어링/prompt-engineering-guide.md`
- `Self_Working_pipeline/docs/multi_agent_design_adoption_guide.md`

---

## 8. 커밋 메모 예시

- `docs(agents): add project-level multi-agent and prompt-authoring rules`
- `docs(agents): add session handoff trigger and auto-read rules`

---

## 9. Termination & Sufficiency Anchors

이 섹션은 에이전트가 무한 검증/무한 정교화 루프에 빠지지 않도록 하는 hard rule이다.
다른 모든 규칙보다 우선한다.

### A1. Finding Budget

- 한 검증 루프당 `P0 finding` 최대 **2개**.
- `P1`, `P2` finding은 별도 요청이 없으면 생성 금지.
- 2개를 넘어가면 가장 치명적 2개만 남기고 나머지 폐기.
- "더 찾을 수 있는데 참는다"가 아니라 "2개로 충분하다"가 기본 태도.

### A2. Fatal-Only Rule

- `fatal finding`의 정의:
  외부 평가자가 산출물(PPT / 발표 / 최종문서)만 보고 5분 안에 "앞뒤가 안 맞는다"를 지적할 수 있는 수준.
- 아래는 fatal이 아니다:
  - "더 엄격하게 만들 수 있음"
  - "경계가 더 선명할 수 있음"
  - "증거가 더 많으면 좋음"
  - "용어가 더 정제될 수 있음"
- 내부 방법론 문서의 정교함 부족은 fatal이 아니다.
  외부에 노출되지 않기 때문이다.

### A3. Elaboration ≠ Error

- "could be sharper" 와 "is wrong"을 분리한다.
- 전자는 **통과(PASS)**, 후자만 차단(BLOCK).
- 판정이 애매하면 **PASS 쪽으로 기울인다**.
  이유: 이 프로젝트의 실패 모드는 under-rigor가 아니라 over-rigor로 인한 실행 지연이다.

### A4. Time-Boxed Validation

- 어떤 검증도 같은 대상을 2회 이상 연속 검증하지 않는다.
- 2회차 검증은 "새로운 P0를 찾는" 일이 아니라 "1회차 P0가 실제로 닫혔는지 확인"하는 일이다.
- 새로운 finding을 1회차와 2회차에 걸쳐 각기 다르게 내면 그것 자체가 A1 위반이다.

### A5. Default to Proceed

- 판정 출력은 **GO / NO-GO** 이진이다.
- `NO-GO`를 내려면 A2의 fatal 정의를 만족함을 **명시적으로 증명**해야 한다.
- 증명 못 하면 자동 `GO`.
- "좀 더 보완하면 좋을 것 같다"는 `GO`다.

### A6. Context Reminder

이 프로젝트는:

- 5주짜리 학부 PBL이다. 박사논문이 아니다.
- 최종 평가자는 30분 발표를 보는 교수다.
- 내부 방법론 문서의 세부는 외부에 노출되지 않는다.
- 실패 모드는 "엉성한 기획"이 아니라 "완성 못 한 기획"이다.

### A7. Anti-Pattern Blacklist

에이전트는 아래 동작을 하지 않는다:

- 한 번 PASS 판정한 항목을 다음 루프에서 재검증
- 이전 루프에서 제기하지 않은 새 P0를 후속 루프에 갑자기 추가
- "완벽하게 하려면..." 으로 시작하는 제안
- 방법론 자체를 더 정교하게 만드는 메타 제안 (요청 없이)
- finding 개수 늘리기 위한 항목 쪼개기
  (splitting one concern into multiple findings to inflate count)
