"""我做了一个: Premiere comes off the glass, piece by piece, and every piece is rebuilt as OpenFilm.

Each element of the Premiere replica (pr/out/pieces: rendered alone, so nothing is left behind when it lifts) is a
thin glass slab: its front is Premiere's pixels, its back is the place it takes in OpenFilm (the hero recording at
7.9 s, or a clean plate of OpenFilm's empty panels). Many become few: six tracks become three, fifty clips ten, the
knobs of Effect Controls the agent's conversation. One piece per target turns over and lands there; the rest fly
into it and are gone.

Timing (film seconds, 30 fps): the spinning wait cursor pops at LIFT (我), a wave runs out from it and lifts each
piece as it passes; the panels open like doors on the light behind; the pieces turn over and land left to right
(通用的视频); everything is in place, still, at LAND. All motion is a pure function of t, keyed every frame."""
import bpy, bmesh, json, math, mathutils
from pathlib import Path

HERE = Path(__file__).parent
PIECES = HERE / 'pr' / 'out' / 'pieces'
FPS = 30
LIFT, LAND = 2.22, 3.46
CURSOR = tuple(json.loads((PIECES / 'meta.json').read_text())['cursor'])   # where the wait cursor sits (Premiere's Play-Stop toggle)
THICK = 0.0006                          # a slab's thickness (m)
D1 = 0.3978                             # the camera's distance from the glass at LIFT (shot.py sets it)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def smooth(x): x = clamp(x); return x * x * (3 - 2 * x)
def inout(x): x = clamp(x); return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
def out3(x): return 1 - (1 - clamp(x)) ** 3
def out5(x): return 1 - (1 - clamp(x)) ** 5
def rnd(i): v = math.sin(i * 127.1 + 311.7) * 43758.5453; return v - math.floor(v)

# ── where OpenFilm's pieces are, in the hero frame (1920 × 1080): the desktop app, dark, as make/recordings/rec-s1.mjs recorded it
#    and make/recordings/s1-layout.py measured it ── tex: 'hero' or 'plate'
_L = json.loads((HERE / 'tex' / 'hero_layout.json').read_text())
T = {k: (r, tex) for k, (r, tex) in _L['T'].items()}
LANE = _L['lane']                         # OpenFilm's timeline, start to end of the trailer (px)
PANELS = {'top', 'media', 'viewer', 'insp', 'chat', 'tl'}

