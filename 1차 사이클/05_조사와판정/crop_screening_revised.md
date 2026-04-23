# Crop Screening Result — Revised (v3: TPP 시나리오 분화 반영)

> **변경 이력**
> - v1 (2026-04-18): 초기 교차검증 반영 — 녹두 D2 하향, 오크라 Borderline, 들깨 편입, 비둘기콩 Tier 재배치
> - v2 (2026-04-19): N사 규모 "대기업급" 확정 → AHP pairwise comparison 실시 → weight·score·순위 재산정
> - v3 (2026-04-19): TPP 시나리오 분화 — 작물별 최적 시나리오 선정 → 시나리오 종속 D점수 재산정 → 시금치·들깨 순위 변동

---

## 1. N사 규모 설정 변경 (v2 핵심)

PBL 원문은 "국내 종자회사 N사"로만 기술. v1에서는 중소~중견으로 가정했으나, 프로젝트 맥락(글로벌 종자기업과 직접 경쟁, 자체 R&D·seed system 보유)을 재검토한 결과 **국내 대기업급(농우바이오·코레곤 수준)**으로 확정했다 (2026-04-19).

### 대기업이라서 달라지는 점
1. **D1(시장 규모)** 중요도 상승 — 니치보다 글로벌 TAM이 큰 작물 선호
2. **D3(자체 delivery)** 중요도 상승 — 파트너 의존이 아니라 자체 seed system 운영
3. **D4(전략적 니치)** 중요도 하락 — 대기업은 기술력·규모로 직접 경쟁 가능
4. **D5(compliance)** 소폭 상승 — EU CS3D, ESG 공시, Cali Fund 등 규제 노출 증가

---

## 2. Hard Filter Y/B/N Matrix (변경 없음)

| 작물 | H1 | H2 | H3 | H4 | H5 | H6 | H7 | H8 | H9 | H10 | 결과 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 고추 | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Shortlist |
| 배추 | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Shortlist |
| 시금치 | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Shortlist |
| 오크라 | Y | B | Y | B | Y | B | Y | Y | B | Y | Borderline |
| 병아리콩 | Y | Y | Y | Y | B | Y | Y | Y | Y | Y | Borderline |
| 렌틸 | Y | Y | Y | Y | B | B | Y | Y | Y | Y | Borderline |
| 강낭콩 | Y | Y | Y | Y | B | Y | Y | Y | Y | Y | Borderline |
| 동부(cowpea) | Y | Y | Y | Y | B | B | Y | Y | Y | Y | Borderline |
| 녹두 | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Shortlist |
| 비둘기콩 | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Shortlist |
| 참깨 | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Shortlist |
| 퀴노아 | Y | B | Y | Y | B | B | Y | Y | B | Y | Borderline |
| 테프 | Y | B | Y | B | B | B | Y | Y | B | Y | Borderline |
| 곡립 아마란스 | Y | B | Y | B | N | B | Y | Y | B | B | Drop |
| 알팔파 | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Shortlist |
| 퍼레니얼 라이그라스 | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Shortlist |
| 이탈리안 라이그라스 | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Shortlist |
| 화이트클로버 | Y | Y | Y | B | Y | B | Y | Y | Y | Y | Borderline |
| 들깨(Perilla) | Y | Y | Y | Y | Y | Y | Y | Y | Y | Y | Shortlist |

---

## 3. AHP Pairwise Comparison 결과

### 3-1. 검증 경로

| 단계 | 수행자 | 내용 |
|---|---|---|
| 1차 | GPT (새 세션) | 대기업 관점 10쌍 pairwise + Soft Score 재검토 |
| 2차 | Claude (Python) | eigenvalue + geometric mean + CR 독립 재계산 |
| 결과 | — | GPT-Python 소수점 4자리 일치, CR 일치 |

### 3-2. 10쌍 Pairwise Comparison (대기업 관점)

