"""설계안 묶음 정답(fixtures/bundle/) — Elixir 판(elixir/sbim/lib/sbim/bundle.ex)이 읽어 같은 내용이 나오는지 본다.

    cd python && uv run python scripts/gen_bundle_fixtures.py [--check]

sample-small(examples/samples) 의 scheme·units 와 손으로 만든 site 를 묶는다. 시각·sha 가 고정이라 다시 떠도 내용이 같다
(zip 바이트는 항목 시각 때문에 달라질 수 있어 --check 는 풀어서 견준다).
"""
import io
import sys
import zipfile
from pathlib import Path

from seoulgaok_bim_core.bundle import pack_bundle

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "examples/samples/sample-small"
OUT = ROOT / "fixtures/bundle/sample-small.sbim"
# 샘플엔 site.json 이 없어 최소 SiteInfo 를 둔다(엔진이 쓰는 키 이름)
SITE = (b'{"parcel_polygon": [[199990.0, 499990.0], [200010.0, 499990.0], [200010.0, 500010.0], [199990.0, 500010.0]], '
        b'"parcel_center": [200000.0, 500000.0], "raw_parcel_area": 400.0}')


def entries(b: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(b)) as z:
        return {n: z.read(n) for n in z.namelist()}


def main():
    files = {n: (SRC / n).read_bytes() for n in ("scheme.json", "units.json")}
    files["site.json"] = SITE
    data = pack_bundle(files, land_ids=["1111010100100010001"], design_id="00000000-0000-0000-0000-000000000001",
                       created_at="2026-01-01T00:00:00Z")
    if "--check" in sys.argv:
        if not OUT.exists() or entries(OUT.read_bytes()) != entries(data):
            print(f"{OUT.relative_to(ROOT)} 가 낡음 — uv run python scripts/gen_bundle_fixtures.py", file=sys.stderr)
            sys.exit(1)
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)
    print(f"{OUT.relative_to(ROOT)} {len(data)}B")


if __name__ == "__main__":
    main()
