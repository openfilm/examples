"""S7's sounds in film.html (ids l7-*), each on what happens in s7.html, timed the way the page is: from the line's
words (assets/audio/vo/l7-v5.vtt) and its own beats. python3 make/sound/s7-sound.py (from the example's folder)"""
import math, re
from pathlib import Path
HERE = Path(__file__).parents[2]                # the example's folder
FILM = HERE / 'film.html'
SFX = 'assets/audio/sfx/'
VO = 0.3
def vtt(path):
    raw = path.read_text(); chars = []; end = 0.0
    sec = lambda h, m, x: int(h) * 3600 + int(m) * 60 + float(x)
    for cue in re.split(r'\n\n+', raw):
        m = re.search(r'(\d\d):(\d\d):(\d\d\.\d+) --> (\d\d):(\d\d):(\d\d\.\d+)\n([\s\S]+)', cue)
        if not m: continue
        t = sec(*m.group(1, 2, 3)); end = max(end, sec(*m.group(4, 5, 6)))
        for part in re.split(r'(<\d\d:\d\d:\d\d\.\d+>)', m.group(7)):
            tag = re.match(r'<(\d\d):(\d\d):(\d\d\.\d+)>', part)
            if tag: t = sec(*tag.groups()); continue
            chars += [(c, t) for c in part if not c.isspace()]
    text = ''.join(c for c, _ in chars)
    return (lambda w: chars[text.index(w)][1] + VO), end + VO
at, END = vtt(HERE / 'assets/audio/vo/l7-v5.vtt')
W = {k: at(w) for k, w in [('cmd', '一行命令'), ('me', '我做它'), ('every', '每个'), ('none', '都不会'), ('young', '很年轻'), ('keep', '我会'),
     ('follow', '现在关注'), ('share', '免费入股'), ('triple', '一键三连'), ('late', '熬夜'), ('power', '动力'), ('last', '最后'), ('want', '你最想'), ('comm', '评论区'),
     ('top', '点赞最高'), ('make', '剪出来'), ('bye', '下期见'), ('try', '想试试'), ('app', '客户端')]}
FO = W['follow'] - 16.54                                                            # the follow block's times, laid out on 现在关注 at 16.54
EV = []   # file, in, out, page time of the hit, offset of the hit in the clip, volume
def ev(f, a, b, hit, off, v): EV.append((f, a, b, hit, off, v))
tap = lambda t, v=0.15: ev('tap', 0.33, 0.75, t, 0.08, v)
tick = lambda t, v=0.06: ev('tick', 0, 0.12, t, 0.02, v)
pop = lambda t, v=0.1: ev('pop', 0, 0.35, t, 0.0, v * 1.7)
whoosh = lambda t, v=0.08: ev('whoosh', 0, 0.29, t, 0.03, v)
paper = lambda t, v=0.08: ev('toss', 0, 0.3, t, 0.08, v)

# A · the film rewinds in the app: a tick as each shot flies past, a stop on the first frame (rec-s7.mjs FILM_FRAME)
src0 = FILM.read_text()
S7 = float(re.search(r'<iframe id="s7" src="s7.html" at="([\d.]+)"', src0).group(1))
LAST = (math.ceil(S7 * 30 - 1e-6) - 1) / 30                                        # S6's last frame; held 14 frames, rewound in 69
starts = [float(re.search(r'<iframe id="%s" src="[^"]+" at="([\d.]+)"' % k, src0).group(1)) for k in ('s6', 's5', 's4', 's3', 's2')]
inout = lambda x: 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
def rewound_to(sec):
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if LAST * (1 - inout(mid)) > sec: lo = mid
        else: hi = mid
    return (14 + 69 * lo) / 30
whoosh(0.5, 0.07)
for s_ in starts: tick(rewound_to(s_), 0.09)
ev('clack', 0.25, 0.6, 83 / 30, 0.05, 0.12)
# B · through the window, into what people want to make
ev('whoosh', 0, 0.88, W['me'] - 0.3, 0.2, 0.09)
# D · ideas written down, turned over into films
paper(W['me'] + 0.1, 0.12)
ranks = [W['every'] - 0.25 + 0.11 * r for r in range(1, 11)]
for r, t in enumerate(ranks):
    if r % 2 == 0: paper(t, 0.06)
