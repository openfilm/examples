# The film engine (`src/px`), adapted from pdoom-video

`src/px` is a port of the engine behind [pdoom-video](https://github.com/mexicat/pdoom-video) by mexicat
(MIT, see [LICENSE-pdoom-video.txt](LICENSE-pdoom-video.txt)): a WebGL2 renderer with linear-HDR bloom, heat-by-age
strokes, plotter type and audio-driven pulses. Its guide,
[docs/ENGINE.md](https://github.com/mexicat/pdoom-video/blob/main/docs/ENGINE.md), explains the scene API; this
file lists what differs here. The plates in `src/plates` and the edit in `src/plates/timeline.js` are this film's.

## Layout

- `src/px/*`: the engine, shared by every plate. `scene.js` says what a plate is given and returns.
- `src/plates/<id>.js`: one plate, default-exporting a `Scene` subclass. Helpers are in `src/plates/<id>-*.js`.
- `src/plates/timeline.js`: the edit, and which section each plate belongs to.
- `src/plates/handoff.js`: the cuts, and what must be on screen, and where, at each one.
- `src/plates/lyric.js`: word lookups by index (`wStart`, `wEnd`, `wText`, `wProg`, `charTimes`). Word indices are in
  `src/lyrics.js`.
- `src/section.js`: hosts the engine in a page, one section at a time.

## Differences from the reference

- `SCALE` follows the device pixel ratio: 1 at 1920×1080, 2 for a 4K render (`openfilm render --4k`).
- Fonts are loaded from `assets/fonts`:
  - `F.archivo(width 62–125, weight 300/500/700/900)`: variable Archivo, instanced at widths 62/75/87.5/100/112.5/125.
  - `F.mono(300–700)`: IBM Plex Mono.
  - `F.serif(400|600)`: Cormorant Garamond, italic.
  - One stroke font, Hershey Sans (`strokeText(text, 'sans')`).
- No opentype.js. Other ways to get text shapes: `textPoints` (raster samples), Canvas2D itself, and for outlines
  three's typeface JSON: `src/font-archivo-black.js` through `src/type3d.js` (`font('block')`).
- Audio (`this.ctx.audio`, from `assets/data/audio.json`):
  - `beats`, `downbeats`, `beatAt`, `timeOfBeat`, `nearestBeat`.
  - `env('rms'|'low'|'mid'|'high', t)`.
  - `hit('kick'|'snare'|'hat', t, hl)`, `events(kind, t0, t1)`.
  - `melAt(t)`: 48 mel bands, 0..1, low → high.
  - Every frame has `f.a.kick / snare / hat`, `f.beat`, `f.beatPhase`.
  - 122 BPM (beat 0.4918 s).
- Lyrics (`this.ctx.lyrics`) are built from `src/lyrics.js`.
- Palette (`palette.js`):
  - `signal #FF5A1F`, `ember #FF9A4D`, `blood #B8260E`; ink, bone, graphite and ash as in the reference.
  - `acid` is a **violet** `#8B5CFF`, only for "purple words" (46.7–50 s).
  - Only signal and ember may exceed ~0.85 linear. Bone type must stay crisp; the default bloom knee is 0.12.
- The engine can average motion-blur sub-frames itself (`Engine.render`'s `samples`), but the pages draw one sample
  per frame, so Studio plays them in real time; a render's motion blur is OpenFilm's (`openfilm render --blur`).

## Checking your work

- `npx openfilm look 12.4` draws one frame at full size; `npx openfilm look 12-16` a dense sheet of a stretch.
- A plate that throws renders dark red, and the error is in the page's console.
- A plate must be a **pure function of `f.t`**: no `Math.random`, no state carried from one frame to the next.
  - Flicker keyed to frames uses `frameIdx(t)`.
  - Particles are indexed by birth time (see `motifs.js sparkParticles`).
- Performance: keep a frame under about 40 ms; keep at most 2–3 Canvas2D layers per plate and precompute in `init()`.
