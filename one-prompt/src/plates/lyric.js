// Lyric lookups by word index (see src/lyrics.js for the table). Scenes use these, never raw times.
import { WORDS, LINES } from '../lyrics.js';
export { WORDS, LINES };
export const wStart = (i) => WORDS[i][1];
export const wEnd = (i) => WORDS[i][2];
export const wText = (i) => WORDS[i][0];
/** 0..1 sung progress of word i at t */
export const wProg = (i, t) => Math.max(0, Math.min(1, (t - wStart(i)) / Math.max(0.05, wEnd(i) - wStart(i))));
/** per-character start times across word i (even split of the sung span, capped at 0.5 s) */
export function charTimes(i) {
  const s = wText(i), a = wStart(i), d = Math.min(0.5, Math.max(0.12, wEnd(i) - a));
  return [...s].map((_, k) => a + (k / s.length) * d);
}
