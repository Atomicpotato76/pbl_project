# AGENTS.md (Template) — Seed R&D Investigation Project

장기 종자 개발 조사/검증 프로젝트를 위한 운영 지침 템플릿입니다.
이 파일을 레포 루트에 `AGENTS.md`로 복사해 사용하세요.

---

## 1) Project Charter

### Goal
- 목표: 종자(육종/품종개발) 후보를 과학적·상업적 근거로 평가하여 우선순위를 도출한다.
- 결과물: 재현 가능한 근거 기반 리포트(월간/분기), 의사결정 로그, 실험/문헌 트레이스.

### Scope
- 포함: 논문/특허/시장/규제/기후/공급망 조사, 가설 수립, 교차검증, 리스크 분석.
- 제외: 무근거 추정, 출처 없는 수치, 검증 불가능한 내부 루머.

### Deliverables
- Executive Summary (1–2p)
- Evidence Table (source, date, method, confidence)
- Risk Register (기술/규제/사업 리스크)
- Next Action Plan (2주 단위)

---

## 2) Operating Rules

### Evidence First
- 모든 핵심 주장에는 반드시 출처를 연결한다.
- 출처 없는 확정 표현 금지 (`~이다` 대신 `~로 확인됨/추정됨` 구분).

### Date Discipline
- 상대 시간 표현(`오늘/최근`) 사용 시 절대 날짜 병기.
- 빠르게 변하는 정보(가격/규제/뉴스)는 최신성 재검증 후 사용.

### Source Priority
1. 1차 자료: 규제기관, 공식 통계, 원문 논문/특허
2. 2차 자료: 리뷰/산업 리포트
3. 3차 자료: 기사/블로그(보조용)

### Inference Labels
- 각 결론에 라벨 표기:
  - `FACT`: 출처로 직접 확인
  - `INFERENCE`: 복수 근거 기반 추론
  - `HYPOTHESIS`: 추가 검증 필요 가설

---

## 3) MCP / Tooling Runbook

> 중요: AGENTS.md는 도구 "설명" 파일이다. 실제 MCP 연결은 환경/클라이언트 설정에서 수행한다.

### Required Connectors (권장)
- Literature: PubMed, Crossref, OpenAlex
- Patent: Google Patents, USPTO/EPO/KIPRIS
- Regulation: USDA, FDA/EFSA, 국내 유관기관
- Market/Data: FAOSTAT, OECD, World Bank, 기상 데이터
- Internal: 사내 실험노트/문서DB/데이터레이크

### Session Start Checklist
1. MCP 서버 연결 여부 확인
2. 인증 토큰/환경변수 확인
3. 샘플 조회 1건 성공 여부 확인
4. 리포트 출력 폴더/파일명 규칙 확인

### Session End Checklist
1. 근거 링크 누락 여부 점검
2. 날짜/단위(kg/ha, ppm 등) 정규화 점검
3. 리스크/한계사항 명시
4. 다음 액션 3개 이상 제시

---

## 4) Standard Workflow

1. **Question Framing**
   - 연구 질문, 가정, 성공 기준 정의
2. **Collection**
   - 문헌/특허/시장/규제 데이터 수집
3. **Normalization**
   - 단위, 통화, 기간 기준 통일
4. **Cross-Validation**
   - 서로 다른 출처 2개 이상으로 핵심 수치 재검증
5. **Synthesis**
   - 품종/기술 후보별 scorecard 작성
6. **Decision Draft**
   - 추천안/보류안/탈락안 + 근거

---

## 5) Output Format (Required)

### Response Structure
- 요약
- 핵심 근거 (표)
- 리스크/불확실성
- 권고안 (즉시 실행 / 추후 검증)

### Evidence Table (minimum)
- Claim
- Source (URL or doc id)
- Source date
- Method (실험/관측/통계)
- Confidence (High/Medium/Low)

### Decision Log
- Decision
- Why now
- Expected upside
- Downside / guardrail
- Revisit date

---

## 6) Research Quality Gates

분석 완료 전, 아래를 모두 통과해야 한다.

- [ ] 핵심 수치 2개 이상 출처로 교차검증
- [ ] 최신성 검토 완료 (date stamp 포함)
- [ ] 지역/기후 조건의 외삽 위험 설명
- [ ] 규제 리스크(국가별) 최소 1개 이상 명시
- [ ] 반대 증거/실패 시나리오 포함

---

## 7) File & Naming Convention

- `reports/YYYY-MM-DD_topic_summary.md`
- `data/raw/<source>/<YYYY-MM-DD>/...`
- `data/processed/<topic>/<version>/...`
- `decisions/YYYY-MM-DD_decision-log.md`

커밋 메시지 예시:
- `docs(agents): add seed R&D operating playbook`
- `feat(pipeline): add patent evidence normalization`

---

## 8) Collaboration Protocol

- 고비용/고위험 의사결정은 반드시 “대안 2개 이상” 제시.
- 데이터 부재 영역은 숨기지 말고 `Unknowns` 섹션에 명시.
- 의견 충돌 시 근거 우선순위 규칙(1차 > 2차 > 3차)을 따른다.

---

## 9) Optional: Scoring Template

후보별 0–5점 (가중치 합 100)

- Agronomic performance (25)
- Stress tolerance (20)
- Regulatory feasibility (15)
- Market attractiveness (20)
- Production scalability (20)

총점 + 민감도 분석(가중치 ±20%)을 함께 보고한다.

---

## 10) Copy Guide

이 파일을 복사해 프로젝트별로 아래만 우선 커스터마이징:
- 목표 작물/지역
- 필수 규제기관 목록
- 내부 데이터 소스 URI
- 의사결정 cadence (주간/격주/월간)

