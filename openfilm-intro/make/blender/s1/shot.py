"""Line 1 of the explainer, in Blender: the room at 3:47, the push into Premiere, the old app coming apart and
rebuilding as OpenFilm. Run:
    blender -b -P shot.py -- still <frame> <out.png> [percent] [samples]
    blender -b -P shot.py -- save                     (writes s1.blend)
"""
import bpy, sys, math, mathutils, importlib
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import room; importlib.reload(room)
import rebuild; importlib.reload(rebuild)

FPS = 30
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS; sc.frame_start = 0; sc.frame_end = 109
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.unit_settings.system = 'METRIC'
    w = bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True
    bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.011, 0.030, 0.087, 1); bg.inputs[1].default_value = 1.0   # the night sky's own blue, seen above the city
    return sc

def cycles(sc, samples=128):
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'; prefs.kernel_optimization_level = 'FULL'; prefs.get_devices()
    for d in prefs.devices: d.use = (d.type == 'METAL')         # the GPU alone: a CPU share only slows the frame down
    c = sc.cycles; c.device = 'GPU'; c.samples = samples; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.015
    c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'
    try: c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    except Exception: pass
    c.max_bounces = 8; c.diffuse_bounces = 4; c.glossy_bounces = 4; c.transmission_bounces = 8; c.transparent_max_bounces = 16
    c.caustics_reflective = False; c.caustics_refractive = False; c.blur_glossy = 1.0
    sc.render.film_transparent = False
    # denoise only what is lit; add what shines (the screen, the slabs' pictures) back untouched, so UI stays crisp
    c.use_denoising = False
    vl = sc.view_layers[0]; vl.use_pass_emit = True
    try: vl.cycles.denoising_store_passes = True
    except Exception: pass
    ng = bpy.data.node_groups.new('finish', 'CompositorNodeTree')
    ng.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = ng.nodes.new('CompositorNodeRLayers'); rl.scene = sc; rl.layer = vl.name; out = ng.nodes.new('NodeGroupOutput')
    sub = ng.nodes.new('ShaderNodeMix'); sub.data_type = 'RGBA'; sub.blend_type = 'SUBTRACT'; sub.inputs['Factor'].default_value = 1.0
    dn = ng.nodes.new('CompositorNodeDenoise')
    try: dn.inputs['HDR'].default_value = True
    except Exception: pass
    add = ng.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'; add.inputs['Factor'].default_value = 1.0
    L = ng.links.new
    L(rl.outputs['Image'], sub.inputs['A']); L(rl.outputs['Emission'], sub.inputs['B'])
    L(sub.outputs['Result'], dn.inputs['Image']); L(rl.outputs['Denoising Albedo'], dn.inputs['Albedo']); L(rl.outputs['Denoising Normal'], dn.inputs['Normal'])
    L(dn.outputs['Image'], add.inputs['A']); L(rl.outputs['Emission'], add.inputs['B'])
    L(add.outputs['Result'], out.inputs['Image'])
    sc.compositing_node_group = ng; sc.render.use_compositing = True
    # Blender writes scene-linear EXR; the finish (tone, bloom, grain) is post.py's
    sc.view_settings.view_transform = 'Standard'

def V(nt, v, label):
    n = nt.nodes.new('ShaderNodeValue'); n.outputs[0].default_value = v; n.label = n.name = label; return n

