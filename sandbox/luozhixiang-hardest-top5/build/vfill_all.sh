#!/usr/bin/env bash
set -uo pipefail
cd /Users/yinshawnrao/explorer/cc-media/sandbox/luozhixiang-hardest-top5
V=/Users/yinshawnrao/explorer/cc-media/tools/video/vfill.sh
# key  crop  BR  SAT
bash $V downloads/jingwumen.mp4 clips/vert_jingwumen.mp4 1280:536:0:88 -0.30 1.08 && echo OK_jwm
bash $V downloads/wujixian.mp4  clips/vert_wujixian.mp4  1920:944:0:0  -0.30 1.08 && echo OK_wjx
bash $V downloads/duyiwuer.mp4  clips/vert_duyiwuer.mp4  640:360:0:60  -0.28 1.08 && echo OK_dyw
bash $V downloads/pinshenme.mp4 clips/vert_pinshenme.mp4 640:360:0:55  -0.20 1.10 && echo OK_psm
bash $V downloads/bujuming.mp4  clips/vert_bujuming.mp4  1920:905:0:0  -0.20 1.10 && echo OK_bjm
echo ALL_VFILL_DONE
