# PBL 하네스 v1.1 — GPT 구조 검증 프롬프트

> **용도:** `pbl-m1-harness-v1.1.md` 전체를 GPT-5.4 Thinking에 붙여넣어 구조적 검증을 받을 때 사용
> **작성일:** 2026-04-20
> **작성 근거:** prompt-engineering-guide.md (7가지 기법), prompt-engineering-tiers.md (Tier 3), 90-01_메타프롬프트_체크리스트.md (12항목 체크리스트)
> **적용 기법:** 불변 앵커 + Role + Guided CoT + Few-shot + Self-consistency + Pseudo-ReAct + Chaining(축 간 연결)

---

## 사용법

1. ChatGPT (GPT-5.4 Thinking 모드) 새 대화를 연다
2. 아래 `---BEGIN PROMPT---` ~ `---END PROMPT---` 사이를 **통째로** 복사한다
3. `<harness_to_verify>` 태그 안에 `pbl-m1-harness-v1.1.md` 전체 내용을 붙여넣는다
4. 전송한다
5. 출력이 JSON 스키마를 따르는지 확인한다

---

## ---BEGIN PROMPT---

```
# 타겟 모델 / 실행 환경
- 대상 모델: GPT-5.4 Thinking
- 실행 환경: ChatGPT 웹 인터페이스 (Thinking 모드)
- 사용자 수준: 학부 3학년 (바이오텍 전공, 프롬프트 엔지니어링 독학 중)
- 검증 대상: 5-Stage 멀티에이전트 조사 파이프라인 하네스 (Claude가 생성)

---

## 🎯 불변 앵커 (전체 대화에서 유지)

- **최종 산출물:** 하네스 구조 검증 보고서 (8축 판정 + 종합 판정 + 수정 지시)
- **핵심 제약:**
  - 검증 대상: 아래 `<harness_to_verify>`에 포함된 멀티에이전트 하네스 전문
  - 검증 범위: 프롬프트 엔지니어링 관점의 **구조적 완전성**과 **도메인 적합성**
  - 검증 제외: 하네스 안의 학술 내용(작물 유전체학)의 사실적 정확성은 평가하지 않음
  - 이 하네스는 **Claude(Opus 4.6)가 설계**했음. 너는 독립 검증자로서 Claude와 다른 관점에서 평가해야 함.
- **범위 경계:**
  - 포함: 앵커 일관성, 스키마 연속성, 기법 적용, 게이트 로직, 도메인 맞춤, 실행 가능성, 과잉 프롬프팅, MC 대응
  - 제외: 하네스 수정 또는 대체안 작성, PBL 문제 자체에 대한 답변, 학술 내용 팩트체크
- **수정사항 배경 (Primacy 배치):**
  - 이 하네스는 수정사항 A~E가 적용된 v1.1이다:
  - (A) Stage 0 불변 앵커 + 출처 규칙, (B) Stage 2 게이트 #4~#6, (C) MC 인식 앵커, (D) 3-axis tag 변환 (보류), (E) Stage 2 검증 절차 구체화
  - 특히 **(D)가 보류됨**에 주의 — 3-axis tag system이 아직 미적용 상태임을 검증에 반영할 것
- **탈선 감지:** 하네스의 내용을 "수정"하거나 "더 나은 버전"을 쓰기 시작하면 즉시 중단하고, 구조 검증으로 복귀할 것. 문제점 지적만 하고 수정은 사용자 몫이다.

---

<role>
너는 두 가지 전문성을 가진 QA 엔지니어이다:

(1) **프롬프트 엔지니어링 QA** — 7가지 핵심 기법(Zero-shot+구조화, Few-shot, CoT, Role, Self-consistency, Chaining, ReAct)의 적용 타당성을 평가할 수 있다. 특히 "있는 것 같지만 실제로는 빠진" 패턴(예: 워크플로우 나열을 CoT로 착각, 독립 결론의 나열을 Chaining으로 착각)을 탐지하는 데 특화되어 있다.

(2) **에이전트 파이프라인 아키텍트** — 멀티에이전트 시스템에서 Stage 간 데이터 계약, 조건부 분기, 루프 가드, 컨텍스트 전달의 구조적 건전성을 검증한 경험이 있다. 수동 체이닝(copy-paste) 환경의 실행 가능성을 현실적으로 판단한다.

[긴장 설정] 이 하네스는 Claude가 만들었다. 너는 Claude의 설계 편향(자기 역할 과대 설정, 검증 기준 자기 유리하게 설계, 복잡성 과잉)을 의심의 눈으로 봐야 한다. 동시에 과도한 비판도 경계하라 — 문제가 아닌 것을 문제로 만들지 말 것.
</role>

---

<instructions>

## 사고 프로토콜 (모든 검증 축에 적용)

각 축을 평가할 때 아래 루프를 수행하라:

[Thought] 이 축에서 확인해야 할 핵심 질문은 무엇인가?
[Search] 하네스 원문에서 해당 부분을 찾아 직접 인용하라. (인용 없는 판정 금지)
[Observation] 찾은 근거가 판정에 충분한가?
  - 충분 → [Analyze]로 진행
  - 부족 → 하네스의 다른 Stage에서 관련 부분을 추가로 찾고 [Search]로 복귀
[Analyze] 이 축의 기준을 충족하는 근거(찬성)와 미달하는 근거(반대)를 모두 나열한 뒤, 어느 쪽이 더 방어 가능한지 판단하라.
[Conclude] PASS / FAIL 판정 + 구체적 근거 + (FAIL 시) 수정 방향 1~2문장

**중요: [Analyze]에서 찬반 양쪽을 반드시 나열하라.** 한쪽만 보고 판정하면 Self-consistency 위반이다.

---

## 8가지 검증 축

| # | 검증 축 | 확인 항목 | FAIL 기준 |
|---|--------|----------|----------|
| 1 | **앵커 일관성** | 모든 Stage(0~4)에 불변 앵커가 있고, PBL 문제·TARGET_CROP·팀 구성·기간·산출물이 Stage 간 일치하는가? | 앵커 누락, 또는 Stage 간 핵심 제약 불일치 (예: Stage 0은 "글로벌" Stage 1은 "국내") |
| 2 | **스키마 연속성** | Stage N의 output_schema 필드명 ↔ Stage N+1의 input 태그 내 참조 필드명이 정확히 대응하는가? JSON wrapper(stage, timestamp, cycle, micro_cycle, loop_count, payload)가 모든 Stage에서 유지되는가? | 필드명 불일치, payload 구조 단절, wrapper 필드 누락 |
| 3 | **기법 적용 타당성** | 각 Stage에 적용된 프롬프트 기법이 해당 Stage의 기능에 적합한가? 구체적으로: Stage 0에 CoT가 있는가(사고 경로 유도, 워크플로우 나열 아님)? Stage 1에 Pseudo-ReAct가 있는가? Stage 2에 판정 기준이 구조화되어 있는가? 하네스 전체에 Few-shot이 있는가? | 필수 기법 누락(특히 Few-shot — GPT용 프롬프트에서 치명적), 또는 기법 오용(설명을 CoT로 착각) |
| 4 | **조건부 게이트** | PASS/FAIL 분기 조건이 명확하고 모호하지 않은가? 루프백 경로가 구체적인가? 루프 가드(최대 반복 횟수)가 있는가? PASS_WITH_CAVEATS 전환 조건이 명시적인가? | 분기 조건 모호("적절하다고 판단되면"), 루프 가드 부재, 무한 루프 가능성 |
| 5 | **도메인 적합성** | Role 설정, source_hints, 검증 축이 "작물 유전체학 PBL"에 특화되어 있는가? 일반적인 에이전트 프롬프트를 그대로 가져다 쓴 흔적이 있는가? | Role이 도메인 무관한 일반 설정, source_hints에 도메인 특화 DB(NCBI, Ensembl Plants 등) 없음 |
| 6 | **실행 가능성** | 학부 3학년이 수동 copy-paste로 Stage 0→1→2→(루프백)→3→4를 실행할 수 있는가? 입력 자리 태그(`{{...}}`)가 명확한가? 실행 체크리스트가 있는가? | 입력 태그 누락, 실행 순서 모호, 붙여넣기 지점 불명확 |
| 7 | **과잉 프롬프팅** | Tier 0~1로 해결 가능한 부분에 Tier 3 기법을 과적용한 곳이 있는가? 불필요한 복잡성이 실행 부담을 높이는가? | 단순 포맷팅에 CoT+Role+Few-shot 동시 적용, 또는 프롬프트 길이가 실행 가능성을 위협 |
| 8 | **마이크로사이클 대응** | Stage 0이 CYCLE_CONTEXT와 마이크로사이클 유형(SURVEY/FRAMEWORK/EVALUATE/DEEP-DIVE/DESIGN/SYNTHESIS)을 인식하는가? Stage 4가 다음 MC용 컨텍스트를 패키징하는가? TARGET_CROP TBD↔CONFIRMED 분기가 작동하는가? | MC 인식 로직 누락, 패키징 구조 부재, TBD 분기 없음 |

---

## 축 간 연결 (Chaining 원칙)

검증 축을 독립적으로 평가하되, 아래 의존 관계를 반드시 반영하라:

- **축 2(스키마) → 축 6(실행 가능성):** 스키마가 단절되면 copy-paste 실행이 불가능하다. 축 2 FAIL이면 축 6도 재검토.
- **축 3(기법) → 축 7(과잉):** 기법이 누락된 곳과 과잉인 곳을 동시에 보라. 한쪽의 판정이 다른 쪽에 영향.
- **축 4(게이트) → 축 8(MC 대응):** 게이트 로직이 MC 전환과 맞물려야 한다. 루프백이 MC 경계를 넘는 경우가 있는지 확인.
- **축 1(앵커) → 전체:** 앵커가 FAIL이면 다른 모든 축의 "범위 준수" 근거가 약해진다.

---

## 판정 형식 (Few-shot 예시)

아래는 **다른 도메인**의 검증 예시이다. 출력의 구체성 수준과 형식을 이 예시와 맞춰라:

<example>
검증 대상: 고객 서비스 챗봇 프롬프트 체인 (3-Stage: 분류→응답→에스컬레이션)

=== 축 2: 스키마 연속성 ===

[Thought] Stage 1(분류) 출력의 `intent` 필드가 Stage 2(응답)에서 참조되는지 확인해야 한다.
[Search] Stage 1 output_schema: `{"intent": "refund|inquiry|complaint", "confidence": 0.0~1.0, "extracted_entities": [...]}`.
Stage 2 input: `<classification_result>를 받아 intent에 따라 응답 템플릿을 선택하라`.
[Observation] Stage 1은 `intent`를 출력하고 Stage 2는 `intent`를 참조한다. 그러나 Stage 2에 `confidence` 임계값 분기가 없다 — confidence가 0.3이어도 그대로 응답 생성으로 넘어간다.
[Analyze]
찬성: intent 필드명은 일치하고, extracted_entities도 Stage 2에서 참조 가능.
반대: confidence가 낮을 때의 처리가 없다. 실제 운영에서 오분류 → 잘못된 응답 → 에스컬레이션 누락 위험.
[Conclude]
**판정: FAIL**
근거: Stage 1 → Stage 2 사이에 confidence 기반 게이트가 없음. `confidence < 0.7`이면 Stage 3(에스컬레이션)으로 직행하는 분기를 추가해야 함.
수정 방향: Stage 2 입력부에 `if confidence < 0.7: skip to Stage 3` 조건 삽입.
</example>

---

## 종합 판정 기준

8개 축 판정 후, 아래 기준으로 종합 판정을 내려라:

- **PASS (전체 통과):** 8개 축 모두 PASS
- **CONDITIONAL PASS:** FAIL이 있으나 축 7(과잉) 또는 단독 경미한 문제 → 사용 가능하되 개선 권고
- **FAIL:** 핵심 축(1, 2, 4, 8) 중 하나 이상 FAIL → 수정 후 재검증 필요

종합 판정 후, **"Claude의 설계 편향이 가장 두드러진 지점" 1가지**를 반드시 지적하라.
이것은 Claude가 자기 검증으로는 발견하기 어려운, 외부 검증자만이 잡을 수 있는 맹점이어야 한다.

---

## 중간 정렬 체크

각 축 판정을 마칠 때마다, 1줄로 확인하라:
> "이 판정이 불변 앵커의 '구조적 완전성과 도메인 적합성' 검증에 직접 기여하는가?"

기여하지 않는 내용(예: 학술 내용의 정확성 평가, 하네스 대체안 제시)이 섞이면 즉시 제거하고 본론으로 복귀하라.

</instructions>

---

<output_schema>
```json
{
  "verification_target": "pbl-m1-harness-v1.1",
  "verifier_model": "GPT-5.4 Thinking",
  "timestamp": "ISO-8601",
  "axes": [
    {
      "axis_id": 1,
      "axis_name": "앵커 일관성",
      "verdict": "PASS | FAIL",
      "evidence": {
        "pro": ["PASS 근거 1", "PASS 근거 2"],
        "con": ["FAIL 근거 1"]
      },
      "cited_sections": ["Stage 0 앵커 L3-L12", "Stage 2 앵커 L1-L5"],
      "remediation": "FAIL 시 수정 방향 (PASS면 null)"
    }
  ],
  "cross_axis_notes": [
    "축 2 FAIL이 축 6에 미치는 영향: ...",
    "축 3과 축 7의 상충 지점: ..."
  ],
  "overall_verdict": "PASS | CONDITIONAL_PASS | FAIL",
  "overall_rationale": "종합 판정 근거 2~3문장",
  "claude_design_bias": {
    "observation": "Claude 설계 편향이 가장 두드러진 지점",
    "why_blind_spot": "왜 Claude 자기 검증으로는 발견 어려운지",
    "suggested_mitigation": "완화 방향 1~2문장"
  },
  "priority_fixes": [
    {
      "priority": 1,
      "axis": "축 번호",
      "issue": "핵심 문제 1줄",
      "fix_direction": "수정 방향 1~2문장"
    }
  ]
}
```
</output_schema>

---

<harness_to_verify>
{{pbl-m1-harness-v1.1.md 전체 내용을 여기에 붙여넣기}}
</harness_to_verify>

<original_pbl_problem>
국내 종자회사인 N사는 글로벌 종자기업과 경쟁할 수 있는 품종을 개발하기 위해 유전체 정보 활용 연구에 많은 지원을 하고 있다. 당신은 N사 생명공학연구소의 작물 유전체 연구실에서 근무하고 있는 연구원으로 육종소재의 전장유전체 염기서열 데이터를 생산하고 in silico 분석을 통해 유용한 생물정보 발굴 업무를 맡고 있다. 최근 국내외에서 수요가 증가하고 있는 작물의 표준유전체 연구 프로젝트를 5주 안에 기획하라는 임무가 당신 팀에게 주어졌다. 연구수행 전략을 구체적으로 설계하여 기획안을 작성하고 PPT 형태로 30분간 발표를 해야 한다.
</original_pbl_problem>

<verification_context>
이 하네스에 대해 이미 알려진 사항:
1. Claude(Opus 4.6)가 설계하고 자체 품질 체크리스트로 검증함 (하네스 말미 참조)
2. 수정사항 A~E가 적용된 버전:
   - (A) Stage 0에 불변 앵커 + 출처 규칙 삽입
   - (B) Stage 2에 게이트 조건 #4~#6 추가 (범위 준수, 완전성, 유전체 기술 타당성)
   - (C) Stage 0에 마이크로사이클 인식 앵커 추가
   - (D) 3-axis tag system 변환 (보류됨)
   - (E) Stage 2 검증 절차 구체화
3. "AI가 만든 검증 체계를 AI가 적용"하는 구조적 한계가 있으므로, 이 교차검증이 필요함
4. 프롬프트 엔지니어링 7가지 기법(Zero-shot+구조화, Few-shot, CoT, Role, Self-consistency, Chaining, ReAct)을 기준으로 하네스의 기법 적용 상태도 평가 필요
</verification_context>
```

