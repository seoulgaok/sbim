"""
SBIM Editor — Local API server (FastAPI)
Wraps Supabase DB + Storage access for the Tauri desktop app.

Usage:
    cd sbim-editor/api-server
    python main.py
"""

import os
import sys
import json
import uuid
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

# ─── Load .env — 상위 디렉토리를 순차적으로 탐색 ────────────────────────────
def _find_dotenv() -> Path | None:
    """api-server/ 에서 위로 올라가며 .env 를 찾는다. SBIM_DOTENV로 직접 지정 가능."""
    if env := os.getenv("SBIM_DOTENV"):
        return Path(env)
    here = Path(__file__).resolve().parent
    for ancestor in [here, *here.parents]:
        if (candidate := ancestor / ".env").exists():
            return candidate
    return None

dotenv_path = _find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
    print(f"[api] Loaded .env from {dotenv_path}")
else:
    load_dotenv()
    print("[api] .env not found, using environment variables")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sbim-api")

# ─── DB connection ────────────────────────────────────────────────────────────

def db_conn():
    return psycopg2.connect(
        host=os.getenv("SUPABASE_DB_HOST", os.getenv("DB_HOST")),
        port=os.getenv("SUPABASE_DB_PORT", os.getenv("DB_PORT", "6543")),
        dbname=os.getenv("SUPABASE_DB_NAME", "postgres"),
        user=os.getenv("SUPABASE_DB_USER", os.getenv("DB_USER")),
        password=os.getenv("SUPABASE_DB_PASSWORD", os.getenv("DB_PASSWORD")),
        connect_timeout=10,
    )

@contextmanager
def get_conn():
    conn = db_conn()
    try:
        yield conn
    finally:
        conn.close()

# ─── Supabase storage helper ───────────────────────────────────────────────────

def fetch_scheme_json(scheme_url: str) -> dict:
    """Download scheme.json from Supabase storage URL."""
    supabase_url = os.getenv("SUPABASE_URL", "")
    svc_key = os.getenv("SUPABASE_SERVICE_KEY", "")

    if not scheme_url:
        raise HTTPException(404, "scheme_url이 없습니다")

    # If it's a full public URL just fetch it
    if scheme_url.startswith("http"):
        url = scheme_url
    else:
        # storage path like "building-data/11215/..." → build full URL
        url = f"{supabase_url}/storage/v1/object/{scheme_url}"

    headers = {}
    if svc_key:
        headers["Authorization"] = f"Bearer {svc_key}"

    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code == 200:
        return resp.json()
    # Try public access
    resp2 = requests.get(url, timeout=15)
    if resp2.status_code == 200:
        return resp2.json()

    raise HTTPException(502, f"scheme.json 다운로드 실패: {resp.status_code} {url}")


def upload_scheme_json(scheme_url: str, data: dict) -> None:
    """Upload modified scheme.json back to Supabase storage."""
    supabase_url = os.getenv("SUPABASE_URL", "")
    svc_key = os.getenv("SUPABASE_SERVICE_KEY", "")

    if not svc_key:
        raise HTTPException(500, "SUPABASE_SERVICE_KEY 환경변수 필요")

    if scheme_url.startswith("http"):
        # Extract path from URL
        # e.g. .../storage/v1/object/public/building-data/...
        for marker in ["/object/public/", "/object/"]:
            if marker in scheme_url:
                path = scheme_url.split(marker, 1)[1]
                break
        else:
            raise HTTPException(500, f"scheme_url 파싱 실패: {scheme_url}")
    else:
        path = scheme_url

    upload_url = f"{supabase_url}/storage/v1/object/{path}"
    headers = {
        "Authorization": f"Bearer {svc_key}",
        "Content-Type": "application/json",
        "x-upsert": "true",
    }
    resp = requests.post(upload_url, headers=headers, data=json.dumps(data), timeout=20)
    if resp.status_code not in [200, 201]:
        raise HTTPException(502, f"scheme.json 업로드 실패: {resp.status_code}")


# ─── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(title="SBIM Editor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost", "http://tauri.localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


# ─── Designs ──────────────────────────────────────────────────────────────────

