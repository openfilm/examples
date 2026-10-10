"""Line 2 in film.html: the cast plate (assets/video/s2-cast.mp4) under its page (s2.html: names and title), and its
sounds (ids l2-*): every landing, Clawd's hops, the sticks popping up, the claps one by one, all together on 剪.
python3 make/sound/s2-sound.py (from the example's folder)"""
import re
from pathlib import Path
FILM = Path(__file__).parents[2] / 'film.html'
SFX = 'assets/audio/sfx/'
EV = []   # file, in, out, hit (film s), offset of the hit in the clip, volume
def ev(f, a, b, hit, off, v): EV.append((f, a, b, hit, off, v))
ev('tile-land', 0.26, 0.75, 6.04, 0.08, 0.62)                                     # Codex
ev('hop', 0.0, 0.6, 6.68, 0.0, 0.34); ev('hop', 0.0, 0.6, 6.96, 0.0, 0.48)        # Clawd's two hops
for t, v in ((7.70, 0.40), (7.86, 0.38), (8.02, 0.36), (8.34, 0.36), (8.50, 0.34)): ev('tile-land', 0.26, 0.75, t, 0.08, v)
ev('tile-land', 0.26, 0.75, 8.18, 0.08, 0.58); ev('impact', 0.0, 0.89, 8.18, 0.0, 0.14)   # OpenCode lands heavy
# Copilot and Cursor come down on a corner: the corner, then the foot as they fall flat (shot.py tile_pose)
for t, v in ((7.965, 0.15), (8.132, 0.15)): ev('tile-land', 0.26, 0.75, t, 0.08, v)
for t, v in ((9.43, 0.34), (9.50, 0.28), (9.57, 0.26), (9.64, 0.24)): ev('pop', 0.0, 0.35, t, 0.0, v)   # the sticks sprout
ev('tap', 0.33, 0.75, 9.58, 0.08, 0.30)                                             # the beret lands
for t in (9.97, 10.09, 10.21, 10.33, 10.45, 10.57, 10.69): ev('clapper', 0.245, 0.62, t, 0.08, 0.42)
ev('clapper', 0.245, 0.62, 10.89, 0.08, 0.8); ev('impact', 0.0, 0.89, 10.89, 0.0, 0.36)    # 剪: all together
ev('tile-land', 0.26, 0.75, 11.25, 0.08, 0.40)                                      # everybody back on the floor
# each tile's one bounce comes down again, softer (shot.py bounce: 0.30 m × its style's scale, G 30)
import math
for t, k in ((6.04, 1.0), (7.70, 1.0), (7.86, 0.7), (8.02, 0.6), (8.18, 0.55), (8.34, 0.6), (8.50, 1.0)):
    ev('tile-land', 0.26, 0.75, round(t + 0.06 + 2 * math.sqrt(2 * 30 * 0.30 * k) / 30, 3), 0.08, 0.16)
src = FILM.read_text()
# the events below are in the film's seconds with this line at 5.433; they move with its page clip
m = re.search(r'<iframe id="s2" src="s2.html" at="([\d.]+)"', src)
SHIFT = (float(m.group(1)) if m else 5.433) - 5.433
src = re.sub(r'  <audio id="l2-[^"]*"[^\n]*\n', '', src)
src = re.sub(r'  <(iframe|video) id="s2(-agents|-badges|-cast)?"[^\n]*\n', '', src)
src = re.sub(r'<section>\n</section>\n', '', src)
# the page with the other pages (right after line 1's recording), the plate under it (before s3's)
src = re.sub(r'(  <video id="s1-hero"[^\n]*\n)', lambda g: g.group(1) + f'  <iframe id="s2" src="s2.html" at="{5.433 + SHIFT:g}"></iframe>\n', src, count=1)
src = re.sub(r'(<section>\n)(  <video id="s3-(logo|mark)")', lambda g: g.group(1) + f'  <video id="s2-cast" src="assets/video/s2-cast.mp4" at="{5.433 + SHIFT:g}"></video>\n' + g.group(2), src, count=1)
items = []
for i, (f, a, b, hit, off, v) in enumerate(EV):
    at = round(hit - off + SHIFT, 3); items.append((at, at + b - a, f'  <audio id="l2-{f}-{i}" src="{SFX}{f}.mp3#t={a},{b}" at="{at}" volume="{v}"></audio>'))
items.sort(); tracks = []
for it in items:
    for tr in tracks:
        if tr[-1][1] <= it[0] - 0.005: tr.append(it); break
    else: tracks.append([it])
src = src.replace('</body>', ''.join('<section>\n' + ''.join(x[2] + '\n' for x in tr) + '</section>\n' for tr in tracks) + '</body>')
FILM.write_text(src)
print(len(items), 'sounds on', len(tracks), 'tracks')
