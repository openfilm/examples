// A look at S6's window before recording it: VESPER as the agent leaves it (no chat), what the top bar and the right
// side offer, the assets panel opened, an asset dragged into the picture — where each thing is, and pictures.
// node make/recordings/probe-s6.mjs <work dir> [asset file to add]   (from the example's folder)
import { cpSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { desktop } from './desktop.mjs';

const WORK = process.argv[2], EXTRA = process.argv[3];
const ROOT = new URL('../..', import.meta.url).pathname, SRC = join(ROOT, 'make/demo-projects/vesper');
rmSync(WORK, { recursive: true, force: true }); mkdirSync(WORK, { recursive: true });
const src = join(WORK, 'src');
cpSync(SRC, src, { recursive: true, filter: (p) => !p.includes('/.film') });
if (EXTRA) { mkdirSync(join(src, 'assets/image'), { recursive: true }); cpSync(EXTRA, join(src, 'assets/image', EXTRA.split('/').pop())); }
const PLATES = ['  <video id="vesper-a" src="assets/video/vesper-a.mp4#t=0.7,5.15" at="0"></video>', '  <video id="vesper-b" src="assets/video/vesper-b.mp4#t=0.6,4.7" at="4.45"></video>'];
const MUSIC = ['  <audio id="vesper" src="assets/audio/vesper.mp3#t=0,11.95" at="0"></audio>'];
const PAGES = ['  <iframe id="title" src="scenes/title.html" at="0"></iframe>', '  <iframe id="line" src="scenes/line.html" at="4.45"></iframe>', '  <iframe id="end" src="scenes/end.html" at="8.55"></iframe>'];
writeFileSync(join(src, 'film.html'), `<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=1920, height=1080">\n</head>\n<body>\n${[PAGES, PLATES, MUSIC].map((t) => `<section>\n${t.join('\n')}\n</section>\n`).join('')}</body>\n</html>\n`);
const app = await desktop({ dir: join(WORK, 'app'), projects: { VESPER: src }, port: 9351 });
await app.open('VESPER');
const page = app.page, mouse = page.mouse;
await page.waitForTimeout(6000);
await page.evaluate(() => window.openfilmDesktop?.setChatOpen?.(false));
await page.waitForTimeout(1200);
const insp = page.getByRole('button', { name: 'Show inspector' });
if (await insp.count()) { await insp.first().click(); await page.waitForTimeout(800); }
const shot = (n) => page.screenshot({ path: join(WORK, `${n}.png`) });
const hideLayers = page.getByRole('button', { name: 'Hide layers' }).first();
if (await hideLayers.count()) { await hideLayers.click(); await page.waitForTimeout(500); }
await page.evaluate(() => window.openfilmDesktop?.setAssetsOpen?.(true)); await page.waitForTimeout(1500);
const buttons = () => page.evaluate(() => [...document.querySelectorAll('button, [role=tab], [role=button]')].map((b) => {
  const r = b.getBoundingClientRect(); return [b.getAttribute('aria-label') || b.getAttribute('title') || b.textContent.trim().slice(0, 30), Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
}).filter((b) => b[3] > 0 && (b[2] < 60 || b[1] > 1150)));
await shot('1-start');
console.log('top and right buttons', JSON.stringify(await buttons()));
const ST = await page.evaluate(() => { const r = document.querySelector('iframe').getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; });
console.log('stage', JSON.stringify(ST));
/* the assets: from the Layout menu */
await page.getByRole('button', { name: 'Layout' }).first().click(); await page.waitForTimeout(700);
await shot('2-layout');
console.log('menu', JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('[role=menuitem], [role=menuitemcheckbox], [role=option]')].map((e) => { const r = e.getBoundingClientRect(); return [e.textContent.trim(), Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }))));
const item = page.getByRole('menuitemcheckbox', { name: /assets/i }).or(page.getByRole('menuitem', { name: /assets/i })).first();
if (await item.count()) { await item.click(); } else { await page.keyboard.press('Escape'); await page.evaluate(() => window.openfilmDesktop?.setAssetsOpen?.(true)); }
await page.waitForTimeout(1500);
await shot('3-assets');
const items = await page.evaluate(() => [...document.querySelectorAll('[draggable=true]')].map((e) => {
  const r = e.getBoundingClientRect(); return [e.textContent.trim().slice(0, 40), Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
}).filter((x) => x[3] > 0));
console.log('draggables', JSON.stringify(items));
console.log('tracks', JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('[data-block-id]')].map((b) => { const r = b.getBoundingClientRect(); return [b.dataset.blockId, b.dataset.blockKind, Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }))));
/* the video folder opened, the new shot dragged onto the footage's track at the second shot */
const folder = items.find((x) => /video$/.test(x[0]));
if (folder) { await mouse.dblclick(folder[1] + folder[3] / 2, folder[2] + 40); await page.waitForTimeout(1200); await shot('4-folder'); }
const items2 = await page.evaluate(() => [...document.querySelectorAll('[draggable=true]')].map((e) => {
  const r = e.getBoundingClientRect(); return [e.textContent.trim().slice(0, 40), Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
}).filter((x) => x[3] > 0));
console.log('in the folder', JSON.stringify(items2));
const c = items2.find((x) => /vesper-c/.test(x[0]));
const vb = await page.evaluate(() => { const b = [...document.querySelectorAll('[data-block-id]')].find((e) => e.dataset.blockId.startsWith('line')); const r = b.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; });
console.log('vesper-b block', JSON.stringify(vb), 'item', JSON.stringify(c));
if (c && vb) {
  const from = [c[1] + c[3] / 2, c[2] + 40], to = [vb[0] + 4, vb[1] + vb[3] / 2];
  await mouse.move(...from); await mouse.down();
  for (let i = 1; i <= 30; i++) { await mouse.move(from[0] + (to[0] - from[0]) * i / 30, from[1] + (to[1] - from[1]) * i / 30); await page.waitForTimeout(30); }
  await page.waitForTimeout(300); await shot('5-dragging'); await mouse.up(); await page.waitForTimeout(1800); await shot('6-dropped');
  console.log('film after drop:\n' + readFileSync(join(WORK, 'app/projects/VESPER/film.html'), 'utf8').split('\n').filter((l) => /<(video|iframe|audio)|section/.test(l)).join('\n'));
  console.log('blocks', JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('[data-block-id]')].map((b) => { const r = b.getBoundingClientRect(); return [b.dataset.blockId, Math.round(r.x), Math.round(r.y), Math.round(r.width)]; }))));
}
writeFileSync(join(WORK, 'film-before.html'), readFileSync(join(WORK, 'app/projects/VESPER/film.html'), 'utf8'));
await app.quit();
