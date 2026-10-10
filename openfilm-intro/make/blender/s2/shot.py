"""Line 2: 它能把 Codex、Claude Code 或者任何一个 AI Agent 变成会做视频的剪辑师。
The agents as characters on a bright studio stage. Each one's mark on a black ceramic tile that lands like it has a
will of its own; Clawd, alive, hops in beside Codex and looks at it. On 变成 every tile sprouts a slate's two striped
clapsticks — it *is* a clapperboard now — and Clawd gets a director's beret; the sticks snap one by one on 会做视频的
and all together on 剪, everybody jumping at once. Film 5.433 → 12.433 is frames 0 → 209.
    blender -b -P shot.py -- still <frame> <out.png> [percent] [samples]
    blender -b -P shot.py -- sheet <dir> <percent> <samples> <frame> …
    blender -b -P shot.py -- save
"""
import bpy, bmesh, sys, os, math, json, mathutils
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import bright
from bright import srgb, mat, link, area

FPS, T0, T1 = 30, 5.433, 12.433
N = round((T1 - T0) * FPS)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def ss(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def out3(x): return 1 - (1 - clamp(x)) ** 3
def lerp(a, b, k): return a + (b - a) * k

sc = bright.reset(FPS, (0, N - 1))
bright.cyclorama()
bright.lights()

M = dict(
    tile=mat('tile', '#0e0e10', 0.30, coat=0.5, coat_rough=0.14),
    mark=mat('mark', '#f4f3f0', 0.32, coat=0.3, coat_rough=0.1),
    clawd=mat('clawd', '#c45a33', 0.38, coat=0.45, coat_rough=0.1, sss=0.02, sss_radius=(0.04, 0.012, 0.006)),
    eye=mat('eye', '#141414', 0.18, coat=1.0),
    felt=mat('felt', '#1d1d20', 0.9, sheen=0.6),
    hinge=mat('hinge', '#c2c4c8', 0.22, 1.0),
)
def stripes(name, angle):
    """slate-stick paint: black and white bands on the diagonal (the two sticks lean opposite ways: chevrons)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, math.radians(angle), 0)
    wv = nt.nodes.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.wave_profile = 'SAW'; wv.inputs['Scale'].default_value = 2.6; wv.inputs['Distortion'].default_value = 0
    rp = nt.nodes.new('ShaderNodeValToRGB'); rp.color_ramp.interpolation = 'CONSTANT'
    rp.color_ramp.elements[0].position = 0.0; rp.color_ramp.elements[0].color = (*srgb('#f2f1ed'), 1)
    rp.color_ramp.elements[1].position = 0.5; rp.color_ramp.elements[1].color = (*srgb('#141416'), 1)
    L(tc.outputs['Object'], mp.inputs['Vector']); L(mp.outputs['Vector'], wv.inputs['Vector']); L(wv.outputs['Fac'], rp.inputs['Fac']); L(rp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.3; b.inputs['Coat Weight'].default_value = 0.5
    return m
STR_TOP, STR_BOT = stripes('stripes_top', 40), stripes('stripes_bot', -40)

# ── geometry ──
TILE_W, TILE_H, TILE_D = 1.0, 1.0, 0.18
def rounded_tile(name):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co.x *= TILE_W; v.co.y *= TILE_D; v.co.z = v.co.z * TILE_H + TILE_H / 2
    edges = [e for e in bm.edges if abs((e.verts[0].co - e.verts[1].co).normalized().y) > 0.99]
    bmesh.ops.bevel(bm, geom=edges, offset=0.24, segments=14, profile=0.5, affect='EDGES')
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); me.materials.append(M['tile'])
    bv = o.modifiers.new('soft', 'BEVEL'); bv.width = 0.022; bv.segments = 4; bv.limit_method = 'ANGLE'
    o.modifiers.new('wn', 'WEIGHTED_NORMAL').keep_sharp = True
    for p in me.polygons: p.use_smooth = True
    return o

def svg_mark(name, path, size, clip=None):
    """the agent's own mark from its SVG, as a raised enamel inlay `size` across, in the XZ plane facing −Y"""
    before = set(bpy.data.objects); bpy.ops.import_curve.svg(filepath=str(path))
    curves = [o for o in bpy.data.objects if o not in before]
    for c in curves: c.data.dimensions = '2D'; c.data.fill_mode = 'BOTH'; c.data.extrude = 0; c.data.resolution_u = 24
    bpy.ops.object.select_all(action='DESELECT')
    for c in curves: c.select_set(True)
    bpy.context.view_layer.objects.active = curves[0]; bpy.ops.object.convert(target='MESH'); bpy.ops.object.join()
    o = bpy.context.active_object; o.name = name
    if clip:   # WorkBuddy's mark is drawn inside a circle: keep what is inside it
        before = set(bpy.data.objects); bpy.ops.import_curve.svg(filepath=str(clip))
        cc = [x for x in bpy.data.objects if x not in before][0]; cc.data.dimensions = '2D'; cc.data.fill_mode = 'BOTH'
        bpy.ops.object.select_all(action='DESELECT'); cc.select_set(True); bpy.context.view_layer.objects.active = cc; bpy.ops.object.convert(target='MESH')
        sol = cc.modifiers.new('s', 'SOLIDIFY'); sol.thickness = 1.0; sol.offset = 0
        bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
        s2 = o.modifiers.new('s', 'SOLIDIFY'); s2.thickness = 0.001; s2.offset = 0
        bo = o.modifiers.new('clip', 'BOOLEAN'); bo.operation = 'INTERSECT'; bo.object = cc; bo.solver = 'EXACT'
        bpy.ops.object.modifier_apply(modifier='s'); bpy.ops.object.modifier_apply(modifier='clip'); bpy.data.objects.remove(cc)
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.delete(bm, geom=[fc for fc in bm.faces if fc.normal.z < 0.5], context='FACES'); bm.to_mesh(o.data); bm.free()
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    xs = [v.co.x for v in o.data.vertices]; ys = [v.co.y for v in o.data.vertices]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2; k = size / max(max(xs) - min(xs), max(ys) - min(ys))
    for v in o.data.vertices: v.co.x = (v.co.x - cx) * k; v.co.y = (v.co.y - cy) * k; v.co.z = 0
    sol = o.modifiers.new('depth', 'SOLIDIFY'); sol.thickness = 0.02; sol.offset = 1     # outward: an inlay standing proud of the face
    bv = o.modifiers.new('round', 'BEVEL'); bv.width = 0.004; bv.segments = 2; bv.limit_method = 'ANGLE'
    o.data.materials.clear(); o.data.materials.append(M['mark'])
    for p in o.data.polygons: p.use_smooth = False
    o.rotation_euler = (math.radians(90), 0, 0)
    return o

def stick(name, m, length, h=0.13):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts: v.co.x = (v.co.x + 0.5) * length; v.co.y *= TILE_D * 0.92; v.co.z = (v.co.z + 0.5) * h
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me)); me.materials.append(m)
    bv = o.modifiers.new('b', 'BEVEL'); bv.width = 0.012; bv.segments = 3
    return o

