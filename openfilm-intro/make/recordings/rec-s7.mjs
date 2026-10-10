// S7's "the film you just watched was made with it": the desktop app (dark, 1600 × 1000 at 2×) with this very film open
// (this example, copied without make/ and Studio's own state), the conversation that made it in the chat (scripted-agent.mjs,
// as Claude Code), the timeline whole; the playhead on the last of S6, rewound to the start, then S1 from its first
// frame — assets/video/s7-ui.mp4 (3200 × 2000, 30 fps, 7 s), a frame for each frame of s7.html.
// node make/recordings/rec-s7.mjs [work dir]   (from the example's folder)
import { execFileSync } from 'node:child_process';
import { cpSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { desktop } from './desktop.mjs';
import { scriptedAgent, useScriptedAgent } from './scripted-agent.mjs';

const WORK = process.argv[2] || '/tmp/s7-rec';
const ROOT = new URL('../..', import.meta.url).pathname;     /* the example's folder */
const FPS = 30, N = 210;
const inout = (x) => (x < 0.5 ? 4 * x ** 3 : 1 - (-2 * x + 2) ** 3 / 2);
/* the film's frame on screen at s7.html's frame f, in whole frames (a time between two frames, rounded, lands on either:
   a frame twice, the next one skipped): S6's last frame, the one the film shows just before S7 (s7.html opens on it:
   the cut is seamless), held; rewound to the first in 2.3 s; S1 from it, a frame a frame */
const S7_AT = Number(/<iframe id="s7" src="s7.html" at="([\d.]+)"/.exec(readFileSync(join(ROOT, 'film.html'), 'utf8'))[1]);
const LAST = Math.ceil(S7_AT * FPS - 1e-6) - 1, HOLD = 14, PLAY = 83;
const FILM_FRAME = (f) => (f < HOLD ? LAST : f < PLAY ? Math.round(LAST * (1 - inout((f - HOLD) / (PLAY - HOLD)))) : f - PLAY);

/* the conversation that made it */
const TURNS = [
  { ask: '给 OpenFilm 做一条发布视频：三分钟以内，暗色，用真实界面讲清楚它能做什么。',
    steps: [{ work: 20, thought: '先定结构。', say: '七段，跟着一首 112 BPM 的配乐走：开场、Agent 们、Logo、能做什么、怎么改、怎么用、结尾。', cmd: 'ls' },
      { work: 28, thought: '开场。', say: 'S1 用 Blender 搭一个房间，把旧剪辑软件一块块拆成 OpenFilm。', cmd: 'ls assets/video' },
      { work: 24, thought: '真实界面。', say: 'S5、S6 用桌面端真录：点选、拖动、改色，框起来交给 Agent。', cmd: 'ls assets/audio/vo' }],
    work: 6, answer: '七段都剪好了，一共 1 分 42 秒。从头放一遍看看？' },
  { ask: 'S5 太急了，展示得不清楚，重做。',
    steps: [{ work: 18, thought: '放慢 S5。', say: '好，S5 重做：每句话分开，位置、大小、旋转、颜色每样都真改一遍，再框一块天空让 Agent 加一点阳光。', cmd: 'ls' }],
    work: 4, answer: '改好了：S5 现在 18 秒，每一步都看得清。' },
];

rmSync(WORK, { recursive: true, force: true }); mkdirSync(join(WORK, 'frames'), { recursive: true });
/* the project as it is, without what only made it (make/: Blender, the recorders) and Studio's caches */
const copy = join(WORK, 'film');
cpSync(ROOT, copy, { recursive: true, filter: (p) => !/\/(make|\.film|__pycache__)(\/|$)/.test(p.slice(ROOT.length - 1)) });
const model = await scriptedAgent({ turns: TURNS });
const app = await desktop({ dir: join(WORK, 'app'), projects: { 'openfilm-launch': copy } });
await app.open('openfilm-launch');
const page = app.page;
await page.waitForTimeout(20000);      /* every page probed, its length known */
await useScriptedAgent(page, page, model.baseUrl);
for (const [i, T] of TURNS.entries()) {
  await page.click('[data-prompt-editor]'); await page.keyboard.insertText(T.ask); await page.keyboard.press('Enter');
  for (let k = 0; k < 1200 && model.stats.turns <= i; k++) await page.waitForTimeout(200);
  await page.waitForTimeout(1500);
}
for (const n of ['Hide layers']) { const b = page.getByRole('button', { name: n }); if (await b.count()) { await b.first().click(); await page.waitForTimeout(300); } }
const subs = page.getByRole('button', { name: 'Subtitles', exact: true });   /* the picture without them */
if (await subs.count() && await subs.first().getAttribute('aria-pressed') === 'true') await subs.first().click();
const fit = page.getByRole('button', { name: 'Fit to width' });
if (await fit.isEnabled().catch(() => false)) await fit.click();
await page.mouse.move(1590, 990);
await page.waitForTimeout(800);
/* where the picture is (s7.html's PIC) */
const pic = await page.evaluate(() => { const r = document.querySelector('iframe').getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; });
writeFileSync(join(WORK, 'pic.json'), JSON.stringify(pic));
console.log('picture', JSON.stringify(pic));

/* the playhead to a frame: from the one it is on, a second at a time (⇧), then a frame at a time */
await page.locator('[role="slider"][aria-valuemax]').first().focus();
await page.keyboard.press('Home');
let cur = 0;
const goTo = async (frame) => {
  const key = frame < cur ? 'ArrowLeft' : 'ArrowRight', d = Math.abs(frame - cur);
  for (let i = 0; i < Math.floor(d / FPS); i++) await page.keyboard.press(`Shift+${key}`);
  for (let i = 0; i < d % FPS; i++) await page.keyboard.press(key);
  cur = frame;
};
await goTo(FILM_FRAME(0)); await page.waitForTimeout(4000);
for (let f = 0; f < N; f++) {
  const jump = Math.abs(FILM_FRAME(f) - cur);
  await goTo(FILM_FRAME(f));
  await page.waitForTimeout(jump > 3 ? 650 : 260);
  await page.screenshot({ path: join(WORK, `frames/f${String(f).padStart(4, '0')}.jpg`), type: 'jpeg', quality: 93 });
}
await app.quit(); await model.close();
execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', String(FPS), '-i', join(WORK, 'frames/f%04d.jpg'), '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-g', '1', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', join(ROOT, 'assets/video/s7-ui.mp4')]);
console.log('done');
