
import { useStore } from "../store";
import type { LayerKey } from "../types/sbim";

export function LayerPanel() {
  const { layers, toggleLayer, activeFloor } = useStore();

  // On upper floors (2+), hide piloti-only layers
  const pilotiOnly: LayerKey[] = ["parking", "columns", "piloti_path"];

  return (
    <div className="layer-panel">
      <div className="panel-title">레이어</div>
      {layers.map((layer) => {
        const disabled = activeFloor > 1 && pilotiOnly.includes(layer.key);
        return (
          <label key={layer.key} className={`layer-row ${disabled ? "disabled" : ""}`}>
            <input
              type="checkbox"
              checked={layer.visible && !disabled}
              disabled={disabled}
              onChange={() => toggleLayer(layer.key)}
            />
            <span
              className="layer-swatch"
              style={{ background: layer.color }}
            />
            <span className="layer-label">{layer.label}</span>
          </label>
        );
      })}
    </div>
  );
}
