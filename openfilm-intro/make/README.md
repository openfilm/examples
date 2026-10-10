# How the intro was made

`film.html` and its pages play the film. This folder holds what made the media they play: the Blender scenes, the
recordings of the desktop app, the sound and the voice-over. Nothing here is needed to watch or edit the film; it is
here so you can make the shots again, change them, or learn from them.

Run every command below from the example's folder (`openfilm-intro/`), unless it says otherwise. Each script writes
its result where the film reads it (`assets/video/`, `assets/audio/`, `lib/`, `blender/*/out/track.json`), so a run
replaces what the film plays. Commit first, or work on a copy.

| Folder | What it makes |
| --- | --- |
| [`blender/`](blender) | Sections 1 – 3: `s1-room.mp4` (the room, Premiere coming apart), `s2-cast.mp4` (the agents on a stage), `s3-mark.mp4` (the OpenFilm mark) |
| [`recordings/`](recordings) | The desktop app on screen: `hero-dark.mp4` (end of section 1), `s5-ui.mp4`, `s6-ui.mp4`, `s7-ui.mp4` |
| [`demo-projects/`](demo-projects) | The two small films the recordings make in the app: a winter road-trip trailer and a perfume ad, VESPER |
| [`voice/`](voice) | The voice-over: the text of each line, and the script that asks ElevenLabs for it |
| [`sound/`](sound) | The sound design: one script a section that places the sound effects, the voice and the score in `film.html` |
| [`pages/`](pages) | `s4-prep.py`: the filmstrips and waveforms `s4.html` draws |
| [`script.md`](script.md), [`beats.md`](beats.md) | Early drafts of the script and the beat sheet, in Chinese |

The pages' comments still name these scripts by their old paths: `ui-rec/…` is `make/recordings/…`, and
`blender/s1/…` is `make/blender/s1/…` (except `blender/s2/out/track.json` and `blender/s3/out/track.json`, which stay
beside the pages).

## What you need

- **Blender 5.2** (the scenes were built and saved with 5.2.2 LTS). The scripts render with Cycles on an Apple
  silicon GPU (Metal). On another GPU, change `compute_device_type` in the `GPU=` line of each `make.sh` and in
  `cycles()` in `s1/shot.py` (`'OPTIX'`, `'CUDA'`, `'HIP'`), or set `S1_CPU=1`, `S2_CPU=1` or `S3_CPU=1` for the CPU.
  `make.sh` looks for Blender at `/Applications/Blender.app`; set `BLENDER=/path/to/blender` otherwise.
