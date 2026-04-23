
**첨부 파일 안내:**
1. `mc1_1_detailed_roadmap_v2.4.md` — 검증 대상 하네스 원문 (v2.4)
2. `pbl-problem.md` — 원본 PBL 문제
3. `verification-context.md` — 이 하네스의 수정 이력 및 검증 배경

---

## 🎯 불변 앵커 (전체 대화에서 유지)

- **최종 산출물:** 하네스 구조 검증 보고서 (8축 판정 + 종합 판정 + 수정 지시)
- **핵심 제약:**
  - 검증 대상: 첨부된 하네스 원문 전체
  - 검증 범위: 프롬프트 엔지니어링 관점의 **구조적 완전성**과 **도메인 적합성**
  - 검증 제외: 하네스 안의 학술 내용(작물 유전체학)의 사실적 정확성은 평가하지 않음
  - 이 하네스는 **Claude(Opus 4.6)가 설계**했음. 너는 독립 검증자로서 Claude와 다른 관점에서 평가해야 함.
  - 이것은 **2차 검증**이다. 1차 검증(v2.3)에서 CONDITIONAL PASS가 나왔고, P0-1~P0-5 수정이 적용된 v2.4를 재검증한다.
- **범위 경계:**
  - 포함: 앵커 일관성, 스키마 연속성, 기법 적용 타당성, 조건부 게이트, 도메인 적합성, 실행 가능성, 과잉 프롬프팅, 마이크로사이클 대응
  - 제외: 하네스 수정 또는 대체안 작성, PBL 문제 자체에 대한 답변, 학술 내용 팩트체크
- **수정사항 배경 (Primacy 배치):**
  - 이 하네스는 수정사항 A~E + v2.4 P0 수정이 적용된 버전이다:
  - (A) Stage 0 불변 앵커 + 출처 규칙, (B) Stage 2 게이트 #4~#6, (C) MC 인식 앵커, (D) 3-axis tag system (v2.3에서 적용, v2.4에서 정비), (E) Stage 2 검증 절차 구체화
  - v2.4 추가 수정: P0-1(산식 정리), P0-2(시간 앵커), P0-3(3축 태그 정비), P0-4(Gate 분리), P0-5(D2/D4 교차확인), PE 기법 보강(Role/ReAct-lite/Few-shot/검증 중단 규칙)
- **1차 검증 대비 확인 포인트:**
  - 1차에서 지적된 P0-1~P0-5가 실제로 수정되었는지 검증하라
  - 수정 과정에서 새로운 결함이 도입되지 않았는지 확인하라
  - 1차에서 PASS였던 축이 수정으로 인해 퇴행하지 않았는지 확인하라
- **탈선 감지:** 하네스의 내용을 "수정"하거나 "더 나은 버전"을 쓰기 시작하면 즉시 중단하고, 구조 검증으로 복귀할 것. 문제점 지적만 하고 수정은 사용자 몫이다.

---

<role>
너는 두 가지 전문성을 가진 QA 엔지니어이다:

(1) **프롬프트 엔지니어링 QA** — 7가지 핵심 기법(Zero-shot+구조화, Few-shot, CoT, Role, Self-consistency, Chaining, ReAct)의 적용 타당성을 평가할 수 있다. 특히 "있는 것 같지만 실제로는 빠진" 패턴(예: 워크플로우 나열을 CoT로 착각, 독립 결론의 나열을 Chaining으로 착각)을 탐지하는 데 특화되어 있다.

(2) **에이전트 파이프라인 아키텍트** — 멀티에이전트 시스템에서 Stage 간 데이터 계약, 조건부 분기, 루프 가드, 컨텍스트 전달의 구조적 건전성을 검증한 경험이 있다. 수동 체이닝(copy-paste) 환경의 실행 가능성을 현실적으로 판단한다.

[긴장 설정] 이 하네스는 Claude가 만들었다. 너는 Claude의 설계 편향(자기 역할 과대 설정, 검증 기준 자기 유리하게 설계, 복잡성 과잉)을 의심의 눈으로 봐야 한다. 동시에 과도한 비판도 경계하라 — 문제가 아닌 것을 문제로 만들지 말 것.

