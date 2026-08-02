# SBIM Editor

Tauri 2 + React 기반 맥 데스크탑 앱 — SBIM 평면도 벡터 에디터

## 구조

```
sbim-editor/
  src/                  # React 프론트엔드
    components/
      Canvas.tsx         # Konva 벡터 에디터 (핵심)
      DesignSelector.tsx # Supabase 디자인 목록
      FloorTabs.tsx      # 층 탭 (1층 필로티 / 상층)
      LayerPanel.tsx     # 레이어 토글
      PropertiesPanel.tsx # 속성 + 저장
      Toolbar.tsx        # 편집 도구
    utils/
      coordTransform.ts  # EPSG:5186 ↔ 스크린 좌표 변환
    types/sbim.ts        # 타입 정의
    store.ts             # Zustand 전역 상태
    api.ts               # API 클라이언트
  api-server/
    main.py              # FastAPI 서버 (localhost:8765)
    start.sh             # 서버 시작 스크립트
  src-tauri/             # Rust/Tauri 백엔드
```

## 편집 가능한 데이터

| 층 | 레이어 | 데이터 소스 |
|---|---|---|
| 1층 (필로티) | 주차 구획 | scheme.json `_parking_stalls` |
| 1층 (필로티) | 필로티 기둥 | scheme.json `_column_centers` |
| 1층 (필로티) | 코어 (EV/계단/복도) | scheme.json `_core_layout` |
| 1층 (필로티) | 보행 동선 | scheme.json `_pedestrian_path` |
| 2층+ | 세대 유닛 폴리곤 | Supabase `units.polygon` |
| 2층+ | 발코니 폴리곤 | Supabase `units.balcony_polygons` |

## 개발 실행

### 1. API 서버 시작 (터미널 1)
```bash
cd api-server
./start.sh
```

### 2. Tauri 앱 개발 모드 (터미널 2)
```bash
npm run tauri dev
```

## 빌드 (DMG)

```bash
npm run tauri build
# → src-tauri/target/release/bundle/macos/SBIM Editor.dmg
```

## 편집 방법

1. 왼쪽 디자인 목록에서 설계 선택
2. 상단 층 탭으로 층 전환
3. **1층**: 필로티 주차 구획, 기둥, 코어, 동선 확인
4. **2층+**: 세대 유닛 클릭 → 버텍스 핸들 드래그로 형상 수정
5. 오른쪽 패널 "Supabase 저장" 버튼으로 저장

## 조작

| 동작 | 방법 |
|---|---|
| 줌 | 스크롤 휠 |
| 팬 | ✋ 도구 선택 후 드래그, 또는 빈 영역 드래그 |
| 유닛 선택 | ↖ 도구로 폴리곤 클릭 |
| 버텍스 이동 | 선택 후 흰 원형 핸들 드래그 |
| 선택 해제 | 같은 폴리곤 다시 클릭 |
