"""pytest가 저장소 안의 python/ 패키지를 보게 한다.

전역에 editable 설치된 다른 경로의 seoulgaok_bim_core가 sys.path에 먼저
들어와 있으면, 고친 코드가 아니라 그쪽이 import된다 — "테스트는 통과하는데
고친 건 안 돌아가는" 상황. 저장소 사본을 맨 앞에 세운다.
"""
import sys
from pathlib import Path

PKG_ROOT = str(Path(__file__).resolve().parents[1])
if sys.path[0] != PKG_ROOT:
    sys.path.insert(0, PKG_ROOT)

for name in [m for m in sys.modules if m.startswith("seoulgaok_bim_core")]:
    del sys.modules[name]