ICONS = HERE.parent / 'icons'
# who, where they stand (x, and a little turn), when they land (film s), and how they land
ROW = [  # name, x, a little turn of its own (°), land, style
    ('codex', -0.625, 3, 6.04, 'drop'),
    ('gemini', -1.875, -3, 7.70, 'spin'),
    ('copilot', 1.875, 4, 7.86, 'wobble'),
    ('cursor', -3.125, -4, 8.02, 'tip'),
    ('opencode', 3.125, 3, 8.18, 'thud'),
    ('devin', -4.375, -5, 8.34, 'skid'),
    ('workbuddy', 4.375, 5, 8.50, 'hop'),
]
ARC = 0.06                                  # the row bends back at the ends (y = ARC·x²), each one turned to face us
def arc_y(x): return ARC * x * x
def face_yaw(x): return -math.degrees(math.atan2(x, 13.0 + arc_y(x)))
SPROUT = {'codex': 9.43, 'gemini': 9.50, 'copilot': 9.50, 'cursor': 9.57, 'opencode': 9.57, 'devin': 9.64, 'workbuddy': 9.64}
CLAP = {'codex': 9.97, 'gemini': 10.09, 'copilot': 10.21, 'cursor': 10.33, 'opencode': 10.45, 'devin': 10.57, 'workbuddy': 10.69}
TOGETHER = 10.89                     # 剪: every stick at once, and everybody jumps
items = {}
for name, x, yaw, land, style in ROW:
    root = link(bpy.data.objects.new(f'char_{name}', None))
    tile = rounded_tile(f'tile_{name}'); tile.parent = root
    mk = svg_mark(f'mark_{name}', ICONS / f'{name}.svg', 0.5 if name != 'opencode' else 0.38,
                  clip=(ICONS / 'workbuddy-clip.svg') if name == 'workbuddy' else None)
    mk.parent = root; mk.location = (0, -TILE_D / 2 + 0.002, TILE_H / 2)
    # the slate's two sticks on the tile's top edge: the lower one fixed, the upper one hinged at the left
    sticks = link(bpy.data.objects.new(f'sticks_{name}', None)); sticks.parent = root; sticks.location = (-TILE_W * 0.46, 0, TILE_H + 0.004)
    low = stick(f'low_{name}', STR_BOT, TILE_W * 0.92); low.parent = sticks
    hinge = link(bpy.data.objects.new(f'hinge_{name}', None)); hinge.parent = sticks; hinge.location = (0, 0, 0.135)
    top = stick(f'top_{name}', STR_TOP, TILE_W * 0.92); top.parent = hinge
    items[name] = dict(root=root, tile=tile, sticks=sticks, hinge=hinge, x=x, yaw=yaw, land=land, style=style)
