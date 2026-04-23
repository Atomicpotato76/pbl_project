# GPT 방법론 검증 프롬프트 — TPP 시나리오 분화 접근법

아래 `[여기부터 복사]` ~ `[여기까지 복사]` 구간을 GPT **새 세션**에 붙여넣기.
**같이 넣을 파일**: `crop_screening_revised.md` (v2) — 현재 AHP weight, score, 포트폴리오 전체 맥락.

---

## [여기부터 복사]

당신은 MCDA(Multi-Criteria Decision Analysis) 방법론 전문가이자, 종자산업 R&D 투자 의사결정에 경험이 있는 컨설턴트입니다.

저는 학부 PBL에서 종자회사 N사의 표준유전체(reference genome) 프로젝트 대상 작물 1개를 선정하고 있습니다. 현재 **AHP weight 확정 + 6개 후보 baseline scoring**까지 완료했고, 다음 단계로 넘어가기 전에 **접근법 자체의 타당성을 검증**받고 싶습니다.

---

# 1. 현재까지 완료된 것

## 1-1. 프로젝트 맥락
- **N사**: 한국 국내 대기업급 종자회사 (농우바이오·코레곤 수준)
- 자체 R&D(wet/dry lab + bioinformatics), 자체 seed system, 글로벌 유통망 보유
- **목표**: reference genome/pangenome 구축 → 육종 → 품종 출시 → 종자 사업화 (5~7년)
- **후보 6개**: 고추, 배추, 비둘기콩(pigeonpea), 시금치, 참깨, 들깨

## 1-2. 평가 구조
- **Hard Filter**(H-1~H-10): 치명적 결격 사유 veto → 통과한 작물만 남음
- **Soft Filter**: 5개 Dimension × AHP weight → FinalScore

## 1-3. 확정된 AHP Weight (대기업 관점, CR=0.0131)

| Dimension | 설명 | Weight |
|---|---|---|
| D1. Market & Revenue | 시장 성장성 + 수익 모델 | 0.3629 |
| D2. Genomic Opportunity | reference 공백 + tractability + downstream | 0.2193 |
| D3. Breeding & Delivery | breeding cycle + phenotyping + seed system + 채택 | 0.2193 |
| D4. Strategic Fit | 경쟁사 차별화 + 한국 germplasm + 국제협력 | 0.0921 |
| D5. Compliance & Governance | DSI/Nagoya + 기후 + FAIR data | 0.1065 |

## 1-4. 현재 Baseline Score (시나리오 분화 전)

| 작물 | D1 | D2 | D3 | D4 | D5 | Score | 비고 |
|---|---|---|---|---|---|---|---|
| 비둘기콩 | 2 | 2 | 2 | 1 | 1 | 90.08 | D3: 1→2 (대기업 delivery 내부화 가정) |
| 고추 | 2 | 1 | 2 | 2 | 2 | 89.05 | — |
| 배추 | 2 | 1 | 2 | 2 | 2 | 89.05 | — |
| 시금치 | 1 | 2 | 2 | 1 | 1 | 71.94 | — |
| 참깨 | 1 | 2 | 1 | 1 | 1 | 60.97 | D5: 2→1 |
| 들깨 | 1 | 1 | 2 | 1 | 1 | 60.97 | D4: 2→1 |

Score 공식: FinalScore = {Σ(D_weight × D_score) / 2} × 100

---

# 2. 문제 인식

위 baseline scoring에서 **D1~D5 점수가 "작물 자체의 속성"으로만 매겨져 있습니다.** 하지만 실제로는:

- **같은 비둘기콩**이라도 India hybrid F1 직접 판매 시나리오와, SSA ODA 연계 B2B2Farmer 시나리오에서는 D1(시장 규모), D3(delivery 방식), D5(규제 경로)가 전부 다릅니다.
- **같은 D3(Breeding & Delivery)**라도 "자체 seed system으로 직접 보급"이 기준인지, "ICRISAT/정부 파트너 경유"가 기준인지에 따라 점수가 달라야 합니다.
- **D1의 수익 모델 tier**(hybrid=2.0, licensing=1.5, service=1.0, public=0.5)도 시나리오에 종속됩니다.

이 문제는 체크리스트 §0 TPP(Target Product Profile)가 "crop × region × end-user"를 먼저 정의하도록 설계한 이유이기도 합니다.

---

# 3. 제안하는 접근법

## 워크플로우

