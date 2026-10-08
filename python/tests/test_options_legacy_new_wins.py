"""구 `ground_floor.<k>` 와 신 거처의 같은 키가 함께 오면 신 위치가 이긴다.

티켓 5202de14(장안동 446-4): 저장 옵션의 구 `ground_floor.core_side="c"` 가 사용자가 바꾼
`core.core_side` 를 덮어써 엔진에는 c 하나만 들어갔다. 사용자가 채운 칸은 어디서나 존중된다.
"""

import logging

from seoulgaok_bim_core.options import BuildOptions

LOGGER = "seoulgaok_bim_core.options"


def test_legacy_only_moves_to_new_home(caplog):
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        o = BuildOptions.model_validate(
            {"core": {"type": 5}, "ground_floor": {"core_side": "c", "tandem": True}}
        )
    assert o.design.core.core_side == "c"
    assert o.design.core.type == 5
    assert o.design.parking.tandem is True
    assert not caplog.records


def test_new_home_only_unchanged(caplog):
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        o = BuildOptions.model_validate({"core": {"type": 5, "core_side": "n"}})
    assert o.design.core.core_side == "n"
    assert not caplog.records


def test_conflict_keeps_new_value_and_warns_once(caplog):
    raw = {
        "core": {"type": 5, "core_side": "n"},
        "parking": {"tandem": False},
        "ground_floor": {"core_side": "c", "tandem": True, "core_rotation": 90},
    }
    for side in ("n", "s", "w"):
        raw["core"]["core_side"] = side
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger=LOGGER):
            o = BuildOptions.model_validate(raw)
        assert o.design.core.core_side == side          # 구 c 가 덮지 않는다
        assert o.design.parking.tandem is False
        assert o.design.core.core_rotation == 90         # 신 쪽에 없는 구 키는 그대로 옮겨 온다
        assert len([r for r in caplog.records if "core_side" in r.getMessage()]) == 1


def test_same_value_in_both_is_silent(caplog):
    with caplog.at_level(logging.WARNING, logger=LOGGER):
        o = BuildOptions.model_validate(
            {"core": {"core_side": "n"}, "ground_floor": {"core_side": "n"}}
        )
    assert o.design.core.core_side == "n"
    assert not caplog.records
