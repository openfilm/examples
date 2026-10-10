// The voice-over, from ElevenLabs with your own key: the audio, and its character timing as a karaoke WebVTT (a cue
// for each sentence, a time tag before every character after the first), which the pages read their timing from.
// The model and the voice are the film's (lines.json); no voice settings are sent, so the voice's own defaults apply.
//   ELEVENLABS_API_KEY=… node make/voice/tts.mjs <line>                     a line of lines.json (l1 … l7)
//   ELEVENLABS_API_KEY=… node make/voice/tts.mjs <voice id> <text> <out>    any text
// → <out>.mp3 and <out>.vtt (a line's out is assets/audio/vo/<line>-new, so the take in the film stays until you
// replace it). Then make the VTT into subtitle lines: python3 make/voice/vtt-lines.py <out>.vtt
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname } from 'node:path';

const LINES = JSON.parse(readFileSync(new URL('./lines.json', import.meta.url), 'utf8'));
const args = process.argv.slice(2);
let voice, text, out, model = LINES.model;
if (args.length === 1 && LINES.lines[args[0]]) {
  ({ text } = LINES.lines[args[0]]); voice = LINES.voice; out = `assets/audio/vo/${args[0]}-new`;
} else if (args.length === 3) {
  [voice, text, out] = args;
} else {
  console.error('node make/voice/tts.mjs <line> | <voice id> <text> <out without extension>');
  process.exit(2);
}
const key = process.env.ELEVENLABS_API_KEY;
if (!key) { console.error('Set ELEVENLABS_API_KEY to your ElevenLabs API key.'); process.exit(2); }

// https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps
const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(voice)}/with-timestamps?output_format=mp3_44100_128`, {
  method: 'POST',
  headers: { 'xi-api-key': key, 'content-type': 'application/json' },
  body: JSON.stringify({ text, model_id: model }),
  signal: AbortSignal.timeout(180_000),
});
if (!res.ok) { console.error('ElevenLabs:', res.status, (await res.text()).slice(0, 300)); process.exit(1); }
const d = await res.json();
mkdirSync(dirname(out), { recursive: true });
writeFileSync(`${out}.mp3`, Buffer.from(d.audio_base64, 'base64'));

const a = d.alignment ?? d.normalized_alignment;
const chars = a.characters, st = a.character_start_times_seconds, en = a.character_end_times_seconds;
const ts = (s) => `${String(Math.floor(s / 3600)).padStart(2, '0')}:${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}:${(s % 60).toFixed(3).padStart(6, '0')}`;
/* one cue a sentence */
const cues = []; let cur = [];
chars.forEach((c, i) => { cur.push([c, st[i], en[i]]); if ('。！？.!?'.includes(c)) { cues.push(cur); cur = []; } });
if (cur.length) cues.push(cur);
const lines = ['WEBVTT', ''];
for (let cue of cues) {
  const kept = cue.filter((x) => x[0].trim()); if (kept.length) cue = kept;
  const body = cue[0][0] + cue.slice(1).map(([c, s]) => `<${ts(s)}>${c}`).join('');
  lines.push(`${ts(cue[0][1])} --> ${ts(cue.at(-1)[2])}`, body, '');
}
writeFileSync(`${out}.vtt`, lines.join('\n'));
console.log(JSON.stringify({ out, dur: en.at(-1), chars: chars.length }));
