"""Parking.parking_graph — 주차 버블을 속성 창 값으로.

버블은 (진입 도로 방위, road|yard|aisle) 튜플의 배열이다 — 위상만 적고 칸 수는 결과다.
방위는 항상 dir8 — 필지에서 본 진입 자리의 위치(core_side 와 같은 규칙)다.
REF 값은 firstmate 설계 보고서(v12-parking-graph-opt §3.1)의 소장 도면 역산이다.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from seoulgaok_bim_core import BuildOptions, Parking, ResolvedOptions

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schema" / "build_options.schema.json"
TS_PATH = ROOT / "typescript" / "src" / "options.ts"

# REF 소장 도면을 버블로 적은 값
YEONHUI_75_9 = [  # 코어가 가른 두 마당 — 같은 서쪽 도로의 북쪽 끝·남쪽 끝 마당 둘
    ["nw", "yard"],
    ["sw", "yard"],
]
SEONGBUK_126_37 = [  # 북측 도로 앞 줄 + 남서측 도로의 마당
    ["n", "road"],
    ["sw", "yard"],
]
HWAEGOK_1033_19_ALT3 = [  # 같은 자리의 대안 — 마당(alt2)이 아니라 곧은 차로 두 줄
    ["w", "aisle"],
]


def _park(graph, **kw):
    return Parking.model_validate({"parking_graph": graph, **kw})


def test_default_is_none_and_old_fields_untouched():
    p = Parking()
    assert p.parking_graph is None
    before = {k: v for k, v in p.model_dump().items() if k != "parking_graph"}
    assert before == {"parking_axis": None, "parking_angle": None, "parallel": None,
                      "road_edge": None, "multi_road": None, "tandem": None,
                      "exit_road": None}


@pytest.mark.parametrize("graph", [YEONHUI_75_9, SEONGBUK_126_37])
def test_ref_graphs_round_trip(graph):
    p = _park(graph)
    assert p.model_dump(mode="json", exclude_none=True)["parking_graph"] == graph
    assert [tuple(t) for t in graph] == list(p.parking_graph)
    assert Parking.model_validate(p.model_dump()) == p


def test_nested_design_path():
    o = BuildOptions.model_validate({"design": {"parking": {"parking_graph": SEONGBUK_126_37}}})
    assert o.design.parking.parking_graph[1] == ("sw", "yard")


def test_legacy_ground_floor_shape_moves_to_parking():
    o = BuildOptions.model_validate({"ground_floor": {"parking_graph": YEONHUI_75_9}})
    assert o.design.parking.parking_graph == [("nw", "yard"), ("sw", "yard")]


def test_legacy_dict_nodes_fold_to_tuples():
    """구 노드(dict) 값은 kind·road_side 만 옮기고 칸 수·면 자리는 버린다 — 대수는 결과."""
    p = _park([
        {"kind": "road", "road_side": "n", "stalls": 5, "tandem": True},
        {"kind": "yard", "road_side": "sw"},
    ])
    assert p.parking_graph == [("n", "road"), ("sw", "yard")]


def test_legacy_dict_nodes_without_side_drop_whole_graph():
    """방위 없는 구 노드는 방위를 지어내지 않는다 — 그래프 전체를 버린다(None)."""
    p = _park([
        {"kind": "road", "road_side": "n"},
        {"kind": "yard", "rows": [{"side": "far", "stalls": 2}]},
    ])
    assert p.parking_graph is None


def test_aisle_tuple_accepted_and_round_trips():
    """화곡 1033-19 alt3 — 곧은 차로가 이름 을 갖는다(alt2 의 마당과 다른 선택)."""
    p = _park(HWAEGOK_1033_19_ALT3)
    assert p.parking_graph == [("w", "aisle")]
    assert p.model_dump(mode="json", exclude_none=True)["parking_graph"] == HWAEGOK_1033_19_ALT3
    assert Parking.model_validate(p.model_dump()) == p
    # 마당·차로가 한 배열에 섞여도 된다(같은 도로의 두 자리)
    mixed = _park([["w", "yard"], ["s", "aisle"]])
    assert mixed.parking_graph == [("w", "yard"), ("s", "aisle")]


def test_legacy_dict_node_with_aisle_kind_folds():
    p = _park([{"kind": "aisle", "road_side": "w", "stalls": 5}])
    assert p.parking_graph == [("w", "aisle")]


def test_aisle_reaches_generated_artifacts():
    """생성물까지 aisle 이 가야 속성 창이 세 종류를 권한다 — TS만 빠지면 UI가 막는다."""
    sch = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    pg = sch["$defs"]["Parking"]["properties"]["parking_graph"]
    # Optional → anyOf[array, null]; 목록 항목 안쪽의 둘째 값 enum
    items = next(s["items"] for s in pg["anyOf"] if s.get("type") == "array")
    kinds = items["prefixItems"][1]["enum"]
    assert kinds == ["road", "yard", "aisle"]
    ts = TS_PATH.read_text(encoding="utf-8")
    assert '"road" | "yard" | "aisle"' in ts
    # 지정한 필드 설명에도 세 뜻이 다 있어야 한다(스키마·TS 같은 문장)
    for src in (pg["description"], ts):
        for kind in ("road=", "yard=", "aisle="):
            assert kind in src, kind


@pytest.mark.parametrize("bad", [
    [],                        # 빈 버블 — None 과 뜻이 갈린다
    [["n", "lane"]],           # 모르는 종류 — 곧은 차로의 이름은 aisle 이다
    [["c", "road"]],           # c 는 방위가 아니다
    [["n"]],                   # 튜플은 값 둘
    [["n", "road", "yard"]],   # 값이 셋
    [[None, "yard"]],          # null 방위 — 주접도 표기는 없어졌다
    [[None, "yard", "extra"]],
    [["w", "Yard"]],           # 대/소문자는 다른 값
    [["w", "aisles"]],         # 단수만 종류다
])
def test_rejects_malformed(bad):
    with pytest.raises(ValidationError):
        _park(bad)


def test_legacy_dict_node_with_unknown_kind_drops_whole_graph():
    """구 노드의 모르는 kind 도 그래프를 통째로 버린다 — 방위를 지어내지 않는다."""
    p = _park([{"kind": "lane", "road_side": "w"}])
    assert p.parking_graph is None


def test_resolved_options_carries_graph():
    r = ResolvedOptions.model_validate({
        "design": {"parking": {"parking_axis": "inner", "parking_graph": YEONHUI_75_9}},
        "source": {"parking.parking_graph": "user"},
    })
    assert r.design.parking.parking_graph == [("nw", "yard"), ("sw", "yard")]