| # | 비교 쌍 | 우세 | 강도 | 이전(중소) | 변화 근거 |
|---|---|---|---|---|---|
| 1 | D1 vs D2 | D1 | 2 | 동등(1) | 대기업은 TAM 우선. CGIAR market-led 전환과 정합 |
| 2 | D1 vs D3 | D1 | 2 | D1(2) | 강도 유지. D3 상승했지만 D1이 여전히 상위조건 |
| 3 | D1 vs D4 | D1 | 3 | D1(2) | 니치 < 시장 규모. 대기업 전환의 상징적 비교 |
| 4 | D1 vs D5 | D1 | 3 | D1(3) | 유지. Cali Fund/CSDDD로 D5 올랐지만 D1이 여전히 1차 driver |
| 5 | D2 vs D3 | 동등 | 1 | 동등(1) | genomics platform + delivery platform 동시 필요 |
| 6 | D2 vs D4 | D2 | 3 | D2(2) | 기술 플랫폼성(pangenome/GS/editing)이 니치보다 중요 |
| 7 | D2 vs D5 | D2 | 2 | D2(3) | D5 상승으로 격차 축소. 강도 3→2 |
| 8 | D3 vs D4 | D3 | 3 | 동등(1) | **구조적 최대 변화**. 자체 seed system이 핵심 자산 |
| 9 | D3 vs D5 | D3 | 2 | D3(2) | 유지. delivery 없으면 상업화 불가 |
| 10 | D4 vs D5 | 동등 | 1 | D4(2) | D4 하락 + D5 상승으로 수렴 |

### 3-3. Pairwise Matrix

|  | D1 | D2 | D3 | D4 | D5 |
|---|---|---|---|---|---|
| **D1** | 1 | 2 | 2 | 3 | 3 |
| **D2** | 1/2 | 1 | 1 | 3 | 2 |
| **D3** | 1/2 | 1 | 1 | 3 | 2 |
| **D4** | 1/3 | 1/3 | 1/3 | 1 | 1 |
| **D5** | 1/3 | 1/2 | 1/2 | 1 | 1 |

### 3-4. Weight 산출 (Eigenvalue Method, Python 검증)

| Dimension | Pilot weight | 이전(중소) | **대기업 (확정)** | 중소→대기업 |
|---|---|---|---|---|
| **D1** Market & Revenue | 0.3000 | 0.3013 | **0.3629** | +0.062 ↑ |
| **D2** Genomic Opportunity | 0.2500 | 0.2646 | **0.2193** | -0.045 ↓ |
| **D3** Breeding & Delivery | 0.2000 | 0.1856 | **0.2193** | +0.034 ↑ |
| **D4** Strategic Fit | 0.1500 | 0.1595 | **0.0921** | -0.067 ↓ |
| **D5** Compliance & Governance | 0.1000 | 0.0891 | **0.1065** | +0.017 ↑ |

**Weight 구조**: D1(0.363) > D2(0.219) = D3(0.219) > D5(0.107) > D4(0.092)

### 3-5. Consistency Check

| 지표 | 값 | 판정 |
|---|---|---|
| λ_max | 5.0586 | — |
| CI | 0.0147 | — |
| RI (n=5) | 1.12 | Saaty |
| **CR** | **0.0131** | **< 0.10 ✅ 통과** |

Geometric Mean 교차검증: 모든 weight ±0.002 이내 수렴.

---

## 4. Soft Score 재평가 (대기업 관점)

### 4-1. Score 변경 셀 (3개)

| 작물 | Dim | 이전 | **변경** | 근거 |
|---|---|---|---|---|
| 비둘기콩 | D3 | 1 | **2** | ICRISAT hybrid pigeonpea 상업화 진행 중. 대기업이면 India 파트너 + 자체 seed system으로 delivery bottleneck 내부화 가능 |
| 참깨 | D5 | 2 | **1** | FAO ITPGRFA Annex I에 sesame 미포함. 대기업은 DSI/Cali Fund compliance 노출이 커서 ABS 경로 불확실성이 리스크 |
| 들깨 | D4 | 2 | **1** | "한국 독점 니치"는 SME에겐 강점이나 대기업에겐 scale limitation. 글로벌 TAM 부재 |