@app.get("/designs")
def list_designs(limit: int = 30, offset: int = 0):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # 전체 개수
        cur.execute("SELECT COUNT(*) AS total FROM public.sbim_designs")
        total = cur.fetchone()["total"]

        cur.execute("""
            SELECT
                d.id,
                d.name,
                d.created_at,
                d.updated_at,
                COALESCE(
                    (SELECT dl.land_id FROM public.design_lands dl
                     WHERE dl.design_id = d.id AND dl.is_primary = true LIMIT 1),
                    (SELECT dl.land_id FROM public.design_lands dl
                     WHERE dl.design_id = d.id LIMIT 1)
                ) AS primary_land_id,
                ARRAY(
                    SELECT dl.land_id FROM public.design_lands dl
                    WHERE dl.design_id = d.id
                ) AS land_ids
            FROM public.sbim_designs d
            ORDER BY d.updated_at DESC NULLS LAST
            LIMIT %s OFFSET %s
        """, (min(limit, 100), offset))
        rows = cur.fetchall()
        cur.close()

    designs = []
    for row in rows:
        designs.append({
            "id": str(row["id"]),
            "name": row["name"] or "",
            "primary_land_id": str(row["primary_land_id"]) if row["primary_land_id"] else "",
            "land_ids": [str(l) for l in (row["land_ids"] or [])],
            "created_at": row["created_at"].isoformat() if row["created_at"] else "",
        })
    return {"designs": designs, "total": total, "offset": offset, "limit": limit}


# ─── Scheme ───────────────────────────────────────────────────────────────────

@app.get("/designs/{design_id}/scheme")
def get_scheme(design_id: str):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Get primary land_id for this design
        cur.execute("""
            SELECT
                COALESCE(
                    (SELECT dl.land_id FROM public.design_lands dl
                     WHERE dl.design_id = %s AND dl.is_primary = true LIMIT 1),
                    (SELECT dl.land_id FROM public.design_lands dl
                     WHERE dl.design_id = %s LIMIT 1)
                ) AS land_id
        """, (design_id, design_id))
        row = cur.fetchone()
        if not row or not row["land_id"]:
            raise HTTPException(404, f"design {design_id} 의 land_id를 찾을 수 없습니다")
        land_id = row["land_id"]

        # Get scheme_file_path
        cur.execute(
            "SELECT scheme_file_path FROM public.building_data WHERE land_id = %s ORDER BY updated_at DESC LIMIT 1",
            (land_id,)
        )
        bd = cur.fetchone()
        cur.close()

    if not bd or not bd["scheme_file_path"]:
        raise HTTPException(404, f"land_id={land_id} 의 scheme.json이 없습니다")

    scheme = fetch_scheme_json(bd["scheme_file_path"])
    return {"scheme": scheme, "land_id": land_id, "scheme_url": bd["scheme_file_path"]}



# ─── Context (주변 필지 + 도로) ───────────────────────────────────────────────

@app.get("/designs/{design_id}/context")
def get_context(design_id: str, radius: float = 150):
    """대상 필지 주변 radius m 이내의 필지·도로 폴리곤을 EPSG:5186 ring 으로 반환."""
    try:
     return _get_context_inner(design_id, radius)
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"context error: {e}", exc_info=True)
        raise HTTPException(500, str(e))

def _get_context_inner(design_id: str, radius: float):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 1. 대상 필지 PNU 조회
        cur.execute("""
            SELECT
                COALESCE(
                    (SELECT dl.land_id FROM public.design_lands dl
                     WHERE dl.design_id = %s AND dl.is_primary = true LIMIT 1),
                    (SELECT dl.land_id FROM public.design_lands dl
                     WHERE dl.design_id = %s LIMIT 1)
                ) AS land_id
        """, (design_id, design_id))
        row = cur.fetchone()
        if not row or not row["land_id"]:
            raise HTTPException(404, "design의 land_id를 찾을 수 없습니다")
        pnu = row["land_id"]

        # 기준점 (대상 필지 centroid, EPSG:5186)
        cur.execute("""
            SELECT ST_AsText(ST_Transform(ST_Centroid(geom), 5186)) AS center_wkt
            FROM public.lands WHERE pnu = %s LIMIT 1
        """, (pnu,))
        center_row = cur.fetchone()
        if not center_row:
            raise HTTPException(404, f"pnu={pnu} 필지를 찾을 수 없습니다")

        # 2. 주변 필지 (lands) — SRID:3857 확정 후 5186 변환
        cur.execute("""
            SELECT
                pnu,
                jibun,
                (pnu = %s) AS is_target,
                ST_AsGeoJSON(
                    ST_Transform(ST_SetSRID(geom, 3857), 5186)
                ) AS gj
            FROM public.lands
            WHERE ST_DWithin(
                ST_Transform(ST_SetSRID(geom, 3857), 5186),
                ST_GeomFromText(%s, 5186),
                %s
            )
            LIMIT 400
        """, (pnu, center_row["center_wkt"], radius))
        land_rows = cur.fetchall()

        # 3. 주변 도로 (roads) — SRID:3857 확정 후 5186 변환
        cur.execute("""
            SELECT
                pnu,
                rn_nm AS label,
                ST_AsGeoJSON(
                    ST_Transform(ST_SetSRID(geom, 3857), 5186)
                ) AS gj
            FROM public.roads
            WHERE ST_DWithin(
                ST_Transform(ST_SetSRID(geom, 3857), 5186),
                ST_GeomFromText(%s, 5186),
                %s
            )
            LIMIT 200
        """, (center_row["center_wkt"], radius))
        road_rows = cur.fetchall()
        cur.close()

    def geojson_to_rings(gj_str: str) -> list[list[list[float]]]:
        """GeoJSON MultiPolygon/Polygon → list of outer rings [[x,y],...]"""
        if not gj_str:
            return []
        gj = json.loads(gj_str)
        rings = []
        if gj["type"] == "Polygon":
            rings.append(gj["coordinates"][0])
        elif gj["type"] == "MultiPolygon":
            for poly in gj["coordinates"]:
                rings.append(poly[0])
        return rings

    parcels = []
    for r in land_rows:
        for ring in geojson_to_rings(r["gj"]):
            parcels.append({
                "ring": ring,
                "is_target": bool(r["is_target"]),
                "feature_type": "parcel",
                "label": r.get("jibun") or "",
            })

    roads = []
    for r in road_rows:
        for ring in geojson_to_rings(r["gj"]):
            roads.append({
                "ring": ring,
                "is_target": False,
                "feature_type": "road",
                "label": r.get("label") or "",
            })

    return {"parcels": parcels, "roads": roads}


