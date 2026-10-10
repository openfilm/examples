// A model for the desktop app's own-key agent that says what a script says (after apps/desktop/bench/fake-model.mjs):
// the OpenAI Responses API on 127.0.0.1, each step a thought, a paragraph and one shell command, then the answer. The
// chat in the recordings is the app's own, fed through its real path; only the words are written here.
// scriptedAgent({ turns: [{ steps: [{ thought, say, cmd, work }], answer, work }], pace, clock, cps }) → { baseUrl, stats, close }; { steps, answer } is one
// turn; a step's `cmd` is a shell command, or { tool, args } for a tool of the agent's own (write, edit…); `work` is
// the seconds it takes before it answers, as a real model would (the turn's "Worked …" is real time), before a
// recording only. With `clock` (the recording's own seconds), text streams at `cps` characters a recorded second, whatever the
// real time a frame takes to photograph.
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { REPO } from './repo.mjs';

const sleep = (ms) => new Promise((done) => setTimeout(done, ms));
let ids = 0;
const id = (p) => `${p}_${(ids += 1).toString(36)}`;
/* the pause before the next piece of streamed text: in real time, or (with a clock) until the recording has moved on */
const after = async (clock, since, chars, cps, pace) => {
  if (!clock || since == null || clock() == null) return sleep(pace);      /* no clock yet: real time */
  while (clock() < since + chars / cps) await sleep(15);
};
const shellCall = (tools, cmd) => {
  const names = new Set((tools ?? []).map((t) => t.name ?? t.type));
  if (cmd && typeof cmd === 'object') return { name: cmd.tool, arguments: JSON.stringify(cmd.args) };   /* a tool by name: { tool, args } */
  if (names.has('bash')) return { name: 'bash', arguments: JSON.stringify({ command: cmd }) };
  if (names.has('exec_command')) return { name: 'exec_command', arguments: JSON.stringify({ cmd }) };
  if (names.has('shell_command')) return { name: 'shell_command', arguments: JSON.stringify({ command: cmd }) };
  return { name: 'shell', arguments: JSON.stringify({ command: ['bash', '-lc', cmd] }) };
};
/* where the conversation is: the latest of the person's messages it has (each turn knows its message by `ask`; the
   app also sends context as the user's, so only those count), and how many commands since have run */
const textOf = (it) => (typeof it?.content === 'string' ? it.content : (it?.content ?? []).map((c) => c?.text ?? '').join(''));
const where = (input, turns) => {
  const items = Array.isArray(input) ? input : [];
  let turn = 0, at = -1;
  items.forEach((it, i) => { if (it?.role !== 'user') return; const k = turns.findIndex((T) => T.ask && textOf(it).includes(T.ask.slice(0, 12))); if (k >= 0) { turn = k; at = i; } });
  return [turn, items.slice(at + 1).filter((it) => it?.type === 'function_call_output').length];
};
export function scriptedAgent({ turns, steps, answer, chunk = 6, pace = 12, clock = null, cps = 60 }) {
  turns = turns ?? [{ steps, answer }];
  const stats = { requests: 0, steps: 0, done: false, turns: 0 };
  const server = createServer(async (req, res) => {
    let body = ''; for await (const c of req) body += c;
    let json = {}; try { json = body ? JSON.parse(body) : {}; } catch { /* not JSON */ }
    stats.requests += 1;
    if (req.method === 'GET' && /\/models\/?$/.test(req.url ?? '')) { res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify({ object: 'list', data: [{ id: 'script', object: 'model' }] })); return; }
    if (!/\/responses\/?$/.test(req.url ?? '')) { res.writeHead(404); res.end('{}'); return; }
    if (json.stream !== true) {
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ id: id('resp'), object: 'response', status: 'completed', output: [{ type: 'message', id: id('msg'), role: 'assistant', content: [{ type: 'output_text', text: 'Red' }] }], usage: { input_tokens: 10, output_tokens: 1, total_tokens: 11 } }));
      return;
    }
    res.writeHead(200, { 'content-type': 'text/event-stream', 'cache-control': 'no-cache', connection: 'keep-alive' });
    let seq = 0;
    const send = (type, data) => res.write(`event: ${type}\ndata: ${JSON.stringify({ type, sequence_number: (seq += 1), ...data })}\n\n`);
    const rid = id('resp'); send('response.created', { response: { id: rid, object: 'response', status: 'in_progress', output: [] } });
    const [turn, step] = where(json.input, turns), T = turns[Math.min(turn, turns.length - 1)], last = step >= T.steps.length, s = T.steps[step] ?? {};
    /* the time it works on this step; a recording's own turn keeps the recording's time instead */
    const work = last ? T.work : s.work;
    if (work && (!clock || clock() == null)) await sleep(work * 1000);
    const output = []; let index = 0;
    const thought = last ? '整理改了什么。' : s.thought;
    if (thought) {
      const rsId = id('rs');
      send('response.output_item.added', { output_index: index, item: { type: 'reasoning', id: rsId, summary: [] } });
      send('response.reasoning_summary_part.added', { item_id: rsId, output_index: index, summary_index: 0, part: { type: 'summary_text', text: '' } });
      const t0 = clock?.() ?? 0;
      for (let i = 0; i < thought.length; i += chunk) { send('response.reasoning_summary_text.delta', { item_id: rsId, output_index: index, summary_index: 0, delta: thought.slice(i, i + chunk) }); await after(clock, t0, i + chunk, cps * 2, pace); }
      send('response.reasoning_summary_text.done', { item_id: rsId, output_index: index, summary_index: 0, text: thought });
      const r = { type: 'reasoning', id: rsId, summary: [{ type: 'summary_text', text: thought }] };
      send('response.output_item.done', { output_index: index, item: r }); output.push(r); index += 1;
    }
    const text = last ? T.answer : s.say;
    if (text) {
      const mId = id('msg');
      send('response.output_item.added', { output_index: index, item: { type: 'message', id: mId, role: 'assistant', status: 'in_progress', content: [] } });
      send('response.content_part.added', { item_id: mId, output_index: index, content_index: 0, part: { type: 'output_text', text: '', annotations: [] } });
      const t0 = clock?.() ?? 0;
      for (let i = 0; i < text.length; i += chunk) { if (res.destroyed) return; send('response.output_text.delta', { item_id: mId, output_index: index, content_index: 0, delta: text.slice(i, i + chunk) }); await after(clock, t0, i + chunk, cps, pace); }
      send('response.output_text.done', { item_id: mId, output_index: index, content_index: 0, text });
      const m = { type: 'message', id: mId, role: 'assistant', status: 'completed', content: [{ type: 'output_text', text, annotations: [] }] };
      send('response.output_item.done', { output_index: index, item: m }); output.push(m); index += 1;
    }
    if (!last) {
      const call = { type: 'function_call', id: id('fc'), call_id: id('call'), status: 'completed', ...shellCall(json.tools, s.cmd ?? 'ls') };
      send('response.output_item.added', { output_index: index, item: { ...call, arguments: '' } });
      send('response.function_call_arguments.done', { item_id: call.id, output_index: index, arguments: call.arguments });
      send('response.output_item.done', { output_index: index, item: call }); output.push(call); stats.steps += 1;
    } else { stats.turns = turn + 1; stats.done = turn + 1 >= turns.length; }
    send('response.completed', { response: { id: rid, object: 'response', status: 'completed', output, usage: { input_tokens: 1000, input_tokens_details: { cached_tokens: 0 }, output_tokens: 200, output_tokens_details: { reasoning_tokens: 20 }, total_tokens: 1200 } } });
    res.end();
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => {
    const { port } = server.address();
    resolve({ baseUrl: `http://127.0.0.1:${port}/v1`, stats, close: () => new Promise((done) => server.close(() => done())) });
  }));
}