### 4-2. 검토했으나 유지한 셀

| 작물 | Dim | 유지 | 이유 |
|---|---|---|---|
| 비둘기콩 | D4 | 1 | India/ICRISAT 생태계가 이미 두터워 Korean germplasm leverage 약함 |
| 참깨 | D3 | 1 | self-pollinated crop, hybrid 경제성이 pepper/cabbage만큼 강하지 않음 |
| 고추·배추 | D4 | 2 | 글로벌 hybrid 시장에서 대기업이 경쟁하기에 적합. 상향 여지 없음 |

### 4-3. 최종 Soft Score (대기업 weight 적용)

**FinalScore = {Σ(D_weight × D_score) / 2} × 100**

| 순위 | 작물 | D1 | D2 | D3 | D4 | D5 | FinalScore | 판정 | 이전 순위 |
|---:|---|---:|---:|---:|---:|---:|---:|---|---|
| **1** | **비둘기콩** | 2 | 2 | **2** | 1 | 1 | **90.08** | Go | 3위(77.5) |
| **2** | **고추** | 2 | 1 | 2 | 2 | 2 | **89.05** | Go | 1위(87.5) |
| **2** | **배추** | 2 | 1 | 2 | 2 | 2 | **89.05** | Go | 1위(87.5) |
| 4 | 시금치 | 1 | 2 | 2 | 1 | 1 | 71.94 | Conditional Go | 4위(72.5) |
| 5 | 참깨 | 1 | 2 | 1 | 1 | **1** | 60.97 | Conditional Go | 5위(67.5) |
| 5 | 들깨 | 1 | 1 | 2 | **1** | 1 | 60.97 | Conditional Go | 5위(67.5) |

---

## 5. 순위 변동 원인 분석

### 5-1. 변동 분리: Weight 효과 vs Score 효과

> **방법**: (A) 이전 weight+이전 score → (B) 대기업 weight+이전 score → (C) 대기업 weight+대기업 score. Weight 효과 = B-A, Score 효과 = C-B.

| 작물 | 이전 | 최종 | 총변동 | Weight 효과 | Score 효과 | 주요 원인 |
|---|---:|---:|---:|---:|---:|---|
| **비둘기콩** | 78.30 | 90.08 | **+11.78** | +0.82 | **+10.97** | D3 상향(1→2)이 결정타 |
| 고추 | 86.78 | 89.05 | +2.27 | +2.27 | 0.00 | 순수 weight 효과(D1↑) |
| 배추 | 86.78 | 89.05 | +2.27 | +2.27 | 0.00 | 순수 weight 효과(D1↑) |
| 시금치 | 72.52 | 71.94 | -0.58 | -0.58 | 0.00 | 순수 weight 효과(D4↓) |
| 참깨 | 67.69 | 60.97 | **-6.72** | -1.39 | **-5.33** | D5 하향(2→1)이 주원인 |
| 들깨 | 67.26 | 60.97 | **-6.29** | -1.69 | **-4.60** | D4 하향(2→1)이 주원인 |

> **참고**: "이전" score는 이전(중소) weight로 계산한 값(pilot weight 87.5/77.5/72.5/67.5와 소수점 차이 존재 — pilot weight가 근사값이었기 때문).

### 5-2. 핵심 해석

**비둘기콩 1위 상승**: weight만 바꿨을 때는 여전히 3위(79.12). 1위로 올라간 결정타는 D3 score 상향(1→2)이며, 이는 "대기업이면 India seed system 병목을 내부화할 수 있다"는 **기업 속성 변화**에 기인한다.

**고추·배추 소폭 상승**: score 변경 없이 D1 weight 상승(0.301→0.363) 효과만으로 +2.27. 두 작물 모두 D1=2이므로 D1 비중 확대의 수혜.

**참깨·들깨 하락**: 둘 다 score 하향이 weight 변화보다 3~4배 큰 영향. 참깨는 enterprise-scale compliance 리스크(D5↓), 들깨는 니치 한계(D4↓).

---

