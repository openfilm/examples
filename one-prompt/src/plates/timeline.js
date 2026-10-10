// The edit: which plate plays when, and the film's sections. Plate boundaries come from lyric words and the
// beat grid (handoff.js CUT). Each section is a page of its own (intro.html, verse.html…), a clip in film.html.
import { CUT } from './handoff.js';
import { sparkPlan } from './premiere-kit.js';

/** the intro's second hit (beat 4): the rewind, run forward, has landed; the construction sheet starts */
export const INTRO_HIT2 = 0.102 + 4 * (60 / 122);
/** the outro plays until its line has retracted into the caret (where its rewind used to start); then the
 *  caret turns into the mark and the address, and the film ends a little after the song */
export const BRAND_T = sparkPlan().parkT + 0.27;
export const FILM_END = 90.9;

/** every plate: its section, its module, and its window in song seconds */
export const PLATES = [
  { section: 'intro', id: 'unfold', load: () => import('./unfold.js'), start: 0, end: INTRO_HIT2 },
  { section: 'intro', id: 'construct', load: () => import('./construct.js'), start: INTRO_HIT2, end: CUT.prompt },
  { section: 'verse', id: 'prompt', load: () => import('./prompt.js'), start: CUT.prompt, end: CUT.ridge },
  { section: 'verse', id: 'ridge', load: () => import('./ridge.js'), start: CUT.ridge, end: CUT.city },
  { section: 'verse', id: 'city', load: () => import('./city.js'), start: CUT.city, end: CUT.plot },
  { section: 'pre-chorus', id: 'plot', load: () => import('./plot.js'), start: CUT.plot, end: CUT.hook },
  { section: 'chorus', id: 'hook1', load: () => import('./hookmontage.js'), start: CUT.hook, end: CUT.zoetrope, params: { n: 1 } },
  { section: 'chorus', id: 'zoetrope', load: () => import('./zoetrope.js'), start: CUT.zoetrope, end: CUT.beam },
  { section: 'chorus', id: 'beam', load: () => import('./beam.js'), start: CUT.beam, end: CUT.marquee },
  { section: 'chorus', id: 'marquee', load: () => import('./marquee.js'), start: CUT.marquee, end: CUT.sky },
  { section: 'verse-2', id: 'sky', load: () => import('./sky.js'), start: CUT.sky, end: CUT.mix },
  { section: 'verse-2', id: 'mix', load: () => import('./mix.js'), start: CUT.mix, end: CUT.stadium },
  { section: 'verse-2', id: 'stadium', load: () => import('./stadium.js'), start: CUT.stadium, end: CUT.edit },
  { section: 'drop', id: 'edit', load: () => import('./edit.js'), start: CUT.edit, end: CUT.hook2 },
  { section: 'final-chorus', id: 'hook2', load: () => import('./hookmontage.js'), start: CUT.hook2, end: CUT.earth, params: { n: 2 } },
  { section: 'final-chorus', id: 'earth', load: () => import('./earth.js'), start: CUT.earth, end: CUT.premiere },
  { section: 'final-chorus', id: 'premiere', load: () => import('./premiere.js'), start: CUT.premiere, end: CUT.outro },
  { section: 'outro', id: 'outro', load: () => import('./outro.js'), start: CUT.outro, end: BRAND_T },
  { section: 'outro', id: 'brand', load: () => import('./brandout.js'), start: BRAND_T, end: FILM_END },
];

/** a time as film.html writes it: to the millisecond */
const ms = (t) => Math.round(t * 1000) / 1000;

/** a section's window in song seconds: where its clip starts in film.html, and how long it plays */
export function sectionSpan(name) {
  const plates = PLATES.filter((p) => p.section === name);
  if (!plates.length) throw new Error(`no section "${name}" (sections: ${[...new Set(PLATES.map((p) => p.section))].join(', ')})`);
  return { start: ms(plates[0].start), end: ms(plates[plates.length - 1].end) };
}

/** the engine's timeline for one section */
export const makeTimeline = (name) => () => PLATES.filter((p) => p.section === name);
