"""Line 3: 它叫 OpenFilm，免费开源，MIT 协议。
On line 2's bright stage the mark from docs/brand comes together the way an edit does. On 它叫 its two clips slide in
and snap onto their track. On Open the playhead drops onto them, and as it lands it cuts the brand's gap around
itself. The jolt stands the name up letter by letter, left to right, through Film, while the camera pulls back to the
end card. The badges and the address are the page's (s3.html, laid out from blender/s3/out/track.json). As the line ends, the
camera dives into the playhead's black head and line 4 opens in the dark. Film 12.433 → 17.033 is frames 0 → 137.
    blender -b -P shot.py -- still <frame> <out.png> [percent] [samples]
    blender -b -P shot.py -- sheet <dir> <percent> <samples> <frame> …
    blender -b -P shot.py -- save
"""
import bpy, bmesh, sys, os, math, json, mathutils
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import bright, outline
from bright import srgb, mat, link, area

FPS, T0, T1 = 30, 12.433, 17.033
N = round((T1 - T0) * FPS)
FR = range(N)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def ss(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def out3(x): return 1 - (1 - clamp(x)) ** 3
def in2(x): return clamp(x) ** 2
def out_back(x, s): x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1
def spring(x, f, d): return 0.0 if x <= 0 else 1 - math.exp(-d * x) * math.cos(f * math.pi * x)
def lerp(a, b, k): return a + (b - a) * k
V = mathutils.Vector

sc = bright.reset(FPS, (0, N - 1))
bright.cyclorama()
bright.lights()

# ── the logo on the stage: 1 unit of logo-light.svg's frame is U metres; the mark is 1.6 m tall, as line 2's cast is 1 m ──
U, XC, BASE = 0.01654, 278.1, 0.70          # metres per unit, the logo's middle at x = 0, its baseline 0.7 m up
def X(x): return (x - XC) * U
def Z(y): return BASE - y * U
M = dict(
    gloss=mat('ink_gloss', '#111111', 0.16, coat=1.0, coat_rough=0.03),     # the playhead: the one glossy piece
    satin=mat('ink_satin', '#111111', 0.34, coat=0.35, coat_rough=0.12),    # clips and letters
)
dg = bpy.context.evaluated_depsgraph_get
def shape(name, loops, pivot, depth, m, y=0.0, bevel=0.0065):
    """outlines (logo frame) → a solid depth m deep with rounded edges, facing −Y, its origin at pivot"""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
    cu.extrude = depth / 2 - bevel; cu.bevel_depth = bevel; cu.bevel_resolution = 3; cu.offset = -bevel   # the bevel would grow it: keep the brand's outline
    for lp in loops:
        sp = cu.splines.new('POLY'); sp.points.add(len(lp) - 1)
        for pt, (x, yy) in zip(sp.points, lp): pt.co = ((x - pivot[0]) * U, (pivot[1] - yy) * U, 0, 1)
        sp.use_cyclic_u = True
    tmp = link(bpy.data.objects.new(name + '_curve', cu))
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg())); bpy.data.objects.remove(tmp); bpy.data.curves.remove(cu)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me); bm.free()
    me.name = name; me.materials.clear(); me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(32))
    o = link(bpy.data.objects.new(name, me)); o.location = (X(pivot[0]), y, Z(pivot[1])); o.rotation_euler = (math.radians(90), 0, 0)
    return o

mk = lambda pts: [outline.mark(p) for p in pts]
PH = shape('playhead', [mk(outline.PLAYHEAD)], outline.mark((27, 92)), 0.20, M['gloss'], y=-0.025)   # 4.5 cm proud of the clips
FULL, CUT = [], []
for i, (x, y, w, h, r) in enumerate(outline.CLIPS):
    pv = outline.mark((x + w / 2, y + h / 2))
    FULL.append(shape(f'clip{i + 1}', [mk(outline.rounded_rect(x, y, w, h, r))], pv, 0.14, M['satin']))
    CUT.append(shape(f'clip{i + 1}_cut', [mk(outline.cut_clip(x, y, w, h, r))], pv, 0.14, M['satin']))
