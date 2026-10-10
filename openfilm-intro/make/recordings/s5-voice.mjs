// S5's voice as s5.html lays it out (lib/s5-voice.json): the file cut at its pauses, each line at its own place.
// said('词') → when the word is said in s5.html.
import { readFileSync } from 'node:fs';
import { vttTimes } from './vtt.mjs';

const ROOT = new URL('../..', import.meta.url).pathname;     /* the example's folder */
export const VOICE = JSON.parse(readFileSync(ROOT + 'lib/s5-voice.json', 'utf8'));
const file = vttTimes(ROOT + VOICE.vtt);
/* a word's time in the file, moved with the line it is in (a cut sits in the pause just before a line's first word) */
export function said(word) {
  const c = file.at(word);
  const line = VOICE.lines.find((l) => c + 0.05 >= l.from && c + 0.05 < l.to) ?? VOICE.lines.at(-1);
  return line.at + (c - line.from);
}