## 6. Revised Portfolio Placement (v2)

| Tier | 작물 | Score | 핵심 논거 |
|---|---|---:|---|
| **Flagship** | 비둘기콩 | 90.08 | CMS hybrid + India/SSA 거대 시장 + pangenome 공백 + 대기업 delivery 내부화 |
| **Flagship** | 고추 | 89.05 | hybrid F1 + 한국 pungency germplasm + 글로벌 수요 |
| **Flagship** | 배추 | 89.05 | hybrid F1 + 김치 value chain + 한국 pangenome 공백 |
| Platform | 시금치 | 71.94 | NLR 공백 + hybrid 채소 + 병저항성 |
| Platform | 참깨 | 60.97 | VACS 작물 + health oil 수요 + genomic 공백 |
| Korea Special | 들깨 | 60.97 | 한국 germplasm 독보적 + pangenome 부재 |

### v1→v2 변경 요약
- **비둘기콩**: Platform(3위, 77.5) → **Flagship(1위, 90.08)** — 대기업 delivery 역량 반영
- **고추·배추**: Flagship 유지, 점수 소폭 상승(87.5→89.05)
- **참깨**: Platform 유지, 점수 하락(67.5→60.97) — compliance 리스크
- **들깨**: Korea Special 유지, 점수 하락(67.5→60.97) — 니치 한계

---

## 7. TPP 시나리오 분화 (v3 신설)

### 7-0. 방법론

GPT 방법론 검증(Q1~Q4)을 거쳐 확정한 워크플로우:

1. **Alternative 재정의**: "작물" → "작물 × canonical scenario" (GPT Q1 권고)
2. **시나리오별 6-item TPP minimum**: region, primary buyer, value proposition, must-win traits 2~4, delivery path, governance issue (GPT Q4 권고)
3. **N사 최적 시나리오 1개 선택** + sensitivity에서 시나리오 전환 검증 (GPT Q3 권고)
4. **Weight 고정**: D1~D5 weight는 "대기업이 genome 투자를 판단하는 기준"이므로 작물·시나리오와 독립 (GPT Q2 확인)
5. **Score만 시나리오에 종속**: 같은 D 정의 내에서 "무엇을 측정하는가"를 시나리오 맥락에 맞춰 분화

참고: CGIAR GloMIP (2022~2025), Rutsaert et al. (2026 Nature Communications), Garner et al. (2024 Nature Plants), Cassava portfolio management (Frontiers 2024)

### 7-1. 비둘기콩 — PP-A: India Hybrid F1 Direct Sales ✅ (선택)

| 항목 | 내용 |
|---|---|
| **Region** | India (Maharashtra, Karnataka, Telangana, MP) — 4.9M ha, 글로벌 생산 90% |
| **Primary Buyer** | Indian smallholder farmers (1–5 ha) via dealer network + state seed corporations |
| **Value Proposition** | CMS-based hybrid F1 (30–40% yield advantage). N사 proprietary CMS lines + hybrid seed production system |
| **Must-Win Traits** | ① CMS hybrid vigor ≥30% ② Fusarium wilt (FW) resistance ③ Sterility mosaic disease (SMD) resistance ④ Short-to-medium duration (150–180 d) |
| **Delivery Path** | N사 Indian subsidiary → ICRISAT germplasm access → A×R hybrid seed production → state seed corps + private dealers |
| **Governance** | ITPGRFA Annex I 미포함. India Biological Diversity Act 2002. Nagoya 비준. DSI: Cali Fund 의무 가능 |
| **Revenue Model** | Hybrid F1 (tier 2.0) — seed price premium + annual repurchase |

> **기각 시나리오**: PP-B (SSA ODA-linked B2B2Farmer) — 수익 모델 불확실(ODA 의존), 다국가 규제 복잡, N사 직접 delivery 불가

### 7-2. 고추 — PE-A: Global Hybrid F1 Hot Pepper ✅ (선택)

