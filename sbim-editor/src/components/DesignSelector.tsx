import { useEffect, useRef, useState, useCallback } from "react";
import { fetchDesigns, fetchScheme, fetchUnits, fetchContext } from "../api";
import { useStore } from "../store";
import type { Design, DesignData } from "../types/sbim";

const PAGE = 30;

export function DesignSelector() {
  const { setDesignData, setLoading, setLoadError, setLoadingDesign, isLoading, loadError } = useStore();

  const [designs, setDesigns]   = useState<Design[]>([]);
  const [total, setTotal]       = useState(0);
  const [offset, setOffset]     = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [selectedId, setSelectedId]  = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const hasMore = designs.length < total;

  const load = useCallback(async (reset = false) => {
    const nextOffset = reset ? 0 : offset;
    if (!reset && loadingMore) return;
    reset ? setLoading(true) : setLoadingMore(true);
    try {
      const page = await fetchDesigns(nextOffset, PAGE);
      setDesigns(prev => reset ? page.designs : [...prev, ...page.designs]);
      setTotal(page.total);
      setOffset(nextOffset + PAGE);
    } catch (e) {
      setLoadError(`디자인 목록 로드 실패: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      reset ? setLoading(false) : setLoadingMore(false);
    }
  }, [offset, loadingMore]);

  useEffect(() => { load(true); }, []);

  // 무한스크롤 — 목록 끝에 도달하면 다음 페이지
  useEffect(() => {
    const el = listRef.current;
    if (!el) return;
    const handler = () => {
      if (el.scrollTop + el.clientHeight >= el.scrollHeight - 20 && hasMore && !loadingMore) {
        load(false);
      }
    };
    el.addEventListener("scroll", handler);
    return () => el.removeEventListener("scroll", handler);
  }, [hasMore, loadingMore, load]);

  async function handleSelect(design: Design) {
    setSelectedId(design.id);
    setLoading(true);
    setLoadingDesign(true, design.name || design.primary_land_id || design.id.slice(0, 8));
    setLoadError(null);
    try {
      const [scheme, units, context] = await Promise.all([
        fetchScheme(design.id),
        fetchUnits(design.id),
        fetchContext(design.id).catch(() => null),
      ]);
      const data: DesignData = { design, scheme, units, context };
      setDesignData(data);
    } catch (e) {
      setLoadError(`데이터 로드 실패: ${e instanceof Error ? e.message : String(e)}`);
      setSelectedId(null);
    } finally {
      setLoading(false);
      setLoadingDesign(false);
    }
  }

  return (
    <div className="design-selector">
      <div className="selector-header">
        <span className="label">디자인 {total > 0 && <span className="total-badge">{total}</span>}</span>
        <button className="refresh-btn" onClick={() => { setOffset(0); load(true); }} disabled={isLoading} title="새로고침">↻</button>
      </div>
      {loadError && <div className="error-msg">{loadError}</div>}
      {isLoading && designs.length === 0 && <div className="loading-msg">로딩 중...</div>}
      <div className="design-list" ref={listRef}>
        {designs.length === 0 && !isLoading && <div className="empty-msg">디자인 없음</div>}
        {designs.map((d) => (
          <button key={d.id}
            className={`design-item ${selectedId === d.id ? "active" : ""}`}
            onClick={() => handleSelect(d)}>
            <span className="design-name">{d.name || d.id.slice(0, 8)}</span>
            <span className="design-pnu">{d.primary_land_id}</span>
          </button>
        ))}
        {loadingMore && <div className="loading-more">로딩 중...</div>}
        {!hasMore && designs.length > 0 && (
          <div className="list-end">— 전체 {total}개 —</div>
        )}
      </div>
    </div>
  );
}
