"""Parking.parking_graph — 주차 버블을 속성 창 값으로.

버블은 (진입 도로 방위, road|yard) 튜플의 배열이다 — 위상만 적고 칸 수는 결과다.
좌표·치수는 없고, 진입 도로는 dir8 방위(빈 값 = 주접도)다.
REF 값은 firstmate 설계 보고서(v12-parking-graph-opt §3.1)의 소장 도면 역산이다.
"""

import pytest
from pydantic import ValidationError

from seoulgaok_bim_core import BuildOptions, Parking, ResolvedOptions

# REF 소장 도면을 버블로 적은 값
YEONHUI_75_9 = [  # 코어가 가른 두 마당 — 같은 주접도에서 마당 둘
    [None, "yard"],
    [None, "yard"],
]
SEONGBUK_126_37 = [  # 북측 도로 앞 줄 + 남서측 도로의 마당
    ["n", "road"],
    ["sw", "yard"],
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
    assert o.design.parking.parking_graph == [(None, "yard"), (None, "yard")]


def test_legacy_dict_nodes_fold_to_tuples():
    """구 노드(dict) 값은 kind·road_side 만 옮기고 칸 수·면 자리는 버린다 — 대수는 결과."""
    p = _park([
        {"kind": "road", "road_side": "n", "stalls": 5, "tandem": True},
        {"kind": "yard", "rows": [{"side": "far", "stalls": 2}]},
    ])
    assert p.parking_graph == [("n", "road"), (None, "yard")]


@pytest.mark.parametrize("bad", [
    [],                        # 빈 버블 — None 과 뜻이 갈린다
    [["n", "lane"]],           # 곧은 차로는 이름이 없다
    [["c", "road"]],           # c 는 방위가 아니다
    [["n"]],                   # 튜플은 값 둘
    [["n", "road", "yard"]],
    [[None, "yard", "extra"]],
])
def test_rejects_malformed(bad):
    with pytest.raises(ValidationError):
        _park(bad)


def test_resolved_options_carries_graph():
    r = ResolvedOptions.model_validate({
        "design": {"parking": {"parking_axis": "inner", "parking_graph": YEONHUI_75_9}},
        "source": {"parking.parking_graph": "user"},
    })
    assert r.design.parking.parking_graph == [(None, "yard"), (None, "yard")]
