"""Core.type 번호 개번(2026-09) — 옛 번호 ↔ 새 번호 이행 계약 (#2).

building-generator가 코어 라이브러리 번호를 DWG 템플릿 시트 순서로 재배열했다
(#190). 값 집합은 1~7 그대로라 스키마 검증으로는 걸리지 않는다 — 옛 번호로
저장된 core.type은 migrate_core_type()으로 옮겨야 뜻이 유지된다.
"""

import pytest

from seoulgaok_bim_core import (
    CORE_TYPE_RENUMBER_2026_09,
    Core,
    migrate_core_type,
)


def test_renumber_covers_every_type():
    """7개 유형이 모두 표에 있다 — 빠진 번호는 조용히 옛 뜻으로 남는다."""
    assert set(CORE_TYPE_RENUMBER_2026_09) == {1, 2, 3, 4, 5, 6, 7}


def test_renumber_is_a_permutation():
    """번호만 바뀌고 유형이 늘거나 줄지 않는다 — 전단사."""
    assert sorted(CORE_TYPE_RENUMBER_2026_09.values()) == [1, 2, 3, 4, 5, 6, 7]


@pytest.mark.parametrize(
    ("old", "new"),
    [(1, 2), (2, 1), (3, 4), (4, 5), (5, 7), (6, 6), (7, 3)],
)
def test_known_pairs(old, new):
    """building-generator #190의 개번 표와 같다."""
    assert migrate_core_type(old) == new


def test_none_stays_auto():
    """None=auto는 번호가 아니다 — 그대로 둔다."""
    assert migrate_core_type(None) is None


def test_unknown_number_rejected():
    """범위 밖 값은 조용히 통과시키지 않는다."""
    with pytest.raises(ValueError):
        migrate_core_type(8)


def test_stored_old_value_moves():
    """구 reference 저장값 core.type=2(옛 좁은타워·꺾인계단)는 새 번호 1이다."""
    assert migrate_core_type(Core(type=2).type) == 1


def test_only_type_6_is_fixed():
    """6번(정방형·ㄱ자계단)만 제자리 — 나머지는 전부 이동한다."""
    assert [k for k, v in CORE_TYPE_RENUMBER_2026_09.items() if k == v] == [6]
