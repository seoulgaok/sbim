# fixtures — 소비처가 같은 정답으로 검사하는 파일

**생성 파일이다 — 손으로 고치지 마라.** 정본은 pydantic `BuildOptions`
(`python/seoulgaok_bim_core/options.py`)이고, 이 파일들은 거기서 뽑는다.

    cd python && uv run python scripts/gen_build_options.py          # 쓴다
    cd python && uv run python scripts/gen_build_options.py --check  # 갈리면 1

## build_options/<case>.json

```json
{ "input": <저장돼 들어오는 raw dict>, "expected": <정규화된 BuildOptions> }
```

- `expected` = `BuildOptions.model_validate(input).model_dump(mode="json")`. 키 순서는
  `model_fields` 선언 순서 그대로다(정렬하지 않는다 — Elixir 포트가 이 순서를 거울로 삼는다).
  `dict[int, …]` 필드(`floor_use`·`units_by_level`)의 키는 JSON 이라 문자열이다.
- 소비처(Elixir·Rust·TS) 테스트는 `input` 을 자기 모델에 넣고 결과가 `expected` 와 같은지
  본다. 케이스는 `gen_build_options.py` 의 `FIXTURE_CASES` 에 있다 — 기본값 전부(`empty`),
  구조 프리셋(`structure_*`), 구 평면 모양(`legacy_*`), 구 주차 노드(`parking_graph_legacy_*`),
  옮긴 법규 보정 이름(`regulations_renamed`), 지운 키 버리기(`dropped_keys`).
- `python/tests/test_fixtures.py` 가 정본으로 되검사하고, `typescript/tests/fixtures.test.ts`
  가 `expected` 의 키가 전부 `BuildOptions` 타입(options.ts) 안에 있는지 본다.

## core_type_renumber.json

코어 유형 번호 개번 표(2026-09, building-generator #190) `{"old_to_new": {"1": 2, …}}`.
값 집합이 1~7 로 같아 `BuildOptions` 검증으로는 걸리지 않는다 — 저장값의 `core.type` 은
소비처가 읽을 때 이 표로 옮긴다(파이썬은 `migrate_core_type()`).

## migrations.json

옛 저장값을 새 모양으로 옮기는 표 — 파이썬 `options.py` 의 `_LEGACY_TOP`·`_GF_TO`·`_GF_DROPPED`·
`_PARKING_DIMS`·`_RENAMED`·`_REG_RENAMED`·`_TO_REGULATIONS`·`_DROPPED`·코어 개번표를 데이터로
낸 것이다. 이행 규칙을 코드로 베끼지 말고 이 표를 읽어 적용한다 — Rust·Elixir 판은 여기서
생성된 상수를 쓴다. 표로 못 적는 규칙(주차 버블 구 노드 접기 등)은 `build_options/` 케이스가
정답을 준다.

## 여기 없는 것

sbim 이 줄 수 있는 것은 입력 → 정규화된 `BuildOptions` 까지다. `resolved_options`
(첫수표가 채운 값)는 giga 엔진 쪽이라 여기 없다.
