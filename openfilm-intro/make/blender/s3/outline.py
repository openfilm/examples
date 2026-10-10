"""The brand's outlines as polygons in logo-light.svg (../icons)'s own frame (viewBox -6 -90.8 574.4 120.9, y down): the playhead,
the two clips whole and as the mark cuts them (minus the playhead grown by half the mask's 7-unit stroke), and the
name's letters. The name's glyphs overlap themselves (the arches of n and m run into their stems, e's bar into its
bowl) and fill nonzero; nonzero() turns each into plain outlines and holes, which a 2D curve fills right."""
import math, re
from pathlib import Path

LOGO = (Path(__file__).parents[1] / 'icons' / 'logo-light.svg').read_text()   # OpenFilm's logo, as the openfilm repository's docs/logo-light.svg draws it
_tr = lambda s: [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', s)]
MARK_T = _tr(re.search(r'<g transform="([^"]+)"', LOGO).group(1))           # translate x y, scale k
WORD_T = _tr(re.findall(r'<path transform="([^"]+)"', LOGO)[-1])
WORD_D = re.findall(r' d="([^"]+)"', LOGO)[-1]
PLAYHEAD_D = re.findall(r'<path d="([^"]+)"', LOGO)[0]

def parse(d, n=12):
    """an SVG path of M L H V Q Z (absolute) → its contours, each a list of points, curves flattened"""
    toks = re.findall(r'[MLHVQZ]|-?\d+(?:\.\d+)?(?:e-?\d+)?', d); out = []; i = 0; pos = (0.0, 0.0)
    num = lambda k: float(toks[k])
    while i < len(toks):
        c = toks[i]; i += 1
        if c == 'M': pos = (num(i), num(i + 1)); i += 2; out.append([pos])
        elif c == 'L': pos = (num(i), num(i + 1)); i += 2; out[-1].append(pos)
        elif c == 'H': pos = (num(i), pos[1]); i += 1; out[-1].append(pos)
        elif c == 'V': pos = (pos[0], num(i)); i += 1; out[-1].append(pos)
        elif c == 'Q':
            p1, p2 = (num(i), num(i + 1)), (num(i + 2), num(i + 3)); i += 4
            for k in range(1, n + 1):
                u = k / n; out[-1].append(((1 - u) ** 2 * pos[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0], (1 - u) ** 2 * pos[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]))
            pos = p2
    return [c[:-1] if len(c) > 1 and math.dist(c[0], c[-1]) < 1e-9 else c for c in out]

def nonzero(contours):
    """the outlines of what the contours fill under the nonzero rule: the edges with filled on one side only, chained"""
    segs = [(c[i], c[(i + 1) % len(c)]) for c in contours for i in range(len(c)) if c[i] != c[(i + 1) % len(c)]]
    cuts = [[0.0, 1.0] for _ in segs]
    for i, (a, b) in enumerate(segs):
        for j in range(i + 1, len(segs)):
            c, d = segs[j]
            if max(a[0], b[0]) < min(c[0], d[0]) or max(c[0], d[0]) < min(a[0], b[0]) or max(a[1], b[1]) < min(c[1], d[1]) or max(c[1], d[1]) < min(a[1], b[1]): continue
            rx, ry, sx, sy = b[0] - a[0], b[1] - a[1], d[0] - c[0], d[1] - c[1]
            den = rx * sy - ry * sx
            if abs(den) < 1e-12: continue
            t = ((c[0] - a[0]) * sy - (c[1] - a[1]) * sx) / den; u = ((c[0] - a[0]) * ry - (c[1] - a[1]) * rx) / den
            if 1e-9 < t < 1 - 1e-9 and 1e-9 < u < 1 - 1e-9: cuts[i].append(t); cuts[j].append(u)
    def winding(p):
        w = 0
        for a, b in segs:
            if a[1] <= p[1] < b[1] and (b[0] - a[0]) * (p[1] - a[1]) - (p[0] - a[0]) * (b[1] - a[1]) > 0: w += 1
            elif b[1] <= p[1] < a[1] and (b[0] - a[0]) * (p[1] - a[1]) - (p[0] - a[0]) * (b[1] - a[1]) < 0: w -= 1
        return w
    key = lambda p: (round(p[0], 4), round(p[1], 4))
    edges = {}
    for (a, b), ts in zip(segs, cuts):
        ts = sorted(set(ts)); L = math.dist(a, b)
        for t0, t1 in zip(ts, ts[1:]):
            p = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0); q = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            if math.dist(p, q) < 1e-7: continue
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2); e = 1e-4 * max(1.0, L) / max(L, 1e-9)
            left = (m[0] - (q[1] - p[1]) * e, m[1] + (q[0] - p[0]) * e); right = (m[0] + (q[1] - p[1]) * e, m[1] - (q[0] - p[0]) * e)
            fl, fr = winding(left) != 0, winding(right) != 0
            if fl != fr:
                s, f = (p, q) if fl else (q, p)
                edges.setdefault(key(s), []).append(f)
    loops = []
    while edges:
        k0 = next(iter(edges)); loop = [k0]; k = k0
        while True:
            nxt = edges[k].pop()
            if not edges[k]: del edges[k]
            k = key(nxt)
            if k == k0 or k not in edges: break
            loop.append(k)
        if len(loop) > 2: loops.append(loop)
    return loops

