/**
 * BimCanvas — sbim 데이터(Scheme/Unit/SurroundingBuilding) 기반 R3F 3D 뷰어.
 *
 * nextbase-v3의 BuildingMeshVisualizer에서 UI 패널·차량·문의 다이얼로그·지도
 * underlay를 제거한 슬림 + 시각 풀 버전.
 *
 * 의존성: react, three, @react-three/fiber, @react-three/drei, @seoulgaok/bim-core
 * shadcn / Next.js / lucide / framer-motion 의존 없음.
 */
import { type Scheme, type SurroundingBuilding, type Unit } from "@seoulgaok/bim-core";
export interface BimCanvasProps {
    schemeData: Scheme;
    unitsData?: Unit[] | null;
    surroundingsData?: SurroundingBuilding[] | null;
    /** 화면에 띄울 층만 필터 (null/undefined면 전체) */
    selectedFloor?: number | null;
    /** 클래스 (size 등) */
    className?: string;
}
export declare function BimCanvas({ schemeData, unitsData, surroundingsData, selectedFloor, className, }: BimCanvasProps): React.JSX.Element;
import * as React from "react";
//# sourceMappingURL=BimCanvas.d.ts.map