# Checkpoint 2026-04-22 - 5차 검증 준비

## 목적

이 문서는 현재까지의 진행상황과, 이제 열릴 여러 세션에서 무엇을 해야 하는지 빠르게 공유하기 위한 handoff/checkpoint 문서다.

현재 프로젝트의 직접 목표는 `작물 추천`이 아니라, `시나리오 세트가 실제 crop selection 단계로 넘어갈 만큼 충분히 잠겼는지`를 레드팀 관점에서 검증받는 것이다.

---

## 2026-04-22 현재 운영 결론 (Peru route 재확인 반영)

- 현재 `accept_for_crop_selection = none`, `ready_to_move = no` 상태를 유지한다.
- active scenario는 `N1`, `N2` 두 개다.
- `P1`은 `drop_now`로 정리한다. 다만 이유는 `Peru route stale`이 아니라, 2026년 현재 Peru school-feeding route가 `PAE`로 재편되어 현행 owner는 확인되었음에도 `SG-6 legal/ABS`, `SG-7 reference-genome necessity`, `HF-0/HF-3 public genome sufficiency`를 넘기 어렵기 때문이다.
- 따라서 현재 단계에서 `남미 전체 제외`로 읽지 않는다. 이번에 제외되는 것은 `P1` 프레이밍이며, South America lane은 필요 시 별도 시나리오로 다시 열 수 있다.
- 운영상 다음 잠금 대상은 `N1`, `N2`다.
  - `N1`: exact subgroup, source-holder/accession, Kenya ABS/NACOSTI/KEPHIS route, named delivery owner/fallback, public-genome insufficiency memo 잠금
  - `N2`: exact food-legume subgroup, public genome fail-fast memo, non-substitutable reference-genome use-case, exact legal route 잠금
- 다른 브랜치에서 종자/crop 조사 작업을 병행하더라도, 현재 시점의 live lane은 `N1/N2 only`로 본다. `P1`이나 broad South America lane은 현 branch 기준 shortlist 작업 범위에서 제외한다.

---

## 현재까지 잠긴 것

### 1. 작업 방식 전환

- 기존 `crop-first` 흐름에서 `scenario-first` 흐름으로 전환했다.
- 즉, 먼저 시나리오를 좁히고 검증한 다음, 그 시나리오에 맞는 작물 long list를 만들고 hard filter를 건다.

### 2. 기준표 업데이트

- 현재 공식 기준표는 `최종_시나리오선정기준_v1.2.md`다.
- 이 버전에서 아래 원칙이 고정되었다.
  - `PBL-first hierarchy`
  - `공개 유전체 충분성 fail-fast (HF-0)`
  - `reference genome necessity`를 hard gate로 취급
  - `heroic assumption`을 baseline에서 금지

### 3. 현재 검증 대상 시나리오 세트

현재 5차 검증에 올릴 대상은 아래 3안이다.

1. `N1`  
   `Kenya dairy forage resilience`

2. `N2`  
   `India protein-security food-legume public route`

3. `P1`  
   `Peru high-Andean public/blended nutrition route for underutilized Andean grains`

### 4. 현재 내부 가설 우선순위

- `N1` = 현재 lead
- `N2` = 현재 backup
- `P1` = 현재 exploratory reserve

중요:
- 이 순서는 `현재 작업 가설`일 뿐이다.
- 5차 레드팀 검증 결과에 따라 뒤집힐 수 있다.

### 5. 현재 판단 요약

- `N1`은 genome-thesis가 가장 강하다.
- `N2`는 payer / governance가 가장 선명하다.
- `P1`은 남미 단일국가형 시나리오로는 가장 그럴듯하지만, 2026년 현재 Peru school-feeding route가 `PAE`로 재편되었음에도 crop phase에서 `공개 유전체 충분성`과 ABS 부담에 걸릴 위험이 크다.

---

## 아직 안 잠긴 것

### 공통 미해결 포인트

1. `scenario level에서 충분히 잠겼는가`
   - 시나리오가 그럴듯한 것과 crop selection으로 넘겨도 되는 것은 다르다.

2. `public genome fail-fast risk`
   - 특히 `N2`, `P1`은 exact crop로 내려가면 `HF-0/HF-3` 리스크가 커질 수 있다.

3. `legal-governance route`
   - 케냐, 인도, 페루 모두 "규제가 없어서 쉬운 지역"이 아니다.
   - 각 국가권의 ABS / seed law / germplasm access를 실제 조사 전 수준까지 잠글 수 있는지 확인이 필요하다.

