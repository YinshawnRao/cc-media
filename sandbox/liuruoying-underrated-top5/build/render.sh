#!/usr/bin/env bash
# Full render with retry (GPU-flaky / contention). Single footage_track => no multi-video hang.
set -u
cd /Users/yinshawnrao/explorer/cc-media/sandbox/liuruoying-underrated-top5
export HYPERFRAMES_EXTRACT_CACHE_DIR="$PWD/.hf_cache"
mkdir -p "$HYPERFRAMES_EXTRACT_CACHE_DIR" renders
for a in 1 2 3 4 5; do
  echo "=== render attempt $a $(date +%H:%M:%S) ==="
  find . -maxdepth 2 -name 'work-*' -type d -exec rm -rf {} + 2>/dev/null
  rm -f renders/full_raw.mp4
  npx --yes hyperframes@0.6.69 render --output renders/full_raw.mp4 --sdr -w 2 > renders/rlog_$a.txt 2>&1
  sz=$(wc -c < renders/full_raw.mp4 2>/dev/null || echo 0)
  echo "attempt $a done size=$sz"
  if [ "${sz:-0}" -gt 40000000 ]; then echo "RENDER OK attempt $a"; break; fi
  sleep 3
done
echo "render.sh finished $(date +%H:%M:%S)"