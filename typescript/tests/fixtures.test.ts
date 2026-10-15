/**
 * fixtures/build_options/*.json — expected(정규화된 BuildOptions)의 키가 전부 options.ts
 * (생성물) 의 interface 필드 안에 있는가. TS 에는 런타임 검증기가 없어 모양만 본다 —
 * 값의 정답은 python/tests/test_fixtures.py 가 정본으로 되검사한다.
 */
import { readFileSync, readdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const FIXTURES = resolve(here, "../../fixtures/build_options");
const ts = readFileSync(resolve(here, "../src/options.ts"), "utf-8");

// {interface: {field: type}} — options.ts 는 생성물이라 `  name?: type;` 한 줄 모양이 고정이다
const interfaces: Record<string, Record<string, string>> = {};
for (const m of ts.matchAll(/export interface (\w+) \{([\s\S]*?)\n\}/g)) {
  const fields: Record<string, string> = {};
  for (const f of m[2].matchAll(/^ {2}(\w+)\??: (.+);$/gm)) fields[f[1]] = f[2];
  interfaces[m[1]] = fields;
}

function checkShape(name: string, obj: Record<string, unknown>, path: string) {
  const fields = interfaces[name];
  expect(fields, `interface ${name} 없음 (${path})`).toBeDefined();
  for (const [k, v] of Object.entries(obj)) {
    expect(Object.keys(fields), `${path}.${k} 는 ${name} 에 없는 키`).toContain(k);
    const t = fields[k].replace(/ \| null$/, "");
    if (interfaces[t] && v && typeof v === "object" && !Array.isArray(v)) {
      checkShape(t, v as Record<string, unknown>, `${path}.${k}`);
    }
  }
}

const cases = readdirSync(FIXTURES).filter((f) => f.endsWith(".json")).sort();

describe("fixtures/build_options", () => {
  it("케이스가 있다", () => {
    expect(cases).toContain("empty.json");
  });

  it.each(cases)("%s 의 expected 가 BuildOptions 모양이다", (file) => {
    const fx = JSON.parse(readFileSync(resolve(FIXTURES, file), "utf-8"));
    expect(Object.keys(fx)).toEqual(["input", "expected"]);
    checkShape("BuildOptions", fx.expected, "expected");
    // 세 묶음이 전부 있다 — 정규화는 기본값을 다 채운다
    expect(Object.keys(fx.expected)).toEqual(Object.keys(interfaces.BuildOptions));
  });

  it("core_type_renumber 는 1~7 의 순열이다", () => {
    const fx = JSON.parse(
      readFileSync(resolve(here, "../../fixtures/core_type_renumber.json"), "utf-8"),
    );
    const table: Record<string, number> = fx.old_to_new;
    expect(Object.keys(table).sort()).toEqual(["1", "2", "3", "4", "5", "6", "7"]);
    expect([...Object.values(table)].sort()).toEqual([1, 2, 3, 4, 5, 6, 7]);
  });
});
