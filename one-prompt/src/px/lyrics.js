// Ported from mexicat/pdoom-video (MIT, see LICENSE-pdoom-video.txt) and adapted for One Prompt.
// Word-timed lyrics (built from src/lyrics.js) with queries for karaoke rendering.
import { smart } from './type.js';

export class Lyrics {
  lines;
  words;
  constructor(j) {
    // display text gets curly apostrophes and quotes (the data keeps the typed ones); mono UI
    // text that wants them straight uses plain()
    this.lines = (j.lines).map((l, li) => ({
      ...l,
      i: li,
      text: smart(l.text),
      words: (l.words).map((w, wi) => ({ ...w, w: smart(w.w), line: li, index: wi, gi: 0 })),
    }));
    this.words = this.lines.flatMap((l) => l.words);
    this.words.forEach((w, i) => (w.gi = i));
  }

  /** From One Prompt's lyrics.js (WORDS = [text, start, end], LINES = [first, last]). */
  static fromTables(words, lines) {
    return new Lyrics({ lines: lines.map(([a, b]) => ({ text: words.slice(a, b + 1).map((w) => w[0]).join(' '), start: words[a][1], end: words[b][2], words: words.slice(a, b + 1).map((w) => ({ w: w[0], start: w[1], end: w[2] })) })) });
  }

  /** The line being sung at t (or null in gaps). */
  lineAt(t) {
    return this.lines.find((l) => t >= l.start && t < l.end) ?? null;
  }
  /** Most recent line that started at or before t. */
  lastLine(t) {
    let best = null;
    for (const l of this.lines) if (l.start <= t) best = l;
    return best;
  }
  nextLine(t) {
    return this.lines.find((l) => l.start > t) ?? null;
  }
  linesIn(t0, t1) {
    return this.lines.filter((l) => l.end > t0 && l.start < t1);
  }
  /** Lines whose text includes `s` (case-insensitive, straight or curly quotes). Handy for finding a lyric by content. */
  find(s) {
    const q = fold(s);
    return this.lines.filter((l) => fold(l.text).includes(q));
  }
  /** First line containing `s`; throws if missing (fail loudly while authoring). */
  get(s, nth = 0) {
    const l = this.find(s)[nth];
    if (!l) throw new Error(`lyric not found: ${s}`);
    return l;
  }
  wordAt(t) {
    return this.words.find((w) => t >= w.start && t < w.end) ?? null;
  }
  lastWord(t) {
    let best = null;
    for (const w of this.words) if (w.start <= t) best = w;
    return best;
  }
  /** Words whose normalized text matches (e.g. 'p(doom)'). */
  findWords(s) {
    const q = norm(s);
    return this.words.filter((w) => norm(w.w) === q);
  }

  /**
   * Sung progress of a word at time t: 0 before start, 1 after end, linear inside
   * (or piecewise across syllables when available). Use for karaoke wipes.
   */
  static wordProgress(w, t) {
    if (t <= w.start) return 0;
    if (t >= w.end) return 1;
    if (w.syl && w.syl.length > 1) {
      const n = w.syl.length;
      for (let i = 0; i < n; i++) {
        const [a, b] = w.syl[i];
        if (t < a) return i / n;
        if (t < b) return (i + (t - a) / Math.max(1e-3, b - a)) / n;
      }
      return 1;
    }
    return (t - w.start) / Math.max(1e-3, w.end - w.start);
  }

  /** Progress through a whole line in characters (0..text.length), for per-glyph wipes. */
  static lineCharProgress(l, t) {
    let chars = 0;
    for (const w of l.words) {
      const p = Lyrics.wordProgress(w, t);
      chars += p * w.w.length;
      if (p < 1) break;
      chars += 1; // the space
    }
    return Math.min(chars, l.text.length);
  }
}

export const norm = (s) => s.toLowerCase().replace(/[^a-z0-9()]/g, '');
const fold = (s) => s.toLowerCase().replace(/[\u2018\u2019]/g, "'").replace(/[\u201C\u201D]/g, '"');
