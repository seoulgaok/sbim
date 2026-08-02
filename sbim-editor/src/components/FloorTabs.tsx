
import { useStore } from "../store";

export function FloorTabs() {
  const { designData, activeFloor, setActiveFloor } = useStore();
  if (!designData) return null;

  const floors = designData.scheme.floor_plans.map((fp) => fp.data.floor_id);

  return (
    <div className="floor-tabs">
      {floors.map((f) => (
        <button
          key={f}
          className={`floor-tab ${activeFloor === f ? "active" : ""} ${f === 1 ? "piloti" : ""}`}
          onClick={() => setActiveFloor(f)}
        >
          {f === 1 ? "1층\n(필로티)" : `${f}층`}
        </button>
      ))}
    </div>
  );
}
