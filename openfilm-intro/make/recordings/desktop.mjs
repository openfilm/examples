// The desktop app for the explainer's screen recordings: the repository's app in its `bench` flavour (apps/desktop/
// bench/app.mjs: data, Studio home and projects in a throwaway folder, its own Studio on 4767), dark, driven over
// DevTools. desktop({ dir, projects: { name: folder }, size: [w, h, chat] }) → { page, open(name), quit }.
// OPENFILM_REPO=<a copy of the repository, its pages already built>: the app from there, as it was when copied — the
// recordings of one film keep one look while the repository's own app changes under them.
import { cpSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { REPO, SNAPSHOT } from './repo.mjs';
const { chromium } = await import(`${REPO}/packages/openfilm/node_modules/playwright-core/index.mjs`);
const { buildShell, launch, prepare, quit, waitForCdp } = await import(`${REPO}/apps/desktop/bench/app.mjs`);

export async function desktop({ dir, projects = {}, port = 9341, build = true, size = null }) {
  prepare(dir);
  /* another window size than the benchmark's */
  if (size) writeFileSync(join(dir, 'data/window.json'), JSON.stringify({ bounds: { x: 40, y: 40, width: size[0], height: size[1] }, chatWidth: size[2] ?? 420, chatOpen: true }));
  for (const [name, from] of Object.entries(projects)) cpSync(from, join(dir, 'projects', name), { recursive: true, filter: (p) => !p.includes('/.film/cache') });
  if (build && !SNAPSHOT) buildShell();
  const { child, cdp } = await launch({ dir, cdpPort: port, log: (l) => process.env.DESKTOP_LOG && process.stdout.write(l) });
  /* a recorder that fails leaves no app behind */
  for (const sig of ['exit', 'uncaughtException', 'unhandledRejection']) process.on(sig, (e) => { try { child.kill('SIGKILL'); } catch {} if (sig !== 'exit') { console.error(e); process.exit(1); } });
  await waitForCdp(cdp);
  const browser = await chromium.connectOverCDP(cdp);
  const ctx = browser.contexts()[0];
  let page = null;
  for (let i = 0; i < 100 && !page; i++) { page = ctx.pages().find((p) => !p.url().startsWith('devtools')) ?? null; if (!page) await new Promise((r) => setTimeout(r, 100)); }
  await page.evaluate(() => { try { localStorage.setItem('openfilm.theme', 'dark'); } catch {} document.documentElement.dataset.theme = 'dark'; });
  /* macOS draws the traffic lights over the page, so a screenshot has none: drawn where the app asks for them
     (src/main.mjs trafficLightPosition { x: 14, y: 10 }), centred on the top bar's icons */
  const lights = () => page.evaluate(() => {
    if (document.getElementById('rec-lights')) return;
    const d = document.createElement('div'); d.id = 'rec-lights';
    d.style.cssText = 'position:fixed;left:14px;top:10px;display:flex;gap:8px;z-index:2147483646;pointer-events:none';
    d.innerHTML = ['#ff5f57', '#febc2e', '#28c840'].map((c) => `<i style="width:12px;height:12px;border-radius:50%;background:${c};box-shadow:inset 0 0 0 .5px rgba(0,0,0,.25)"></i>`).join('');
    document.body.append(d);
  }).catch(() => {});
  await lights(); page.on('framenavigated', () => setTimeout(lights, 300));
  /* a film opened as `openfilm open` opens it: Studio shows it in the window */
  const open = async (name) => {
    const runFile = join(dir, 'home', 'run.json');
    for (let i = 0; i < 200 && !existsSync(runFile); i++) await new Promise((r) => setTimeout(r, 100));
    const run = JSON.parse(readFileSync(runFile, 'utf8'));
    const res = await fetch(`${run.origin}/api/open`, { method: 'POST', headers: { 'content-type': 'application/json', 'x-studio-key': run.key }, body: JSON.stringify({ path: join(dir, 'projects', name), fallback: 0 }) });
    if (!res.ok) throw new Error(`opening ${name}: ${res.status}`);
  };
  return { page, ctx, child, open, quit: async () => { await browser.close().catch(() => {}); await quit(child); } };
}
