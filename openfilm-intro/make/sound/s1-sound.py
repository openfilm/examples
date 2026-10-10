"""Line 1's picture and sound in film.html: the Blender plate (0 → 3.633 s), then the hero recording from the frame
after the one the plate lands on, and every sound effect on the moment it belongs to (ids l1-*).
Run from the example's folder:  python3 make/sound/s1-sound.py"""
import re
from pathlib import Path

FILM = Path(__file__).parents[2] / 'film.html'
PLATE_END = 109 / 30                      # frames 0..108
HERO_IN = 1 / 30                          # the plate's last frame is the recording's first (make/recordings/rec-s1.mjs: the desktop app, dark)
S1_END = 5.0                              # line 1 is five seconds: line 2 starts here
SFX = 'assets/audio/sfx/'
# file, in, out, at (the hit is at = when it lands), volume
EVENTS = [
    # 3:47, the cut playing back through the speakers; on 剪 (1.36) Premiere hangs and its audio stutters, then stops
    ('pr-playback', 0, 1.84, 0.0, 0.42),
    # 0.30: a message; the phone buzzes against the mat (its first pulse is 0.10 s into the file)
    ('phone-buzz', 0, 1.48, 0.20, 0.55),
    # 剪: Premiere hangs and the camera pushes in on it, rising into the pop on 我 (2.22)
    ('whoosh', 0, 0.29, 1.62, 0.20), ('riser', 0.9, 1.76, 1.48, 0.40),
    # 我: the wait cursor pops, the wave runs out from it, the light behind comes up
    ('pop', 0, 0.35, 2.22, 0.42), ('flash', 0, 1.6, 2.26, 0.26), ('shimmer', 0.3, 1.6, 2.32, 0.24),
    # the slats turn over, left to right
    *[('tick', 0, 0.12, round(2.56 + i * 0.068, 3), round(0.10 + 0.12 * min(1, i / 4) * (1 - max(0, i - 8) / 5), 3)) for i in range(12)],
    ('flip', 1.6, 2.2, 2.72, 0.24), ('flip', 1.6, 2.2, 3.00, 0.20),
    # 通用的视频: OpenFilm's pieces land, left to right (media, viewer, inspector, chat), all in place at 3.45
    ('tile-land', 0.26, 0.75, 2.94, 0.22), ('tile-land', 0.26, 0.75, 3.07, 0.22), ('tile-land', 0.26, 0.75, 3.19, 0.21), ('tile-land', 0.26, 0.75, 3.30, 0.20),
    ('impact', 0, 0.89, 3.46, 0.28),
    # Agent: in the recording, the pointer clicks Play (3.88) and the trailer starts
    ('tap', 0.33, 0.75, 3.71, 0.34), ('shimmer', 0.3, 1.6, 3.76, 0.20),        # the click on Play is hero 6.80 = film 3.80 (tap's hit is 0.08 into the clip)
]

src = FILM.read_text()
src = re.sub(r'  <audio id="l1-[^"]*"[^\n]*\n', '', src)
src = re.sub(r'<section>\n</section>\n', '', src)
# picture: the three.js page goes, the plate and the recording take its place on the first track
src = re.sub(r'  <iframe id="s1" src="s1.html"[^\n]*\n', '', src)
src = re.sub(r'  <video id="s1-(room|hero)"[^\n]*\n', '', src)
pic = (f'  <video id="s1-room" src="assets/video/s1-room.mp4" at="0"></video>\n'
       f'  <video id="s1-hero" src="assets/video/hero-dark.mp4#t={HERO_IN:.4f},{HERO_IN + S1_END - PLATE_END:.4f}" at="{PLATE_END:.4f}"></video>\n')
# before line 2's picture on the first picture track, whichever version of line 2 is there
anchor = re.search(r'\n  <(video id="s2-badges"|iframe id="s2")', src)
src = src[:anchor.start() + 1] + pic + src[anchor.start() + 1:]
# the chat is the recording's own now: no column laid over it
src = re.sub(r'<section>\n  <img id="s1-chat"[^\n]*\n</section>\n', '', src)
src = re.sub(r'  <img id="s1-chat"[^\n]*\n', '', src)
items = sorted((at, at + b - a, f'  <audio id="l1-{f}-{i}" src="{SFX}{f}.mp3#t={a},{b}" at="{at}" volume="{v}"></audio>') for i, (f, a, b, at, v) in enumerate(EVENTS))
tracks = []
for it in items:
    for tr in tracks:
        if tr[-1][1] <= it[0] - 0.005: tr.append(it); break
    else: tracks.append([it])
src = src.replace('</body>', ''.join('<section>\n' + ''.join(x[2] + '\n' for x in tr) + '</section>\n' for tr in tracks) + '</body>')
FILM.write_text(src)
print(len(items), 'sounds on', len(tracks), 'tracks')
