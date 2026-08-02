import { BimCanvas } from "@seoulgaok/bim-visualizer";
import type { Scheme, Unit } from "@seoulgaok/bim-core";
import { useCallback, useState } from "react";

type DropZoneId = "scheme" | "units";

function readJsonFile<T>(file: File): Promise<T> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        resolve(JSON.parse(e.target?.result as string) as T);
      } catch {
        reject(new Error(`${file.name}: JSON 파싱 실패`));
      }
    };
    reader.onerror = () => reject(new Error(`${file.name}: 읽기 실패`));
    reader.readAsText(file);
  });
}

function guessFileType(name: string): DropZoneId | null {
  const lower = name.toLowerCase();
  if (lower.includes("scheme")) return "scheme";
  if (lower.includes("unit")) return "units";
  return null;
}

export function App() {
  const [scheme, setScheme] = useState<Scheme | null>(null);
  const [units, setUnits] = useState<Unit[] | null>(null);
  const [selectedFloor, setSelectedFloor] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState<DropZoneId | null>(null);
  const [errors, setErrors] = useState<Partial<Record<DropZoneId, string>>>({});

  const handleDrop = useCallback(
    (zoneId: DropZoneId) => async (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(null);

      const files = Array.from(e.dataTransfer.files).filter((f) =>
        f.name.endsWith(".json"),
      );
      if (files.length === 0) return;

      // 파일 이름으로 자동 감지해서 분배
      for (const file of files) {
        const guessed = guessFileType(file.name) ?? zoneId;
        try {
          if (guessed === "scheme") {
            const data = await readJsonFile<Scheme>(file);
            setScheme(data);
            setSelectedFloor(null);
            setErrors((prev) => ({ ...prev, scheme: undefined }));
          } else {
            const data = await readJsonFile<Unit[]>(file);
            setUnits(data);
            setErrors((prev) => ({ ...prev, units: undefined }));
          }
        } catch (err) {
          setErrors((prev) => ({
            ...prev,
            [guessed]: String(err),
          }));
        }
      }
    },
    [],
  );

  const handleDragOver = useCallback(
    (zoneId: DropZoneId) => (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(zoneId);
    },
    [],
  );

  const handleDragLeave = useCallback(() => setDragOver(null), []);

  const floors =
    scheme?.floor_plans
      .map((fp) => fp.data.floor_id)
      .sort((a, b) => a - b) ?? [];

  const resetAll = useCallback(() => {
    setScheme(null);
    setUnits(null);
    setSelectedFloor(null);
    setErrors({});
  }, []);

  return (
    <div style={styles.root}>
      {/* 상단 툴바 */}
      <header style={styles.toolbar}>
        <span style={styles.logo}>SBIM Viewer</span>

        {scheme && (
          <div style={styles.floorBar}>
            <button
              style={floorBtn(selectedFloor === null)}
              onClick={() => setSelectedFloor(null)}
            >
              전체
            </button>
            {floors.map((f) => (
              <button
                key={f}
                style={floorBtn(selectedFloor === f)}
                onClick={() => setSelectedFloor(f)}
              >
                {f < 0 ? `B${Math.abs(f)}` : f === 0 ? "P" : `${f}F`}
              </button>
            ))}
          </div>
        )}

        <div style={styles.fileZones}>
          <DropZone
            id="scheme"
            label="scheme.json"
            loaded={!!scheme}
            active={dragOver === "scheme"}
            error={errors.scheme}
            onDrop={handleDrop("scheme")}
            onDragOver={handleDragOver("scheme")}
            onDragLeave={handleDragLeave}
            onClear={() => {
              setScheme(null);
              setSelectedFloor(null);
            }}
          />
          <DropZone
            id="units"
            label="units.json"
            loaded={!!units}
            active={dragOver === "units"}
            error={errors.units}
            onDrop={handleDrop("units")}
            onDragOver={handleDragOver("units")}
            onDragLeave={handleDragLeave}
            onClear={() => setUnits(null)}
          />
          {(scheme || units) && (
            <button style={styles.resetBtn} onClick={resetAll}>
              초기화
            </button>
          )}
        </div>
      </header>

      {/* 본문 */}
      <main style={styles.main}>
        {!scheme ? (
          <DropPrompt
            onDrop={handleDrop("scheme")}
            onDragOver={handleDragOver("scheme")}
            onDragLeave={handleDragLeave}
            active={dragOver === "scheme"}
          />
        ) : (
          <div style={{ width: "100%", height: "100%" }}>
            <BimCanvas
              schemeData={scheme}
              unitsData={units}
              selectedFloor={selectedFloor}
              className="bim-canvas"
            />
          </div>
        )}
      </main>
    </div>
  );
}

