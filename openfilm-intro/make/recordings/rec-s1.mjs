// S1's OpenFilm: the desktop app (dark, its 1600 × 900 window at 2×, which is the film's 1920 × 1080 at 1.2×) with the
// winter trailer made in it as the chat shows (trailer.mjs: the footage and music attached, the agent writing each
// scene and the film for real, on a scripted model), its timeline's thumbnails all in. What line 1 rebuilds Premiere
// into, and what it lands on:
//   assets/video/hero-dark.mp4   the hand on the transport presses Play, and the trailer plays from its start as Studio
//                                plays it (real time, the window's own frames: CDP screencast), 2 s
//   make/blender/s1/tex/hero_land.png  its first frame at the film's size (post.py eases the plate's last frames into it)
//   make/blender/s1/tex/hero_land_nocursor.png  the same without the pointer, at 2× (the rebuild's OpenFilm side: sharp)
//   make/blender/s1/tex/hero_layout.json   where each of OpenFilm's pieces is in that frame (rebuild.py's targets)
// node make/recordings/rec-s1.mjs [work dir]   (from the example's folder)
import { execFileSync } from 'node:child_process';
import { copyFileSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { desktop } from './desktop.mjs';
import { scriptedAgent, useScriptedAgent } from './scripted-agent.mjs';
import { MAKE, askWithMedia, emptyProject, filmIn, thumbsIn } from './trailer.mjs';

const WORK = process.argv[2] || '/tmp/s1-rec';
const ROOT = new URL('../..', import.meta.url).pathname;     /* the example's folder */
const TEX = join(ROOT, 'make/blender/s1/tex');
const FPS = 30, N = 60, Z = 1.2;                         /* frames of the recording; css px → the film's px */

rmSync(WORK, { recursive: true, force: true }); mkdirSync(join(WORK, 'frames'), { recursive: true });
const model = await scriptedAgent({ turns: [MAKE] });
emptyProject(join(WORK, 'src'));
const app = await desktop({ dir: join(WORK, 'app'), size: [1600, 900, 420], projects: { 'winter-trip': join(WORK, 'src') } });
const project = join(WORK, 'app/projects/winter-trip');
await app.open('winter-trip');
const page = app.page, mouse = page.mouse;
await page.waitForTimeout(6000);
await page.getByRole('button', { name: 'Show inspector' }).click(); await page.waitForTimeout(600);

/* the conversation that made the trailer: the footage and the music attached, the agent at work */
await useScriptedAgent(page, page, model.baseUrl);
await askWithMedia(page, project, MAKE.ask);
for (let i = 0; i < 3600 && !model.stats.done; i++) await page.waitForTimeout(200);
await page.waitForTimeout(3000);
console.log('film', await filmIn(page), 'thumbnails', await thumbsIn(page, { least: 12000 }));

/* the trailer at its start, the timeline holding the keys, the pointer away */
await mouse.click(...(await page.evaluate(() => { const r = [...document.querySelectorAll('[aria-label="Drag the playhead"]')][0].getBoundingClientRect(); return [r.x + 1, r.y + 10]; })));
await page.keyboard.press('Home'); await page.waitForTimeout(800);
await mouse.move(1200, 860);
if (process.env.PROBE) { await page.screenshot({ path: join(WORK, 'probe.png') }); await app.quit(); await model.close(); process.exit(0); }

/* where OpenFilm's pieces are (rebuild.py's targets), in the film's px */
const R = await page.evaluate(() => {
  const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); return [r.x, r.y, r.x + r.width, r.y + r.height]; };
  const q = (s) => document.querySelector(s);
  const byText = (t, root = document) => [...root.querySelectorAll('*')].find((e) => e.children.length === 0 && e.textContent.trim() === t);
  const label = (l) => q(`[aria-label="${l}"]`);
  const up = (e, n) => { for (let i = 0; i < n && e; i++) e = e.parentElement; return e; };
  const stage = q('iframe');
  return { stage: box(stage), playhead: box(label('Drag the playhead')), play: box(label('Play')), undo: box(label('Undo (⌘Z)')), redo: box(label('Redo (⌘⇧Z)')),
    select: box(label('Select')), split: box(label('Split (⌘B)')), history: box(label('Edit history')), zoomOut: box(label('Zoom out (⌘-)')), fit: box(label('Fit to width')),
    layersHead: box(byText('Layers')), inspHead: box(byText('Inspector')),
    rows: [...document.querySelectorAll('*')].filter((e) => e.children.length === 0 && /^(title|INTO THE WHITE|−18°C|-18°C|61\.|14:32|REC ·|#vf|snow-drive\.mp4)/.test(e.textContent.trim()) && e.getBoundingClientRect().x < 300).map((e) => box(up(e, 1))),
    clips: [...document.querySelectorAll('*')].filter((e) => e.children.length === 0 && /^(title|track|days|km|end|snow-drive\.mp4|winter\.mp3)$/.test(e.textContent.trim()) && e.getBoundingClientRect().y > 700).map((e) => [e.textContent.trim(), box(e)]),
    heads: ['P1', 'V1', 'A1'].map((t) => box(byText(t))),
    w: innerWidth, h: innerHeight };
});
writeFileSync(join(WORK, 'dom.json'), JSON.stringify(R, null, 1));

/* the recording: the hand presses Play, and the trailer plays as Studio plays it — in real time, so taken from the
   window's own frames as it draws them (a screencast), each kept with its time; 30 a second picked from them after */
await page.evaluate(() => {
  const c = document.createElement('div'); c.id = 'rec-cursor';
  c.style.cssText = 'position:fixed;left:0;top:0;width:24px;height:24px;z-index:2147483647;pointer-events:none;filter:drop-shadow(0 1px 2px rgba(0,0,0,.5));opacity:0';
  c.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M4 2.5v17.2l4.6-4.3 2.9 6.6 3.1-1.4-2.9-6.4h6.4Z" fill="#000" stroke="#fff" stroke-width="1.5" stroke-linejoin="round"/></svg>';
  document.body.append(c);
});
const [px0, py0, px1, py1] = R.play;
await page.evaluate(([x, y]) => { const c = document.getElementById('rec-cursor'); c.style.transform = `translate(${x}px, ${y}px)`; }, [(px0 + px1) / 2 + 6, (py0 + py1) / 2 + 8]);
await page.screenshot({ path: join(WORK, 'land_nocursor.png') });
await page.evaluate(() => { document.getElementById('rec-cursor').style.opacity = '1'; });
await page.screenshot({ path: join(WORK, 'frames/f0000.png') });
const press = (down) => page.evaluate((d) => { const c = document.getElementById('rec-cursor'); c.style.transformOrigin = '4px 3px'; c.firstElementChild.style.transform = d ? 'scale(.86)' : ''; c.firstElementChild.style.transformOrigin = '4px 3px'; }, down);
const cdp = await page.context().newCDPSession(page);
const shots = [];                                                          /* [ms since the screencast began, jpeg] */
let t0 = null;
cdp.on('Page.screencastFrame', ({ data, sessionId }) => { const now = performance.now(); t0 ??= now; shots.push([now - t0, Buffer.from(data, 'base64')]); cdp.send('Page.screencastFrameAck', { sessionId }).catch(() => {}); });
await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 95, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
await page.waitForTimeout(300);
const tPress = performance.now();
await press(true); await page.waitForTimeout(90);
await page.mouse.click((px0 + px1) / 2, (py0 + py1) / 2);               /* Play, for real: Studio plays */
await press(false);
await page.waitForTimeout(2600);
await cdp.send('Page.stopScreencast');
await page.keyboard.press('Space');
await app.quit(); await model.close();
/* 30 frames a second from where the press began (a little before it, so the hand is seen to press) */
const from = tPress - t0 - 120;
for (let f = 0; f < N; f++) {
  const want = from + (f * 1000) / FPS;
  let pick = shots[0]; for (const s of shots) { if (s[0] <= want) pick = s; else break; }
  writeFileSync(join(WORK, `frames/c${String(f).padStart(4, '0')}.jpg`), pick[1]);
}
console.log('screencast', shots.length, 'frames over', Math.round(shots.at(-1)[0] - shots[0][0]), 'ms');

/* to the film's size */
const scale = (src, out) => execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', src, '-vf', 'scale=1920:1080:flags=lanczos', out]);
copyFileSync(join(WORK, 'land_nocursor.png'), join(TEX, 'hero_land_nocursor.png'));
scale(join(WORK, 'frames/f0000.png'), join(TEX, 'hero_land.png'));
execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(FPS), '-i', join(WORK, 'frames/c%04d.jpg'), '-vf', 'scale=1920:1080:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-g', '1', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', join(ROOT, 'assets/video/hero-dark.mp4')]);
console.log('done');
