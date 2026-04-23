## Comparison Basis

provisional only, not final.

- 이번 bounded comparison은 로컬에서 standalone `P3/P4/P5 result md`가 따로 확인되지 않아서, 현재 그 결과가 합쳐져 있는 operative artifact인 [03-25_부분재검증준비_증거수집통합_2026-04-22.md](</C:/Users/skyhu/Desktop/AI 와 유전체학/최신 상황/03_검증프롬프트와설정/03-25_부분재검증준비_증거수집통합_2026-04-22.md:140>)를 기준으로 읽었다.
- 비교 축은 `buyer-side specificity`, `genome-core burden`, `legal/value-capture burden` 3개로 고정했다.
- `generic pulse demand`는 두 작물 모두의 배경 수요 신호일 뿐이고, crop-specific buyer lock으로 올려 읽지 않았다.
- `genome-core burden`과 `buyer-side burden`은 분리했고, `legal/value-capture burden`도 별도 층으로 두었다.
- 현재 `HF-0 / HF-3 / HF-4 / HF-7`는 lentil, urdbean 둘 다 `PENDING`이고, `G2`와 `G8`도 아직 필드 분리가 안 끝나서 닫힌 lane은 없다.
- 그래서 이번 메모의 목적은 winner 선언이 아니라, `N2` 내부에서 어느 쪽이 어떤 종류의 signal을 더 갖고 있나만 bounded하게 적는 것이다.

## Lens Side Summary

- `lentil/masur`는 buyer-side evidence가 아예 없는 것은 아니다. `NAFED Bharat Masur Dal`, `NCCF masur tender`, `TNCSC tender`처럼 crop명이 보이는 procurement-retail route는 확인되어 있다.
- 다만 이건 `lentil-specific named route exists` 정도지, `national lentil buyer lock exists`까지는 아니다. 통합 artifact도 `national lentil buyer lock = not yet`로 읽고 있다.
- 그래서 lentil 쪽 약점은 수요 부재가 아니라 `payer / budget holder / procurement buyer / technical user / delivery controller / acceptance criterion`이 아직 정확히 분해되지 않았다는 점이다. 즉 buyer map이 존재하지만, `G2/G8` closure가 안 됐다.
- genome-core 쪽에서는 `Lens culinaris`에 이미 public reference assembly가 있다. 그래서 lentil의 질문은 `genome이 없나?`가 아니라 `existing public resource로는 왜 exact benchmark/use-case가 아직 안 풀리나?`로 바뀐다.
- 그 말은 lentil이 genome-core에서 바로 carry되는 구조가 아니라는 뜻이다. `HF-0 / HF-3 / HF-4 / HF-7`을 benchmark-use-case 기준으로 다시 닫아야 한다.
- legal/value-capture 쪽에서 lentil만의 별도 우위도 아직 안 보인다. 현재 `N2` legal burden은 crop-specific differentiator라기보다 공통 pending burden에 가깝다.

## Urd Side Summary

- `urad/urdbean/black gram`은 buyer-side에서 lentil보다 한 단계 더 직접적이다. 통합 artifact 기준으로 `Tamil Nadu school meal`, `co-op/PDS`, `NAFED sale` 같은 named program/procurement 흔적이 바로 보인다.
- 그래서 buyer-side만 놓고 보면 urdbean은 `named crop line`이 좀 더 직선적으로 보이고, lane ledger에도 사실상 그 차이가 반영되어 있다. 현재 `N2 x Vigna mungo`는 `buyer-side stronger than lentil`로 적혀 있다.
- 하지만 이것도 아직 `exact buyer lock`은 아니다. urdbean도 마찬가지로 `budget holder`, `procurement buyer`, `technical user`, `delivery controller`, `transaction object`, `acceptance criterion`이 아직 fully split되지 않았다.
- genome-core 쪽에서는 `Vigna mungo`도 이미 public draft genome이 있다. 그래서 urdbean 역시 `new genome necessity`를 benchmark-use-case 기준으로 다시 증명해야 한다.
- 즉 urdbean의 상대 우위는 지금 단계에서 `buyer-side clarity` 쪽이지, `genome-core simplicity` 쪽은 아니다. genome hard gate는 lentil과 거의 같은 종류의 pending burden을 안고 있다.
- legal/value-capture 쪽에서도 urdbean만 따로 더 가볍다거나 더 무겁다는 근거는 아직 없다. 현재로선 `N2` 공통 burden으로 보는 게 맞다.

## N2 Provisional Carry Signal

- 지금 `N2` 내부에서 보이는 provisional carry signal은 `buyer-side only`로는 `urdbean` 쪽이다.
- 이유는 `urdbean`이 lentil보다 crop명이 직접 박힌 named program/procurement 흔적이 조금 더 선명해서, `generic pulse demand`에서 `crop-specific route`로 내려오는 선이 더 짧기 때문이다.
- 반대로 `lentil`은 route는 있지만 아직 `national lentil buyer lock`까지 닫히지 않아서, buyer-side에서 한 단계 더 설명이 필요하다.
- 다만 이 carry signal은 `overall N2 carry candidate` 선언이 아니다. `genome-core burden`은 두 작물 다 아직 무겁고, `legal/value-capture burden`도 둘 다 공통 pending이어서, buyer-side 우위만으로 lane을 잠그면 과잉 해석이 된다.
- 그래서 현재 수렴은 이렇게 적는 것이 가장 안전하다: `urdbean has the stronger provisional buyer-side carry signal, but N2 overall remains reopen-required before scoring`.

## N2 Reopen Questions

- lentil과 urdbean 각각에 대해 `payer / budget holder / procurement buyer / technical user / delivery controller / transaction object / acceptance criterion`를 분리해서 `G2`와 `G8`을 실제로 닫을 수 있는가?
- `Lens culinaris`의 existing public reference assembly와 `Vigna mungo`의 existing public draft genome이 각각 어떤 exact benchmark/use-case에서 insufficient한가? 이걸 `HF-0 / HF-3 / HF-4 / HF-7` 언어로 다시 써야 한다.
- lentil과 urdbean의 `source-holder / public-domain status`가 accession/material 단위에서 실제로 어떻게 다른가? 지금은 둘 다 legal route 판단의 핵심 unknown이다.
- `ITPGRFA / SMTA` route가 실제 material에 practical route로 작동하는지, 아니면 `Annex I` 수준의 favorable signal에 그치는지 crop별로 더 닫아야 한다.
- `PPV&FR Section 39` 아래에서 private seed-type value capture burden이 lentil과 urdbean 사이에 실질 차등을 만드는가, 아니면 둘 다 같은 방향의 burden인가?
- state-level named buyer concentration이 실제 `scenario-level absorbability`로 이어지는지, 아니면 단지 fragmentary named evidence인지도 아직 reopen 대상이다.
