/**
 * Scheme JSON load/save (브라우저 fetch 또는 Node fs).
 */

import type { Scheme, SurroundingBuilding, Unit } from "./types.js";

/** URL에서 scheme.json fetch */
export async function fetchScheme(url: string): Promise<Scheme> {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`Failed to fetch scheme: ${r.status}`);
  return (await r.json()) as Scheme;
}

export async function fetchUnits(url: string): Promise<Unit[]> {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`Failed to fetch units: ${r.status}`);
  return (await r.json()) as Unit[];
}

export async function fetchSurroundings(url: string): Promise<SurroundingBuilding[]> {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`Failed to fetch surroundings: ${r.status}`);
  return (await r.json()) as SurroundingBuilding[];
}
