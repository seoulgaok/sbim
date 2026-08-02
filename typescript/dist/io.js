/**
 * Scheme JSON load/save (브라우저 fetch 또는 Node fs).
 */
/** URL에서 scheme.json fetch */
export async function fetchScheme(url) {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok)
        throw new Error(`Failed to fetch scheme: ${r.status}`);
    return (await r.json());
}
export async function fetchUnits(url) {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok)
        throw new Error(`Failed to fetch units: ${r.status}`);
    return (await r.json());
}
export async function fetchSurroundings(url) {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok)
        throw new Error(`Failed to fetch surroundings: ${r.status}`);
    return (await r.json());
}
//# sourceMappingURL=io.js.map