// The OpenFilm mark and wordmark, from OpenFilm's logo (logo-dark.svg in github.com/openfilm/openfilm, docs/):
// a flag on its pole, the letter F, set beside "OpenFilm". Here as exact geometry: a GLSL signed distance field of
// the mark, and the wordmark's glyphs as paths for Canvas2D.

/** the mark, in its own units (the logo's 100 × 100 box, y down): the pole with its rounded head, as one path */
const POLE = 'M17 12H37Q40 12 40 15V27Q40 29 38.5 30.5L31 37V88Q31 92 27 92Q23 92 23 88V37L15.5 30.5Q14 29 14 27V15Q14 12 17 12Z';
/** the two flags (x, y, w, h, corner radius), cut back from the pole by GAP */
const FLAGS = [[22, 12, 64, 20, 5], [25, 44, 47, 19, 5]];
const GAP = 3.5;
/** the mark's box and its centre (the pole runs 12 → 92, the top flag reaches x = 86) */
export const MARK_BOX = { x0: 14, y0: 12, x1: 86, y1: 92 };
export const MARK_MID = { x: (MARK_BOX.x0 + MARK_BOX.x1) / 2, y: (MARK_BOX.y0 + MARK_BOX.y1) / 2 };
/** where the flags hang from the pole: the gust ripples them outward from here */
export const POLE_X = 23;

/** the lockup, as the logo sets it: logo units → lockup units (the mark), glyph units → lockup units (the word) */
export const LOCKUP = { mark: { x: -16.93, y: -96.85, s: 1.2095 }, word: { x: 110.37, y: 0, s: 0.04883 } };

