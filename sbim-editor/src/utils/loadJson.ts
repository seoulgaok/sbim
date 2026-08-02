import type { Design, DesignData, Scheme, Unit, ContextData } from "../types/sbim";

/**
 * 드롭된 JSON을 DesignData로 정규화한다.
 *
 * 지원 형태:
 *  1) 전체 export   — { design, scheme, units, context }
 *  2) bare scheme   — { data, floor_plans, _core_layout, _column_centers, _parking_stalls, ... }
 *
 * @throws 알 수 없는 형태이면 Error
 */
export function normalizeToDesignData(raw: unknown, fileName = "dropped.json"): DesignData {
  if (!raw || typeof raw !== "object") {
    throw new Error("JSON 최상위가 객체가 아닙니다");
  }
  const obj = raw as Record<string, unknown>;

  // ── 1) 전체 export 래퍼 ───────────────────────────────────────────────────
  if (obj.scheme && typeof obj.scheme === "object") {
    const scheme = obj.scheme as Scheme;
    assertScheme(scheme);
    return {
      design: coerceDesign(obj.design, fileName),
      scheme,
      units: Array.isArray(obj.units) ? (obj.units as Unit[]) : [],
      context: (obj.context as ContextData | null) ?? null,
    };
  }

  // ── 2) bare scheme.json ───────────────────────────────────────────────────
  if (isScheme(obj)) {
    const scheme = obj as unknown as Scheme;
    return {
      design: coerceDesign(undefined, fileName, scheme),
      scheme,
      units: [],
      context: null,
    };
  }

  throw new Error("지원하지 않는 JSON 형태입니다 (scheme / floor_plans 키가 없음)");
}

function isScheme(o: Record<string, unknown>): boolean {
  return (
    Array.isArray(o.floor_plans) ||
    Array.isArray(o._parking_stalls) ||
    (typeof o._core_layout === "object" && o._core_layout !== null)
  );
}

function assertScheme(s: unknown): asserts s is Scheme {
  if (!s || typeof s !== "object" || !isScheme(s as Record<string, unknown>)) {
    throw new Error("scheme 형태가 올바르지 않습니다 (floor_plans / _core_layout 누락)");
  }
}

function coerceDesign(raw: unknown, fileName: string, scheme?: Scheme): Design {
  const d = (raw && typeof raw === "object" ? raw : {}) as Partial<Design>;
  const pnu = d.primary_land_id || scheme?.data?.pnu || "";
  return {
    id: d.id || `local:${fileName}`,
    name: d.name || fileName.replace(/\.json$/i, ""),
    land_ids: d.land_ids || (pnu ? [pnu] : []),
    primary_land_id: pnu,
    created_at: d.created_at || "",
  };
}

/** File → DesignData (JSON 파싱 + 정규화). */
export async function loadDesignFromFile(file: File): Promise<DesignData> {
  const text = await file.text();
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (e) {
    throw new Error(`JSON 파싱 실패: ${e instanceof Error ? e.message : String(e)}`);
  }
  return normalizeToDesignData(parsed, file.name);
}
