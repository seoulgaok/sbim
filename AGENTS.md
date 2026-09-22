# sbim — agent memory

## 속성 창은 세 묶음이다 (#10 ①②)

- `design`(이 설계에서 고르는 것) · `standards`(회사 표준) · `business`(사업성). 도면을
  만들 때 마주하는 건 `design`뿐이다. 새 필드를 넣을 때 이 셋 중 어디인지 먼저 정한다.
- 묶음은 **대상**이다(매스·세대·코어·주차·동선·외장). 단계로 자르면 같은 대상이 두 집에
  나뉜다 — 구 `GroundFloor`가 그 실패였다(주차·코어·동선·기둥 21필드 한 서랍).
- 치수는 표준이다(`standards.dimensions`) — 칸 폭·스팬·캔틸레버는 사업마다 고르지 않는다.
- 구 13블록 모양(`ground_floor`·`concrete`·`windows` …)은 `_migrate_legacy_shape`가 받아서
  옮긴다. 저장된 설계안과 DB jsonb가 옛 경로라 이 이행층을 지우면 기존 데이터가 깨진다.

## 엔진에는 "더 좋다"가 없다 (#12)

- 엔진 = f(대지, 속성 창) → 도면. 엔진이 아는 것은 **법과 물리의 된다/안 된다**뿐이다.
  취향은 **첫수표**(속성 창의 `None`을 채우는 표, giga `prior.py::FirstMove`)에만 산다.
- 그래서 옵션 설명에 「엔진이 평가해 채택한다」류를 쓰지 않는다 — `None=첫수표가 정한다`.
  명세가 탐색을 시키면 엔진이 그대로 따라 **소장 값을 받고도 안 믿는다**(값을 넣으면 대수가
  줄었다: `core_type` 25→22, `road_edge` 4→2). 가드는 `tests/test_options_axiom.py`.
- derive(법·기하가 한 값을 계산)와 취향(첫수표가 채움)은 다르다 — `road_edge`·`exit_road`는
  derive, `parking_axis`·`core_side`는 취향.

## `BuildOptions`는 속성 창이다 (#8)

- 서울가옥 = 게임메이커, Revit = 유니티. 무엇이든 만들게 하지 않고 **만들 수 있는 것을 정해
  두고 고르게** 한다. `BuildOptions`는 그 속성 창, giga 어휘는 오브젝트 라이브러리.
- 그래서 값·필드 이름은 **고르는 사람의 말**로 짓는다 — 엔진 구현이 이름으로 새면 안 된다
  (`parking_axis="core"`가 그 사례). 설명도 엔진 동작이 아니라 도면에서 보이는 생김새로 쓴다.
- 다만 **라이브러리에 있다고 다 속성 창에 올리지 않는다.** 엔진이 특례로 갖는 갈래와 소장이
  고르는 선택은 다르다 — 내부 차로 방식 넷에 이름을 줬다가 하루 만에 되돌렸다(#9 → #10 ④).
  소장 GT는 방식을 고르지 않고 한 방식 안에서 직각·평행을 **섞고** 있었다(12필지 중 9).
  새 어휘에 이름을 주기 전에 **소장 도면에서 그게 선택으로 나타나는지** 먼저 센다.
- `parking_axis`의 축은 `road`·`inner` 둘뿐이다. 구 `"core"`는 제거됐고 **거부**한다 —
  giga `manual_options.json`의 이태원동 303-22가 이 값을 심고 있어, 그 줄과
  `stalls.py::stage_core_axis`를 함께 걷어내야 한다.
- 「자동」의 표기는 `None` 하나다. legacy `"auto"`는 `_fold_legacy_auto`가 받아서 접는다 —
  구 저장값 51건이 심고 있어 거부하면 통째로 깨진다. 자동 가능 여부는
  `json_schema_extra={"auto": True}`로 표시한다(산문 description에 묻지 않는다).

## 코어 배향 — `GroundFloor.core_rotation` (#4)

- `core_rotation`(0/90/180/270)이 코어 배향의 정본이다. `core_axis`(road/depth)는
  deprecated — 절반 지정(road↔{0,180}, depth↔{90,270})으로 남는다.
- 이행 규칙(`GroundFloor._sync_core_axis`): `core_rotation` 명시 시 legacy
  `core_axis`로 자동 동기화, 둘 다 주고 모순되면 에러.
- 구 `reference/sbim/*/_build_options.json` 17필지가 `core_axis`를 심고 있다 —
  뜻을 바꾸지 않는 것이 이행의 조건. `core_axis`를 리팩터로 제거하기 전에
  building-generator 소비처가 `core_rotation`으로 정규화돼 있어야 한다
  (그 소비처 마이그레이션은 별도 작업: `shared/modules/aaro/prior.py`,
  `core_stage.py`).

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