/* ─── DropZone chip (툴바 안) ─── */
function DropZone({
  id,
  label,
  loaded,
  active,
  error,
  onDrop,
  onDragOver,
  onDragLeave,
  onClear,
}: {
  id: DropZoneId;
  label: string;
  loaded: boolean;
  active: boolean;
  error?: string;
  onDrop: React.DragEventHandler;
  onDragOver: React.DragEventHandler;
  onDragLeave: React.DragEventHandler;
  onClear: () => void;
}) {
  const bg = error
    ? "#5c1a1a"
    : active
      ? "#1a3a5c"
      : loaded
        ? "#1a3a1a"
        : "#1e1e1e";
  const border = error
    ? "#e05555"
    : active
      ? "#4da6ff"
      : loaded
        ? "#4daa4d"
        : "#444";

  return (
    <div
      title={error ?? (loaded ? `${label} 로드됨` : `${label} 드래그`)}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        padding: "4px 10px",
        borderRadius: 6,
        border: `1px dashed ${border}`,
        background: bg,
        cursor: "default",
        fontSize: 12,
        color: loaded ? "#aaffaa" : "#aaa",
        userSelect: "none",
        transition: "all 0.15s",
        minWidth: 120,
      }}
    >
      <span style={{ flex: 1 }}>
        {loaded ? `✓ ${label}` : `+ ${label}`}
      </span>
      {loaded && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onClear();
          }}
          style={{
            background: "none",
            border: "none",
            color: "#888",
            cursor: "pointer",
            fontSize: 14,
            lineHeight: 1,
            padding: "0 2px",
          }}
          title="제거"
        >
          ×
        </button>
      )}
    </div>
  );
}

/* ─── 중앙 드롭 프롬프트 ─── */
function DropPrompt({
  onDrop,
  onDragOver,
  onDragLeave,
  active,
}: {
  onDrop: React.DragEventHandler;
  onDragOver: React.DragEventHandler;
  onDragLeave: React.DragEventHandler;
  active: boolean;
}) {
  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 16,
        border: `2px dashed ${active ? "#4da6ff" : "#333"}`,
        borderRadius: 12,
        transition: "border-color 0.15s",
        color: active ? "#4da6ff" : "#555",
      }}
    >
      <span style={{ fontSize: 48 }}>🏗</span>
      <p style={{ fontSize: 18, fontWeight: 600 }}>
        scheme.json을 드래그해서 놓으세요
      </p>
      <p style={{ fontSize: 13, color: "#444" }}>
        units.json은 선택 사항 — scheme 로드 후 추가 가능
      </p>
    </div>
  );
}

/* ─── 스타일 ─── */
const styles: Record<string, React.CSSProperties> = {
  root: {
    width: "100%",
    height: "100%",
    display: "flex",
    flexDirection: "column",
    background: "#0e0e0e",
    fontFamily: "system-ui, sans-serif",
    color: "#eee",
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "8px 16px",
    background: "#161616",
    borderBottom: "1px solid #2a2a2a",
    flexShrink: 0,
    flexWrap: "wrap",
  },
  logo: {
    fontSize: 14,
    fontWeight: 700,
    letterSpacing: "0.05em",
    color: "#fff",
    marginRight: 8,
  },
  floorBar: {
    display: "flex",
    gap: 4,
    flexWrap: "wrap",
    flex: 1,
  },
  fileZones: {
    display: "flex",
    gap: 8,
    alignItems: "center",
    marginLeft: "auto",
    flexWrap: "wrap",
  },
  main: {
    flex: 1,
    overflow: "hidden",
    padding: 8,
  },
  resetBtn: {
    padding: "4px 10px",
    borderRadius: 6,
    border: "1px solid #444",
    background: "#1e1e1e",
    color: "#aaa",
    cursor: "pointer",
    fontSize: 12,
  },
};

function floorBtn(active: boolean): React.CSSProperties {
  return {
    padding: "3px 10px",
    borderRadius: 5,
    border: `1px solid ${active ? "#4da6ff" : "#333"}`,
    background: active ? "#1a3a5c" : "#1e1e1e",
    color: active ? "#4da6ff" : "#888",
    cursor: "pointer",
    fontSize: 12,
    fontWeight: active ? 700 : 400,
    transition: "all 0.1s",
  };
}
