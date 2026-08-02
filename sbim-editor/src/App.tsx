import React, { useEffect, useState, useCallback } from "react";
import { Toolbar } from "./components/Toolbar";
import { DesignSelector } from "./components/DesignSelector";
import { FloorTabs } from "./components/FloorTabs";
import { LayerPanel } from "./components/LayerPanel";
import { Canvas } from "./components/Canvas";
import { PropertiesPanel } from "./components/PropertiesPanel";
import { checkHealth } from "./api";
import { useStore } from "./store";
import { loadDesignFromFile } from "./utils/loadJson";
import "./App.css";

export function App() {
  const [serverOk, setServerOk] = useState<boolean | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const { isLoadingDesign, loadingDesignName, setDesignData, setLoadError } = useStore();

  useEffect(() => {
    checkHealth().then(setServerOk);
    const id = setInterval(() => checkHealth().then(setServerOk), 5000);
    return () => clearInterval(id);
  }, []);

  const onDragOver = useCallback((e: React.DragEvent) => {
    if (Array.from(e.dataTransfer.types).includes("Files")) {
      e.preventDefault();
      setDragOver(true);
    }
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    // app-root 바깥으로 나갈 때만 해제 (자식 위로 이동 시 깜빡임 방지)
    if (e.currentTarget === e.target) setDragOver(false);
  }, []);

  const onDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    if (!/\.json$/i.test(file.name)) {
      setLoadError(`JSON 파일만 지원합니다: ${file.name}`);
      return;
    }
    try {
      const data = await loadDesignFromFile(file);
      setLoadError(null);
      setDesignData(data);
    } catch (err) {
      setLoadError(`파일 로드 실패: ${err instanceof Error ? err.message : String(err)}`);
    }
  }, [setDesignData, setLoadError]);

  return (
    <div className="app-root" onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}>
      <Toolbar />

      {serverOk === false && (
        <div className="server-banner">
          ⚠️ API 서버(localhost:8765)에 연결할 수 없습니다 —{" "}
          <code>cd api-server && python main.py</code> 를 실행해주세요
        </div>
      )}

      <div className="app-body">
        <aside className="sidebar-left">
          <DesignSelector />
          <LayerPanel />
        </aside>

        <main className="canvas-area" style={{ position: "relative" }}>
          <FloorTabs />
          <Canvas />
          {isLoadingDesign && (
            <div className="design-loading-overlay">
              <div className="design-loading-box">
                <div className="design-loading-spinner" />
                <div className="design-loading-name">{loadingDesignName}</div>
                <div className="design-loading-sub">필지·유닛·컨텍스트 로딩 중…</div>
              </div>
            </div>
          )}
        </main>

        <aside className="sidebar-right">
          <PropertiesPanel />
        </aside>
      </div>

      {dragOver && (
        <div className="drop-overlay">
          <div className="drop-box">
            <div className="drop-icon">⬇</div>
            <div className="drop-title">JSON 파일을 놓아 디자인 불러오기</div>
            <div className="drop-sub">전체 export 또는 scheme.json 지원</div>
          </div>
        </div>
      )}
    </div>
  );
}
