/**
 * Scheme JSON load/save (브라우저 fetch 또는 Node fs).
 */
import type { Scheme, SurroundingBuilding, Unit } from "./types.js";
/** URL에서 scheme.json fetch */
export declare function fetchScheme(url: string): Promise<Scheme>;
export declare function fetchUnits(url: string): Promise<Unit[]>;
export declare function fetchSurroundings(url: string): Promise<SurroundingBuilding[]>;
//# sourceMappingURL=io.d.ts.map