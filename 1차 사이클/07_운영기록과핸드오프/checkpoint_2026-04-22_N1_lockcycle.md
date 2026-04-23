# Checkpoint 2026-04-22

## 현재 진행상황

- 프로젝트는 `crop-first`에서 `scenario-first` 구조로 이미 전환되었다.
- 기준표는 `최종_시나리오선정기준_v1.1.md`까지 수정되어 현재 조사 기준으로 사용 중이다.
- broad lane 조사 결과:
  - keep: `S1 SSA staple public/blended`
  - keep: `S3 protein-security grain-legume`
  - keep: `S4 climate-resilient forage/feed`
  - drop for now: `S2 hybrid horticulture`
- narrow scenario 검증 결과:
  - lead finalist: `N1 Kenya dairy forage resilience`
  - backup: `N2 India protein-security food-legume public route`
  - hold: `N3 East Africa public procurement dryland staple route`
- 아직 시나리오 선정 단계는 완전히 닫히지 않았다.
  이유는 `N1`이 `SG-5`, `SG-6`, `SG-7`, `SG-8` 일부에서 추가 잠금이 필요했기 때문이다.

## 이번 cycle의 목적

이번 cycle은 `N1`을 닫을 수 있는지 확인하는 마지막 lock cycle이다.

잠가야 하는 항목은 아래 5개다.

1. 정확한 forage subgroup 1개
2. germplasm source country
3. ABS / Treaty route
4. named delivery owner + fallback
5. public genome saturation memo

## 현재 판단 프레임

- `Brachiaria/Urochloa` 계열:
  - 장점: Kenya 공식 seed route, KALRO/KEPHIS 기반 등록·유통 논리가 상대적으로 선명함
  - 약점: 최근 public genome 축이 빠르게 채워져 `reference-genome necessity`가 약해질 위험이 있음
- `indigenous / drought-tolerant pasture grasses` 계열:
  - 장점: genome gap 가능성이 더 큼
  - 약점: commercial route가 더 공공형·프로그램형으로 기울 수 있어 delivery/payer를 더 정교하게 적어야 함

## 이번 cycle에서 사용할 판정 규칙

- `N1`에 `B`, `UNKNOWN`, `CONFLICT`가 남으면 시나리오 선정 단계는 닫지 않는다.
- `N1`이 실질적으로 잠기면 그 다음 단계는 `crop-group long-list` 생성이다.
- long-list는 시나리오 통과 뒤에만 만들고, 이후 `crop × scenario hard filter`로 넘어간다.
- 기존 shortlist를 정당화하는 방향으로 역으로 쓰지 않는다.

## 향후 계획

### Step 1. N1 마지막 lock cycle

- commercial lens:
  - Kenya 공식 livestock / feed / pasture seed 수요와 payer 구조 재확인
  - named delivery owner와 fallback 확인
- governance lens:
  - Kenya ABS/Nagoya/Seed law route 확인
  - breeder-source 예외 또는 permit 필요 여부 확인
- genome-science lens:
  - 후보 forage subgroup별 public genome saturation 비교
  - `reference-genome necessity`와 `technical feasibility`를 동시에 확인

### Step 2. 조건부 crop-group long-list

- Step 1에서 `N1`이 잠기면:
  - N1에 맞는 `crop-group long-list` 생성
  - 각 후보에 대해 `fit rationale`과 초기 위험 메모 부착
- Step 1에서 `N1`이 안 잠기면:
  - long-list 생성 보류
  - 남은 blocker만 정리하고 `N2`와 비교할지 판단

## 산출물 예정

- `시나리오 검증용/40_N1_심화검증/40-04_N1_락사이클정리.md`
- 조건 충족 시 `시나리오 검증용/N1_crop_group_longlist_v1.md`

## 메모

- 이번 턴에서는 에이전트를 `commercial`, `governance`, `genome-science` 3개 read-only 트랙으로 나눠 병렬 조사하고, 리드가 합성한다.
- 운영 방식은 `엔지니어링/meta-prompt-multi-agent-design-brief.md`의 `slim coordinator-worker`, `explicit responsibilities`, `artifact-first handoff` 원칙에 맞춘다.
