export interface UseBuildingDataResult<T> {
    data: T | null;
    isLoading: boolean;
    error: Error | null;
}
/**
 * URL에서 JSON을 fetch하는 React 훅. 폴링 옵션 지원 (artifact 갱신 감지용).
 */
export declare function useBuildingData<T>(url: string | null, options?: {
    pollIntervalMs?: number;
}): UseBuildingDataResult<T>;
//# sourceMappingURL=useBuildingData.d.ts.map