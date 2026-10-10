// A voice-over's word timing from its WebVTT (a tag before each character): at('词') → when it starts, end → when it stops.
import { readFileSync } from 'node:fs';
export function vttTimes(path, offset = 0) {
  const raw = readFileSync(path, 'utf8'); const chars = []; let end = 0;
  const sec = (h, m, s) => +h * 3600 + +m * 60 + +s;
  for (const cue of raw.split(/\n\n+/)) {
    const m = cue.match(/(\d\d):(\d\d):(\d\d\.\d+) --> (\d\d):(\d\d):(\d\d\.\d+)\n([\s\S]+)/);
    if (!m) continue;
    let t = sec(m[1], m[2], m[3]); end = Math.max(end, sec(m[4], m[5], m[6]));
    for (const part of m[7].split(/(<\d\d:\d\d:\d\d\.\d+>)/)) {
      const tag = part.match(/<(\d\d):(\d\d):(\d\d\.\d+)>/);
      if (tag) { t = sec(tag[1], tag[2], tag[3]); continue; }
      for (const ch of part) if (/\S/.test(ch)) chars.push([ch, t]);
    }
  }
  const text = chars.map((c) => c[0]).join('');
  return { at: (s) => { const i = text.indexOf(s); if (i < 0) throw new Error(`not said: ${s}`); return chars[i][1] + offset; }, end: end + offset };
}