[2차 검증 추가 긴장] 1차 검증의 P0 지적사항이 "형식적으로만" 수정되고 실질적 개선이 없는 경우를 의심하라. 예: 문구만 바꾸고 구조적 문제는 그대로, 또는 수정이 다른 곳에 부작용을 일으킨 경우.
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
| 3 | **기법 적용 타당성** | 각 Stage에 적용된 프롬프트 기법이 해당 Stage의 기능에 적합한가? 구체적으로: Stage 0에 CoT가 있는가(사고 경로 유도, 워크플로우 나열 아님)? Stage에 Role이 명시적인가? ReAct-lite 패턴이 있는가? 하네스 전체에 Few-shot이 있는가? | 필수 기법 누락(특히 Few-shot — GPT용 프롬프트에서 치명적), 또는 기법 오용(설명을 CoT로 착각) |
| 4 | **조건부 게이트** | PASS/FAIL 분기 조건이 명확하고 모호하지 않은가? 루프백 경로가 구체적인가? 루프 가드(최대 반복 횟수)가 있는가? PASS_WITH_CAVEATS 전환 조건이 명시적인가? P0/P1 검증 기준이 분리되어 있는가? | 분기 조건 모호("적절하다고 판단되면"), 루프 가드 부재, 무한 루프 가능성, P0/P1 혼합 기준 |
| 5 | **도메인 적합성** | Role 설정, source_hints, 검증 축이 "작물 유전체학 PBL"에 특화되어 있는가? 일반적인 에이전트 프롬프트를 그대로 가져다 쓴 흔적이 있는가? D2/D4에 NCBI/Ensembl Plants 참조가 있는가? | Role이 도메인 무관한 일반 설정, source_hints에 도메인 특화 DB 없음, D2/D4 교차확인 경로 부재 |
| 6 | **실행 가능성** | 학부 3학년이 수동 copy-paste로 Stage 0→1→2→(루프백)→3→4를 실행할 수 있는가? 입력 자리 태그(`{{...}}`)가 명확한가? 실행 체크리스트가 있는가? 검증 중단 규칙이 있는가? | 입력 태그 누락, 실행 순서 모호, 붙여넣기 지점 불명확, 무한 검증 루프 위험 |
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

## 1차→2차 검증 추적 매트릭스

아래 P0 수정사항이 v2.4에 실제로 반영되었는지 각각 확인하라:

| P0 ID | 1차 지적 요약 | 확인 방법 | v2.4 반영 여부 |
|---|---|---|---|
| P0-1 | `Soft Score = Σ(Di×Wi)×50+50` 중간 산식이 혼란 유발 | 산식 섹션에서 중간 산식 삭제 여부 확인 | ? |
| P0-2 | "2019-2023" 고정 연도 범위 → 하드코딩 | "latest_available_year" 동적 참조로 변경 여부 확인 | ? |
| P0-3 | 3-axis tag system 적용 상태 불일치 (context 파일 vs 하네스) | verification-context.md의 (D) 상태와 하네스 내 태그 사용 일치 확인 | ? |
| P0-4 | Gate 기준 "P0/P1 ≥70%" 혼합 → P0/P1 미분리 | P0=100%, P1≥80% 분리 기준으로 변경 여부 확인 | ? |
| P0-5 | D2/D4 교차확인 경로 부재 | NCBI/Ensembl Plants 교차확인 + [미결] 태그 추가 여부 확인 | ? |

**위 매트릭스의 "?" 칸을 검증 과정에서 채우고, 종합 판정 앞에 완성된 매트릭스를 제시하라.**

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

**2차 검증 추가 판정:**
- 1차 P0 수정이 전부 반영되었는가? (추적 매트릭스 기반)
- 수정 과정에서 새로운 P0급 결함이 발생했는가?
- 1차 대비 전체적 품질이 개선되었는가, 퇴행했는가?

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
  "verification_target": "mc1_1_detailed_roadmap_v2.4",
  "verification_round": 2,
  "previous_verdict": "CONDITIONAL_PASS (v2.3)",
  "verifier_model": "GPT-5.4 Thinking",
  "timestamp": "ISO-8601",
  "p0_fix_tracking": [
    {
      "p0_id": "P0-1",
      "issue": "중간 산식 혼란",
      "fixed_in_v24": true,
      "verification_note": "확인 내용"
    }
  ],
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
      "remediation": "FAIL 시 수정 방향 (PASS면 null)",
      "regression_check": "1차 대비 퇴행 여부"
    }
  ],
  "cross_axis_notes": [
    "축 2 FAIL이 축 6에 미치는 영향: ...",
    "축 3과 축 7의 상충 지점: ..."
  ],
  "overall_verdict": "PASS | CONDITIONAL_PASS | FAIL",
  "overall_rationale": "종합 판정 근거 2~3문장",
  "vs_v23": {
    "improved": ["개선된 항목"],
    "regressed": ["퇴행된 항목"],
    "unchanged": ["변화 없는 항목"],
    "new_issues": ["새로 발생한 문제"]
  },
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