def screen_material(screen):
    """The screen: Premiere being worked on (an image sequence, then held), then — once the pieces have left the
    glass — the dark between Premiere's panels, a light coming up behind them, the wave that lifted them, and at last
    OpenFilm's own dark between its panels."""
    m = bpy.data.materials.new('screen'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links.new
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexImage'); img = bpy.data.images.load(str(HERE / 'pr' / 'out' / 'frames' / '0001.png'))
    img.source = 'SEQUENCE'; tex.image = img; tex.interpolation = 'Cubic'
    tex.image_user.frame_duration = 42; tex.image_user.frame_start = 0; tex.image_user.frame_offset = 0; tex.image_user.use_auto_refresh = True; tex.image_user.use_cyclic = False
    uv = nt.nodes.new('ShaderNodeTexCoord')
    # d: distance from the middle in screen heights; dp: from the wait cursor, in Premiere pixels
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L(uv.outputs['UV'], sep.inputs[0])
    def math(op, a, b=None, v=None):
        n = nt.nodes.new('ShaderNodeMath'); n.operation = op
        L(a, n.inputs[0]) if not isinstance(a, (int, float)) else setattr(n.inputs[0], 'default_value', a)
        if b is not None: L(b, n.inputs[1]) if not isinstance(b, (int, float)) else setattr(n.inputs[1], 'default_value', b)
        return n.outputs[0]
    ux = math('MULTIPLY', math('SUBTRACT', sep.outputs['X'], 0.5), 1.7778); uy = math('SUBTRACT', sep.outputs['Y'], 0.5)
    d = math('SQRT', math('ADD', math('MULTIPLY', ux, ux), math('MULTIPLY', uy, uy)))
    px = math('SUBTRACT', math('MULTIPLY', sep.outputs['X'], 1920.0), rebuild.CURSOR[0]); py = math('SUBTRACT', math('MULTIPLY', math('SUBTRACT', 1.0, sep.outputs['Y']), 1080.0), rebuild.CURSOR[1])
    dp = math('SQRT', math('ADD', math('MULTIPLY', px, px), math('MULTIPLY', py, py)))
    lifted, leak, ringR, ringI, appbg = V(nt, 0, 'lifted'), V(nt, 0, 'leak'), V(nt, 0, 'ringR'), V(nt, 0, 'ringI'), V(nt, 0, 'appbg')
    # the light behind: a low cool glow, the dark app it opens on (no white flash before a dark landing)
    fall = math('ADD', math('MULTIPLY', math('EXPONENT', math('MULTIPLY', math('MULTIPLY', d, d), -1.0)), 0.16), 0.40)   # even and soft: no hot centre
    warm = nt.nodes.new('ShaderNodeMix'); warm.data_type = 'RGBA'; warm.inputs['A'].default_value = (0.10, 0.12, 0.16, 1); warm.inputs['B'].default_value = (0.04, 0.05, 0.07, 1)
    L(math('MINIMUM', math('MULTIPLY', d, 1.1), 1.0), warm.inputs['Factor'])
    leakc = nt.nodes.new('ShaderNodeVectorMath'); leakc.operation = 'SCALE'; L(warm.outputs['Result'], leakc.inputs[0]); L(math('MULTIPLY', fall, leak.outputs[0]), leakc.inputs['Scale'])
    # the wave: a bright ring running out from the cursor
    rg = math('EXPONENT', math('MULTIPLY', math('POWER', math('DIVIDE', math('SUBTRACT', dp, ringR.outputs[0]), 26.0), 2.0), -1.0))
    ringc = nt.nodes.new('ShaderNodeVectorMath'); ringc.operation = 'SCALE'; ringc.inputs[0].default_value = (0.75, 0.85, 1.0); L(math('MULTIPLY', rg, ringI.outputs[0]), ringc.inputs['Scale'])
    gap = nt.nodes.new('ShaderNodeVectorMath'); gap.operation = 'ADD'; gap.inputs[0].default_value = (0.0037, 0.0037, 0.0037); L(leakc.outputs[0], gap.inputs[1])
    gap2 = nt.nodes.new('ShaderNodeVectorMath'); gap2.operation = 'ADD'; L(gap.outputs[0], gap2.inputs[0]); L(ringc.outputs[0], gap2.inputs[1])
    m1 = nt.nodes.new('ShaderNodeMix'); m1.data_type = 'RGBA'; L(lifted.outputs[0], m1.inputs['Factor']); L(tex.outputs['Color'], m1.inputs['A']); L(gap2.outputs[0], m1.inputs['B'])
    m2 = nt.nodes.new('ShaderNodeMix'); m2.data_type = 'RGBA'; L(appbg.outputs[0], m2.inputs['Factor']); L(m1.outputs['Result'], m2.inputs['A']); m2.inputs['B'].default_value = (0.0056, 0.0056, 0.0056, 1)      # the desktop app's shell, #111
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0; L(m2.outputs['Result'], em.inputs['Color']); L(em.outputs[0], out.inputs['Surface'])
    screen.data.materials.clear(); screen.data.materials.append(m)
    return m, {'lifted': lifted, 'leak': leak, 'ringR': ringR, 'ringI': ringI, 'appbg': appbg}

def of_material(name, path):
    """OpenFilm's side of a slab: the recording's (or the clean plate's) pixels, light only — no glint once it lands."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links.new
    out = nt.nodes.new('ShaderNodeOutputMaterial'); tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(path)); tex.interpolation = 'Cubic'; tex.extension = 'EXTEND'
    em = nt.nodes.new('ShaderNodeEmission'); L(tex.outputs['Color'], em.inputs['Color'])
    oi = nt.nodes.new('ShaderNodeObjectInfo'); sep = nt.nodes.new('ShaderNodeSeparateColor'); L(oi.outputs['Color'], sep.inputs['Color'])
    gl = nt.nodes.new('ShaderNodeBsdfGlossy'); gl.inputs['Roughness'].default_value = 0.22
    fr = nt.nodes.new('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.5
    k = nt.nodes.new('ShaderNodeMath'); k.operation = 'MULTIPLY'; L(fr.outputs[0], k.inputs[0]); L(sep.outputs['Red'], k.inputs[1])
    mx = nt.nodes.new('ShaderNodeMixShader'); L(k.outputs[0], mx.inputs[0]); L(em.outputs[0], mx.inputs[1]); L(gl.outputs[0], mx.inputs[2])
    geo = nt.nodes.new('ShaderNodeNewGeometry'); vis = nt.nodes.new('ShaderNodeMath'); vis.operation = 'SUBTRACT'; vis.inputs[0].default_value = 1.0; L(geo.outputs['Backfacing'], vis.inputs[1])
    va = nt.nodes.new('ShaderNodeMath'); va.operation = 'MULTIPLY'; L(oi.outputs['Alpha'], va.inputs[0]); L(vis.outputs[0], va.inputs[1])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx2 = nt.nodes.new('ShaderNodeMixShader'); L(va.outputs[0], mx2.inputs[0]); L(tr.outputs[0], mx2.inputs[1]); L(mx.outputs[0], mx2.inputs[2])
    L(mx2.outputs[0], out.inputs['Surface'])
    return m

def beachball(ui_root, k):
    """macOS's spinning wait cursor, where the hand was, from the moment Premiere stops answering."""
    me = bpy.data.meshes.new('beachball'); bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=0.5)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=mathutils.Matrix.Rotation(math.radians(90), 3, 'X'))
    uvl = bm.loops.layers.uv.new('UVMap')
    for f in bm.faces:
        for loop in f.loops: loop[uvl].uv = (loop.vert.co.x + 0.5, loop.vert.co.z + 0.5)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('beachball', me); bpy.context.scene.collection.objects.link(o); o.parent = ui_root
    mat = bpy.data.materials.new('beachball'); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear(); L = nt.links.new
    out = nt.nodes.new('ShaderNodeOutputMaterial'); tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(HERE / 'tex' / 'beachball.png')); tex.extension = 'CLIP'
    em = nt.nodes.new('ShaderNodeEmission'); L(tex.outputs['Color'], em.inputs['Color'])
    oi = nt.nodes.new('ShaderNodeObjectInfo'); a = nt.nodes.new('ShaderNodeMath'); a.operation = 'MULTIPLY'; L(tex.outputs['Alpha'], a.inputs[0]); L(oi.outputs['Alpha'], a.inputs[1])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader'); L(a.outputs[0], mx.inputs[0]); L(tr.outputs[0], mx.inputs[1]); L(em.outputs[0], mx.inputs[2]); L(mx.outputs[0], out.inputs['Surface'])
    me.materials.append(mat); o.visible_shadow = False
    D = 30 * k
    for fr in range(0, 110):
        t = fr / FPS
        shown = rebuild.FREEZE_T <= t < rebuild.LIFT + 0.14
        pop = rebuild.prog(t, rebuild.LIFT, rebuild.LIFT + 0.12)
        o.location = ((rebuild.CURSOR[0] - 960) * k, -0.0012 - pop * 0.01, -(rebuild.CURSOR[1] - 540) * k)
        o.rotation_euler = (0, -(t - rebuild.FREEZE_T) * math.tau * 1.7, 0)
        sz = D * (1 + 0.9 * rebuild.out3(pop)); o.scale = (sz, sz, sz)
        o.color = (0, 0, 0, 1 - pop); o.hide_render = not shown
        for path in ('location', 'rotation_euler', 'scale', 'color', 'hide_render'): o.keyframe_insert(path, frame=fr)
    return o

