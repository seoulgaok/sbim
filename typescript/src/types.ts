/**
 * Seoulgaok BIM core — scheme.json / units.json 데이터 계약의 **단일 진실**.
 *
 * 규율: 생성기가 새 키·userData kind를 방출하려면 여기(+python/types.py)에
 * 먼저 정의하고 sbim을 푸시한 뒤 소비처가 import한다.
 * schema/*.json은 walls/floors/roof 시절의 산물 — 현재 정본은 이 파일이다.
 *
 * 좌표계: 링·점 좌표는 EPSG:5186 절대(parcel_center 더해진 상태).
 * 메시(BufferGeometry positions)만 parcel_center 상대 — 혼동 금지.
 */

/** EPSG:5186 절대 좌표점 */
export type Point2 = [number, number];
/** 닫힘 여부 무관 좌표 링 */
export type Ring = Point2[];

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
  /** LOD300 부재 메타 (three.js BufferGeometry JSON 표준 필드).
   *  좌표는 EPSG:5186 절대(_core_layout·_column_centers와 동일 프레임) —
   *  메시 positions는 parcel_center 상대이므로 혼동 금지. */
  userData?: PartUserData | Record<string, unknown>;
}

// --- LOD300 부재 userData (kind 판별 유니언) --------------------------------

export interface MaterialLayer {
  name: string;
  /** 두께 (m) */
  t: number;
}

export interface WallUserData {
  kind: "wall";
  /** 벽 중심선 양끝 (EPSG:5186 절대) */
  p0: Point2;
  p1: Point2;
  /** 구조 두께 (m) — 중심선 양쪽 t/2 */
  t: number;
  /** 총두께 (m) = 구조 + 단열 + 마감 — 개구는 이걸로 뚫는다 */
  t_total?: number;
  /** 기준선(구조 중심)→외피 오프셋 (m) — IFC 레이어셋 offset */
  offset_out?: number;
  exterior: boolean;
  base_z: number;
  top_z: number;
  /** 마이터 확정 quad (emitter 단일 소스) — 있으면 재계산 없이 이걸 그린다 */
  quad?: Ring;
  /** 안→밖 순 레이어 (구조/단열/마감) */
  layers: MaterialLayer[];
}

export interface SlabUserData {
  kind: "slab";
  /** 슬래브 외곽 ring (절대) */
  outline: Ring;
  t: number;
  /** 구조체 두께 (m) — t는 마감 포함 총두께 */
  t_struct?: number;
  /** 상면 z — 두께는 하향 점유 (층 레벨 수치 불변) */
  top_z: number;
  role: "interfloor" | "foundation" | "roof";
  layers?: MaterialLayer[];
}

export interface ColumnUserData {
  kind: "column";
  center: Point2;
  size: number;
  base_z: number;
  top_z: number;
  /** 전이보와 만나는 기둥인가 */
  transfer: boolean;
}

export interface BeamUserData {
  kind: "beam";
  p0: Point2;
  p1: Point2;
  /** 폭 (m) */
  w: number;
  /** 춤 (m) — top_z에서 하향 */
  h: number;
  top_z: number;
  role: "transfer" | "sloped";
}

/** 개구부 호스트 벽 (IFC RelVoids·2D gap 매칭용) */
export interface HostWallRef {
  p0: Point2;
  p1: Point2;
  t: number;
  t_total?: number;
}

export interface DoorUserData {
  kind: "door";
  p0: Point2;
  p1: Point2;
  width: number;
  height: number;
  unit_id?: string;
  /** "공동현관" | "욕실" | "옥상" 등 — 없으면 세대 현관 */
  door_type?: string;
  fire_exit?: boolean;
  /** 스윙이 향할 실내 기준점 — 세대문=복도쪽 밖여닫이, 욕실문=거실쪽 */
  swing_into?: Point2;
  host_wall?: HostWallRef;
}

export interface WindowUserData {
  kind: "window";
  p0: Point2;
  p1: Point2;
  width: number;
  height: number;
  /** 창대 높이 (층 바닥 기준 m) */
  sill: number;
  /** 호스트 벽 구조 두께 (m) */
  wall_t?: number;
  /** 호스트 벽 총두께 — 개구를 이걸로 뚫어야 단열 띠까지 끊긴다 */
  wall_total?: number;
  /** 창 유형 라벨 (채광 역산 배치) */
  type?: string;
  unit_id?: string;
  host_wall?: HostWallRef;
}