/** The app's own-key agent on this model, the only one its chat offers (bench/scenarios.mjs useFakeAgent). */
const CLAUDE_PATH = readFileSync(`${REPO}/apps/desktop/chat/src/components/AgentIcons.tsx`, 'utf8').match(/claude: '([^']+)'/)[1];
const CLAUDE_SVG = `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='${CLAUDE_PATH}'/></svg>`)}")`;
/* the agent the recordings show is Claude Code (as the person runs it): its mark where the own-key agent's key and
   the OpenFilm mark would be, its effort after the model, and its name on hover. Styles only: nothing in the page changes */
const AS_CLAUDE = `
  button:has(> span > span > svg.lucide-key-round) svg.lucide-key-round, span[title="Your own key"] > svg { visibility: hidden; }
  span:has(> svg.lucide-key-round), span[title="Your own key"] { position: relative; }
  span:has(> svg.lucide-key-round)::before, span[title="Your own key"]::before { content: ''; position: absolute; inset: 0; margin: auto; width: 13px; height: 13px;
    background: currentColor; -webkit-mask: ${CLAUDE_SVG} center / contain no-repeat; }
  span[title="Your own key"]::before { width: 12px; height: 12px; }
  span:has(> svg.lucide-key-round) + span.truncate::after { content: ' High'; color: var(--text-muted); }`;
export async function asClaudeCode(page) {
  const css = AS_CLAUDE;
  await page.addStyleTag({ content: css }).catch(() => {});
}
export async function useScriptedAgent(page, chat, baseUrl) {
  const done = await page.evaluate((u) => window.openfilmHost.agents.configureByok({ format: 'responses', baseUrl: u, model: 'Opus 5.5', key: 'script-key' }), baseUrl);
  if (!done?.ok) throw new Error(`setting up the agent: ${done?.error ?? 'no answer'}`);
  for (const a of ['codex', 'claude', 'openfilm']) await page.evaluate((x) => window.openfilmHost.agents.setShown(x, false), a);
  for (let i = 0; i < 240; i++) { if (await page.evaluate(async () => (await window.openfilmHost.agents.list()).find((a) => a.id === 'byok')?.status === 'ready')) break; await sleep(500); }
  await chat.evaluate(() => localStorage.setItem('openfilm.local-agents.v2', JSON.stringify({ picked: 'byok', prefs: {}, options: {} })));
  await chat.reload();
  for (let i = 0; i < 120; i++) { if (await chat.evaluate(() => Boolean(document.querySelector('[data-prompt-editor]'))).catch(() => false)) break; await sleep(500); }
  await asClaudeCode(chat);
}
