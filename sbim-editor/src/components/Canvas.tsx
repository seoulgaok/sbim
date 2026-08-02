import React, { useEffect, useRef, useState } from "react";
import Konva from "konva";
import { Stage, Layer, Line, Circle, Text, Group } from "react-konva";
import { useStore } from "../store";
import {
  fitToCanvas, worldToScreen, ringToFlat, columnRect, collectAllCoords,
} from "../utils/coordTransform";
import type { Coord, ViewTransform } from "../types/sbim";

const C = {
  units: "#4A90E2", parking: "#E8A838",
  core_ev: "#9B59B6", core_stair: "#7B68EE", core_corridor: "#B39DDB",
  columns: "#5DA55D", piloti_path: "#E25757",
  parcel: "#666677", parcel_target: "#4A90E2",
  road: "#C8A96E",
  vertex: "#fff", vertex_stroke: "#333",
};
const VR = 5;

function sw(sx: number, sy: number, t: ViewTransform): Coord {
  return [(sx - t.offsetX) / t.scale, -(sy - t.offsetY) / t.scale];
}
function moveRing(ring: Coord[], idx: number, wx: number, wy: number): Coord[] {
  const n = [...ring] as Coord[];
  n[idx] = [wx, wy];
  if (idx === 0) n[n.length - 1] = [wx, wy];
  if (idx === n.length - 1) n[0] = [wx, wy];
  return n;
}

interface VHProps {
  ring: Coord[]; t: ViewTransform; closed?: boolean;
  onMove: (i: number, e: Konva.KonvaEventObject<DragEvent>) => void;
}
function VH({ ring, t, closed = true, onMove }: VHProps) {
  const end = closed ? ring.length - 1 : ring.length;
  return <>
    {ring.slice(0, end).map((c, i) => {
      const s = worldToScreen(c, t);
      return <Circle key={i} x={s.x} y={s.y} radius={VR}
        fill={C.vertex} stroke={C.vertex_stroke} strokeWidth={1.5}
        draggable onDragMove={(e) => onMove(i, e)} />;
    })}
  </>;
}

