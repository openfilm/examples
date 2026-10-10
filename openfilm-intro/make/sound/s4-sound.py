"""S4's sounds in film.html (ids l4-*), each on its moment in s4.html, which this reads the same way the page does:
the voice-over transcript for when each thing is said, plus the page's own offsets into each clip. A new take of the
line moves them all with it. python3 make/sound/s4-sound.py (from the example's folder)"""
import re
from pathlib import Path
HERE = Path(__file__).parents[2]                # the example's folder
FILM = HERE / 'film.html'
VTT = HERE / 'assets/audio/vo/l4-v4.vtt'
VO = 0.55
SAID = ['剪口播', '挑素材', '加字幕', '配B-roll', '调色', '做MG动画', '配音配乐', '产品片', '广告', '知识讲解', '绘本', '课件', 'MV', '它都能做']
SFX = 'assets/audio/sfx/'

def beats():
    raw = VTT.read_text(); chars = []; end = 0.0
    sec = lambda h, m, s: int(h) * 3600 + int(m) * 60 + float(s)
    for cue in re.split(r'\n\n+', raw):
        m = re.search(r'(\d\d):(\d\d):(\d\d\.\d+) --> (\d\d):(\d\d):(\d\d\.\d+)\n([\s\S]+)', cue)
        if not m: continue
        t = sec(*m.group(1, 2, 3)); end = max(end, sec(*m.group(4, 5, 6)))
        for part in re.split(r'(<\d\d:\d\d:\d\d\.\d+>)', m.group(7)):
            tag = re.match(r'<(\d\d):(\d\d):(\d\d\.\d+)>', part)
            if tag: t = sec(*tag.groups()); continue
            chars += [(ch, t) for ch in part if not ch.isspace()]
    text = ''.join(c for c, _ in chars); B = {}; at = 0
    for w in SAID:
        i = text.index(w, at); B[w] = chars[i][1] + VO; at = i + len(w)
    return B, end + VO

B, END = beats()
a, bEnd = B['剪口播'], B['它都能做']
EV = []   # file, in, out, page time of the hit, offset of the hit in the clip, volume
def ev(f, a0, b0, hit, off, v): EV.append((f, a0, b0, hit, off, v))
ev('swoosh', 0.04, 0.46, 0.5, 0.16, 0.1)                                                      # the mark comes apart, its three pieces at once
ev('tick', 0, 0.12, 0.92, 0.02, 0.09); ev('tick', 0, 0.12, 0.95, 0.02, 0.12)                  # the clips land in the row, the playhead on them
for j in range(3): ev('snip', 0, 0.32, a + 0.14 + 0.05 * j, 0.06, 0.16)                       # 剪口播: each um, as it is cut
k = B['挑素材']; ev('keys', 0, 0.3, k, 0.01, 0.12)                                            # 海边 日落
for m in range(3): ev('pop', 0, 0.35, k + 0.16 + 0.04 * m, 0.0, 0.16)                          # the three that fit
for m in range(3): ev('tick', 0, 0.12, k + 0.56 + 0.05 * m, 0.02, 0.07)                       # into the tray
for i in range(3): ev('pop', 0, 0.35, B['加字幕'] + 0.03 + 0.13 * i, 0.0, 0.14)               # the subtitles, word by word
k, n = B['配B-roll'], B['调色'] - B['配B-roll']
ev('tick', 0, 0.12, k + 0.2, 0.02, 0.08)                                                      # the cutaway lands on V2
ev('swoosh', 0.04, 0.46, k + (480 - 300) / 620 * n, 0.16, 0.07)                               # the picture goes to it
ev('swoosh', 0.04, 0.46, B['做MG动画'] + 0.1, 0.16, 0.08)                                    # the glass comes forward, turning
ev('shimmer', 0.3, 1.4, B['做MG动画'] + 0.12, 0.12, 0.07)                                     # its light
ev('ding', 0, 0.8, B['做MG动画'] + 0.06 + 0.3, 0.02, 0.06)                                     # the name up
ev('shimmer', 0.3, 1.6, B['配音配乐'] + 0.05, 0.12, 0.08)                                     # the sound laid in
for w in ('产品片', '广告', '知识讲解', '绘本', '课件', 'MV'): ev('tick', 0, 0.12, B[w], 0.02, 0.10)   # each film as it is named
ev('shimmer', 0.3, 1.6, bEnd + 0.05, 0.12, 0.12)                                              # all of them: the whole edit
ev('whoosh', 0, 0.29, END + 0.1, 0.03, 0.10)                                                  # into the dark of S5

src = FILM.read_text()
AT = float(re.search(r'<iframe id="s4" src="s4.html" at="([\d.]+)"', src).group(1))
src = re.sub(r'  <audio id="l4-[^"]*"[^\n]*\n', '', src)
src = re.sub(r'<section>\n</section>\n', '', src)
items = []
for i, (f, a0, b0, hit, off, v) in enumerate(EV):
    at = round(AT + hit - off, 3); items.append((at, at + b0 - a0, f'  <audio id="l4-{f}-{i}" src="{SFX}{f}.mp3#t={a0},{b0}" at="{at}" volume="{v}"></audio>'))
items.sort(); tracks = []
for it in items:
    for tr in tracks:
        if tr[-1][1] <= it[0] - 0.005: tr.append(it); break
    else: tracks.append([it])
src = src.replace('</body>', ''.join('<section>\n' + ''.join(x[2] + '\n' for x in tr) + '</section>\n' for tr in tracks) + '</body>')
FILM.write_text(src)
print(len(items), 'sounds on', len(tracks), 'tracks')
