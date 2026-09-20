# sbim — agent memory

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
