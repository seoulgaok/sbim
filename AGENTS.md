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

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
