# Credits

## Voice, music and sound

The voice-over in `assets/audio/vo/` was made with [ElevenLabs](https://elevenlabs.io) by the OpenFilm contributors
for this film; the word timings in the `.vtt` files beside it come from those generations. The score and the outro in
`assets/audio/music/` and the sound effects in `assets/audio/sfx/` are by the OpenFilm contributors too. Like the rest
of this example, they are under the MIT license: use them, change them, put them in your own films.

## Pictures and footage

The footage in `assets/video/`, the stills in `assets/image/` and the frames in `lib/` were made by the OpenFilm
contributors for this film (rendered, generated, or recorded from the OpenFilm app), and are under the MIT license
like the rest of this example.

## Fonts

All in `fonts/`. The license text and copyright notices are in [fonts/OFL.txt](fonts/OFL.txt).

| Font | Files | License |
| --- | --- | --- |
| [Geist](https://github.com/vercel/geist-font) © 2024 The Geist Project Authors | `Geist.ttf` | SIL Open Font License 1.1 |
| [Geist Mono](https://github.com/vercel/geist-font) © 2024 The Geist Project Authors | `GeistMono.ttf` | SIL Open Font License 1.1 |
| [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) © 2020 The JetBrains Mono Project Authors | `JetBrainsMono.ttf` | SIL Open Font License 1.1 |
| [Noto Sans SC](https://github.com/notofonts/noto-cjk) © 2014-2021 Adobe, Reserved Font Name "Source" | `NotoSansSC.ttf` | SIL Open Font License 1.1 |

`s7.html` also asks for Hannotate SC and Kaiti SC from the system (they come with macOS); they are not included.

## The sources in make/

The scripts, the Blender scenes, the textures in `make/blender/s1/tex/`, the Premiere replica and its pictures
(`make/blender/s1/pr/`), and the demo projects' pages were made by the OpenFilm contributors for this film, under the
MIT license like the rest of this example. The textures and the replica's pictures are drawn by the scripts, rendered
from the app, or cut from footage made for the film.

- `make/blender/s1/post.py` follows the post-processing of
  [mexicat/pdoom-video](https://github.com/mexicat/pdoom-video) (MIT).
- `make/blender/icons/codex.svg`, `copilot.svg`, `cursor.svg` and `gemini.svg` are the OpenAI, GitHub Copilot, Cursor
  and Google Gemini icons from [Simple Icons](https://simpleicons.org) (CC0 1.0). The marks themselves belong to
  their owners. `logo-light.svg` is the OpenFilm logo (see Marks below).
- The fonts in `make/demo-projects/` (Inter, JetBrains Mono, Bodoni Moda) are under the SIL Open Font License 1.1;
  their notices and the license are in [make/demo-projects/OFL.txt](make/demo-projects/OFL.txt).
- `make/voice/` holds the text the voice-over was generated from with ElevenLabs; `make/sound/prompts.json` holds the
  prompts the score and some of the sound effects were generated from.
- `make/blender/s1/pr/pr.html` draws a likeness of Adobe Premiere Pro's interface, to show the kind of editor the film
  talks about. Premiere Pro is a trademark of Adobe; this example is not affiliated with or endorsed by Adobe.

## Marks

The OpenFilm mark and wordmark are OpenFilm's logo; see
[TRADEMARK.md](https://github.com/openfilm/openfilm/blob/main/TRADEMARK.md) for how they may be used. The marks of
the agents in section 2 (`assets/video/s2-cast.mp4`) and the Claude mark in the app recordings belong to their owners
and are shown to name their products. Clawd, Claude Code's mascot, which section 2 builds in Blender, and the marks
in `make/blender/icons/` belong to their owners too.
