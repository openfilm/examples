"""Pictures the room needs, drawn once: the two sticky notes (in a hand), the phone's lock screen at 3:47, the city
behind the blinds, and macOS's spinning wait cursor. Run with the system python3 (PIL): python3 tex.py"""
import math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = Path(__file__).parent / 'tex'; OUT.mkdir(exist_ok=True)
HAND = '/System/Library/AssetsV2/com_apple_MobileAsset_Font8'   # where macOS keeps downloadable fonts
PINGFANG = '/System/Library/AssetsV2/com_apple_MobileAsset_Font8/86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc'
HANZIPEN = '/System/Library/AssetsV2/com_apple_MobileAsset_Font8/a3c69464b629577766c23bcdb12ffbfe3759b923.asset/AssetData/Hanzipen.ttc'
FACES = {'HanziPen SC:style=Bold': (HANZIPEN, 2), 'PingFang SC:style=Semibold': (PINGFANG, 11), 'PingFang SC:style=Regular': (PINGFANG, 3)}
import sys as _s
def font(name, size):
    if name.startswith('SF Pro'):
        f = ImageFont.truetype('/System/Library/Fonts/SFNS.ttf', size); f.set_variation_by_name(name.split('style=')[1]); return f
    path, index = FACES[name]
    return ImageFont.truetype(path, size, index=index)