```
① 작물별 TPP sketch (1~2개 시나리오)
   - 타겟 시장(region) × 수익 모델 × N사 역할 × 간략 end-user
         ↓
② N사에 최적인 시나리오 1개 선택
   - 선택 근거 1~2줄
         ↓
③ 선택된 시나리오 기준으로 D1~D5 재채점
   - D의 "정의"는 동일하지만, "무엇을 측정하는가"가 시나리오에 종속
         ↓
④ 확정 weight 적용 → FinalScore 재계산
         ↓
⑤ Sensitivity analysis
   - weight ±20%
   - 시나리오 전환 시 순위 변동
```

## 설계 원칙
- **AHP weight는 고정** (D1~D5 간 상대적 중요도는 "대기업이 genome 투자를 판단하는 기준"이므로 작물과 독립)
- **Score만 시나리오에 종속** (같은 D3이라도 "자체 delivery" vs "파트너 경유"로 기준 분화)
- **시나리오 1개 선택 방식** (가중평균이 아닌, N사 최적 시나리오 기준으로 scoring)
- **End-user는 경량화** — genome 선정 단계에서는 "이 genome이 어떤 end-user 시나리오를 열어주는가" 수준만 파악

## 참고 문헌
- CGIAR GloMIP: 700+ market segments → TPP → breeding investment 구조 (2022~2025)
- Cassava portfolio management (Frontiers, 2024): stage-gate + market segment 기반 포트폴리오 관리
- Rutsaert et al. (2026), Nature Communications: VACS 7개 opportunity crop의 market-guided prioritization
- Garner et al. (2024), Nature Plants: 657편 scoping review, 시장 segment별 분화 평가 부족 확인

---

# 4. 검증 요청

아래 4개 질문에 대해 각각 판정(✅ 타당 / ⚠️ 조건부 타당 / ❌ 재설계 필요)과 근거를 제시해주세요.

## Q1. 시나리오 종속 scoring의 방법론적 타당성

"D1~D5의 정의(criteria)는 동일하게 유지하되, 점수(score)를 작물별 시장 시나리오에 종속시킨다"는 접근이 AHP/MCDA 방법론적으로 유효합니까?

- 일반적으로 AHP는 criteria를 대안(alternative)과 독립적으로 정의합니다. 우리는 criteria 정의는 유지하되 score의 **해석 맥락**을 시나리오별로 분화시키는 것인데, 이것이 AHP의 전제를 위반하지는 않는지?
- 위반한다면, 어떻게 수정해야 하는지?

## Q2. Weight 고정 vs 시나리오별 가변

AHP weight를 모든 작물에 동일하게 적용하는 것이 맞습니까?

- 논리: "대기업이 genome 투자를 판단하는 기준의 상대적 중요도"는 작물과 무관
- 반론: B2B2Farmer 모델(비둘기콩)에서는 D3의 의미가 달라지므로 weight도 달라져야 하는 것 아닌가?
- 어느 쪽이 더 방어 가능한지, 그리고 그 이유

## Q3. 시나리오 1개 선택 vs 가중평균

한 작물에 시나리오가 2~3개 나올 때, "N사에 최적인 1개만 선택"하는 방식과 "시나리오별 Score를 실현 확률로 가중평균"하는 방식 중 어느 쪽이 더 적절합니까?

- PBL 5주 기획이라는 맥락
- 학술적 엄밀성 vs 실무적 판단 가능성
- 추천하는 방식과 그 근거

## Q4. End-user 경량화의 적절성

Reference genome 선정 단계에서 end-user 분석을 "이 genome이 어떤 시나리오를 열어주는가" 수준으로 경량화하는 것이 충분합니까?

- CGIAR TPP는 "crop × region × end-user"를 3축으로 정의하지만, 우리 프로젝트의 1차 산출물은 genome이지 품종이 아님
- 품종 단계의 end-user 분석을 genome 선정에 끌어오는 것이 과도한지, 아니면 필수적인지
- 경량화가 적절하다면 어떤 수준까지, 부적절하다면 무엇을 추가해야 하는지

---

# 5. 출력 형식

```
=== Q1 ===
[판정: ✅/⚠️/❌]
[근거 3~5줄]
[수정 필요 시 구체적 제안]

=== Q2 ===
[판정]
[근거]
[제안]

=== Q3 ===
[판정]
[추천 방식 + 근거]

=== Q4 ===
[판정]
[근거]
[경량화 수준 제안]

=== 종합 ===
[4개 답변을 종합한 최종 권고 — 워크플로우 수정이 필요하면 수정안 제시]
```

## [여기까지 복사]

---

# GPT 답변을 받은 후

GPT 답변을 레나한테 보여주면:
1. Q1~Q4 판정이 우리 설계와 충돌하는지 확인
2. 워크플로우 수정이 필요하면 반영
3. 확정된 워크플로우로 6개 작물 TPP sketch 시작