def mark(p):  return (MARK_T[0] + MARK_T[2] * p[0], MARK_T[1] + MARK_T[2] * p[1])
def word(p):  return (WORD_T[0] + WORD_T[2] * p[0], WORD_T[1] + WORD_T[2] * p[1])

def rounded_rect(x, y, w, h, r, n=10):
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        pts += [(cx + r * math.cos(math.radians(a0 + 90 * k / n)), cy + r * math.sin(math.radians(a0 + 90 * k / n))) for k in range(n + 1)]
    return pts

PLAYHEAD = parse(PLAYHEAD_D)[0]                                   # in the mark's own units (0 0 100 100)
R = 3.5                                                           # half the mask's stroke: the gap
_dense = [(a[0] + (b[0] - a[0]) * k / m, a[1] + (b[1] - a[1]) * k / m) for a, b in zip(PLAYHEAD, PLAYHEAD[1:] + PLAYHEAD[:1]) for m in [max(4, math.ceil(math.dist(a, b) / 0.05))] for k in range(m)]
def cut_x(y):
    """where the grown playhead ends on the right at height y: the clips start there"""
    return max((q[0] + math.sqrt(R * R - (y - q[1]) ** 2) for q in _dense if abs(y - q[1]) <= R), default=-1e9)
def cut_clip(x, y, w, h, r, n=10):
    """a clip with its left end cut away by the grown playhead: the cut edge on the left, round corners on the right"""
    pts = [(cut_x(y), y)]
    pts += [(x + w - r + r * math.cos(math.radians(-90 + 90 * k / n)), y + r + r * math.sin(math.radians(-90 + 90 * k / n))) for k in range(n + 1)]
    pts += [(x + w - r + r * math.cos(math.radians(90 * k / n)), y + h - r + r * math.sin(math.radians(90 * k / n))) for k in range(n + 1)]
    pts += [(cut_x(y + h - h * k / 60), y + h - h * k / 60) for k in range(60)]
    return pts
CLIPS = [(22, 12, 64, 20, 5), (25, 44, 47, 19, 5)]               # the mark's two rects (x y w h rx)

def letters():
    """the name's glyphs, grouped by what overlaps in x (the i's dot with its stem), in reading order: [loops], in the logo's frame"""
    subs = parse(WORD_D); groups = []
    for c in subs:
        x0, x1 = min(p[0] for p in c), max(p[0] for p in c)
        for g in groups:
            if x0 < g['x1'] and x1 > g['x0']: g['c'].append(c); g['x0'] = min(g['x0'], x0); g['x1'] = max(g['x1'], x1); break
        else: groups.append({'x0': x0, 'x1': x1, 'c': [c]})
    groups.sort(key=lambda g: g['x0'])
    return [[[word(p) for p in lp] for lp in nonzero(g['c'])] for g in groups]

if __name__ == '__main__':
    L = letters(); print(len(L), 'letters', [len(g) for g in L])
    for g in L: print([round(min(p[0] for lp in g for p in lp), 2), round(max(p[0] for lp in g for p in lp), 2)], [len(lp) for lp in g])
    print('cut', round(cut_x(12), 2), round(cut_x(20), 2), round(cut_x(32), 2), round(cut_x(44), 2), round(cut_x(63), 2))
    print('mark box', mark((14, 12)), mark((86, 92)))