def camera(sc):
    d = bpy.data.cameras.new('cam'); d.lens = 24; d.sensor_fit = 'HORIZONTAL'; d.sensor_width = 36; d.clip_start = 0.01
    o = bpy.data.objects.new('cam', d); sc.collection.objects.link(o); sc.camera = o
    d.dof.use_dof = True; d.dof.aperture_fstop = 2.8; d.dof.aperture_blades = 7
    return o

def place(cam, loc, target, focus=None, fstop=None, lens=None):
    cam.location = loc
    v = mathutils.Vector(target) - mathutils.Vector(loc); cam.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    if focus is not None: cam.data.dof.focus_distance = focus
    if fstop is not None: cam.data.dof.aperture_fstop = fstop
    if lens is not None: cam.data.lens = lens

sc = reset()
col = bpy.data.collections.new('room'); sc.collection.children.link(col)
R = room.build_room(col)
import bmesh
SCR_MAT, SCR = screen_material(R['screen'])
HERO = of_material('of_hero', HERE / 'tex' / 'hero_land_nocursor.png'); PLATE = of_material('of_plate', HERE / 'tex' / 'plate.png')
UI, SLABS = rebuild.build(col, room.SC + mathutils.Vector((0, -0.0002, 0)), room.SW, HERO, PLATE)
# the slabs are lit by their own pictures, not by the screen behind them (its fill would blaze on a slab turned edge-on)
fill_light = bpy.data.objects['screen_fill']
for sl in SLABS:
    sl['o'].light_linking.receiver_collection = None
