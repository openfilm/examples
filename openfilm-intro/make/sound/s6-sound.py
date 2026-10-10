"""S6's sounds in film.html (ids l6-<sfx>-n), each on what happens in s6.html, at the moments it draws them on
(lib/s6-plan.json): the paste, the typing, Enter, the app growing out of the address, each piece the agent writes,
the interruption and the fix, the person's own edit (a shot dragged in from the assets, trimmed), the export and what it writes; and its voice clips (l6-a … l6-i), each
line of the file at its place (lib/s6-voice.json). Every other sound inside S6 but its voice and the score is replaced.
python3 make/sound/s6-sound.py (from the example's folder)"""
import json, re
from pathlib import Path
HERE = Path(__file__).parents[2]                # the example's folder
FILM = HERE / 'film.html'
SFX = 'assets/audio/sfx/'
P = json.loads((HERE / 'lib/s6-plan.json').read_text())
V = json.loads((HERE / 'lib/s6-voice.json').read_text())
EV = []   # file, in, out, page time of the hit, offset of the hit in the clip, volume
def ev(f, a, b, hit, off, v): EV.append((f, a, b, hit, off, v))
tap = lambda t, v=0.15: ev('tap', 0.33, 0.75, t, 0.08, v)
tick = lambda t, v=0.1: ev('tick', 0, 0.12, t, 0.02, v)
keys = lambda t, d, v=0.16: ev('keys', 0.01, round(0.01 + d, 2), t, 0.01, v)
enter = lambda t, v=0.26: ev('enter', 0, 0.4, t, 0.02, v)
pop = lambda t, v=0.1: ev('pop', 0, 0.35, t, 0.0, v)
swoosh = lambda t, v=0.1: ev('swoosh', 0.04, 0.46, t, 0.16, v)
ev('whoosh', 0, 0.29, 0.05, 0.03, 0.16)                                             # in, out of S5's dark
tap(P['paste'], 0.13)                                                               # ⌘V: the command
enter(P['send']); tick(P['send'] + 0.42, 0.12)                                      # sent; ✓ installed
keys(P['ask'][0], round(P['ask'][1] - P['ask'][0], 2))                              # the ask, typed
enter(P['askSend'])
swoosh(P['open'] + 0.12); pop(P['open'] + 0.05)                                     # the app grows out of the address
for s in P['steps']: tick(s, 0.11)                                                  # each piece the agent writes, in
tap(P['esc'] - 0.18, 0.13)                                                          # a click on the terminal
tap(P['esc'], 0.18)                                                                 # Esc
keys(P['fixType'][0], round(P['fixType'][1] - P['fixType'][0] + 0.04, 2), 0.15); enter(P['fixSend'], 0.24)   # 字标改成金色
ev('shimmer', 0, 1.4, P['fix'] + 0.08, 0.05, 0.07)                                  # gold
tap(P['folder'], 0.12); tap(P['folder'] + 0.09, 0.1)                              # the video folder, opened
tap(P['grab'], 0.1); swoosh((P['grab'] + P['drop']) / 2, 0.08)                      # the third shot, picked up and dragged
ev('tile-land', 0.26, 0.75, P['drop'], 0.08, 0.13)                                  # onto the timeline: a track of its own
tap(P['view'], 0.13)                                                                # the ruler: the film there
tap(P['trim'][0], 0.1); tick(P['trim'][1], 0.09)                                    # its tail trimmed, snapped to the end card
tap(P['more'], 0.14); tap(P['menu'], 0.14); pop(P['menu'] + 0.08)                  # More → Export…: the dialog
for g in (P['formats'], P['project']):                                              # what it writes, out to each side
    swoosh(g + 0.12, 0.08)
    for i in range(6): tick(g + 0.06 * i + 0.22, 0.05)

src = FILM.read_text()
AT = float(re.search(r'<iframe id="s6" src="s6.html" at="([\d.]+)"', src).group(1))
END = float(re.search(r'<iframe id="s7" src="s7.html" at="([\d.]+)"', src).group(1))
# the voice: its lines where lib/s6-voice.json lays them, on the track the whole line was on
VOICE = re.compile(r'  <audio id="l6(-[a-z])?" src="%s[^\n]*\n' % re.escape(V['src']))
m = VOICE.search(src)
vol = re.search(r'volume="([\d.]+)"', m.group(0)).group(1)
lines = ''.join(f'  <audio id="l6-{"abcdefghi"[i]}" src="{V["src"]}#t={l["from"]},{l["to"]}" at="{round(AT + l["at"], 4)}" volume="{vol}"></audio>\n' for i, l in enumerate(V['lines']))
src = src[:m.start()] + lines + VOICE.sub('', src[m.start():])
KEEP = re.compile(r'^(l6(-[a-i])?|section1-score.*|outro)$')
def gone(m):                                                                        # this script's own, wherever they were; anything else in S6 but its voice and the score
    at, cid = float(m.group(2)), m.group(1)
    return (cid.startswith('l6-') and not KEEP.match(cid)) or (AT - 0.2 <= at < END and not KEEP.match(cid) and not cid.startswith(('l5-', 'l7-')))
src = '\n'.join(ln for ln in src.split('\n') if not ((m := re.search(r'<audio id="([^"]+)"[^>]*at="([\d.]+)"', ln)) and gone(m)))
src = re.sub(r'<section>\n</section>\n', '', src)
items = []
for i, (f, a, b, hit, off, v) in enumerate(EV):
    t = round(AT + hit - off, 3); items.append((t, t + b - a, f'  <audio id="l6-{f}-{i}" src="{SFX}{f}.mp3#t={a},{b}" at="{t}" volume="{v}"></audio>'))
items.sort(); tracks = []
for it in items:
    for tr in tracks:
        if tr[-1][1] <= it[0] - 0.005: tr.append(it); break
    else: tracks.append([it])
src = src.replace('</body>', ''.join('<section>\n' + ''.join(x[2] + '\n' for x in tr) + '</section>\n' for tr in tracks) + '</body>')
FILM.write_text(src)
print(len(items), 'sounds on', len(tracks), 'tracks;', len(V['lines']), 'voice lines')
