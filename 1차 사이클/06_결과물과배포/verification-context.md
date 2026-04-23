# 검증 컨텍스트 — MC1-1 하네스 v2.4

이 하네스에 대해 이미 알려진 사항:

1. **설계자:** Claude(Opus 4.6)가 설계하고 자체 품질 체크리스트로 검증함

2. **수정사항 A~E가 적용된 버전:**
   - **(A)** Stage 0에 불변 앵커 + 출처 규칙 삽입
   - **(B)** Stage 2에 게이트 조건 #4~#6 추가 (범위 준수, 완전성, 유전체 기술 타당성)
   - **(C)** Stage 0에 마이크로사이클 인식 앵커 추가
   - **(D)** 3-axis tag system — v2.3에서 하네스 본문에 적용됨 (출력 계약 섹션에 Type×Verification×Argument 3축 태그 + 예시 포함). v2.4에서 Few-shot 예시 보강 및 일관성 정비 완료.
   - **(E)** Stage 2 검증 절차 구체화

3. **v2.4 P0 수정사항 (GPT-5.4 1차 외부 검증 반영):**
   - **P0-1:** 중간 산식 `Soft Score = Σ(Di×Wi)×50+50` 삭제 → 정규화 Score = (Σ(Di×Wi)/2.000)×100 만 유지
   - **P0-2:** "2019-2023" 고정 연도 범위 → `latest_available_year` 동적 기준으로 변경
   - **P0-3:** 3-axis tag system 적용 상태 불일치 해소 (이 context 파일의 (D) 항목 수정 + 하네스 내 Few-shot 예시 보강)
   - **P0-4:** Gate 기준 "P0/P1 ≥70%" → P0=100%, P1≥80% 분리 기준
   - **P0-5:** D2/D4에 NCBI Genome/Ensembl Plants 교차확인 경로 추가 + 불일치 시 [미결] 태그

4. **v2.4 PE 기법 보강:**
   - 각 stage_0_command에 [Role] 명시 추가
   - MC1-1a에 ReAct-lite 패턴 (Search→Observe→Decide 루프) 추가
   - MC1-1a에 Tier A 셀 작성 Few-shot 예시 추가
   - 검증 중단 규칙 (Verification Stop Rule) 추가
   - D점수 루브릭에 AND/OR 논리 연산자 명시

5. **구조적 한계:** "AI가 만든 검증 체계를 AI가 적용"하는 자기참조 구조이므로, 독립적인 외부 모델(GPT)에 의한 교차검증이 필요함

6. **1차 외부 검증 결과 (v2.3):** GPT-5.4 Thinking이 CONDITIONAL PASS 판정. P0 5건, P1 다수 지적. 핵심 축(앵커, 게이트, MC대응) PASS, PE 기법과 실행가능성에서 결함 발견.

7. **평가 기준:** 프롬프트 엔지니어링 7가지 기법(Zero-shot+구조화, Few-shot, CoT, Role, Self-consistency, Chaining, ReAct)을 기준으로 하네스의 기법 적용 상태도 평가 필요

8. **PBL 배경:** 국내 종자회사 N사의 표준유전체 해독 프로젝트 대상 작물 선정. 학부 3학년 팀이 5주 PBL로 수행. 현재 MC1-1 단계(작물 선정 실증 분석).