# ── sticky notes: 76 mm squares, 1024 px ──
def note(path, bg, lines, ink=(38, 36, 40), rot=-1.5, strike=None):
    W = 1024
    im = Image.new('RGB', (W, W), bg)
    d = ImageDraw.Draw(im)
    # the glue strip is a touch darker; paper has a faint grain
    rnd = random.Random(path)
    for y in range(0, 150): d.line([(0, y), (W, y)], fill=tuple(max(0, c - 10 + y // 20) for c in bg))
    px = im.load()
    for _ in range(60000):
        x, y = rnd.randrange(W), rnd.randrange(W); c = px[x, y]; k = rnd.randint(-6, 6); px[x, y] = tuple(max(0, min(255, v + k)) for v in c)
    txt = Image.new('RGBA', (W, W), (0, 0, 0, 0)); td = ImageDraw.Draw(txt)
    y = 200
    for size, text in lines:
        f = font('HanziPen SC:style=Bold', size)
        td.text((92, y), text, font=f, fill=(*ink, 235))
        if strike == text:
            w = td.textlength(text, font=f); td.line([(86, y + size * 0.62), (98 + w, y + size * 0.5)], fill=(*ink, 230), width=10)
        y += int(size * 1.32)
    txt = txt.rotate(rot, resample=Image.BICUBIC, center=(W / 2, W / 2))
    im.paste(txt, (0, 0), txt)
    im.save(OUT / path, quality=95)

note('note_yellow.png', (246, 222, 98), [(150, 'v9 最终版'), (124, '3点前导出!!'), (96, '（真的最后一版）')], rot=-2)
note('note_pink.png', (244, 166, 190), [(124, '客户：'), (124, '片头再炸'), (124, '一点')], rot=1.5)

# ── the phone, on the desk: lock screen, 3:47, the client's message ──
def phone():
    W, H = 1170, 2532
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(18 + 20 * k), int(22 + 14 * k), int(44 + 30 * (1 - k))))
    glow = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(glow); gd.ellipse([W * 0.1, H * 0.55, W * 1.2, H * 1.2], fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    im = Image.composite(Image.new('RGB', (W, H), (96, 64, 120)), im, glow)
    d = ImageDraw.Draw(im)
    f_date = font('PingFang SC:style=Semibold', 62); f_time = font('SF Pro Display:style=Bold', 330)
    d.text((W / 2, 420), '10月8日 星期四', font=f_date, fill=(235, 235, 245), anchor='mm')
    d.text((W / 2, 690), '3:47', font=f_time, fill=(240, 240, 250), anchor='mm')
    # notification card
    card = Image.new('RGBA', (W - 90, 250), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, W - 91, 249], radius=56, fill=(60, 60, 78, 210))
    cd.rounded_rectangle([40, 52, 140, 152], radius=24, fill=(52, 199, 89, 255))
    f1 = font('PingFang SC:style=Semibold', 50); f2 = font('PingFang SC:style=Regular', 48); f3 = font('PingFang SC:style=Regular', 40)
    cd.text((176, 58), '客户 王总', font=f1, fill=(255, 255, 255, 255)); cd.text((W - 140, 62), '现在', font=f3, fill=(200, 200, 210, 255), anchor='ra')
    cd.text((176, 132), '明早9点前要看到成片哦～', font=f2, fill=(235, 235, 240, 255))
    im.paste(card, (45, 1660), card)
    d.rounded_rectangle([W / 2 - 200, H - 60, W / 2 + 200, H - 46], radius=7, fill=(230, 230, 235))
    im.save(OUT / 'phone.png')
phone()

# ── the city behind the blinds: blocks and lit windows, mostly asleep ──
def city():
    W, H = 4096, 2048
    rnd = random.Random(7)
    im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(6 + 26 * k ** 2.2), int(9 + 18 * k ** 2), int(22 + 30 * k ** 1.5)))
    for layer, (n, hmin, hmax, shade) in enumerate([(26, 700, 1500, 16), (34, 420, 1100, 11), (40, 200, 700, 7)]):
        x = -100
        while x < W:
            w = rnd.randint(160, 420); h = rnd.randint(hmin, hmax)
            d.rectangle([x, H - h, x + w, H], fill=(shade, shade + 1, shade + 5))
            for wy in range(H - h + 40, H - 20, 46):
                for wx in range(x + 24, x + w - 24, 38):
                    if rnd.random() < (0.10 if layer < 2 else 0.05):
                        warm = rnd.random() < 0.7
                        c = (255, 196, 120) if warm else (170, 205, 255)
                        a = rnd.uniform(0.35, 1.0)
                        d.rectangle([wx, wy, wx + 20, wy + 26], fill=tuple(int(v * a) for v in c))
            if rnd.random() < 0.25: d.rectangle([x + w // 2 - 3, H - h - 60, x + w // 2 + 3, H - h], fill=(shade, shade, shade + 3)); d.ellipse([x + w // 2 - 9, H - h - 70, x + w // 2 + 9, H - h - 52], fill=(255, 40, 30))
            x += w + rnd.randint(-30, 40)
    im.save(OUT / 'city.png')
city()

# ── macOS's spinning wait cursor, 512 px, with its glossy cap ──
def beachball():
    S = 512; R = S / 2 - 6
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); px = im.load()
    import colorsys
    for y in range(S):
        for x in range(S):
            dx, dy = x - S / 2 + 0.5, y - S / 2 + 0.5; r = math.hypot(dx, dy)
            if r > R + 1: continue
            a = (math.atan2(dy, dx) / (2 * math.pi) + r / R * 0.28) % 1.0          # a slight swirl
            h = (a * 1.0) % 1.0
            cr, cg, cb = colorsys.hsv_to_rgb(h, 0.86, 1.0)
            shade = 0.82 + 0.18 * (1 - r / R)
            hl = max(0.0, 1 - math.hypot(dx + R * 0.28, dy + R * 0.38) / (R * 0.62)) ** 2 * 0.55   # the gloss, upper left
            edge = max(0.0, min(1.0, R + 1 - r))
            c = [min(255, int(255 * (v * shade + hl))) for v in (cr, cg, cb)]
            px[x, y] = (*c, int(255 * edge))
    ring = ImageDraw.Draw(im); ring.ellipse([6, 6, S - 6, S - 6], outline=(40, 40, 40, 160), width=5)
    im.save(OUT / 'beachball.png')
beachball()
print('done', sorted(p.name for p in OUT.iterdir()))

# ── two anime film posters (the art is generated, assets/image/poster-*.png), typeset as one-sheets ──
MINCHO = '/System/Library/AssetsV2/com_apple_MobileAsset_Font8/36a81f2dad2ef266c50802d85839e0201fcf4e57.asset/AssetData/ToppanBunkyuMidashiMinchoStdN-ExtraBold.otf'
KAKU = '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
KAKU3 = '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'
ART = Path(__file__).parents[3] / 'assets' / 'image'
def poster(src, out, title, en, line, title_xy, vertical=True, size=150, col=(255, 255, 255)):
    im = Image.open(ART / src).convert('RGB').resize((1400, 2100), Image.LANCZOS)
    W, H = im.size
    # a darker foot for the credits, as one-sheets have
    foot = Image.new('L', (W, H), 0); fd = ImageDraw.Draw(foot)
    for y in range(int(H * 0.80), H): fd.line([(0, y), (W, y)], fill=int(170 * ((y - H * 0.80) / (H * 0.20)) ** 1.4))
    im = Image.composite(Image.new('RGB', (W, H), (8, 10, 18)), im, foot)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = ImageFont.truetype(MINCHO, size)
    x, y = title_xy
    if vertical:
        for ch in title:
            d.text((x, y), ch, font=f, fill=(*col, 250), anchor='mt'); y += int(size * 1.06)
    else:
        d.text((x, y), title, font=f, fill=(*col, 250), anchor='mm')
    glow = lay.filter(ImageFilter.GaussianBlur(14))
    im = Image.alpha_composite(Image.alpha_composite(im.convert('RGBA'), glow), lay)
    d = ImageDraw.Draw(im)
    fe = ImageFont.truetype(KAKU, 46); fl = ImageFont.truetype(KAKU3, 28)
    d.text((W / 2, H - 230), en, font=fe, fill=(240, 240, 245), anchor='mm')
    d.text((W / 2, H - 160), line, font=fl, fill=(205, 205, 215), anchor='mm')
    # a credit block, too small to read, as on every one-sheet
    rnd = random.Random(out)
    for r in range(3):
        xx = 140
        while xx < W - 140:
            w = rnd.randint(30, 110); d.rectangle([xx, H - 112 + r * 22, xx + w, H - 104 + r * 22], fill=(150, 150, 160)); xx += w + rnd.randint(10, 22)
    im.convert('RGB').save(OUT / out, quality=94)
poster('poster-snow.png', 'poster_snow.jpg', '雪の向こうへ', 'BEYOND THE SNOW', 'この冬、いちばん遠い道へ。', (1210, 150), size=150)
poster('poster-city.png', 'poster_whale.jpg', 'くじらの空', 'THE WHALE SKY', '夜の街に、ゆっくりと。', (700, 1770), vertical=False, size=150, col=(255, 236, 214))

# ── the phone's lock screen, asleep (its wallpaper, unlit) and awake with the client's message ──
def lockscreen():
    W, H = 1170, 2532
    im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(24 + 26 * k), int(28 + 18 * k), int(58 + 30 * (1 - k))))
    glow = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(glow); gd.ellipse([W * 0.05, H * 0.5, W * 1.25, H * 1.25], fill=130)
    im = Image.composite(Image.new('RGB', (W, H), (120, 70, 130)), im, glow.filter(ImageFilter.GaussianBlur(240)))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 410), '10月8日 星期四', font=font('PingFang SC:style=Semibold', 64), fill=(238, 238, 248), anchor='mm')
    d.text((W / 2, 690), '3:47', font=font('SF Pro:style=Bold', 340), fill=(242, 242, 252), anchor='mm')
    # the notification, as iOS stacks it under the clock, at a large text size: the film reads it from across the mat
    card = Image.new('RGBA', (W - 70, 480), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, W - 71, 479], radius=72, fill=(70, 66, 92, 230))
    cd.rounded_rectangle([44, 70, 194, 220], radius=36, fill=(52, 199, 89, 255))
    cd.ellipse([80, 108, 158, 172], fill=(255, 255, 255, 255)); cd.polygon([(98, 164), (90, 196), (120, 172)], fill=(255, 255, 255, 255))
    cd.text((232, 72), '王总（客户）', font=font('PingFang SC:style=Semibold', 76), fill=(255, 255, 255, 255))
    cd.text((W - 116, 84), '现在', font=font('PingFang SC:style=Regular', 58), fill=(205, 205, 220, 255), anchor='ra')
    cd.text((232, 196), '改了这么多版…', font=font('PingFang SC:style=Regular', 78), fill=(240, 240, 248, 255))
    cd.text((232, 306), '要不还是用第一版吧', font=font('PingFang SC:style=Regular', 78), fill=(240, 240, 248, 255))
    im.paste(card, (35, 1480), card)
    d.rounded_rectangle([W / 2 - 200, H - 60, W / 2 + 200, H - 46], radius=7, fill=(232, 232, 238))
    im.save(OUT / 'phone_awake.png')
