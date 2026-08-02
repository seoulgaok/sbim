// ─── Coordinate types ───────────────────────────────────────────────────────
/** EPSG:5186 coordinate [x, y] in meters */
export type Coord = [number, number];

/** Screen coordinate */
export type ScreenCoord = { x: number; y: number };

// ─── Supabase design ─────────────────────────────────────────────────────────
export interface Design {
  id: string;
  name: string;
  land_ids: string[];
  primary_land_id: string;
  created_at: string;
}

// ─── Scheme data (from scheme.json) ─────────────────────────────────────────
export interface FloorData {
  floor_id: number;
  floor_area: number;
  floor_height: number;
  floor_bottom_height: number;
  parking_count?: number;
}

export interface FloorPlan {
  data: FloorData;
  /** raw ThreeJS geom – only used for reference, not edited directly */
  geom?: Record<string, unknown>;
}

export interface CoreLayout {
  ev: Coord[];
  stair: Coord[];
  corridor: Coord[];
}

export interface SchemeData {
  lot_area: number;
  build_area: number;
  far: number;
  bcr: number;
  pnu: string;
}

export interface Scheme {
  data: SchemeData;
  floor_plans: FloorPlan[];
  unit_ids: string[];
  _core_layout: CoreLayout;
  _column_centers: Coord[];
  _parking_stalls: Coord[][];   // each stall = closed ring of coords
  _column_size: number;
  _pedestrian_path?: Coord[];
}

// ─── Units (from Supabase units table) ───────────────────────────────────────
export interface Unit {
  id: string;
  land_id: string;
  design_id?: string;
  name: string;
  floor_id: number;
  floor_height: number;
  floor_bottom_height: number;
  area_net: number;
  area_contract: number;
  price: number;
  /** EPSG:5186 closed ring */
  polygon: Coord[] | null;
  /** list of balcony polygons */
  balcony_polygons: Coord[][] | null;
}

// ─── Context (주변 필지 + 도로) ──────────────────────────────────────────────
export interface ContextFeature {
  /** outer ring. holes는 별도 저장 안 함 (단순화) */
  ring: Coord[];
  is_target: boolean;
  feature_type: "parcel" | "road";
  /** 도로명, 지번 등 표시용 */
  label?: string;
}

export interface ContextData {
  parcels: ContextFeature[];
  roads: ContextFeature[];
}

// ─── Editor state ─────────────────────────────────────────────────────────────
export type LayerKey = "parcels" | "roads" | "units" | "parking" | "core" | "columns" | "piloti_path";

export interface EditorLayer {
  key: LayerKey;
  label: string;
  color: string;
  visible: boolean;
}

export type EditMode = "select" | "move_vertex" | "pan";

// ─── Transform ────────────────────────────────────────────────────────────────
export interface ViewTransform {
  /** pixels per meter */
  scale: number;
  /** canvas-space offset (pixels) */
  offsetX: number;
  offsetY: number;
}

// ─── Loaded design data ───────────────────────────────────────────────────────
export interface DesignData {
  design: Design;
  scheme: Scheme;
  units: Unit[];
  context: ContextData | null;
}

// ─── API response types ───────────────────────────────────────────────────────
export interface ApiDesignsResponse {
  designs: Design[];
}

export interface ApiSchemeResponse {
  scheme: Scheme;
}

export interface ApiUnitsResponse {
  units: Unit[];
}
