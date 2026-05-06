import { useEffect, useState } from "react";

export interface UseBuildingDataResult<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
}

/**
 * URL에서 JSON을 fetch하는 React 훅. 폴링 옵션 지원 (artifact 갱신 감지용).
 */
export function useBuildingData<T>(
  url: string | null,
  options?: { pollIntervalMs?: number },
): UseBuildingDataResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const pollMs = options?.pollIntervalMs ?? 0;

  useEffect(() => {
    if (!url) {
      setData(null);
      return;
    }

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function tick() {
      setIsLoading(true);
      try {
        const r = await fetch(url!, { cache: "no-store" });
        if (!r.ok) throw new Error(`Fetch failed: ${r.status}`);
        const json = await r.json();
        if (!cancelled) {
          setData(json as T);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e as Error);
      } finally {
        if (!cancelled) setIsLoading(false);
        if (!cancelled && pollMs > 0) {
          timer = setTimeout(tick, pollMs);
        }
      }
    }

    void tick();

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [url, pollMs]);

  return { data, isLoading, error };
}
