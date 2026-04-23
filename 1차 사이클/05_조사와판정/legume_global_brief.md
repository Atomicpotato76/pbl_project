# 콩과식물(Fabaceae) 표준유전체 후보 — 글로벌 조사 브리프

**작성 맥락**: 첨부한 PBL 모듈1 문제지(N사 시나리오, 5주 기획 + 발표)와 작물 선택 체크리스트(rev 2.0) 기반으로, **전 세계 콩과식물 유전체 공백 지도**를 깔고 **4개의 포트폴리오 옵션**으로 압축한 사전 스크리닝 결과.

**작성일**: 2026-04-16 (2025–2026년 문헌 반영)
**사용법**: 첨부한 체크리스트 v2.0 + PBL 문제지와 함께 GPT 세션에 투입. 이 브리프의 후속 작업 프레임(§6)을 참고해 GPT에게 심화 작업 지시.

---

## 1. 2025–2026년 콩과 유전체 지형 — 대륙별 현황

단순 "reference 첫 구축" 논리는 2026년 시점에 설득력이 없음. 체크리스트 §2의 "기존 assembly quality 정량 평가"에서 이미 BUSCO ≥ 98% / contig N50 ≥ 10Mb 수준이 수두룩함. 차별화는 (a) **지역 특이 germplasm 공백**, (b) **pangenome/super-pangenome 구조변이 레이어**, (c) **orphan/underutilized 영역**에서만 가능.

### 1-1 동아시아 (East Asia)
- **Soybean (*Glycine max*)** — 포화. Williams 82, Zhonghuang 13, Lee, Jack 등 T2T 다수 + 2,898 accessions graph pangenome (SoyBase)
- **Mungbean (*Vigna radiata*)** — 포화. VC1973A(2014) → JL7(2022) → Weilv-9 T2T(2024) → KUML4(2024) → VR_IPM02-03 Indian(2025)
- **Adzuki bean (*V. angularis*)** — 중국 cultivar 기반 4–5개 ref (Yang 2015, Kang 2015, Chu Jingnong6 2024, Li 2024, Hu ZH20 2026). **Korean cultivar 공백**
- **Wild soybean (*G. soja*)** — 중국·홍콩 중심 (W05 Xie 2019, Liu 2020 26-accession). **Korean island+mainland germplasm 공백**
- **Ricebean (*V. umbellata*)** — 인도 계통 2개 (Kaul 2019 Himshakti, Guan 2022 FF25). **East Asian 계통 공백**

### 1-2 남아시아 (South Asia)
- **Chickpea (*Cicer arietinum*)** — **완전 마감**. Khan et al. 2024 *Nature Genetics* Cicer **super-pangenome** (8 annual wild + 2 cultivated, BGI × ICRISAT × Murdoch)
- **Pigeon pea (*Cajanus cajan*)** — Zhao 2020 PBJ pangenome + ICRISAT 2024 **세계 최초 speed-breeding protocol** (ICPV 25444, 45°C 내열 품종 2025 출시)
- **Blackgram/urad (*V. mungo*)** — reference 있음, pangenome 진행 중
- **Grass pea (*Lathyrus sativus*)** — reference 최근 공개, pangenome 공백. **β-ODAP(neurotoxin) 저감 breeding이 핵심 과제**, South Asia/East Africa 극한 기후 작물

### 1-3 아프리카 (Sub-Saharan)
- **Cowpea (*V. unguiculata*)** — Wu 2024 *Nat Genet* + Wang 2025 커버. **Southern African smallholder landrace pangenome 공백** (2025 *Nat Comms* climate-adaptation 제시)
- **Bambara groundnut (*V. subterranea*)** — AOCC reference (Chang 2018). Population-scale pangenome 공백. Sub-Saharan 수억 명 dietary protein 원천, 가뭄·척박지 내성
- **Kersting's groundnut (*Macrotyloma geocarpum*)** — Kafoutchoni et al. 2025 *Nat Comms* reference + population 발표 (막 공개)
- **African yam bean (*Sphenostylis stenocarpa*)** — reference 거의 없음, Tier 3 classic orphan
- **AOCC (African Orphan Crops Consortium)** — 101개 orphan crops 목표 중 ~30개 진행, 30+개 미사용 상태

