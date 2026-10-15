"""pydantic 정본 → schema/*.json + typescript/src/options.ts + fixtures/.

정본은 pydantic 둘이다 — `BuildOptions`(options.py)와 scheme·units·surroundings 계약
(types.py). 이 스크립트가 거기서 JSON Schema 를 뽑고, BuildOptions 는 스키마에서 TS 타입을
**생성**한다 — 손으로 베끼면 갈린다(소비처 nextbase가 SbimStudio.tsx에 속성 창을 재정의해
두었다가 sbim과 어긋난 게 이 파일의 이유). types.ts 는 손판이라 만들지 않는다 —
`tests/test_types_parity.py` 가 필드 집합을 지킨다.

    cd python && uv run python scripts/gen_build_options.py          # 쓴다
    cd python && uv run python scripts/gen_build_options.py --check  # 어긋나면 1로 끝난다

쓰는 것:
- schema/build_options.schema.json · typescript/src/options.ts  (BuildOptions)
- schema/scheme.schema.json (Scheme) · schema/units.schema.json (UnitRecord 배열) ·
  schema/surroundings.schema.json (SurroundingBuilding 배열) · schema/site.schema.json (SiteInfo)
- fixtures/build_options/<case>.json — 소비처(Elixir·Rust·TS)가 같은 정답으로 검사하는
  입력→정규화 BuildOptions 짝(`FIXTURE_CASES`). fixtures/core_type_renumber.json — 코어 번호 개번 표.
  fixtures/migrations.json — 이행 표, fixtures/presets.json — STRUCTURE_PRESET.
- rust/sbim-types/src/*.rs · elixir/sbim/lib/sbim/generated/*.ex — 언어별 방출기(emit_rust.py ·
  emit_elixir.py)가 같은 묶음(`bundle()`)에서 쓴다. 기본값은 `empty` fixture 의 expected 에서.

옵션을 바꾸면 이걸 돌리고 `pnpm -r build`로 dist를 다시 굽는다. `tests/test_build_options_schema.py`·
`tests/test_fixtures.py`가 생성물이 정본과 같은지 지킨다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import TypeAdapter

from seoulgaok_bim_core import options as O
from seoulgaok_bim_core.options import CORE_TYPE_RENUMBER_2026_09, BuildOptions
from seoulgaok_bim_core.types import Scheme, SiteInfo, SurroundingBuilding, UnitRecord

# 언어별 방출기 — 같은 스키마 묶음을 받아 rust/·elixir/ 를 쓴다. 이 디렉터리를 경로에 올려
# 스크립트로 돌리든 테스트가 spec 으로 읽든 같은 모듈이 잡히게 한다.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import emit_elixir  # noqa: E402
import emit_rust  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_FIXTURE_PATH = ROOT / "fixtures" / "migrations.json"
PRESETS_FIXTURE_PATH = ROOT / "fixtures" / "presets.json"
SCHEMA_DIR = ROOT / "schema"
SCHEMA_PATH = SCHEMA_DIR / "build_options.schema.json"
SCHEME_SCHEMA_PATH = SCHEMA_DIR / "scheme.schema.json"
UNITS_SCHEMA_PATH = SCHEMA_DIR / "units.schema.json"
SURROUNDINGS_SCHEMA_PATH = SCHEMA_DIR / "surroundings.schema.json"
SITE_SCHEMA_PATH = SCHEMA_DIR / "site.schema.json"
TS_PATH = ROOT / "typescript" / "src" / "options.ts"
FIXTURES_DIR = ROOT / "fixtures" / "build_options"
CORE_TYPE_FIXTURE_PATH = ROOT / "fixtures" / "core_type_renumber.json"

HEADER = """\
/**
 * BuildOptions — 속성 창 입력 타입. **생성 파일 — 손으로 고치지 마라.**
 *
 * 정본: python/seoulgaok_bim_core/options.py (pydantic BuildOptions)
 * 생성: cd python && uv run python scripts/gen_build_options.py
 *       (schema/build_options.schema.json 을 거쳐 이 파일을 쓴다)
 *
 * 거의 모든 필드가 옵셔널이다 — 비우면 sbim 기본값(대부분 None=첫수표가 정한다)이 채운다.
 * 필수는 목록 항목 안쪽뿐이다(주차 버블 튜플의 둘째 값 road|yard|aisle).
 * 지운 키(core_along·interior_aisle·far_target …)는 서버가 받아서 버리거나 옮기지만,
 * 새로 보내는 값은 이 모양으로 보낸다.
 */