export interface CoveringUserData {
  kind: "covering";
  role: "ceiling" | "flooring" | string;
  t: number;
  top_z: number;
  outline: Ring;
  layers?: MaterialLayer[];
}

export interface RailingUserData {
  kind: "railing";
  base_z: number;
  top_z: number;
  /** 하부 낮은벽 상단 z (0이면 동자+손스침만) */
  wall_top_z: number;
  /** 손스침 단면 (m) */
  bar: number;
  /** 난간 라인 세그먼트들 (절대) */
  lines: Ring[];
}

/** 계단 3D 부재 분해 (IFC IfcMember SF RISER/TREAD/LANDING) */
export interface StairMemberUserData {
  kind: "stair_member";
  part: "tread" | "riser" | "landing" | string;
  index: number;
  z0: number;
  z1: number;
}

/** 코어 6타입 정답지 배치 항목 (생성기 코어 단계 정답지).
 *  flight quad = [시작변0, 시작변1, 끝변1, 끝변0] — p0→p3 = 진행(오름) 방향 */
export interface StairLayoutItem {
  role: "flight" | "landing";
  quad: Ring;
  /** flight 단수 (landing엔 없음) */
  n?: number;
}

export interface StairUserData {
  kind: "stair";
  /** 계단실 quad (절대) */
  quad: Ring;
  riser: number;
  tread: number;
  n_risers: number;
  waist: number;
  flights: number;
  /** 정답지 6타입 배치 — 있으면 arms/quad보다 우선 소비 */
  layout?: StairLayoutItem[];
  /** (구) ㄱ자 3분해 [긴팔, 짧은팔, 코너참] — layout 없는 구 scheme용 */
  arms?: Ring[];
  runs?: number[];
}

export type PartUserData =
  | WallUserData
  | SlabUserData
  | ColumnUserData
  | BeamUserData
  | DoorUserData
  | WindowUserData
  | CoveringUserData
  | RailingUserData
  | StairUserData
  | StairMemberUserData;

// --- Floor / FloorPlan -----------------------------------------------------

