"""첫수표가 채우는 필드의 단일 정본 — `options.Design` 의 `empty` 표시 (#440).

비울 수 있는 design 필드는 전부 비웠을 때 누가 정하는지를 하나로 적는다:
auto=첫수표(→ resolved_options 에 나온다) · law=법 · default=적힌 기본값.
ResolvedDesign(python·TS)은 auto 집합을 손으로 옮긴 것이라, 둘이 갈리면 여기서 걸린다 —
갈리면 엔진이 채운 값을 되돌려주지 않거나(되먹임이 재현되지 않는다) 법이 정하는 값을
첫수표 값처럼 고정시킨다(tandem 의 법정 폴백이 꺼진다).
"""

import re
import typing
from pathlib import Path

from pydantic import BaseModel

from seoulgaok_bim_core import AUTO_FIELDS, EMPTY_MARKERS, Design, ResolvedDesign

ROOT = Path(__file__).resolve().parents[2]

# 정해 둔 분류 (2026-10-08 소장 결정, #440)
EXPECTED = {
    "massing.target_floor_count": "auto",
    "massing.first_floor_height": "default",
    "massing.mass_axis": "auto",
    "units.units_per_floor": "auto",
    "units.units_by_level": "auto",
    "units.max_net_area": "default",
    "core.type": "auto",
    "core.core_side": "auto",
    "core.core_rotation": "auto",
    "core.core_mirror": "auto",
    "core.core_entries": "default",
    "parking.parking_angle": "auto",
    "parking.parallel": "auto",
    "parking.tandem": "auto",
    "parking.exit_road": "law",
    "parking.parking_graph": "auto",
    "regulations.far_limit_override": "law",
    "regulations.bcr_limit_override": "law",
    "regulations.road_setback": "law",
    "regulations.pedestrian_width": "default",
}


def _sections():
    for sec, f in Design.model_fields.items():
        if isinstance(f.annotation, type) and issubclass(f.annotation, BaseModel):
            yield sec, f.annotation


def test_markers_are_the_decided_classification():
    assert EMPTY_MARKERS == EXPECTED


def test_every_nullable_design_field_is_marked():
    """None 을 받는 design 필드는 하나도 빠짐없이 auto|law|default 중 하나다."""
    unmarked = [
        f"{sec}.{name}"
        for sec, model in _sections()
        for name, f in model.model_fields.items()
        if type(None) in typing.get_args(f.annotation) and f"{sec}.{name}" not in EMPTY_MARKERS
    ]
    assert unmarked == [], f"비웠을 때 누가 정하는지 표시가 없다: {unmarked}"
    assert set(EMPTY_MARKERS.values()) <= {"auto", "law", "default"}


def test_resolved_design_is_the_auto_set():
    leaves = {
        f"{sec}.{name}"
        for sec, f in ResolvedDesign.model_fields.items()
        for name in typing.get_args(f.annotation)[0].model_fields
    }
    assert leaves == AUTO_FIELDS


def test_ts_resolved_design_is_the_auto_set():
    ts = (ROOT / "typescript" / "src" / "types.ts").read_text(encoding="utf-8")
    body = re.search(r"export interface ResolvedDesign \{(.*?)\n\}", ts, re.S).group(1)
    # 각 묶음: `<sec>?: Pick<Model, "a" | "b">;`
    leaves = {
        f"{sec}.{name}"
        for sec, pick in re.findall(r"^\s*(\w+)\?:\s*Pick<\s*\w+,(.*?)>;", body, re.S | re.M)
        for name in re.findall(r'"(\w+)"', pick)
    }
    assert leaves == AUTO_FIELDS


def test_generated_schema_carries_the_marker():
    sch = Design.model_json_schema()
    for key, marker in EMPTY_MARKERS.items():
        sec, name = key.split(".")
        model = Design.model_fields[sec].annotation.__name__
        assert sch["$defs"][model]["properties"][name]["empty"] == marker, key
