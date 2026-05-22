/**
 * Seoulgaok BIM core — TypeScript types for scheme.json
 *
 * JSON Schema 단일 진실은 schema/*.json에 있음.
 * 이 파일은 동기화되어야 함 (수동 또는 json-schema-to-typescript).
 */

// --- BufferGeometry (THREE.js serialized) ----------------------------------

export interface BufferAttributeData {
  itemSize: number;
  type: string; // e.g. "Float32Array"
  array: number[];
}

export interface BufferGeometryData {
  metadata: {
    version: number;
    type: string;
    generator: string;
  };
  uuid: string;
  type: "BufferGeometry";
  data: {
    attributes: {
      position: BufferAttributeData;
      normal: BufferAttributeData;
      uv?: BufferAttributeData | null;
    };
    index: {
      type: string;
      array: number[];
    };
  };
}

// --- Floor / FloorPlan -----------------------------------------------------

export interface FloorData {
  /** 층 ID. -1=지하1, 0=주차/필로티, 1+=일반 */
  floor_id: number;
  floor_area: number;
  floor_height: number;
  floor_bottom_height: number;
}

export interface FloorGeometry {
  walls: BufferGeometryData[][];
  floors: BufferGeometryData[][];
  roof?: BufferGeometryData[][];
  /** 외벽 면별 창. 향별 WWR 기반 quad face. wall과 같은 평면에 ±epsilon. */
  windows?: BufferGeometryData[][];
  /** 파라펫(난간). step-back 노출 외곽 + 최상층 옥상 외곽에 1.1m 높이 wall. */
  parapets?: BufferGeometryData[][];
  /** 필로티 기둥. 1층 piloti 층에서만 채워짐. 0.4×0.4m × 1층 floor_height prism. */
  columns?: BufferGeometryData[][];
  /** 주차 stall 외곽선. 1층 piloti에 배치. base_z 살짝 위 quad. */
  parking_stalls?: BufferGeometryData[][];
}

export interface FloorPlan {
  data: FloorData;
  geom: FloorGeometry;
}

// --- Scheme (top-level) ----------------------------------------------------

export interface SchemeData {
  /** 대지면적 ㎡ */
  lot_area: number;
  /** 건축면적 ㎡ */
  build_area: number;
  /** 용적률 */
  far: number;
  /** 건폐율 */
  bcr: number;
  /** 부동산고유번호 */
  pnu: number | string;
}

export interface Scheme {
  data: SchemeData;
  floor_plans: FloorPlan[];
  unit_ids: string[];
}

// --- Unit -------------------------------------------------------------------

export interface UnitGeometry {
  boundary: BufferGeometryData[];
}

export interface UnitData {
  id: string;
  name: string;
  price: number;
  floor_id: number;
  floor_height: number;
  floor_bottom_height: number;
  /** 전용 ㎡ — 발코니 차감 후 (주차 산정 기준) */
  area_net: number;
  /** 공용 ㎡ — 계단·EV·복도 지분 안분 */
  area_common: number;
  /** 대지지분 ㎡ */
  land_portion: number;
  /** 분양 ㎡ = net + common */
  area_contract: number;
  /** 베란다 ㎡ — 위층 step-back 슬래브 (건축법 정의) */
  area_veranda: number;
  /** 발코니 ㎡ — 외벽 캔틸레버 (목적: 전용 임계 하향 → 주차 절감) */
  area_balcony: number;
  /** 발코니 실효 폭 (m, ≤ 1.5 법정) */
  balcony_depth: number;
  /** legacy alias = area_veranda (신규 코드는 area_veranda 사용) */
  area_service: number;
}

export interface Unit {
  geom: UnitGeometry;
  data: UnitData;
}

// --- Surroundings ----------------------------------------------------------

export interface SurroundingGeometry {
  boundary: BufferGeometryData[];
}

export interface SurroundingData {
  address?: string;
  /** 건물 높이 m */
  height: number;
  /** 층수 */
  floor: number;
}

export interface SurroundingBuilding {
  geom: SurroundingGeometry;
  data: SurroundingData;
}
