"""IFC 정답(fixtures/ifc/) 생성 — Elixir 판(elixir/sbim/lib/sbim/ifc.ex)이 바이트 단위로 같아야 하는 파일.

    cd python && uv run python scripts/gen_ifc_fixtures.py           # 다시 뜬다
    cd python && uv run python scripts/gen_ifc_fixtures.py --check   # 어긋나면 1로 끝난다(CI)

ifc.py 를 고치면 이것이 CI 에서 먼저 깨지고, 정답을 다시 뜨면 Elixir 판 시험(elixir/sbim/test/ifc_test.exs)이 깨진다 —
그래서 두 판이 갈린 채로 들어가지 않는다. 정답은 gzip(mtime 0 — 다시 떠도 같은 바이트)으로 둔다(샘플 하나 2MB).

결정성: GlobalId 는 1부터 세는 정수 UUID 를 압축한 22자(`_gid` 갈아끼움), FILE_NAME 시각은
고정값으로 바꿔 쓴다. 나머지(개체 번호·속성·실수 표기)는 ifcopenshell 가 쓴 그대로다.
입력은 examples/samples/<이름>/{scheme,units}.json — parcel_center 는 넘기지 않는다
(generate_ifc 가 derive_parcel_center 로 구한다).
쓰는 IFC 타입 목록(types.txt)도 같이 남긴다 — 스키마 표 생성기(gen_ifc_schema.py)의 입력.
"""
import gzip
import itertools
import json
import random
import re
import struct
import sys
import uuid
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid

from seoulgaok_bim_core import ifc as I

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "fixtures/ifc"
STAMP = "2026-01-01T00:00:00"


def _put(path: Path, data: bytes, check: bool, bad: list):
    """쓰거나(--check 면) 견준다. gzip 은 내용으로 견준다."""
    if check:
        old = path.read_bytes() if path.exists() else None
        if path.suffix == ".gz" and old is not None:
            old = gzip.decompress(old)
        if old != data:
            bad.append(path.name)
        return
    if path.suffix == ".gz":
        data = gzip.compress(data, mtime=0)
    path.write_bytes(data)


def gen_format(check: bool, bad: list):
    """표기 정답 — 실수(경계·무작위 비트)와 문자열(따옴표·역빗금·한글·BMP 밖) 을 ifcopenshell 이 쓴 그대로.
    값은 비트(u64)로 남긴다 — 십진 문자열로 옮기면 그 자체가 반올림이라 시험이 안 된다."""
    rnd = random.Random(7)
    vals = [0.0, -0.0, 1.0, -1.0, 3.0, 0.1, 0.2, 1e-5, 1e-4, 1.5e-4, 9.99e-5, 1e16, 1e17,
            1.2345678901234567e17, 2.5, 1 / 3, 200000.0, 5e-324, 1e-300, 1e300, 0.30000000000000004,
            12345.678, -7.25e-7, 100.0, 0.001]
    for _ in range(500):
        vals.append(struct.unpack("d", struct.pack("Q", rnd.getrandbits(64)))[0])
        vals.append(rnd.uniform(-50, 50))
        vals.append(rnd.uniform(-1e-3, 1e-3))
        vals.append(round(rnd.uniform(-100, 100), rnd.randint(0, 6)))
    vals = [v for v in vals if v == v and abs(v) != float("inf")]
    strs = ["a'b\\c\nd 철근 x ㎡·é😀", "PNU  · EPSG", "[외벽] 철콘200 / EPS200", "\t탭"]
    f = ifcopenshell.file(schema="IFC4")
    for v in vals:
        f.create_entity("IfcCartesianPoint", Coordinates=(v,))
    for s in strs:
        f.create_entity("IfcMaterial", Name=s)
    tmp = OUT / ".format.tmp.ifc"
    f.write(str(tmp))
    lines = [l for l in tmp.read_text(encoding="utf-8").splitlines() if l.startswith("#")]
    tmp.unlink()
    _put(OUT / "format.json", json.dumps({
        "reals": [[struct.unpack("Q", struct.pack("d", v))[0], l.split("((", 1)[1][:-3]]
                  for v, l in zip(vals, lines)],
        "strings": [[s, l.split("(", 1)[1].rsplit(",$,$);", 1)[0]] for s, l in zip(strs, lines[len(vals):])],
    }, ensure_ascii=False).encode("utf-8"), check, bad)
    print(f"format: {len(vals)} reals · {len(strs)} strings")


def main():
    check = "--check" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--check"]
    bad: list[str] = []
    OUT.mkdir(parents=True, exist_ok=True)
    gen_format(check, bad)
    types: set[str] = set()
    orig = ifcopenshell.file.create_entity

    def traced(self, type, *a, **kw):
        e = orig(self, type, *a, **kw)
        types.add(e.is_a())
        return e

    ifcopenshell.file.create_entity = traced
    names = args or sorted(p.name for p in (ROOT / "examples/samples").iterdir() if p.is_dir())
    for name in names:
        src = ROOT / "examples/samples" / name
        c = itertools.count(1)
        I._gid = lambda: ifcopenshell.guid.compress(uuid.UUID(int=next(c)).hex)
        out = OUT / f".{name}.tmp.ifc"
        scheme = json.loads((src / "scheme.json").read_text(encoding="utf-8"))
        units = json.loads((src / "units.json").read_text(encoding="utf-8"))
        I.generate_ifc(scheme, units, out_path=str(out))
        txt = out.read_text(encoding="utf-8")
        out.unlink()
        txt = re.sub(r"(FILE_NAME\('[^']*',)'[^']*'", rf"\1'{STAMP}'", txt, count=1)
        _put(OUT / f"{name}.ifc.gz", txt.encode("utf-8"), check, bad)
        print(f"{name}: {txt.count(chr(10))} lines")
    if not args:
        _put(OUT / "types.txt", ("\n".join(sorted(types)) + "\n").encode("utf-8"), check, bad)
    if bad:
        print(f"정답이 ifc.py 와 어긋남: {', '.join(bad)} — uv run python scripts/gen_ifc_fixtures.py", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
