"""The room at 3:47 a.m., modelled for Cycles. Metres; X right, Y away from the viewer, Z up; the desk's top is at
z = 0.74 and the monitor faces -Y. Everything rests on what it stands on, nothing passes through anything.
build_room() returns the handles the shot animates (the screen's material, the monitor, the lights)."""
import bpy, bmesh, math, mathutils
from pathlib import Path

HERE = Path(__file__).parent
TEX = HERE / 'tex'
DT = 0.74                                   # the desk's top
MAT = 0.003                                 # the felt mat on it
SW, SH = 0.5967, 0.3357                     # the screen's lit area (27", 16:9)
SC = mathutils.Vector((0.0, 0.15, 1.115))   # its centre
BEZ = 0.0085                                # black glass around it

def srgb(h):
    """'#rrggbb' → linear RGB, the way a colour picked on screen is stored in a shader."""
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)

# ── materials ───────────────────────────────────────────────────────────────────────────────────────────────────────
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; return m, nt, nt.nodes['Principled BSDF']

def pbr(name, color, rough=0.5, metal=0.0, coat=0.0, coat_rough=0.05, sheen=0.0, sheen_rough=0.5, sss=0.0, sss_radius=(0.1, 0.05, 0.03), ior=1.5, aniso=0.0, transmission=0.0, alpha=1.0):
    m, nt, b = node_mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    vals = {'Roughness': rough, 'Metallic': metal, 'Coat Weight': coat, 'Coat Roughness': coat_rough, 'Sheen Weight': sheen, 'Sheen Roughness': sheen_rough,
            'Subsurface Weight': sss, 'IOR': ior, 'Anisotropic': aniso, 'Transmission Weight': transmission, 'Alpha': alpha}
    for k, v in vals.items():
        if k in b.inputs: b.inputs[k].default_value = v
    if sss and 'Subsurface Radius' in b.inputs: b.inputs['Subsurface Radius'].default_value = sss_radius
    return m