os.makedirs(ICONS, exist_ok=True)
# each name sits right under its logo (s2.html): no marks on the floor

# ── Clawd: body, legs and eyelids apart, so it can tuck its legs in the air and blink ──
SPRITE = ['..XXXXXXXX..', '..XEXXXXEX..', 'XXXXXXXXXXXX', 'XXXXXXXXXXXX', '..XXXXXXXX..', '..XXXXXXXX..', '..X.X..X.X..', '..X.X..X.X..']
U = 0.1
def voxel_mesh(name, cells, mats):
    """cells: {(c, d, r)} filled (c across, d depth layer 0 = front, r up from the bottom); eyes: front faces of 'E' cells"""
    bm = bmesh.new(); vmap = {}
    def v(x, y, z):
        if (x, y, z) not in vmap: vmap[(x, y, z)] = bm.verts.new(((x - 6) * U, (y - 2) * U, z * U))
        return vmap[(x, y, z)]
    dirs = {(-1, 0, 0): [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], (1, 0, 0): [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
            (0, -1, 0): [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], (0, 1, 0): [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
            (0, 0, -1): [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)], (0, 0, 1): [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]}
    for (x, y, z), eye in cells.items():
        for (dx, dy, dz), quad in dirs.items():
            if (x + dx, y + dy, z + dz) in cells: continue
            f = bm.faces.new([v(x + a, y + b, z + c) for a, b, c in quad]); f.material_index = 1 if (eye and (dx, dy, dz) == (0, -1, 0)) else 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me))
    for m in mats: me.materials.append(m)
    bv = o.modifiers.new('bevel', 'BEVEL'); bv.width = U * 0.16; bv.segments = 3; bv.limit_method = 'ANGLE'
    o.modifiers.new('wn', 'WEIGHTED_NORMAL').keep_sharp = True
    for p in me.polygons: p.use_smooth = True
    return o
def depth_of(r, c):
    if r >= 6: return [0, 3]
    if c < 2 or c > 9: return [1, 2]
    return [0, 1, 2, 3]
H = len(SPRITE)
body_cells, leg_cells = {}, {}
for r, row in enumerate(SPRITE):
    for c, ch in enumerate(row):
        if ch == '.': continue
        for d in depth_of(r, c):
            z = H - 1 - r
            (leg_cells if r >= 6 else body_cells)[(c, d, z)] = (ch == 'E' and d == min(depth_of(r, c)))