"""


# 비웠을 때 누가 정하나 — options.Design 의 `json_schema_extra={"empty": …}`
EMPTY_NOTE = {
    "auto": "None=첫수표가 정한다(resolved_options 에 나온다)",
    "law": "None=법이 정한다",
    "default": "None=설명에 적힌 기본 동작",
}


def schema() -> dict:
    return BuildOptions.model_json_schema()


def array_schema(model: type, title: str, description: str) -> dict:
    """루트가 배열인 파일(units.json·surroundings.json) — 항목은 `$defs` 의 모델을 가리킨다."""
    s = TypeAdapter(list[model]).json_schema()
    return {"title": title, "description": description, "type": "array",
            "items": s["items"], "$defs": s["$defs"]}


def scheme_schema() -> dict:
    return Scheme.model_json_schema()


def site_schema() -> dict:
    return SiteInfo.model_json_schema()


def units_schema() -> dict:
    return array_schema(UnitRecord, "Units", "units.json — 생성기 세대 레코드(UnitRecord) 배열.")


def surroundings_schema() -> dict:
    return array_schema(SurroundingBuilding, "Surroundings",
                        "surroundings.json — 주변 건물(SurroundingBuilding) 배열. 일조·시각화용.")


def _lit(v) -> str:
    return json.dumps(v, ensure_ascii=False)


def ts_type(s: dict) -> str:
    if "$ref" in s:
        return s["$ref"].rsplit("/", 1)[-1]
    if "anyOf" in s:
        parts = []
        for sub in s["anyOf"]:
            t = ts_type(sub)
            if t not in parts:
                parts.append(t)
        return " | ".join(parts)
    if "prefixItems" in s:
        return "[" + ", ".join(ts_type(sub) for sub in s["prefixItems"]) + "]"
    if "const" in s:
        return _lit(s["const"])
    if "enum" in s:
        return " | ".join(_lit(v) for v in s["enum"])
    t = s.get("type")
    if t == "null":
        return "null"
    if t == "string":
        return "string"
    if t in ("number", "integer"):
        return "number"
    if t == "boolean":
        return "boolean"
    if t == "array":
        inner = ts_type(s.get("items", {}))
        return f"({inner})[]" if "|" in inner else f"{inner}[]"
    if t == "object":
        ap = s.get("additionalProperties")
        if isinstance(ap, dict):
            return f"Record<string, {ts_type(ap)}>"
        return "Record<string, unknown>"
    return "unknown"


def _doc(notes: list[str], indent: str) -> list[str]:
    body = [ln.rstrip() for n in notes for ln in n.strip().split("\n")]
    while body and not body[-1]:
        body.pop()
    if not body:
        return []
    return ([f"{indent}/**"]
            + [f"{indent} * {ln}".rstrip().replace("*/", "*\\/") for ln in body]
            + [f"{indent} */"])


def interface(name: str, s: dict) -> list[str]:
    out = _doc([s.get("description", "")], "")
    out.append(f"export interface {name} {{")
    for prop, ps in s.get("properties", {}).items():
        notes = [ps.get("description", "")]
        if "default" in ps:
            notes.append(f"@default {_lit(ps['default'])}")
        if ps.get("empty"):
            notes.append(f"@empty {ps['empty']} — {EMPTY_NOTE[ps['empty']]}")
        # JSON Schema 표준 `deprecated` 키 — 값이 문자열이면 그 이유를 태그에 쓴다
        # (`json_schema_extra={"deprecated": "..."}` 또는 pydantic Field(deprecated=...)).
        dep = ps.get("deprecated")
        if dep:
            notes.append(f"@deprecated {dep}" if isinstance(dep, str) else "@deprecated")
        out += _doc([n for n in notes if n], "  ")
        opt = "" if prop in s.get("required", ()) else "?"
        out.append(f"  {prop}{opt}: {ts_type(ps)};")
    out.append("}")
    return out


def render_ts(sch: dict) -> str:
    defs = dict(sch.get("$defs", {}))
    root = {k: v for k, v in sch.items() if k != "$defs"}
    blocks = [interface(n, defs[n]) for n in sorted(defs)]
    blocks.append(interface(root["title"], root))
    return HEADER + "\n" + "\n\n".join("\n".join(b) for b in blocks) + "\n"


def render_json(obj) -> str:
    """키 순서는 그대로(sort_keys 금지) — fixture 의 expected 는 model_fields 선언 순서를 거울로
    삼는 포트(Elixir)가 읽는다."""
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


# ── fixtures — 입력(저장돼 들어오는 raw dict) → 정규화된 BuildOptions ─────────────────
# 각 케이스는 작은 입력 하나다. expected 는 BuildOptions.model_validate(input).model_dump(mode="json")
# — 개번(migrate_core_type)은 model_validate 가 하지 않으므로(값 집합이 같아 못 가린다) 여기 없다.
# 구 13블록 평면 모양은 tests/test_options_regroup.py 의 LEGACY 와 같다.
_LEGACY_FLAT = {
    "massing": {"target_floor_count": 6, "first_floor_height": 3.6},
    "units": {"units_per_floor": 3, "cut_axis": "depth"},
    "core": {"type": 2, "composition": "stair"},
    "structure": {"system": "rahmen"},
    "windows": {"style": "open"},
    "exterior": {"style": "brick"},
    "parking": {
        "count": 7, "ratio_mode": "non_residential",
        "stall_width": 2.6, "stall_depth": 5.2, "aisle_width": 6.5,
    },
    "ground_floor": {
        "core_side": "ne", "core_rotation": 90, "core_entries": 2,
        "parking_axis": "inner", "parking_angle": 45, "road_edge": 1,
        "entry2": True, "tandem": False, "bk_offset": 5.5,
        "interior_aisle": True, "exit_road": 0, "road_setback": 1.5,
        "corridor_mode": "edge", "pedestrian_width": 1.8,
        "commercial_remainder": True,
        "max_span": 7.2, "cantilever": 1.4, "min_col_dist": 3.1,
        "preferred_min_span": 4.2,
    },
    "concrete": {"wall_thickness": 0.22, "price_per_m3": 190000},
    "schedule": {"construction_months": 14},
    "financing": {"land_loan_ltv": 0.7},
    "regulations": {"bcr_target": 58.0},
}

FIXTURE_CASES: dict[str, dict] = {
    # 기본값 전부 — max_span 8.0/8.1 같은 기본값 사고를 이것 하나가 잡는다
    "empty": {},
    # STRUCTURE_PRESET — 벽두께·스팬·기둥 간격이 구조방식에서 채워진다
    "structure_wall": {"design": {"structure": "wall"}},
    "structure_rahmen": {"design": {"structure": "rahmen"}},
    "structure_steel": {"design": {"structure": "steel"}},
    # 명시 값은 프리셋을 이긴다
    "structure_steel_explicit_span": {
        "design": {"structure": "steel"},
        "standards": {"dimensions": {"max_span": 9.0}},
    },
    # 구 13블록 평면 모양 — `_migrate_legacy_shape`·`_GF_TO`
    "legacy_ground_floor": _LEGACY_FLAT,
    # 구 평면 모양의 financing 에 남은 분양 필드(`_DROPPED`) — 받아서 버린다
    "legacy_financing_dropped_keys": {
        "financing": {"land_loan_ltv": 0.6, "deposit_pct": 0.1, "presale_period": 6},
    },
    # 구 parking_graph 노드(dict) → (방위, kind) 튜플 — 칸 수·연접은 버린다
    "parking_graph_legacy_nodes": {"design": {"parking": {"parking_graph": [
        {"kind": "road", "road_side": "n", "stalls": 5, "tandem": True},
        {"kind": "yard", "road_side": "sw"},
    ]}}},
    # 방위 없는 구 노드가 하나라도 있으면 그래프 전체를 버린다(None)
    "parking_graph_legacy_nodes_without_side": {"design": {"parking": {"parking_graph": [
        {"kind": "road", "road_side": "n"},
        {"kind": "yard", "rows": [{"side": "far", "stalls": 2}]},
    ]}}},
    # 구 이름 → 새 이름(`_REG_RENAMED`), 옛 자리 → regulations(`_TO_REGULATIONS`)
    "regulations_renamed": {"design": {
        "regulations": {"far_target": 230.0, "bcr_target": 55.0},
        "parking": {"road_setback": 0.5, "ratio_mode": "non_residential"},
        "circulation": {"pedestrian_width": 1.8},
    }},
    # 새 모양에 섞여 온 지운 키 — 거부하지 않고 버린다
    "dropped_keys": {
        "design": {
            "massing": {"target_floor_count": 5, "commercial_remainder": True},
            "units": {"units_per_floor": 4, "cut_axis": "road"},
            "core": {"type": 1, "core_axis": "road", "core_along": "mid", "composition": "stair"},
            "parking": {
                "count": 6, "type": "perpendicular", "bk_offset": 5.5, "interior_aisle": True,
                "parking_axis": "auto", "road_edge": 2, "multi_road": True, "tandem": True,
            },
        },
        "standards": {"dimensions": {"stall_width": 2.6, "stall_depth": 5.2,
                                     "aisle_width": 6.5, "preferred_min_span": 4.2}},
    },
}


def fixture(raw: dict) -> dict:
    return {"input": raw,
            "expected": BuildOptions.model_validate(raw).model_dump(mode="json")}


def core_type_fixture() -> dict:
    """코어 번호 개번 표(2026-09) — 저장값의 core.type 은 소비처가 읽을 때 이 표로 옮긴다."""
    return {"old_to_new": {str(k): v for k, v in CORE_TYPE_RENUMBER_2026_09.items()}}


def migrations_fixture() -> dict:
    """옛 저장값을 새 모양으로 옮기는 표 — 코드가 아니라 데이터로 내보내 모든 언어가 같은 표를
    적용한다(파이썬은 `BuildOptions._migrate_legacy_shape`·각 모델의 before validator)."""
    return {
        "legacy_top_blocks": list(O._LEGACY_TOP),
        "ground_floor_to": dict(O._GF_TO),
        "ground_floor_dropped": sorted(O._GF_DROPPED),
        "parking_dims_dropped": list(O._PARKING_DIMS),
        "renamed": dict(O._RENAMED),
        "regulations_renamed": dict(O._REG_RENAMED),
        "moved_to_regulations": [list(p) for p in O._TO_REGULATIONS],
        "dropped": {k: list(v) for k, v in O._DROPPED.items()},
        "core_type_old_to_new": core_type_fixture()["old_to_new"],
    }


def bundle() -> dict:
    """방출기들이 받는 묶음 — 스키마와 표 전부."""
    return {
        "build_options": schema(),
        "scheme": scheme_schema(),
        "units": units_schema(),
        "surroundings": surroundings_schema(),
        "site": site_schema(),
        "migrations": migrations_fixture(),
        "structure_preset": {k: dict(v) for k, v in O.STRUCTURE_PRESET.items()},
        "fixtures": {name: fixture(raw) for name, raw in FIXTURE_CASES.items()},
    }


def outputs() -> dict[Path, str]:
    b = bundle()
    sch = b["build_options"]
    want = {
        SCHEMA_PATH: render_json(sch),
        TS_PATH: render_ts(sch),
        SCHEME_SCHEMA_PATH: render_json(b["scheme"]),
        UNITS_SCHEMA_PATH: render_json(b["units"]),
        SURROUNDINGS_SCHEMA_PATH: render_json(b["surroundings"]),
        SITE_SCHEMA_PATH: render_json(b["site"]),
        CORE_TYPE_FIXTURE_PATH: render_json(core_type_fixture()),
        MIGRATIONS_FIXTURE_PATH: render_json(b["migrations"]),
        PRESETS_FIXTURE_PATH: render_json({"structure_preset": b["structure_preset"]}),
    }
    for name, fx in b["fixtures"].items():
        want[FIXTURES_DIR / f"{name}.json"] = render_json(fx)
    want.update(emit_rust.outputs(ROOT, b))
    want.update(emit_elixir.outputs(ROOT, b))
    return want


def main(argv: list[str]) -> int:
    want = outputs()
    if "--check" in argv:
        stale = [p for p, txt in want.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != txt]
        for p in stale:
            print(f"낡음: {p.relative_to(ROOT)} — gen_build_options.py 를 다시 돌려라")
        unknown = sorted(set(FIXTURES_DIR.glob("*.json")) - set(want)) if FIXTURES_DIR.exists() else []
        for p in unknown:
            print(f"모르는 fixture: {p.relative_to(ROOT)} — FIXTURE_CASES 에 없다, 지워라")
        return 1 if stale or unknown else 0
    for p, txt in want.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
        print(f"썼다: {p.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