| 항목 | 내용 |
|---|---|
| **Region** | Global — India, China, SE Asia, Latin America, Korea. Capsicum seed market USD 31.3B (2024) |
| **Primary Buyer** | Commercial farmers (fresh + processing) via N사 global dealer network (70+ countries) |
| **Value Proposition** | Korean pungency germplasm (capsaicinoid QTL) + virus resistance package. N사 기존 breeding + 글로벌 유통 |
| **Must-Win Traits** | ① Capsaicinoid content stability ② TMV/CMV/TSWV resistance complex ③ Phytophthora blight resistance ④ Fruit uniformity + shelf life |
| **Delivery Path** | N사 breeding stations (Korea, India, Indonesia, Turkey) → hybrid seed production → 70+ country dealer network. 기존 인프라 |
| **Governance** | Korean 자체 germplasm → ABS 리스크 최소. DSI: 자체 데이터 중심 |
| **Revenue Model** | Hybrid F1 (tier 2.0) — established premium market |

### 7-3. 배추 — CC-A: Korean Kimchi Premium + Asian Fresh Market ✅ (선택)

| 항목 | 내용 |
|---|---|
| **Region** | Korea (kimchi industry ~USD 4B) + East/SE Asia fresh market |
| **Primary Buyer** | Korean kimchi processors (industrial) + Asian fresh vegetable distributors |
| **Value Proposition** | Kimchi-optimized cultivars (texture, fermentation quality) + clubroot/TuMV resistance |
| **Must-Win Traits** | ① Clubroot resistance (multi-pathotype) ② TuMV resistance ③ Kimchi fermentation quality ④ Heat tolerance |
| **Delivery Path** | N사 Korea HQ breeding → hybrid seed production → 국내 직접 + Asian subsidiaries |
| **Governance** | ITPGRFA Annex I 포함 (B. rapa). ABS 경로 명확. Cali Fund 해당되나 Annex I 표준 경로 |
| **Revenue Model** | Hybrid F1 (tier 2.0) — established premium market |

> ⚠️ **Critical Note**: Science (2025) — *B. rapa* 11 T2T gapless genomes + 1,720 accession pangenome 공개. "Reference genome 구축" 프로젝트의 novelty 대폭 감소. D2=1 유지하되 실질적 기회는 0.5 수준.

### 7-4. 시금치 — SP-A: Global Hybrid Baby Leaf + Downy Mildew Resistance ✅ (선택)

| 항목 | 내용 |
|---|---|
| **Region** | N. America (22% share) + Europe + E. Asia. Hybrid seeds = 88% of market |
| **Primary Buyer** | Baby leaf salad processors (Dole, Fresh Express 등) + fresh market growers |
| **Value Proposition** | Pan-NLRome-informed downy mildew resistance breeding. *P. effusa* 19+ races → rapid R-gene stacking pipeline |
| **Must-Win Traits** | ① Broad-spectrum downy mildew resistance (Pfs-1~19+) ② Baby leaf architecture ③ Bolt resistance ④ Oxalate reduction |
| **Delivery Path** | N사 breeding station 신설/인수 (Netherlands/US) → hybrid production → baby leaf processor contracts |
| **Governance** | ITPGRFA Annex I 미포함. Wild *Spinacia* 접근 필요 → 중앙아시아 ABS 복잡. Pan-NLRome 공개 데이터 활용 가능 |
| **Revenue Model** | Hybrid F1 (tier 2.0) — high-value baby leaf segment |

### 7-5. 참깨 — SE-A: Africa Health Oil Export + VACS Alignment ✅ (선택)

| 항목 | 내용 |
|---|---|
| **Region** | Africa (56.8% global production) → export to Asia/EU/Middle East. VACS priority crop |
| **Primary Buyer** | Export aggregators, health oil processors, confectionery industry |
| **Value Proposition** | Non-shattering + high oil content varieties. VACS alignment → 국제 펀딩 leverage |
| **Must-Win Traits** | ① Non-shattering capsule ② Oil content >50% ③ Drought tolerance ④ Charcoal rot resistance |
| **Delivery Path** | N사 → African breeding station/partnership → OPV licensing to local seed companies → extension |
| **Governance** | ITPGRFA Annex I 미포함. Africa multi-country ABS 복잡. Wild *Sesamum* 접근 시 추가 규제 |
| **Revenue Model** | Licensing/service (tier 1.0–1.5) — OPV 중심, hybrid premium 불가 |