/** "OpenFilm", glyph by glyph: its outline and its ink from x0 to x1 (font units, baseline at y = 0, y down) */
export const WORDMARK = [
  { ch: 'O', x0: 93.9, x1: 1484.0, d: 'M789.4 20Q591.9 20 434.3 -70.1Q276.7 -160.1 185.3 -331.1Q93.9 -502.1 93.9 -744Q93.9 -987.5 185.3 -1158.7Q276.7 -1329.9 434.3 -1420Q591.9 -1510 789.4 -1510Q986.9 -1510 1144 -1420Q1301.1 -1329.9 1392.5 -1158.7Q1484 -987.5 1484 -744Q1484 -501.5 1392.5 -330.6Q1301.1 -159.6 1144 -69.8Q986.9 20 789.4 20ZM789.4 -251Q905.1 -251 991.6 -307.7Q1078 -364.4 1126.1 -474.6Q1174.2 -584.8 1174.2 -744Q1174.2 -904.7 1126.1 -1015.1Q1078 -1125.6 991.6 -1182.3Q905.1 -1239 789.4 -1239Q673.8 -1239 587.1 -1182Q500.4 -1125.1 452 -1014.7Q403.7 -904.2 403.7 -744Q403.7 -584.8 452 -474.8Q500.4 -364.9 587.1 -308Q673.8 -251 789.4 -251Z' },
  { ch: 'p', x0: 1664.8, x1: 2746.4, d: 'M1664.8 418V-1118H1959.8V-929.8H1974.4Q1995 -974.4 2033.3 -1021.2Q2071.6 -1068.1 2134.8 -1100Q2198 -1132 2293 -1132Q2417.3 -1132 2520 -1067.9Q2622.7 -1003.9 2684.6 -876Q2746.4 -748.1 2746.4 -557.1Q2746.4 -371 2686.4 -242.6Q2626.4 -114.2 2523.4 -47.8Q2420.5 18.6 2291.3 18.6Q2200.4 18.6 2137.3 -12.2Q2074.2 -43.1 2034.8 -88.5Q1995.5 -133.9 1974.4 -178.9H1964.7V418ZM2198.9 -221.8Q2277.5 -221.8 2330.7 -264.8Q2383.9 -307.8 2411.3 -383.8Q2438.7 -459.9 2438.7 -558Q2438.7 -656.2 2411.5 -731.3Q2384.4 -806.5 2331.1 -849Q2277.9 -891.6 2198.9 -891.6Q2121.8 -891.6 2068 -850.4Q2014.2 -809.2 1986.3 -734.5Q1958.4 -659.9 1958.4 -558Q1958.4 -457.2 1986.5 -381.7Q2014.7 -306.1 2068.7 -263.9Q2122.8 -221.8 2198.9 -221.8Z' },
  { ch: 'e', x0: 2868.4, x1: 3929.7, d: 'M3420.5 21.8Q3249.3 21.8 3125.3 -48.3Q3001.3 -118.4 2934.9 -247.4Q2868.4 -376.4 2868.4 -553.2Q2868.4 -725.8 2934.5 -856Q3000.5 -986.2 3121.3 -1059.1Q3242.1 -1132 3405.4 -1132Q3514.9 -1132 3610.1 -1097.1Q3705.2 -1062.2 3777.1 -991.8Q3848.9 -921.5 3889.3 -815Q3929.7 -708.6 3929.7 -564.9V-480.7H2991.5V-669.4H3783.5L3643.4 -618.8Q3643.4 -706.2 3616.7 -770.6Q3590 -835 3537.7 -870.6Q3485.4 -906.1 3407.6 -906.1Q3329.8 -906.1 3275.6 -870.1Q3221.4 -834.1 3193.2 -772.4Q3164.9 -710.8 3164.9 -632.2V-499.3Q3164.9 -402.3 3197.3 -336.3Q3229.8 -270.4 3288.7 -237.2Q3347.6 -204 3425.3 -204Q3477.8 -204 3520.7 -219Q3563.6 -233.9 3594.5 -263.3Q3625.4 -292.6 3641.6 -335.5L3912.8 -285.4Q3885.7 -192.7 3818.8 -123.6Q3752 -54.5 3651.3 -16.3Q3550.6 21.8 3420.5 21.8Z' },
  { ch: 'n', x0: 4093.9, x1: 5113.2, d: 'M4393.8 -647.3V0H4093.9V-1118H4377L4381.8 -838.9H4363.8Q4407.8 -978.8 4497.5 -1055.4Q4587.1 -1132 4728.7 -1132Q4844.9 -1132 4931.3 -1081.5Q5017.6 -1030.9 5065.4 -936.6Q5113.2 -842.3 5113.2 -711.1V0H4813.3V-658.8Q4813.3 -763 4759.6 -822.2Q4705.8 -881.4 4611 -881.4Q4547.7 -881.4 4498.5 -853.7Q4449.4 -826 4421.6 -773.9Q4393.8 -721.7 4393.8 -647.3Z' },
  { ch: 'F', x0: 5334.8, x1: 6315.2, d: 'M5334.8 0V-1490H6315.2V-1236.7H5640.4V-820.6H6249.3V-571.6H5640.4V0Z' },
  { ch: 'i', x0: 6474.4, x1: 6803.7, d: 'M6489 0V-1118H6788.8V0ZM6638.8 -1263.7Q6571.1 -1263.7 6522.7 -1309Q6474.4 -1354.3 6474.4 -1417.7Q6474.4 -1482.4 6522.7 -1527.2Q6571.1 -1571.9 6638.8 -1571.9Q6706.9 -1571.9 6755.3 -1527.2Q6803.7 -1482.5 6803.7 -1417.8Q6803.7 -1354.3 6755.3 -1309Q6706.9 -1263.7 6638.8 -1263.7Z' },
  { ch: 'l', x0: 7003.0, x1: 7302.9, d: 'M7302.9 -1490V0H7003V-1490Z' },
  { ch: 'm', x0: 7517.0, x1: 9130.0, d: 'M7517 0V-1118H7795.7L7810.2 -839.9H7788.7Q7813.8 -943.3 7864.7 -1008.2Q7915.5 -1073.1 7983.6 -1104Q8051.8 -1134.8 8126.5 -1134.8Q8246.8 -1134.8 8321 -1058.1Q8395.1 -981.5 8430.1 -821.7H8395.3Q8420.2 -929.5 8476.9 -998.9Q8533.7 -1068.2 8610.8 -1101.5Q8688 -1134.8 8773.7 -1134.8Q8876.1 -1134.8 8956.7 -1090.1Q9037.2 -1045.4 9083.6 -960.6Q9130 -875.9 9130 -754V0H8830.2V-696.6Q8830.2 -791.7 8778.9 -838Q8727.6 -884.4 8652.8 -884.4Q8596.1 -884.4 8554.6 -859.6Q8513 -834.9 8490.8 -790.9Q8468.6 -747 8468.6 -687.9V0H8178.5V-704.9Q8178.5 -787.1 8130 -835.7Q8081.5 -884.4 8004.3 -884.4Q7951.7 -884.4 7909 -860.1Q7866.4 -835.8 7841.7 -789.6Q7816.9 -743.3 7816.9 -675.9V0Z' },
];