### 1-4 중남미 (Latin America)
- **Common bean (*Phaseolus vulgaris*)** — Schmutz 2014 + Wang 2025 완료
- **Tepary bean (*P. acutifolius*)** — Moghaddam et al. 2021 *Nat Comms* reference (Sonoran Desert landrace + wild). Barrera 2024 *Crop Science* + López-Hernández 2025 *IJMS* multi-environment GWAS. **Heat/drought 최강 Phaseolus**, common bean introgression platform
- **Lima bean (*P. lunatus*)** — reference 있음, pangenome 공백
- **Andean lupin (*Lupinus mutabilis*)** — orphan, 고단백 (~45%), reference 최근

### 1-5 동남아 (Southeast Asia)
- **Winged bean (*Psophocarpus tetragonolobus*)** — 2024–2025 reference 출현. Underutilized, 잎·덩이뿌리·종자 모두 식용·고단백
- **Jack bean, velvet bean** — orphan, 의약·사료 수요

### 1-6 유럽·지중해 (Europe / Mediterranean)
- **Faba bean (*Vicia faba*)** — Jayakodi 2023 *Nature* 거대 게놈 (~13 Gb) 완료 + Wang 2025
- **Lupin (*L. albus*, *L. angustifolius*)** — reference 완료, pangenome 공백. **EU alt-protein 정책수요 강함**
- **Pea (*Pisum sativum*)** — Wang 2025 커버. EU INCREASE project로 landrace 수집 중

---

## 2. Hard Filter 탈락 후보 및 사유

| 작물 | 학명 | 주 탈락 사유 | 체크리스트 항목 |
|---|---|---|---|
| Soybean (단일 ref) | *Glycine max* | T2T 다수, blue ocean 부재 | H-1, §2 |
| Mungbean (단일 ref) | *V. radiata* | T2T + pangenome 완료 | §2 |
| Chickpea | *Cicer arietinum* | 2024 super-pangenome 완료 (BGI×ICRISAT) | H-1 |
| Pigeon pea | *Cajanus cajan* | pangenome + speed-breeding 완료 | H-1 |
| Common bean (단일 ref) | *P. vulgaris* | Schmutz 2014 + Wang 2025 | H-1 |
| Faba bean | *Vicia faba* | ~13 Gb (H-3 경계), Jayakodi 2023 *Nature* 완료 | H-1, H-3 |
| Peanut | *Arachis hypogaea* | allotetraploid, 국내 재배면적 < 7,000 ha | H-1, H-3 |
| Pea, lentil, hyacinth bean | — | Wang 2025 일괄 커버 | H-1 |

---

## 3. 글로벌 전략 축 4개

전 지구 관점에서 N사가 택할 수 있는 **전략적 포지셔닝 축**:

| 축 | 핵심 논리 | 회수 경로 | 주 리스크 |
|---|---|---|---|
| **축 A — 상업 종자 경쟁** | 대형 수요 작물 pangenome 차별화 | hybrid F1, licensing, marker service | 다국적 기업(Bayer, Corteva, BGI) 선점 |
| **축 B — 지역 germplasm 공백** | 기존 ref 미커버 지역 계통 집중 | 지역 브랜드 품종, 수출 | 시장 규모 제한 |
| **축 C — 기후 회복력 + ODA** | drought/heat/salt tolerance + CGIAR/KOPIA/KAFACI 연계 | ODA, 공공사업, SDG, climate fund | 상업 ROI 지연 |
| **축 D — Orphan 블루오션** | AOCC / underutilized 작물 선점 | 기능성 식품, 사료, 가공 원료 | Seed system·adoption 취약 |

어느 축이 맞는지는 **N사 포지셔닝 + PBL 평가자의 "글로벌 경쟁" 해석 깊이**에 달려있음.

