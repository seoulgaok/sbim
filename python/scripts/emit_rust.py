"""rust/ 방출기 — gen_build_options.py 가 부른다. 아직 비어 있다.

`outputs(root, bundle)` 는 {경로: 내용} 을 돌려준다. bundle 키: build_options · scheme · units ·
surroundings(JSON Schema dict) · migrations(이행 표) · fixtures({케이스: {input, expected}}).
"""

from __future__ import annotations

from pathlib import Path


def outputs(root: Path, bundle: dict) -> dict[Path, str]:
    return {}
