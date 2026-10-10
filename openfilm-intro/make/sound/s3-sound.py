"""Line 3 in film.html: the mark's plate (assets/video/s3-mark.mp4) under its page (s3.html: the badges and the
address), and its sounds (ids l3-*): the clips rushing in and snapping onto the track, the playhead's fall and its hit,
a tick as each letter stands up, the badges snapping in, and the dive into the cut.
python3 make/sound/s3-sound.py (from the example's folder)"""
import re
from pathlib import Path
FILM = Path(__file__).parents[2] / 'film.html'
SFX = 'assets/audio/sfx/'
OLD = ('riser-2', 'snap', 'shimmer-2', 'pop', 'logo-hit', 'whip-9', 'whip-10', 'pop-6', 'pop-7', 'snap-2')   # the last version's, 12.3–15.4 s
EV = []   # file, in, out, hit (film s), offset of the hit in the clip, volume
def ev(f, a, b, hit, off, v): EV.append((f, a, b, hit, off, v))
ev('whoosh', 0, 0.29, 12.44, 0.03, 0.20); ev('snap', 0, 0.4, 12.78, 0.07, 0.26)        # the first clip, in and onto the track (它)
ev('whoosh', 0, 0.29, 12.62, 0.03, 0.16); ev('snap', 0, 0.4, 12.97, 0.07, 0.24)        # the second (叫)
ev('riser', 0.96, 1.62, 13.20, 0.66, 0.18)                                              # rising into the landing
ev('whip', 0, 0.14, 13.08, 0.03, 0.22)                                                  # the playhead falls
ev('logo-hit', 0, 2.2, 13.20, 0.0, 0.28); ev('impact', 0, 0.89, 13.20, 0.02, 0.16)     # and lands, cutting its gap (Open): under the name being said
for i in range(8): ev('tick', 0, 0.12, round(13.27 + 0.09 * i + 0.17, 3), 0.02, round(0.12 - 0.005 * i, 3))   # O p e n F i l m stand up
ev('shimmer', 0.3, 1.6, 14.40, 0.12, 0.12)                                              # the sheen crosses the logo
for w in (14.27, 14.79, 15.53): ev('snap', 0, 0.4, round(w + 0.08, 3), 0.07, 0.26)    # 免费 · 开源 · MIT 协议 snap in
# no dive: S4 takes the end card into its viewer (s4.html), its sound is S4's
src = FILM.read_text()
# the events below are in the film's seconds with this line at 12.433; they move with its page clip
m = re.search(r'<iframe id="s3" src="s3.html(?:#t=[^"]*)?" at="([\d.]+)"', src)
SHIFT = (float(m.group(1)) if m else 12.433) - 12.433
CARD_END = 16.553                 # the end card, still, before the plate dives: S4 takes it from here (this line at 12.433)
src = re.sub(r'  <audio id="l3-[^"]*"[^\n]*\n', '', src)
src = re.sub(r'  <audio id="(%s)"[^\n]*\n' % '|'.join(map(re.escape, OLD)), '', src)
src = re.sub(r'  <video id="s3-(logo|mark)"[^\n]*\n', '', src)
src = re.sub(r'<section>\n</section>\n', '', src)
# the plate on the plates' track, after line 2's
src = re.sub(r'(  <video id="s2-cast"[^\n]*\n)', lambda g: g.group(1) + f'  <video id="s3-mark" src="assets/video/s3-mark.mp4#t=0,{CARD_END - 12.433:.3f}" at="{12.433 + SHIFT:g}"></video>\n', src, count=1)
assert 'id="s3-mark"' in src, 'no s2-cast plate to put the mark after'
items = []
for i, (f, a, b, hit, off, v) in enumerate(EV):
    at = round(hit - off + SHIFT, 3); items.append((at, at + b - a, f'  <audio id="l3-{f}-{i}" src="{SFX}{f}.mp3#t={a},{b}" at="{at}" volume="{v}"></audio>'))
items.sort(); tracks = []
for it in items:
    for tr in tracks:
        if tr[-1][1] <= it[0] - 0.005: tr.append(it); break
    else: tracks.append([it])
src = src.replace('</body>', ''.join('<section>\n' + ''.join(x[2] + '\n' for x in tr) + '</section>\n' for tr in tracks) + '</body>')
FILM.write_text(src)
print(len(items), 'sounds on', len(tracks), 'tracks')
