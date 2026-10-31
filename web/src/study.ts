import { analyze, linear, type RGB, type Method } from "./pipeline";

export function syntheticDrift(
  rgb: RGB[],
  n: number,
  method: Method,
): number | null {
  const base = analyze(rgb, n, method).features;
  if (!base.every(Number.isFinite)) return null;
  const shifts = [
    { exposure: 0.6, gain: [1, 1, 1] },
    { exposure: 1.4, gain: [1, 1, 1] },
    { exposure: 1, gain: [1.4, 0.95, 0.6] },
    { exposure: 1, gain: [0.8, 1, 1.3] },
  ];
  const drifts: number[] = [];
  for (const spec of shifts) {
    const lum =
      spec.gain[0] * 0.2126 + spec.gain[1] * 0.7152 + spec.gain[2] * 0.0722;
    const changed = rgb.map((p) =>
      linear(p).map((v, c) => {
        const x = Math.max(
          0,
          Math.min(1, (v * spec.exposure * spec.gain[c]) / lum),
        );
        return Math.round(
          255 * (x <= 0.0031308 ? 12.92 * x : 1.055 * x ** (1 / 2.4) - 0.055),
        );
      }),
    );
    const f = analyze(changed, n, method).features;
    if (f.every(Number.isFinite))
      drifts.push(f.reduce((s, v, i) => s + (v - base[i]) ** 2, 0) / f.length);
  }
  return drifts.length
    ? Math.sqrt(drifts.reduce((a, b) => a + b, 0) / drifts.length)
    : null;
}