claw = link(bpy.data.objects.new('clawd', None))
cbody = voxel_mesh('clawd_body', body_cells, [M['clawd'], M['eye']]); cbody.parent = claw
legs = voxel_mesh('clawd_legs', leg_cells, [M['clawd'], M['eye']]); legs.parent = claw
# eyelids: thin orange plates over the two eyes, closed when scaled up
lids = []
for c in (3, 8):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for vv in bm.verts: vv.co.x *= U * 1.04; vv.co.y *= 0.012; vv.co.z = (vv.co.z - 0.5) * U * 1.04     # hangs down from its top edge
    me = bpy.data.meshes.new(f'lid{c}'); bm.to_mesh(me); bm.free(); lid = link(bpy.data.objects.new(f'lid{c}', me)); me.materials.append(M['clawd']); lid.parent = claw
    lid.location = ((c - 6 + 0.5) * U, -2 * U - 0.007, (H - 1) * U + 0.002)
    lids.append(lid)
beret = link(bpy.data.objects.new('beret', bpy.data.meshes.new('beret')))
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.36); bmesh.ops.scale(bm, vec=(1.0, 0.95, 0.30), verts=bm.verts)
bm.to_mesh(beret.data); bm.free(); beret.data.materials.append(M['felt'])
for p in beret.data.polygons: p.use_smooth = True
stem = link(bpy.data.objects.new('beret_stem', bpy.data.meshes.new('stem')))
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.022, radius2=0.012, depth=0.07); bm.to_mesh(stem.data); bm.free()
stem.data.materials.append(M['felt']); stem.parent = beret; stem.location = (0, 0, 0.12)

# ── motion ──
G = 30.0
def fall(t, tl, h0, bounce=0.26, n=3):
    """height above the floor: free fall from h0 landing at tl, then n bounces losing (1 − bounce) of their speed"""
    tf = math.sqrt(2 * h0 / G)
    if t < tl - tf: return None                      # not yet in the air above the frame
    if t <= tl: d = tl - t; return 0.5 * G * d * d
    v = G * tf * bounce; tt = t - tl
    for _ in range(n):
        tb = 2 * v / G
        if tt < tb: return v * tt - 0.5 * G * tt * tt
        tt -= tb; v *= 0.32
    return 0.0
def squash(t, tl, amt=0.17):
    if t < tl: return 1 + 0.06 * max(0, 1 - (tl - t) / 0.12)
    d = t - tl; return 1 - amt * math.exp(-13 * d) * math.cos(26 * d)
CORNER = 0.24                       # a tile's corners are rounded this much: it rocks on them, never into the floor
def on_corner(phi):
    """where a tile's foot is (along its width, up) as it leans phi about its own y (+ lifts its left side), rolling on a corner"""
    if abs(phi) < 1e-9: return 0.0, 0.0
    cx = math.copysign(TILE_W / 2 - CORNER, phi)
    return cx + CORNER * phi - cx * math.cos(phi) - CORNER * math.sin(phi), CORNER + cx * math.sin(phi) - CORNER * math.cos(phi)
LEAN = {'wobble': 0.10, 'tip': -0.30}           # how a tile comes down leaning (rad): on one corner first
SKID = 0.42                                     # Devin comes down moving and slides the last of it onto its mark
BOUNCE = (0.30,)                    # how high a tile comes back up (m): one bounce, then it stays — more pull the eye around
SQUASH = (0.24, 0.10)               # how much the first contact squashes it, and the landing after the bounce
CONTACT = 0.06                      # how long a contact lasts (s): the squash and the push off the floor
SCALE = {'thud': 0.55, 'wobble': 0.7, 'tip': 0.6, 'skid': 0.6}   # heavier or off-balance tiles bounce lower
def bounce(u, k=1.0, amt=1.0):
    """after first touching the floor at u = 0: (height, squash) — squashed on each contact, stretched as it leaves
    the floor and as it falls back, each bounce lower, then settled"""
    for h, a in zip(BOUNCE, SQUASH):
        h *= k; a *= amt
        if u < CONTACT: return 0.0, 1 - a * math.sin(math.pi * u / CONTACT)
        u -= CONTACT
        v = math.sqrt(2 * G * h); air = 2 * v / G
        if u < air:
            p = u / air
            return v * u - 0.5 * G * u * u, 1 + 0.45 * a * abs(1 - 2 * p) ** 1.5
        u -= air
    a = SQUASH[-1] * amt                                  # down again: a softer squash, and it is still
    if u < CONTACT: return 0.0, 1 - a * math.sin(math.pi * u / CONTACT)
    u -= CONTACT
    return 0.0, 1 - 0.02 * amt * math.exp(-12 * u) * math.cos(30 * u)
