#!/bin/zsh
# Line 2's plate: the cast on the bright stage → s2.blend → PNG frames on the GPU → assets/video/s2-cast.mp4
#   ./make.sh [percent=100] [samples=128] [first=0] [last=209]     (KEEP=1 keeps frames already rendered)
set -e
cd "${0:A:h}"
mkdir -p out
B=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
PCT=${1:-100}; SPP=${2:-128}; F0=${3:-0}; F1=${4:-209}; OUT=${OUT:-../../../assets/video/s2-cast.mp4}
GPU="import bpy; p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.kernel_optimization_level='FULL'; p.get_devices(); [setattr(d,'use',d.type=='METAL') for d in p.devices]; sc=bpy.context.scene; sc.render.resolution_percentage=$PCT; sc.cycles.samples=$SPP"
$B -b -P shot.py -- save > out/save.log 2>&1
[[ -n "$KEEP" ]] || rm -rf out/png; mkdir -p out/png; : > out/progress.log; : > out/render.log
for f in $(seq $F0 $F1); do
  [[ -f out/png/$(printf %04d $f).png ]] && continue
  for try in 1 2 3; do
    $B -b s2.blend --python-expr "$GPU" -f $f >> out/render.log 2>&1 &
    pid=$!; s=$(date +%s)
    while kill -0 $pid 2>/dev/null; do (( $(date +%s) - s > ${LIMIT:-150} )) && { kill $pid; echo "frame $f stalled (try $try)" >> out/progress.log; break; }; sleep 1; done
    wait $pid 2>/dev/null || true
    [[ -f out/png/$(printf %04d $f).png ]] && break
  done
  echo "frame $f $(( $(date +%s) - s ))s" >> out/progress.log
done
ffmpeg -v error -y -framerate 30 -start_number 0 -i out/png/%04d.png -c:v libx264 -preset slow -crf 12 -g 1 -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 "$OUT"
echo "→ $OUT"
