"""The finish, after the post in github.com/mexicat/pdoom-video (MIT): a linear HDR frame (Blender's EXR) → bloom pyramid (soft-knee
threshold, box down, tent up), film halation, a tone shoulder that is the identity below k, radial chromatic
aberration, vignette, two-scale grain, sRGB. Every parameter can ease to neutral, so the last frames are exactly the
recording they hand over to. Run inside Blender's Python (it reads EXR):
    blender -b -P post.py -- <in.exr|dir> <out.png|dir> [params.json]
"""
import bpy, sys, json, math
import numpy as np
from pathlib import Path

def load_exr(path):
    img = bpy.data.images.load(str(path), check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1, :, :3].copy()

def save_png(path, rgb8):
    h, w, _ = rgb8.shape
    img = bpy.data.images.new('out', w, h, alpha=False, float_buffer=False)
    rgba = np.concatenate([rgb8[::-1].astype(np.float32) / 255.0, np.ones((h, w, 1), np.float32)], axis=2)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = str(path); img.file_format = 'PNG'; img.save()
    bpy.data.images.remove(img)

def down(x):
    h, w = x.shape[0] // 2 * 2, x.shape[1] // 2 * 2
    x = x[:h, :w]
    return 0.25 * (x[0::2, 0::2] + x[1::2, 0::2] + x[0::2, 1::2] + x[1::2, 1::2])

def up(x, shape):
    y = np.repeat(np.repeat(x, 2, axis=0), 2, axis=1)
    # a 3-tap tent along each axis, so the pyramid does not show blocks
    y = 0.25 * np.roll(y, 1, 0) + 0.5 * y + 0.25 * np.roll(y, -1, 0)
    y = 0.25 * np.roll(y, 1, 1) + 0.5 * y + 0.25 * np.roll(y, -1, 1)
    out = np.zeros((shape[0], shape[1], 3), np.float32)
    out[:y.shape[0], :y.shape[1]] = y[:shape[0], :shape[1]]
    return out

def bloom(x, threshold, knee, levels=7):
    l = x.max(axis=2, keepdims=True)
    rq = np.clip(l - threshold + knee, 0, 2 * knee); rq = rq * rq / (4 * knee + 1e-5)
    w = np.maximum(rq, l - threshold) / np.maximum(l, 1e-5)
    p = [down(np.minimum(x, 40.0) * w)]
    for _ in range(levels - 1): p.append(down(p[-1]))
    acc = p[-1]
    for lev in reversed(p[:-1]): acc = lev + up(acc, lev.shape)
    return up(acc, x.shape), up(p[3] if len(p) > 3 else p[-1], x.shape)

def shoulder(x, k):
    if k >= 0.999: return x
    y = np.where(x > k, k + (1 - k) * (1 - np.exp(-(x - k) / (1 - k))), x)
    over = x.max(axis=2, keepdims=True)
    t = np.clip((over - 2.0) / 10.0, 0, 1); t = t * t * (3 - 2 * t)
    return y * (1 - t * 0.85) + t * 0.85

def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)

