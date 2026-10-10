// S5's screen recording: the desktop app (dark, its 1600 × 1000 window at 2×) with the winter trailer made in it as the
// chat shows (trailer.mjs: the footage and music attached, the agent writing each scene and the film for real), then
// driven a frame at a time on S5's voice as s5.html lays it out (lib/s5-voice.json) — assets/video/s5-ui.mp4 (3200 ×
// 2000, 30 fps, every frame a key frame so s5.html can seek it frame by frame). On its lines: the title clicked in the
// picture on 点; moved, made bigger by its corner, turned by the corner's outside, each on its word; coloured from the
// picker under its swatch; more of its properties on the right, the inspector rolled down to them (a shadow); a shape
// (the red rule) stretched; the footage picked in Layers and its brightness pulled down; then a ⌘ box round the sky
// handed to the agent with "这里加点阳光" — it answers at once and puts a low sun there, in that box only, for real, on
// a track of its own; the hand off the window.
// node make/recordings/rec-s5.mjs [work dir]   (from the example's folder)
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { desktop } from './desktop.mjs';
import { scriptedAgent, useScriptedAgent } from './scripted-agent.mjs';
import { MAKE, askWithMedia, emptyProject, filmIn, thumbsIn } from './trailer.mjs';
import { VOICE, said } from './s5-voice.mjs';

const WORK = process.argv[2] || '/tmp/s5-rec';
const FRAMES = join(WORK, 'frames');
const FPS = 30, DUR = VOICE.duration;
const T = { click: said('点一下'), pos: said('位置'), size: said('大小'), rot: said('旋转'), color: said('颜色'), more: said('更多属性'),
  not: said('不只是'), text: said('文字'), shape: said('图形'), video: said('视频'), vague: said('说不清'), box: said('框起来'), tell: said('告诉'), fix: said('它来改') };

rmSync(WORK, { recursive: true, force: true }); mkdirSync(FRAMES, { recursive: true });
/* the sun, where the person boxed the sky (film px): the page, and its clip on a track of its own over the picture */
const SKY = { x: 760, y: 20, w: 420, h: 250 };
const SUN = readFileSync(new URL('./sun.html', import.meta.url), 'utf8');
const WRITE_SUN = { tool: 'write', args: { path: 'scenes/sun.html', content: SUN } };
const ADD_SUN = { tool: 'edit', args: { path: 'film.html', edits: [{ oldText: '<body>\n<section>\n',
  newText: `<body>\n<section>\n  <iframe id="sun" src="scenes/sun.html" style="left: ${SKY.x}px; top: ${SKY.y}px"></iframe>\n</section>\n<section>\n` }] } };
const ASK = '这里加点阳光';
const TURNS = [MAKE, { ask: ASK,
  steps: [{ thought: '看框住的地方。', say: '好，在这片天上加一轮冬日的太阳。', cmd: WRITE_SUN }, { thought: '放到最上面一层。', say: '', cmd: ADD_SUN }],
  answer: '加好了。' }];
let FRAME_T = null;                          /* the recording's own clock (none before it starts): the agent streams on it */
const model = await scriptedAgent({ turns: TURNS, clock: () => FRAME_T, cps: 46 });
emptyProject(join(WORK, 'src'));
const app = await desktop({ dir: join(WORK, 'app'), projects: { 'winter-trip': join(WORK, 'src') } });
const project = join(WORK, 'app/projects/winter-trip');
const film = join(project, 'film.html');
await app.open('winter-trip');
const page = app.page, mouse = page.mouse;
await page.waitForTimeout(6000);
await page.getByRole('button', { name: 'Show inspector' }).click();          /* open from the start: the picture keeps its place */
await page.waitForTimeout(800);
/* the conversation that made the trailer */
await useScriptedAgent(page, page, model.baseUrl);
await askWithMedia(page, project, MAKE.ask);
for (let k = 0; k < 3600 && model.stats.turns < 1; k++) await page.waitForTimeout(200);
await page.waitForTimeout(3000);
console.log('film', await filmIn(page), 'thumbnails', JSON.stringify(await thumbsIn(page, { least: 12000 })));
await page.mouse.click(700, 120); await page.waitForTimeout(300);           /* out of the chat: Studio has the keys */

/* where things are, in css px of the window: the stage (the picture), its scale */
const ST = await page.evaluate(() => { const r = document.querySelector('iframe').getBoundingClientRect(); return { x: r.x, y: r.y, k: r.width / 1920 }; });
const stage = (x, y) => [ST.x + x * ST.k, ST.y + y * ST.k];
console.log('stage', JSON.stringify(ST));