def mapping(pieces):
    """Premiere piece id → (OpenFilm target, primary?). Primary pieces turn over into the target; the others fold into it."""
    M = {}
    def to(src, dst, primary=True): M[src] = (dst, primary)
    to('app', 'top'); to('mac', 'top', False)
    to('ec', 'chat'); to('prog', 'viewer'); to('side', 'insp'); to('proj', 'media'); to('tl', 'tl')
    to('tools', 'tl', False); to('meter', 'tl', False)
    # Effect Controls → the conversation: the parameter one would drag becomes what one asks for
    # Effect Controls becomes the conversation: the panel turns over into the chat, whole; every knob in it folds away
    for r in ('head', 'foot', 'mini') + tuple(f'r_{k}' for k in ('video', 'motion', 'pos', 'scale', 'scalew', 'uni', 'rot', 'anchor', 'flick', 'opfx', 'mask', 'op', 'blend', 'time', 'text')):
        to(f'ec_{r}', 'chat', False)
    # Program → the viewer
    to('prog_pic', 'pic'); to('prog_bar', 'vbar'); to('prog_scrub', 'vbar', False); to('prog_tp', 'vbar', False)
    # Info and the stacked panels → the inspector's
    to('side_info', 'insp_c')
    for i in range(9): to(f'side_s{i}', 'insp_c', False)
    # Project → the media panel
    to('proj_path', 'm_head'); to('proj_search', 'm_head', False); to('proj_foot', 'media', False)
    for src, dst in (('proj_t0', 't_video'), ('proj_t1', 't_audio'), ('proj_t2', 't_end'), ('proj_t3', 't_title'), ('proj_t4', 't_track'), ('proj_t5', 't_km')):
        to(src, dst)
    to('proj_t6', 't_audio', False); to('proj_t7', 't_video', False)
    # tools → the timeline's tools
    for src, dst in (('tool_sel', 'o_sel'), ('tool_track', 'o_undo'), ('tool_ripple', 'o_redo'), ('tool_slip', 'o_time'), ('tool_razor', 'o_razor')):
        to(src, dst)
    for t in ('pen', 'rect', 'hand', 'type'): to(f'tool_{t}', 'o_razor', False)
    to('tl_tc', 'o_zoom'); to('tl_tbar', 'o_zoom', False); to('tl_ruler', 'ruler'); to('tl_ph', 'ruler', False)
    to('tl_hsb', 'tl', False); to('tl_vsb0', 'tl', False); to('tl_vsb1', 'tl', False)
    for m in ('meter_l', 'meter_r', 'meter_db', 'meter_s0', 'meter_s1'): to(m, 'o_zoom', False)
    to('tl_hV3', 'h_P1'); to('tl_hV1', 'h_V1'); to('tl_hA1', 'h_A1')
    to('tl_hV2', 'h_P1', False); to('tl_hA2', 'h_A1', False); to('tl_hA3', 'h_A1', False); to('tl_hMix', 'h_A1', False)
    # clips: V3 → P1, V1 → V1 (V2 folds in), A1 → A1 (A2, A3 fold in); the clip nearest each new clip's place turns over
    clips = [p for p in pieces if p['id'].startswith('c_')]
    lane = lambda p: p['id'].split('_')[1]
    cx = lambda r: (r[0] + r[2]) / 2
    for dl, srcl, extra in (('P1', 'V3', []), ('V1', 'V1', ['V2']), ('A1', 'A1', ['A2', 'A3'])):
        dsts = [k for k in T if k.startswith(dl + '_')]
        # Premiere's lane runs 592 → 1542, OpenFilm's LANE: compare positions as fractions of each
        fp = lambda p: (cx(p['r']) - 592) / (1542 - 592)
        fd = lambda d: (cx(T[d][0]) - LANE[0]) / (LANE[1] - LANE[0])
        used = set()
        for d in dsts:
            pool = [p for p in clips if lane(p) == srcl and p['id'] not in used and (p['r'][2] - p['r'][0]) > 20]
            best = min(pool, key=lambda p: abs(fp(p) - fd(d)))
            used.add(best['id']); to(best['id'], d)
        for p in clips:
            if p['id'] in used or (lane(p) != srcl and lane(p) not in extra): continue
            d = min(dsts, key=lambda d: abs(fp(p) - fd(d)))
            to(p['id'], d, False)
    return M

