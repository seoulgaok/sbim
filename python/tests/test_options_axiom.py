"""옵션 설명의 공리 정합 — None은 「첫수표가 정한다」다 (#12).

엔진에는 "더 좋다"가 없다. 엔진 = f(대지, 속성 창) → 도면이고, 엔진이 아는 것은 법과
물리의 된다/안 된다뿐이다. 취향은 첫수표(속성 창의 None을 채우는 표)에만 산다
(building-generator #213).

그런데 설명 문장이 그 반대를 명세하고 있었다 — "None=자동: 둘 다 평가해 대수 최대 채택".
명세가 엔진에게 여러 판을 그려 고르라고 시키는 꼴이라, 소장 값을 넣으면 오히려 대수가
줄었다(core_type 25→22, road_edge 4→2). 문장이 되돌아가면 여기서 걸린다.
"""

import pytest
from pydantic import BaseModel

from seoulgaok_bim_core import options as O

# 취향 필드 — 값이 없으면 첫수표가 정한다 (derive 필드와 구분된다:
# road_edge·exit_road처럼 법·기하가 한 값을 계산해 주는 것은 여기 없다)
CHOICE_FIELDS = [
    (O.Parking, "parking_axis"),
    (O.Parking, "parking_angle"),
    (O.Parking, "interior_aisle"),
    (O.Core, "core_side"),
    (O.Core, "core_rotation"),
    (O.Core, "core_axis"),
]

# 엔진에게 탐색을 시키는 명세 — 어느 필드에도 없어야 한다
SEARCH_PHRASES = [
    "둘 다 평가",
    "평가·대수 우위",
    "우위만 채택",
    "argmax 자동",
    "엔진이 자동 선택",
    "엔진이 정함",
    "엔진이 계산해 고르는",
]


@pytest.mark.parametrize(("cls", "name"), CHOICE_FIELDS)
def test_choice_field_defers_to_first_move(cls, name):
    desc = cls.model_fields[name].description
    assert "첫수표" in desc, f"{cls.__name__}.{name}: None의 주인이 첫수표라고 말하지 않는다"


@pytest.mark.parametrize(("cls", "name"), CHOICE_FIELDS)
def test_choice_field_does_not_promise_selection(cls, name):
    desc = cls.model_fields[name].description
    assert "채택" not in desc, f"{cls.__name__}.{name}: 엔진이 골라 채택한다고 적혀 있다"


def _all_descriptions():
    for cls_name in dir(O):
        cls = getattr(O, cls_name)
        if isinstance(cls, type) and issubclass(cls, BaseModel):
            for fname, f in cls.model_fields.items():
                if f.description:
                    yield f"{cls_name}.{fname}", f.description


@pytest.mark.parametrize("phrase", SEARCH_PHRASES)
def test_no_field_orders_the_engine_to_search(phrase):
    hits = [path for path, desc in _all_descriptions() if phrase in desc]
    assert hits == [], f"'{phrase}' — 엔진에 탐색을 시키는 명세: {hits}"
