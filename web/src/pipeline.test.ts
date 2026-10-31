import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { analyze, methods, predict, type Method, type Model } from "./pipeline";
import manifest from "../public/model/manifest.json";
for (const name of ["eye", "dark", "noise"])
  describe(name, () => {
    const fixture = JSON.parse(
      readFileSync(
        new URL(`../../tests/parity/${name}.json`, import.meta.url),
        "utf8",
      ),
    );
    for (const method of methods)
      it(method, () => {
        const out = analyze(fixture.rgb, fixture.size, method as Method),
          expected = fixture.expected[method];
        expect(out.mask).toEqual(expected.mask);
        for (const [key, value] of Object.entries(out.quality))
          expect(value).toBeCloseTo(expected.quality[key], 8);
        out.features.forEach((v, i) =>
          expected.features[i] === null
            ? expect(Number.isNaN(v)).toBe(true)
            : expect(Math.abs(v - expected.features[i])).toBeLessThan(1e-3),
        );
        if (expected.normalized === null) expect(out.normalized).toBeNull();
        else
          out.normalized!.forEach((p, i) =>
            p.forEach((v, c) =>
              expect(v).toBeCloseTo(expected.normalized[i][c], 8),
            ),
          );
      });
  });
it("exports finite probabilities", () => {
  expect(
    predict(manifest.model.mean, manifest.model as Model),
  ).toBeGreaterThanOrEqual(0);
  expect(
    predict(manifest.model.mean, manifest.model as Model),
  ).toBeLessThanOrEqual(1);
});
