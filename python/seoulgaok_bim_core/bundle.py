"""설계안 묶음(.sbim) — 설계안 폴더의 JSON 들을 zip 한 파일로.

설계안 폴더는 storage 에 파일로 따로 놓인다(scheme.json 옆에 site.json·units.json). 내려받아 다른 곳
(에디터·다른 기계·보관)으로 옮기려면 한 덩어리가 필요해서 묶음을 정의한다.

꼴 (bundle_version 1):
  - 확장자 `.sbim`, 내용은 보통 zip(deflate). 항목은 루트에 이 이름 그대로:
      manifest.json      필수 — `BundleManifest` (첫 항목)
      scheme.json        필수 — `Scheme`
      units.json         필수 — `UnitRecord` 목록
      site.json          선택 — `SiteInfo`
  - surroundings.json 은 넣지 않는다 — 엔진이 안 만들고(파이썬·Elixir 둘 다 None) 소비처는 주변 건물을 지도
    타일에서 읽는다(nextbase tileSurroundings.ts, 2026-10).
  - manifest.files = {항목 이름: sha256 hex} — manifest 자신은 빼고 묶은 항목 전부. 읽는 쪽은 이것으로
    빠짐·손상을 잡는다. 목록에 없는 항목은 읽지 않는다(앞으로 늘 항목은 bundle_version 을 올려서).

JSON 은 바이트 그대로 담는다 — 엔진이 storage 에 올린 그 파일과 같은 바이트라 sha256 이 같다.
Elixir 판은 elixir/sbim/lib/sbim/bundle.ex (같은 꼴 — 시험은 서로의 정답 fixtures/bundle/ 을 읽는다).
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .types import BundleManifest, Scheme, SiteInfo, UnitRecord

BUNDLE_VERSION = 1
MANIFEST = "manifest.json"
REQUIRED = ("scheme.json", "units.json")
OPTIONAL = ("site.json",)
ENTRIES = REQUIRED + OPTIONAL


class BundleError(ValueError):
    """묶음이 꼴에 안 맞는다 — 항목 빠짐·sha 어긋남·모르는 판."""


@dataclass
class Bundle:
    manifest: BundleManifest
    scheme: Scheme
    units: list[UnitRecord]
    site: Optional[SiteInfo] = None
    raw: dict[str, bytes] = field(default_factory=dict)


def pack_bundle(files: dict[str, bytes], *, land_ids: list[str], design_id: str | None = None,
                created_at: str | None = None) -> bytes:
    """{항목 이름: JSON 바이트} → .sbim 바이트. scheme.json·units.json 은 있어야 한다.

    engine_stamp 는 scheme.json 의 `_engine_stamp` 를 옮겨 적는다(어느 엔진 판이 낸 안인지)."""
    unknown = set(files) - set(ENTRIES)
    if unknown:
        raise BundleError(f"묶을 수 없는 항목: {sorted(unknown)} — {list(ENTRIES)} 만")
    missing = [n for n in REQUIRED if n not in files]
    if missing:
        raise BundleError(f"필수 항목 없음: {missing}")
    from . import __version__
    stamp = json.loads(files["scheme.json"]).get("_engine_stamp")
    manifest = BundleManifest(
        format="sbim-bundle", bundle_version=BUNDLE_VERSION, sbim_version=__version__,
        created_at=created_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        land_ids=list(land_ids), design_id=design_id, engine_stamp=stamp,
        files={n: hashlib.sha256(files[n]).hexdigest() for n in ENTRIES if n in files})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(MANIFEST, manifest.model_dump_json(indent=2))
        for n in ENTRIES:
            if n in files:
                z.writestr(n, files[n])
    return buf.getvalue()


def read_bundle(data: bytes | str | Path) -> Bundle:
    """.sbim(바이트 또는 경로) → `Bundle`. manifest 의 sha256 과 안 맞으면 `BundleError`."""
    if not isinstance(data, (bytes, bytearray)):
        data = Path(data).read_bytes()
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        raise BundleError(f"zip 이 아니다: {e}") from e
    with z:
        names = set(z.namelist())
        if MANIFEST not in names:
            raise BundleError("manifest.json 없음")
        manifest = BundleManifest.model_validate_json(z.read(MANIFEST))
        if manifest.format != "sbim-bundle" or manifest.bundle_version > BUNDLE_VERSION:
            raise BundleError(f"모르는 묶음: {manifest.format} v{manifest.bundle_version}")
        raw = {}
        for n, sha in manifest.files.items():
            if n not in names:
                raise BundleError(f"manifest 에 있는데 묶음에 없음: {n}")
            b = z.read(n)
            if hashlib.sha256(b).hexdigest() != sha:
                raise BundleError(f"sha256 어긋남: {n}")
            raw[n] = b
    for n in REQUIRED:
        if n not in raw:
            raise BundleError(f"필수 항목 없음: {n}")
    j = {n: json.loads(b) for n, b in raw.items()}
    return Bundle(
        manifest=manifest,
        scheme=Scheme.model_validate(j["scheme.json"]),
        units=[UnitRecord.model_validate(u) for u in j["units.json"]],
        site=SiteInfo.model_validate(j["site.json"]) if "site.json" in j else None,
        raw=raw)