def tile_pose(t, st, tl):
    """a 1 m tile falling onto its mark and landing its own way: (shift along the row, height, lean, turn°, squash);
    None while it is still above the frame. It bounces like it means it: squash on the floor, stretch off it, three
    one bounce and it stays, its own character on top (a spin, a rock on a corner, a slide)"""
    h0 = 6.0 if tl < 7 else 9.0
    tf = math.sqrt(2 * h0 / G); u = t - tl
    if u < -tf: return None
    turn = 360 * (1 - smooth(prog(t, tl - 0.45, tl))) if st == 'spin' else 0.0
    if u < 0:   # falling: stretched by its speed
        dx = -SKID - 2 * SKID / 0.32 * -u if st == 'skid' else 0.0
        return dx, 0.5 * G * u * u, LEAN.get(st, 0.0), turn, 1 + 0.10 * smooth(1 + u / 0.15)
    k = SCALE.get(st, 1.0)
    z, sq = bounce(u, k, 1.25 if st == 'thud' else 1.0)
    phi = 0.0; dx = 0.0
    if st == 'wobble': phi = LEAN['wobble'] * math.exp(-4 * u) * math.cos(13 * u)          # off its corner, rocking
    if st == 'tip': phi = LEAN['tip'] * math.exp(-5 * u) * math.cos(12 * u)                # over its corner onto its foot
    if st == 'skid':
        kk = prog(u, 0, 0.32); dx = -SKID * (1 - kk) ** 2                                  # the slide stops it
        phi = 0.055 * math.sin(math.pi * kk) if u < 0.32 else -0.02 * math.exp(-8 * (u - 0.32)) * math.sin(18 * (u - 0.32))
    return dx, z, phi, turn, sq
def jump(t, t0, h=0.55, dur=0.36):
    """everybody's hop on 剪: crouch, up, down, squash"""
    if t < t0 - 0.08 or t > t0 + dur + 0.3: return 0.0, 1.0
    if t < t0: return 0.0, 1 - 0.10 * smooth((t - (t0 - 0.08)) / 0.08)
    if t < t0 + dur: u = (t - t0) / dur; return 4 * h * u * (1 - u), 1 + 0.08 * math.sin(math.pi * u)
    return 0.0, squash(t, t0 + dur, 0.12)
def clap_angle(t, tc):
    """the upper stick: opens and snaps shut at tc, and again all together at TOGETHER (degrees)"""
    def snap(t, a, b):
        if t < a: return 0.0
        if t < b: return 36 * smooth((t - a) / 0.12)
        d = t - b
        return 36 * max(0, 1 - d / 0.05) if d < 0.05 else 3.5 * math.exp(-18 * (d - 0.05)) * abs(math.sin(40 * (d - 0.05)))
    if t < TOGETHER - 0.26: return snap(t, tc - 0.18, tc)
    return snap(t, TOGETHER - 0.20, TOGETHER)

def key(o, f, loc=None, rot=None, scale=None):
    if loc is not None: o.location = loc; o.keyframe_insert('location', frame=f)
    if rot is not None: o.rotation_euler = rot; o.keyframe_insert('rotation_euler', frame=f)
    if scale is not None: o.scale = scale; o.keyframe_insert('scale', frame=f)