rx = bpy.data.collections.new('slab_receivers'); sc.collection.children.link(rx); rx.hide_render = False
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.name.startswith(('slab_', 'strip', 'beachball', 'phone_glass')):   # nor the phone: its glass would mirror the fill as a blot
        rx.objects.link(o)
fill_light.light_linking.receiver_collection = rx
for o in [R['screen']] + [sl['o'] for sl in SLABS]:
    o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False; o.visible_volume_scatter = False
cam = camera(sc)
LENS = 30.0
D1 = room.SW * LENS / 36.0                                  # the distance at which the screen is the frame
P2, T2 = room.SC + mathutils.Vector((0, -D1, 0)), room.SC.copy()
FREEZE = 1.36; LIFT = rebuild.LIFT
rebuild.D1 = D1
rebuild.FREEZE_T = FREEZE
CAM_LAND = 3.46
# ── the camera: one move, from the room to the glass, in the line's rhythm ──
# The room at 3:47 from the left of the desk, drifting in while Premiere plays. On 剪 it hangs, and the camera
# pushes in on it, and takes a breath on the frozen screen. On 我 the cursor pops and Premiere comes apart toward
# the camera, which swings round through the pieces in the air and squares up to the glass as OpenFilm lands,
# on exactly the frame the recording takes over from. No cut, no pull-back.
V3 = mathutils.Vector
KEYS = [  # t, yaw° (− from the left), distance to the glass, height over its centre, aim (x, z) off its centre, roll°, lens
    (0.00, -21.5, 1.32, 0.185, (0.032, -0.108), -1.1, 28.0),
    (1.36, -16.5, 1.18, 0.160, (0.030, -0.095), -0.9, 28.0),   # the room, drifting: Premiere playing, the phone lighting up
    (2.15, -12.0, 0.70, 0.045, (0.012, -0.020), -0.5, 29.0),   # 剪: pushed in on it as it hangs
    (2.30, -11.3, 0.685, 0.040, (0.011, -0.018), -0.45, 29.1), # a breath, and the cursor pops (2.22)
    (2.80, -4.4, 0.565, 0.015, (0.004, -0.007), -0.17, 29.6),  # through the pieces in the air
    (CAM_LAND, 0.0, D1, 0.0, (0.0, 0.0), 0.0, LENS),           # squared up: the recording's frame
]
SPEED = [None, None, 0.15, 0.15, 1.25, 0.0]   # each key's speed as a share of the move into it (None: the drift's own pace)
def track(vs):
    """values at the keys' times → a function of t, Hermite through them at the keys' speeds"""
    ts = [k[0] for k in KEYS]
    sl = [(vs[1] - vs[0]) / (ts[1] - ts[0]) if SPEED[j] is None else SPEED[j] * (vs[j] - vs[j - 1]) / (ts[j] - ts[j - 1]) for j in range(len(ts))]
    def f(t):
        if t <= ts[0]: return vs[0] + sl[0] * (t - ts[0])
        if t >= ts[-1]: return vs[-1]
        for j in range(len(ts) - 1):
            if t <= ts[j + 1]:
                h = ts[j + 1] - ts[j]; u = (t - ts[j]) / h
                return (2 * u ** 3 - 3 * u ** 2 + 1) * vs[j] + (u ** 3 - 2 * u ** 2 + u) * h * sl[j] + (-2 * u ** 3 + 3 * u ** 2) * vs[j + 1] + (u ** 3 - u ** 2) * h * sl[j + 1]
    return f
