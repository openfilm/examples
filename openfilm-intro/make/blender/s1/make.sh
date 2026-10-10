#!/bin/zsh
# Line 1's plate, start to finish: Premiere's screen and pieces → the scene (s1.blend) → EXR frames on the GPU →
# the finish (post.py: bloom, shoulder, grain, easing to the recording) → assets/video/s1-room.mp4.
#   ./make.sh [percent=100] [samples=256] [first=0] [last=108]
set -e
cd "${0:A:h}"
mkdir -p out
B=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
PCT=${1:-100}; SPP=${2:-256}; F0=${3:-0}; F1=${4:-108}; OUT=${OUT:-../../../assets/video/s1-room.mp4}
GPU="import bpy; p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.kernel_optimization_level='FULL'; p.get_devices(); [setattr(d,'use',d.type=='METAL') for d in p.devices]; sc=bpy.context.scene; sc.render.resolution_percentage=$PCT; sc.cycles.samples=$SPP"

[[ -f pr/out/frames/0042.png && -f pr/out/pieces/pieces.json ]] || { (cd pr && node render.mjs frames out/frames && node render.mjs pieces out/pieces) && python3 pr/bg.py; }
$B -b -P shot.py -- save > out/save.log 2>&1
[[ -n "$KEEP" ]] || rm -rf out/exr; rm -rf out/png; mkdir -p out/exr out/png; : > out/progress.log
# one process a frame: rendering many frames in one Cycles session on Metal can stall on the image sequence
: > out/render.log
for f in $(seq $F0 $F1); do
  [[ -f out/exr/$(printf %04d $f).exr ]] && continue
  # a watchdog: Metal now and then stalls a frame for good; such a frame is killed and tried again
  for try in 1 2 3; do
    $B -b s1.blend --python-expr "$GPU" -f $f >> out/render.log 2>&1 &
    pid=$!; s=$(date +%s)
    while kill -0 $pid 2>/dev/null; do (( $(date +%s) - s > ${LIMIT:-240} )) && { kill $pid; echo "frame $f stalled (try $try)" >> out/progress.log; break; }; sleep 1; done
    wait $pid 2>/dev/null || true
    [[ -f out/exr/$(printf %04d $f).exr ]] && break
  done
  echo "frame $f $(( $(date +%s) - s ))s" >> out/progress.log
done
$B -b -P post.py -- --seq out/exr out/png tex/hero_land.png > out/post.log 2>&1
ffmpeg -v error -y -framerate 30 -start_number 0 -i out/png/%04d.png -c:v libx264 -preset slow -crf 12 -g 1 -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 "$OUT"
echo "→ $OUT"
