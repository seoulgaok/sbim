/**
 * scheme.json 의 `_column_sections` — 기둥마다의 실단면을 싣는 밑줄 키.
 *
 * `_column_centers`·`_column_size`만 있으면 소비처는 모든 기둥을 w×w 정사각으로
 * 그린다 — 얇은 단면 기둥(0.9×0.3 m)이 주차 칸을 문다(서초 1508-29). 있음이면
 * 소비처는 실단면으로 그리고 없음(구 scheme) = `_column_size` 정사각 폴백.
 * python/tests/test_scheme_column_sections.py 와 같은 계약을 양쪽에서 지킨다.
 */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { ColumnSection, Scheme } from "../src/index.js";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(resolve(here, rel), "utf-8");

// ColumnSection 계약 — _column_centers와 같은 좌표 프레임·같은 순서.
const COLUMN_SECTIONS: ColumnSection[] = [
  { center: [935000.1, 1742000.2], w: 0.9, d: 0.3, angle_deg: 0.0 },
  { center: [935001.4, 1742003.8], w: 0.3, d: 0.3, angle_deg: 45.0 },
];
const COLUMN_CENTERS: [number, number][] = [
  [935000.1, 1742000.2],
  [935001.4, 1742003.8],
];

function schemeWith(sections?: ColumnSection[]): Scheme {
  const scheme: Scheme = {
    data: { lot_area: 999, build_area: 999, far: 2.0, bcr: 0.6, pnu: 1111111111 },
    floor_plans: [],
    unit_ids: [],
    _column_centers: COLUMN_CENTERS,
  };
  if (sections !== undefined) scheme._column_sections = sections;
  return scheme;
}

describe("Scheme._column_sections", () => {
  it("직렬화 왕복에서 실단면이 지워지지 않는다", () => {
    const scheme = schemeWith(COLUMN_SECTIONS);
    const revived = JSON.parse(JSON.stringify(scheme)) as Scheme;
    expect(revived._column_sections).toEqual(COLUMN_SECTIONS);
    expect(revived._column_sections?.[0].w).toBe(0.9);
  });

  it("_column_centers와 같은 순서다 — i번째 실단면은 i번째 중심의 기둥", () => {
    const revived = JSON.parse(JSON.stringify(schemeWith(COLUMN_SECTIONS))) as Scheme;
    const sections = revived._column_sections!;
    expect(sections).toHaveLength(revived._column_centers!.length);
    sections.forEach((s, i) => expect(s.center).toEqual(revived._column_centers![i]));
  });

  it("없음은 키 자체가 없다 (구 scheme) — 소비처는 _column_size 정사각 폴백", () => {
    const gone = JSON.parse(JSON.stringify(schemeWith())) as Scheme;
    expect("_column_sections" in gone).toBe(false);
  });

  it("네 칸은 center·w·d·angle_deg — 치수는 수, angle_deg 는 도", () => {
    for (const s of COLUMN_SECTIONS) {
      expect(Object.keys(s).sort()).toEqual(["angle_deg", "center", "d", "w"]);
      expect(s.center).toHaveLength(2);
      for (const k of ["w", "d", "angle_deg"] as const) expect(typeof s[k]).toBe("number");
    }
  });

  it("src 와 dist 가 같은 키를 선언한다 (dist 는 추적되는 빌드 산출물)", () => {
    const src = read("../src/types.ts");
    const dist = read("../dist/types.d.ts");
    for (const [name, text] of [
      ["src/types.ts", src],
      ["dist/types.d.ts", dist],
    ] as const) {
      // src 는 2단, dist(tsc 발행물)는 4단 들여쓰기 — 인덱스는 같게, 공백은 느슨하게
      expect(text, `${name} 에 키 선언 없음`).toMatch(
        /^\s+_column_sections\?: ColumnSection\[\];$/m,
      );
      expect(text, `${name} 에 ColumnSection interface 없음`).toMatch(
        /^export interface ColumnSection \{$/m,
      );
    }
  });

  it("python types.py docstring 에 같은 키가 있다", () => {
    expect(read("../../python/seoulgaok_bim_core/types.py")).toMatch(/_column_sections/);
  });
});
