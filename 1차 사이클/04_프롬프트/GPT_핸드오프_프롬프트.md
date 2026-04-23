# GPT 프로젝트 핸드오프 브리핑

## 🎯 너의 역할

너는 **N사(국내 대형 종자회사) 표준유전체 해독 프로젝트 기획**의 아키텍트 겸 실행 엔진이야. 이 프로젝트는 학부 3학년 PBL(Problem-Based Learning) 과제이고, 5주 안에 기획안 + PPT 발표를 완성해야 해.

지금까지 Claude(Opus 4.6)가 메인 설계를 맡았고, GPT는 교차검증용으로만 쓰였어. **이제부터 너(GPT)가 메인**이야. Claude는 보조 검증용으로만 쓸 거야.

---

## 📁 첨부 파일 가이드 (중요도순)

### 🔴 필수 — 반드시 먼저 읽어야 함

| # | 파일명 | 크기 | 설명 |
|---|--------|------|------|
| 1 | `작물선정하네스_v2.9.md` | 58KB | **메인 하네스**. MC1-1 전체 실행 명세. JSON wrapper, 상태전이(E-1/E-2/E-3), 게이트 조건, verdict 병합(F), State Invariants(G) 포함. v2.4부터 6차 검증을 거쳐 v2.9까지 발전함 |
| 2 | `검증컨텍스트_v2.9.md` | 6.5KB | v2.4→v2.9 수정 이력 전체. P0-1~P0-22까지 뭘 왜 고쳤는지 추적 가능 |
| 3 | `PBL문제상황.md` | 1.5KB | PBL 원문 + 핵심 요약. "N사가 뭐 하는 곳이고 뭘 해야 하는지"의 원점 |
| 4 | `pbl_roadmap_v1.md` | 21KB | 상위 로드맵. 2사이클 4MC 구조, 학습목표↔MC 매핑, 타임라인 |

### 🟡 참고 — 필요할 때 읽으면 됨

| # | 파일명 | 크기 | 설명 |
|---|--------|------|------|
| 5 | `하네스검증프롬프트_v2.9_7차.md` | 17KB | Claude가 만든 7차 검증 프롬프트. 8축 검증 프레임워크 포함. 참고용으로 "이전에 어떤 기준으로 검증했는지" 볼 때 유용 |
| 6 | `research_verification_framework.md` | 14KB | 검증 프레임워크 v1.1. 출처 등급(A/B/C/D), 3축 태그, risk-based 검증 규칙 |
| 7 | `종자선정/crop_screening_revised.md` | 22KB | AHP 쌍대비교 원본 + D1~D5 점수표. 9개 후보작물 점수 산출 근거 |
| 8 | `mc1_1a_결과보고서_쉬운버전.md` | 10KB | MC1-1a(SURVEY) 결과. 작물별 판정과 핵심 논점 정리 |

---

## 🗺️ 프로젝트 전체 구조

```
PBL 모듈 1: 표준유전체 해독 기획
├── 사이클 1: 작물 선정
│   ├── MC1-1a SURVEY    ← ✅ 완료 (9개→4개 축소)
│   ├── MC1-1b EVALUATE  ← ⏸️ 대기 (하네스 검증 완료 후 실행)
│   └── MC1-1c SYNTHESIS ← ⏸️ 대기
└── 사이클 2: 유전체 해독 설계
    ├── MC2-1 DEEP-DIVE
    ├── MC2-2 DESIGN
    └── MC2-3 SYNTHESIS → 최종 기획안 + PPT
```

### 타임라인
- **4/24 (목)**: 초안 제출 — 3일 남음
- **5/21 (수)**: 최종 발표

---

## 📊 현재 상태 요약

### MC1-1a 결과 (SURVEY 단계 — 완료)

9개 후보 작물 중 핵심 4개:

| 작물 | 판정 | 핵심 논점 |
|------|------|-----------|
| 고추 | 가장 안정적 | 38.31Mt 글로벌 생산, CAGR +1.45%, Hybrid 비중 확고 |
| 배추 | 유지 가능 | 김치 프리미엄 세그먼트로 D1=2 정당화 |
| 비둘기콩 | 가장 논쟁적 | D5↑ 타이밍 우수, D3↓ IP 회수 장벽 |
| 시금치 | 역전 후보 #1 | CAGR +3.20% (9작물 최고), D1·D5 과소평가 가능성 |

### D점수 체계 (5축 AHP 가중치)
- D1 시장 매력도: **0.363** (36.3%)
- D2 유전체 신규성: 0.219 (21.9%)
- D3 사업 실행 가능성: 0.219 (21.9%)
- D4 기술 장벽: 0.092 (9.2%)
- D5 전략적 타이밍: 0.107 (10.7%)

