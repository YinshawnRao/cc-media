#!/usr/bin/env bash
# Render with per-attempt stall watchdog (HyperFrames silently hangs on GPU frame capture).
# Stall = no growth in (work-dir file count + captured frames + output bytes) for STALL_MAX seconds,
# UNLESS we're in the encode phase (output file exists / capture near-complete).
cd /Users/yinshawnrao/explorer/cc-media/sandbox/liangyongqi-hardest-top5 || exit 1
# Long video (316s) > default 240s streaming cap -> falls back to capture-all path that hangs.
# Raise cap so streaming encode (default-on) engages; it encodes frames incrementally
# (requires -w 1) instead of the capture-all path that hangs at this duration.
export PRODUCER_STREAMING_ENCODE_MAX_DURATION_SECONDS=900
LOG=renders/render.log
OUT=renders/full_raw.mp4
TARGET=313        # min acceptable duration (s) ~ master 315.9
STALL_MAX=120     # seconds of no progress -> kill & retry (deadlock shows 0% CPU immediately)
HF="hyperframes@0.6.47"   # pin to project's known-good version (0.6.88 hung pre-capture)
: > "$LOG"

sig() {
  local f c b
  f=$(find renders/work-* -type f 2>/dev/null | wc -l | tr -d ' ')
  c=$(find renders/work-*/captured-frames -type f 2>/dev/null | wc -l | tr -d ' ')
  b=0; [ -f "$OUT" ] && b=$(($(wc -c < "$OUT")/1000000))
  echo "$((f + c)) $c $b"
}
ok() {
  [ -f "$OUT" ] || return 1
  local d; d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" 2>/dev/null | cut -d. -f1)
  [ -n "$d" ] && [ "$d" -ge "$TARGET" ] 2>/dev/null
}

for attempt in 1 2 3 4; do
  echo "=== attempt $attempt $(date +%T) ===" >> "$LOG"
  rm -rf renders/work-* "$OUT" 2>/dev/null
  npx "$HF" render --output "$OUT" --sdr -w 1 >> "$LOG" 2>&1 &
  RPID=$!
  prev="x"; stall=0
  while kill -0 "$RPID" 2>/dev/null; do
    sleep 15
    if ok; then echo "OK mid dur ok @ $(date +%T)" >> "$LOG"; break; fi
    read total cap bytes <<< "$(sig)"
    cur="$total $bytes"
    if [ "$cur" = "$prev" ]; then stall=$((stall+15)); else stall=0; fi
    prev="$cur"
    echo "  $(date +%T) total=$total captured=$cap outMB=$bytes stall=${stall}s" >> "$LOG"
    # encode phase (output exists OR capture ~complete): be patient, don't kill
    # sig (cur) already includes outMB, so streaming progress keeps stall=0.
    # Only the capture-all final-encode phase (cap~complete, no incremental bytes) is exempt.
    if [ "$stall" -ge "$STALL_MAX" ]; then
      if [ "$cap" -ge 9000 ] && [ ! -f "$OUT" ]; then
        echo "  stall but final-encode phase, waiting" >> "$LOG"; stall=0
      else
        echo "  STALL ${stall}s no progress -> kill & retry" >> "$LOG"
        kill "$RPID" 2>/dev/null; sleep 2; pkill -f puppeteer_dev_chrome_profile 2>/dev/null
        break
      fi
    fi
  done
  wait "$RPID" 2>/dev/null
  if ok; then echo "RENDER_OK attempt $attempt dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")" >> "$LOG"; break; fi
  pkill -f puppeteer_dev_chrome_profile 2>/dev/null
  echo "  attempt $attempt incomplete" >> "$LOG"
done
echo "=== watchdog done $(date +%T) ===" >> "$LOG"