for r in range(11):
    if r < 6 or r % 2 == 0: ev('flip', 1.55, 1.95, W['none'] + 0.12 * r + 0.2, 0.15, 0.09 if r == 0 else 0.06)
ev('shimmer', 0, 2.2, W['none'] + 1.4, 0.05, 0.06)
# C · the command, or the app: the films stand back for it
whoosh(W['try'] - 0.2, 0.06)
ev('keys', 0.01, 0.6, W['cmd'] + 0.02, 0.01, 0.1); ev('enter', 0, 0.4, W['cmd'] + 0.7, 0.02, 0.12)
pop(W['cmd'] + 0.82, 0.1)                                                           # ✓
pop(W['app'] - 0.8, 0.14)                                                           # the app's icon
tap(W['app'], 0.16); ev('ding', 0, 0.8, W['app'] + 0.5, 0.0, 0.05)                  # Download, done
whoosh(W['young'] - 0.45, 0.07); ev('tile-land', 0, 0.5, W['young'] + 0.45, 0.03, 0.14)   # the films, into the timeline
# E · the playhead; the versions to come
tick(W['young'] + 0.15, 0.08)
for k in range(5): tick(W['keep'] + 0.3 * k + 0.1, 0.05 + 0.005 * k)
# F · follow, free shares, the triple tap
whoosh(16.35 + FO, 0.05); pop(W['follow'] - 0.05, 0.1)
tap(17.24 + FO, 0.16); ev('ding', 0, 0.8, 17.3 + FO, 0.0, 0.06)
paper(W['share'] - 0.15, 0.1)
ev('stamp', 0.2, 0.9, W['share'] + 0.52, 0.1, 0.22)
for k in range(3): pop(W['triple'] - 0.05 + 0.08 * k + 0.1, 0.07)
ev('riser', 0.8, 1.7, 19.92 + FO, 0.9, 0.08)                                        # held, filling
ev('impact', 0, 1.2, 19.92 + FO, 0.0, 0.16); ev('shimmer', 0, 1.6, 19.95 + FO, 0.05, 0.08)   # the burst
whoosh(20.12 + FO, 0.06); ev('ding', 0, 0.8, W['power'] + 0.05, 0.0, 0.08)          # into v0.2, filled
pop(W['late'], 0.06)
# G, H · what you'd have it make; the comments
whoosh(W['last'], 0.07)                                                             # the panel comes up
tap(W['want'] + 0.66, 0.13)                                                         # a click in its box
ev('keys', 0.01, 1.0, W['want'] + 0.78, 0.01, 0.08)                                 # written
tap(W['comm'] - 0.06, 0.16); pop(W['comm'] + 0.08, 0.1)                             # sent: in at the top
ev('riser', 0.7, 1.7, W['top'] + 1.2, 1.0, 0.06)                                    # the likes pour in
pop(W['top'] + 1.0, 0.07)                                                           # 最热
ev('stamp', 0.2, 0.9, W['make'], 0.1, 0.24)
# I · see you
whoosh(W['bye'] - 0.8, 0.05); ev('shimmer', 0, 1.8, W['bye'] + 0.1, 0.05, 0.06)

src = FILM.read_text()
AT = float(re.search(r'<iframe id="s7" src="s7.html" at="([\d.]+)"', src).group(1))
src = re.sub(r'  <audio id="l7-[^"]*"[^\n]*\n', '', src)
src = re.sub(r'<section>\n</section>\n', '', src)
items = []
for i, (f, a, b, hit, off, v) in enumerate(EV):
    t = round(AT + hit - off, 3); items.append((t, t + b - a, f'  <audio id="l7-{f}-{i}" src="{SFX}{f}.mp3#t={a},{b}" at="{t}" volume="{v}"></audio>'))
items.sort(); tracks = []
for it in items:
    for tr in tracks:
        if tr[-1][1] <= it[0] - 0.005: tr.append(it); break
    else: tracks.append([it])
src = src.replace('</body>', ''.join('<section>\n' + ''.join(x[2] + '\n' for x in tr) + '</section>\n' for tr in tracks) + '</body>')
FILM.write_text(src)
print(len(items), 'sounds on', len(tracks), 'tracks')
