/* Timing helpers shared by the shots: every one is a pure function of t. */
export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, k) => a + (b - a) * k;
export const prog = (t, a, b) => clamp((t - a) / (b - a));
export const smooth = (x) => { x = clamp(x); return x * x * (3 - 2 * x); };
export const inout = (x) => { x = clamp(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
export const out3 = (x) => 1 - Math.pow(1 - clamp(x), 3);
export const out5 = (x) => 1 - Math.pow(1 - clamp(x), 5);
export const in3 = (x) => Math.pow(clamp(x), 3);
export const outBack = (x, s = 1.70158) => { x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1; };
/* a damped spring from 0 to 1: overshoots, settles */
export const spring = (x, f = 3.2, d = 5.5) => { if (x <= 0) return 0; return 1 - Math.exp(-d * x) * Math.cos(f * Math.PI * x); };
export const rnd = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
/* the projective map of a 1920 × 1080 box onto a quad (TL, TR, BR, BL), for transform-origin 0 0 */
export function quadMatrix(q, W = 1920, H = 1080) {
  const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = q;
  const dx1 = x1 - x2, dx2 = x3 - x2, dy1 = y1 - y2, dy2 = y3 - y2, sx = x0 - x1 + x2 - x3, sy = y0 - y1 + y2 - y3;
  const den = dx1 * dy2 - dx2 * dy1;
  const g = (sx * dy2 - dx2 * sy) / den, h = (dx1 * sy - sx * dy1) / den;
  const a = x1 - x0 + g * x1, b = x3 - x0 + h * x3, c = x0, d = y1 - y0 + g * y1, e = y3 - y0 + h * y3, f = y0;
  return `matrix3d(${a / W},${d / W},0,${g / W},${b / H},${e / H},0,${h / H},0,0,1,0,${c},${f},0,1)`;
}
export const fontsReady = () => document.fonts.ready.then(() => Promise.all([...document.images].map((i) => i.decode().catch(() => {}))));