---

## 4. 포트폴리오 옵션 4개

모든 옵션은 체크리스트 §14의 3-tier 구조(Flagship / Platform / High-risk)를 유지.

### 옵션 1 — **Global Commercial** (축 A 중심)

> 글로벌 종자기업과 정면승부. 리스크 가장 높지만 시나리오 원문 "글로벌 경쟁" 스토리 가장 강함.

- **Tier 1 (Flagship)**: **Cowpea (*V. unguiculata*)** African-adapted drought elite cultivar pangenome
  - ~14M ha 글로벌 재배 (FAO), Wu 2024 ref 있으나 smallholder landrace pangenome 공백
  - IITA·KAFACI 연계, Sub-Saharan + South Asia 시장
- **Tier 2 (Platform)**: ***Vigna* 속 super-pangenome** — cowpea + mungbean + adzuki + ricebean + wild relatives
- **Tier 3 (Orphan)**: **Bambara groundnut** landrace pangenome (AOCC 연계, climate resilience)

### 옵션 2 — **Climate-Resilience Platform** (축 C 중심) ★ 가장 균형잡힘

> CGIAR / Cali Fund / EU CS3D 흐름 정중앙. 체크리스트 §9 cross-cutting 완벽 충족.

- **Tier 1 (Flagship)**: **Tepary bean (*P. acutifolius*)** × common bean introgression platform
  - Sonoran Desert 기반 heat/drought 최강
  - 전 세계 최대 소비 legume(common bean) 개량 파이프라인 직접 제공
  - CIAT·Alliance Bioversity·AGROSAVIA 연계
- **Tier 2 (Platform)**: ***Phaseolus* super-pangenome** — vulgaris + acutifolius + lunatus + coccineus
- **Tier 3 (Orphan)**: **Grass pea (*Lathyrus sativus*)** low-ODAP landrace pangenome
  - South Asia / East Africa 극한 기후 작물
  - neurotoxin 저감 breeding = 글로벌 nutrition security 이슈

### 옵션 3 — **AOCC Orphan** (축 D 중심)

> 블루오션 극대화. 상업 ROI 가장 지연, 학술 차별화·논문 임팩트 최강.

- **Tier 1 (Flagship)**: **Bambara groundnut** Sub-Saharan landrace pangenome + trait GWAS
- **Tier 2 (Platform)**: **West African legume cluster** — Kersting's groundnut + African yam bean + bambara 공통 pipeline
- **Tier 3 (Orphan)**: **Winged bean** East/Southeast Asian landrace reference

### 옵션 4 — **Hybrid: Korea-anchored Global** (축 B + C)

> 국내 실행 안전성 + 글로벌 스토리 동시 확보. 가장 현실적.

- **Tier 1 (Flagship, 국내 기반)**: **Korean adzuki elite cultivar + landrace pangenome**
  - Arari, Hongeon, Chungju, Dahyun, Sinpalkwang 주요 품종 + RDA KACC landrace
  - 중국 ref(Jingnong6, ZH20)와 차별화, 국내 ~30,000 ha 수요 견고
- **Tier 2 (Platform, 글로벌)**: **Cowpea** African landrace × Korean-adapted line **cross-reference pangenome**
  - KAFACI 연계, drought trait introgression
- **Tier 3 (Orphan)**: **Rice bean (East Asian)** 또는 **Bambara groundnut** 선택

---

## 5. 옵션 비교표