# ─── Save scheme ──────────────────────────────────────────────────────────────

class SaveSchemeRequest(BaseModel):
    scheme: dict


@app.put("/designs/{design_id}/scheme")
def save_scheme(design_id: str, body: SaveSchemeRequest):
    """Supabase storage의 scheme.json을 수정된 내용으로 덮어씁니다."""
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT bd.scheme_file_path
            FROM public.building_data bd
            JOIN public.design_lands dl ON dl.land_id = bd.land_id
            WHERE dl.design_id = %s
            ORDER BY bd.updated_at DESC LIMIT 1
        """, (design_id,))
        row = cur.fetchone()
        cur.close()

    if not row or not row["scheme_file_path"]:
        raise HTTPException(404, f"design {design_id} 의 scheme.json 경로를 찾을 수 없습니다")

    upload_scheme_json(row["scheme_file_path"], body.scheme)
    return {"ok": True}


# ─── Units ────────────────────────────────────────────────────────────────────

@app.get("/designs/{design_id}/units")
def get_units(design_id: str):
    with get_conn() as conn:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                id, land_id, design_id, name, price,
                floor_id, floor_height, floor_bottom_height,
                area_net, area_common, area_service, area_contract,
                polygon, balcony_polygons
            FROM public.units
            WHERE design_id = %s
            ORDER BY floor_id, id
        """, (design_id,))
        rows = cur.fetchall()
        cur.close()

    units = []
    for row in rows:
        polygon = row["polygon"]
        if isinstance(polygon, str):
            polygon = json.loads(polygon)
        balcony_polygons = row["balcony_polygons"]
        if isinstance(balcony_polygons, str):
            balcony_polygons = json.loads(balcony_polygons)

        units.append({
            "id": str(row["id"]),
            "land_id": str(row["land_id"]),
            "design_id": str(row["design_id"]) if row["design_id"] else None,
            "name": row["name"] or "",
            "price": int(row["price"] or 0),
            "floor_id": int(row["floor_id"]),
            "floor_height": float(row["floor_height"] or 3.3),
            "floor_bottom_height": float(row["floor_bottom_height"] or 0),
            "area_net": float(row["area_net"] or 0),
            "area_common": float(row["area_common"] or 0),
            "area_service": float(row["area_service"] or 0),
            "area_contract": float(row["area_contract"] or 0),
            "polygon": polygon,
            "balcony_polygons": balcony_polygons or [],
        })

    return {"units": units}


# ─── Save units ───────────────────────────────────────────────────────────────

class SaveUnitsRequest(BaseModel):
    units: list[dict]


@app.put("/designs/{design_id}/units")
def save_units(design_id: str, body: SaveUnitsRequest):
    """Update polygon + balcony_polygons for each unit in the design."""
    now = datetime.now(timezone.utc).isoformat()

    with get_conn() as conn:
        cur = conn.cursor()
        try:
            for unit in body.units:
                unit_id = unit.get("id")
                polygon = unit.get("polygon")
                balcony_polygons = unit.get("balcony_polygons") or []

                cur.execute("""
                    UPDATE public.units
                    SET polygon = %s,
                        balcony_polygons = %s,
                        updated_at = %s
                    WHERE id = %s AND design_id = %s
                """, (
                    json.dumps(polygon) if polygon is not None else None,
                    json.dumps(balcony_polygons),
                    now,
                    unit_id,
                    design_id,
                ))
            conn.commit()
        except Exception as e:
            conn.rollback()
            log.error(f"save_units error: {e}")
            raise HTTPException(500, str(e))
        finally:
            cur.close()

    return {"ok": True, "updated": len(body.units)}


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[api] Starting SBIM Editor API on http://localhost:8765")
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