LETTERS = []
for i, loops in enumerate(outline.letters()):
    x0 = min(p[0] for lp in loops for p in lp); x1 = max(p[0] for lp in loops for p in lp)
    LETTERS.append(shape(f'letter{i}', loops, ((x0 + x1) / 2, 0.0), 0.14, M['satin']))

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert('location', frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert('rotation_euler', frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert('scale', frame=f)
def show(o, f, on):
    o.hide_render = not on; o.keyframe_insert('hide_render', frame=f)

# ── the motion ──
TL = 13.20                                    # the playhead lands: "O" of Open
BACK = 0.55                                   # how far past its place a clip slides before it settles
SLIDES = [(12.36, 13.01), (12.56, 13.196)]    # each clip's slide in from the right (the first already moving as the shot opens)
LANDS = [a + (b - a) / (1 + BACK) for a, b in SLIDES]   # where each first reaches its place: 12.78 (它), 12.97 (叫)
SLIDE = 4.6
TF, DROP = 0.30, 2.4                          # the playhead's fall: how long, from how high
WAVE = [13.27 + 0.09 * i for i in range(8)]  # each letter stands up, O through m, with the word
R90 = math.radians(90)
REST_C = [tuple(o.location) for o in FULL]
REST_PH = tuple(PH.location)
REST_L = [tuple(o.location) for o in LETTERS]
for f in FR:
    t = T0 + f / FPS
    u = t - TL
    jolt = -0.022 * math.exp(-11 * u) * math.sin(24 * u) if u > 0 else 0.0     # what the landing does to the track
    for i, (a, b) in enumerate(SLIDES):
        x0, y0, z0 = REST_C[i]
        dx = SLIDE * (1 - out_back(prog(t, a, b), BACK))
        tau = t - LANDS[i]
        sx = 1 - (0.045 * math.exp(-16 * tau) * math.sin(30 * tau) if tau > 0 else 0.0)   # it stops hard: a little give
        for o in (FULL[i], CUT[i]): key(o, f, loc=(x0 + dx, y0, z0 + jolt), scale=(sx, 1, 1))
        show(FULL[i], f, t < TL); show(CUT[i], f, t >= TL)
    # the playhead: hidden above until it falls, stretched by the fall, squashed by the landing
    x0, y0, z0 = REST_PH
    k = prog(t, TL - TF, TL)
    if u < 0: dz, sz = DROP * (1 - k * k), 1 + 0.10 * k * k
    else: dz, sz = 0.0, 1 - 0.13 * math.exp(-10 * u) * math.cos(25 * u)
    key(PH, f, loc=(x0, y0, z0 + dz), scale=(1 + 0.45 * (1 - sz), sz, 1))
    show(PH, f, t >= TL - TF - 0.02)
    # the name stands up, a letter at a time: from lying back to upright, a little past, and settles
    for o, (lx, ly, lz), a in zip(LETTERS, REST_L, WAVE):
        p = prog(t, a, a + 0.55)
        s = out3(prog(t, a, a + 0.10)) if t >= a else 0.0
        flip = -(1 - spring(p, 1.6, 5.0)) * math.radians(82)
        key(o, f, loc=(lx, ly, lz - 0.10 * (1 - out3(p))), rot=(R90 + flip, 0, 0), scale=(max(s, 1e-4),) * 3)
def fcurves(o):
    a = o.animation_data.action if o.animation_data else None
    if a is None: return []
    if hasattr(a, 'fcurves'): return list(a.fcurves)
    return [fc for ly in a.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
for o in [PH, *FULL, *CUT]:
    for fc in fcurves(o):
        if fc.data_path == 'hide_render':
            for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'

# a strip of light crosses the logo once it is whole: its reflection runs over the black like a sheen (glossy rays only)
sweep = area('sweep', (-7.5, -5.5, 1.25), (-7.5, 0, 1.25), 0, '#fff6ea', (0.35, 6.0))
sweep.visible_diffuse = False; sweep.visible_transmission = False; sweep.visible_volume_scatter = False
for f in FR:
    t = T0 + f / FPS; k = prog(t, 14.30, 15.15)
    sweep.data.energy = 160 * math.sin(math.pi * k); sweep.data.keyframe_insert('energy', frame=f)
    key(sweep, f, loc=(lerp(-7.5, 7.5, smooth(k)), -5.5, 1.25))

# ── camera ──
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 40; cam_d.sensor_width = 36
cam = link(bpy.data.objects.new('cam', cam_d)); sc.camera = cam
cam_d.dof.use_dof = True; cam_d.dof.aperture_blades = 7
HEAD = V((X(outline.mark((27, 24))[0]), -0.115, Z(outline.mark((27, 24))[1])))
K0 = (V((-5.02, -2.50, 1.06)), V((-3.78, 0, 1.52)))     # 3/4, low and close, where the clips come in
K2 = (V((-5.35, -3.40, 1.18)), V((-3.90, 0, 1.30)))     # the landing: the whole mark
K4 = (V((0.0, -15.6, 1.62)), V((0.0, 0, 0.74)))         # the end card
K5 = (V((0.0, -14.9, 1.60)), V((0.0, 0, 0.74)))
def cam_pose(t):
    """location, target, f-stop, the plane in focus (y)"""
    if t < 13.24:
        k = 1 - (1 - prog(t, T0, 13.24)) ** 2                                    # moving as the shot opens, settling for the landing
        return K0[0].lerp(K2[0], k), K0[1].lerp(K2[1], k), 2.8, -0.07
    if t < 14.0:
        k = ss(prog(t, 13.24, 14.0) ** 0.8)                                      # pulled back by the jolt, round to the front
        return K2[0].lerp(K4[0], k), K2[1].lerp(K4[1], k), lerp(3.2, 6.0, k), -0.07
    if t < 16.6:
        k = smooth(prog(t, 14.0, 16.6))
        return K4[0].lerp(K5[0], k), K4[1].lerp(K5[1], k), 6.0, -0.07
    s = in2(prog(t, 16.6, T1 - 1 / FPS))                                         # into the head: the distance falls by a constant ratio
    d0 = (K5[0] - HEAD).length; d = d0 * (0.24 / d0) ** s
    loc = HEAD + (K5[0] - HEAD).normalized() * d
    return loc, K5[1].lerp(HEAD, smooth(min(1.0, s * 1.8))), lerp(6.0, 3.5, s), -0.115
for f in FR:
    t = T0 + f / FPS
    p, tg, fs, yf = cam_pose(t)
    u = t - TL
    if u > 0:                                                                    # the landing shakes the camera a little
        a = 0.010 * math.exp(-9 * u)
        p = p + V((math.sin(53 * t) * a, math.sin(41 * t + 1) * a * 0.5, math.sin(61 * t + 2) * a))
    cam.location = p; cam.rotation_euler = (tg - p).to_track_quat('-Z', 'Y').to_euler()
    v = (tg - p).normalized()
    cam_d.dof.focus_distance = max(0.05, (yf - p.y) / v.y) if abs(v.y) > 1e-6 else 10.0
    cam_d.dof.aperture_fstop = fs
    key(cam, f, loc=tuple(p), rot=tuple(cam.rotation_euler)); cam_d.dof.keyframe_insert('focus_distance', frame=f); cam_d.dof.keyframe_insert('aperture_fstop', frame=f)

# ── where the logo is on screen, frame by frame (the page lays the badges and the address out from this) ──
from bpy_extras.object_utils import world_to_camera_view
def px(p):
    c = world_to_camera_view(sc, cam, V(p)); return [round(c.x * 1920, 1), round((1 - c.y) * 1080, 1)]
track = {}
for f in FR:
    sc.frame_set(f)
    track[f] = {'tl': px((X(0), -0.07, Z(-82.34))), 'br': px((X(87.09), -0.07, Z(14.42))), 'word': px((X(114.96), -0.07, Z(14.42)))}
# the page reads it from the example's own blender/s3/out/track.json
TRACK = HERE.parents[2] / 'blender' / 's3' / 'out' / 'track.json'
TRACK.parent.mkdir(parents=True, exist_ok=True)
json.dump(track, open(TRACK, 'w'))

bright.cycles(sc, 128)
mode = args[0] if args else 'still'
c = sc.cycles
if os.environ.get('S3_CPU'): c.device = 'CPU'
if mode == 'still':
    fr = int(args[1]) if len(args) > 1 else 0
    sc.render.filepath = args[2] if len(args) > 2 else str(HERE / 'out' / 'still.png')
    sc.render.resolution_percentage = int(args[3]) if len(args) > 3 else 50
    c.samples = int(args[4]) if len(args) > 4 else 64
    sc.frame_set(fr); bpy.ops.render.render(write_still=True)
elif mode == 'sheet':
    out = Path(args[1]); out.mkdir(parents=True, exist_ok=True)
    sc.render.resolution_percentage = int(args[2]); c.samples = int(args[3])
    for fr in [int(a) for a in args[4:]]:
        sc.frame_set(fr); sc.render.filepath = str(out / f'{fr:04d}.png'); bpy.ops.render.render(write_still=True)
elif mode == 'save':
    sc.render.filepath = '//out/png/####'
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 's3.blend'))
