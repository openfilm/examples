"""The bright studio that lines 2 and 3 share: a warm off-white cyclorama (the floor sweeping up into the wall
without a seam), a big soft key from the front left, a cool fill, an overhead softbox, a warm rim from behind, and two
softboxes on stands far back at the edges, so it reads as a studio even out of focus. Cycles on the GPU.
Units are the old agents stage's: a character tile is 1 m square, standing on the floor at z = 0, facing −Y."""
import bpy, bmesh, math, mathutils

def srgb(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)

def reset(fps=30, frames=(0, 100)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = fps; sc.frame_start, sc.frame_end = frames
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080; sc.render.resolution_percentage = 100
    w = bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']; bg.inputs[0].default_value = (*srgb('#e6ddd0'), 1); bg.inputs[1].default_value = 0.30
    # glossy surfaces see a dark studio (as if flagged with black cards), so black ceramic reads black with clean highlights
    dark = nt.nodes.new('ShaderNodeBackground'); dark.inputs[0].default_value = (*srgb('#2a2826'), 1); dark.inputs[1].default_value = 0.30
    lp = nt.nodes.new('ShaderNodeLightPath'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Glossy Ray'], mx.inputs[0]); nt.links.new(bg.outputs[0], mx.inputs[1]); nt.links.new(dark.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], nt.nodes['World Output'].inputs['Surface'])
    return sc

def mat(name, color, rough=0.5, metal=0.0, coat=0.0, coat_rough=0.05, sss=0.0, sss_radius=(0.05, 0.03, 0.02), sheen=0.0, emit=None, emit_strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*(srgb(color) if isinstance(color, str) else color), 1)
    for k, v in (('Roughness', rough), ('Metallic', metal), ('Coat Weight', coat), ('Coat Roughness', coat_rough), ('Subsurface Weight', sss), ('Sheen Weight', sheen)):
        if k in b.inputs: b.inputs[k].default_value = v
    if sss: b.inputs['Subsurface Radius'].default_value = sss_radius
    if emit: b.inputs['Emission Color'].default_value = (*srgb(emit), 1); b.inputs['Emission Strength'].default_value = emit_strength
    return m

def link(o, col=None):
    (col or bpy.context.scene.collection).objects.link(o); return o

def area(name, loc, target, power, color='#ffffff', size=(1, 1), visible=False):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = power; d.color = srgb(color); d.shape = 'RECTANGLE'; d.size, d.size_y = size
    o = link(bpy.data.objects.new(name, d)); o.location = loc
    o.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    o.visible_camera = visible
    return o

def cyclorama(color='#e2d8c9', floor_rough=0.48):
    """floor (y < 3) curving up with radius 4 into the back wall at y = 7, 40 m wide; one smooth surface"""
    bm = bmesh.new(); prof = []
    for i in range(24): prof.append((-30 + i * (33.0 / 23), 0.0))                       # floor, y from −30 to 3
    for k in range(1, 24):
        a = k / 23 * math.pi / 2; prof.append((3 + 4 * math.sin(a), 4 - 4 * math.cos(a)))   # the cove
    for i in range(1, 8): prof.append((7.0, 4 + i * 2.0))                                   # the wall, to z = 18
    rows = []
    for x in (-40, -20, 0, 20, 40):
        rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for a, b in zip(rows, rows[1:]):
        for i in range(len(prof) - 1): bm.faces.new((a[i], b[i], b[i + 1], a[i + 1]))
    # every face toward the stage: the floor up, the cove toward the centre of its curve, the wall to the front
    for f in bm.faces:
        c = f.calc_center_median()
        want = mathutils.Vector((0, 0, 1)) if c.y < 3 else (mathutils.Vector((0, 3 - c.y, 4 - c.z)).normalized() if c.z < 4 else mathutils.Vector((0, -1, 0)))
        if f.normal.dot(want) < 0: f.normal_flip()
    me = bpy.data.meshes.new('cyc'); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = link(bpy.data.objects.new('cyc', me))
    m = bpy.data.materials.new('cyc'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; L = nt.links.new
    b.inputs['Base Color'].default_value = (*srgb(color), 1)
    # a little glossier on the floor than on the wall, so the characters stand in their soft reflections
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L(geo.outputs['Position'], sep.inputs[0])
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 2.5
    mr.inputs['To Min'].default_value = floor_rough; mr.inputs['To Max'].default_value = 0.62; L(sep.outputs['Z'], mr.inputs['Value']); L(mr.outputs['Result'], b.inputs['Roughness'])
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = 3.0; n.inputs['Detail'].default_value = 3.0
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.02; L(n.outputs['Fac'], bump.inputs['Height']); L(bump.outputs['Normal'], b.inputs['Normal'])
    me.materials.append(m)
    return o

def softbox_on_stand(x, y, h=3.0, w=1.15, hh=1.45, face=(0, -1, 0), power=0.0, glow=1.6):
    """a softbox far back: its glowing white face, a black rim, a black stand; seen out of focus it says 'studio'"""
    root = link(bpy.data.objects.new('softbox', None)); root.location = (x, y, 0)
    blk = mat('stand_black', '#1b1b1d', 0.45, 0.4)
    face_m = mat('softbox_face', '#ffffff', 0.9, emit='#fff3e4', emit_strength=glow)
    def box(name, size, loc, m):
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = link(bpy.data.objects.new(name, me)); o.location = loc; me.materials.append(m); o.parent = root
        return o
    box('sb_body', (w + 0.12, 0.35, hh + 0.12), (0, 0.18, h), blk)
    box('sb_face', (w, 0.02, hh), (0, -0.01, h), face_m)
    box('sb_pole', (0.05, 0.05, h - hh / 2), (0, 0.3, (h - hh / 2) / 2), blk)
    for k in range(3):
        a = k / 3 * math.tau; leg = box('sb_leg', (0.04, 0.9, 0.04), (math.sin(a) * 0.4, 0.3 + math.cos(a) * 0.4, 0.15), blk)
        leg.rotation_euler = (math.radians(70), 0, a)
    root.rotation_euler = (0, 0, math.atan2(face[0], -face[1]))
    return root

def lights(key=1.0, warm_rim=True):
    area('key', (-5.5, -7.5, 7.0), (0, 0, 0.6), 1500 * key, '#fff1e2', (4.0, 3.0))
    area('fill', (7.5, -6.0, 3.5), (0, 0, 0.6), 260 * key, '#eef3ff', (4.0, 4.0))
    area('top', (0, -0.5, 9.0), (0, 0, 0), 380 * key, '#fffaf2', (8.0, 3.0))
    if warm_rim:
        area('rim', (0, 5.5, 5.0), (0, 0, 0.8), 900 * key, '#ffd2a3', (8.0, 1.5))
    # a soft pool of light on the wall behind the cast: the centre glows, the edges fall off — depth, and a place to look
    d = bpy.data.lights.new('pool', 'SPOT'); d.energy = 9000 * key; d.color = srgb('#fff0dc'); d.spot_size = math.radians(42); d.spot_blend = 1.0; d.shadow_soft_size = 1.5
    o = link(bpy.data.objects.new('pool', d)); o.location = (0, -6.0, 9.0)
    o.rotation_euler = (mathutils.Vector((0, 7.0, 3.0)) - o.location).to_track_quat('-Z', 'Y').to_euler(); o.visible_camera = False
    # and a black card behind the camera, so fronts of glossy things reflect dark
    me = bpy.data.meshes.new('flag'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=14); bm.to_mesh(me); bm.free()
    fl = link(bpy.data.objects.new('flag', me)); fl.location = (0, -26, 6); fl.rotation_euler = (math.radians(90), 0, 0)
    me.materials.append(mat('flag_black', '#060606', 1.0)); fl.visible_camera = False; fl.visible_shadow = False; fl.visible_diffuse = False

def cycles(sc, samples=128):
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'; prefs.kernel_optimization_level = 'FULL'; prefs.get_devices()
    for d in prefs.devices: d.use = (d.type == 'METAL')
    c = sc.cycles; c.device = 'GPU'; c.samples = samples; c.use_adaptive_sampling = True; c.adaptive_threshold = 0.02
    c.use_denoising = True; c.denoiser = 'OPENIMAGEDENOISE'; c.max_bounces = 8; c.caustics_reflective = False; c.caustics_refractive = False
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.4
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    sc.render.image_settings.file_format = 'PNG'