def add_bump(m, scale=200.0, strength=0.05, detail=6.0, kind='noise', distance=0.002):
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexNoise' if kind == 'noise' else 'ShaderNodeTexVoronoi'); t.inputs['Scale'].default_value = scale
    if kind == 'noise': t.inputs['Detail'].default_value = detail
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = strength; bump.inputs['Distance'].default_value = distance
    nt.links.new(t.outputs[0 if kind == 'noise' else 'Distance'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m

def speckled(m):
    """Stoneware: a scatter of iron speckles under the glaze."""
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 420.0; vo.feature = 'F1'
    ramp = nt.nodes.new('ShaderNodeValToRGB'); r = ramp.color_ramp
    r.elements[0].position = 0.0; r.elements[0].color = (*srgb('#5a4a3c'), 1); r.elements[1].position = 0.06; r.elements[1].color = b.inputs['Base Color'].default_value[:]
    nt.links.new(vo.outputs['Distance'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    return m

def hair_mat(name, color):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); h = nt.nodes.new('ShaderNodeBsdfHairPrincipled')
    try: h.parametrization = 'COLOR'
    except Exception: pass
    for k, v in (('Color', (*color, 1)), ('Roughness', 0.42), ('Radial Roughness', 0.55), ('Coat', 0.05), ('IOR', 1.55)):
        if k in h.inputs: h.inputs[k].default_value = v
    nt.links.new(h.outputs[0], out.inputs['Surface'])
    return m

def walnut(name):
    """Oiled walnut: long grain, a few darker streaks, a satin lacquer that catches the screen."""
    m, nt, b = node_mat(name)
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.9, 14.0, 1.0)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    warp = nt.nodes.new('ShaderNodeTexNoise'); warp.inputs['Scale'].default_value = 3.0; warp.inputs['Detail'].default_value = 3.0
    wave = nt.nodes.new('ShaderNodeTexWave'); wave.wave_type = 'BANDS'; wave.bands_direction = 'Y'; wave.inputs['Scale'].default_value = 3.2
    wave.inputs['Distortion'].default_value = 6.0; wave.inputs['Detail'].default_value = 6.0; wave.inputs['Detail Scale'].default_value = 1.6
    fine = nt.nodes.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value = 260.0; fine.inputs['Detail'].default_value = 4.0
    mp2 = nt.nodes.new('ShaderNodeMapping'); mp2.inputs['Scale'].default_value = (1.0, 22.0, 1.0)
    nt.links.new(tc.outputs['Object'], mp2.inputs['Vector']); nt.links.new(mp2.outputs['Vector'], fine.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], wave.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); r = ramp.color_ramp
    r.elements[0].position = 0.0; r.elements[0].color = (*srgb('#2a1a10'), 1)
    r.elements[1].position = 1.0; r.elements[1].color = (*srgb('#6b4428'), 1)
    e = r.elements.new(0.55); e.color = (*srgb('#4a2e1a'), 1)
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'FLOAT'; mix.inputs['Factor'].default_value = 0.25
    nt.links.new(wave.outputs['Fac'], mix.inputs[2]); nt.links.new(fine.outputs['Fac'], mix.inputs[3])
    nt.links.new(mix.outputs[0], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    rr = nt.nodes.new('ShaderNodeMapRange'); rr.inputs['To Min'].default_value = 0.42; rr.inputs['To Max'].default_value = 0.56
    nt.links.new(fine.outputs['Fac'], rr.inputs['Value']); nt.links.new(rr.outputs['Result'], b.inputs['Roughness'])
    b.inputs['Coat Weight'].default_value = 0.10; b.inputs['Coat Roughness'].default_value = 0.35
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.08; bump.inputs['Distance'].default_value = 0.0005
    nt.links.new(wave.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m

def image_emit(name, path, strength=1.0, interp='Cubic', alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(path)); tex.interpolation = interp
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = strength
    nt.links.new(tex.outputs['Color'], em.inputs['Color'])
    if alpha:
        tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(tex.outputs['Alpha'], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs['Surface'])
    else: nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m, tex, em

def paper(name, path):
    """A sticky note: matte paper that lets a little light through, with its words printed on it."""
    m, nt, b = node_mat(name)
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(path))
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.88; b.inputs['Subsurface Weight'].default_value = 0.12; b.inputs['Subsurface Radius'].default_value = (0.004, 0.004, 0.003)
    b.inputs['Sheen Weight'].default_value = 0.2
    return m

# ── geometry helpers ────────────────────────────────────────────────────────────────────────────────────────────────
COL = None
def link(o):
    COL.objects.link(o); return o

def mesh_obj(name, bm, mat=None, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = link(bpy.data.objects.new(name, me))
    if mat:
        for mm in (mat if isinstance(mat, (list, tuple)) else [mat]): me.materials.append(mm)
    for p in me.polygons: p.use_smooth = smooth
    return o

def rbox(name, size, loc, mat=None, bevel=0.0, seg=4, rot=(0, 0, 0), subsurf=0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    o = mesh_obj(name, bm, mat); o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]
    if not bevel and not subsurf:
        for p in o.data.polygons: p.use_smooth = False          # a hard box: flat faces (smooth normals would bend light like a lens)
    if bevel:
        bv = o.modifiers.new('bevel', 'BEVEL'); bv.width = bevel; bv.segments = seg; bv.limit_method = 'NONE'; bv.profile = 0.5
        o.modifiers.new('wn', 'WEIGHTED_NORMAL').keep_sharp = True
    if subsurf:
        ss = o.modifiers.new('ss', 'SUBSURF'); ss.levels = subsurf; ss.render_levels = subsurf
    return o

def cylinder(name, r, h, loc, mat=None, verts=64, bevel=0.0, rot=(0, 0, 0), r2=None):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r if r2 is None else r2, depth=h)
    o = mesh_obj(name, bm, mat); o.location = loc; o.rotation_euler = [math.radians(a) for a in rot]
    if bevel:
        bv = o.modifiers.new('bevel', 'BEVEL'); bv.width = bevel; bv.segments = 3; bv.limit_method = 'ANGLE'
        o.modifiers.new('wn', 'WEIGHTED_NORMAL').keep_sharp = True
    return o

def lathe(name, profile, loc, mat=None, steps=96):
    """A body of revolution from (radius, height) points, bottom to top along the outside then back down inside."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in profile]
    for a, b in zip(vs, vs[1:]): bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=steps, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, mat); o.location = loc
    return o

def curve_tube(name, pts, radius, mat, res=12):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = radius; cu.bevel_resolution = 4; cu.resolution_u = res
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    o = link(bpy.data.objects.new(name, cu)); cu.materials.append(mat); return o

def light(name, kind, loc, power, color, size=0.1, size_y=None, target=None, spot=60, blend=0.5, camera_visible=False, angle=0.5):
    d = bpy.data.lights.new(name, kind); d.energy = power; d.color = color
    if kind == 'AREA':
        d.shape = 'RECTANGLE'; d.size = size; d.size_y = size_y or size
    elif kind == 'SPOT':
        d.spot_size = math.radians(spot); d.spot_blend = blend; d.shadow_soft_size = size
    elif kind == 'POINT':
        d.shadow_soft_size = size
    elif kind == 'SUN':
        d.angle = math.radians(angle)
    o = link(bpy.data.objects.new(name, d)); o.location = loc
    if target is not None:
        v = mathutils.Vector(target) - mathutils.Vector(loc); o.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    o.visible_camera = camera_visible
    return o

# ── the props ───────────────────────────────────────────────────────────────────────────────────────────────────────
def keyboard(M):
    """A 75 % board after the NuPhy Halo75 V2 (the person's pick): a frosted mint case with its ribbed light bar along the
    front, nSA keycaps (round, dished, sculpted by row), cream alphas and mint mods, the function row in blocks."""
    root = link(bpy.data.objects.new('keyboard', None)); root.location = (-0.02, -0.125, DT + MAT); root.rotation_euler = (0, 0, math.radians(0.8))
    P = 0.01905                                           # one key unit
    W, D = 16 * P + 0.012, 6 * P + 0.012                  # sixteen units by six, a thin rim
    case = rbox('kb_case', (W, D, 0.021), (0, 0, 0.0105), M['kb_case'], bevel=0.0058, seg=5); case.parent = root
    # the light bar: a frosted strip low along the front, ribbed, lit from inside
    bar = rbox('kb_halo', (W - 0.016, 0.0030, 0.0062), (0, -D / 2 + 0.0006, 0.0060), M['kb_halo'], bevel=0.0012, seg=2); bar.parent = root
    plate = rbox('kb_well', (W - 0.010, D - 0.010, 0.003), (0, 0, 0.0218), M['kb_plate'], bevel=0.0012); plate.parent = root
    # a small brushed badge top right, where Halo's sits
    badge = rbox('kb_badge', (0.014, 0.0045, 0.0009), (W / 2 - 0.016, D / 2 - 0.0036, 0.0212), M['alu'], bevel=0.0006); badge.parent = root

    # one keycap, nSA-like: tapered walls, a top a little smaller than its foot, a spherical dish, everything rounded
    HEIGHT = [0.0104, 0.0101, 0.0093, 0.0089, 0.0093, 0.0096]   # sculpted: the function row tallest, the home row lowest
    TILT = [-9.0, -6.5, -3.0, 0.0, 3.5, 6.0]                  # each row's top faces the hands
    def cap_mesh(wu, row):
        w = wu * P - 0.0012; d = P - 0.0012; h = HEIGHT[row]
        tw, td = w - 0.0046, d - 0.0046
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
        for v in bm.verts:
            if v.co.z > h / 2: v.co.x *= tw / w; v.co.y *= td / d
        top = [f for f in bm.faces if f.normal.z > 0.9]
        bmesh.ops.subdivide_edges(bm, edges=list({e for f in top for e in f.edges}), cuts=5, use_grid_fill=True)
        dish = 0.0009 if wu <= 1.5 else 0.0006
        for v in bm.verts:
            if v.co.z > h - 1e-5:
                r = (v.co.x / (tw / 2)) ** 2 + (v.co.y / (td / 2)) ** 2
                v.co.z -= dish * max(0.0, 1.0 - r)
        me = bpy.data.meshes.new(f'cap{wu}_{row}'); bm.to_mesh(me); bm.free()
        for p in me.polygons: p.use_smooth = True
        return me
    meshes = {}
    A, G, E = 'alpha', 'mod', 'esc'                          # cream, mint, the deeper mint of Esc and Enter
    rows = [  # (width in units, colour), sixteen units a row, left to right
        [(1, E)] + [(1, G)] * 4 + [(1, A)] * 4 + [(1, G)] * 4 + [(1, A)] * 3,
        [(1, A)] * 13 + [(2, G), (1, G)],
        [(1.5, G)] + [(1, A)] * 12 + [(1.5, A), (1, G)],
        [(1.75, G)] + [(1, A)] * 11 + [(2.25, E), (1, G)],
        [(2.25, G)] + [(1, A)] * 10 + [(1.75, G), (1, G), (1, G)],
        [(1.25, G)] * 3 + [(6.25, A)] + [(1, G)] * 3 + [(1, G)] * 3,
    ]
    for ri, row in enumerate(rows):
        x = -8 * P
        for wu, col in row:
            key = (wu, ri)
            if key not in meshes: meshes[key] = cap_mesh(wu, ri)
            k = link(bpy.data.objects.new(f'key{ri}_{x:.3f}', meshes[key]))
            k.parent = root; w = wu * P
            k.location = (x + w / 2, 2.5 * P - ri * P, 0.0242)
            k.rotation_euler = (math.radians(TILT[ri]), 0, 0)
            bv = k.modifiers.new('bevel', 'BEVEL'); bv.width = 0.0009; bv.segments = 3; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(40)
            ss = k.modifiers.new('ss', 'SUBSURF'); ss.levels = 1; ss.render_levels = 1
            if not k.material_slots: k.data.materials.append(M['cap_' + col])
            k.material_slots[0].link = 'OBJECT'; k.material_slots[0].material = M['cap_' + col]
            x += w
    return root

def mug(M):
    """A stoneware mug, half full, cold: glaze outside, a darker unglazed foot, coffee at rest inside."""
    x, y = 0.545, -0.045                    # on the right, on the bare walnut beside the mat, where a right hand sets it down
    prof = [(0.0, 0.0), (0.038, 0.0), (0.040, 0.003), (0.0415, 0.010), (0.0420, 0.090), (0.0418, 0.0955), (0.0395, 0.0960), (0.0385, 0.0920), (0.0380, 0.012), (0.0, 0.010)]
    body = lathe('mug', prof, (x, y, DT), M['glaze'])
    body.modifiers.new('ss', 'SUBSURF').levels = 1
    # coffee, 2.5 cm below the rim
    cof = cylinder('coffee', 0.0379, 0.002, (x, y, DT + 0.071), M['coffee'], verts=96)
    # the handle: a D-shaped loop whose ends sink into the wall (no gap, no visible intersection)
    pts = [(x + 0.040, y, DT + 0.078), (x + 0.064, y, DT + 0.080), (x + 0.071, y, DT + 0.052), (x + 0.064, y, DT + 0.026), (x + 0.040, y, DT + 0.022)]
    h = curve_tube('mug_handle', pts, 0.0062, M['glaze'])
    h.data.bevel_resolution = 6
    root = link(bpy.data.objects.new('mug_root', None)); root.location = (0, 0, 0)
    for o in (body, cof, h): o.parent = root
    # turn the handle a little toward the camera
    root.location = (0, 0, 0)
    return body, h

_FUR_GROUP = None
def fur_group(M):
    """Fleece as geometry: tiny cones scattered over the surface, standing on its normal with a random lean. They are
    meshes, not hair curves (curves stall Cycles on Metal now and then)."""
    global _FUR_GROUP
    if _FUR_GROUP: return _FUR_GROUP
    ng = bpy.data.node_groups.new('fleece', 'GeometryNodeTree')
    ng.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N = ng.nodes; L = ng.links.new
    gi = N.new('NodeGroupInput'); go = N.new('NodeGroupOutput')
    dist = N.new('GeometryNodeDistributePointsOnFaces'); dist.distribute_method = 'RANDOM'
    dist.inputs['Density'].default_value = 1.5e6; dist.inputs['Seed'].default_value = 7
    cone = N.new('GeometryNodeMeshCone'); cone.inputs['Vertices'].default_value = 3
    cone.inputs['Radius Top'].default_value = 0.000015; cone.inputs['Radius Bottom'].default_value = 0.0001; cone.inputs['Depth'].default_value = 0.0012
    lift = N.new('GeometryNodeTransform'); lift.inputs['Translation'].default_value = (0, 0, 0.00052)
    L(cone.outputs['Mesh'], lift.inputs['Geometry'])
    inst = N.new('GeometryNodeInstanceOnPoints')
    L(dist.outputs['Points'], inst.inputs['Points']); L(lift.outputs['Geometry'], inst.inputs['Instance']); L(dist.outputs['Rotation'], inst.inputs['Rotation'])
    rs = N.new('FunctionNodeRandomValue'); rs.data_type = 'FLOAT'; rs.inputs['Min'].default_value = 0.6; rs.inputs['Max'].default_value = 1.35; rs.inputs['Seed'].default_value = 3
    L(rs.outputs['Value'], inst.inputs['Scale'])
    tilt = N.new('GeometryNodeRotateInstances')
    rr = N.new('FunctionNodeRandomValue'); rr.data_type = 'FLOAT_VECTOR'; rr.inputs['Min'].default_value = (-0.55, -0.55, 0); rr.inputs['Max'].default_value = (0.55, 0.55, 6.28); rr.inputs['Seed'].default_value = 11
    L(inst.outputs['Instances'], tilt.inputs['Instances'])
    eul = N.new('FunctionNodeEulerToRotation'); L(rr.outputs['Value'], eul.inputs['Euler']); L(eul.outputs['Rotation'], tilt.inputs['Rotation'])
    try: tilt.inputs['Local Space'].default_value = True
    except Exception: pass
    mat = N.new('GeometryNodeSetMaterial'); mat.inputs['Material'].default_value = M['fur']
    L(tilt.outputs['Instances'], mat.inputs['Geometry'])
    join = N.new('GeometryNodeJoinGeometry')
    L(gi.outputs['Geometry'], dist.inputs['Mesh']); L(gi.outputs['Geometry'], join.inputs['Geometry']); L(mat.outputs['Geometry'], join.inputs['Geometry'])
    L(join.outputs['Geometry'], go.inputs['Geometry'])
    _FUR_GROUP = ng
    return ng

def fur(o, M, count=None, length=None, children=None):
    mod = o.modifiers.new('fleece', 'NODES'); mod.node_group = fur_group(M)
    o.cycles.use_motion_blur = False; o.cycles.use_deform_motion = False
    return mod

def clawd(M):
    """Clawd as a plush toy: the sprite's blocks (an 8 × 6 body, 2 × 2 arms, four short legs), stuffed: soft edges,
    a little sag, real fleece on it, two black felt eyes."""
    u = 0.0128
    root = link(bpy.data.objects.new('clawd', None)); root.location = (0.255, 0.068, DT); root.rotation_euler = (0, 0, math.radians(-22))
    def part(name, size, loc, bev, n):
        o = rbox(name, size, loc, M['fleece'], bevel=bev, seg=3); o.parent = root
        ss = o.modifiers.new('ss', 'SUBSURF'); ss.levels = 2; ss.render_levels = 2
        fur(o, M, count=n)
        return o
    LEG = 1.75 * u
    body = part('clawd_body', (8 * u, 5.2 * u, 6 * u), (0, 0, LEG + 3 * u - 0.15 * u), 1.2 * u, 16000)
    tex = bpy.data.textures.new('stuff', 'CLOUDS'); tex.noise_scale = 0.03
    dp = body.modifiers.new('stuffed', 'DISPLACE'); dp.texture = tex; dp.strength = 0.0016; dp.mid_level = 0.5
    body.modifiers.move(len(body.modifiers) - 1, 1)
    for sx in (-1, 1):
        part(f'clawd_arm{sx}', (2.4 * u, 2.6 * u, 2.1 * u), (sx * (4 * u + 1.05 * u), 0, LEG + 6 * u - 3 * u), 0.8 * u, 3000)
    for i, lx in enumerate((-3.5, -1.5, 1.5, 3.5)):
        part(f'clawd_leg{i}', (1.25 * u, 2.5 * u, LEG + 0.6 * u), (lx * u, 0.05 * u, (LEG + 0.6 * u) / 2), 0.5 * u, 1500)
    for sx in (-1, 1):
        e = rbox(f'clawd_eye{sx}', (1.0 * u, 0.4 * u, 1.3 * u), (sx * 2.5 * u, -2.66 * u, LEG + 6 * u - 1.55 * u), M['felt_black'], bevel=0.25 * u, seg=3); e.parent = root
    return root

def phone(M):
    """An iPhone face up on the mat, left of the keyboard. Its screen is black glass that reflects the room until a
    message wakes it (shot.py keys 'wake' on its material and buzzes the phone)."""
    root = link(bpy.data.objects.new('phone', None)); root.location = (-0.300, -0.035, DT + MAT); root.rotation_euler = (0, 0, math.radians(8))
    body = rbox('phone_body', (0.0716, 0.1476, 0.0078), (0, 0, 0.0039), M['phone_frame'], bevel=0.0095, seg=6); body.parent = root
    glass = rbox('phone_glass', (0.0690, 0.1450, 0.0006), (0, 0, 0.0079), M['phone_screen'], bevel=0.0085, seg=6); glass.parent = root
    lens = cylinder('phone_cam', 0.0055, 0.0012, (0, 0, 0.0002), M['black_glass'], verts=32); lens.parent = root; lens.location = (0.022, 0.058, -0.0002)
    me = glass.data
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co.x / 0.069 + 0.5, co.y / 0.145 + 0.5)
    return root

def phone_screen_mat(name, path):
    """Black glass that shows the lock screen as light when 'wake' > 0."""
    m, nt, b = node_mat(name); L = nt.links.new
    b.inputs['Base Color'].default_value = (0.003, 0.003, 0.004, 1); b.inputs['Roughness'].default_value = 0.04
    b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.02
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(path)); tex.interpolation = 'Cubic'
    L(tex.outputs['Color'], b.inputs['Emission Color'])
    wake = nt.nodes.new('ShaderNodeValue'); wake.name = wake.label = 'wake'; wake.outputs[0].default_value = 0.0
    L(wake.outputs[0], b.inputs['Emission Strength'])
    return m

def lamp(M):
    """A desk lamp on the right, its head low over the desk, a warm bulb turned down."""
    bx, by = 0.63, 0.30
    base = cylinder('lamp_base', 0.068, 0.016, (bx, by, DT + 0.008), M['lamp_black'], bevel=0.005)
    a = mathutils.Vector((bx, by, DT + 0.016)); b = mathutils.Vector((bx + 0.03, by + 0.02, DT + 0.36)); c = mathutils.Vector((bx - 0.17, by - 0.10, DT + 0.43))
    for n, (p, q) in enumerate(((a, b), (b, c))):
        v = q - p; o = cylinder(f'lamp_arm{n}', 0.0065, v.length, (p + q) / 2, M['lamp_black'], verts=24)
        o.rotation_euler = v.to_track_quat('Z', 'Y').to_euler()
    j = link(bpy.data.objects.new('lamp_joint', bpy.data.meshes.new('lj'))); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.012); bm.to_mesh(j.data); bm.free(); j.location = b; j.data.materials.append(M['lamp_black'])
    for p in j.data.polygons: p.use_smooth = True
    head = cylinder('lamp_head', 0.042, 0.10, c + mathutils.Vector((0, 0, -0.012)), M['lamp_black'], verts=48, r2=0.030)
    head.rotation_euler = mathutils.Vector((0.25, 0.4, -1)).to_track_quat('-Z', 'Y').to_euler()
    bulb = link(bpy.data.objects.new('lamp_bulb', bpy.data.meshes.new('lb'))); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.016); bm.to_mesh(bulb.data); bm.free()
    bulb.location = c + mathutils.Vector((-0.012, -0.024, -0.05)); bulb.data.materials.append(M['bulb'])
    return c + mathutils.Vector((-0.012, -0.024, -0.05))

def leaf_strip(name, mat, base, height, width, lean, lean_dir, twist, fold, seed):
    """One sansevieria leaf: a blade from the soil to a sharp tip, narrow at the base, widest a little below the middle,
    slightly folded along its length, leaning out and turning a little as it rises. u runs across it, v up it."""
    import random
    rnd = random.Random(seed)
    NU, NV = 6, 28
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    up = mathutils.Vector((0, 0, 1)); out = mathutils.Vector((math.cos(lean_dir), math.sin(lean_dir), 0))
    rows = []
    for j in range(NV + 1):
        v = j / NV
        # the spine: up, bending out more toward the top
        bend = lean * (0.35 * v + 0.65 * v * v)
        c = mathutils.Vector(base) + up * (height * v) + out * (height * bend)
        tangent = (up + out * (lean * (0.35 + 1.3 * v))).normalized()
        side = tangent.cross(out).normalized()
        if side.length < 0.5: side = mathutils.Vector((-out.y, out.x, 0))
        normal = side.cross(tangent).normalized()
        ang = twist * v + rnd.uniform(-0.02, 0.02)
        side_r = side * math.cos(ang) + normal * math.sin(ang); norm_r = normal * math.cos(ang) - side * math.sin(ang)
        wv = width * ((0.38 + 0.62 * math.sin(min(1.0, v / 0.48) * math.pi / 2)) if v < 0.48 else (1 - ((v - 0.48) / 0.52) ** 1.7))
        wv = max(wv, 0.0006)
        row = []
        for i in range(NU + 1):
            u = i / NU * 2 - 1
            p = c + side_r * (u * wv / 2) + norm_r * (fold * wv * u * u)
            row.append(bm.verts.new(p))
        rows.append(row)
    for j in range(NV):
        for i in range(NU):
            f = bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
            for loop, (di, dj) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                loop[uvl].uv = ((i + di) / NU, (j + dj) / NV)
    o = mesh_obj(name, bm, mat)
    sol = o.modifiers.new('thick', 'SOLIDIFY'); sol.thickness = 0.0016; sol.offset = 0
    ss = o.modifiers.new('ss', 'SUBSURF'); ss.levels = 1; ss.render_levels = 2
    return o

def sansevieria_mat(name):
    """Snake-plant green: dark leaf with paler grey-green bands that wave across it, a cream-yellow edge, waxy."""
    m, nt, b = node_mat(name); L = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ'); L(tc.outputs['UV'], sep.inputs[0])
    wave = nt.nodes.new('ShaderNodeTexWave'); wave.wave_type = 'BANDS'; wave.bands_direction = 'Y'
    wave.inputs['Scale'].default_value = 9.0; wave.inputs['Distortion'].default_value = 7.0; wave.inputs['Detail'].default_value = 3.0
    L(tc.outputs['UV'], wave.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB'); r = ramp.color_ramp
    r.elements[0].position = 0.35; r.elements[0].color = (*srgb('#173520'), 1); r.elements[1].position = 0.75; r.elements[1].color = (*srgb('#5f7f55'), 1)
    L(wave.outputs['Fac'], ramp.inputs['Fac'])
    # the margins: |u − 0.5| > 0.42 → cream
    d = nt.nodes.new('ShaderNodeMath'); d.operation = 'SUBTRACT'; d.inputs[1].default_value = 0.5; L(sep.outputs['X'], d.inputs[0])
    a = nt.nodes.new('ShaderNodeMath'); a.operation = 'ABSOLUTE'; L(d.outputs[0], a.inputs[0])
    edge = nt.nodes.new('ShaderNodeMapRange'); edge.inputs['From Min'].default_value = 0.40; edge.inputs['From Max'].default_value = 0.46; L(a.outputs[0], edge.inputs['Value'])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; L(edge.outputs['Result'], mix.inputs['Factor']); L(ramp.outputs['Color'], mix.inputs['A']); mix.inputs['B'].default_value = (*srgb('#d6c76a'), 1)
    L(mix.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.42; b.inputs['Coat Weight'].default_value = 0.35; b.inputs['Coat Roughness'].default_value = 0.18
    b.inputs['Subsurface Weight'].default_value = 0.12; b.inputs['Subsurface Radius'].default_value = (0.003, 0.006, 0.002)
    return m

def plant(M):
    """A snake plant in a speckled cream pot on a little ash saucer, back left, by the window: its leaves catch the
    moonlight through the blinds and stand dark against them."""
    px, py = -0.585, 0.275
    lathe('saucer', [(0.0, 0.0), (0.066, 0.0), (0.069, 0.004), (0.069, 0.010), (0.064, 0.010), (0.062, 0.004), (0.0, 0.004)], (px, py, DT), M['ash'])
    pot = lathe('pot', [(0.0, 0.004), (0.046, 0.004), (0.050, 0.010), (0.058, 0.098), (0.061, 0.104), (0.059, 0.110), (0.054, 0.110), (0.052, 0.102), (0.0, 0.098)],
                (px, py, DT), M['pot'])
    pot.modifiers.new('ss', 'SUBSURF').levels = 1
    cylinder('soil', 0.052, 0.003, (px, py, DT + 0.1015), M['soil'], verts=64)
    # top dressing: small pale pebbles
    import random
    rnd = random.Random(5)
    peb = bpy.data.meshes.new('pebble'); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); bm.to_mesh(peb); bm.free()
    for p in peb.polygons: p.use_smooth = True
    peb.materials.append(M['pebble'])
    for i in range(70):
        a = rnd.uniform(0, math.tau); r = 0.048 * math.sqrt(rnd.random())
        o = link(bpy.data.objects.new(f'pebble{i}', peb)); s_ = rnd.uniform(0.0028, 0.0052)
        o.scale = (s_ * rnd.uniform(0.9, 1.3), s_, s_ * 0.7); o.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3))
        o.location = (px + math.cos(a) * r, py + math.sin(a) * r, DT + 0.103 + s_ * 0.3)
    mat = M['sansevieria']
    leaves = [  # (angle round the pot, distance out, height, width, lean, twist)
        (0.3, 0.012, 0.36, 0.050, 0.10, 0.5), (1.4, 0.018, 0.30, 0.046, 0.18, -0.4), (2.6, 0.015, 0.39, 0.052, 0.08, 0.3),
        (3.7, 0.020, 0.27, 0.044, 0.22, -0.6), (4.8, 0.014, 0.33, 0.048, 0.14, 0.45), (5.6, 0.022, 0.24, 0.040, 0.26, -0.3),
        (0.9, 0.006, 0.42, 0.054, 0.05, 0.2), (2.0, 0.026, 0.20, 0.036, 0.30, 0.6), (4.2, 0.008, 0.37, 0.050, 0.09, -0.25),
    ]
    for i, (ang, dist, h, w, lean, tw) in enumerate(leaves):
        base = (px + math.cos(ang) * dist, py + math.sin(ang) * dist, DT + 0.100)
        leaf_strip(f'sans_leaf{i}', mat, base, h, w, lean, ang, tw, 0.16, i * 17 + 3)

def magic_mouse(M):
    """Apple Magic Mouse, to its spec (113.5 × 57.1 × 21.6 mm): a thin aluminium base, a short flat white side wall
    (about 3 mm), and a low plain arc on top that peaks a little behind the middle, where the palm lies. It sits on
    the mat where the right hand left it."""
    root = link(bpy.data.objects.new('magic_mouse', None)); root.location = (0.262, -0.072, DT + MAT); root.rotation_euler = (0, 0, math.radians(-7))
    A, B, n = 0.05675, 0.02855, 2.6           # half length, half width, super-ellipse exponent of the outline
    H, ZB, ZE = 0.0216, 0.0032, 0.0066        # peak height, top of the aluminium base, top of the white side wall
    Y0 = -0.10 * A                            # where the arc peaks (toward the back, −y)
    def outline(th, k=1.0):
        c, s_ = math.cos(th), math.sin(th)
        return (B * k * math.copysign(abs(c) ** (2 / n), c), A * k * math.copysign(abs(s_) ** (2 / n), s_))
    def zc(y):                                # the height along the centre line
        sgn = (y - Y0) / (A - Y0) if y >= Y0 else (Y0 - y) / (A + Y0)
        return ZE + (H - ZE) * max(0.0, 1 - min(1.0, abs(sgn)) ** 2.0) ** 1.0
    def xmax(y): return B * max(0.0, 1 - abs(y / A) ** n) ** (1 / n)
    def ztop(x, y):
        xm = xmax(y); u = 0.0 if xm < 1e-6 else min(1.0, abs(x) / xm)
        return ZE + (zc(y) - ZE) * max(0.0, 1 - u * u) ** 0.95
    NR, NT = 22, 96
    bm = bmesh.new(); rings = []
    for i in range(NR + 1):
        rho = i / NR
        ring = []
        for j in range(NT):
            x, y = outline(j / NT * math.tau, rho)
            ring.append(bm.verts.new((x, y, ztop(x, y) if i < NR else ZE)))
        rings.append(ring)
    wall = [bm.verts.new((v.co.x, v.co.y, ZB + 0.0002)) for v in rings[-1]]
    centre = bm.verts.new((0, Y0 * 0.0, zc(0.0)))
    for j in range(NT): bm.faces.new((centre, rings[0][j], rings[0][(j + 1) % NT]))
    for i in range(NR):
        for j in range(NT): bm.faces.new((rings[i][j], rings[i + 1][j], rings[i + 1][(j + 1) % NT], rings[i][(j + 1) % NT]))
    for j in range(NT): bm.faces.new((rings[-1][j], wall[j], wall[(j + 1) % NT], rings[-1][(j + 1) % NT]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    shell = mesh_obj('mm_shell', bm, M['mm_white']); shell.parent = root
    # the crisp edge where the top meets the side wall, softened a hair
    bv = shell.modifiers.new('edge', 'BEVEL'); bv.width = 0.0006; bv.segments = 2; bv.limit_method = 'ANGLE'; bv.angle_limit = math.radians(40)
    # the base: an aluminium plate the width of the shell, its edge slightly rounded under the seam
    bm = bmesh.new(); top = []; bot = []
    for j in range(NT):
        x, y = outline(j / NT * math.tau, 1.0); xb, yb = outline(j / NT * math.tau, 0.965)
        top.append(bm.verts.new((x * 0.996, y * 0.996, ZB))); bot.append(bm.verts.new((xb, yb, 0.0003)))
    bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    for j in range(NT): bm.faces.new((bot[j], bot[(j + 1) % NT], top[(j + 1) % NT], top[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    base = mesh_obj('mm_base', bm, M['alu']); base.parent = root
    # the dark hairline seam between the shell and the base
    bm = bmesh.new(); ring = [bm.verts.new((*outline(j / NT * math.tau, 1.0005), ZB + 0.0001)) for j in range(NT)]
    ring2 = [bm.verts.new((*outline(j / NT * math.tau, 1.0005), ZB + 0.00045)) for j in range(NT)]
    for j in range(NT): bm.faces.new((ring[j], ring[(j + 1) % NT], ring2[(j + 1) % NT], ring2[j]))
    seam = mesh_obj('mm_seam', bm, M['rubber']); seam.parent = root
    return root

def ssd(M):
    root = link(bpy.data.objects.new('ssd', None)); root.location = (0.43, 0.17, DT); root.rotation_euler = (0, 0, math.radians(-8))
    b = rbox('ssd_body', (0.057, 0.085, 0.0092), (0, 0, 0.0046), M['ssd'], bevel=0.0035); b.parent = root
    led = rbox('ssd_led', (0.004, 0.0012, 0.0012), (0.018, -0.0426, 0.0055), M['led_blue']); led.parent = root
    return root

def sticky(name, mat, w, loc, rot_z, curl, hang_from_top=True, face=(0, -1, 0)):
    """A note stuck by its glue strip, the rest falling away from the surface a little (more at the free edge)."""
    bm = bmesh.new(); n = 18
    for j in range(n + 1):
        for i in range(n + 1):
            u, v = i / n, j / n                      # v = 0 at the glue strip (top), 1 at the free edge
            free = max(0.0, (v - 0.2) / 0.8)
            bm.verts.new(((u - 0.5) * w, -curl * free ** 2 - 0.0002, -v * w))
    bm.verts.ensure_lookup_table()
    uvs = []
    for j in range(n):
        for i in range(n):
            a = j * (n + 1) + i
            f = bm.faces.new((bm.verts[a], bm.verts[a + 1], bm.verts[a + n + 2], bm.verts[a + n + 1])); uvs.append((f, i, j))
    uvl = bm.loops.layers.uv.new('UVMap')
    for f, i, j in uvs:
        for loop, (di, dj) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = ((i + di) / n, 1 - (j + dj) / n)
    o = mesh_obj(name, bm, mat); o.location = loc; o.rotation_euler = (0, 0, 0)
    o.rotation_euler = (0, math.radians(rot_z), 0)          # one sheet of paper: a single surface, no thickness to shade
    return o

def washi(name, w, loc, rot_y, tex):
    """A short piece of washi tape: matte paper tape with a tiny print and torn ends, a little see-through."""
    m = pbr(name + '_m', (1, 1, 1), 0.88, sss=0.2, sss_radius=(0.002, 0.002, 0.002))
    nt = m.node_tree; bsdf = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(TEX / tex)); t.extension = 'CLIP'
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], bsdf.inputs['Alpha'])
    bm = bmesh.new(); h = w * 0.35
    vs = [bm.verts.new((x * w / 2, 0, z * h / 2)) for x, z in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; f = bm.faces.new(vs)
    uvl = bm.loops.layers.uv.new('UVMap')
    for loop, uvv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): loop[uvl].uv = uvv
    o = mesh_obj(name, bm, m); o.location = loc; o.rotation_euler = (0, math.radians(rot_y), 0); o.visible_shadow = False
    return o

def poster(name, path, w, h, centre, WY, tape_colors, curl=0.004, tilt=0.0):
    """An unframed print taped to the wall at its top corners; the paper bows off the wall a little toward the bottom."""
    pm = pbr(name + '_paper', (1, 1, 1), 0.62, sss=0.05, sss_radius=(0.002, 0.002, 0.002))
    nt = pm.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(path)); t.interpolation = 'Cubic'
    nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    bm = bmesh.new(); NU, NV = 10, 14; uvl = bm.loops.layers.uv.new('UVMap'); rows = []
    for j in range(NV + 1):
        v = j / NV; row = []
        for i in range(NU + 1):
            u = i / NU
            off = curl * (v ** 2.2) * (0.6 + 0.4 * abs(u * 2 - 1) ** 2)      # the bottom corners lift most
            row.append(bm.verts.new(((u - 0.5) * w, -0.0004 - off, (0.5 - v) * h)))
        rows.append(row)
    for j in range(NV):
        for i in range(NU):
            f = bm.faces.new((rows[j + 1][i], rows[j + 1][i + 1], rows[j][i + 1], rows[j][i]))
            for loop, (di, dj) in zip(f.loops, ((0, 1), (1, 1), (1, 0), (0, 0))):
                loop[uvl].uv = ((i + di) / NU, 1 - (j + dj) / NV)
    o = mesh_obj(name, bm, pm); o.location = (centre[0], WY, centre[1]); o.rotation_euler = (0, math.radians(tilt), 0)
    o.modifiers.new('thick', 'SOLIDIFY').thickness = 0.0002
    for k, sx in enumerate((-1, 1)):
        x = centre[0] + sx * (w / 2 - 0.006); z = centre[1] + h / 2 - 0.004
        washi(f'{name}_tape{k}', 0.032, (x, WY - 0.0008, z), sx * 42 + tilt, tape_colors[k])
    return o

def fairy_lights(M, a, b, sag, n, WY):
    """Warm string lights hung on two pins: a thin wire in a catenary, small bulbs along it, a few dimmer than others."""
    import random
    rnd = random.Random(11)
    pts = []
    for i in range(41):
        k = i / 40
        x = a[0] + (b[0] - a[0]) * k; z = a[1] + (b[1] - a[1]) * k - sag * 4 * k * (1 - k)
        pts.append((x, WY - 0.012 - 0.01 * math.sin(math.pi * k), z))
    curve_tube('fairy_wire', pts, 0.0007, M['wire'], res=4)
    for p in (a, b):
        cylinder('pin', 0.003, 0.004, (p[0], WY - 0.002, p[1]), M['alu'], verts=16, rot=(90, 0, 0))
    bulbs = []
    for i in range(n):
        k = (i + 0.5) / n
        x = a[0] + (b[0] - a[0]) * k; z = a[1] + (b[1] - a[1]) * k - sag * 4 * k * (1 - k) - 0.008
        y = WY - 0.012 - 0.01 * math.sin(math.pi * k)
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.0030)
        me = bpy.data.meshes.new(f'bulb{i}'); bm.to_mesh(me); bm.free()
        mat = M['fairy_dim'] if rnd.random() < 0.25 else M['fairy']
        me.materials.append(mat)
        o = link(bpy.data.objects.new(f'fairy{i}', me)); o.location = (x, y, z); o.scale = (1, 1, 1.35)
        o.visible_shadow = False
        bulbs.append(o)
    return bulbs

def image_card(name, path, w, h, loc, rot_y, M, rough=0.45):
    """A print, card thin, its picture on the front."""
    m = pbr(name + '_m', (1, 1, 1), rough, sss=0.03, sss_radius=(0.002, 0.002, 0.002))
    nt = m.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(path)); t.interpolation = 'Cubic'
    nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    bm = bmesh.new(); vs = [bm.verts.new((x * w / 2, 0, z * h / 2)) for x, z in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; f = bm.faces.new(vs)
    uvl = bm.loops.layers.uv.new('UVMap')
    for loop, uvv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): loop[uvl].uv = uvv
    o = mesh_obj(name, bm, m); o.location = loc; o.rotation_euler = (0, math.radians(rot_y), 0)
    o.modifiers.new('thick', 'SOLIDIFY').thickness = 0.0006
    return o

def switch_console(M, root, loc, lean):
    """A Nintendo Switch standing on its little shelf, leaning back against the board: the dark tablet with its
    neon-blue and neon-red controllers on either side, the sticks and buttons picked out."""
    g = link(bpy.data.objects.new('switch', None)); g.parent = root; g.location = loc; g.rotation_euler = (math.radians(-lean), 0, 0)
    H = 0.1016
    body = rbox('sw_body', (0.1732, 0.0139, H), (0, 0, H / 2), M['sw_black'], bevel=0.005); body.parent = g
    scr = rbox('sw_screen', (0.1390, 0.0010, 0.0782), (0, -0.0070, H / 2), M['black_glass'], bevel=0.0008); scr.parent = g
    for side, col, x in (('L', M['joy_blue'], -0.1732 / 2 - 0.0177), ('R', M['joy_red'], 0.1732 / 2 + 0.0177)):
        j = rbox(f'joy{side}', (0.0354, 0.0139, H), (x, 0, H / 2), col, bevel=0.0075, seg=6); j.parent = g
        sx = x + (0.002 if side == 'L' else -0.002)
        stick_z = H - 0.030 if side == 'L' else 0.037
        st = cylinder(f'stick{side}', 0.0085, 0.006, (sx, -0.0085, stick_z), M['sw_dark'], verts=32, rot=(90, 0, 0), bevel=0.0015); st.parent = g
        bz = 0.037 if side == 'L' else H - 0.030
        for k, (dx, dz) in enumerate(((0, 0.0085), (0, -0.0085), (0.0085, 0), (-0.0085, 0))):
            bt = cylinder(f'btn{side}{k}', 0.0033, 0.0022, (sx + dx, -0.0076, bz + dz), M['sw_dark'], verts=16, rot=(90, 0, 0)); bt.parent = g
    return g

def headphones(M, root, hook, R=0.062, CR=0.034):
    """Over-ear headphones hung by their band on a peg: the band over the hook, the cups hanging below it."""
    g = link(bpy.data.objects.new('headphones', None)); g.parent = root; g.location = hook
    bm = bmesh.new(); bmesh.ops.create_circle(bm, segments=48, radius=R)
    me = bpy.data.meshes.new('band_path'); bm.to_mesh(me); bm.free()
    pts = [(R * math.cos(a), -0.012, -R * math.sin(a) + R * 0.98) for a in [math.pi * (i / 24) for i in range(25)]]
    pts = [(x, y, -abs(z - R * 0.98) + 0.004) for x, y, z in pts]
    band = curve_tube('hp_band', [(R * math.cos(math.pi * i / 24), -0.014, -(R - R * math.sin(math.pi * i / 24)) - 0.004) for i in range(25)], 0.0075, M['hp_black'], res=6)
    band.parent = g
    for sx in (-1, 1):
        cx = sx * R
        cup = cylinder(f'hp_cup{sx}', CR, 0.022, (cx + sx * 0.004, -0.030, -R - 0.030), M['hp_black'], verts=48, rot=(0, 90, 0), bevel=0.004); cup.parent = g
        pad = link(bpy.data.objects.new(f'hp_pad{sx}', bpy.data.meshes.new(f'pad{sx}'))); bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=CR * 0.95, radius2=CR * 0.85, depth=0.014); bm.to_mesh(pad.data); bm.free()
        for p in pad.data.polygons: p.use_smooth = True
        pad.data.materials.append(M['hp_pad']); pad.parent = g; pad.location = (cx - sx * 0.014, -0.030, -R - 0.030); pad.rotation_euler = (0, math.radians(90), 0)
        sl = rbox(f'hp_slider{sx}', (0.006, 0.010, 0.040), (cx, -0.026, -R + 0.006), M['alu']); sl.parent = g
    return g

def pen_cup(M, root, loc):
    """A pen cup on the desk: pens, a marker, a pencil, and the scissors (of course)."""
    g = link(bpy.data.objects.new('pen_cup', None))
    if root: g.parent = root
    g.location = loc
    cup = lathe('cup', [(0.0, 0.0), (0.034, 0.0), (0.035, 0.002), (0.035, 0.090), (0.032, 0.090), (0.032, 0.004), (0.0, 0.004)], (0, 0, 0), M['cup_metal'])
    cup.parent = g
    import random
    rnd = random.Random(8)
    items = [(0.0055, 0.150, M['pen_black'], -0.012, 0.010, 8), (0.0055, 0.148, M['pen_blue'], 0.010, 0.012, -6), (0.0075, 0.135, M['marker'], 0.006, -0.012, 4),
             (0.0040, 0.175, M['pencil'], -0.014, -0.010, -9)]
    for k, (r, h, m, dx, dy, tilt) in enumerate(items):
        o = cylinder(f'pen{k}', r, h, (dx, dy, h / 2 + 0.004), m, verts=16, rot=(tilt * 0.6, tilt, 0)); o.parent = g
        cap = cylinder(f'pencap{k}', r * 1.1, 0.02, (dx + math.sin(math.radians(tilt)) * h / 2, dy, h + 0.004), M['pen_cap'] if k < 3 else M['eraser'], verts=16, rot=(tilt * 0.6, tilt, 0)); cap.parent = g
    # the scissors: handles up, two orange loops
    for k, sx in enumerate((-1, 1)):
        loop = link(bpy.data.objects.new(f'sc_loop{k}', bpy.data.meshes.new(f'scl{k}'))); bm = bmesh.new()
        bmesh.ops.create_circle(bm, segments=1, radius=1)
        bm.free()
        lp = curve_tube(f'sc_handle{k}', [(sx * 0.010 + 0.016 * math.cos(a), 0.004, 0.155 + 0.011 * math.sin(a)) for a in [i / 16 * math.tau for i in range(17)]], 0.0028, M['scissor'], res=4)
        lp.parent = g; bpy.data.objects.remove(loop)
        bl = rbox(f'sc_blade{k}', (0.004, 0.0012, 0.10), (sx * 0.004, 0.004, 0.090), M['steel_bright']); bl.parent = g
        bl.rotation_euler = (0, math.radians(sx * 4), 0)
    return g

def pegboard(M, centre, WY):
    """A birch pegboard 2 cm off the wall: three instant prints pinned along the top (the trip, the friends, the cat),
    the Switch on a little shelf, headphones on a peg, a cup of pens. Board-local: x right, z up, −y toward the room."""
    BW, BH, BT = 0.40, 0.40, 0.012
    root = link(bpy.data.objects.new('pegboard', None)); root.location = (centre[0], WY - 0.020 - BT / 2, centre[1])
    pm = pbr('pegboard_m', (1, 1, 1), 0.66)
    nt = pm.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(TEX / 'pegboard.jpg'))
    dk = nt.nodes.new('ShaderNodeMix'); dk.data_type = 'RGBA'; dk.blend_type = 'MULTIPLY'; dk.inputs['Factor'].default_value = 1.0
    dk.inputs['B'].default_value = (0.50, 0.47, 0.44, 1)
    nt.links.new(t.outputs['Color'], dk.inputs['A']); nt.links.new(dk.outputs['Result'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    board = rbox('pegboard', (BW, BT, BH), (0, 0, 0), pm, bevel=0.002); board.parent = root
    me = board.data; uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co.x / BW + 0.5, co.z / BH + 0.5)
    for sx in (-1, 1):
        for sz in (-1, 1):
            sp = cylinder('spacer', 0.006, 0.020, (sx * (BW / 2 - 0.03), BT / 2 + 0.010, sz * (BH / 2 - 0.03)), M['alu'], verts=16, rot=(90, 0, 0)); sp.parent = root
    F = -BT / 2                                                   # the board's front face (local y)
    def peg(x, z, length=0.035, up=True):
        p = cylinder('peg', 0.0022, length, (x, F - length / 2, z), M['steel_bright'], verts=12, rot=(90, 0, 0)); p.parent = root
        if up:
            tip = cylinder('peg_tip', 0.0022, 0.012, (x, F - length, z + 0.006), M['steel_bright'], verts=12); tip.parent = root
        return p
    # the prints, pinned at their tops with coloured push pins
    prints = [('print_road', TEX / 'print_road.jpg', 0.108, 0.086, -0.128, 0.130, -4.0, (0.95, 0.30, 0.25)),
              ('print_friends', TEX / 'print_friends.jpg', 0.090, 0.090, -0.018, 0.126, 3.0, (0.25, 0.60, 0.95)),
              ('print_cat', TEX / 'print_cat.jpg', 0.090, 0.090, -0.122, 0.022, -2.5, (0.98, 0.80, 0.25))]
    for name, path, w, h, x, z, rot, pin in prints:
        c = image_card(name, path, w, h, (x, F - 0.0012, z), rot, M); c.parent = root
        pin_m = pbr(name + '_pin', pin, 0.25, coat=0.6)
        hd = link(bpy.data.objects.new(name + '_pinhead', bpy.data.meshes.new(name + '_ph'))); bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.0055); bm.to_mesh(hd.data); bm.free()
        hd.data.materials.append(pin_m); hd.parent = root; hd.location = (x, F - 0.0075, z + h / 2 - 0.008)
        for p_ in hd.data.polygons: p_.use_smooth = True
    # the shelf and the Switch on it
    SX, SZ = -0.070, -0.135
    shelf = rbox('shelf', (0.27, 0.075, 0.010), (SX, F - 0.0375, SZ), M['ash'], bevel=0.0015); shelf.parent = root
    lip = rbox('shelf_lip', (0.27, 0.006, 0.018), (SX, F - 0.072, SZ + 0.009), M['ash'], bevel=0.001); lip.parent = root
    for x in (SX - 0.10, SX + 0.10):
        br = rbox('shelf_bracket', (0.008, 0.06, 0.04), (x, F - 0.03, SZ - 0.023), M['steel_bright'], bevel=0.001); br.parent = root
    switch_console(M, root, (SX, F - 0.030, SZ + 0.005), 9)
    # headphones on a long peg, top right
    peg(0.125, 0.135, length=0.05)
    headphones(M, root, (0.125, F - 0.030, 0.135))
    # the client's note, stuck on bottom right, clear of the shelf
    note = sticky('note_pink', paper('note_p', TEX / 'note_pink.png'), 0.072, (0.118, F - 0.0008, -0.040), 0, 0.0012); note.parent = root
    note.rotation_euler = (0, math.radians(4), 0)
    return root

def frame_print(M):
    """A print of the winter road in a thin black frame, leaning against the wall at the back of the desk."""
    root = link(bpy.data.objects.new('print', None)); root.location = (0.47, 0.365, DT); root.rotation_euler = (math.radians(-9), 0, math.radians(-4))
    W, H, D = 0.21, 0.27, 0.014
    fr = rbox('print_frame', (W, D, H), (0, 0, H / 2), M['lamp_black'], bevel=0.002); fr.parent = root
    mat = rbox('print_mat', (W - 0.02, 0.002, H - 0.02), (0, -D / 2 - 0.0005, H / 2), M['paper_white']); mat.parent = root
    ph_m, _, _ = image_emit('print_photo_tex', HERE / 'pr' / 'img' / 'snow-12.0.jpg', 0.0)
    pm = pbr('print_photo', (1, 1, 1), 0.35); nt = pm.node_tree; t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(HERE / 'pr' / 'img' / 'snow-12.0.jpg'))
    nt.links.new(t.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    pw, ph = W - 0.06, (W - 0.06) * 9 / 16 * 1.6
    bm = bmesh.new(); vs = [bm.verts.new((x * pw / 2, 0, z * ph / 2)) for x, z in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; f = bm.faces.new(vs)
    uvl = bm.loops.layers.uv.new('UVMap')
    for loop, uvv in zip(f.loops, ((0.18, 0), (0.82, 0), (0.82, 1), (0.18, 1))): loop[uvl].uv = uvv
    o = mesh_obj('print_photo', bm, pm); o.parent = root; o.location = (0, -D / 2 - 0.0017, H / 2 + 0.01)
    gl = rbox('print_glass', (W - 0.012, 0.0015, H - 0.012), (0, -D / 2 - 0.003, H / 2), M['glass']); gl.parent = root

def build_room(collection):
    global COL; COL = collection
    M = {
        'wall': add_bump(pbr('wall', srgb('#4a4a50'), 0.92), 120, 0.03),
        'trim': pbr('trim', srgb('#8f8f93'), 0.55),
        'slat': pbr('slat', srgb('#a4a6ab'), 0.36, 0.35),
        'cord': pbr('cord', srgb('#c8c6c0'), 0.8),
        'floor': pbr('floor', srgb('#2a211b'), 0.55),
        'desk': walnut('walnut'),
        'steel': pbr('steel', srgb('#1a1a1c'), 0.38, 1.0),
        'alu': pbr('alu', srgb('#c4c6ca'), 0.24, 1.0, aniso=0.4),
        'alu_dark': pbr('alu_dark', srgb('#2e2f33'), 0.45, 1.0),
        'kb_case': add_bump(pbr('kb_case', srgb('#a9d8b8'), 0.36, coat=0.45, coat_rough=0.18, sss=0.25, sss_radius=(0.004, 0.006, 0.005)), 1600, 0.05, 2, distance=0.0001),
        'kb_plate': pbr('kb_plate', srgb('#e4ece4'), 0.6),
        'cap_alpha': add_bump(pbr('cap_alpha', srgb('#f2ede0'), 0.58, sss=0.03, sss_radius=(0.002, 0.0015, 0.001)), 900, 0.12, 2, distance=0.0002),
        'cap_mod': add_bump(pbr('cap_mod', srgb('#a3d3aa'), 0.58, sss=0.03, sss_radius=(0.002, 0.0015, 0.001)), 900, 0.12, 2, distance=0.0002),
        'cap_esc': add_bump(pbr('cap_esc', srgb('#7fc395'), 0.56, sss=0.03, sss_radius=(0.002, 0.0015, 0.001)), 900, 0.12, 2, distance=0.0002),
        'mat': add_bump(pbr('desk_mat', srgb('#2f3033'), 0.95, sheen=0.4), 1400, 0.25, 2, distance=0.0003),
        'black_glass': pbr('black_glass', (0.002, 0.002, 0.002), 0.04, coat=1.0, coat_rough=0.02),
        'glaze': speckled(pbr('glaze', srgb('#ebe5da'), 0.22, coat=0.7, coat_rough=0.04, sss=0.04, sss_radius=(0.004, 0.003, 0.002))),
        'fur': pbr('fur', srgb('#e07a55'), 0.85, sheen=1.0, sheen_rough=0.3, sss=0.15, sss_radius=(0.004, 0.0015, 0.001)),
        'coffee': pbr('coffee', srgb('#1c0e07'), 0.06, ior=1.34),
        'fleece': add_bump(pbr('fleece', srgb('#de7350'), 0.92, sheen=1.0, sheen_rough=0.35, sss=0.08, sss_radius=(0.01, 0.004, 0.002)), 1600, 0.35, 3, distance=0.0004),
        'felt_black': pbr('felt_black', (0.006, 0.006, 0.006), 0.95, sheen=0.6),
        'phone_frame': pbr('phone_frame', srgb('#2b2c30'), 0.28, 1.0),
        'lamp_black': pbr('lamp_black', srgb('#1d1d1f'), 0.45, 0.3),
        'concrete': add_bump(pbr('concrete', srgb('#8a8884'), 0.9), 300, 0.2, 4),
        'soil': add_bump(pbr('soil', srgb('#2a1d14'), 1.0), 500, 0.4, 2),
        'succulent': pbr('succulent', srgb('#8fb19a'), 0.48, sss=0.25, sss_radius=(0.004, 0.006, 0.003), coat=0.3),
        'ssd': pbr('ssd', srgb('#2d4a6e'), 0.4, 0.9),
        'rubber': pbr('rubber', srgb('#111113'), 0.7),
        'paper_white': pbr('paper_white', srgb('#e9e6df'), 0.85),
        'mm_white': pbr('mm_white', srgb('#e4e4e2'), 0.22, coat=0.8, coat_rough=0.06, sss=0.04, sss_radius=(0.003, 0.003, 0.003)),
        'ash': add_bump(pbr('ash', srgb('#b89a76'), 0.55, coat=0.2), 400, 0.05, 3),
        'pot': speckled(pbr('pot', srgb('#e4ded2'), 0.68)),
        'pebble': pbr('pebble', srgb('#cfc8bd'), 0.75),
        'sansevieria': sansevieria_mat('sansevieria'),
        'wire': pbr('wire', srgb('#2b2620'), 0.5, 0.6),
        'sw_black': pbr('sw_black', srgb('#1d1e21'), 0.42),
        'sw_dark': pbr('sw_dark', srgb('#2a2b2e'), 0.55),
        'joy_blue': pbr('joy_blue', srgb('#16b9df'), 0.38, coat=0.3),
        'joy_red': pbr('joy_red', srgb('#f2484f'), 0.38, coat=0.3),
        'hp_black': pbr('hp_black', srgb('#202124'), 0.5),
        'hp_pad': add_bump(pbr('hp_pad', srgb('#2a2a2d'), 0.75, sheen=0.4), 800, 0.15, 2, distance=0.0003),
        'cup_metal': pbr('cup_metal', srgb('#3d4248'), 0.45, 0.8),
        'pen_black': pbr('pen_black', srgb('#1a1a1a'), 0.35),
        'pen_blue': pbr('pen_blue', srgb('#2f5fb8'), 0.35),
        'marker': pbr('marker', srgb('#e8e6e0'), 0.4),
        'pencil': pbr('pencil', srgb('#e9b93a'), 0.55),
        'pen_cap': pbr('pen_cap', srgb('#2a2a2a'), 0.3),
        'eraser': pbr('eraser', srgb('#e7a0a0'), 0.7),
        'scissor': pbr('scissor', srgb('#f07c2f'), 0.35, coat=0.4),
        'steel_bright': pbr('steel_bright', srgb('#b9bcc2'), 0.25, 1.0),
        'glass': pbr('glass', (1, 1, 1), 0.02, transmission=1.0, ior=1.5),
    }
    M['phone_screen'] = phone_screen_mat('phone_screen', TEX / 'phone_awake.png')
    M['fairy'] = pbr('fairy', (1, 0.8, 0.55), 0.3); bb = M['fairy'].node_tree.nodes['Principled BSDF']; bb.inputs['Emission Color'].default_value = (1.0, 0.62, 0.30, 1); bb.inputs['Emission Strength'].default_value = 3.2
    M['fairy_dim'] = pbr('fairy_dim', (1, 0.8, 0.55), 0.3); bb = M['fairy_dim'].node_tree.nodes['Principled BSDF']; bb.inputs['Emission Color'].default_value = (1.0, 0.58, 0.28, 1); bb.inputs['Emission Strength'].default_value = 1.4
    # the keyboard's light bar: frosted, ribbed (a band every 1.5 mm), lit mint from inside, softly
    M['kb_halo'] = pbr('kb_halo', srgb('#d6f2e0'), 0.32, sss=0.3, sss_radius=(0.003, 0.004, 0.0035))
    nt = M['kb_halo'].node_tree; bb = nt.nodes['Principled BSDF']
    bb.inputs['Emission Color'].default_value = (*srgb('#bdf0cf'), 1); bb.inputs['Emission Strength'].default_value = 0.9
    rib = nt.nodes.new('ShaderNodeTexWave'); rib.wave_type = 'BANDS'; rib.bands_direction = 'X'; rib.inputs['Scale'].default_value = 190.0
    rbump = nt.nodes.new('ShaderNodeBump'); rbump.inputs['Strength'].default_value = 0.6; rbump.inputs['Distance'].default_value = 0.0004
    nt.links.new(rib.outputs['Fac'], rbump.inputs['Height']); nt.links.new(rbump.outputs['Normal'], bb.inputs['Normal'])
    M['led_blue'] = pbr('led', (0, 0, 0), 0.4); b = M['led_blue'].node_tree.nodes['Principled BSDF']; b.inputs['Emission Color'].default_value = (0.1, 0.4, 1, 1); b.inputs['Emission Strength'].default_value = 25
    M['bulb'] = pbr('bulb', (1, 1, 1), 0.3); b = M['bulb'].node_tree.nodes['Principled BSDF']; b.inputs['Emission Color'].default_value = (1, 0.62, 0.32, 1); b.inputs['Emission Strength'].default_value = 12
    city_m, _, _ = image_emit('city', TEX / 'window_city.png', 1.25)

    # floor, walls, the window with its blinds and the city beyond
    rbox('floor', (6, 6, 0.02), (0, 0.5, -0.01), M['floor'])
    WY = 0.43
    for name, size, loc in (('wall_r', (3.5, 0.12, 2.9), (1.25, WY + 0.06, 1.45)), ('wall_l', (1.0, 0.12, 2.9), (-1.75, WY + 0.06, 1.45)),
                            ('wall_low', (0.75, 0.12, 1.0), (-0.875, WY + 0.06, 0.5)), ('wall_top', (0.75, 0.12, 0.85), (-0.875, WY + 0.06, 2.475))):
        rbox(name, size, loc, M['wall'])
    rbox('sill', (0.80, 0.16, 0.02), (-0.875, WY - 0.01, 1.01), M['trim'], bevel=0.003)
    for name, size, loc in (('frame_t', (0.75, 0.06, 0.03), (-0.875, WY + 0.04, 2.035)), ('frame_l', (0.03, 0.06, 1.05), (-1.235, WY + 0.04, 1.525)),
                            ('frame_r', (0.03, 0.06, 1.05), (-0.515, WY + 0.04, 1.525))):
        rbox(name, size, loc, M['trim'])
    # Venetian blinds: 25 mm aluminium slats every 22 mm, tilted half shut, on three ladder cords
    n = 0; z = 1.07
    while z < 1.985:
        rbox(f'slat{n}', (0.705, 0.025, 0.0011), (-0.875, WY + 0.018, z), M['slat'], rot=(9, 0, 0)); z += 0.0215; n += 1
    for cx in (-1.15, -0.875, -0.60):
        for side in (-0.011, 0.011):
            rbox(f'cord{cx}{side}', (0.0012, 0.0012, 0.93), (cx, WY + 0.018 + side, 1.525), M['cord'])
    rbox('blind_rail', (0.72, 0.04, 0.03), (-0.875, WY + 0.02, 2.0), M['trim'], bevel=0.004)
    # (the city stays far behind, seen through the window)
    pl = bpy.data.meshes.new('cityplane'); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
    bm.to_mesh(pl); bm.free(); city = link(bpy.data.objects.new('city', pl)); city.scale = (4.8, 2.7, 1); city.rotation_euler = (math.radians(90), 0, 0); city.location = (-3.6, 4.0, 0.67)
    city.visible_diffuse = True; city.visible_glossy = True
    # glass in the window: it reflects the room's lights; it casts no shadow, so the moon still comes through
    gl = rbox('window_glass', (0.72, 0.006, 1.03), (-0.875, WY + 0.045, 1.525), M['glass']); gl.visible_shadow = False
    pl.materials.append(city_m); city.visible_shadow = False
    uv = pl.uv_layers.new(name='UVMap')
    for poly in pl.polygons:
        for li in poly.loop_indices:
            co = pl.vertices[pl.loops[li].vertex_index].co; uv.data[li].uv = (co.x / 2 + 0.5, co.y / 2 + 0.5)

    # the desk: walnut top on a black steel frame
    rbox('desk_top', (1.60, 0.76, 0.032), (0, 0, DT - 0.016), M['desk'], bevel=0.004, seg=5)
    for sx in (-1, 1):
        rbox(f'leg{sx}a', (0.05, 0.05, DT - 0.032), (sx * 0.74, -0.30, (DT - 0.032) / 2), M['steel'], bevel=0.003)
        rbox(f'leg{sx}b', (0.05, 0.05, DT - 0.032), (sx * 0.74, 0.30, (DT - 0.032) / 2), M['steel'], bevel=0.003)
        rbox(f'rail{sx}', (0.04, 0.60, 0.04), (sx * 0.74, 0, DT - 0.052), M['steel'], bevel=0.003)
    rbox('rail_back', (1.44, 0.04, 0.04), (0, 0.30, DT - 0.052), M['steel'], bevel=0.003)
    rbox('desk_mat', (0.86, 0.36, 0.003), (0.05, -0.15, DT + 0.0015), M['mat'], bevel=0.0012)

    # the monitor: black glass front, aluminium back and stand
    mon = link(bpy.data.objects.new('monitor', None)); mon.location = SC
    # black glass front, set into an aluminium shell whose edge shows as a thin silver rim
    glass = rbox('mon_glass', (SW + 2 * BEZ, 0.003, SH + 2 * BEZ), (0, 0.0015, 0), M['black_glass'], bevel=0.0010); glass.parent = mon
    shell = rbox('mon_shell', (SW + 2 * BEZ + 0.003, 0.017, SH + 2 * BEZ + 0.003), (0, 0.0105, 0), M['alu'], bevel=0.0045, seg=6); shell.parent = mon
    # the stand: one aluminium plate from behind the middle of the display down to its foot, leaning back
    top = mathutils.Vector((0, 0.030, -0.02)); bot = mathutils.Vector((0, 0.115, -(SC.z - DT) + 0.010))
    v = bot - top
    neck = rbox('mon_neck', (0.13, 0.010, v.length), (top + bot) / 2, M['alu'], bevel=0.003); neck.parent = mon
    neck.rotation_euler = (math.atan2(v.y, -v.z), 0, 0)
    foot = rbox('mon_foot', (0.20, 0.185, 0.008), (0, 0.085, -(SC.z - DT) + 0.004), M['alu'], bevel=0.009, seg=6); foot.parent = mon
    # the screen: an image the shot drives, a hair in front of the glass
    sm = bpy.data.meshes.new('screen'); bm = bmesh.new()
    vs = [bm.verts.new((x * SW / 2, -0.0002, z * SH / 2)) for x, z in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f = bm.faces.new(vs); uvl = bm.loops.layers.uv.new('UVMap')
    for loop, uvv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): loop[uvl].uv = uvv
    bm.normal_update(); bm.to_mesh(sm); bm.free()
    screen = link(bpy.data.objects.new('screen', sm)); screen.parent = mon; screen.location = (0, 0, 0)
    screen.visible_shadow = False

    # bias light behind the monitor, on the wall
    light('bias', 'AREA', (SC.x, SC.y + 0.03, SC.z + 0.02), 4.0, (0.58, 0.62, 1.0), size=0.46, size_y=0.24, target=(SC.x, 3, SC.z + 0.05))
    # the screen's light into the room (the picture itself is the screen mesh; this is its spill, not seen by the camera)
    light('screen_fill', 'AREA', (SC.x, SC.y - 0.006, SC.z), 9.0, (0.78, 0.86, 1.0), size=SW, size_y=SH, target=(SC.x, -2, SC.z - 0.25))
    # moonlight through the blinds
    sun = light('moon', 'SUN', (-1.3, 1.2, 2.0), 0.20, (0.60, 0.70, 1.0), angle=0.45, target=(-1.3 + 0.45, 1.2 - 0.60, 2.0 - 0.66))
    # the lamp's warm cone
    light('room_fill', 'AREA', (0.0, -2.2, 2.4), 0.7, (0.30, 0.36, 0.55), size=2.0, size_y=1.0, target=(0, 0.3, 1.0))

    keyboard(M)
    magic_mouse(M)
    # on the wall right of the monitor: two prints taped up, and warm string lights above them
    poster('poster_whale', TEX / 'poster_whale.jpg', 0.21, 0.297, (0.475, 1.285), WY - 0.0002, ['washi_pink.png', 'washi_mint.png'], tilt=1.2)
    pegboard(M, (0.805, 1.265), WY)
    fairy_lights(M, (-0.44, 1.605), (1.06, 1.595), 0.04, 22, WY)
    light('fairy_glow', 'AREA', (0.30, WY - 0.12, 1.59), 0.22, (1.0, 0.66, 0.38), size=1.4, size_y=0.10, target=(0.30, WY + 1, 1.40))
    # a ring the mug left earlier in the night, a hand's width from where it stands now
    ring_m = pbr('coffee_ring', (1, 1, 1), 0.5); nt = ring_m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(str(TEX / 'coffee_ring.png'))
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    bm = bmesh.new(); vs = [bm.verts.new((x * 0.05, y * 0.05, 0)) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; f = bm.faces.new(vs)
    uvl = bm.loops.layers.uv.new('UVMap')
    for loop, uvv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): loop[uvl].uv = uvv
    rg = mesh_obj('coffee_ring', bm, ring_m); rg.location = (0.585, 0.075, DT + 0.0002); rg.visible_shadow = False
    mug(M)
    clawd(M)
    phone(M)
    plant(M)
    ssd(M)
    # the notes: yellow hangs from the bottom bezel under the screen's left half; pink is stuck on the wall
    ny = paper('note_y', TEX / 'note_yellow.png'); np_ = paper('note_p', TEX / 'note_pink.png')
    # its glue on the bezel's bottom edge only, just under the lit screen; the rest hangs below the monitor
    sticky('note_yellow', ny, 0.076, (SC.x - 0.20, SC.y - 0.0016, SC.z - SH / 2 - 0.0006), 0, 0.0012)
    # cables: the monitor's down behind the desk, the drive's to the monitor, the lamp's off the back edge
    # out of the back of the display beside the stand, down to the desk, and off its back edge into the gap by the wall
    curve_tube('cable_mon', [(0.09, SC.y + 0.0215, 0.99), (0.10, SC.y + 0.05, 0.86), (0.11, 0.30, DT + 0.0035), (0.12, 0.372, DT + 0.0035), (0.13, 0.395, DT - 0.06), (0.14, 0.405, 0.30)], 0.0032, M['rubber'])
    curve_tube('cable_ssd', [(0.43 - 0.006, 0.17 + 0.044, DT + 0.0025), (0.39, 0.26, DT + 0.0022), (0.22, 0.26, DT + 0.0022), (0.13, 0.205, DT + 0.06), (0.105, SC.y + 0.0215, 0.97)], 0.0018, M['rubber'])
    curve_tube('cable_lamp', [(0.63, 0.30 + 0.07, DT + 0.004), (0.66, 0.38, DT + 0.003), (0.70, 0.40, DT - 0.05), (0.72, 0.42, 0.25)], 0.0025, M['rubber'])
    return {'screen': screen, 'monitor': mon, 'M': M}