4. `heroic assumption leakage`
   - 공공 프로그램이 알아서 흡수한다
   - partner를 구하면 된다
   - 대기업이면 해결 가능하다
   같은 가정이 baseline에 숨어 있지 않은지 봐야 한다.

---

## 5차 검증 패키지 상태

### 패키지 폴더

- `운영지원_통합\03_배포세트\20_신기준_시나리오검증세트`

### 포함 문서

1. `00-01_문제정의_PBL원문.md`
2. `21-01_신기준_시나리오선정기준_강화본.md`
3. `30-01_검증대상정리_현재시나리오삼안.md`
4. `60-01_판정결과_시나리오축소검증.md`
5. `20-01_신원칙_PBL우선원칙과추가시나리오.md`
6. `50-01_조사결과_시나리오병렬조사.md`
7. `40-01_검증실행_시나리오검증프롬프트.md`

### 패키지 목적

- 이 패키지는 `레드팀 시나리오 검증`용이다.
- 목적은 shortlist 시나리오 세트를 통과시키는 것이 아니라, 지금 상태에서 crop selection 단계로 넘어가도 되는지 막판 감사하는 것이다.

---

## 지금 당장 할 일

### 메인 액션

- 5차 검증 패키지를 사용해 레드팀 검증을 보낸다.

### 검증 질문

핵심 질문은 하나다.

> 현재 `N1 / N2 / P1` 시나리오 세트가 crop selection 단계로 넘어갈 만큼 충분히 잠겼는가?

검증 결과는 아래 셋 중 하나로 받아야 한다.

- `yes`
- `conditional yes`
- `no`

---

## 향후 계획

### Plan A. 결과가 `yes`

- 시나리오 잠금 완료로 간주한다.
- 바로 crop selection 단계로 이동한다.
- 순서는 아래와 같다.
  1. accepted scenario만 확정
  2. 시나리오별 crop-group long list 생성
  3. `HF-0 -> HF-9` 순서로 작물 hard filter
  4. surviving candidate만 shortlist로 이동

### Plan B. 결과가 `conditional yes`

- 조건부 잠금으로 간주한다.
- 레드팀이 요구한 blocker만 먼저 보완한다.
- blocker가 작은 경우:
  - 시나리오는 유지
  - 부족한 legal / delivery / HF-0 memo만 보강
- blocker가 구조적인 경우:
  - 해당 시나리오는 hold
  - 나머지 시나리오로만 crop selection 진입 여부 재판단

### Plan C. 결과가 `no`

- 시나리오 잠금 실패로 간주한다.
- 즉시 crop selection으로 가지 않는다.
- 레드팀 finding을 바탕으로 다음 중 하나를 수행한다.
  1. `N1 / N2 / P1` 중 문제 시나리오 드롭
  2. 남은 시나리오만으로 재검토
  3. 필요하면 narrow scenario를 다시 열되, 이전 broad lane으로 후퇴하지는 않는다.

---

## 세 세션 운용 메모

세 세션을 병렬로 쓸 경우 추천 역할 분리는 아래와 같다.

### Session 1

- 메인 레드팀 검증 송부 및 결과 수신
- 가장 권위 있는 세션
- 여기서 받은 `yes / conditional yes / no`가 최종 분기점이 된다

### Session 2

- 레드팀 결과가 오면 즉시 finding 정리
- 각 finding을
  - `바로 수정 가능`
  - `추가 공식 출처 필요`
  - `시나리오 구조 문제`
  로 분류

### Session 3

- crop selection 진입 준비 세션
- 단, 레드팀 결과가 나오기 전까지는 작물 선정 확정 작업을 하지 않는다
- 할 수 있는 준비는 아래까지만:
  - 시나리오별 crop-group long list 템플릿 준비
  - HF-0 prescreen 템플릿 준비
  - 공식 source bucket 정리

중요:
- Session 3는 준비만 하고, `작물 추천`이나 `ranking 확정`으로 먼저 가면 안 된다.

---

## 현재 결론

현재 상태는 `시나리오 작업이 거의 잠겼지만, 아직 공식 close 전`이다.

정확히는:
- 시나리오 세트는 충분히 좁혀졌다.
- 5차 레드팀 검증 패키지까지 준비되었다.
- 이제 필요한 것은 "좋아 보이는 설명"이 아니라, 실제로 crop selection으로 넘어가도 되는지 마지막으로 깨보는 검증이다.

즉 다음 관문은 `시나리오 창작`이 아니라 `시나리오 감사`다.