/** a path of M / L / H / V / Q / Z (absolute) as a polygon, each curve in `n` straight steps */
function polygon(d, n = 8) {
  const tok = d.match(/[MLHVQZ]|-?\d*\.?\d+/g);
  const out = [];
  let x = 0, y = 0, cmd = '';
  for (let i = 0; i < tok.length; ) {
    if (/[MLHVQZ]/.test(tok[i])) cmd = tok[i++];
    if (cmd === 'Z') continue;
    const num = () => Number(tok[i++]);
    if (cmd === 'M' || cmd === 'L') { x = num(); y = num(); out.push([x, y]); }
    else if (cmd === 'H') { x = num(); out.push([x, y]); }
    else if (cmd === 'V') { y = num(); out.push([x, y]); }
    else if (cmd === 'Q') {
      const cx = num(), cy = num(), ex = num(), ey = num();
      for (let k = 1; k <= n; k++) {
        const u = k / n, a = (1 - u) * (1 - u), b = 2 * u * (1 - u), c = u * u;
        out.push([a * x + b * cx + c * ex, a * y + b * cy + c * ey]);
      }
      x = ex; y = ey;
    }
  }
  const [a, b] = [out[0], out[out.length - 1]];
  if (a[0] === b[0] && a[1] === b[1]) out.pop(); // closed where it began: no edge of length 0
  return out;
}

const f1 = (v) => v.toFixed(3);
const POLE_PTS = polygon(POLE);

/**
 * GLSL: sdMark(p, amp, phase) in logo units (y down): the pole, and the flags cut back from it. A gust ripples the
 * flags: a wave of `amp` units travels out along them from the pole (`phase` in radians), growing toward their ends.
 */
export const GLSL_MARK = /* glsl */ `
const int POLE_N = ${POLE_PTS.length};
const vec2 POLE_V[POLE_N] = vec2[POLE_N](${POLE_PTS.map(([x, y]) => `vec2(${f1(x)}, ${f1(y)})`).join(', ')});
float sdPole(vec2 p) {
  float d = dot(p - POLE_V[0], p - POLE_V[0]), s = 1.0;
  for (int i = 0; i < POLE_N; i++) {
    int j = i == 0 ? POLE_N - 1 : i - 1;
    vec2 e = POLE_V[j] - POLE_V[i], w = p - POLE_V[i];
    vec2 b = w - e * clamp(dot(w, e) / dot(e, e), 0.0, 1.0);
    d = min(d, dot(b, b));
    bvec3 c = bvec3(p.y >= POLE_V[i].y, p.y < POLE_V[j].y, e.x * w.y > e.y * w.x);
    if (all(c) || all(not(c))) s = -s;
  }
  return s * sqrt(d);
}
float sdRBox(vec2 p, vec4 r, float rad) {
  vec2 h = 0.5 * r.zw, q = abs(p - r.xy - h) - h + rad;
  return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - rad;
}
float sdMark(vec2 p, float amp, float phase) {
  float pole = sdPole(p);
  float run = max(0.0, p.x - ${f1(POLE_X)});
  vec2 f = p - vec2(0.0, amp * sat(run / ${f1(MARK_BOX.x1 - POLE_X)}) * sin(run * 0.12 - phase));
  float d = pole;
  ${FLAGS.map(([x, y, w, h, r]) => `d = min(d, max(sdRBox(f, vec4(${f1(x)}, ${f1(y)}, ${f1(w)}, ${f1(h)}), ${f1(r)}), ${f1(GAP)} - pole));`).join('\n  ')}
  return d;
}
`;
