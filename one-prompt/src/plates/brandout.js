// Plate `brandout` (BRAND_T → FILM_END): the outro has drawn its one line back into the caret at the mark's centre
// (MARK_C). The caret wakes and stands up to the mark's height; then, as a clock hand through the mark's centre, it
// sweeps half a turn and leaves the OpenFilm mark (a flag on its pole, the F) behind it, engraved along its outline
// and then filled, a gust rippling the flags once. The wordmark is set beside it, and the caret types the address
// under it.
import * as THREE from 'three';
import { Scene } from '../px/scene.js';
import { FSPass, Layer2D, clearRT } from '../px/gl.js';
import { LineBatch } from '../px/lines.js';
import { sparkHead } from '../px/motifs.js';
import { F, font } from '../px/type.js';
import { LIN, rgba } from '../px/palette.js';
import { clamp, ease, lerp } from '../px/util.js';
import { CARET_H1, MARK_C } from './handoff.js';
import { hotType, EDGE_POST } from './leader-kit.js';
import { GLSL_MARK, MARK_BOX, MARK_MID, LOCKUP, WORDMARK } from './brand.js';

const seg = (t, a, b) => clamp((t - a) / Math.max(1e-6, b - a));
const MX = MARK_C.x, MY = MARK_C.y; // the mark's centre (px)
// the lockup's scale (px per lockup unit), so that the whole of it, mark to the end of the word, is centred on the frame
const { mark: LM, word: LW } = LOCKUP;
const lockX = (x) => LM.x + LM.s * x; // logo units → lockup units
const wordX = (x) => LW.x + LW.s * x; // glyph units → lockup units
const K = (960 - MX) / ((lockX(MARK_BOX.x0) + wordX(WORDMARK[WORDMARK.length - 1].x1)) / 2 - lockX(MARK_MID.x));
const MS = K * LM.s; // px per logo unit
const RPX = Math.hypot(MARK_BOX.x1 - MARK_BOX.x0, MARK_BOX.y1 - MARK_BOX.y0) / 2 * MS; // the hand's half length: reaches the mark's far corners
// the wordmark: px per glyph unit, its baseline, and where its first glyph's ink starts
const WK = K * LW.s;
const WB = MY + (LW.y - (LM.y + LM.s * MARK_MID.y)) * K;
const WX = MX + (wordX(WORDMARK[0].x0) - lockX(MARK_MID.x)) * K;
const URL = 'openfilm.dev', URL_HOT = [4, 8]; // "film" in the signal colour
const UX = WX + 8, UB = WB + 80, US = 36, UADV = US * 0.6;
const GLYPHS = WORDMARK.map((g) => ({ ...g, path: new Path2D(g.d) }));

const FRAG = /* glsl */ `
${GLSL_MARK}
uniform float uT, uFill, uAmp, uPhase, uFade, uSweep, uHand; uniform vec2 uC, uMid; uniform float uS;
float eline(float u, float w) { float d = abs(u - floor(u + 0.5)); float aa = max(fwidth(u), 1e-4) * 0.75; return sat((w * 0.5 - d) / aa + 0.5); }
void main() {
  vec2 fp = vec2(FRAG_PX.x, 1080.0 - FRAG_PX.y);
  vec2 q = (fp - uC) / uS + uMid;
  float d = sdMark(q, uAmp, uPhase);
  float dp = d * uS; // the same distance in px
  vec3 col = C_INK * 0.0;
  // the sweep: only what the hand has passed is there (both ends of the hand paint, half a turn fills it)
  vec2 r = fp - uC;
  float a = mod(atan(r.x, -r.y) - uHand + 6.2831853, 3.14159265);   // angle behind the hand, 0..pi
  float swept = uSweep >= 3.14159 ? 1.0 : step(3.14159265 - uSweep, a);
  float fresh = exp(-(3.14159265 - a) / 0.35) * step(uSweep, 3.1415) ; // just painted
  if (d > 0.0) {
    // rings going out from the filled mark
    float line = eline(dp / 14.5 - uT * 0.9, 0.14);
    col += mix(C_EMBER, C_BONE, sat(dp / 100.0)) * line * 0.12 * exp(-dp / 160.0) * uFill;
  }
  float aa = fwidth(d) * 0.9 + 1e-4;
  float cov = sat(0.5 - d / aa) * swept;
  float lit = 0.55 + 0.45 * sat(1.0 - dot(q, vec2(0.6, 0.8)) / 130.0);
  // engraved first: lines along its outline, inset one after another; then filled
  vec3 eng = C_BONE * (0.3 + 0.95 * eline(-dp / 4.9, 0.35 + 0.55 * lit));
  vec3 solid = C_BONE * (0.85 + 0.15 * lit);
  vec3 m = mix(eng, solid, uFill);
  float rim = sat(1.0 - abs(d) / (aa * 2.5));
  m += (C_SIGNAL * 1.5 + C_EMBER) * (rim * exp(-max(0.0, uT) * 3.0) + fresh * 1.2);
  col = mix(col, m, cov);
  fragColor = vec4(col * (1.0 - uFade), 1.0);
}`;