export interface FloorData {
  /** 층 ID. -1=지하1, 0=주차/필로티, 1+=일반 */
  floor_id: number;
  floor_area: number;
  floor_height: number;
  floor_bottom_height: number;
  /** 옥탑층·지붕층 등 특수 층 이름 (숫자 라벨 무의미) */
  floor_name?: string;
  parking_count?: number;
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
  /** 세대 출입문. userData.kind="door" — 문짝 quad + 호스트 벽. */
  doors?: BufferGeometryData[][];
  /** 보. 1층 전이보(600×800) 등. userData.kind="beam". */
  beams?: BufferGeometryData[][];
  /** 계단 단·계단판. userData.kind="stair" (riser/tread/waist 치수). */
  stairs?: BufferGeometryData[][];
  /** 마감. 1층 천장마감·테라스 판석 등. userData.kind="covering". */
  coverings?: BufferGeometryData[][];
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

/** 코어 내부 분할 — 링은 EPSG 절대 */
export interface CoreLayout {
  ev?: Ring;
  stair?: Ring;
  corridor?: Ring;
  ev_front?: Ring;
}

/** scheme.json 최상위 밑줄 키 — 생성기 scheme 방출부 방출 계약.
 *  전부 옵셔널 (구 scheme 호환). */
export interface SchemeSpatial {
  _core_layout?: CoreLayout;
  _parking_stalls?: Ring[];
  _column_centers?: Point2[];
  _basement_outline?: Ring | null;
  /** 층별 footprint ring — 복도(=층외곽−세대−코어) 유도 기준 */
  _floor_outlines?: Record<string, Ring>;
  /** 보행 출입로 (도로→코어) — 보행 경로 산출. 1F 전용 */
  _pedestrian_path?: Ring | null;
  /** 옥탑(계단탑) 외곽 — 옥탑층·지붕층 평면이 공유 */
  _penthouse_outline?: Ring | null;
  /** 전층 교집합 — 코어 탐색공간 */
  _common_footprint?: Ring | null;
  /** 준법 위반·경고 메모 */
  _validation?: string[];
  /** 기둥 단면 한 변 (m) — Concrete.column_size 확정값. 도면 재구성이
   *  scheme만 보고도 같은 크기를 그리도록 방출(폴백 이원화 방지). */
  _column_size?: number | null;
  /** 정북일조 기준선 (EPSG:5186 절대, 변마다 [p1,p2]) — 3D 뷰어 천공면.
   *  북향 변마다 별도 엣지(상업 인접 면제·도로 인접은 중심선 offset),
   *  매스 깎기(apply_north_setback)와 동일 기준. 면제면 []. */
  _north_ref_edges?: [Point2, Point2][];
  /** 정북일조 기산면 보정 (m) — 영 119조①5호 나목: 높이는 본 대지와 북측
   *  인접대지의 평균 수평면 기준. z0 − 본 대지 지표면 = 고저차의 1/2.
   *  천공면 그리기: 유효높이 h' = z − 이 값 (경사지에서 프로파일이 수직으로
   *  이동). 미방출·null이면 0(평지 가정). */
  _north_datum_offset?: number | null;
  /** 법규 체크리스트 33항목 판정 실값 (giga legal_checklist.yaml SSOT, #16).
   *
   *  합격/불합격이 아니라 **적용여부 + 산출값**이다 — 엔진은 규제를 생성
   *  단계에서 지켜버리므로(사선은 매스를 깎고, 미충족은 compile_errors)
   *  완성 설계에 '미달' 항목이 존재할 수 없다. law-graph가 결정 노드에서
   *  근거 조문으로 엣지를 이을 때 이 실값을 쓴다.
   *  key는 legal_checklist.yaml의 key와 일치(변경 금지 — 그래프 노드 id).
   *  구 scheme엔 없다 — 소비처는 부재를 "구 버전"으로 처리할 것. */
  _legal_checks?: {
    key: string;
    group: string;
    item: string;
    /** '적용' | '해당없음' | '검토' | '참고' 또는 실값 포함('적용 (확폭 12㎡)') */
    status: string;
    /** 적용 내용 — 산출값 채워진 문장 */
    apply: string;
    /** 근거 조문 */
    law: string;
    note?: string;
  }[];
}

export interface Scheme extends SchemeSpatial {
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

// --- units.json (생성기 직렬화 실계약) ----------------------------------------
// 위 Unit/UnitData(flat area_*)는 BuildingVisualizer 레거시 경로용 —
// 생성기가 실제로 쓰는 units.json 레코드는 아래 UnitRecord(중첩 area{})다.
// 형식 통일은 별도 트랙; 신규 소비 코드는 UnitRecord를 쓴다.

export interface UnitAreaBreakdown {
  net?: number;
  common?: number;
  land_portion?: number;
  contract?: number;
  veranda?: number;
  veranda_eq?: number;
  balcony?: number;
  balcony_depth?: number;
  service?: number;
  actual_use?: number;
  duplex_upper?: number;
}

/** 방 최소 의미론 — 벽·문 기하는 geom userData가 따로 옴 */
export interface UnitRoom {
  use: "욕실" | "주방" | string;
  polygon: Ring;
}

/** units.json 레코드 — 생성기 units 직렬화 계약 */
export interface UnitRecord {
  id: string;
  floor: number;
  floor_height?: number | null;
  floor_bottom_height?: number | null;
  price: number;
  area: UnitAreaBreakdown;
  /** 메시 경계 — DB 저장 시 Json이라 소비 경계에서 형태 미보장(null 허용) */
  geom?: UnitGeometry | null | unknown;
  /** 주층 단일 ring (EPSG 절대) — polygons_by_floor의 호환용 */
  polygon?: Ring | null;
  duplex_upper_polygon?: Ring | null;
  balcony_polygons?: Ring[];
  /** 층별 점유 맵 {floor: ring} — 복층 포함 단일 표현 (생성기 계약 ③) */
  polygons_by_floor?: Record<string, Ring>;
  rooms?: UnitRoom[];
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