CLAWD_X = 0.625
HOPS = [(6.42, 6.68, 3.6, 2.15, 0.62), (6.68, 6.96, 2.15, CLAWD_X, 0.55)]     # start, land, from x, to x, height
def clawd_pose(t):
    """(x, z, sx, sz, yaw°, legs tucked 0..1, lids closed 0..1)"""
    x, z, s, tuck = HOPS[0][2], 0.0, 1.0, 0.0
    if t < HOPS[0][0] - 0.08: x = 6.0                                     # off frame to the right
    for a, b, x0, x1, h in HOPS:
        if a - 0.08 <= t < a: s = 1 - 0.12 * smooth((t - (a - 0.08)) / 0.08); x = x0  # crouch before each hop
        if a <= t < b:
            k = (t - a) / (b - a); x = x0 + (x1 - x0) * smooth(k) * 0.85 + (x1 - x0) * k * 0.15
            z = 4 * h * k * (1 - k); s = 1 + 0.10 * math.sin(math.pi * k); tuck = math.sin(math.pi * k)
        if t >= b: x = x1
    if t >= HOPS[-1][1]:
        s = squash(t, HOPS[-1][1], 0.16)
    j, js = jump(t, TOGETHER, 0.62)
    z += j; s *= js; tuck = max(tuck, math.sin(math.pi * clamp((t - TOGETHER) / 0.36)) if TOGETHER <= t < TOGETHER + 0.36 else 0.0)
    # it looks at Codex when it lands, back to us; and again at the very end
    yaw = -24 * smooth(prog(t, 7.05, 7.30)) * (1 - smooth(prog(t, 7.75, 8.0))) - 10 * smooth(prog(t, 11.75, 12.0))
    blink = 0.0
    for b0 in (7.42, 9.05, 11.55, 12.15):
        if b0 <= t < b0 + 0.14: blink = math.sin(math.pi * (t - b0) / 0.14)
    return x, z, 1 + (1 - s) * 0.5, s, yaw, tuck, blink

FR = range(N)
for f in FR:
    t = T0 + f / FPS
    for i, (name, it) in enumerate(items.items()):
        st = it['style']; land = it['land']
        pose = tile_pose(t, st, land)
        j, js = jump(t, TOGETHER + 0.015 * i, 0.55)
        js *= 1 + 0.014 * math.sin(math.tau * (t - land) / 1.25 + i * 1.7) * smooth(prog(t, land + 0.5, land + 1.0))
        if pose is None: dx, z, phi, turn, sq = 0.0, 30.0, 0.0, 0.0, 1.0
        else: dx, z, phi, turn, sq = pose
        yaw = math.radians(it['yaw'] + face_yaw(it['x']) + turn)
        fx, fz = on_corner(phi)
        loc = (it['x'] + dx + fx * math.cos(yaw), arc_y(it['x']) + fx * math.sin(yaw), z + fz + j)
        key(it['root'], f, loc=loc, rot=(0, phi, yaw), scale=(1 + (1 - sq * js) * 0.3, 1, sq * js))
        # the sticks: pop up from the tile's top on 变成, then clap
        sp = prog(t, SPROUT[name], SPROUT[name] + 0.22)
        k = 0.0 if sp <= 0 else (1 + 0.25 * math.sin(math.pi * sp) * (1 - sp)) * smooth(sp * 1.4)
        key(it['sticks'], f, scale=(max(k, 0.001), max(k, 0.001), max(k, 0.001)))
        key(it['hinge'], f, rot=(0, -math.radians(clap_angle(t, CLAP[name])), 0))
    x, z, sx, sz, yaw, tuck, blink = clawd_pose(t)
    breathe = 1 + 0.02 * math.sin(math.tau * (t - 6.96) / 1.1) * smooth(prog(t, 7.3, 7.8)); sz *= breathe; sx /= breathe ** 0.5
    key(claw, f, loc=(x, arc_y(x), z), rot=(0, 0, math.radians(yaw + face_yaw(x))), scale=(sx, sx, sz))
    key(legs, f, loc=(0, 0, 0.6 * tuck * U), scale=(1, 1, 1 - 0.45 * tuck))
    for lid in lids: key(lid, f, scale=(1, 1, max(0.001, blink)))
    # the beret drops onto its head on 变成, and rides the jump
    bz = fall(t, 9.58, 5.0, 0.04, 1)
    head = (H * U) * sz + z
    key(beret, f, loc=(x + 0.06, arc_y(x) - 0.02, 30 if bz is None else head + 0.025 + bz), rot=(math.radians(-12), math.radians(16), math.radians(yaw)), scale=(1, 1, squash(t, 9.58, 0.2) if t > 9.5 else 1))

# a warm flash of light on 剪
flash = area('flash', (0, -9.0, 4.0), (0, 0, 0.8), 0, '#fff3e6', (8.0, 4.0))
for f in FR:
    t = T0 + f / FPS; d = t - TOGETHER
    flash.data.energy = 2600 * math.exp(-7 * d) if d >= 0 else 0.0; flash.data.keyframe_insert('energy', frame=f)