def finish(x, p, frame=0):
    h, w, _ = x.shape
    x = x * p.get('exposure', 1.0)
    if p.get('bloom', 0) > 0 or p.get('halation', 0) > 0:
        b, ha = bloom(x, p.get('bloom_threshold', 0.9), p.get('bloom_knee', 0.5))
        x = x + b * (p.get('bloom', 0) / 3.0)
        lum = (ha * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(axis=2, keepdims=True)
        x = x + lum * np.array([1.0, 0.22, 0.06], np.float32) * p.get('halation', 0)
    ca = p.get('ca', 0)
    if ca > 0:
        # red out, blue in, growing with the square of the distance from the centre (a few pixels at the corners)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        dx, dy = xx / w - 0.5, yy / h - 0.5; r2 = (dx * w / h) ** 2 + dy ** 2
        ox, oy = dx * r2 * ca * 4.0 * (w / 1920), dy * r2 * ca * 4.0 * (h / 1080)
        def shift(ch, s):
            sx = np.clip(np.rint(xx + s * ox), 0, w - 1).astype(np.int32); sy = np.clip(np.rint(yy + s * oy), 0, h - 1).astype(np.int32)
            return x[sy, sx, ch]
        x = np.stack([shift(0, 1.0), x[..., 1], shift(2, -1.0)], axis=2)
    x = shoulder(x, p.get('shoulder', 0.72))
    # a little contrast (about mid grey, in stops) and colour, for the room; both 1 by the time the recording takes over
    con, sat = p.get('contrast', 1.0), p.get('saturation', 1.0)
    if con != 1.0:
        x = 0.18 * np.power(np.maximum(x, 1e-6) / 0.18, con)
    if sat != 1.0:
        l = (x * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(axis=2, keepdims=True)
        x = np.maximum(l + (x - l) * sat, 0)
    v = p.get('vignette', 0)
    if v > 0:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.sqrt(((xx / w - 0.5)) ** 2 + ((yy / h - 0.5) * 0.8) ** 2)
        t = np.clip((d - 0.25) / 0.7, 0, 1); t = t * t * (3 - 2 * t)
        x = x * (1 - v * t)[..., None]
    s = to_srgb(x)
    g = p.get('grain', 0)
    if g > 0:
        rng = np.random.default_rng(frame * 7919 + 17)
        g1 = rng.random((h, w), dtype=np.float32) - 0.5
        g2 = np.repeat(np.repeat(rng.random((h // 2 + 1, w // 2 + 1), dtype=np.float32) - 0.5, 2, 0), 2, 1)[:h, :w]
        lm = (s * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(axis=2)
        s = s + ((g1 * 0.6 + g2 * 0.4) * g * (0.55 + 1.2 * lm * (1 - lm)))[..., None]
    rng = np.random.default_rng(frame + 99991)
    s = s + (rng.random(s.shape[:2], dtype=np.float32)[..., None] - 0.5) / 255.0
    return (np.clip(s, 0, 1) * 255 + 0.5).astype(np.uint8)

def smooth01(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)

def params_at(t):
    """The finish over the shot: a night room's (bloom on the lamp and the screen, halation, a soft shoulder, grain,
    vignette) easing to nothing as OpenFilm lands, so the last frames are the recording itself."""
    white = smooth01((t - 2.42) / 0.36)                # OpenFilm's white faces arriving (from the first flips): no bloom glare on them
    calm = smooth01((t - 3.05) / 0.33)                 # everything that is not the recording goes
    return {'exposure': 1.0, 'bloom': 0.3 * (1 - calm), 'bloom_threshold': 0.9 + 1.8 * white, 'bloom_knee': 0.5,
            'halation': 0.1 * (1 - calm), 'ca': 0.25 * (1 - calm), 'shoulder': 0.72 + 0.28 * calm if calm < 0.999 else 1.0,
            'vignette': 0.3 * (1 - calm), 'grain': 0.018 * (1 - calm), 'hero': smooth01((t - 3.40) / 0.16),
            'contrast': 1.0 + 0.10 * (1 - calm), 'saturation': 1.0 + 0.08 * (1 - calm)}

def run_sequence(src_dir, dst_dir, hero_png, fps=30):
    src_dir, dst_dir = Path(src_dir), Path(dst_dir); dst_dir.mkdir(parents=True, exist_ok=True)
    hero = None
    for f in sorted(src_dir.glob('*.exr')):
        frame = int(''.join(ch for ch in f.stem if ch.isdigit()))
        p = params_at(frame / fps)
        rgb = finish(load_exr(f), p, frame)
        if p['hero'] > 0:
            if hero is None:
                hero = load_png(hero_png)
                while hero.shape[0] > rgb.shape[0]:      # a preview at a fraction of the size: average the recording down
                    hh = hero.astype(np.float32); hero = ((hh[0::2, 0::2] + hh[1::2, 0::2] + hh[0::2, 1::2] + hh[1::2, 1::2]) / 4 + 0.5).astype(np.uint8)
            rgb = (rgb.astype(np.float32) * (1 - p['hero']) + hero.astype(np.float32) * p['hero'] + 0.5).astype(np.uint8)
        save_png(dst_dir / f'{frame:04d}.png', rgb)
        print('post', frame, flush=True)

def load_png(path):
    img = bpy.data.images.load(str(path), check_existing=False); img.colorspace_settings.name = 'Non-Color'
    w, h = img.size; a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a); bpy.data.images.remove(img)
    return (a.reshape(h, w, 4)[::-1, :, :3] * 255 + 0.5).astype(np.uint8)

if __name__ == '__main__' and '--seq' in sys.argv:
    a = sys.argv[sys.argv.index('--seq') + 1:]
    run_sequence(a[0], a[1], a[2])
elif __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:]
    src, dst = Path(args[0]), Path(args[1])
    params = json.loads(Path(args[2]).read_text()) if len(args) > 2 else {}
    default = {'exposure': 1.0, 'bloom': 0.6, 'bloom_threshold': 0.9, 'halation': 0.25, 'ca': 1.0, 'shoulder': 0.72, 'vignette': 0.35, 'grain': 0.04}
    files = sorted(src.glob('*.exr')) if src.is_dir() else [src]
    if src.is_dir(): dst.mkdir(parents=True, exist_ok=True)
    for f in files:
        frame = int(''.join(ch for ch in f.stem if ch.isdigit()) or 0)
        p = dict(default); p.update(params.get(str(frame), params.get('all', {})) if isinstance(params, dict) else {})
        out = dst / (f.stem + '.png') if src.is_dir() else dst
        save_png(out, finish(load_exr(f), p, frame))
        print('post', f.name)