### 7-6. 들깨 — PL-A: Korean Domestic Omega-3 Premium ✅ (선택)

| 항목 | 내용 |
|---|---|
| **Region** | Korea domestic (primary) + Japan (limited). Global market = niche |
| **Primary Buyer** | Korean perilla oil processors, functional food companies, domestic farmers |
| **Value Proposition** | Korea 세계 최대 germplasm 보유. α-linolenic acid 54–64%. Functional food 트렌드 |
| **Must-Win Traits** | ① α-linolenic acid >60% ② Lodging resistance ③ Uniform maturity ④ Downy mildew resistance |
| **Delivery Path** | N사 Korea HQ → 국내 종자 유통. Scale-out 제한 (한국/일본 niche) |
| **Governance** | Korean 자체 germplasm → ABS 리스크 최소. DSI: 자체 생산 데이터 자산화 용이 |
| **Revenue Model** | OPV/improved variety (tier 1.0) — self-pollinated, hybrid 불가 |

### 7-7. 시나리오 종속 D점수 재채점

#### 변경된 셀 (baseline v2 → scenario v3)

| 작물 | Dim | v2 | **v3** | 변경 근거 |
|---|---|---|---|---|
| 시금치 | D1 | 1 | **2** | Baby leaf 글로벌 시장 공략 시나리오 확정 → market scale 상향 |
| 시금치 | D3 | 2 | **1** | N사 시금치 글로벌 인프라 부재 → 신규 breeding station 필요 → delivery 하향 |
| 들깨 | D2 | 1 | **2** | 재배종 *P. frutescens* var. *frutescens* 고품질 reference 부재 확인 → genomic opportunity 상향 |
| 들깨 | D5 | 1 | **2** | Korean 자체 germplasm 중심 운영 → ABS/DSI 리스크 최소 → compliance 상향 |

> 비둘기콩, 고추, 배추, 참깨: baseline과 동일 (시나리오 분석이 기존 가정을 재확인)

#### 최종 Score (v3: scenario-conditioned)

| 순위 | 작물 × 시나리오 | D1 | D2 | D3 | D4 | D5 | Score | v2 Score | Delta |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **1** | **비둘기콩** (India Hybrid F1) | 2 | 2 | 2 | 1 | 1 | **90.08** | 90.08 | 0.00 |
| **2** | **고추** (Global Hybrid F1) | 2 | 1 | 2 | 2 | 2 | **89.05** | 89.05 | 0.00 |
| **2** | **배추** (Kimchi + Asia) | 2 | 1 | 2 | 2 | 2 | **89.05** | 89.05 | 0.00 |
| **4** | **시금치** (Global Baby Leaf) | 2 | 2 | 1 | 1 | 1 | **79.12** | 71.94 | **+7.18** |
| **5** | **들깨** (Korea Omega-3) | 1 | 2 | 2 | 1 | 2 | **77.26** | 60.97 | **+16.29** |
| **6** | **참깨** (Africa VACS) | 1 | 2 | 1 | 1 | 1 | **60.97** | 60.97 | 0.00 |

### 7-8. v2→v3 변동 분석

**상위 3개(비둘기콩, 고추, 배추) 순위 안정**: 시나리오 분석이 기존 baseline 가정을 재확인. TPP를 통해 각 작물의 시장 논리가 명시적으로 문서화되었지만, 점수 자체는 변동 없음.

**시금치 4위 상승 (+7.18)**: D1 상향(1→2)과 D3 하향(2→1)의 net effect가 양수. D1 weight(0.3629)이 D3 weight(0.2193)보다 크기 때문. "시장은 크지만 delivery가 없다"는 구조 — 대기업이라면 인수/진출로 해결 가능하므로 잠재력 있는 4위.

