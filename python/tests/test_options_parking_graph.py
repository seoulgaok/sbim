"""Parking.parking_graph — 주차 버블을 속성 창 값으로.

노드는 두 종류다: road(도로가 곧 차로)·yard(대지 안 차로). 곧은 차로는 이름이 없다 —
면이 나란한 yard 다. 좌표·치수는 없고, 진입 도로는 dir8 방위(빈 값 = 주접도)다.
REF 값은 firstmate 설계 보고서(v12-parking-graph-opt §3.1)의 소장 도면 역산이다.
"""

import pytest
from pydantic import ValidationError

from seoulgaok_bim_core import BuildOptions, Parking, ResolvedOptions

# REF 소장 도면을 버블로 적은 값
YEONHUI_75_9 = [          # 코어(c)가 가른 두 마당 — 앞은 곧은 차로(면이 나란하다)
    {"kind": "yard", "rows": [{"side": "left", "stalls": 3}, {"side": "right", "stalls": 8}]},
    {"kind": "yard", "rows": [{"side": "left", "stalls": 2}, {"side": "far", "stalls": 3},
                              {"side": "near", "stalls": 2}]},
]
SEONGBUK_126_37 = [       # 주접도 도로 앞 5대 + 서측 도로의 작은 마당
    {"kind": "road", "stalls": 5, "tandem": True},
    {"kind": "yard", "road_side": "w",
     "rows": [{"side": "far", "stalls": 2}, {"side": "left", "stalls": 1, "align": "wall"}]},
]
HONGJE_122_31 = [         # 마당 연접
    {"kind": "yard", "tandem": True,
     "rows": [{"side": "far", "stalls": 4}, {"side": "left", "stalls": 2}]},
]
BUKAHYEON_189_35 = [      # 입구 마당 → 끝 마당(via)
    {"kind": "yard", "rows": [{"side": "near", "stalls": 2}, {"side": "far", "stalls": 2},
                              {"side": "left", "stalls": 1}]},
    {"kind": "yard", "via": 0, "rows": [{"side": "left", "stalls": 3},
                                        {"side": "right", "stalls": 1}]},
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


@pytest.mark.parametrize("graph", [YEONHUI_75_9, SEONGBUK_126_37, HONGJE_122_31,
                                   BUKAHYEON_189_35])
def test_ref_graphs_round_trip(graph):
    p = _park(graph)
    assert p.model_dump(exclude_none=True)["parking_graph"] == graph
    assert Parking.model_validate(p.model_dump()) == p


def test_nested_design_path():
    o = BuildOptions.model_validate({"design": {"parking": {"parking_graph": SEONGBUK_126_37}}})
    assert o.design.parking.parking_graph[1].rows[1].align == "wall"


def test_legacy_ground_floor_shape_moves_to_parking():
    o = BuildOptions.model_validate({"ground_floor": {"parking_graph": HONGJE_122_31}})
    assert o.design.parking.parking_graph[0].tandem is True


@pytest.mark.parametrize("node", [
    {"kind": "road", "rows": [{"side": "far", "stalls": 2}]},
    {"kind": "road", "via": 0},
])
def test_road_node_takes_no_yard_fields(node):
    with pytest.raises(ValidationError, match="road 노드는 rows·via"):
        _park([{"kind": "yard"}, node])


@pytest.mark.parametrize("via", [0, 1, 2])
def test_via_points_back_only(via):
    graph = [{"kind": "yard"}, {"kind": "yard", "via": via}]
    if via == 0:
        assert _park(graph).parking_graph[1].via == 0
    else:
        with pytest.raises(ValidationError, match="앞에 적힌 마당"):
            _park(graph)


def test_via_must_point_at_yard():
    with pytest.raises(ValidationError, match="road 노드입니다"):
        _park([{"kind": "road"}, {"kind": "yard", "via": 0}])


def test_yard_stalls_must_match_rows():
    rows = [{"side": "far", "stalls": 4}, {"side": "left", "stalls": 2}]
    assert _park([{"kind": "yard", "stalls": 6, "rows": rows}])
    with pytest.raises(ValidationError, match="rows 합 6"):
        _park([{"kind": "yard", "stalls": 5, "rows": rows}])


def test_one_row_per_side():
    with pytest.raises(ValidationError, match="같은 자리 면이 둘"):
        _park([{"kind": "yard", "rows": [{"side": "far", "stalls": 2},
                                         {"side": "far", "stalls": 1}]}])


@pytest.mark.parametrize("bad", [
    [],                                                      # 빈 버블 — None 과 뜻이 갈린다
    [{"kind": "lane"}],                                      # 곧은 차로는 이름이 없다
    [{"kind": "road", "road_side": "c"}],                    # c 는 방위가 아니다
    [{"kind": "yard", "rows": [{"side": "north", "stalls": 1}]}],   # 면 자리는 상대 자리
    [{"kind": "yard", "rows": [{"side": "far", "stalls": 0}]}],
    [{"kind": "yard", "rows": []}],
    [{"kind": "road", "stalls": 0}],
    [{"kind": "road", "x": 1.0}],                            # 좌표 금지
    [{"kind": "yard", "rows": [{"side": "far", "stalls": 1, "angle": 30}]}],
])
def test_rejects_malformed(bad):
    with pytest.raises(ValidationError):
        _park(bad)


def test_resolved_options_carries_graph():
    r = ResolvedOptions.model_validate({
        "design": {"parking": {"parking_axis": "inner", "parking_graph": YEONHUI_75_9}},
        "source": {"parking.parking_graph": "user"},
    })
    assert r.design.parking.parking_graph[0].rows[1].stalls == 8
