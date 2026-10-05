# sbim — agent memory

## 속성 창은 세 묶음이다 (#10 ①②)

- `design`(이 설계에서 고르는 것) · `standards`(회사 표준) · `business`(사업성). 도면을
  만들 때 마주하는 건 `design`뿐이다. 새 필드를 넣을 때 이 셋 중 어디인지 먼저 정한다.
- 묶음은 **대상**이다(매스·세대·코어·주차·동선·외장). 단계로 자르면 같은 대상이 두 집에
  나뉜다 — 구 `GroundFloor`가 그 실패였다(주차·코어·동선·기둥 21필드 한 서랍).
- 치수는 표준이다(`standards.dimensions`) — 칸 폭·스팬·캔틸레버는 사업마다 고르지 않는다.
- 구 13블록 모양(`ground_floor`·`concrete`·`windows` …)은 `_migrate_legacy_shape`가 받아서
  옮긴다. 저장된 설계안과 DB jsonb가 옛 경로라 이 이행층을 지우면 기존 데이터가 깨진다.

## 속성 창 정리 — 수만 남긴다 (2026-09-28)

- 옵션 = 설계자가 두는 **수**뿐이다. 법은 엔진 상수(주차 칸·차로 치수), 대수는 결과,
  엔진이 안 읽는 키는 두지 않는다. 한 뜻에 한 이름(`interior_aisle`→`parking_axis`).
- 지운 키는 **거부하지 않고 받아서 버린다**(`_drop`·각 모델의 before validator) — 옮길
  자리가 있으면 옮긴다(`far_target`→`far_limit_override`, 옛 자리 → `regulations`).
  옛 평평한 모양(`ground_floor`)도 `_migrate_legacy_shape`·`_GF_TO`로 같은 새 모양에 떨어진다.
- 법이 정하는 값을 필지 사정으로 덮어쓰는 것은 전부 `design.regulations`(법규 보정)다 —
  설계 묶음에 섞지 않는다.
- TS `BuildOptions`는 **생성물**이다(`python/scripts/gen_build_options.py` →
  `schema/build_options.schema.json` → `typescript/src/options.ts`). 옵션을 바꾸면 생성을
  돌리고 dist를 굽는다 — `test_build_options_schema.py`가 어긋남을 잡는다.

## 엔진에는 "더 좋다"가 없다 (#12)

- 엔진 = f(대지, 속성 창) → 도면. 엔진이 아는 것은 **법과 물리의 된다/안 된다**뿐이다.
  취향은 **첫수표**(속성 창의 `None`을 채우는 표, giga `prior.py::FirstMove`)에만 산다.
- 그래서 옵션 설명에 「엔진이 평가해 채택한다」류를 쓰지 않는다 — `None=첫수표가 정한다`.
  명세가 탐색을 시키면 엔진이 그대로 따라 **소장 값을 받고도 안 믿는다**(값을 넣으면 대수가
  줄었다: `core_type` 25→22, `road_edge` 4→2). 가드는 `tests/test_options_axiom.py`.
