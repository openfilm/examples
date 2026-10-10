"""A voice's WebVTT made into subtitle lines a viewer reads at a glance: a cue for each phrase (cut at the pauses: ，、：；
and the ends of sentences), at most MAX characters, the commas and full stops at a line's end left off (a ？ or ！ kept),
each character's own time kept as its tag (the karaoke form the pages read their timing from). Run it once, on the VTT
as tts.mjs writes it: the lines it writes have lost the pause marks it cuts at.
python3 make/voice/vtt-lines.py <file.vtt> [...]   (in place)"""
import re, sys
MAX = 18
CUT = set('，、：；。！？,;:!?')
DROP = set('，、：；。,;:')
ts = lambda s: '%02d:%02d:%06.3f' % (s // 3600, s % 3600 // 60, s % 60)
for path in sys.argv[1:]:
    raw = open(path, encoding='utf-8').read()
    chars = []          # (character, its start, the end of its cue)
    sec = lambda h, m, x: int(h) * 3600 + int(m) * 60 + float(x)
    for cue in re.split(r'\n\n+', raw):
        m = re.search(r'(\d\d):(\d\d):(\d\d\.\d+) --> (\d\d):(\d\d):(\d\d\.\d+)\n([\s\S]+)', cue)
        if not m: continue
        t, end = sec(*m.group(1, 2, 3)), sec(*m.group(4, 5, 6))
        for part in re.split(r'(<\d\d:\d\d:\d\d\.\d+>)', m.group(7)):
            tag = re.match(r'<(\d\d):(\d\d):(\d\d\.\d+)>', part)
            if tag: t = sec(*tag.groups()); continue
            for c in part.replace('\n', ''):
                chars.append([c, t, end])
    # the spaces between Latin words, which the voice's own timing leaves out: back in, at the next word's time
    SPACED = ['Claude Code', 'AI Agent']
    text = ''.join(c[0] for c in chars)
    for w in SPACED:
        joined = w.replace(' ', '')
        i = text.find(joined)
        while i >= 0:
            j = i + w.index(' ')
            chars.insert(j, [' ', chars[j][1], chars[j][2]])
            text = ''.join(c[0] for c in chars); i = text.find(joined, j + 1)
    # phrases: cut after a pause mark; a phrase longer than MAX is cut again at its middle space or evenly
    phrases, cur = [], []
    for c in chars:
        cur.append(c)
        if c[0] in CUT: phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    lines = []
    for ph in phrases:
        vis = [c for c in ph if c[0].strip()]
        n = len(vis)
        if n <= MAX: lines.append(ph); continue
        k = -(-n // MAX); size = -(-len(ph) // k)
        for i in range(0, len(ph), size): lines.append(ph[i:i + size])
    out = ['WEBVTT', '']
    for i, ln in enumerate(lines):
        while len(ln) > 1 and (ln[-1][0] in DROP or not ln[-1][0].strip()): ln = ln[:-1]
        while len(ln) > 1 and not ln[0][0].strip(): ln = ln[1:]
        start = ln[0][1]
        nxt = lines[i + 1][0][1] if i + 1 < len(lines) else ln[-1][2]
        end = max(ln[-1][2], ln[-1][1] + 0.2)
        if i + 1 < len(lines): end = min(end, nxt)          # never on screen with the next line
        body = ln[0][0] + ''.join(f'<{ts(c[1])}>{c[0]}' for c in ln[1:])
        out += [f'{ts(start)} --> {ts(end)}', body, '']
    open(path, 'w', encoding='utf-8').write('\n'.join(out))
    print(path, len(lines), 'lines:', ' / '.join(''.join(c[0] for c in l).strip('，、：；。,;: ') for l in lines))
