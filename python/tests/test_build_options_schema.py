"""생성물(schema/build_options.schema.json · typescript/src/options.ts)이 정본과 같은가.

TS 타입은 pydantic `BuildOptions`에서 생성한다 — 옵션을 바꾸고 생성을 안 돌리면 여기서
걸린다. 고치려면: cd python && uv run python scripts/gen_build_options.py
"""

import importlib.util
import json
from pathlib import Path

from seoulgaok_bim_core import ResolvedOptions, Scheme
from seoulgaok_bim_core.options import Parking

GEN = Path(__file__).resolve().parents[1] / "scripts" / "gen_build_options.py"


def _gen():
    spec = importlib.util.spec_from_file_location("gen_build_options", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generated_files_are_fresh():
    assert _gen().main(["--check"]) == 0


def test_removed_keys_not_in_generated_ts():
    ts = (_gen().TS_PATH).read_text(encoding="utf-8")
    for gone in ("core_along?:", "interior_aisle?:", "far_target?:", "bcr_target?:",
                 "bk_offset?:", "cut_axis?:", "commercial_remainder?:", "stall_width?:"):
        assert gone not in ts, gone
    assert "far_limit_override?:" in ts and "export interface BuildOptions" in ts


# 주차 버블이 대신하는 세 필드 — 엔진이 버블 없는 필지에서 아직 읽으므로 지금은 삭제가 아니라
# 표시만 한다. 표시가 생성물에서 빠지면 속성 창이 지워질 필드를 그대로 권한다.
SUPERSEDED_BY_BUBBLE = ("parking_axis", "road_edge", "multi_road")


def test_bubble_superseded_fields_marked_through_generated_files():
    gen = _gen()
    props = json.loads(gen.SCHEMA_PATH.read_text(encoding="utf-8"))["$defs"]["Parking"]["properties"]
    ts = gen.TS_PATH.read_text(encoding="utf-8")
    lines = ts.splitlines()
    for name in SUPERSEDED_BY_BUBBLE:
        desc = Parking.model_fields[name].description
        assert desc.startswith("[지울 예정"), f"{name}: 정본 설명에 표시가 없다"
        assert props[name].get("deprecated"), f"{name}: 스키마에 deprecated 가 없다"
        at = next(i for i, ln in enumerate(lines) if ln.startswith(f"  {name}?:"))
        doc = "\n".join(lines[:at])
        jsdoc = doc[doc.rindex("/**"):]
        assert "[지울 예정" in jsdoc, f"{name}: TS JSDoc 첫 줄에 표시가 없다"
        assert "@deprecated" in jsdoc, f"{name}: TS JSDoc 에 @deprecated 가 없다"


def test_resolved_options_shape():
    r = ResolvedOptions.model_validate({
        "design": {"core": {"core_side": "s", "core_rotation": 90, "type": 2},
                   "parking": {"parking_axis": "inner", "parking_angle": 60}},
        "source": {"core.core_side": "prior", "core.type": "user"},
    })
    assert r.design.core.core_side == "s"
    assert r.source["core.core_side"] == "prior"


def test_scheme_carries_resolved_options_optionally():
    base = {"data": {"lot_area": 1, "build_area": 1, "far": 1, "bcr": 1, "pnu": "1"},
            "floor_plans": [], "unit_ids": []}
    assert Scheme.model_validate(base).resolved_options is None
    s = Scheme.model_validate({**base, "resolved_options": {"design": {}, "source": {}}})
    assert s.resolved_options is not None