- derive(법·기하가 한 값을 계산)와 취향(첫수표가 채움)은 다르다 — `road_edge`·`exit_road`는
  derive, `parking_axis`·`core_side`·`mass_axis`(매스 작업축, #15)는 취향.

## `BuildOptions`는 속성 창이다 (#8)

- 서울가옥 = 게임메이커, Revit = 유니티. 무엇이든 만들게 하지 않고 **만들 수 있는 것을 정해
  두고 고르게** 한다. `BuildOptions`는 그 속성 창, giga 어휘는 오브젝트 라이브러리.
- 그래서 값·필드 이름은 **고르는 사람의 말**로 짓는다 — 엔진 구현이 이름으로 새면 안 된다
  (`parking_axis="core"`가 그 사례). 설명도 엔진 동작이 아니라 도면에서 보이는 생김새로 쓴다.
- 다만 **라이브러리에 있다고 다 속성 창에 올리지 않는다.** 엔진이 특례로 갖는 갈래와 소장이
  고르는 선택은 다르다 — 내부 차로 방식 넷에 이름을 줬다가 하루 만에 되돌렸다(#9 → #10 ④).
  소장 GT는 방식을 고르지 않고 한 방식 안에서 직각·평행을 **섞고** 있었다(12필지 중 9).
  새 어휘에 이름을 주기 전에 **소장 도면에서 그게 선택으로 나타나는지** 먼저 센다.
- 「자동」의 표기는 `None` 하나다. 자동 가능 여부는 `json_schema_extra={"auto": True}`로
  표시한다(산문 description에 묻지 않는다).
- **주차 버블이 대신한 세 필드는 삭제됐다(2026-10-05)** — `parking_axis`·`road_edge`·
  `multi_road`·`interior_aisle`. building-generator 가 어디서도 읽지 않고 REF 48 필지가
  전부 버블 경로로 까는 것이 전제였다. 저장값에 남아 있는 키는 `Parking._fold_legacy`가
  조용히 버린다(거부하지 않는다 — 구 `"auto"`·`"core"` 값도 같이).

## 주차 버블 — `Parking.parking_graph` (2026-09-29)

- **버블 = (진입 도로 방위 dir8, road|yard|aisle) 튜플의 배열** — 위상만 담는다. 방위는 항상
  8방위(null 없음, 2026-09-29) — 필지에서 본 진입 자리의 위치(core_side 와 같은 규칙:
  정방위=그쪽 변 도로 가운데부터, 대각=그 모서리 도로 끝부터 검토; 주접도도 그 방위로
  적는다). 둘째 = 그 도로에서 까는 모양: `road` 도로 앞 한 줄(도로가 곧 차로), `yard` 대지 안
  마당(빈터를 칸이 두 방향 이상, 서로 다른 축에서 둘러싼다), `aisle` 대지 안 곧은 차로(칸이 한
  축으로만 — 마주보는 두 줄 또는 한 줄). **yard 와 aisle 의 판정은 칸 진입 방향의 축 수**(45°
  미만은 같은 축) — REF 40필지 재독에서 옛 `yard` 24개 중 15개가 곧은 차로였다(화곡 1033-19
  alt2 는 세 면 마당, alt3 는 같은 자리의 차로). 배열
  순서 = 놓는 순서. 예: 성북 `["n","road"],["sw","yard"]` · 연희
  `["nw","yard"],["sw","yard"]`.
- **칸 수는 입력이 아니다 — 대수는 결과다.** stalls 를 주자 엔진이 「이 도로에 정확히
  8대」를 못 맞추면 실패로 떨어졌다. 칸 수·면 자리(far/left/right/near)·정렬·via·노드
  연접은 전부 지웠다 — 연접은 `parking.tandem`, 나머지는 엔진이 정한다. 좌표·치수도
  넣지 않는다(법 상수·코어 축).
- 구 노드(dict) 저장값은 kind·road_side 만 튜플로 옮겨 받고 나머지는 버린다(`_fold_legacy`) —
  road_side 없는 노드를 만나면 방위를 지어내지 않고 그래프 전체를 버린다(None).
- `parking_axis`와의 모순은 **거부하지 않는다** — REF 추출 축과 버블이 갈리는 필지가 있고
  엔진이 버블을 다 읽기 전까지 옛 경로가 그 축을 쓴다.
- 버블이 뜻을 대신 가져간 `parking_axis`·`road_edge`·`multi_road` 는 **삭제됐다**(2026-10-05,
  전제: building-generator PR #346 머지 + REF 48 필지 전부 버블 경로) — 저장값의 키는
  `_fold_legacy`가 조용히 버린다.
- 엔진은 road → yard → 섞임 순으로 붙이고, 모든 튜플을 지원할 때만 버블을 읽는다(아니면
  통째로 무시) — 일부만 읽으면 옵션이 가짜 필드가 된다. `aisle` 는 뒤에 늘어난 셋째 종류 —
  추출기와 엔진(building-generator)이 이 값을 다루기 전까지는 속성 창만 열려 있다.

## 코어 배향 — `Core.core_rotation` · `Core.core_mirror` (#4, #13)

- `core_rotation`(0/90/180/270)이 코어 회전의 **유일한** 표현이다. 구 `core_axis`(road/depth)는
  같은 뜻을 두 정밀도로 받는 중복이라 제거됐다.
- 들어오면 **버린다**(거부하지 않는다) — 절반 지정이라 회전각으로 못 옮기고, 거부하면 구
  `_build_options.json` 19필지가 안 열린다. 비면 첫수표가 정한다.
- 그 19필지의 배향을 되살리려면 giga가 회전각을 다시 재어 `core_rotation`으로 심어야 한다.
- 손잡이는 `core_mirror`(좌우 뒤집기)가 따로 받는다 — 회전으로는 거울이 안 나온다(회전 180°는
  복도 면까지 옮긴다). 뒤집기를 먼저, 회전을 나중에: 둘로 코어가 변에 앉는 여덟 자세를 전부
  적는다. 옛 giga 엔진은 90·270을 한 축 뒤집기로 처리해 거울을 회전값 속에 숨겨 적었다.

## 코어 유형 번호 — 2026-09 개번 (#2)

- 번호의 정본은 building-generator `shared/modules/aaro/core_library.json`이다.
  2026-09 DWG 시트 순서 개번(#190)은 **그 저장소에서 머지된 뒤**에 유효하다.
- 옛→새 표는 `options.CORE_TYPE_RENUMBER_2026_09`(`migrate_core_type()`)가 정본.
  값 집합이 1~7로 같아 검증에 걸리지 않으니, 저장된 값은 반드시 이 표로 옮긴다.
- 구 `reference/sbim/*/_build_options.json` 중 `core.type=2`인 2필지가 여기 해당한다
  (옛 2 = 새 1).
- 라이브러리 캡션은 아직 옛 이름이다 — sbim 설명은 외곽 형태(세장형·정방형·ㄱ자형)
  + 괄호 계단 형식으로 통일했고, 라이브러리 캡션 정렬은 별도 작업.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