/* the hand: drawn into the page so it is photographed with it, the cursor the page would show where it is */
await page.evaluate(() => {
  const c = document.createElement('div'); c.id = 'rec-cursor';
  c.style.cssText = 'position:fixed;left:0;top:0;width:24px;height:24px;z-index:2147483647;pointer-events:none;filter:drop-shadow(0 1px 2px rgba(0,0,0,.5))';
  document.body.append(c);
});
const CURSORS = {
  arrow: [3, 2, '<path d="M4 2.5v17.2l4.6-4.3 2.9 6.6 3.1-1.4-2.9-6.4h6.4Z" fill="#000" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/>'],
  nwse: [12, 12, '<path d="M5 5h6.5L9 7.5l7.5 7.5L19 12.5V19h-6.5l2.5-2.5L7.5 9 5 11.5Z" fill="#000" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/>'],
  ew: [12, 12, '<path d="M2 12l5-5v3h10V7l5 5-5 5v-3H7v3Z" fill="#000" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/>'],
  text: [12, 12, '<path d="M9 4h6M9 20h6M12 4v16" stroke="#000" stroke-width="3.2" stroke-linecap="round"/><path d="M9 4h6M9 20h6M12 4v16" stroke="#fff" stroke-width="1.4" stroke-linecap="round"/>'],
  pointer: [8, 2, '<path d="M9 2.8c0-1 1.8-1 1.8 0v7.4l.3-2.3c.1-1 1.8-.9 1.8.1l-.1 2.4.4-1.6c.2-1 1.8-.8 1.7.2v2l.4-1c.3-.9 1.7-.6 1.6.4l-.2 4.4c-.2 2.7-1.2 4.2-2.6 5.2H9.6c-1-.7-2.6-2.7-3.6-4.3l-1.6-2.6c-.6-1 .7-1.9 1.5-1.1L9 14.2Z" fill="#fff" stroke="#000" stroke-width="1.2" stroke-linejoin="round"/>'],
};
let cx = 640, cy = 640, shown = 0;
async function drawCursor() {
  await page.evaluate(([x, y, o, C]) => {
    const el = document.elementFromPoint(x, y), cur = el ? getComputedStyle(el).cursor : 'default';
    const c = document.getElementById('rec-cursor');
    /* Studio's own cursor (a turn, at the frame's angle): url("…") x y — the address read whole, quotes and all (an
       SVG's own parentheses are inside it) */
    const own = /url\("((?:[^"\\]|\\.)*)"\)\s*(-?\d+)?\s*(-?\d+)?/.exec(cur);
    if (own) {
      if (c.dataset.src !== own[1]) { c.innerHTML = `<img src="${own[1].replace(/"/g, '&quot;')}" width="24" height="24" style="display:block">`; c.dataset.src = own[1]; }
      c.style.transform = `translate(${x - (+own[2] || 12)}px, ${y - (+own[3] || 12)}px)`; c.style.opacity = String(o);
      return;
    }
    c.dataset.src = '';
    const kind = /nwse|nesw|se-resize|nw-resize/.test(cur) ? 'nwse' : /ew-resize|col-resize/.test(cur) ? 'ew' : cur === 'text' ? 'text' : cur === 'pointer' ? 'pointer' : 'arrow';
    const [hx, hy, svg] = C[kind];
    c.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24">${svg}</svg>`;
    c.style.transform = `translate(${x - hx}px, ${y - hy}px)`; c.style.opacity = String(o);
  }, [cx, cy, shown, CURSORS]);
}

/* the script: from t, what the hand does. A move glides from where the hand is to a point (or a point found then);
   every press and release is where the hand is */