# ── materials ──
def face_material(name, image_path):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(image_path), check_existing=True); tex.interpolation = 'Cubic'
    tex.extension = 'CLIP'
    em = nt.nodes.new('ShaderNodeEmission'); nt.links.new(tex.outputs['Color'], em.inputs['Color'])
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    # object colour: r = glint (the room reflected in the glass while it is in the air), a = how much is left of it
    sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(oi.outputs['Color'], sep.inputs['Color'])
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.35
    fr = nt.nodes.new('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.5
    k = nt.nodes.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; nt.links.new(fr.outputs[0], k.inputs[0]); nt.links.new(sep.outputs['Red'], k.inputs[1])
    k2 = nt.nodes.new('ShaderNodeMath'); k2.operation = 'MULTIPLY'; k2.inputs[1].default_value = 0.35; nt.links.new(k.outputs[0], k2.inputs[0]); k = k2
    add = nt.nodes.new('ShaderNodeMixShader'); nt.links.new(k.outputs[0], add.inputs[0]); nt.links.new(em.outputs[0], add.inputs[1]); nt.links.new(gl.outputs[0], add.inputs[2])
    a = nt.nodes.new('ShaderNodeMath'); a.operation = 'MULTIPLY'; nt.links.new(tex.outputs['Alpha'], a.inputs[0]); nt.links.new(oi.outputs['Alpha'], a.inputs[1])
    # a picture is only seen from outside the slab: from inside (through a clear part of the other face) it is not there
    geo = nt.nodes.new('ShaderNodeNewGeometry'); front = nt.nodes.new('ShaderNodeMath'); front.operation = 'SUBTRACT'; front.inputs[0].default_value = 1.0
    nt.links.new(geo.outputs['Backfacing'], front.inputs[1])
    a2 = nt.nodes.new('ShaderNodeMath'); a2.operation = 'MULTIPLY'; nt.links.new(a.outputs[0], a2.inputs[0]); nt.links.new(front.outputs[0], a2.inputs[1]); a = a2
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(a.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(add.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return m

def edge_material():
    m = bpy.data.materials.new('slab_edge'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.010, 0.011, 0.013, 1); b.inputs['Roughness'].default_value = 0.55; b.inputs['Coat Weight'].default_value = 0.0
    b.inputs['Specular IOR Level'].default_value = 0.2
    oi = nt.nodes.new('ShaderNodeObjectInfo'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(oi.outputs['Alpha'], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    return m

def slab_mesh(name, back_rect):
    """A unit slab (x: width, y: thickness, z: height): front (−Y) shows its own picture 0..1; back (+Y) the target's
    crop of OpenFilm, mirrored in u so it reads right once the slab has turned over about Z."""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    uv = bm.loops.layers.uv.new('UVMap')
    u0, v0, u1, v1 = back_rect[0] / 1920, 1 - back_rect[3] / 1080, back_rect[2] / 1920, 1 - back_rect[1] / 1080
    for f in bm.faces:
        n = f.normal
        if n.y < -0.5: f.material_index = 0
        elif n.y > 0.5: f.material_index = 1
        else: f.material_index = 2
        for loop in f.loops:
            x, z = loop.vert.co.x + 0.5, loop.vert.co.z + 0.5
            if f.material_index == 0: loop[uv].uv = (x, z)
            elif f.material_index == 1: loop[uv].uv = (u0 + (1 - x) * (u1 - u0), v0 + z * (v1 - v0))
            else: loop[uv].uv = (0, 0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me

STRIPS = 40                               # the background turns over in this many vertical slats

def build(col, screen_center, screen_w, hero_mat, plate_mat):
    """The slabs, parented to an empty at the screen's centre: local X right, local Z up, local −Y toward the viewer.
    Premiere's panels (everything with nothing above it) are one background, cut into slats that turn over into
    OpenFilm's empty panels; every element on them is a slab of its own that flies to its place in OpenFilm."""
    pieces = json.loads((PIECES / 'pieces.json').read_text())
    M = mapping(pieces)
    k = screen_w / 1920.0
    root = bpy.data.objects.new('ui', None); col.objects.link(root); root.location = screen_center
    edge = edge_material()
    out = []
    bg = face_material('pr_bg', HERE / 'tex' / 'pr_bg.png')
    w = 1920 / STRIPS
    for i in range(STRIPS):
        rect = [i * w, 0, (i + 1) * w, 1080]
        me = slab_mesh(f'strip{i}', rect)
        # the front shows its own column of Premiere's background
        uvl = me.uv_layers[0]
        for poly in me.polygons:
            if poly.material_index != 0: continue
            for li in poly.loop_indices:
                u, v = uvl.data[li].uv
                uvl.data[li].uv = ((i + u) / STRIPS, v)
        me.materials.append(bg); me.materials.append(plate_mat); me.materials.append(edge)
        o = bpy.data.objects.new(f'strip{i}', me); col.objects.link(o); o.parent = root; o.visible_shadow = False
        out.append({'o': o, 'id': f'strip{i}', 'box': rect, 'dst': None, 'rect': rect, 'primary': True, 'strip': True, 'seed': i * 3.7 + 1, 'k': k, 'level': 0})
    for i, p in enumerate(pieces):
        if p['parent'] is None: continue
        if p['id'] not in M: raise KeyError(f"no OpenFilm place for {p['id']}")
        dst, primary = M[p['id']]
        rect, tex = T[dst]
        me = slab_mesh('slab_' + p['id'], rect)
        me.materials.append(face_material('pr_' + p['id'], PIECES / f"{p['id']}.png"))
        me.materials.append(hero_mat if tex == 'hero' else plate_mat)
        me.materials.append(edge)
        o = bpy.data.objects.new('slab_' + p['id'], me); col.objects.link(o); o.parent = root
        o.visible_shadow = False
        out.append({'o': o, 'id': p['id'], 'box': p['box'], 'dst': dst, 'rect': rect, 'primary': primary, 'strip': False, 'seed': i * 7.31 + 3, 'k': k, 'level': 1})
    return root, out

# ── the motion ──
def landing(fx):
    """When OpenFilm's pieces land at x (0..1 across the screen): a wave from left to right."""
    return 2.98 + 0.46 * fx

def strip_window(cx):
    """When the slat at x turns over: done just before the pieces above it land, so no white stands empty."""
    end = landing(cx / 1920.0) - 0.08
    return end - 0.37, end

def pose(s, t):
    """(location (local, m), rotation (rad), scale (m), glint, alpha, shown) of a slab at time t."""
    k = s['k']; b = s['box']; r = s['rect']
    sx, sy, sw, sh = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, b[2] - b[0], b[3] - b[1]
    dx, dy, dw, dh = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, r[2] - r[0], r[3] - r[1]
    seed = s['seed']
    base = THICK / 2 + 0.0004 + s['level'] * (THICK + 0.0005)
    c = (D1 - base) / D1
    if s['strip']:
        t0, t1 = strip_window(sx)
        e = inout(prog(t, t0, t1))
        turning = math.sin(math.pi * e)
        z = 5.0 * turning                                       # it stands off the glass a hair while it turns
        loc = ((sx - 960) * k * c, -(base + z * k), -(sy - 540) * k * c)
        # flat, the slats meet edge to edge and have no thickness to show; only turning do they part and catch light
        thick = THICK * turning + 0.00002
        return loc, (0.0, 0.0, math.pi * e), ((sw - 1.2 * turning) * k * c, thick, sh * k * c), 0.14 * turning, 1.0, t >= LIFT
    # the wave from the cursor: it reaches a piece's centre at 2600 px/s and lifts it off the glass
    dist = math.hypot(sx - CURSOR[0], sy - CURSOR[1])
    leave = LIFT + 0.03 + dist / 3600.0
    a = out3(prog(t, leave, leave + 0.45))
    # px toward the viewer: an exploded view of Premiere (rows and panels' contents stay near their panel)
    depth = (28 + 60 * rnd(seed + 2)) if s['id'].startswith(('ec_', 'side_', 'tool_')) else (70 + 190 * rnd(seed + 2))
    spread = 1.0 + 0.07 * a
    x, y = 960 + (sx - 960) * spread, 540 + (sy - 540) * spread
    z = depth * a
    rx = (rnd(seed + 3) - 0.5) * 0.26 * a; ry = (rnd(seed + 4) - 0.5) * 0.10 * a; rz = (rnd(seed + 5) - 0.5) * 0.20 * a
    if s['id'].startswith(('ec_', 'side_')): rx *= 0.3; rz *= 0.3; ry *= 0.3        # long rows barely tip
    drift = a * (1 - prog(t, 2.62, 2.9))
    x += math.sin(t * 2.1 + seed) * 5 * drift; y += math.cos(t * 1.7 + seed) * 4 * drift; z += math.sin(t * 2.6 + seed * 2) * 6 * drift
    # the flight: left to right across OpenFilm's layout, an arc toward the viewer, turning over on the way
    fx = dx / 1920.0
    fb = min(LAND - 0.01, landing(fx) + 0.03 * rnd(seed + 6))
    # big pieces turn over more slowly: a large bright face spun fast smears into a glow under motion blur
    big = clamp((sw * sh) / (680.0 * 382.0))
    fa = fb - (0.52 + 0.34 * big) - (0.08 if not s['primary'] else 0.0)
    f = prog(t, fa, fb); e = inout(f)
    w, h = sw, sh; glint = 0.40 * a; alpha = 1.0; flip = 0.0
    if f > 0:
        if s['primary']:
            x = x + (dx - x) * e; y = y + (dy - y) * e
            z = z * (1 - e) + math.sin(math.pi * e) * (90 + 80 * rnd(seed + 7))
            rx *= 1 - e; ry *= 1 - e; rz *= 1 - e
            flip = math.pi * e
            m = smooth((e - 0.3) / 0.4)                       # it changes size while edge-on
            w = sw + (dw - sw) * m; h = sh + (dh - sh) * m
        else:
            g = out3(prog(t, fa, fa + 0.36))
            x = x + (dx - x) * g; y = y + (dy - y) * g
            z = z * (1 - g) + math.sin(math.pi * g) * 60 + 20 * g
            sc = 1 - 0.8 * g; w = sw * sc; h = sh * sc
            flip = 0.55 * math.sin(math.pi * g) * (1 if rnd(seed + 8) > 0.5 else -1)
            alpha = 1 - smooth(prog(t, fa + 0.12, fa + 0.34))
    thick = THICK
    if s['primary']:
        settle = prog(t, fb - 0.10, fb + 0.04); glint *= 1 - settle
        thick = THICK * (1 - settle) + 0.00002 * settle          # landed, it is a picture again: no edge to see
        if f >= 1: z = 0.0
    loc = ((x - 960) * k * c, -(base + max(z, 0.0) * k), -(y - 540) * k * c)
    return loc, (rx, 0.0, rz + flip), (max(w, 0.5) * k * c, thick, max(h, 0.5) * k * c), glint, alpha, t >= LIFT

def bulk_keys(idb, path, frames, values, interpolation='LINEAR'):
    """Key one property (vector or scalar) on every frame at once, through the f-curves (far faster than keyframe_insert)."""
    import bpy
    values = list(values); n = len(values[0]) if isinstance(values[0], (tuple, list)) else 1
    ad = idb.animation_data or idb.animation_data_create()
    if ad.action is None: ad.action = bpy.data.actions.new(f'{idb.name}_act')
    act = ad.action
    for i in range(n):
        if hasattr(act, 'fcurve_ensure_for_datablock'): fc = act.fcurve_ensure_for_datablock(idb, path, index=i)
        else: fc = act.fcurves.new(path, index=i)
        fc.keyframe_points.clear()
        fc.keyframe_points.add(len(frames))
        co = []
        for fr, v in zip(frames, values): co += [fr, v[i] if n > 1 else v]
        fc.keyframe_points.foreach_set('co', co)
        fc.keyframe_points.foreach_set('interpolation', [{'CONSTANT': 0, 'LINEAR': 1, 'BEZIER': 2}[interpolation]] * len(frames))
        fc.update()

def animate(slabs, frames):
    frames = list(frames)
    for s in slabs:
        o = s['o']
        P = [pose(s, fr / FPS) for fr in frames]
        bulk_keys(o, 'location', frames, [p[0] for p in P])
        bulk_keys(o, 'rotation_euler', frames, [p[1] for p in P])
        bulk_keys(o, 'scale', frames, [p[2] for p in P])
        bulk_keys(o, 'color', frames, [(p[3], 0.0, 0.0, p[4] if p[5] else 0.0) for p in P])
        bulk_keys(o, 'hide_render', frames, [float((not p[5]) or p[4] <= 0.002) for p in P], 'CONSTANT')

def animate_slow(slabs, frames):
    for s in slabs:
        o = s['o']
        for fr in frames:
            t = fr / FPS
            loc, rot, size, glint, alpha, shown = pose(s, t)
            o.location = loc; o.rotation_euler = rot; o.scale = size
            o.color = (glint, 0, 0, alpha if shown else 0.0)
            o.hide_render = not shown or alpha <= 0.002
            o.keyframe_insert('location', frame=fr); o.keyframe_insert('rotation_euler', frame=fr); o.keyframe_insert('scale', frame=fr)
            o.keyframe_insert('color', frame=fr); o.keyframe_insert('hide_render', frame=fr)
