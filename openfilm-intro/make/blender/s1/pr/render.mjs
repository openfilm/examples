/* Renders the Premiere replica (pr.html) for Blender, at 2× (3840 × 2160):
     node render.mjs still <t> <out.png>        one frame
     node render.mjs frames <dir>               the screen while it is worked on: 0 → FREEZE, 30 fps
     node render.mjs pieces <dir>               every element alone at FREEZE, transparent around it, plus pieces.json
   The pieces put back together give the frozen frame exactly: that is what lets the old app come apart for real. */
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { chromium } from 'playwright-core';      /* make/package.json: npm install in make/, then npx playwright-core install chromium */

const [mode, a, b] = process.argv.slice(2);
const here = dirname(fileURLToPath(import.meta.url));
const browser = await chromium.launch({ args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
await page.goto(pathToFileURL(resolve(here, 'pr.html')).href);
await page.evaluate(async () => { await document.fonts.ready; await Promise.all([...document.images].map((i) => i.decode().catch(() => {}))); });

const shot = (path, opts = {}) => page.screenshot({ path, type: 'png', ...opts });
if (mode === 'still') {
  await page.evaluate((t) => window.pr.setState(t), Number(a));
  await shot(b);
} else if (mode === 'frames') {
  mkdirSync(a, { recursive: true });
  const n = Math.round((await page.evaluate(() => window.pr.FREEZE)) * 30);
  for (let f = 0; f <= n; f++) {
    await page.evaluate((t) => window.pr.setState(t), f / 30);
    await shot(resolve(a, `${String(f + 1).padStart(4, '0')}.png`));
  }
  console.log(n + 1, 'frames');
} else if (mode === 'pieces') {
  mkdirSync(a, { recursive: true });
  await page.evaluate(() => window.pr.setState(window.pr.FREEZE, { noCursor: true }));
  await shot(resolve(a, '_frozen.png'));
  const list = await page.evaluate(() => [...document.querySelectorAll('[data-piece]')].filter((e) => e.offsetParent !== null || e.id === 'mac').map((e) => {
    const r = e.getBoundingClientRect(); const par = e.parentElement.closest('[data-piece]');
    return { id: e.dataset.piece, r: [r.left, r.top, r.right, r.bottom], parent: par ? par.dataset.piece : null };
  }).filter((p) => p.r[2] - p.r[0] > 1 && p.r[3] - p.r[1] > 1 && p.id !== 'cursor'));
  for (const p of list) {
    await page.evaluate((id) => { document.documentElement.classList.add('iso'); document.body.classList.add('iso'); document.querySelectorAll('.iso-on').forEach((e) => e.classList.remove('iso-on')); document.querySelector(`[data-piece="${id}"]`).classList.add('iso-on'); }, p.id);
    /* a pixel of margin all round, for the antialiased edge */
    const x = Math.max(0, Math.floor(p.r[0]) - 1), y = Math.max(0, Math.floor(p.r[1]) - 1);
    const w = Math.min(1920, Math.ceil(p.r[2]) + 1) - x, h = Math.min(1080, Math.ceil(p.r[3]) + 1) - y;
    p.box = [x, y, x + w, y + h];
    await shot(resolve(a, `${p.id}.png`), { omitBackground: true, clip: { x, y, width: w, height: h } });
  }
  await page.evaluate(() => { document.body.classList.remove('iso'); document.documentElement.classList.remove('iso'); });
  writeFileSync(resolve(a, 'pieces.json'), JSON.stringify(list, null, 1));
  writeFileSync(resolve(a, 'meta.json'), JSON.stringify({ cursor: await page.evaluate(() => window.pr.playCentre()) }));
  console.log(list.length, 'pieces');
}
await browser.close();
