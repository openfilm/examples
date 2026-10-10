// A look at S5's window before recording it: the trailer's project as the agent leaves it (no chat), the title picked,
// the inspector scrolled, the colour picker opened, the footage picked in Layers — where each thing is, and pictures.
// node make/recordings/probe-s5.mjs <work dir>   (from the example's folder)
import { cpSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { desktop } from './desktop.mjs';
import { FILM, MEDIA, emptyProject, WT } from './trailer.mjs';
import { readFileSync } from 'node:fs';

const WORK = process.argv[2];
rmSync(WORK, { recursive: true, force: true }); mkdirSync(WORK, { recursive: true });
const src = join(WORK, 'src'); emptyProject(src);
mkdirSync(join(src, 'assets/upload'), { recursive: true }); mkdirSync(join(src, 'scenes'), { recursive: true });
for (const f of MEDIA) cpSync(f, join(src, 'assets/upload', f.split('/').pop()));
for (const s of ['title', 'track', 'days', 'km', 'end']) writeFileSync(join(src, `scenes/${s}.html`), readFileSync(join(WT, `scenes/${s}.html`), 'utf8').replaceAll('assets/video/', 'assets/upload/').replaceAll('assets/audio/', 'assets/upload/'));
writeFileSync(join(src, 'film.html'), FILM);
const app = await desktop({ dir: join(WORK, 'app'), projects: { 'winter-trip': src }, port: 9351 });
await app.open('winter-trip');
const page = app.page, mouse = page.mouse;
await page.waitForTimeout(7000);
await page.getByRole('button', { name: 'Show inspector' }).click(); await page.waitForTimeout(800);
const shot = (n) => page.screenshot({ path: join(WORK, `${n}.png`) });
const ST = await page.evaluate(() => { const r = document.querySelector('iframe').getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height, k: r.width / 1920 }; });
console.log('stage', JSON.stringify(ST));
const stage = (x, y) => [ST.x + x * ST.k, ST.y + y * ST.k];
/* the trailer to where its title is up */
await page.focus('[role="slider"][aria-valuemax]'); await page.keyboard.press('Home');
for (let i = 0; i < 35; i++) await page.keyboard.press('ArrowRight');
await page.waitForTimeout(1500);
await mouse.click(...stage(860, 852)); await page.waitForTimeout(1200); await shot('1-title');
const rects = () => page.evaluate(() => {
  const r = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; };
  const sections = Object.fromEntries([...document.querySelectorAll('[data-section]')].map((e) => [e.getAttribute('data-section'), r(e)]));
  const sc = [...document.querySelectorAll('*')].filter((e) => e.scrollHeight > e.clientHeight + 4 && getComputedStyle(e).overflowY !== 'visible' && e.getBoundingClientRect().x > 860 && e.getBoundingClientRect().x < 1200).map((e) => ({ r: r(e), top: e.scrollTop, h: e.scrollHeight }));
  return { sections, swatch: r(document.querySelector('button[aria-label="Color"]')), scrollers: sc };
});
console.log('after title click', JSON.stringify(await rects()));
/* the inspector scrolled so the swatch is at y 400 */
await mouse.move(1030, 450);
const sw = (await rects()).swatch; let left = sw[1] + sw[3] / 2 - 400;
while (Math.abs(left) > 2) { const d = Math.sign(left) * Math.min(40, Math.abs(left)); await mouse.wheel(0, d); left -= d; await page.waitForTimeout(30); }
await page.waitForTimeout(600); await shot('2-scrolled');
console.log('scrolled', JSON.stringify(await rects()));
const sw2 = (await rects()).swatch; await mouse.click(sw2[0] + sw2[2] / 2, sw2[1] + sw2[3] / 2); await page.waitForTimeout(800); await shot('3-picker');
console.log('picker', JSON.stringify(await page.evaluate(() => {
  const r = (e) => { if (!e) return null; const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; };
  const dlg = [...document.querySelectorAll('[role="dialog"], [data-radix-popper-content-wrapper]')].map(r);
  return { dialogs: dlg, gold: r(document.querySelector('button[aria-label="#ffd166"]')), presets: [...document.querySelectorAll('button[aria-label^="#"]')].map((e) => [e.getAttribute('aria-label'), ...r(e)]) };
})));
await page.keyboard.press('Escape'); await page.waitForTimeout(400);
/* the footage, picked in Layers */
const row = await page.evaluate(() => { const e = [...document.querySelectorAll('*')].find((x) => x.children.length === 0 && x.textContent.trim() === 'snow-drive.mp4' && x.getBoundingClientRect().x < 250); if (!e) return null; const b = e.getBoundingClientRect(); return [b.x + b.width / 2, b.y + b.height / 2]; });
console.log('layers row', JSON.stringify(row));
if (row) { await mouse.click(row[0], row[1]); await page.waitForTimeout(1200); await shot('4-footage'); console.log('after footage', JSON.stringify(await rects())); }
const head = await page.evaluate(() => [...document.querySelectorAll('*')].filter((e) => e.children.length === 0 && e.getBoundingClientRect().x > 880 && e.getBoundingClientRect().x < 1180 && e.getBoundingClientRect().y < 130 && e.textContent.trim()).map((e) => e.textContent.trim()).slice(0, 8));
console.log('inspector head', JSON.stringify(head));
await app.quit();