const ease = (k) => (k < 0.5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2);
const S = [];
const move = (t0, t1, to) => S.push({ t0, t1, kind: 'move', to });
const act = (t, fn) => S.push({ t0: t, t1: t, kind: 'act', fn });
/* a roll of the wheel over what is under the hand, spread over the frames from t0 to t1 (eased): `by` says how far, once it starts */
const scroll = (t0, t1, by) => S.push({ t0, t1, kind: 'scroll', by });
const box = async (loc) => { const b = await loc.boundingBox(); return [b.x + b.width / 2, b.y + b.height / 2]; };
const typeIn = (t0, chars, per) => [...chars].forEach((ch, i) => act(t0 + i * per, async () => { await page.keyboard.type(ch); }));
const press = (t) => act(t, async () => { await mouse.down(); });
const release = (t) => act(t, async () => { await mouse.up(); });
const click = (t) => act(t, async () => { await mouse.down(); await mouse.up(); });
const named = (name) => async () => box(page.getByRole('button', { name, exact: true }).first());
const handle = (want) => async () => (await page.evaluate((want) => {
  const c = [...document.querySelectorAll('[data-layer-kind]')].filter((e) => e.getAttribute('data-layer-kind') === want.kind && (!want.at || e.getAttribute('data-layer-handle') === want.at))
    .map((e) => { const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; });
  return c.sort((a, b) => b[0] + b[1] - a[0] - a[1])[0];
}, want)) || [cx, cy];
/* the timeline's playhead, a frame a step: its own slider keeps the keys */
const seek = async (key) => { await page.focus('[role="slider"][aria-valuemax]'); await page.keyboard.press(key); };

/* 做完哪里不满意？ the trailer to where its title is up (frame 35), the hand comes in from below the picture */
act(0, async () => { await seek('Home'); for (let i = 0; i < 35; i++) await seek('ArrowRight'); });
act(0.85, async () => { shown = 1; });
/* 点一下就能改: to the title, nothing else on the way (its outline lights up under the hand), and the click on 点 */
move(0.9, T.click - 0.1, stage(860, 852));
click(T.click);
/* 位置、大小、旋转: each on its word, quick: dragged up over the dark of the trees; bigger by its corner; turned by the
   corner's outside, where the hand becomes Studio's turn cursor */
press(T.pos - 0.02);
move(T.pos + 0.02, T.pos + 0.52, stage(800, 852 - 470));
release(T.pos + 0.55);
move(T.pos + 0.6, T.size - 0.06, handle({ kind: 'scale', at: 'se' }));
press(T.size - 0.03);
move(T.size + 0.01, T.size + 0.42, async () => [cx + 22, cy + 5]);
release(T.size + 0.45);
move(T.size + 0.5, T.rot - 0.08, async () => { const [x, y] = await handle({ kind: 'rotate', at: 'ne' })(); return [x + 2, y - 2]; });
press(T.rot - 0.05);
move(T.rot - 0.02, T.rot + 0.4, async () => [cx - 3, cy - 16]);
release(T.rot + 0.43);
/* 颜色: onto the inspector, rolled up a little (the picker opens under its swatch, clear of the title), the swatch,
   a gold from the picker's own colours, shut */
const swatchAt = async (y) => { const b = await page.locator('button[aria-label="Color"]').first().boundingBox(); return b ? b.y + b.height / 2 - y : 0; };
move(T.rot + 0.48, T.color - 0.2, [1030, 470]);
scroll(T.color - 0.18, T.color + 0.1, () => swatchAt(400));
move(T.color + 0.12, T.color + 0.25, async () => box(page.locator('button[aria-label="Color"]').first()));
click(T.color + 0.28);
move(T.color + 0.36, T.color + 0.66, async () => box(page.locator('button[aria-label="#ffd166"]').first()));
click(T.color + 0.7);
act(T.color + 0.95, async () => { await page.keyboard.press('Escape'); });
/* 更多属性，都在右边: the inspector rolled down past the mask, appearance and adjustments to the effects: a shadow */
const sectionAt = (id, y) => async () => ((await page.evaluate((s) => document.querySelector(`[data-section=${s}]`)?.getBoundingClientRect().y ?? null, id)) ?? y) - y;
move(T.color + 1.0, T.more - 0.02, [1030, 520]);
scroll(T.more, T.more + 1.1, sectionAt('effects', 170));
move(T.more + 1.16, T.more + 1.4, named('Add an effect'));
click(T.more + 1.44);
move(T.more + 1.52, T.more + 1.76, named('Shadow'));
click(T.more + 1.8);
/* 不只是文字，图形: the red rule under the title, clicked in the picture on 文字, stretched by its end on 图形 */
act(T.text - 0.55, async () => { await page.keyboard.press('Escape'); });
move(T.text - 0.5, T.text - 0.06, stage(300, 983));
click(T.text);
move(T.text + 0.08, T.shape - 0.06, handle({ kind: 'stretch', at: 'e' }));
press(T.shape - 0.03);
move(T.shape + 0.01, T.shape + 0.42, async () => [cx + 110, cy]);
release(T.shape + 0.45);
/* 视频也一样: the footage picked in Layers on 视频; its brightness pulled well down on the right (dusk: the gold title
   stands out) — a change no one can miss */
