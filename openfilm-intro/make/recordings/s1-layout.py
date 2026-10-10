"""From rec-s1.mjs's recording: where OpenFilm's pieces are in the hero frame (make/blender/s1/tex/hero_layout.json, the
film's px) and the frame the background slats turn into (make/blender/s1/tex/plate.png: the recording's own, whole).
rebuild.py lands Premiere's pieces there.
python3 make/recordings/s1-layout.py <rec-s1 work dir>   (from the example's folder)"""
import json, sys
from pathlib import Path
from PIL import Image
WORK = Path(sys.argv[1]); TEX = Path(__file__).parents[1] / 'blender/s1/tex'
D = json.loads((WORK / 'dom.json').read_text()); Z = 1920 / D['w']
px = lambda r: [round(v * Z, 1) for v in r]
X0, PPS = D['playhead'][0], None
# the ruler: px a second, from the clips' own lengths (title 3 s from the lane's start to track's label)
track_x = [b for n, b in D['clips'] if n == 'track'][0][0] - 6
PPS = (track_x - X0) / 3.0
tx = lambda s: X0 + s * PPS
P1 = D['heads'][0][1] - 21, D['heads'][0][3] + 21          # each lane's top and bottom, about its head's label
V1 = D['heads'][1][1] - 20, D['heads'][1][3] + 20
A1 = D['heads'][2][1] - 14, D['heads'][2][3] + 15
CUTS = [(0, 3), (3, 6), (6, 8), (8, 11), (11, 14.5)]
rows = sorted({tuple(r) for r in D['rows']}, key=lambda r: r[1])
T = {
  'top': ([0, 0, 1600, 32], 'plate'), 'media': ([6, 32, 246, 636], 'plate'), 'viewer': ([252, 32, 874, 636], 'plate'),
  'insp': ([880, 32, 1180, 636], 'plate'), 'chat': ([1186, 32, 1594, 894], 'plate'), 'tl': ([6, 642, 1180, 894], 'plate'),
  'm_head': ([10, 36, 244, 60], 'hero'),
  'pic': (D['stage'], 'hero'), 'vbar': ([256, 606, 872, 634], 'hero'), 'insp_c': ([884, 70, 1176, 270], 'hero'),
  'o_sel': ([20] + D['select'][1:], 'hero'), 'o_undo': (D['undo'], 'hero'), 'o_redo': (D['redo'], 'hero'),
  'o_time': (D['history'], 'hero'), 'o_razor': (D['split'], 'hero'), 'o_zoom': ([D['zoomOut'][0] - 36] + D['zoomOut'][1:2] + [1176, D['zoomOut'][3]], 'hero'),
  'ruler': (D['playhead'], 'hero'),
  'h_P1': ([6, P1[0], X0, P1[1]], 'hero'), 'h_V1': ([6, V1[0], X0, V1[1]], 'hero'), 'h_A1': ([6, A1[0], X0, A1[1]], 'hero'),
  'A1_0': ([tx(0), A1[0], tx(14.5), A1[1]], 'hero'),
}
for i, name in enumerate(['t_audio', 't_video', 't_end', 't_km', 't_title', 't_track']): T[name] = (list(rows[min(i, len(rows) - 1)]), 'hero')
for i, (a, b) in enumerate(CUTS):
    T[f'P1_{i}'] = ([tx(a), P1[0], tx(b), P1[1]], 'hero'); T[f'V1_{i}'] = ([tx(a), V1[0], tx(b), V1[1]], 'hero')
out = {k: [px(r), tex] for k, (r, tex) in T.items()}
(TEX / 'hero_layout.json').write_text(json.dumps({'T': out, 'lane': [round(tx(0) * Z, 1), round(tx(14.5) * Z, 1)]}, indent=1))
# the plate: the same window, whole: what the slats turn into is exactly what the recording shows, so nothing
# appears at the cut that the rebuild did not bring
im = Image.open(TEX / 'hero_land_nocursor.png').convert('RGB')
im.save(TEX / 'plate.png')
print('ok', len(out), 'targets; lane', out['A1_0'][0][:3:2])
