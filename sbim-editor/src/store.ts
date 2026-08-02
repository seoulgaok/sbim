import { create } from "zustand";
import type {
  Design,
  DesignData,
  EditMode,
  LayerKey,
  EditorLayer,
  Coord,
  Unit,
  Scheme,
  ViewTransform,
} from "./types/sbim";


const DEFAULT_LAYERS: EditorLayer[] = [
  { key: "parcels",     label: "주변 필지",      color: "#888888", visible: true },
  { key: "roads",       label: "도로",           color: "#C8A96E", visible: true },
  { key: "units",       label: "세대 유닛",      color: "#4A90E2", visible: true },
  { key: "parking",     label: "주차 구획",      color: "#E8A838", visible: true },
  { key: "core",        label: "코어 (EV·계단)", color: "#7B68EE", visible: true },
  { key: "columns",     label: "필로티 기둥",    color: "#5DA55D", visible: true },
  { key: "piloti_path", label: "보행 동선",      color: "#E25757", visible: true },
];

export interface SelectionState {
  type: "unit" | "parking_stall" | "core_ev" | "core_stair" | "core_corridor" | "column" | "piloti_path" | null;
  /** unit id, or stall/column index as string */
  id: string | null;
}

interface AppState {
  designs: Design[];
  setDesigns: (d: Design[]) => void;

  designData: DesignData | null;
  setDesignData: (d: DesignData | null) => void;

  activeFloor: number;
  setActiveFloor: (f: number) => void;

  layers: EditorLayer[];
  toggleLayer: (key: LayerKey) => void;

  editMode: EditMode;
  setEditMode: (m: EditMode) => void;

  selection: SelectionState;
  setSelection: (s: SelectionState) => void;

  viewTransform: ViewTransform;
  setViewTransform: (t: ViewTransform) => void;

  // ── 유닛 편집 ────────────────────────────────────────────────────────────
  isDirtyUnits: boolean;
  editedUnits: Unit[] | null;
  setEditedUnits: (u: Unit[] | null) => void;
  updateUnitPolygon: (unitId: string, newRing: Coord[]) => void;

  // ── 스킴 편집 (필로티 레이어) ────────────────────────────────────────────
  isDirtyScheme: boolean;
  editedScheme: Scheme | null;
  /** 주차 구획 ring 수정 */
  updateParkingStall: (stallIdx: number, newRing: Coord[]) => void;
  /** 기둥 중심 이동 */
  updateColumnCenter: (colIdx: number, newCenter: Coord) => void;
  /** 코어 폴리곤 수정 */
  updateCorePolygon: (part: "ev" | "stair" | "corridor", newRing: Coord[]) => void;
  /** 보행 동선 수정 */
  updatePedestrianPath: (newPath: Coord[]) => void;
  /** 스킴 편집 초기화 */
  resetScheme: () => void;

  isLoading: boolean;
  setLoading: (l: boolean) => void;
  /** 특정 디자인 로딩 중 (scheme + units + context) — 캔버스 오버레이용 */
  isLoadingDesign: boolean;
  loadingDesignName: string;
  setLoadingDesign: (loading: boolean, name?: string) => void;
  loadError: string | null;
  setLoadError: (e: string | null) => void;
}

function cloneScheme(s: Scheme): Scheme {
  return JSON.parse(JSON.stringify(s));
}

export const useStore = create<AppState>((set, get) => ({
  designs: [],
  setDesigns: (designs) => set({ designs }),

  designData: null,
  setDesignData: (designData) => set({
    designData,
    editedUnits: null,
    editedScheme: null,
    isDirtyUnits: false,
    isDirtyScheme: false,
    activeFloor: 1,
    selection: { type: null, id: null },
  }),

  activeFloor: 1,
  setActiveFloor: (activeFloor) => set({ activeFloor }),

  layers: DEFAULT_LAYERS,
  toggleLayer: (key) =>
    set((s) => ({
      layers: s.layers.map((l) => (l.key === key ? { ...l, visible: !l.visible } : l)),
    })),

  editMode: "select",
  setEditMode: (editMode) => set({ editMode }),

  selection: { type: null, id: null },
  setSelection: (selection) => set({ selection }),

  viewTransform: { scale: 20, offsetX: 0, offsetY: 0 },
  setViewTransform: (viewTransform) => set({ viewTransform }),

  // ── 유닛 편집 ────────────────────────────────────────────────────────────
  isDirtyUnits: false,
  editedUnits: null,
  setEditedUnits: (editedUnits) => set({ editedUnits, isDirtyUnits: false }),

  updateUnitPolygon: (unitId, newRing) => {
    const { editedUnits, designData } = get();
    const base = editedUnits ?? designData?.units ?? [];
    const next = base.map((u) => u.id === unitId ? { ...u, polygon: newRing } : u);
    set({ editedUnits: next, isDirtyUnits: true });
  },

  // ── 스킴 편집 ─────────────────────────────────────────────────────────────
  isDirtyScheme: false,
  editedScheme: null,

  updateParkingStall: (stallIdx, newRing) => {
    const { editedScheme, designData } = get();
    const base = editedScheme ?? (designData ? cloneScheme(designData.scheme) : null);
    if (!base) return;
    const next = cloneScheme(base);
    next._parking_stalls[stallIdx] = newRing;
    set({ editedScheme: next, isDirtyScheme: true });
  },

  updateColumnCenter: (colIdx, newCenter) => {
    const { editedScheme, designData } = get();
    const base = editedScheme ?? (designData ? cloneScheme(designData.scheme) : null);
    if (!base) return;
    const next = cloneScheme(base);
    next._column_centers[colIdx] = newCenter;
    set({ editedScheme: next, isDirtyScheme: true });
  },

  updateCorePolygon: (part, newRing) => {
    const { editedScheme, designData } = get();
    const base = editedScheme ?? (designData ? cloneScheme(designData.scheme) : null);
    if (!base) return;
    const next = cloneScheme(base);
    next._core_layout[part] = newRing;
    set({ editedScheme: next, isDirtyScheme: true });
  },

  updatePedestrianPath: (newPath) => {
    const { editedScheme, designData } = get();
    const base = editedScheme ?? (designData ? cloneScheme(designData.scheme) : null);
    if (!base) return;
    const next = cloneScheme(base);
    next._pedestrian_path = newPath;
    set({ editedScheme: next, isDirtyScheme: true });
  },

  resetScheme: () => set({ editedScheme: null, isDirtyScheme: false }),

  isLoading: false,
  setLoading: (isLoading) => set({ isLoading }),
  isLoadingDesign: false,
  loadingDesignName: "",
  setLoadingDesign: (isLoadingDesign, name = "") => set({ isLoadingDesign, loadingDesignName: name }),
  loadError: null,
  setLoadError: (loadError) => set({ loadError }),
}));