**들깨 5위 상승 (+16.29)**: 가장 큰 변동. D2(1→2)와 D5(1→2) 동시 상향. 재배종 genome 공백이 baseline에서 과소평가되었고, Korean germplasm의 governance 이점이 시나리오 분석에서 드러남. 다만 D1=1(niche market)이 구조적 한계.

**참깨 최하위 고정 (60.97)**: D1=1(OPV, licensing 모델) + D3=1(Africa 직접 delivery 불가)의 조합이 치명적. VACS alignment에도 불구하고 대기업 관점에서 수익 구조가 약함.

**배추 D2 주의사항**: Science (2025) pangenome 공개로 D2의 실질적 가치가 1 이하. 2-tier 스케일(1/2)에서는 1로 유지하지만, 배추를 최종 선택할 경우 "기존 pangenome 대비 N사 genome의 부가가치"를 별도 정당화해야 함.

---

## 8. 미결 사항 (Sensitivity Analysis 전)

1. **비둘기콩 D3=2 민감도**: 이 단일 셀이 1위/3위를 가르므로, D3를 1로 되돌렸을 때 순위 역전 여부 확인 필요
2. **D1 weight ±20% 변동**: D1이 0.363으로 가장 크므로, 변동 시 상위 3개 순위 안정성 확인
3. **D2 > D1 역전 시나리오**: 체크리스트 Rev 3.2에서 명시한 필수 확인 항목
4. **참깨 D5 경계**: D5=1과 D5=2 사이에서 ABS 경로 해석에 따라 갈릴 수 있음
5. **(v3 신설) 시금치 D1=2 검증**: baby leaf 글로벌 시장 규모(USD 0.76–1.5B)가 pepper(31.3B)/cabbage(4B+)와 같은 tier로 분류 가능한지
6. **(v3 신설) 들깨 D2=2 검증**: *P. citriodora* genome만 chromosome-scale → 재배종 *P. frutescens* var. *frutescens* 고품질 reference 정말 부재인지 추가 문헌 확인
7. **(v3 신설) 배추 D2 실질 가치**: Science (2025) pangenome 이후 N사가 추가 genome을 만들 novelty가 있는지 — pangenome에 포함되지 않은 한국 kimchi 계통이 존재하는지
8. **(v3 신설) 시나리오 전환 sensitivity**: 비둘기콩 PP-B(SSA) 시나리오, 시금치 delivery 해결 시나리오 등 대안 시나리오 전환 시 순위 변동

---

## 8. 참고 문헌

| 문헌 | 활용 |
|---|---|
| Kholová et al. (2021), J Exp Bot | AHP weight 순서(market→genomic→breeding) 지지 |
| CGIAR (2023–2025), 21 crops, 500+ SPMS | Market-led breeding 전환 근거 |
| VACS / Rutsaert et al. (2026), Nat Commun | pigeonpea·sesame VACS priority 작물 |
| IJtech Thailand (2025) | AHP 7-stakeholder crop prioritization, CR=5.16% |
| CBD Cali Fund / ITPGRFA Annex I | D5 compliance 판단 근거 (sesame 미포함) |
| ICRISAT hybrid pigeonpea reports | 비둘기콩 D3 상향 근거 |
| EU CSDDD (2024) | 대기업 compliance 노출 증가 근거 |

---

## 9. Revision History

| 날짜 | 버전 | 변경 내용 |
|---|---|---|
| 2026-04-18 | v1 | 초기 교차검증: 녹두 D2↓, 오크라 Borderline, 들깨 편입, 비둘기콩 Tier 재배치 |
| 2026-04-19 | v2 | N사 대기업급 확정. AHP pairwise(CR=0.0131). 대기업 weight+score 반영. 비둘기콩 1위 상승, 참깨·들깨 하락 |
| 2026-04-19 | v3 | TPP 시나리오 분화. 6개 작물 × 최적 시나리오 선정. 시금치 D1↑D3↓(4위 상승), 들깨 D2↑D5↑(5위 상승). 배추 D2 실질 가치 경고(Science 2025 pangenome) |