- **Python 3** with Pillow and NumPy (`pip install pillow numpy`), for the texture and layout scripts.
- **ffmpeg** and **ffprobe**.
- **Node.js 22** or newer.
- For section 1's Premiere screen: `npm install` in `make/`, then `npx playwright-core install chromium`.
- For the recordings: a checkout of [openfilm/openfilm](https://github.com/openfilm/openfilm) with `pnpm install` done,
  next to this repository (`../openfilm` from it), or anywhere with `OPENFILM_REPO=/path/to/openfilm`.
- For the voice: an [ElevenLabs](https://elevenlabs.io) API key of your own.
- macOS, for two things only: `blender/s1/tex.py` draws its notes and posters in fonts that come with macOS, and the
  recordings run the desktop app as it runs there.

## Sections 1 – 3: Blender

Every shot is built by a script, from nothing: `shot.py` makes the scene, keys every frame as a function of time,
and saves it as the `.blend` beside it (the `.blend` files here are those saves, so you can open one and look around).
`make.sh` saves the scene, renders it a frame at a time (one Blender process a frame, with a watchdog that retries a
frame that stalls) and encodes the frames into the film's video.

```sh
make/blender/s1/make.sh            # → assets/video/s1-room.mp4   109 frames, 256 samples
make/blender/s2/make.sh            # → assets/video/s2-cast.mp4   210 frames, 128 samples
make/blender/s3/make.sh            # → assets/video/s3-mark.mp4   138 frames, 128 samples
```

Each takes `[percent] [samples] [first] [last]` for a quicker pass, e.g. `make/blender/s2/make.sh 50 32`, and
`KEEP=1` keeps frames already rendered. To look at one frame:

```sh
cd make/blender/s3 && blender -b -P shot.py -- still 90 /tmp/s3-90.png 50 64      # frame, file, percent, samples
```

The renders go to `out/` in each shot's folder (ignored by git).

**s1, the room at 3:47 a.m.** `room.py` models the room and desk; `rebuild.py` takes Premiere apart, piece by
piece, and lands each piece where it belongs in OpenFilm; `post.py` is the finish (bloom, halation, a tone
shoulder, grain), run on the EXR frames, easing to nothing on the last frames so the cut to the app recording is
seamless. The screen is a replica of Premiere Pro made as a web page (`pr/pr.html`). `make.sh` renders it first, the
first time:

```sh
cd make/blender/s1/pr
node render.mjs frames out/frames      # the screen while it plays, 42 frames at 3840 × 2160
node render.mjs pieces out/pieces      # every element alone, so each can lift off the glass
cd .. && python3 pr/bg.py              # tex/pr_bg.png: Premiere's panels with nothing on them
```

`tex/` holds the room's pictures. `tex.py` draws most of them (the sticky notes, the phone's lock screen, the prints,
the washi tape, the posters from `assets/image/`); `coffee_ring.png` was drawn the same way, and `window_city.png` is
`assets/image/window-city.png`. `hero_land.png`, `hero_land_nocursor.png`, `plate.png` and `hero_layout.json` come
from the app recording (`recordings/rec-s1.mjs` and `s1-layout.py`, below): what Premiere is rebuilt into.

**s2, the agents.** The agents' marks, as enamel on black tiles, land on a bright studio stage (`bright.py`, shared
with s3); Clawd is built from voxels. It reads the marks from `blender/icons/`. Four are there; the OpenCode,
Devin and WorkBuddy marks are not (see [What is not here](#what-is-not-here)): put `opencode.svg`, `devin.svg` and
`workbuddy.svg` there, each a single-colour SVG, before you run it.

**s3, the mark.** The OpenFilm mark and name, from `icons/logo-light.svg` (`outline.py` turns them into outlines).

s2 and s3 also write where each mark is in every frame to `blender/s2/out/track.json` and `blender/s3/out/track.json`
(at the example's top level): `s2.html` and `s3.html` set the names and badges there.

## The recordings

Sections 5, 6 and 7, and the end of section 1, are the real desktop app, recorded. A recorder starts the app from
the openfilm checkout in its benchmark flavour (`apps/desktop/bench/app.mjs`): its data, its own Studio and its
projects all live in a throwaway folder, so your own Studio and projects are not touched. It drives the window over
DevTools and photographs it a frame at a time, so the result is smooth however slow the machine is. Then ffmpeg makes
the video.

The chat in the recordings is the app's own chat, fed by a **scripted agent** (`scripted-agent.mjs`): a small local
server that speaks the OpenAI Responses API, which the app connects to as a model with your own key. It says what the
script says, step by step, and runs real commands and file writes in the project, so the chat shows real tool calls
and the film really grows. It is styled as Claude Code (its mark, from the openfilm checkout). No model is called.

```sh
node make/recordings/rec-s1.mjs /tmp/s1-rec       # → assets/video/hero-dark.mp4, make/blender/s1/tex/hero_land*.png
python3 make/recordings/s1-layout.py /tmp/s1-rec  # → make/blender/s1/tex/hero_layout.json, plate.png
node make/recordings/rec-s5.mjs /tmp/s5-rec       # → assets/video/s5-ui.mp4
node make/recordings/rec-s6.mjs /tmp/s6-rec       # → assets/video/s6-ui.mp4, lib/s6-targets.json
node make/recordings/rec-s7.mjs /tmp/s7-rec       # → assets/video/s7-ui.mp4
```

The argument is a work folder; it is emptied first. `probe-s5.mjs` and `probe-s6.mjs` open the same windows without
recording, and print where things are and take pictures: what the recorders' coordinates were measured with.

- `rec-s1.mjs` and `rec-s5.mjs` make the winter trailer in the app (`trailer.mjs`: the footage and music attached to
  the first message, the agent writing each scene). `rec-s5.mjs` then edits it on the voice's words
  (`lib/s5-voice.json`): picks the title, moves, scales, turns and colours it, and boxes the sky for the agent, which
  adds a sun (`sun.html`).
- `rec-s6.mjs` makes VESPER, writing its `film.html` a piece at a time on the moments in `lib/s6-plan.json`, then
  drags a shot in, trims it and opens the export dialog. Nothing is exported.
- `rec-s7.mjs` opens this film itself in the app (copied without `make/`) and rewinds it.

**The demo projects' media are not included** (about 135 MB). Put your own there, with these names, before you
record; any footage works, the recordings only show it:

| File | What the film had |
| --- | --- |
| `demo-projects/winter-trip/assets/video/snow-drive.mp4` | 52 s, 1920 × 1080: driving behind a car on a snowy forest road |
| `demo-projects/winter-trip/assets/audio/winter.mp3` | 30 s of music at 112 BPM |
| `demo-projects/vesper/assets/video/vesper-a.mp4`, `vesper-b.mp4`, `vesper-c.mp4` | about 5 s each, 1920 × 1080: a perfume bottle; in the third it lights up and lilies open |
| `demo-projects/vesper/assets/audio/vesper.mp3` | 12 s of music |

VESPER's Chinese font is the example's own `fonts/NotoSansSC.ttf`; `rec-s6.mjs` copies it in.

## The voice-over

Seven lines, one ElevenLabs request each, model `eleven_v4`, voice `i2gDhHnLj4CvKBpf3gPR` (from the ElevenLabs voice
library: add it to your voices, or use any other voice id), no voice settings. The text of each line is in
`voice/lines.json`.

```sh
export ELEVENLABS_API_KEY=…                         # your own key
node make/voice/tts.mjs l4                          # → assets/audio/vo/l4-new.mp3, l4-new.vtt
python3 make/voice/vtt-lines.py assets/audio/vo/l4-new.vtt
```

`tts.mjs` saves the audio and its timing, a cue a sentence with a time before every character. `vtt-lines.py` cuts
that into subtitle lines a viewer reads at a glance, keeping each character's time. The pages time their moves on
those characters, so after a new take, point the film and the pages at it: the `<audio>` in `film.html` and the
`.vtt` the page reads (`s4.html`'s `VTT`, `lib/s5-voice.json`, `lib/s6-voice.json`, `s7.html`). A new take speaks at
another pace, so the pages' moves land on the new words by themselves, but the cuts in `lib/s5-voice.json` and
`lib/s6-voice.json` may need moving. The l7 take in the film joins two requests (see `lines.json`).

Any voice works: with a service connected to OpenFilm, `npx openfilm get tts` makes the voice-over too.

## The sound

The score and the sound effects were generated with `openfilm get music` and `openfilm get sfx` (a sound service
connected to OpenFilm). `sound/prompts.json` has the prompts that were kept: the score's, and those of a few effects.

Each section has a script that writes its sounds into `film.html`: it removes that section's sounds (by their `id`s,
`l1-…` to `l7-…`) and places each effect so its hit lands on its moment (a landing, a click, a word), at the volume
it should have, on as few tracks as they need.

```sh
python3 make/sound/s1-sound.py     # and s2 … s7
```

The scripts give the film's sound exactly. Two small differences to know: the s2 script puts section 2's sounds on
tracks of their own, where the film has them packed onto fewer, and the film has one voice clip (`l5-g`) at 38.864 s
where the s5 script writes 38.8643 s. The s1, s2 and s3 scripts also place their sections' videos and pages.

## Section 4's data

`s4.html` is a page; it plays the films in `assets/video/showcase-hd/`. `pages/s4-prep.py` takes the frames for its
filmstrips (`lib/s4/thumbs/`) and the loudness of the voice and the score for its waveforms (`lib/s4/peaks.json`).
It reads `assets/audio/vo/l4-v2.mp3`, the take the waveform was drawn from, which is not in the example: change it to
`l4-v4.mp3` (the take the film plays) to run it.

## How it comes together

`film.html` is the cut. The first track holds the pages (`s2.html` … `s7.html`); under them, the rendered shots and
recordings play as video (`s1-room.mp4`, then `hero-dark.mp4`, `s2-cast.mp4`, `s3-mark.mp4`); the pages draw on top
of them or play the recordings inside their own frames (`s5.html`, `s6.html`, `s7.html`). Below are the voice, the
score and the effects, as the sound scripts placed them. The film's settings (60 fps, the subtitles' style) were set
in Studio and are in `.film/settings.json` and `.film/subtitles.json`.

## What is not here

- **Renders and caches**: frames, EXRs, logs, the replica's renders (`pr/out/`), Studio's own state. The scripts make
  them again.
- **The OpenCode, Devin and WorkBuddy marks** for section 2: their license could not be confirmed, so they are left
  out. The other four marks are from [Simple Icons](https://simpleicons.org).
- **The demo projects' footage and music** (above).
- **Earlier takes that are not in the film**: the first Blender versions of the opening, the agents and the logo; a
  three.js version of the opening; a recorded version of section 4; the first `film.html` writer. The film was made
  over many versions; this folder keeps what made the one you watch.
