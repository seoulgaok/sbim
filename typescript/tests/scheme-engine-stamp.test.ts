/**
 * scheme.json 의 `_engine_stamp` — 이 설계안을 만든 엔진 빌드를 적는 밑줄 키.
 *
 * 같은 소스라도 서버(x86_64)와 로컬(arm64) 컴파일 분기가 갈릴 수 있어 방출 빌드를
 * 찍어 둔다. 값 모양은 EngineStamp — engine_commit·platform·python·compiled_at 전부
 * 문자열. python/tests/test_scheme_engine_stamp.py 와 같은 계약을 양쪽에서 지킨다.
 */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { EngineStamp, Scheme } from "../src/index.js";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(resolve(here, rel), "utf-8");

const ENGINE_STAMP: EngineStamp = {
  engine_commit: "e10b99a79b65984dcda516792cd79ab2290b075d",
  platform: "linux-x86_64",
  python: "3.12.7",
  compiled_at: "2026-10-06T02:15:33Z",
};

function schemeWith(stamp?: EngineStamp): Scheme {
  const scheme: Scheme = {
    data: { lot_area: 999, build_area: 999, far: 2.0, bcr: 0.6, pnu: 1111111111 },
    floor_plans: [],
    unit_ids: [],
  };
  if (stamp !== undefined) scheme._engine_stamp = stamp;
  return scheme;
}

describe("Scheme._engine_stamp", () => {
  it("직렬화 왕복에서 도장이 지워지지 않는다", () => {
    const scheme = schemeWith(ENGINE_STAMP);
    const revived = JSON.parse(JSON.stringify(scheme)) as Scheme;
    expect(revived._engine_stamp).toEqual(ENGINE_STAMP);
    expect(revived._engine_stamp?.platform).toBe("linux-x86_64");
  });

  it("없음은 키 자체가 없다 (구 scheme)", () => {
    const gone = JSON.parse(JSON.stringify(schemeWith())) as Scheme;
    expect("_engine_stamp" in gone).toBe(false);
  });

  it("네 칸은 전부 문자열 — compiled_at 은 ISO-8601 UTC", () => {
    for (const v of Object.values(ENGINE_STAMP)) expect(typeof v).toBe("string");
    expect(Date.parse(ENGINE_STAMP.compiled_at)).not.toBeNaN();
  });

  it("src 와 dist 가 같은 키를 선언한다 (dist 는 추적되는 빌드 산출물)", () => {
    const src = read("../src/types.ts");
    const dist = read("../dist/types.d.ts");
    for (const [name, text] of [
      ["src/types.ts", src],
      ["dist/types.d.ts", dist],
    ] as const) {
      // src 는 2단, dist(tsc 발행물)는 4단 들여쓰기 — 인덱스는 같게, 공백은 느슨하게
      expect(text, `${name} 에 키 선언 없음`).toMatch(/^\s+_engine_stamp\?: EngineStamp;$/m);
      expect(text, `${name} 에 EngineStamp interface 없음`).toMatch(
        /^export interface EngineStamp \{$/m,
      );
    }
  });

  it("python types.py docstring 에 같은 키가 있다", () => {
    expect(read("../../python/seoulgaok_bim_core/types.py")).toMatch(/_engine_stamp/);
  });
});
