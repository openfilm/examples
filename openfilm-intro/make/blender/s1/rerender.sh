#!/bin/zsh
# re-render frames [F0, F1] of the line-1 plate after a scene change, keep the rest, finish and encode again
set -e
cd "${0:A:h}"
mkdir -p out
F0=${1:?first}; F1=${2:?last}
B=${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}
GPU="import bpy; p=bpy.context.preferences.addons['cycles'].preferences; p.compute_device_type='METAL'; p.kernel_optimization_level='FULL'; p.get_devices(); [setattr(d,'use',d.type=='METAL') for d in p.devices]; sc=bpy.context.scene; sc.render.resolution_percentage=100; sc.cycles.samples=256"
$B -b -P shot.py -- save > out/save.log 2>&1
for f in $(seq $F0 $F1); do rm -f out/exr/$(printf %04d $f).exr; done
: > out/progress.log
for f in $(seq $F0 $F1); do
  for try in 1 2 3; do
    $B -b s1.blend --python-expr "$GPU" -f $f >> out/render.log 2>&1 &
    pid=$!; s=$(date +%s)
    while kill -0 $pid 2>/dev/null; do (( $(date +%s) - s > 180 )) && { kill $pid; echo "frame $f stalled (try $try)" >> out/progress.log; break; }; sleep 1; done
    wait $pid 2>/dev/null || true
    [[ -f out/exr/$(printf %04d $f).exr ]] && break
  done
  echo "frame $f $(( $(date +%s) - s ))s" >> out/progress.log
done
rm -rf out/png; mkdir -p out/png
$B -b -P post.py -- --seq out/exr out/png tex/hero_land.png > out/post.log 2>&1
ffmpeg -v error -y -framerate 30 -start_number 0 -i out/png/%04d.png -c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 ../../../assets/video/s1-room.mp4
echo "→ s1-room.mp4 re-rendered $F0..$F1"