export default class BrandOut extends Scene {
  bg = new FSPass(FRAG, {
    uT: { value: 0 }, uFill: { value: 0 }, uAmp: { value: 0 }, uPhase: { value: 0 }, uFade: { value: 0 }, uSweep: { value: 0 }, uHand: { value: 0 },
    uC: { value: new THREE.Vector2(MX, MY) }, uMid: { value: new THREE.Vector2(MARK_MID.x, MARK_MID.y) }, uS: { value: MS },
  });
  lb = new LineBatch(4000, { screen2D: true, blend: 'add' });
  text = new Layer2D();

  render(f, out) {
    const { renderer, comp, start: S0, end: S1 } = this.ctx;
    const t = f.t;
    const tWake = S0 + 0.04, tGlide = tWake + 0.06, tSweep = tGlide + 0.55, tFill = tSweep + 0.1, tWord = tFill + 0.1, tUrl = tWord + 0.38;
    const fade = seg(t, S1 - 0.45, S1 - 0.03);
    // the caret: wake, stand up to the hand's length at the mark's centre
    const wake = ease.outCubic(seg(t, S0, tWake));
    const up = ease.outExpo(seg(t, tGlide - 0.08, tGlide + 0.1));
    const sw = ease.inOutCubic(seg(t, tGlide + 0.1, tSweep));
    const cx = MX, cy = MY;
    const half = lerp(CARET_H1.h / 2, RPX, up);
    const handA = sw * Math.PI; // clockwise from 12 o'clock
    // the gust: once the mark is full, a wave runs out along the flags and dies away
    const g = Math.max(0, t - tFill);
    const amp = t > tFill ? 3.2 * Math.exp(-g * 3) * (1 - Math.exp(-g * 20)) : 0;
    const u = this.bg.u;
    u.uT.value = t - tFill; u.uFill.value = ease.outCubic(seg(t, tFill, tFill + 0.35)); u.uAmp.value = amp; u.uPhase.value = g * 10; u.uFade.value = fade;
    u.uSweep.value = t < tGlide + 0.1 ? 0 : sw >= 1 ? Math.PI + 0.01 : sw * Math.PI; u.uHand.value = handA;
    clearRT(renderer, out, [0, 0, 0]);
    this.bg.render(renderer, out);
    const lb = this.lb; lb.clear();
    const handOn = 1 - seg(t, tSweep - 0.02, tSweep + 0.14);
    if (handOn > 0 && t >= S0) {
      const dx = Math.sin(handA) * half, dy = -Math.cos(handA) * half;
      const w = lerp(CARET_H1.w, 5, up);
      const col = [LIN.signal[0] * (1 + 1.5 * up), LIN.signal[1] * (1 + 1.5 * up), LIN.signal[2] * (1 + 1.5 * up)];
      lb.seg2(cx - dx, cy - dy, cx + dx, cy + dy, w, col, (0.85 + 0.15 * wake) * handOn);
      if (up > 0.5) { sparkHead(lb, cx + dx, cy + dy, t, 0.7, handOn); sparkHead(lb, cx - dx, cy - dy, t, 0.7, handOn); }
    }
    lb.render(renderer, out);
    // the wordmark, glyph by glyph, widening as it is set; and the address
    const L = this.text; L.clear();
    const c = L.ctx;
    const o = 1 - fade;
    if (t >= tWord) {
      const sx = lerp(0.7, 1, ease.outExpo(seg(t, tWord, tWord + 0.35)));
      const n = Math.min(GLYPHS.length, Math.floor((t - tWord) / 0.035) + 1);
      for (let k = 0; k < n; k++) {
        const gl = GLYPHS[k];
        c.save();
        c.translate(WX, WB); c.scale(WK * sx, WK); c.translate(-GLYPHS[0].x0, 0);
        c.fillStyle = hotType(t - (tWord + k * 0.035), o, 0.3);
        c.fill(gl.path);
        c.restore();
      }
    }
    if (t >= tUrl) {
      c.textBaseline = 'alphabetic';
      c.font = font(F.mono(500), US);
      const n = Math.min(URL.length, Math.floor((t - tUrl) / 0.05) + 1);
      for (let k = 0; k < n; k++) { c.fillStyle = k >= URL_HOT[0] && k < URL_HOT[1] ? rgba('signal', o) : hotType(t - (tUrl + k * 0.05), o * 0.9, 0.3); c.fillText(URL[k], UX + k * UADV, UB); }
      const done = t > tUrl + URL.length * 0.05;
      const blink = !done || Math.floor((t - tUrl - URL.length * 0.05) * 2.2) % 2 === 0;
      c.fillStyle = rgba('signal', (blink ? 1 : 0.12) * o);
      c.fillRect(UX + n * UADV + 6, UB - US * 0.78, 5, US * 0.95);
    }
    comp.draw(renderer, L.upload(), out);
    const flash = t > tSweep ? 0.03 * Math.exp(-(t - tSweep) * 30) : 0;
    return { ...EDGE_POST, bloom: 0.62, halation: 0.26, flash };
  }
}
