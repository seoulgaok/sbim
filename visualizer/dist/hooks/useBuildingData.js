import { useEffect, useState } from "react";
/**
 * URL에서 JSON을 fetch하는 React 훅. 폴링 옵션 지원 (artifact 갱신 감지용).
 */
export function useBuildingData(url, options) {
    const [data, setData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const pollMs = options?.pollIntervalMs ?? 0;
    useEffect(() => {
        if (!url) {
            setData(null);
            return;
        }
        let cancelled = false;
        let timer;
        async function tick() {
            setIsLoading(true);
            try {
                const r = await fetch(url, { cache: "no-store" });
                if (!r.ok)
                    throw new Error(`Fetch failed: ${r.status}`);
                const json = await r.json();
                if (!cancelled) {
                    setData(json);
                    setError(null);
                }
            }
            catch (e) {
                if (!cancelled)
                    setError(e);
            }
            finally {
                if (!cancelled)
                    setIsLoading(false);
                if (!cancelled && pollMs > 0) {
                    timer = setTimeout(tick, pollMs);
                }
            }
        }
        void tick();
        return () => {
            cancelled = true;
            if (timer)
                clearTimeout(timer);
        };
    }, [url, pollMs]);
    return { data, isLoading, error };
}
//# sourceMappingURL=useBuildingData.js.map