export function Canvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 800, h: 600 });
  const [xf, setXf] = useState<ViewTransform>({ scale: 20, offsetX: 0, offsetY: 0 });
  const [initialized, setInitialized] = useState(false);
  const isPan = useRef(false);
  const lastPt = useRef<{ x: number; y: number } | null>(null);

  const {
    designData, activeFloor, layers, editMode,
    selection, setSelection,
    editedUnits, updateUnitPolygon,
    editedScheme, updateParkingStall, updateColumnCenter, updateCorePolygon, updatePedestrianPath,
    setViewTransform,
  } = useStore();

  useEffect(() => {
    const el = containerRef.current; if (!el) return;
    const ro = new ResizeObserver(() => setSize({ w: el.clientWidth, h: el.clientHeight }));
    ro.observe(el); return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (!designData || initialized) return;
    const s = designData.scheme;
    const ctx = designData.context;
    const allUnits = (editedUnits ?? designData.units).filter(u => u.polygon).map(u => u.polygon!) as Coord[][];

    // context 포함해서 fit
    const ctxCoords: Coord[] = [
      ...(ctx?.parcels.flatMap(f => f.ring) ?? []),
      ...(ctx?.roads.flatMap(f => f.ring) ?? []),
    ];
    const all = [
      ...collectAllCoords(s._parking_stalls, s._column_centers, s._core_layout.ev, s._core_layout.stair, s._core_layout.corridor, allUnits, s._pedestrian_path ?? []),
      ...ctxCoords,
    ];
    const t = fitToCanvas(all.length ? all : collectAllCoords(s._parking_stalls, s._column_centers, s._core_layout.ev, s._core_layout.stair, s._core_layout.corridor, allUnits, []), size.w, size.h, 60);
    setXf(t); setViewTransform(t); setInitialized(true);
  }, [designData, size, initialized]);

  useEffect(() => { setInitialized(false); }, [designData]);

  const units     = editedUnits ?? designData?.units ?? [];
  const scheme    = editedScheme ?? designData?.scheme;
  const context   = designData?.context;
  const floorUnits = units.filter(u => u.floor_id === activeFloor && u.polygon);
  const lm        = Object.fromEntries(layers.map(l => [l.key, l.visible]));
  const isPiloti  = activeFloor === 1;
  const t         = xf;

  function onWheel(e: Konva.KonvaEventObject<WheelEvent>) {
    e.evt.preventDefault();
    const st = e.target.getStage(); if (!st) return;
    const p = st.getPointerPosition(); if (!p) return;
    const f = e.evt.deltaY < 0 ? 1.12 : 1 / 1.12;
    setXf(prev => {
      const scale = Math.min(Math.max(prev.scale * f, 1), 8000);
      return { scale, offsetX: p.x - (p.x - prev.offsetX) / prev.scale * scale, offsetY: p.y + (p.y - prev.offsetY) / prev.scale * scale };
    });
  }
  function onDown(e: Konva.KonvaEventObject<MouseEvent>) {
    if (e.target === e.target.getStage() || editMode === "pan") { isPan.current = true; lastPt.current = { x: e.evt.clientX, y: e.evt.clientY }; }
  }
  function onMove(e: Konva.KonvaEventObject<MouseEvent>) {
    if (!isPan.current || !lastPt.current) return;
    const dx = e.evt.clientX - lastPt.current.x, dy = e.evt.clientY - lastPt.current.y;
    lastPt.current = { x: e.evt.clientX, y: e.evt.clientY };
    setXf(p => ({ ...p, offsetX: p.offsetX + dx, offsetY: p.offsetY + dy }));
  }
  function onUp() { isPan.current = false; lastPt.current = null; }

  function toggleSel(type: typeof selection.type, id: string) {
    if (editMode === "pan") return;
    setSelection(selection.type === type && selection.id === id ? { type: null, id: null } : { type, id });
  }

  if (!designData) return (
    <div ref={containerRef} className="canvas-container empty">
      <div className="canvas-placeholder">← 왼쪽에서 디자인을 선택하세요</div>
    </div>
  );

  return (
    <div ref={containerRef} className="canvas-container">
      <Stage width={size.w} height={size.h}
        onWheel={onWheel} onMouseDown={onDown} onMouseMove={onMove} onMouseUp={onUp}
        style={{ cursor: editMode === "pan" ? "grab" : "default" }}>
        <Layer>

          {/* ══ 도로 배경 (맨 아래) ══ */}
          {lm.roads && context?.roads.map((f, i) => (
            <Line key={`road-${i}`}
              points={ringToFlat(f.ring, t)} closed
              fill={C.road + "55"} stroke={C.road} strokeWidth={1}
              listening={false} />
          ))}

          {/* ══ 주변 필지 배경 ══ */}
          {lm.parcels && context?.parcels.map((f, i) => (
            <Line key={`parcel-${i}`}
              points={ringToFlat(f.ring, t)} closed
              fill={f.is_target ? C.parcel_target + "22" : C.parcel + "18"}
              stroke={f.is_target ? C.parcel_target : C.parcel}
              strokeWidth={f.is_target ? 2 : 0.8}
              dash={f.is_target ? undefined : undefined}
              listening={false} />
          ))}

          {/* ══ 1층 필로티 ══ */}
          {isPiloti && scheme && (
            <Group>
              {/* 주차 구획 — 드래그로 이동, 클릭으로 버텍스 편집 선택 */}
              {lm.parking && scheme._parking_stalls.map((stall, si) => {
                const sel = selection.type === "parking_stall" && selection.id === String(si);
                return <Group key={`st-${si}`}>
                  <Line
                    points={ringToFlat(stall, t)} closed
                    fill={C.parking + (sel ? "77" : "44")}
                    stroke={C.parking} strokeWidth={sel ? 2.5 : 1.5}
                    draggable
                    onDragStart={(e) => {
                      // 드래그 시작 시 기존 선택 해제
                      e.cancelBubble = true;
                    }}
                    onDragEnd={(e) => {
                      // 노드 이동량(px) → 월드 델타
                      const dx =  e.target.x() / t.scale;
                      const dy = -e.target.y() / t.scale;   // Y축 반전
                      const newRing = stall.map(([x, y]) => [x + dx, y + dy] as Coord);
                      updateParkingStall(si, newRing);
                      e.target.position({ x: 0, y: 0 });    // 노드 위치 리셋
                    }}
                    onClick={(e) => {
                      // 드래그 없이 클릭만 했을 때만 선택 토글
                      if (e.target.x() === 0 && e.target.y() === 0) {
                        toggleSel("parking_stall", String(si));
                      }
                    }}
                    onMouseEnter={(e) => {
                      const stage = e.target.getStage();
                      if (stage) stage.container().style.cursor = "move";
                    }}
                    onMouseLeave={(e) => {
                      const stage = e.target.getStage();
                      if (stage) stage.container().style.cursor = editMode === "pan" ? "grab" : "default";
                    }}
                  />
                  {sel && <VH ring={stall} t={t} onMove={(vi, e) => {
                    const [wx, wy] = sw(e.target.x(), e.target.y(), t);
                    updateParkingStall(si, moveRing(stall, vi, wx, wy));
                  }} />}
                </Group>;
              })}

              {/* 기둥 */}
              {lm.columns && scheme._column_centers.map((center, ci) => {
                const cs = scheme._column_size ?? 0.4;
                const sel = selection.type === "column" && selection.id === String(ci);
                const sc = worldToScreen(center, t);
                return <Group key={`col-${ci}`}>
                  <Line points={columnRect(center, cs, t)} closed
                    fill={C.columns + (sel ? "cc" : "88")} stroke={C.columns} strokeWidth={sel ? 2.5 : 1.5}
                    onClick={() => toggleSel("column", String(ci))} style={{ cursor: "pointer" }} />
                  {sel && <Circle x={sc.x} y={sc.y} radius={VR + 2}
                    fill={C.vertex} stroke={C.columns} strokeWidth={2} draggable
                    onDragMove={e => { const [wx, wy] = sw(e.target.x(), e.target.y(), t); updateColumnCenter(ci, [wx, wy]); }} />}
                </Group>;
              })}

              {/* 보행 동선 */}
              {lm.piloti_path && scheme._pedestrian_path && (() => {
                const sel = selection.type === "piloti_path" && selection.id === "0";
                return <Group>
                  <Line points={ringToFlat(scheme._pedestrian_path, t)}
                    stroke={C.piloti_path} strokeWidth={sel ? 3 : 2} dash={[8, 4]} hitStrokeWidth={12}
                    onClick={() => toggleSel("piloti_path", "0")} style={{ cursor: "pointer" }} />
                  {sel && <VH ring={scheme._pedestrian_path} t={t} closed={false}
                    onMove={(vi, e) => {
                      if (!scheme._pedestrian_path) return;
                      const path = [...scheme._pedestrian_path] as Coord[];
                      const [wx, wy] = sw(e.target.x(), e.target.y(), t);
                      path[vi] = [wx, wy]; updatePedestrianPath(path);
                    }} />}
                </Group>;
              })()}

              {/* 코어 */}
              {lm.core && (["ev", "stair", "corridor"] as const).map(part => {
                const ring = scheme._core_layout[part]; if (!ring?.length) return null;
                const color = part === "ev" ? C.core_ev : part === "stair" ? C.core_stair : C.core_corridor;
                const st = `core_${part}` as typeof selection.type;
                const sel = selection.type === st && selection.id === "0";
                const label = part === "ev" ? "EV" : part === "stair" ? "계단" : "복도";
                const cx = ring.reduce((s, c) => s + c[0], 0) / ring.length;
                const cy = ring.reduce((s, c) => s + c[1], 0) / ring.length;
                const sc = worldToScreen([cx, cy], t);
                return <Group key={part}>
                  <Line points={ringToFlat(ring, t)} closed
                    fill={color + (sel ? "bb" : "77")} stroke={color} strokeWidth={sel ? 2.5 : 1.5}
                    onClick={() => toggleSel(st, "0")} style={{ cursor: "pointer" }} />
                  <Text x={sc.x - 14} y={sc.y - 7} text={label} fontSize={10} fill={color} fontStyle="bold" listening={false} />
                  {sel && <VH ring={ring} t={t} onMove={(vi, e) => {
                    const [wx, wy] = sw(e.target.x(), e.target.y(), t);
                    updateCorePolygon(part, moveRing(ring, vi, wx, wy));
                  }} />}
                </Group>;
              })}
            </Group>
          )}

          {/* ══ 세대 유닛 ══ */}
          {lm.units && floorUnits.map(unit => {
            if (!unit.polygon) return null;
            const ring = unit.polygon;
            const sel = selection.type === "unit" && selection.id === unit.id;
            const cx = ring.reduce((s, c) => s + c[0], 0) / ring.length;
            const cy = ring.reduce((s, c) => s + c[1], 0) / ring.length;
            const sc = worldToScreen([cx, cy], t);
            return <Group key={unit.id}>
              <Line points={ringToFlat(ring, t)} closed
                fill={C.units + (sel ? "55" : "33")} stroke={C.units} strokeWidth={sel ? 2.5 : 1.5}
                onClick={() => toggleSel("unit", unit.id)} style={{ cursor: "pointer" }} />
              {unit.balcony_polygons?.map((bp, bi) =>
                <Line key={bi} points={ringToFlat(bp, t)} closed
                  fill={C.units + "22"} stroke={C.units + "99"} strokeWidth={1} dash={[4, 3]} listening={false} />
              )}
              <Text x={sc.x - 20} y={sc.y - 7} text={`${unit.area_net.toFixed(1)}㎡`}
                fontSize={10} fill={C.units} listening={false} />
              {sel && editMode === "select" && <VH ring={ring} t={t} onMove={(vi, e) => {
                const [wx, wy] = sw(e.target.x(), e.target.y(), t);
                updateUnitPolygon(unit.id, moveRing(ring, vi, wx, wy));
              }} />}
            </Group>;
          })}

        </Layer>
      </Stage>
    </div>
  );
}
