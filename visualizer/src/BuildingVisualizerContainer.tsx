// src/components/BuildingVisualizer/BuildingVisualizerContainer.tsx
"use client";
//@orchestra workspace

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Building, AlertCircle, Loader2 } from "lucide-react";
import { useBuildingData } from './hooks/useBuildingData.js';
import { GeoJSON } from 'geojson';

// Dynamic import for the 3D visualizer component to avoid SSR issues with Three.js
const BuildingMeshVisualizer = dynamic(
  () => import('@/components/BuildingVisualizer/BuildingMeshVisualizer'),
  { ssr: false }
);

interface BuildingVisualizerContainerProps {
  workspaceId: string;
  buildingData: any;
  unitsData: any;
  landGeojson: GeoJSON;
  initialLatitude: number;
  initialLongitude: number;
}

export default function BuildingVisualizerContainer({
                                                      workspaceId,
                                                      buildingData,
                                                      unitsData,
                                                      landGeojson,
                                                      initialLatitude,
                                                      initialLongitude
                                                    }: BuildingVisualizerContainerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 건물 구조 데이터 로드
  const {
    data: schemeData,
    isLoading: isSchemeLoading,
    error: schemeError
  } = useBuildingData(buildingData?.scheme_file_path || null);

  // 주변 건물 데이터 로드
  const {
    data: surroundingsData,
    isLoading: isSurroundingsLoading,
    error: surroundingsError
  } = useBuildingData(buildingData?.surroundings_file_path || null);

  useEffect(() => {
    // 로딩 상태 통합 관리
    const loading = isSchemeLoading || isSurroundingsLoading;
    setIsLoading(loading);

    // 오류 상태 통합 관리
    if (schemeError) {
      setError('건물 구조 데이터를 불러오는 중 오류가 발생했습니다');
    } else if (surroundingsError && buildingData?.surroundings_file_path) {
      setError('주변 건물 데이터를 불러오는 중 오류가 발생했습니다');
    } else if (!buildingData?.scheme_file_path) {
      setError('등록된 건물 구조 데이터가 없습니다');
    } else {
      setError(null);
    }
  }, [isSchemeLoading, isSurroundingsLoading, schemeError, surroundingsError, buildingData]);

  // 로딩 중인 경우
  if (isLoading) {
    return (
      <div className="h-[calc(100vh-60px)] w-full flex flex-col items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="mt-4 text-lg font-medium">건물 데이터 로드 중...</p>
      </div>
    );
  }

  // 오류가 있는 경우
  if (error || !schemeData) {
    return (
      <div className="h-[calc(100vh-60px)] w-full flex items-center justify-center">
        <Alert className="max-w-lg">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>건물 데이터 로드 실패</AlertTitle>
          <AlertDescription>
            {error || '건물 구조 데이터를 불러올 수 없습니다. 관리자 설정에서 데이터를 업로드해주세요.'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // 정상적으로 데이터 로드 완료
  return (
    <div className="h-[calc(100vh-60px)] w-full">
      <BuildingMeshVisualizer
        schemeData={schemeData}
        unitsData={unitsData}
        surroundingsData={surroundingsData || null}
        landGeojson={landGeojson}
        initialLatitude={initialLatitude}
        initialLongitude={initialLongitude}
      />
    </div>
  );
}
