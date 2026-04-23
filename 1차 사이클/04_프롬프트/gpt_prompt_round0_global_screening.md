# GPT 프롬프트 — Round 0: 전체 작물 스크리닝
## Rev 3.2 기반 · 콩과 제한 해제 · ISF 분류 전체 대상

아래 전체를 GPT에 복붙해서 사용.

---

```
당신은 식물 유전체학·종자산업·작물 육종 전문가다. 아래 상황과 프레임워크를 읽고 체계적으로 작물 후보를 스크리닝해라.

## 상황

국내 종자회사 N사는 글로벌 종자기업과 경쟁할 수 있는 품종을 개발하기 위해, "최근 국내외에서 수요가 증가하고 있는 작물"의 표준유전체(reference genome / pangenome) 연구 프로젝트를 기획하려 한다. 5주 안에 기획안을 완성해야 하며, 최종 PPT 발표(30분)를 한다.

### N사 프로필 (가정)
- 한국 중견 종자회사, 국내 채소·일부 field crop에 기반
- 자체 육종 파이프라인 보유 (wet lab + dry lab)
- 글로벌 진출 의지 있으나 Bayer/Corteva/Syngenta 대비 규모 열세
- 한국 농진청(RDA) 유전자원 + Golden Seed Project + KOPIA/ODA 연계 가능
- CGIAR와 직접 경쟁하기보다 B2B2Farmer(genomic platform provider) 모델 지향 가능

### 핵심 제약
- "콩과 작물이어야 한다"는 제한은 **없다** — 전체 작물 대상 스크리닝
- 영양번식 작물(cassava, potato, banana 등)은 종자회사 사업 모델에 구조적으로 부합하지 않으므로 **기본 제외** (단, TPS 등 예외 경로가 있으면 별도 언급)

---

## 스크리닝 프레임워크 (Rev 3.2 체크리스트 기반)

### ISF 작물 분류 (대상 범위)
모든 후보는 아래 ISF 공식 crop-specific groups 중 하나에 속해야 한다:
1. **Vegetables & Ornamentals** — hybrid F1 비중 높음, 수익 모델 유리
2. **Field Crops** — 곡류·콩과·유지·섬유 등, 작물 간 수익 구조 편차 큼
3. **Sugar Beet** — 특수 시장
4. **Forage and Turf** — 유전체 공백 + 수요 증가 후보 가능
5. **Tree and Shrub** — 장기 ROI, 대부분 제외하되 예외 가능

### Hard Filter (H-1 ~ H-10)
아래 중 **하나라도 N이면 탈락**. 각 후보에 대해 Y/B/N 판정을 내려라.

| # | 탈락 조건 | 판정 기준 |
|---|---|---|
| H-1 | 수요 증가 근거 부재 | 최근 5년 재배면적/소비량 비감소 추세 확인 불가 + 정책·영양안보 수요 부재 |
| H-2 | germplasm 접근 불명확 | ABS 적법 경로 부재 |
| H-3 | 기술 난도 과도 | genome ≥6Gb, ploidy ≥6x, het >2%, assembly workflow 부재 중 2개+ 동시 + 완화 수단 없음 |
| H-4 | Phenotyping 체계 부재 | 핵심 형질 ≥3개에 standard protocol 없음 OR MET 1년 내 불가 |
| H-5 | 상업 seed 보급 구조 취약 | farmer-saved seed 주도 + formal/intermediate 채널 부재 + 전환 경로 없음 |
| H-6 | 농가 채택 가능성 낮음 | benchmark 대비 명시적 개선 목표 제시 불가 + trait-to-market path 부재 (공공가치 예외 시 B) |
| H-7 | 5주 기획 불가 | 기초 문헌·germplasm·파트너 동시 결여 |
| H-8 | TPP 정의 불가 | SPMS·must-have traits·TPE 중 하나 이상 미설정 |
| H-9 | DSI 규제 리스크 | Cali Fund + bilateral ABS 경로 모두 미확보 |
| H-10 | 수익 모델 구조적 불가 | hybrid/licensing/service/public-blended 중 어느 경로도 불가 |

### 수익 모델 계층 (§6-A)
| Tier | 모델 | 연간 수익 지속성 |
|---|---|---|
| Tier 1 | Hybrid F1 seed (매년 재구매) | ★★★ |
| Tier 2 | Variety/trait/parental-line licensing | ★★☆ |
| Tier 3 | Genomic service/platform (B2B) | ★★☆ |
| Tier 4 | Public/blended revenue (ODA/consortium) | ★☆☆ |

### Soft Filter — 5 Dimension (순위화용)
| Dimension | Weight | 핵심 평가 포인트 |
|---|---|---|
| D1. Market & Revenue | 0.30 | 시장 성장성 + 수익 모델 tier + 상업 종자시장 규모 |
| D2. Genomic Opportunity | 0.25 | reference 공백 + genome tractability + downstream 확장성 |
| D3. Breeding & Delivery | 0.20 | breeding cycle + phenotyping + seed system + 채택 가능성 |
| D4. Strategic Fit | 0.15 | N사 차별화 + 한국 germplasm + 경쟁 회피 |
| D5. Compliance & Governance | 0.10 | 규제·DSI·기후적합·FAIR |

---

## 요청 사항

### Task 1: Longlist 생성 (15~20개)
ISF 5개 분류에서 **"수요 증가 + 유전체 공백 + 종자회사 수익 가능"** 교집합에 해당하는 작물 15~20개를 선별해라. 각 작물에 대해 아래 정보를 1~2줄로 제시:
- ISF 분류
- 수요 증가 근거 (1줄)
- 유전체 현황 (reference 유무, pangenome 유무, 주요 공백)
- 수익 모델 tier (1~4)
- N사 차별화 가능성 (1줄)

### Task 2: Hard Filter 적용 → Shortlist (7~10개)
Longlist 각 작물에 H-1~H-10을 적용해라. Y/B/N 판정 표를 작성하고, **N이 0개인 작물만** shortlist로 남겨라. B가 있는 작물은 별도 "Borderline" 목록에 둬라.

### Task 3: Shortlist Soft Scoring
Shortlist 작물에 대해 D1~D5 각각 0/1/2 점수를 매기고, 종합 score를 계산해라.
공식: FinalScore = {Σ(D_weight × D_score) / 2} × 100

### Task 4: Top 5 추천 + 포트폴리오 배치
종합 score 상위 5개 작물을 추천하고, 각각을 아래 tier에 배치해라:
- **Tier 1 (Flagship)** — 수요 확실, 단기 회수
- **Tier 2 (Platform)** — 중장기 유전체 플랫폼 가치
- **Tier 3 (High-risk/High-return)** — orphan/underutilized

각 Top 5 작물에 대해 다음을 2~3줄로 서술:
1. 왜 이 작물인가 (핵심 논거)
2. N사가 잡을 수 있는 포지션
3. 가장 큰 리스크 1개

### Task 5: 한국 특화 후보 별도 분석
위 스크리닝과 별개로, **한국 germplasm/역량이 글로벌 차별화로 연결될 수 있는 작물**을 2~3개 추가로 제시해라. (예: 들깨, 배추, 고추 등) 이 작물들이 Top 5에 포함되지 않더라도 별도로 분석해라.

---

## 출력 포맷

1. **Longlist 표** (15~20개)
2. **Hard Filter 판정 표** (Y/B/N matrix)
3. **Shortlist Soft Score 표** (D1~D5 + 종합)
4. **Top 5 추천 + 포트폴리오 배치**
5. **한국 특화 후보 분석**

각 표 아래에 핵심 판단 근거를 짧게 달아라. 불확실한 정보는 "미확인" 표기하고 확인이 필요한 사항은 별도로 모아라.
```

---

*프롬프트 버전: v1.0 · 2026-04-18 · Rev 3.2 체크리스트 기반*
