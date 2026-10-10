"""Premiere with nothing on it: the panels (every piece with nothing above it) composited on the gaps' grey.
That is what the slats show, so no element is ever left behind on them. python3 pr/bg.py"""
import json
from pathlib import Path
from PIL import Image
here = Path(__file__).parent; d = here / 'out' / 'pieces'
P = json.loads((d / 'pieces.json').read_text())
bg = Image.new('RGBA', (3840, 2160), (12, 12, 12, 255))
for p in P:
    if p['parent'] is None:
        bg.alpha_composite(Image.open(d / f"{p['id']}.png").convert('RGBA'), (p['box'][0] * 2, p['box'][1] * 2))
bg.convert('RGB').save(here.parent / 'tex' / 'pr_bg.png')
print('pr_bg from', [p['id'] for p in P if p['parent'] is None])