---

## 🔧 하네스 핵심 설계 (v2.9)

이 하네스가 이 프로젝트의 심장이야. 핵심만 정리하면:

### 5-Stage 구조
```
Stage 0 DISPATCH → Stage 1 RESEARCH → Stage 2 VERIFY → Stage 3 CROSS-VERIFY → Stage 4 SYNTHESIZE
```

### FSM (유한상태기계) 핵심
- **4개 상태 변수**: TARGET_CROP, DATA_SUFFICIENCY, SCORING, BLOCK1_BRIEF
- **DATA_SUFFICIENCY enum**: INCOMPLETE(0) < GATE_READY(1) < PASSED(2)
- **final_verdict** = gate.verdict × cross_verification.verdict (F 테이블로 병합)
- **final_verdict가 유일한 진행 기준** — gate.verdict 단독 사용 금지
- **final_action 정제 규칙**: CONDITIONAL일 때 E-3의 next_action이 final_action을 결정
- **human_judgment_required override**: 이 issue_type 있으면 무조건 HALT_HUMAN_CHECKPOINT

### 검증 이력 (6차까지 Claude↔GPT 교차검증)
| 차수 | 버전변경 | 결과 | 핵심 수정 |
|------|----------|------|-----------|
| 1차 | v2.3→v2.4 | CONDITIONAL | P0 5건 (산식, 시간앵커, 태그, Gate, NCBI) |
| 2차 | v2.4→v2.5 | FAIL | 앵커 누락, Few-shot 하드코딩, enum 확장 |
| 3차 | v2.5→v2.6 | FAIL | CONDITIONAL 분기, FAIL retry, cross_verification |
| 4차 | v2.6→v2.7 | FAIL | final_verdict 통일, AUTO_REPAIR, rollback, carry_forward |
| 5차 | v2.7→v2.8 | FAIL | gate.verdict 잔존, E-1 final_verdict, State Invariants |
| 6차 | v2.8→v2.9 | FAIL | AUTO_REPAIR→final_action, DATA_SUFFICIENCY 통일, human_judgment override, enum ordinal |

---

## ✅ 지금부터 네가 해야 할 일 (Phase 1~4)

### Phase 1: 하네스 최종 검증 (최우선)

v2.9 하네스를 **아키텍트 관점**에서 검증해줘. 이전 6차까지 GPT가 검증하면서 매번 P0급 구조적 결함을 발견했어. v2.9에서 P0-19~22를 수정했으니, 이번에는:

1. 하네스 전문 읽기
2. **end-to-end dry-run**: MC1-1a PASS → MC1-1b → MC1-1c 전체 시나리오를 상태 변수 추적하면서 시뮬레이션
3. 8축 검증: 앵커일관성, 스키마연속성, 기법적용타당성, 조건부게이트, 도메인적합성, 실행가능성, 과잉프롬프팅, 마이크로사이클대응
4. 판정: PASS / CONDITIONAL / FAIL
5. **PASS 또는 마이너만 남을 때까지 수정→재검증 반복**

### Phase 2: 로드맵 업데이트
- `pbl_roadmap_v1.md`를 하네스 v2.9 기준으로 업데이트
- 타임라인 재조정 (4/24 초안 데드라인 반영)

### Phase 3: MC1-1b (EVALUATE) 실행
- 하네스의 MC1-1b Stage 0 명령에 따라 실행
- D점수 재산정 + 민감도 분석 (흔들기 테스트)
- Gate 조건 충족 시 MC1-1c로

### Phase 4: 최종 결과물
- MC1-1c (SYNTHESIS) 실행 → 최종 작물 1개 확정
- 발표 블록 1 brief 작성
- 체크포인트 기록 + 형주 리딩 문서

---

## ⚠️ 주의사항

1. **이 하네스는 Claude가 설계한 거야.** "AI가 만든 체계를 AI가 실행"하는 자기참조 구조. 네가 실행하면서 구조적 문제를 발견하면 즉시 지적해줘.

2. **v2.5~v2.8 하네스 파일은 절단되어 있음.** Edit tool 버그로 46,627 bytes에서 잘렸어. **v2.9만 완전한 파일**이야.

3. **출처 등급 규칙**: A(Primary/DOI) > B(Secondary) > C(Tertiary) > D(Non-verifiable). D등급만으로 게이트 PASS 불가.

4. **형주는 비전공 2학년**이야. 최종 보고서와 발표 자료는 형주가 이해하고 설명할 수 있는 수준이어야 해.

5. **4/24 초안 데드라인.** 시간이 없어. Phase 1 검증은 빠르게 끝내고 Phase 3 실행에 집중해야 해.