| 차원 | 옵션 1 Global Commercial | 옵션 2 Climate-Resilience ★ | 옵션 3 AOCC Orphan | 옵션 4 Hybrid Korea-Global |
|---|---|---|---|---|
| Tier 1 주 작물 | Cowpea (~14M ha) | Tepary × common bean | Bambara groundnut | Korean adzuki |
| 글로벌 시장 규모 | 매우 큼 | 큼 (common bean 파생) | 중간–작음 | 중간 |
| 국내 실행 안전성 | 낮음 | 낮음–중 | 낮음 | **높음** |
| 경쟁 선점 리스크 | **매우 높음** | 중간 | 낮음 | 낮음 |
| 5주 기획 feasibility | 중 (파트너 필수) | 중 | 중 | **높음** |
| 기후변화 스토리 | 중 | **매우 강함** | 강함 | 중 |
| ODA/CGIAR 연계 | 강함 (IITA) | **매우 강함** (CIAT) | **매우 강함** (AOCC) | 중 |
| 학술 차별화 | 중 | 강함 | **매우 강함** | 중 |
| 상업 ROI 회수 | **빠름** | 중 | 느림 | 빠름 |
| SDG 2·13·15 기여 | 강함 | **매우 강함** | **매우 강함** | 중 |
| 체크리스트 §9 충족 | 중 | **100%** | 강함 | 중 |
| 체크리스트 §14 시너지 | Vigna 공통 pipeline | Phaseolus 공통 pipeline | AOCC 공통 pipeline | Vigna 일부 공유 |
| 체크리스트 §8 DSI 리스크 | 중 (다국 ABS) | 중–높 (Mexico·US·CIAT MTA) | 높음 (다수 아프리카국) | 낮음 (Tier 1 국내) |

---

## 6. 권장 판단 프레임 및 후속 작업 요청

### 6-1 옵션 선택 기준

| PBL 평가자 해석 | 권장 옵션 |
|---|---|
| "글로벌 경쟁" 스토리 강하게 요구 | **옵션 2** (Climate-Resilience) |
| "실행 가능성" 우선시 | **옵션 4** (Hybrid Korea-Global) |
| "학술 신규성·임팩트" 우선시 | **옵션 3** (AOCC Orphan) |
| "상업 ROI 속도" 우선시 | **옵션 1** (Global Commercial) 또는 옵션 4 |

시나리오 원문이 "글로벌 종자기업과 경쟁 가능한 품종"이므로 **옵션 2가 가장 정합적**. 단, germplasm 접근(Mexico·US ABS + CIAT MTA) 리스크 존재 → **옵션 2 + 옵션 4 하이브리드**도 타당:

> Tier 1: Korean adzuki (실행 즉시) / Tier 2: Tepary × common bean platform (기후 스토리) / Tier 3: Bambara groundnut (AOCC 연계)

### 6-2 GPT 후속 작업 요청 목록

옵션 선택 후 아래 중 하나 또는 복수 진행:

1. **선택된 옵션의 각 Tier별 체크리스트 §0 TPP (Target Product Profile) 초안 작성**
   - SPMS (Seed Product Market Segment) 정의
   - must-have traits + value-added traits 정량 threshold
   - TPE (Target Population of Environments) — geography + agroecology + 2030·2050 기후 projection

2. **5-year milestone 상세화** (체크리스트 부록 B 템플릿 기반)
   - Y1~Y5 deliverable + KPI + 예산 배분
   - Y1 reference v1.0, Y2 diversity panel, Y3 marker validation, Y4 GS training + pangenome v1.0, Y5 pre-release + licensing MoU

3. **Sequencing·Assembly·Annotation pipeline 상세 설계**
   - Platform 조합: PacBio HiFi / ONT / Hi-C / Illumina coverage 권장치
   - Bioinformatics tool chain: HiFiasm / Verkko + BUSCO + MAKER/BRAKER + InterProScan
   - Pangenome: PGGB / minigraph-cactus / VG
   - 인력 구성 (wet ≥ 2 + dry ≥ 1 + 육종 ≥ 1 + PM ≥ 1)

4. **체크리스트 §8 규제·IP 분석**
   - 각 Tier 작물의 germplasm 원산지 ABS 법률 매핑
   - DSI / Cali Fund contribution threshold 분석
   - ITPGRFA MLS Annex I 해당 여부 + SMTA 적용 가능성
   - Korea RDA + ABS Clearing House 실무 경로

