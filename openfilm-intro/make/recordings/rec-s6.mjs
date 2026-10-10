// S6's editor: the desktop app (dark, 1600 × 1000 at 2×, Layers folded away, the project's assets open on the right:
// the agent here is the one in the terminal s6.html draws) on a perfume ad, VESPER (make/demo-projects/vesper), as the agent
// makes it. Its film.html is written here a piece at a time at the moments the terminal shows the agent writing
// (lib/s6-plan.json), so Studio fills the way it does while an agent works, and the film plays as it grows; then the
// agent's fix after the interruption (the wordmark in gold); the person's own edit: the video folder opened in the
// assets, a third shot (the bottle lighting up, the lilies opening) dragged onto the pages' row over the second shot
// (Studio gives it a track of its own between them), the film looked at there, the shot's tail trimmed to the end card,
// played; and the export dialog opened (More → Export…), which s6.html surrounds with the formats it writes. The hand
// is not drawn here: s6.html draws one hand across both windows, where this run put the real one (lib/s6-targets.json).
// Nothing is exported (that would write into ~/Movies).
// → assets/video/s6-ui.mp4 (3200 × 2000, 30 fps, every frame a key frame), its 0 = the plan's rec0.
// node make/recordings/rec-s6.mjs [work dir]   (from the example's folder)
import { execFileSync } from 'node:child_process';
import { cpSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { desktop } from './desktop.mjs';

const WORK = process.argv[2] || '/tmp/s6-rec';
const ROOT = new URL('../..', import.meta.url).pathname;     /* the example's folder */
const PLAN = JSON.parse(readFileSync(join(ROOT, 'lib/s6-plan.json'), 'utf8'));
const FRAMES = join(WORK, 'frames');
const FPS = 30;
const r = (t) => t - PLAN.rec0;                                  /* the plan's seconds → the recording's */

rmSync(WORK, { recursive: true, force: true }); mkdirSync(FRAMES, { recursive: true });
/* the project as the agent finds it: footage, music, fonts, the scenes it will write held back until it writes them */
const SRC = join(ROOT, 'make/demo-projects/vesper');
const src = join(WORK, 'src');
cpSync(SRC, src, { recursive: true, filter: (p) => !p.includes('/scenes') && !p.includes('/.film') });
/* its Chinese font is the example's own (fonts/NotoSansSC.ttf), not kept twice */
cpSync(join(ROOT, 'fonts/NotoSansSC.ttf'), join(src, 'fonts/NotoSansSC.ttf'));
mkdirSync(join(src, 'scenes'), { recursive: true });
const EMPTY = '<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=1920, height=1080">\n</head>\n<body>\n</body>\n</html>\n';
writeFileSync(join(src, 'film.html'), EMPTY);
const app = await desktop({ dir: join(WORK, 'app'), projects: { VESPER: src } });
const project = join(WORK, 'app/projects/VESPER');
const film = join(project, 'film.html');
const scene = (name, text = readFileSync(join(SRC, 'scenes', name), 'utf8')) => writeFileSync(join(project, 'scenes', name), text);
const write = (tracks) => writeFileSync(film, `<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=1920, height=1080">\n</head>\n<body>\n${tracks.filter((t) => t.length).map((t) => `<section>\n${t.join('\n')}\n</section>\n`).join('')}</body>\n</html>\n`);
await app.open('VESPER');
const page = app.page, mouse = page.mouse;
await page.waitForTimeout(6000);
const layers = page.getByRole('button', { name: 'Hide layers' });
if (await layers.count()) { await layers.first().click(); await page.waitForTimeout(500); }
await page.evaluate(() => window.openfilmDesktop?.setAssetsOpen?.(true));          /* the right column: the project's assets */
await page.waitForTimeout(1500);
/* the inspector open from the start: a selection does not then move the picture under the hand */
const insp = page.getByRole('button', { name: 'Show inspector' });
if (await insp.count()) { await insp.first().click(); await page.waitForTimeout(800); }

/* what the agent writes, in order */
const PLATES = ['  <video id="vesper-a" src="assets/video/vesper-a.mp4#t=0.7,5.15" at="0"></video>', '  <video id="vesper-b" src="assets/video/vesper-b.mp4#t=0.6,4.7" at="4.45"></video>'];
const MUSIC = ['  <audio id="vesper" src="assets/audio/vesper.mp3#t=0,11.95" at="0"></audio>'];
const TITLE = '  <iframe id="title" src="scenes/title.html" at="0"></iframe>', LINE = '  <iframe id="line" src="scenes/line.html" at="4.45"></iframe>', END = '  <iframe id="end" src="scenes/end.html" at="8.55"></iframe>';
const steps = [
  [r(PLAN.steps[0]), () => write([[], PLATES, MUSIC])],
  [r(PLAN.steps[1]), () => { scene('title.html'); write([[TITLE], PLATES, MUSIC]); }],
  [r(PLAN.steps[2]), () => { scene('line.html'); write([[TITLE, LINE], PLATES, MUSIC]); }],
  [r(PLAN.steps[3]), () => { scene('end.html'); write([[TITLE, LINE, END], PLATES, MUSIC]); }],
  /* 字标改成金色: the agent's fix, after the person stopped it */
  [r(PLAN.fix), () => scene('title.html', readFileSync(join(SRC, 'scenes/title.html'), 'utf8').replace('color: #f3e7cf; text-shadow: 0 2px 24px rgba(0,0,0,.25);', 'color: #e3bf7f; text-shadow: 0 2px 24px rgba(0,0,0,.3), 0 0 40px rgba(227,191,127,.25);'))],
];

/* where the hand goes, found when it goes there (in css px of the window), kept for s6.html */
const TARGETS = {};
const center = async (loc) => { const b = await loc.boundingBox(); return [b.x + b.width / 2, b.y + b.height / 2]; };
const slider = () => page.locator('[role="slider"][aria-valuemax]').first();
const seek = async (key) => { await slider().focus(); await page.keyboard.press(key); };
const rulerAt = async (sec) => page.evaluate((s) => {
  const lab = [...document.querySelectorAll('*')].find((e) => e.children.length === 0 && e.textContent.trim() === `00:${String(s).padStart(2, '0')}`);
  const r = lab.getBoundingClientRect(); return [r.x + 1, r.y + r.height / 2];
}, sec);
const A = [];
const act = (t, fn) => A.push({ t: r(t), fn });
/* the film plays as it grows, from its start */
let playing = false;
act(PLAN.play[0], async () => { await seek('Home'); playing = true; });
act(PLAN.play[1], async () => { playing = false; });
/* the person's own edit: the video folder opened in the assets; the third shot dragged onto the pages' row at the
   second shot (a track of its own, between the pages and the footage); the film looked at there; the shot's tail
   trimmed back to the end card; a moment of it played */
const tile = async (re) => page.evaluate((src) => {
  const e = [...document.querySelectorAll('[draggable=true]')].find((x) => new RegExp(src).test(x.textContent.trim()));
  if (!e) return null; const r = e.getBoundingClientRect(); const im = e.querySelector('img, video, canvas') ?? e; const b = im.getBoundingClientRect();
  return { at: [b.x + b.width / 2, b.y + b.height / 2], box: [b.x, b.y, b.width, b.height] };
}, re.source);
const block = async (id) => page.evaluate((id) => { const b = [...document.querySelectorAll('[data-block-id]')].find((e) => e.dataset.blockId.startsWith(id)); if (!b) return null; const r = b.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; }, id);
act(PLAN.folder - 0.1, async () => { const f = await tile(/video$/); TARGETS.folder = f.at; await mouse.move(...f.at); });
act(PLAN.folder, async () => { await mouse.dblclick(...TARGETS.folder); });
act(PLAN.grab - 0.1, async () => { const c = await tile(/vesper-c\.mp4$/); TARGETS.clip = c.at; TARGETS.clipBox = c.box; await mouse.move(...c.at); });
act(PLAN.grab, async () => { await mouse.down(); });
const DROP = 16;                                                       /* frames the drag takes */
for (let i = 1; i <= DROP; i++) {
  act(PLAN.grab + 0.05 + ((PLAN.drop - 0.05 - PLAN.grab) * i) / DROP, async () => {
    if (!TARGETS.drop) { const l = await block('line'); TARGETS.drop = [l[0] + 6, l[1] + l[3] / 2]; }
    const k = i / DROP, e = k < 0.5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2;
    await mouse.move(TARGETS.clip[0] + (TARGETS.drop[0] - TARGETS.clip[0]) * e, TARGETS.clip[1] + (TARGETS.drop[1] - TARGETS.clip[1]) * e);
  });
}
act(PLAN.drop, async () => { await mouse.up(); });
act(PLAN.view - 0.1, async () => { TARGETS.ruler = await rulerAt(PLAN.viewAt); await mouse.move(...TARGETS.ruler); });
act(PLAN.view, async () => { await mouse.click(...TARGETS.ruler); });
act(PLAN.trim[0] - 0.12, async () => {
  const c = await block('vesper-c'), e = await block('end');
  TARGETS.edge = [c[0] + c[2] - 2, c[1] + c[3] / 2]; TARGETS.edgeTo = [e[0], TARGETS.edge[1]]; await mouse.move(...TARGETS.edge);
});
act(PLAN.trim[0], async () => { await mouse.down(); });
const TRIM = 9;
for (let i = 1; i <= TRIM; i++) {
  act(PLAN.trim[0] + 0.03 + ((PLAN.trim[1] - 0.06 - PLAN.trim[0]) * i) / TRIM, async () => {
    const k = i / TRIM, e = k < 0.5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2;
    await mouse.move(TARGETS.edge[0] + (TARGETS.edgeTo[0] - TARGETS.edge[0]) * e, TARGETS.edge[1]);
  });
}
act(PLAN.trim[1], async () => { await mouse.up(); });
act(PLAN.play2[0], async () => { playing = true; });
act(PLAN.play2[1], async () => { playing = false; });
/* 做完直接导出: More → Export…, the dialog open (s6.html puts the formats round it) */
act(PLAN.more - 0.15, async () => { TARGETS.more = await center(page.getByRole('button', { name: 'More' }).first()); await mouse.move(...TARGETS.more); });
act(PLAN.more, async () => { await mouse.click(...TARGETS.more); });
act(PLAN.menu - 0.12, async () => { TARGETS.menu = await center(page.getByText(/^Export…?$/).first()); await mouse.move(...TARGETS.menu); });
act(PLAN.menu, async () => { await mouse.click(...TARGETS.menu); });
act(PLAN.menu + 0.3, async () => { const b = await page.locator('[role=dialog]').first().boundingBox(); TARGETS.dialog = [b.x, b.y, b.width, b.height]; await mouse.move(1590, 990); });

/* the frames */
const N = Math.round((PLAN.duration - PLAN.rec0) * FPS);
for (let f = 0; f < N; f++) {
  const t = f / FPS;
  let settle = 0;
  for (const st of steps) if (st[0] <= t && !st.done) { st.done = true; st[1](); settle = 900; }
  for (const a of A) if (a.t <= t && !a.done) { a.done = true; await a.fn(); settle = Math.max(settle, 220); }
  if (playing) await seek('ArrowRight');
  await page.waitForTimeout(110 + settle);
  await page.screenshot({ path: `${FRAMES}/f${String(f).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 93 });
  if (f % 60 === 0) console.log('frame', f);
}
writeFileSync(join(ROOT, 'lib/s6-targets.json'), JSON.stringify({ about: 'Where the hand went in make/recordings/rec-s6.mjs, in css px of its 1600 × 1000 window: s6.html draws it there.', ...TARGETS }, null, 1));
console.log(JSON.stringify(TARGETS));
console.log(readFileSync(film, 'utf8').match(/overrides='[^']*'/g));
await app.quit();
execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(FPS), '-i', `${FRAMES}/f%04d.jpg`, '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-g', '1', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
  join(ROOT, 'assets/video/s6-ui.mp4')]);
console.log('done');
