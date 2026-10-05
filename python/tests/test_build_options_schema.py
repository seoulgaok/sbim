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
                 "bk_offset?:", "cut_axis?:", "commercial_remainder?:", "stall_width?:",
                 "parking_axis?:", "road_edge?:", "multi_road?:"):
        assert gone not in ts, gone
    assert "far_limit_override?:" in ts and "export interface BuildOptions" in ts


# 주차 버블이 대신한 세 필드 — 삭제됐다(2026-10-05). 생성물에 되살아나면 속성 창이
# 지워진 필드를 다시 권한다.
SUPERSEDED_BY_BUBBLE = ("parking_axis", "road_edge", "multi_road")


def test_bubble_superseded_fields_absent_from_generated_files():
    gen = _gen()
    props = json.loads(gen.SCHEMA_PATH.read_text(encoding="utf-8"))["$defs"]["Parking"]["properties"]
    ts = gen.TS_PATH.read_text(encoding="utf-8")
    for name in SUPERSEDED_BY_BUBBLE:
        assert name not in Parking.model_fields, f"{name}: 정본에 돌아왔다"
        assert name not in props, f"{name}: 스키마에 남아 있다"
        assert f"  {name}?:" not in ts, f"{name}: TS 에 남아 있다"


def test_resolved_options_shape():
    r = ResolvedOptions.model_validate({
        "design": {"core": {"core_side": "s", "core_rotation": 90, "type": 2},
                   "parking": {"parking_angle": 60}},
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
