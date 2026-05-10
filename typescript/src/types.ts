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
  /** 외벽 외측 발코니 슬래브 + 난간. 향별(남·동·서) 외벽 edge별로 생성. */
  balconies?: BufferGeometryData[][];
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
  /** 전용면적 ㎡ */
  area_net: number;
  /** 공용면적 ㎡ */
  area_common: number;
  /** 대지지분 ㎡ */
  land_portion: number;
  /** 서비스면적 ㎡ */
  area_service: number;
  /** 계약면적 ㎡ */
  area_contract: number;
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