const layerRow = (name) => async () => (await page.evaluate((n) => {
  const e = [...document.querySelectorAll('*')].find((x) => x.children.length === 0 && x.textContent.trim() === n && x.getBoundingClientRect().x < 250);
  if (!e) return null; const b = e.getBoundingClientRect(); return [b.x + Math.min(b.width / 2, 40), b.y + b.height / 2];
}, name)) || [cx, cy];
move(T.shape + 0.5, T.video - 0.05, layerRow('snow-drive.mp4'));
click(T.video);
move(T.video + 0.08, T.video + 0.3, [1030, 560]);
scroll(T.video + 0.32, T.video + 0.6, sectionAt('adjust', 560));
move(T.video + 0.62, T.video + 0.78, async () => box(page.getByLabel('Brightness', { exact: true }).first()));
press(T.video + 0.8);
move(T.video + 0.83, T.video + 1.15, async () => [cx - 26, cy]);
release(T.video + 1.18);
/* 说不清的地方，框起来告诉 Agent: a box drawn with ⌘ round the sky on 框起来 goes to the chat, and a word with it */
act(T.vague - 0.1, async () => { await page.keyboard.press('Escape'); });
move(T.vague, T.box - 0.08, stage(SKY.x, SKY.y));
act(T.box - 0.02, async () => { await page.keyboard.down('Meta'); await mouse.down(); });
move(T.box + 0.02, T.tell + 0.04, stage(SKY.x + SKY.w, SKY.y + SKY.h));
act(T.tell + 0.07, async () => { await mouse.up(); await page.keyboard.up('Meta'); });
typeIn(T.tell + 0.24, ASK, 0.075);
act(T.tell + 0.8, async () => { await page.keyboard.press('Enter'); });
move(T.tell + 0.9, T.tell + 1.3, [1120, 640]);
/* 它来改: it answers and puts the sun there; the hand away, the window whole: the picture, the new track, the answer */
act(T.tell + 1.32, async () => { shown = 0; });
let sunAt = null;

/* the frames */
const N = Math.round(DUR * FPS);
let seg = null, from = null, target = null;
for (let f = 0; f < N; f++) {
  const t = f / FPS; FRAME_T = t;
  for (const s of S) if (s.kind === 'act' && s.t0 <= t && !s.done) { s.done = true; await s.fn(); }
  if (sunAt == null && readFileSync(film, 'utf8').includes('id="sun"')) { sunAt = t; console.log('sun written at', t.toFixed(2)); }
  for (const s of S) if (s.kind === 'scroll' && s.t0 <= t && t <= s.t1 + 0.5 / FPS) {
    if (s.total == null) { s.total = await s.by(); s.rolled = 0; }
    const d = Math.round(s.total * ease(Math.min(1, (t - s.t0) / Math.max(1e-3, s.t1 - s.t0))) - s.rolled);
    if (d) { await mouse.wheel(0, d); s.rolled += d; }
  }
  const m = S.find((s) => s.kind === 'move' && s.t0 <= t && t <= s.t1 + 0.5 / FPS);
  if (m) {
    if (seg !== m) { seg = m; from = [cx, cy]; target = typeof m.to === 'function' ? (await page.waitForTimeout(200), await m.to()) : m.to; }   /* what it finds: once the page has drawn what the last click opened */
    const k = ease(Math.min(1, (t - m.t0) / Math.max(1e-3, m.t1 - m.t0)));
    cx = from[0] + (target[0] - from[0]) * k; cy = from[1] + (target[1] - from[1]) * k;
    await mouse.move(cx, cy);
  }
  await drawCursor();
  await page.waitForTimeout(90);
  await page.screenshot({ path: `${FRAMES}/f${String(f).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 93 });
  if (f % 60 === 0) console.log('frame', f);
}
console.log(readFileSync(film, 'utf8').match(/overrides='[^']*'|id="sun"[^>]*>/g));
await app.quit(); await model.close();
execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(FPS), '-i', `${FRAMES}/f%04d.jpg`, '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-g', '1', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
  new URL('../../assets/video/s5-ui.mp4', import.meta.url).pathname]);
console.log('done', JSON.stringify(T), 'sun', sunAt);
