/**
 * options.ts(생성물)가 schema/build_options.schema.json 과 갈리지 않는가.
 * 스키마의 모든 모델이 인터페이스로, 모든 필드가 그 인터페이스 안에 있어야 한다.
 */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import type { BuildOptions, ResolvedOptions } from "../src/index.js";

const here = dirname(fileURLToPath(import.meta.url));
const schema = JSON.parse(
  readFileSync(resolve(here, "../../schema/build_options.schema.json"), "utf-8"),
);
const ts = readFileSync(resolve(here, "../src/options.ts"), "utf-8");

function body(name: string): string {
  const m = ts.match(new RegExp(`export interface ${name} \\{([\\s\\S]*?)\\n\\}`));
  return m ? m[1] : "";
}

describe("BuildOptions TS 타입", () => {
  const models: Record<string, any> = { ...schema.$defs, [schema.title]: schema };

  it.each(Object.keys(models))("%s 의 필드가 전부 있다", (name) => {
    const b = body(name);
    expect(b, `interface ${name} 없음`).not.toBe("");
    const fields = Object.keys(models[name].properties ?? {});
    const declared = [...b.matchAll(/^ {2}(\w+)\?:/gm)].map((m) => m[1]);
    expect(declared).toEqual(fields);
  });

  it("새 모양 값을 타입이 받는다", () => {
    const o: BuildOptions = {
      design: {
        core: { type: 2, core_side: "s", core_rotation: 90, core_mirror: false },
        parking: { parking_axis: "inner", parking_angle: 60 },
        regulations: { far_limit_override: 250, road_setback: 0, ratio_mode: "multi_family" },
      },
    };
    const r: ResolvedOptions = {
      design: { core: { core_side: "s" } },
      source: { "core.core_side": "prior" },
    };
    expect(o.design?.regulations?.far_limit_override).toBe(250);
    expect(r.source["core.core_side"]).toBe("prior");
  });
});
