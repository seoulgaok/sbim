
import { useStore } from "../store";
import type { EditMode } from "../types/sbim";

const TOOLS: { mode: EditMode; icon: string; label: string }[] = [
  { mode: "select",       icon: "↖",  label: "선택 / 버텍스 편집" },
  { mode: "pan",          icon: "✋",  label: "화면 이동" },
];

export function Toolbar() {
  const { editMode, setEditMode, designData } = useStore();

  return (
    <div className="toolbar">
      <span className="toolbar-brand">SBIM Editor</span>
      <div className="toolbar-tools">
        {TOOLS.map(({ mode, icon, label }) => (
          <button
            key={mode}
            className={`tool-btn ${editMode === mode ? "active" : ""}`}
            onClick={() => setEditMode(mode)}
            title={label}
            disabled={!designData}
          >
            {icon}
          </button>
        ))}
      </div>
      {designData && (
        <span className="toolbar-info">
          {designData.design.name || designData.design.id.slice(0, 8)} — PNU {designData.design.primary_land_id}
        </span>
      )}
    </div>
  );
}
