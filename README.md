# sbim — Seoulgaok BIM Core

서울가옥 BIM 데이터 모델·연산·시각화 공통 패키지.

`scheme.json`을 단일 진실로 하여 Python·TypeScript·React 시각화를 통합합니다.

---

## 사용 프로젝트

```
volume_suggestion (Python)
    ↓ scheme.json 생성
    │
    ├── python/seoulgaok_bim_core
    │       Scheme, FloorPlan, Unit dataclass + io + validators
    │
    ├── typescript/                    ← Luis frontend, nextbase-v3
    │       동일 타입 + operations
    │
    └── visualizer/                    ← Luis frontend, nextbase-v3
            BuildingMeshVisualizer (R3F)

DeerFlow (Luis backend)
    ↓ Python 패키지로 import
    operations.move_core, operations.set_unit_count, ...
    validators.check_all
    ↓ scheme.json 편집 후 저장 → artifact 갱신
    ↓ frontend 시각화 자동 리렌더
```

---

## 디렉토리 구조

```
sbim/
├── schema/                    # 단일 진실 — JSON Schema
│   ├── scheme.schema.json
│   ├── units.schema.json
│   └── surroundings.schema.json
├── python/                    # Python 패키지 (pip install -e .)
│   └── seoulgaok_bim_core/
│       ├── types.py           # pydantic 모델
│       ├── io.py              # load/save
│       ├── operations.py      # 편집 함수
│       ├── validators.py      # 건축법 검증
│       └── geometry.py        # BufferGeometry 헬퍼
├── typescript/                # TS 패키지 (@seoulgaok/bim-core)
│   └── src/
│       ├── types.ts
│       ├── io.ts
│       ├── operations.ts
│       └── geometry.ts        # convertToThreeGeometry
├── visualizer/                # React + R3F (@seoulgaok/bim-visualizer)
│   └── src/
│       ├── BuildingMeshVisualizer.tsx
│       ├── MapFloor.tsx
│       └── hooks/useBuildingData.ts
└── examples/samples/          # 샘플 scheme.json, units.json
```

---

## 설치 (3개 프로젝트에서 사용 시)

### Python (volume_suggestion / Luis backend)
```bash
pip install -e /Users/ichanghyeon/Desktop/seoulgaok/20260506_sbim/python
```

### TypeScript (Luis frontend / nextbase-v3)
```json
// package.json
{
  "dependencies": {
    "@seoulgaok/bim-core": "file:../20260506_sbim/typescript",
    "@seoulgaok/bim-visualizer": "file:../20260506_sbim/visualizer"
  }
}
```

---

## 데이터 모델 (요약)

```
Scheme
├── data: { lot_area, build_area, far, bcr, pnu }
├── floor_plans[]: FloorPlan
│   ├── data: { floor_id, floor_area, floor_height, floor_bottom_height }
│   └── geom: { walls, floors, roof? }
└── unit_ids[]

Unit
├── geom: { boundary }
└── data: { id, name, price, floor_id, area_net, area_common, ... }

Surroundings (배열)
├── geom: { boundary }
└── data: { address, height, floor }
```

---

## 단일 진실 원칙

1. JSON Schema가 **유일한 정의**. Python·TS 타입은 여기서 생성.
2. 같은 데이터를 양쪽이 다르게 정의하지 않는다.
3. 필드 추가 시 schema 먼저 수정 → 양쪽 코드 갱신.

---

## 향후 단계

- [ ] schema/scheme.schema.json 정식 작성
- [ ] Python/TS 타입 자동 생성 파이프라인 (datamodel-code-generator, json-schema-to-typescript)
- [ ] operations 함수 (move_core, set_unit_count, set_floor_type, ...)
- [ ] validators (사선·일조·BCR·FAR·주차)
- [ ] visualizer 이식 (nextbase-v3 → 패키지)
- [ ] LoD 200 룰 (건축사 합류 후)
- [ ] IFC import/export (Phase 2)