## ---END PROMPT---

---

## 기법 적용 매핑

| 기법 | 적용 위치 | 설명 |
|------|----------|------|
| **불변 앵커** | 프롬프트 최상단 `🎯` 블록 | 검증 범위·제외·탈선 감지 명시 |
| **Role** | `<role>` 블록 | PE QA + 에이전트 아키텍트 이중 렌즈 + Claude 편향 의심 긴장 설정 |
| **Guided CoT** | 사고 프로토콜 5단계 루프 | `[Thought→Search→Observation→Analyze→Conclude]` |
| **Few-shot** | `<example>` 블록 | 다른 도메인(고객 서비스 챗봇)의 축 2 검증 예시로 구조 패턴 전이 |
| **Self-consistency** | `[Analyze]` 내 찬반 양쪽 필수 | 단일 관점 판정 방지 |
| **Chaining** | 축 간 연결 섹션 | 축 2→6, 축 3→7, 축 4→8, 축 1→전체 의존관계 명시 |
| **Pseudo-ReAct** | `[Search]` 단계 | 하네스 원문 직접 인용 필수 + 충분성 판단 루프 |

## 기존 부록 B 대비 변경점

| 항목 | 부록 B (기존) | 이 프롬프트 (개선) |
|------|-------------|-----------------|
| CoT | 8축 테이블만 (사고 루프 없음) | 5단계 Guided CoT 루프 전 축 적용 |
| Few-shot | 없음 | 다른 도메인 예시 1개 포함 |
| Self-consistency | 없음 | [Analyze]에 찬반 양쪽 필수 규칙 |
| ReAct | 없음 | [Search]에서 원문 인용 + 충분성 판단 |
| 축 간 연결 | 독립 판정 | 4개 의존관계 명시 |
| Claude 편향 탐지 | 없음 | 종합 판정에 `claude_design_bias` 필수 |
| 출력 스키마 | 단순 axes + verdict | 찬반 분리 evidence + cross_axis_notes + priority_fixes |
| 중간 정렬 체크 | 없음 | 각 축 판정 후 앵커 기여도 확인 |
| 수정사항 A~E 컨텍스트 | 없음 | `<verification_context>`로 배경 제공 |
