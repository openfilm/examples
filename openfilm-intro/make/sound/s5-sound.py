"""S5's sounds in film.html (ids l5-<sfx>-n), each on what the hand does in make/recordings/rec-s5.mjs, timed the way it is: from
S5's voice as lib/s5-voice.json lays it out; and its voice clips (l5-a … l5-k), each line of the file at its place.
python3 make/sound/s5-sound.py (from the example's folder)"""
import json, re
from pathlib import Path
HERE = Path(__file__).parents[2]                # the example's folder
FILM = HERE / 'film.html'
SFX = 'assets/audio/sfx/'
V = json.loads((HERE / 'lib/s5-voice.json').read_text())

def vtt(path):
    raw = path.read_text(); chars = []
    sec = lambda h, m, x: int(h) * 3600 + int(m) * 60 + float(x)
    for cue in re.split(r'\n\n+', raw):
        m = re.search(r'(\d\d):(\d\d):(\d\d\.\d+) --> (\d\d):(\d\d):(\d\d\.\d+)\n([\s\S]+)', cue)
        if not m: continue
        t = sec(*m.group(1, 2, 3))
        for part in re.split(r'(<\d\d:\d\d:\d\d\.\d+>)', m.group(7)):
            tag = re.match(r'<(\d\d):(\d\d):(\d\d\.\d+)>', part)
            if tag: t = sec(*tag.groups()); continue
            chars += [(c, t) for c in part if not c.isspace()]
    return chars
CHARS = vtt(HERE / V['vtt']); TEXT = ''.join(c for c, _ in CHARS)
def said(w):
    c = CHARS[TEXT.index(w)][1]
    line = next((l for l in V['lines'] if l['from'] <= c + 0.05 < l['to']), V['lines'][-1])
    return line['at'] + (c - line['from'])
T = {k: said(w) for k, w in [('click', '点一下'), ('pos', '位置'), ('size', '大小'), ('rot', '旋转'), ('color', '颜色'), ('more', '更多属性'),
     ('text', '文字'), ('shape', '图形'), ('video', '视频'), ('box', '框起来'), ('tell', '告诉')]}
SUN = V.get('sun', 16.5)                     # the sun lands in the picture (the recording writes when)
EV = []   # file, in, out, page time of the hit, offset of the hit in the clip, volume
def ev(f, a, b, hit, off, v): EV.append((f, a, b, hit, off, v))
tap = lambda t, v=0.15: ev('tap', 0.33, 0.75, t, 0.08, v)
drag = lambda t, v=0.08: ev('swoosh', 0.04, 0.46, t, 0.16, v)
pop = lambda t, v=0.12: ev('pop', 0, 0.35, t, 0.0, v)
tick = lambda t, v=0.05: ev('tick', 0, 0.12, t, 0.02, v)
tap(T['click'], 0.18)                                                               # the title, clicked on 点
drag(T['pos'] + 0.25, 0.09)                                                         # dragged up over the trees
drag(T['size'] + 0.2)                                                               # bigger by its corner
drag(T['rot'] + 0.18)                                                               # turned
tick(T['color'] - 0.12); tick(T['color'] + 0.02)                                    # the inspector rolled up a little
tap(T['color'] + 0.28); pop(T['color'] + 0.31)                                      # the swatch: the picker opens
tap(T['color'] + 0.7, 0.16)                                                         # gold
for d in (0.15, 0.5, 0.85): tick(T['more'] + d)                                     # the inspector, rolled down
tap(T['more'] + 1.44, 0.13); pop(T['more'] + 1.47); tap(T['more'] + 1.8, 0.13)      # + , Shadow
tap(T['text'], 0.16); drag(T['shape'] + 0.2)                                        # the rule, clicked and stretched
tap(T['video'], 0.15)                                                               # the footage, in Layers
tick(T['video'] + 0.4); tap(T['video'] + 0.8, 0.12); drag(T['video'] + 1.0, 0.07)  # rolled to Adjust; brightness down
drag((T['box'] + T['tell']) / 2, 0.07)                                              # the ⌘ box drawn
pop(T['tell'] + 0.1, 0.14)                                                          # into the chat
ev('keys', 0, 0.5, T['tell'] + 0.24, 0.01, 0.08)                                    # 这里加点阳光
ev('enter', 0, 0.4, T['tell'] + 0.8, 0.02, 0.1)                                     # sent
ev('shimmer', 0, 2.2, SUN, 0.05, 0.08)                                              # the sun, in the box

src = FILM.read_text()
AT = float(re.search(r'<iframe id="s5" src="s5.html" at="([\d.]+)"', src).group(1))
for i, l in enumerate(V['lines']):
    vid = 'l5-' + 'abcdefghijk'[i]
    src, k = re.subn(r'(<audio id="%s" src="%s)#t=[\d.]+,[\d.]+(" at=")[\d.]+' % (vid, V['src']), lambda m: f"{m.group(1)}#t={l['from']},{l['to']}{m.group(2)}{round(AT + l['at'], 4)}", src)
    assert k == 1, vid
src = re.sub(r'  <audio id="l5-[^"]*" src="assets/audio/sfx/[^\n]*\n', '', src)
src = re.sub(r'<section>\n</section>\n', '', src)
items = []
for i, (f, a, b, hit, off, v) in enumerate(EV):
    t = round(AT + hit - off, 3); items.append((t, t + b - a, f'  <audio id="l5-{f}-{i}" src="{SFX}{f}.mp3#t={a},{b}" at="{t}" volume="{v}"></audio>'))
items.sort(); tracks = []
for it in items:
    for tr in tracks:
        if tr[-1][1] <= it[0] - 0.005: tr.append(it); break
    else: tracks.append([it])
src = src.replace('</body>', ''.join('<section>\n' + ''.join(x[2] + '\n' for x in tr) + '</section>\n' for tr in tracks) + '</body>')
FILM.write_text(src)
print(len(items), 'sounds on', len(tracks), 'tracks')