# ── camera ──
cam_d = bpy.data.cameras.new('cam'); cam_d.lens = 50; cam_d.sensor_fit = 'HORIZONTAL'; cam_d.sensor_width = 36; cam_d.clip_start = 0.05
cam = link(bpy.data.objects.new('cam', cam_d)); sc.camera = cam
cam_d.dof.use_dof = True; cam_d.dof.aperture_blades = 7
K = [  # t, location, target
    (5.433, (-0.50, -5.3, 1.02), (-0.58, 0, 0.56)),
    (6.70, (-0.25, -5.4, 1.00), (-0.33, 0, 0.56)),
    (7.25, (0.00, -5.9, 1.05), (0.00, 0, 0.58)),      # Codex and Clawd, side by side
    (8.75, (0.00, -14.0, 2.05), (0.00, 0.3, 1.45)),   # the whole cast, low in frame: the title goes above
    (10.80, (0.00, -13.5, 2.00), (0.00, 0.3, 1.47)),
    (12.433, (0.06, -12.8, 1.92), (0.03, 0.3, 1.40)), # leaning in on the jump's aftermath, everybody still in frame
]
def spline(keys, t):
    """keys: [(t, vector)]; cubic Hermite with slopes from the neighbouring secants (zero at both ends)"""
    ts = [k[0] for k in keys]; vs = [mathutils.Vector(k[1]) for k in keys]
    if t <= ts[0]: return vs[0].copy()
    if t >= ts[-1]: return vs[-1].copy()
    sl = []
    for i in range(len(ts)):
        if i == 0 or i == len(ts) - 1: sl.append(mathutils.Vector((0, 0, 0)))
        else: sl.append(((vs[i + 1] - vs[i]) / (ts[i + 1] - ts[i]) + (vs[i] - vs[i - 1]) / (ts[i] - ts[i - 1])) * 0.5)
    for i in range(len(ts) - 1):
        if t <= ts[i + 1]:
            h = ts[i + 1] - ts[i]; u = (t - ts[i]) / h
            return (2 * u ** 3 - 3 * u ** 2 + 1) * vs[i] + (u ** 3 - 2 * u ** 2 + u) * h * sl[i] + (-2 * u ** 3 + 3 * u ** 2) * vs[i + 1] + (u ** 3 - u ** 2) * h * sl[i + 1]
for f in FR:
    t = T0 + f / FPS
    p = spline([(k[0], k[1]) for k in K], t); tg = spline([(k[0], k[2]) for k in K], t)
    cam.location = p; cam.rotation_euler = (tg - p).to_track_quat('-Z', 'Y').to_euler()
    cam_d.dof.focus_distance = (mathutils.Vector((tg.x, 0.25, 0.6)) - p).length; cam_d.dof.aperture_fstop = lerp(3.2, 2.8, smooth(prog(t, 7.0, 8.4)))
    key(cam, f, loc=tuple(p), rot=tuple(cam.rotation_euler)); cam_d.dof.keyframe_insert('focus_distance', frame=f); cam_d.dof.keyframe_insert('aperture_fstop', frame=f)

# ── where each name goes on screen, frame by frame (the page lays the labels and the title out from this) ──
from bpy_extras.object_utils import world_to_camera_view
def px(p):
    c = world_to_camera_view(sc, cam, mathutils.Vector(p)); return [round(c.x * 1920, 1), round((1 - c.y) * 1080, 1)]
track = {}
for f in FR:
    sc.frame_set(f)
    row = {n: {'foot': px((it['x'], arc_y(it['x']) - TILE_D / 2, 0)), 'top': px((it['x'], arc_y(it['x']), TILE_H + 0.25))} for n, it in items.items()}
    row['clawd'] = {'foot': px((claw.location.x, arc_y(claw.location.x) - 0.2, 0)), 'top': px((claw.location.x, arc_y(claw.location.x), 1.2))}
    track[f] = row
# the page reads it from the example's own blender/s2/out/track.json
TRACK = HERE.parents[2] / 'blender' / 's2' / 'out' / 'track.json'
TRACK.parent.mkdir(parents=True, exist_ok=True)
json.dump(track, open(TRACK, 'w'))

bright.cycles(sc, 128)
mode = args[0] if args else 'still'
c = sc.cycles
if os.environ.get('S2_CPU'): c.device = 'CPU'
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
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 's2.blend'))