5. **Budget 추정 및 ROI 모델링**
   - WGS 비용: accessions × coverage × platform (PacBio HiFi ~$2,500/sample @ 30x, ONT ~$1,200/sample, Illumina WGRS ~$150/sample @ 15x)
   - Phenotyping 비용: MET (≥ 3 sites × ≥ 2 years) × HTP 인프라
   - 5년 총예산 + licensing / marker service / 공공사업 수익 시나리오
   - IRR·NPV 추정, Sharpe ratio 적 포트폴리오 최적화

6. **30분 PPT 발표 목차 설계** (PBL 심사 평가자 관점)
   - 문제 정의 → 글로벌 지형 분석 → 후보 선정 근거 → TPP·TPE → 실행계획 → 기대효과·SDG 기여
   - 시각 자료: 대륙별 공백 지도, Tier 포트폴리오 tree, 5-year Gantt, ROI projection

7. **체크리스트 Sequential Filter 정량 적용**
   - Stage 1 Hard Filter 9개 threshold 각 후보 pass/fail 표
   - Stage 2 Soft Filter 12개 항목 0–2 weighted scoring
   - Stage 3 Strategic Filter + Stage 4 Feasibility Filter 점검
   - 종합 score (0–100) + 판정 대역(Go / Conditional / Hold / Reject)

---

## 7. 핵심 참고문헌

### 🟢 Peer-reviewed (DOI 확보)

**Pangenome·Super-pangenome 이론**
- Jayakodi, Shim, Mascher (2025). *Annual Review of Plant Biology* 76:663. doi:10.1146/annurev-arplant-090823-015358
- He et al. (2025). Super-pangenome review. *Plant Communications* 6:101230. doi:10.1016/j.xplc.2024.101230
- Wang et al. (2025). Pangenome analysis of nine pulses. *Nature Genetics* 57:2052. doi:10.1038/s41588-025-02280-5

**Chickpea / Pigeon pea**
- Khan et al. (2024). Cicer super-pangenome. *Nature Genetics* 56:1225. doi:10.1038/s41588-024-01760-4
- Zhao et al. (2020). Pigeon pea pangenome. *Plant Biotechnology Journal* 18:1946

**Adzuki / Mungbean / Ricebean (East Asian)**
- Chu et al. (2024). Adzuki Jingnong6 ref + 322 accessions. *Plant Biotechnology Journal* 22:2173. doi:10.1111/pbi.14337
- Hu et al. (2026). Adzuki ZH20 ref + AdzukiBeanAtlas. *Advanced Science*. doi:10.1002/advs.202507157
- Guan et al. (2022). Ricebean FF25 + 440 landraces. *Nature Communications* 13:5707. doi:10.1038/s41467-022-33515-2

**Soybean / Wild soybean**
- Xie et al. (2019). W05 reference-grade wild soybean. *Nature Communications* 10:1216. doi:10.1038/s41467-019-09142-9
- Liu et al. (2020). 26-accession graph pangenome. *Cell* 182:162. doi:10.1016/j.cell.2020.05.023

**Phaseolus / Tepary**
- Moghaddam et al. (2021). Tepary bean genome. *Nature Communications* 12:2638. doi:10.1038/s41467-021-22858-x
- Barrera et al. (2024). Multi-environment trial tepary vs common vs Lima. *Crop Science*. doi:10.1002/csc2.21354

**African orphan legumes**
- Kafoutchoni et al. (2025). Kersting's groundnut genome. *Nature Communications* (Orphan crop collection)
- Kumar et al. (2019). AOCC 101 African orphan crops/trees status. *Planta*. doi:10.1007/s00425-019-03156-9

### 🟡 Secondary / supporting
- Stupar et al. (2024). Soybean community strategic plan 2024–2028. *The Plant Genome*. doi:10.1002/tpg2.20516
- ICRISAT press release (2025). Heat-tolerant pigeonpea ICPV 25444 via speed breeding
- Kang et al. (2015). Korean adzuki draft. *Scientific Reports* 5:8069
- Li et al. (2014). G. soja pangenome. *Nature Biotechnology* 32:1045

---

*End of brief — 2026-04-16*