lockscreen()
print('posters and phone done')

# ── the pegboard: birch plywood, a hole every inch ──
def pegboard():
    W, H = 2200, 2000                       # 0.44 × 0.40 m → 5000 px a metre
    rnd = random.Random(21)
    im = Image.new('RGB', (W, H), (219, 196, 160)); d = ImageDraw.Draw(im)
    for i in range(240):                    # long soft grain along the width
        y = rnd.uniform(0, H); a = rnd.uniform(0.04, 0.12); w = rnd.uniform(2, 9)
        c = tuple(int(v * (1 - a)) for v in (219, 196, 160)) if rnd.random() < 0.7 else (232, 212, 178)
        pts = [(x, y + math.sin(x * 0.004 + i) * rnd.uniform(4, 18)) for x in range(0, W + 40, 40)]
        d.line(pts, fill=c, width=int(w))
    im = im.filter(ImageFilter.GaussianBlur(1.6)); d = ImageDraw.Draw(im)
    step = 127; r = 16                       # 25.4 mm apart, 6.4 mm holes
    x0 = (W - step * (W // step - 1)) / 2; y0 = (H - step * (H // step - 1)) / 2
    for j in range(H // step):
        for i in range(W // step):
            cx, cy = x0 + i * step, y0 + j * step
            d.ellipse([cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3], fill=(196, 172, 136))      # the hole's chamfer
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(26, 22, 20))
    im.save(OUT / 'pegboard.jpg', quality=93)
pegboard()

def instax_wide(src, out):
    """A wide instant print (108 × 86 mm): the picture in a 99 × 62 mm window, the wider margin at the bottom."""
    W, H = 1080, 860; im = Image.new('RGB', (W, H), (238, 234, 224))
    pic = Image.open(src).convert('RGB'); tw, th = 990, 620
    s = max(tw / pic.width, th / pic.height); pic = pic.resize((int(pic.width * s) + 1, int(pic.height * s) + 1), Image.LANCZOS)
    pic = pic.crop(((pic.width - tw) // 2, (pic.height - th) // 2, (pic.width - tw) // 2 + tw, (pic.height - th) // 2 + th))
    im.paste(pic, (45, 50))
    im = Image.blend(im, Image.new('RGB', (W, H), (226, 210, 168)), 0.06)
    im.save(OUT / out, quality=92)

def generated_print(src, out):
    """A generated photo that already is an instant print: trimmed to its card."""
    im = Image.open(src).convert('RGB')
    # the card is the light area: find it by brightness along the middle row and column
    g = im.convert('L'); w, h = im.size
    xs = [x for x in range(w) if g.getpixel((x, h // 2)) > 200 or g.getpixel((x, int(h * 0.9))) > 200]
    ys = [y for y in range(h) if g.getpixel((w // 2, y)) > 200]
    box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1) if xs and ys else (0, 0, w, h)
    im.crop(box).save(OUT / out, quality=92)
    return box
ART = Path(__file__).parents[3] / 'assets' / 'image'
print('friends card', generated_print(ART / 'photo-friends.png', 'print_friends.jpg'))
print('cat card', generated_print(ART / 'photo-cat.png', 'print_cat.jpg'))
instax_wide(Path(__file__).parent / 'pr' / 'img' / 'snow-3.0.jpg', 'print_road.jpg')

# ── washi tape for the poster: small, matte, muted pastel with a tiny print, torn ends ──
def washi_tex(out, base, motif, seed):
    W, H = 600, 210
    rnd = random.Random(seed)
    im = Image.new('RGBA', (W, H), (*base, 235)); d = ImageDraw.Draw(im)
    ink = tuple(min(255, int(c * 1.22)) for c in base)
    if motif == 'dots':
        for y in range(18, H, 44):
            for x in range(18 + (y // 44 % 2) * 22, W, 44): d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(*ink, 235))
    else:   # tiny four-point stars
        for y in range(24, H, 54):
            for x in range(20 + (y // 54 % 2) * 27, W, 54):
                r1, r2 = 11, 3
                pts = []
                for k in range(8):
                    a = k * math.pi / 4; r = r1 if k % 2 == 0 else r2
                    pts.append((x + r * math.cos(a), y + r * math.sin(a)))
                d.polygon(pts, fill=(*ink, 235))
    # torn ends: a ragged alpha edge on the left and right
    a = im.split()[3]; ad = ImageDraw.Draw(a)
    for side in (0, 1):
        for y in range(0, H, 6):
            depth = rnd.randint(4, 22)
            x0 = 0 if side == 0 else W - depth
            ad.rectangle([x0, y, x0 + depth, y + 6], fill=0)
    im.putalpha(a.filter(ImageFilter.GaussianBlur(1.2)))
    im.save(OUT / out)
washi_tex('washi_pink.png', (214, 168, 170), 'dots', 3)
washi_tex('washi_mint.png', (162, 196, 182), 'stars', 7)
print('washi done')
