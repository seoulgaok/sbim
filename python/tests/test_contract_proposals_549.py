"""building-generator #549 로 제안한 옵셔널 키 — 엔진이 아직 안 내지만 계약은 받아들인다.

wall.role · UnitRoom.{use 확장, floor_finish, ceiling_h} · UnitRecord.fixtures. `Scheme._mep` 은 0.1.3 에서 뺐다(설비는
범위 밖) — 옛 파일의 `_mep` 키는 extra 로 지나간다.
없어도(구 scheme) 그대로 열리고, 있으면 모양대로 읽힌다.
"""
import json
from pathlib import Path

from seoulgaok_bim_core import Scheme, UnitFixture, UnitRecord, UnitRoom

SAMPLE = Path(__file__).resolve().parents[2] / "examples" / "samples" / "sample-medium"


def test_old_scheme_and_units_still_load():
    s = Scheme.model_validate(json.loads((SAMPLE / "scheme.json").read_text()))
    assert not hasattr(s, "mep")
    u = [UnitRecord.model_validate(x) for x in json.loads((SAMPLE / "units.json").read_text())]
    assert all(x.fixtures is None for x in u)


def test_new_keys_round_trip():
    room = UnitRoom(use="거실", polygon=[(0, 0), (3, 0), (3, 4)], floor_finish="강마루10", ceiling_h=2.3)
    fx = UnitFixture(kind="싱크", origin=(1.0, 2.0), w=1.2, d=0.6, room_index=0)
    rec = UnitRecord(id="201", floor=2, rooms=[room], fixtures=[fx])
    back = UnitRecord.model_validate(json.loads(rec.model_dump_json(by_alias=True)))
    assert back.fixtures[0].kind == "싱크" and back.rooms[0].floor_finish == "강마루10"
    # 옛 파일에 남은 `_mep` 는 거부하지 않고 지나간다(설비는 0.1.3 부터 범위 밖)
    s = Scheme.model_validate({
        "data": {"lot_area": 1, "build_area": 1, "far": 1, "bcr": 1, "pnu": 1},
        "floor_plans": [],
        "unit_ids": [],
        "_mep": [{"system": "water", "kind": "device", "name": "급수분배기", "floor_id": 2, "origin": [1, 2]}],
    })
    assert not hasattr(s, "mep")


def test_site_json_contract_round_trip(tmp_path):
    from seoulgaok_bim_core import SiteInfo
    from seoulgaok_bim_core.io import load_site
    site = SiteInfo(parcel_polygon=[(0, 0), (20, 0), (20, 15), (0, 15)], parcel_center=(10, 7.5),
                    road_polygon=[[(0, -6), (20, -6), (20, 0), (0, 0)]], road_centerline_widths=[6.0])
    p = tmp_path / "site.json"
    p.write_text(site.model_dump_json(), encoding="utf-8")
    back = load_site(p)
    assert back.parcel_center == (10, 7.5) and back.road_polygon and back.road_centerline_widths == [6.0]
