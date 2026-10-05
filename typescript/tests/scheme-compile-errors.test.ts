/**
 * scheme.json 의 `_compile_errors` — 엔진이 스스로 이 설계안을 거절한 사유를 싣는 밑줄 키.
 *
 * 설계는 저장되지만 경고와 함께 보여야 한다. 값 모양은 생성기 방출형
 * (type · reason · details · suggestion) = errors.ts CompileError. python/tests
 * /test_scheme_compile_errors.py 와 같은 계약을 양쪽에서 지킨다.
 */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { CompileError, Scheme } from "../src/index.js";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(resolve(here, rel), "utf-8");

// 생성기 방출형 그대로 (building-generator pipeline.py · units.py 의 compile_errors.append)
const ENGINE_ERRORS: CompileError[] = [
  {
    type: "UnitUnreachable",
    reason:
      "5층 502호의 전용 면적 중 문에서 폭 1.2m 경로로 도달 가능한 비율이 61%뿐입니다(기준 90%). " +
      "사람이 쓸 수 없는 평면이라 이 기획안은 만들 수 없습니다.",
    details: { unit: "502", reach: 0.61 },
    suggestion: "층 세대 수를 낮추거나 코어 위치·매스를 조정하세요.",
  },
  {
    type: "ParkingSufficiency",
    reason:
      "법정 주차 12대가 필요하지만 이 대지에는 10대만 둘 수 있어 2대가 모자랍니다. " +
      "주차 기준을 충족하지 못해 이 기획안은 만들 수 없습니다.",
    details: { required: 12, actual: 10, shortfall: 2 },
    suggestion: "세대 수를 줄이거나(현재 10세대), 기계식 주차 또는 층수 조정을 검토하세요.",
  },
];

function schemeWith(errors?: CompileError[]): Scheme {
  const scheme: Scheme = {
    data: { lot_area: 999, build_area: 999, far: 2.0, bcr: 0.6, pnu: 1111111111 },
    floor_plans: [],
    unit_ids: [],
  };
  if (errors !== undefined) scheme._compile_errors = errors;
  return scheme;
}

describe("Scheme._compile_errors", () => {
  it("직렬화 왕복에서 경고가 지워지지 않는다", () => {
    const scheme = schemeWith(ENGINE_ERRORS);
    const revived = JSON.parse(JSON.stringify(scheme)) as Scheme;
    expect(revived._compile_errors).toEqual(ENGINE_ERRORS);
    expect(revived._compile_errors?.[1].details.shortfall).toBe(2);
  });

  it("없음과 [] 는 구별된다 (둘 다 컴파일 통과)", () => {
    const gone = JSON.parse(JSON.stringify(schemeWith())) as Scheme;
    expect("_compile_errors" in gone).toBe(false);
    const empty = JSON.parse(JSON.stringify(schemeWith([]))) as Scheme;
    expect(empty._compile_errors).toEqual([]);
    expect("_compile_errors" in empty).toBe(true);
  });

  it("src 와 dist 가 같은 키를 선언한다 (dist 는 추적되는 빌드 산출물)", () => {
    const src = read("../src/types.ts");
    const dist = read("../dist/types.d.ts");
    for (const [name, text] of [
      ["src/types.ts", src],
      ["dist/types.d.ts", dist],
    ] as const) {
      // src 는 2단, dist(tsc 발행물)는 4단 들여쓰기 — 인덱스는 같게, 공백은 느슨하게
      expect(text, `${name} 에 키 선언 없음`).toMatch(/^\s+_compile_errors\?: CompileError\[\];$/m);
    }
    // 정본 어휘는 errors.ts 하나 — types.ts가 자기 모양을 발명하지 않는다
    expect(src).toMatch(/^import type \{ CompileError \} from "\.\/errors\.js";$/m);
  });

  it("python types.py docstring 에 같은 키가 있다", () => {
    expect(read("../../python/seoulgaok_bim_core/types.py")).toMatch(/_compile_errors/);
  });
});