_YAW, _DIST, _H, _ROLL, _LENS = (track([k[i] for k in KEYS]) for i in (1, 2, 3, 5, 6))
_AIMX, _AIMZ = (track([k[4][i] for k in KEYS]) for i in (0, 1))
def cam_pose(t):
    """(location, target, roll, focus distance, f-stop, lens)"""
    yaw = math.radians(_YAW(t)); d = _DIST(t)
    p = room.SC + V3((math.sin(yaw) * d, -math.cos(yaw) * d, _H(t)))
    tg = room.SC + V3((_AIMX(t), 0, _AIMZ(t)))
    hand = 0.0012 * (1 - rebuild.smooth(rebuild.prog(t, 1.6, 2.6)))                 # held, breathing, steadier as it closes in
    p = p + V3((math.sin(t * 1.9) * hand, math.sin(t * 1.3 + 2) * hand * 0.5, math.sin(t * 2.4 + 1) * hand * 0.7))
    focus = (room.SC - p).dot((tg - p).normalized()) - 0.012 * rebuild.smooth(rebuild.prog(t, LIFT, LIFT + 0.3)) * (1 - rebuild.smooth(rebuild.prog(t, 3.0, CAM_LAND)))
    fstop = 2.8 + 1.4 * rebuild.smooth(rebuild.prog(t, 1.4, 2.15)) + 6.8 * rebuild.smooth(rebuild.prog(t, LIFT, 2.9))   # deeper as the pieces come off the glass
    return p, tg, math.radians(_ROLL(t)), focus, fstop, _LENS(t)
