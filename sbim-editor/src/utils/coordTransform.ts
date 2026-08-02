import type { Coord, ScreenCoord, ViewTransform } from "../types/sbim";

/** Compute bounding box of all coords */
export function bbox(coords: Coord[]): { minX: number; minY: number; maxX: number; maxY: number } {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const [x, y] of coords) {
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }
  return { minX, minY, maxX, maxY };
}

/** Collect all coords from design data to compute initial transform */
export function collectAllCoords(
  parkingStalls: Coord[][],
  columnCenters: Coord[],
  coreEv: Coord[],
  coreStair: Coord[],
  coreCorridor: Coord[],
  unitPolygons: Coord[][],
  pedestrianPath: Coord[],
): Coord[] {
  return [
    ...parkingStalls.flat(),
    ...columnCenters,
    ...coreEv,
    ...coreStair,
    ...coreCorridor,
    ...unitPolygons.flat(),
    ...pedestrianPath,
  ];
}

/**
 * Compute initial ViewTransform that fits all coords into the canvas.
 * EPSG:5186: +X is east, +Y is north → screen: +X right, +Y DOWN (flip Y)
 */
export function fitToCanvas(
  allCoords: Coord[],
  canvasWidth: number,
  canvasHeight: number,
  padding = 60,
): ViewTransform {
  if (allCoords.length === 0) {
    return { scale: 10, offsetX: 0, offsetY: 0 };
  }
  const { minX, minY, maxX, maxY } = bbox(allCoords);
  const worldW = maxX - minX || 1;
  const worldH = maxY - minY || 1;
  const scaleX = (canvasWidth - padding * 2) / worldW;
  const scaleY = (canvasHeight - padding * 2) / worldH;
  const scale = Math.min(scaleX, scaleY);
  // Center
  const offsetX = padding + (canvasWidth - padding * 2 - worldW * scale) / 2 - minX * scale;
  // Flip Y: screen_y = offsetY - y * scale
  const offsetY = canvasHeight - padding - (canvasHeight - padding * 2 - worldH * scale) / 2 + minY * scale;
  return { scale, offsetX, offsetY };
}

/** Convert EPSG:5186 world coord → screen coord */
export function worldToScreen(coord: Coord, t: ViewTransform): ScreenCoord {
  return {
    x: coord[0] * t.scale + t.offsetX,
    y: -coord[1] * t.scale + t.offsetY, // flip Y
  };
}

/** Convert screen coord → EPSG:5186 world coord */
export function screenToWorld(screen: ScreenCoord, t: ViewTransform): Coord {
  return [
    (screen.x - t.offsetX) / t.scale,
    -(screen.y - t.offsetY) / t.scale,
  ];
}

/** Flatten polygon ring to Konva-compatible flat array [x1,y1,x2,y2,...] */
export function ringToFlat(ring: Coord[], t: ViewTransform): number[] {
  const pts: number[] = [];
  for (const coord of ring) {
    const s = worldToScreen(coord, t);
    pts.push(s.x, s.y);
  }
  return pts;
}

/** Square column footprint given center + size */
export function columnRect(center: Coord, size: number, t: ViewTransform): number[] {
  const half = size / 2;
  const corners: Coord[] = [
    [center[0] - half, center[1] - half],
    [center[0] + half, center[1] - half],
    [center[0] + half, center[1] + half],
    [center[0] - half, center[1] + half],
  ];
  return ringToFlat(corners, t);
}
