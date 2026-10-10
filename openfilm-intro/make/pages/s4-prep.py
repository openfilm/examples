"""What s4.html's timeline draws from the real media: each sample film's frames for its clip's filmstrip
(lib/s4/thumbs/<film>-<k>.jpg) and the voice's and the score's loudness over the page (lib/s4/peaks.json).
python3 make/pages/s4-prep.py (from the example's folder); run again after a new take of l4 or a new score."""
import json, subprocess
from array import array
from pathlib import Path
V4 = Path(__file__).parents[2]; HERE = V4 / 'lib' / 's4'   # the example's folder; what s4.html reads
FILMS = ['product-film', 'commercial', 'explainer', 'picture-book', 'education', 'music-video', 'video-editing', 'presentation']
N, RATE, DUR = 6, 50, 13.351                  # frames per strip; peaks per second; the page's length
(HERE / 'thumbs').mkdir(exist_ok=True)
SEG = {'music-video': (4.4, 7.2), 'education': (0.6, 1.8)}     # the stretch s4.html plays of these (its SEG)
for f in FILMS:
    src = V4 / f'assets/video/showcase/{f}.mp4'
    d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src]))
    a, b = SEG.get(f, (0, min(d, 5)))
    for k in range(N):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a + (k + 0.5) * (b - a) / N:.3f}', '-i', src, '-frames:v', '1',
                        '-vf', 'scale=384:216', '-q:v', '3', HERE / f'thumbs/{f}-{k}.jpg'], check=True)
def pcm(src, a, b):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(a), '-t', str(b - a), '-i', src, '-ac', '1', '-ar', '8000', '-f', 's16le', '-'])
    return array('h', raw)
def peaks(samples, offset):
    """loudness (0..1) every 1/RATE s of the page, the audio starting `offset` s into it"""
    step = 8000 // RATE; out = []
    for i in range(int(DUR * RATE)):
        j = int((i / RATE - offset) * 8000)
        w = samples[j:j + step] if 0 <= j < len(samples) else []
        out.append(max((abs(x) for x in w), default=0) / 32768)
    top = max(out) or 1
    return [round(x / top, 3) for x in out]
# the take the published peaks.json was drawn from: an earlier take of line 4, not in the example (the film plays
# l4-v4.mp3); point this at l4-v4.mp3 to draw the voice the film has
vo = pcm(V4 / 'assets/audio/vo/l4-v2.mp3', 0, DUR)
score = V4 / 'assets/audio/music/section1-score.mp3'
mu = pcm(score, 19.5 - 0.48, 20.3464) + pcm(score, 19.275, 31.3)                   # film.html: -3, -4, -4b under this page
(HERE / 'peaks.json').write_text(json.dumps({'rate': RATE, 'vo': peaks(vo, 0.68), 'music': peaks(mu, 0)}))
print('ok')