def key_camera():
    """keyed every frame, linear"""
    for fr in range(0, 110):
        p, tg, roll, focus, fstop, lens = cam_pose(fr / FPS)
        cam.location = p
        q = (tg - p).to_track_quat('-Z', 'Y') @ mathutils.Quaternion((0, 0, 1), roll); cam.rotation_euler = q.to_euler('XYZ', cam.rotation_euler)
        cam.data.dof.focus_distance = focus; cam.data.dof.aperture_fstop = fstop; cam.data.lens = lens
        cam.keyframe_insert('location', frame=fr); cam.keyframe_insert('rotation_euler', frame=fr)
        cam.data.dof.keyframe_insert('focus_distance', frame=fr); cam.data.dof.keyframe_insert('aperture_fstop', frame=fr); cam.data.keyframe_insert('lens', frame=fr)
    for idb in (cam, cam.data):
        act = idb.animation_data.action
        fcs = act.fcurves if hasattr(act, 'fcurves') else [fc for ly in act.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
        for fc in fcs:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
def key_screen_and_lights():
    fill = bpy.data.objects['screen_fill'].data
    for fr in range(0, 110):
        t = fr / FPS
        lifted = 1.0 if t >= LIFT else 0.0
        leak = rebuild.smooth(rebuild.prog(t, LIFT + 0.08, 2.62)) * (1 - rebuild.smooth(rebuild.prog(t, 3.05, 3.38)))
        ringR = max(0.0, (t - LIFT) * 3600.0); ringI = 2.5 * (1 - rebuild.prog(t, LIFT, LIFT + 0.6)) * (1.0 if t >= LIFT else 0.0)
        appbg = rebuild.smooth(rebuild.prog(t, 3.05, 3.36))
        for name, v in (('lifted', lifted), ('leak', leak), ('ringR', ringR), ('ringI', ringI), ('appbg', appbg)):
            SCR[name].outputs[0].default_value = v; SCR[name].outputs[0].keyframe_insert('default_value', frame=fr)
        # the room's light holds still through the rebuild: what the screen shows changes, the room does not
        fill.energy = 9.0; fill.color = (0.78, 0.86, 1.0)
        fill.keyframe_insert('energy', frame=fr); fill.keyframe_insert('color', frame=fr)
import bmesh
rebuild.lerp = lambda a, b, k: a + (b - a) * k
key_camera(); key_screen_and_lights()
rebuild.animate(SLABS, range(0, 110))
beachball(UI, room.SW / 1920)

# ── 0.30 s: a message. The phone on the mat buzzes against it (two pulses) and its screen wakes ──
MSG = 0.30
def key_phone():
    ph = bpy.data.objects['phone']; base_loc = ph.location.copy(); base_rot = ph.rotation_euler.copy()
    wake = bpy.data.materials['phone_screen'].node_tree.nodes['wake'].outputs[0]
    import random
    rnd = random.Random(4)
    for fr in range(0, 110):
        t = fr / FPS
        buzz = (1.0 if MSG <= t < MSG + 0.14 else 0.0) + (0.7 if MSG + 0.17 <= t < MSG + 0.32 else 0.0)        # the two pulses of phone-buzz.mp3
        ph.location = base_loc + mathutils.Vector((rnd.uniform(-1, 1) * 0.00045 * buzz, rnd.uniform(-1, 1) * 0.00045 * buzz, 0)) \
            + mathutils.Vector((0.0009, -0.0004, 0)) * rebuild.smooth(rebuild.prog(t, MSG, MSG + 0.40))          # it walks a hair on the mat
        ph.rotation_euler = (base_rot.x, base_rot.y, base_rot.z + math.radians(0.5) * rebuild.smooth(rebuild.prog(t, MSG, MSG + 0.40)) + rnd.uniform(-1, 1) * math.radians(0.25) * buzz)
        ph.keyframe_insert('location', frame=fr); ph.keyframe_insert('rotation_euler', frame=fr)
        wake.default_value = 0.62 * rebuild.smooth(rebuild.prog(t, MSG + 0.02, MSG + 0.20)); wake.keyframe_insert('default_value', frame=fr)
key_phone()
for o in bpy.data.objects:
    ad = o.animation_data
    for idb in (o, o.data) if o.data is not None else (o,):
        pass
cycles(sc)
import os
sc.render.use_motion_blur = os.environ.get('S1_MBLUR', '1') == '1'; sc.render.motion_blur_shutter = 0.35
if os.environ.get('S1_FUR', '1') == '0':
    for o in bpy.data.objects:
        for m in list(o.modifiers):
            if m.type == 'PARTICLE_SYSTEM': o.modifiers.remove(m)
if os.environ.get('S1_METALRT'):
    try: bpy.context.preferences.addons['cycles'].preferences.metalrt = os.environ['S1_METALRT']
    except Exception as e: print('metalrt pref', e)

mode = args[0] if args else 'still'
if os.environ.get('S1_CPU'): sc.cycles.device = 'CPU'      # previews on the CPU while the GPU renders something else
if mode == 'sheet':
    # sheet <dir> <percent> <samples> <frame> …: finished stills, one process
    import post; importlib.reload(post)
    out = Path(args[1]); out.mkdir(parents=True, exist_ok=True)
    sc.render.resolution_percentage = int(args[2]); sc.cycles.samples = int(args[3])
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '16'; sc.render.image_settings.exr_codec = 'ZIP'
    for frame in [int(a) for a in args[4:]]:
        exr = str(out / f'{frame:04d}.exr'); sc.render.filepath = exr; sc.frame_set(frame); bpy.ops.render.render(write_still=True)
        pp = post.params_at(frame / FPS); post.save_png(str(out / f'{frame:04d}.png'), post.finish(post.load_exr(exr), pp, frame))
if mode == 'close':
    # an inspection camera: close <x y z> <tx ty tz> <lens> <out.png>
    cam.animation_data_clear(); cam.data.animation_data_clear()
    vals = [float(v) for v in args[1:8]]
    place(cam, mathutils.Vector(vals[0:3]), mathutils.Vector(vals[3:6]), focus=(mathutils.Vector(vals[3:6]) - mathutils.Vector(vals[0:3])).length, fstop=8, lens=vals[6])
    args = ['still', '0', args[8], '50', '96']; mode = 'still'
if mode == 'still':
    frame = int(args[1]) if len(args) > 1 else 0
    out = args[2] if len(args) > 2 else str(HERE / 'out' / 'still.png')
    pct = int(args[3]) if len(args) > 3 else 50
    sc.cycles.samples = int(args[4]) if len(args) > 4 else 64
    sc.render.resolution_percentage = pct
    exr = str(Path(out).with_suffix('.exr'))
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '16'; sc.render.image_settings.exr_codec = 'ZIP'
    sc.render.filepath = exr
    sc.frame_set(frame)
    bpy.ops.render.render(write_still=True)
    import post; importlib.reload(post)
    pp = post.params_at(frame / FPS); rgb = post.finish(post.load_exr(exr), pp, frame)
    if pp['hero'] > 0:
        import numpy as np
        h = post.load_png(HERE / 'tex' / 'hero_land.png')
        while h.shape[0] > rgb.shape[0]:      # a preview at a fraction of the size: average the recording down
            h = h.astype(np.float32); h = ((h[0::2, 0::2] + h[1::2, 0::2] + h[0::2, 1::2] + h[1::2, 1::2]) / 4 + 0.5).astype(np.uint8)
        rgb = (rgb.astype(np.float32) * (1 - pp['hero']) + h.astype(np.float32) * pp['hero'] + 0.5).astype(np.uint8)
    post.save_png(out, rgb)
elif mode == 'save':
    sc.cycles.samples = 256
    sc.render.image_settings.file_format = 'OPEN_EXR'; sc.render.image_settings.color_depth = '16'; sc.render.image_settings.exr_codec = 'ZIP'
    sc.render.filepath = '//out/exr/####'
    sc.render.use_file_extension = True
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 's1.blend'))
