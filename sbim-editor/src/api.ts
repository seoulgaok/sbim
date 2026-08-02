import axios from "axios";
import type { Design, Scheme, Unit, ContextData } from "./types/sbim";

const BASE = "http://localhost:8765";

const client = axios.create({ baseURL: BASE, timeout: 15000 });

export interface DesignPage {
  designs: Design[];
  total: number;
  offset: number;
  limit: number;
}

export async function fetchDesigns(offset = 0, limit = 30): Promise<DesignPage> {
  const { data } = await client.get<DesignPage>("/designs", { params: { offset, limit } });
  return data;
}

export async function fetchScheme(designId: string): Promise<Scheme> {
  const { data } = await client.get<{ scheme: Scheme }>(`/designs/${designId}/scheme`);
  return data.scheme;
}

export async function fetchUnits(designId: string): Promise<Unit[]> {
  const { data } = await client.get<{ units: Unit[] }>(`/designs/${designId}/units`);
  return data.units;
}

export async function saveUnits(designId: string, units: Unit[]): Promise<void> {
  await client.put(`/designs/${designId}/units`, { units });
}

export async function saveScheme(designId: string, scheme: Scheme): Promise<void> {
  await client.put(`/designs/${designId}/scheme`, { scheme });
}

export async function fetchContext(designId: string, radiusM = 150): Promise<ContextData> {
  const { data } = await client.get<ContextData>(`/designs/${designId}/context`, {
    params: { radius: radiusM },
  });
  return data;
}

export async function checkHealth(): Promise<boolean> {
  try {
    await client.get("/health", { timeout: 3000 });
    return true;
  } catch {
    return false;
  }
}
