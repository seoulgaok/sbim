"""building-generator #549 로 제안한 옵셔널 키 — 엔진이 아직 안 내지만 계약은 받아들인다.

wall.role · UnitRoom.{use 확장, floor_finish, ceiling_h} · UnitRecord.fixtures · Scheme._mep.
없어도(구 scheme) 그대로 열리고, 있으면 모양대로 읽힌다.
"""
import json
from pathlib import Path

from seoulgaok_bim_core import MepItem, Scheme, UnitFixture, UnitRecord, UnitRoom

SAMPLE = Path(__file__).resolve().parents[2] / "examples" / "samples" / "sample-medium"


def test_old_scheme_and_units_still_load():
    s = Scheme.model_validate(json.loads((SAMPLE / "scheme.json").read_text()))
    assert s.mep is None
    u = [UnitRecord.model_validate(x) for x in json.loads((SAMPLE / "units.json").read_text())]
    assert all(x.fixtures is None for x in u)


def test_new_keys_round_trip():
    room = UnitRoom(use="거실", polygon=[(0, 0), (3, 0), (3, 4)], floor_finish="강마루10", ceiling_h=2.3)
    fx = UnitFixture(kind="싱크", origin=(1.0, 2.0), w=1.2, d=0.6, room_index=0)
    rec = UnitRecord(id="201", floor=2, rooms=[room], fixtures=[fx])
    back = UnitRecord.model_validate(json.loads(rec.model_dump_json(by_alias=True)))
    assert back.fixtures[0].kind == "싱크" and back.rooms[0].floor_finish == "강마루10"
    s = Scheme.model_validate({
        "data": {"lot_area": 1, "build_area": 1, "far": 1, "bcr": 1, "pnu": 1},
        "floor_plans": [],
        "unit_ids": [],
        "_mep": [{"system": "water", "kind": "device", "name": "급수분배기", "floor_id": 2, "origin": [1, 2]}],
    })
    assert isinstance(s.mep[0], MepItem) and s.mep[0].name == "급수분배기"
    assert json.loads(s.model_dump_json(by_alias=True))["_mep"][0]["system"] == "water"
