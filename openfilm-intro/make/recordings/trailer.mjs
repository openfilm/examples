// The conversation that made the winter trailer (make/demo-projects/winter-trip) as the desktop app's chat shows it, for the
// recordings that have it on screen: the footage and the music attached to the first message through the composer's +
// (they go into the project's assets/upload), the agent writing each scene and the film for real (so the chat shows
// its tool calls and change cards), and what it says at the end.
import { cpSync, existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

export const WT = new URL('../demo-projects/winter-trip/', import.meta.url).pathname;
/* a file of the trailer as the agent writes it: its media where the chat put them (the project's assets/upload) */
const read = (p) => readFileSync(join(WT, p), 'utf8').replaceAll('assets/video/', 'assets/upload/').replaceAll('assets/audio/', 'assets/upload/');
export const MEDIA = [join(WT, 'assets/video/snow-drive.mp4'), join(WT, 'assets/audio/winter.mp3')];
/* the finished film, as the agent writes it: no one's changes on it yet */
export const FILM = read('film.html')
  .replace(/<iframe id="title" src="scenes\/title.html"[^>]*><\/iframe>/, '<iframe id="title" src="scenes/title.html"></iframe>');
const write = (path, content) => ({ tool: 'write', args: { path, content } });

export const MAKE = {
  ask: '给我们的冬季公路之旅剪一条 15 秒的预告片：标题要有动感，镜头跟着车走，卡在音乐节拍上。',
  steps: [
    { work: 6, thought: '先看手上的素材。', say: '先看素材：一段 4 分钟雪地里跟车的视频，一首 112 BPM 的配乐。', cmd: 'ls -l assets/upload' },
    { work: 48, thought: '片头怎么开。', say: '片头做成取景框：REC、时间码、坐标和温度，标题 INTO THE WHITE 从雪地里升起来。', cmd: write('scenes/title.html', read('scenes/title.html')) },
    { work: 36, thought: '第二段。', say: '第二段，路线图跟着车走。', cmd: write('scenes/track.html', read('scenes/track.html')) },
    { work: 28, thought: '第三段。', say: '第三段，三天两夜。', cmd: write('scenes/days.html', read('scenes/days.html')) },
    { work: 30, thought: '第四段。', say: '第四段，142 公里的里程数从雪里跳出来。', cmd: write('scenes/km.html', read('scenes/km.html')) },
    { work: 24, thought: '片尾。', say: '片尾停在标题上，停满一小节。', cmd: write('scenes/end.html', read('scenes/end.html')) },
    { work: 32, thought: '剪在一起。', say: '行车素材按拍子切成五段，每一刀都落在拍上，配乐铺满。', cmd: write('film.html', FILM) },
  ],
  work: 12,
  answer: '预告片做好了：\n\n- 片头 **INTO THE WHITE**，取景框和 REC 跟着出来\n- 路线图跟着车走，142 公里的里程从雪里跳出来\n- 五个镜头都卡在节拍上，片尾停满一小节\n\n哪里想改，直接在画面上点它就行。',
};

/* the project before the first message: the fonts the scenes use, and a film with nothing in it */
export function emptyProject(dir) {
  mkdirSync(dir, { recursive: true });
  cpSync(join(WT, 'fonts'), join(dir, 'fonts'), { recursive: true });
  writeFileSync(join(dir, 'film.html'), '<!doctype html>\n<html>\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=1920, height=1080">\n</head>\n<body>\n</body>\n</html>\n');
}

/* a message with the footage and the music attached: picked with the composer's + (its file input), in the project
   once they are, then the words, sent */
export async function askWithMedia(page, project, ask) {
  /* by path, as the system's file picker gives them (the footage is too big for Playwright to send over) */
  const cdp = await page.context().newCDPSession(page);
  const { result } = await cdp.send('Runtime.evaluate', { expression: "document.querySelector('input[type=file][multiple]')" });
  await cdp.send('DOM.setFileInputFiles', { files: MEDIA, objectId: result.objectId });
  await cdp.detach();
  const there = () => MEDIA.every((f) => { const p = join(project, 'assets/upload', f.split('/').pop()); return existsSync(p) && statSync(p).size === statSync(f).size; });
  for (let i = 0; i < 600 && !there(); i++) await page.waitForTimeout(100);
  await page.waitForTimeout(1500);
  await page.click('[data-prompt-editor]'); await page.keyboard.insertText(ask); await page.keyboard.press('Enter');
}

/* the film the agent wrote, whole in Studio: its scenes on the timeline (a page is on it once Studio has measured it;
   a window reloaded measures them again) */
export async function filmIn(page, names = ['title', 'track', 'days', 'km', 'end']) {
  const all = () => page.evaluate((ns) => ns.every((n) => [...document.querySelectorAll('*')].some((e) => e.children.length === 0 && e.textContent.trim() === n && e.getBoundingClientRect().y > innerHeight * 0.6)), names);
  for (let round = 0; round < 3; round++) {
    for (let i = 0; i < 60; i++) { if (await all()) return true; await page.waitForTimeout(500); }
    await page.reload(); await page.waitForTimeout(8000);
  }
  return all();
}

/* Studio shoots the timeline's thumbnails a while after the film changes: wait until every clip with a picture has
   its own, each loaded (a clip whose pictures are still coming has none, or one hidden) */
export async function thumbsIn(page, { least = 6000, most = 150000, nudge = true } = {}) {
  /* the zoom moved and back: the timeline asks for its shots again (one stuck on a video's black first frame from
     before the film settled is asked for anew) */
  if (nudge) {
    for (const name of [/^Zoom out/, /^Zoom in/]) { const b = page.getByRole('button', { name }); if (await b.count()) { await b.first().click(); await page.waitForTimeout(1200); } }
  }
  const check = () => page.evaluate(() => {
    /* a video's first thumbnails can be its first frame, black, until the clip's own come: those are not in yet */
    const light = (img) => { const c = document.createElement('canvas'); c.width = c.height = 8; const g = c.getContext('2d'); g.drawImage(img, 0, 0, 8, 8);
      const d = g.getImageData(0, 0, 8, 8).data; let s = 0; for (let k = 0; k < d.length; k += 4) s += d[k] + d[k + 1] + d[k + 2]; return s / (64 * 3 * 255); };
    const clips = [...document.querySelectorAll('[data-block-id]')].filter((b) => ['mg', 'video', 'still'].includes(b.dataset.blockKind ?? ''));
    const done = clips.filter((b) => { const imgs = [...b.querySelectorAll('img')]; return imgs.length > 0 && imgs.every((i) => i.complete && i.naturalWidth > 0 && i.style.visibility !== 'hidden' && (b.dataset.blockKind !== 'video' || light(i) > 0.05)); });
    return { clips: clips.length, done: done.length, missing: clips.filter((b) => !done.includes(b)).map((b) => b.dataset.blockTitle) };
  });
  const t0 = Date.now(); let c = null, still = 0;
  while (Date.now() - t0 < most) {
    c = await check();
    still = c.clips > 0 && c.done === c.clips ? still + 1 : 0;
    if (Date.now() - t0 > least && still >= 6) return c;
    await page.waitForTimeout(500);
  }
  return c;
}
