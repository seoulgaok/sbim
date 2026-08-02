import { useStore } from "../store";
import { saveUnits, saveScheme } from "../api";

export function PropertiesPanel() {
  const {
    designData, editedUnits, editedScheme,
    selection, isDirtyUnits, isDirtyScheme,
    setEditedUnits, resetScheme, activeFloor,
  } = useStore();

  if (!designData) return null;

  const units = editedUnits ?? designData.units;
  const selectedUnit = selection.type === "unit" ? units.find((u) => u.id === selection.id) : null;
  const fp = designData.scheme.floor_plans.find((f) => f.data.floor_id === activeFloor);

  async function handleSaveUnits() {
    if (!isDirtyUnits || !editedUnits) return;
    try {
      await saveUnits(designData!.design.id, editedUnits);
      setEditedUnits(null);
      alert("세대 유닛 저장 완료");
    } catch (e) { alert(`저장 실패: ${e instanceof Error ? e.message : e}`); }
  }

  async function handleSaveScheme() {
    if (!isDirtyScheme || !editedScheme) return;
    try {
      await saveScheme(designData!.design.id, editedScheme);
      resetScheme();
      alert("필로티 레이아웃 저장 완료");
    } catch (e) { alert(`저장 실패: ${e instanceof Error ? e.message : e}`); }
  }

  return (
    <div className="properties-panel">
      {/* 층 요약 */}
      <div className="panel-section">
        <div className="panel-title">{activeFloor === 1 ? "1층 (필로티)" : `${activeFloor}층`}</div>
        {fp && (
          <div className="prop-grid">
            <span>층 면적</span><span>{fp.data.floor_area.toFixed(1)} ㎡</span>
            <span>층고</span>   <span>{fp.data.floor_height.toFixed(1)} m</span>
            {fp.data.parking_count != null && <><span>주차</span><span>{fp.data.parking_count} 대</span></>}
          </div>
        )}
      </div>

      {/* 건물 요약 */}
      <div className="panel-section">
        <div className="panel-title">건물 정보</div>
        <div className="prop-grid">
          <span>대지 면적</span><span>{designData.scheme.data.lot_area.toFixed(1)} ㎡</span>
          <span>건축 면적</span><span>{designData.scheme.data.build_area.toFixed(1)} ㎡</span>
          <span>건폐율</span>   <span>{designData.scheme.data.bcr.toFixed(1)} %</span>
          <span>용적률</span>   <span>{designData.scheme.data.far.toFixed(1)} %</span>
        </div>
      </div>

      {/* 선택 항목 */}
      {selectedUnit && (
        <div className="panel-section selected">
          <div className="panel-title">선택 세대</div>
          <div className="prop-grid">
            <span>층</span>       <span>{selectedUnit.floor_id}층</span>
            <span>전용 면적</span><span>{selectedUnit.area_net.toFixed(1)} ㎡</span>
            <span>계약 면적</span><span>{selectedUnit.area_contract.toFixed(1)} ㎡</span>
            <span>분양가</span>   <span>{(selectedUnit.price / 1e8).toFixed(2)} 억</span>
          </div>
        </div>
      )}
      {selection.type === "parking_stall" && (
        <div className="panel-section selected">
          <div className="panel-title">주차 구획 #{selection.id}</div>
          <div className="prop-hint">버텍스 드래그로 형상 편집</div>
        </div>
      )}
      {selection.type === "column" && (
        <div className="panel-section selected">
          <div className="panel-title">필로티 기둥 #{selection.id}</div>
          <div className="prop-hint">중심 핸들 드래그로 이동</div>
        </div>
      )}
      {(selection.type === "core_ev" || selection.type === "core_stair" || selection.type === "core_corridor") && (
        <div className="panel-section selected">
          <div className="panel-title">코어 — {selection.type === "core_ev" ? "EV" : selection.type === "core_stair" ? "계단" : "복도"}</div>
          <div className="prop-hint">버텍스 드래그로 형상 편집</div>
        </div>
      )}
      {selection.type === "piloti_path" && (
        <div className="panel-section selected">
          <div className="panel-title">보행 동선</div>
          <div className="prop-hint">점 드래그로 경로 편집</div>
        </div>
      )}

      {/* 저장 */}
      <div className="panel-actions">
        <button className="btn-save" onClick={handleSaveUnits} disabled={!isDirtyUnits}>
          💾 세대 유닛 저장
        </button>
        {isDirtyUnits && <span className="dirty-badge">미저장 유닛 변경</span>}

        <button className="btn-save btn-scheme" onClick={handleSaveScheme} disabled={!isDirtyScheme}>
          💾 필로티 레이아웃 저장
        </button>
        {isDirtyScheme && <span className="dirty-badge">미저장 필로티 변경</span>}

        <button className="btn-reset" onClick={() => { setEditedUnits(null); resetScheme(); }}
          disabled={!isDirtyUnits && !isDirtyScheme}>
          ↩ 모두 되돌리기
        </button>
      </div>
    </div>
  );
}
