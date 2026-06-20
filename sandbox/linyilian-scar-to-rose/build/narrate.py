# -*- coding: utf-8 -*-
"""生成各段旁白 wav 到 audio/。男声 zm_yunxi。
用法: python build/narrate.py [intro s8_v s8_t ...]  (无参=全部)
段 key: intro / outro / cta / <songkey>_v / <songkey>_t
"""
import sys, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from content import INTRO_VOICE, OUTRO_VOICE, CTA_VOICE, SONGS

TTS = "../../tools/tts/venv/bin/python"
NARR = "../../tools/tts/narrate.py"
AUDIO = Path("audio"); AUDIO.mkdir(exist_ok=True)

SEGS = {"intro": INTRO_VOICE, "outro": OUTRO_VOICE, "cta": CTA_VOICE}
for s in SONGS:
    SEGS[f"{s['key']}_v"] = s["voice"]
    if s["trans"]:
        SEGS[f"{s['key']}_t"] = s["trans"]

want = sys.argv[1:] or list(SEGS.keys())
for k in want:
    if k not in SEGS:
        print("skip unknown", k); continue
    out = AUDIO / f"{k}.wav"
    subprocess.run([TTS, NARR, SEGS[k], "-o", str(out)], check=True)
    print("OK", out)
