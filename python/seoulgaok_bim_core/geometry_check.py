"""형상 온전성 검사 — 말도 안 되는 부재를 내보내기 전에 잡는다.

2026-10-08 현장: 사이트에서 받은 IFC를 아키캐드에서 열었더니 원점의 작은 건물에서
가느다란 기둥 하나가 위아래로 끝없이 뻗은 "타워"가 나왔다. 모델 전체가 커진 게
아니라 **부재 하나의 높이가 터진 것**이었다(단위 문제였다면 건물도 같이 커진다).

엔진이 그런 값을 내놓는 일은 막을 수 없지만, 그걸 **조용히 IFC로 써 보내는 것**은
막을 수 있다. 20km짜리 기둥이 든 파일은 없느니만 못하다 — 받은 사람은 우리 모델
전체를 의심하게 된다.

검사는 층 표고에서 봉투를 세우고 거기서 크게 벗어난 것만 잡는다. 느슨하게 잡아
정상 설계가 걸리지 않게 하고, 터진 값만 걸리게 한다.
"""

from __future__ import annotations

# 봉투 여유 — 옥탑·파라펫·지하 여유를 넉넉히 덮는다
Z_MARGIN = 30.0
# 한 필지 모델의 평면 반경 한계 (메시는 상대좌표라 원점 근처에 있어야 한다)
XY_LIMIT = 300.0
# userData가 높이로 쓰는 키
_Z_KEYS = ("base_z", "top_z", "z0", "z1", "sill")


def storey_envelope(scheme_json) -> tuple[float, float]:
    """층 표고에서 세운 z 봉투 (아래, 위). 층 정보가 없으면 넉넉한 기본값."""
    lo, hi = [], []
    for fp in scheme_json.get("floor_plans") or []:
        d = fp.get("data") or {}
        z0 = d.get("floor_bottom_height")
        h = d.get("floor_height") or 0
        if z0 is None:
            continue
        lo.append(float(z0))
        hi.append(float(z0) + float(h))
    if not lo:
        return -20.0, 100.0
    return min(lo) - Z_MARGIN, max(hi) + Z_MARGIN


def check_geometry_sanity(scheme_json) -> list[str]:
    """터진 형상을 찾아 사람이 읽을 수 있는 줄로 돌려준다. 정상이면 빈 리스트."""
    zlo, zhi = storey_envelope(scheme_json)
    bad: list[str] = []

    for fp in scheme_json.get("floor_plans") or []:
        fid = (fp.get("data") or {}).get("floor_id")
        for bucket, groups in (fp.get("geom") or {}).items():
            for g in (groups or []):
                for bg in (g if isinstance(g, list) else [g]):
                    if not isinstance(bg, dict):
                        continue
                    ud = bg.get("userData") or {}
                    for k in _Z_KEYS:
                        v = ud.get(k)
                        if isinstance(v, (int, float)) and not (zlo <= v <= zhi):
                            bad.append(
                                f"{fid}층 {bucket}: {k}={v:.1f}m — 허용 {zlo:.1f}~{zhi:.1f}m")
                    att = ((bg.get("data") or {}).get("attributes") or {}).get("position") or {}
                    arr = att.get("array")
                    if not arr:
                        continue
                    zs = arr[2::3]
                    if zs:
                        z0, z1 = min(zs), max(zs)
                        if z0 < zlo or z1 > zhi:
                            bad.append(
                                f"{fid}층 {bucket}: 메시 z {z0:.1f}~{z1:.1f}m "
                                f"— 허용 {zlo:.1f}~{zhi:.1f}m")
                    xs, ys = arr[0::3], arr[1::3]
                    if xs and (max(map(abs, xs)) > XY_LIMIT or max(map(abs, ys)) > XY_LIMIT):
                        bad.append(
                            f"{fid}층 {bucket}: 메시가 원점에서 "
                            f"{max(max(map(abs, xs)), max(map(abs, ys))):.0f}m 떨어짐 "
                            f"— 한계 {XY_LIMIT:.0f}m")
    return bad


def raise_if_insane(scheme_json, *, limit: int = 6) -> None:
    """터진 형상이 있으면 거부한다. 조용히 내보내지 않는다."""
    bad = check_geometry_sanity(scheme_json)
    if not bad:
        return
    head = "\n  ".join(bad[:limit])
    more = f"\n  … 외 {len(bad) - limit}건" if len(bad) > limit else ""
    raise ValueError(
        f"형상이 층 표고 봉투를 벗어났습니다 ({len(bad)}건) — IFC로 내보내지 않습니다.\n"
        f"  {head}{more}\n"
        "엔진 출력(scheme.json)을 먼저 확인하세요. 이대로 내보내면 받는 쪽에서 "
        "모델 전체를 의심하게 됩니다.")
