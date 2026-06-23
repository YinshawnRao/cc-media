#!/usr/bin/env python3
"""展示段对齐机械闸门：用人声段数据强制校验「副歌入点 vs 旁白收尾」「展示段结尾 vs 乐句边界」。

解决两个反复翻车的问题（CONVENTIONS「展示段硬规则 (C)」的机械化执行）：
  问题1（旁白盖副歌）：转场配音把副歌人声大片盖住，旁白一结束副歌也快唱完了，
                       展示段推满音量时反而落在间奏/前奏/outro 纯器乐 —— 观众听不到"炸点"。
                       理想：配音快结束时副歌人声正好进来，并贯穿整个展示段。
  问题2（暴力裁切）  ：展示段因时长限制硬切在一句唱到半路的地方，人声戛然而止。
                       理想：结尾落在唱完一句之后或纯器乐 gap 上。

时间基准（全部用「源时间码」，即 vocal_segments 所在的那条 vert clip 的时间轴）：
  narr_end_src   —— 转场旁白念完那一刻对应的源时间
  show_start_src —— 展示段音乐推满（full volume）起点对应的源时间
  show_end_src   —— 展示段结束对应的源时间
对 full_build 风格：narr_end_src = ch_off-(POST+DIG)，show_start_src = ch_off，show_end_src = ch_off+show。
（ch_off = 手填的"副歌在源里的时间码" = 展示段音乐推满起点。见 sandbox/*/build/full_build.py。）

用法：
  # 1) 校验（闸门，违规 exit 1）—— 给 build 末尾内联调用，或 QA 阶段单独跑
  tools/tts/venv/bin/python tools/video/showcase_align.py check \
      --plan build/showcase_plan.json --vocals probe/vocal_analysis.json [--clips clips]

  # 2) 反推正确切点（authoring 期，避免手填 ch_off/show 拍脑袋）
  tools/tts/venv/bin/python tools/video/showcase_align.py plan \
      --vocals probe/vocal_analysis.json --clip vert_p4_wait --voice-dur 14.0 \
      [--lead 0.35 --post 0.25 --dig 1.45 --near 105 --min-show 25]

showcase_plan.json 结构（build 末尾用 dump_plan() 自动产出，无需手写）：
  {"consts": {"POST":0.25,"DIG":1.45},
   "songs": [{"key":"p4_wait","clip":"vert_p4_wait",
              "narr_end_src":103.70,"show_start_src":105.40,"show_end_src":135.40}, ...]}

build 内联用法（最强约束 —— 不对齐就不出 master）：
  from tools.video.showcase_align import verify, dump_plan
  plan = [dict(key=b["key"], clip=b["clip"],
               narr_end_src=b["narr_end"]-b["start"]+mseek ... ) for b in blocks]   # 见 dump_plan 注释
  dump_plan(plan, ROOT/"build"/"showcase_plan.json", consts={...})
  fails = [v for v in (verify_song(vocals[s["clip"]]["vocal_segments"], **s) for s in plan) if v["status"]=="FAIL"]
  if fails and not os.environ.get("SHOWCASE_OVERRIDE"):
      raise SystemExit("展示段对齐闸门未过：" + ...)

人声检测不可靠时（响摇滚/满编曲管弦乐，人声频带被乐器淹没 → vocal_segments 漏报）自动降级为
WARN 而非 FAIL，并打印 26s 试听 mp3 抽取命令，交回人工耳验（见 CONVENTIONS (C)）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ---- 可调阈值（改这里即可全局调松紧）----
ENTRY_BEFORE = 1.0   # 人声入点最早可早于旁白收尾多少秒仍算"正好进来"
ENTRY_AFTER = 4.0    # 人声入点最晚可晚于旁白收尾多少秒（再晚=展示段开头空器乐）
COVER_MIN = 0.50     # 展示段被人声覆盖的最低比例（低于=副歌被旁白盖走/落在器乐）
END_TOL = 1.2        # 展示段结尾允许落在一句结束后多少秒内仍算"唱完整句"
RELIABLE_PAD = 10.0  # showcase 前后这么宽的窗里若完全无人声活动 → 判检测不可靠（降级 WARN）
MIN_SHOW = 25.0      # plan 反推时展示段的最短目标（解说盘点类，见硬规则 (B)）


def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def verify_song(vocal_segments, narr_end_src, show_start_src, show_end_src,
                key=None, clip=None, **_ignore):
    """对一首歌做机械校验，返回 verdict dict。

    vocal_segments: [[s,e], ...]（源时间码，与 narr_end_src/show_* 同基准）
    返回 {status: OK|FAIL|WARN, reasons:[...], metrics:{...}, key, clip}
    """
    segs = sorted([[float(s), float(e)] for s, e in vocal_segments])
    show_dur = max(1e-6, show_end_src - show_start_src)

    # 检测可靠性：showcase 邻域内必须有人声活动，否则判检测漏报
    near_lo, near_hi = show_start_src - RELIABLE_PAD, show_end_src + RELIABLE_PAD
    activity_near = sum(_overlap(s, e, near_lo, near_hi) for s, e in segs)
    reliable = activity_near > 1.0

    # --- 覆盖率：展示段里有多少在唱 ---
    cover = sum(_overlap(s, e, show_start_src, show_end_src) for s, e in segs)
    coverage = cover / show_dur

    # --- Check 1：人声入点对齐旁白收尾（问题1）---
    entry_lo, entry_hi = narr_end_src - ENTRY_BEFORE, narr_end_src + ENTRY_AFTER
    onset_in_window = any(entry_lo <= s <= entry_hi for s, e in segs)
    # 或：旁白收尾时已有人声在唱且延续进展示段（人声在旁白尾巴下起来）
    carried_in = any(s <= narr_end_src <= e and e > show_start_src for s, e in segs)
    entry_ok = onset_in_window or carried_in
    coverage_ok = coverage >= COVER_MIN

    # --- Check 2：结尾不切半句（问题2）---
    end_seg = next(([s, e] for s, e in segs if s <= show_end_src <= e), None)
    if end_seg is None:
        end_ok = True            # 结尾落在器乐 gap → 干净
        tail_remaining = 0.0
    else:
        tail_remaining = end_seg[1] - show_end_src
        end_ok = tail_remaining <= END_TOL

    reasons = []
    if not reliable:
        status = "WARN"
        reasons.append(
            "人声检测不可靠（showcase 邻域几乎无人声活动；响摇滚/满编曲常漏报）→ 必须导 26s mp3 人工耳验")
    else:
        problems = []
        if not entry_ok:
            problems.append(
                f"问题1 人声入点没对上旁白收尾：旁白 {narr_end_src:.1f}s 收，"
                f"附近 [{entry_lo:.1f},{entry_hi:.1f}] 无人声入点（副歌可能被旁白盖走/展示段开头是空器乐）")
        if not coverage_ok:
            problems.append(
                f"问题1 展示段人声覆盖仅 {coverage*100:.0f}%（< {COVER_MIN*100:.0f}%）：大段没人唱，像在放伴奏")
        if not end_ok:
            problems.append(
                f"问题2 结尾切在半句：show_end {show_end_src:.1f}s 落在人声段 "
                f"[{end_seg[0]:.1f},{end_seg[1]:.1f}] 中，后面还要唱 {tail_remaining:.1f}s 就被切走")
        if problems:
            status = "FAIL"
            reasons = problems
        else:
            status = "OK"
            reasons.append(
                f"入点对齐 ✓ 覆盖 {coverage*100:.0f}% ✓ 结尾"
                + ("落器乐 gap ✓" if end_seg is None else f"在句末 {tail_remaining:.1f}s 内 ✓"))

    return {
        "key": key, "clip": clip, "status": status, "reasons": reasons,
        "metrics": {
            "coverage": round(coverage, 3),
            "narr_end_src": round(narr_end_src, 2),
            "show_start_src": round(show_start_src, 2),
            "show_end_src": round(show_end_src, 2),
            "tail_remaining": round(tail_remaining, 2),
            "reliable": reliable,
        },
    }


def dump_plan(songs, path, consts=None):
    """把 build 算好的展示段时间轴落盘成 showcase_plan.json，供 check 复核。

    songs: 每首一个 dict，至少含 clip / narr_end_src / show_start_src / show_end_src（key 可选）。
    full_build 风格的换算（在 build 里 blocks 算完后）：
        narr_end_src   = block["mseek"] + (block["narr_end"]   - block["start"])
        show_start_src = block["mseek"] + (block["full_start"] - block["start"])   # == ch_off
        show_end_src   = block["mseek"] + (block["end"]        - block["start"])   # == ch_off + show
    （mseek 是预切 -ss，clip-local 时间 + mseek = vert clip 源时间 = vocal_segments 基准。）
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"consts": consts or {}, "songs": songs}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def gate(blocks, vocals, consts=None, plan_path=None, clips_dir="clips",
         override_env="SHOWCASE_OVERRIDE", verbose=True):
    """build 内联强制闸门：对齐不过就不出 master（最强约束）。一行接入。

    blocks: full_build 风格的 list，每首至少含
        clip / start / narr_end / full_start / end，可选 mseek（预切 -ss，默认 0）。
        源时间码自动换算：
            narr_end_src   = mseek + (narr_end   - start)
            show_start_src = mseek + (full_start  - start)
            show_end_src   = mseek + (end         - start)
    vocals: vocal_analysis.json 路径，或 {clip: [[s,e],...]} dict。
            必须在 build 前先跑 tools/video/vocal_segments.py 产出（人声段基准 = 各 vert clip 源时间）。
    consts/plan_path: 落盘 showcase_plan.json（可复核/留档）。
    FAIL（且环境变量 override_env 未设）→ raise SystemExit；WARN 不阻断但必须人工耳验。

    用法（build 算完 blocks、建 master 之前）：
        import os, sys; sys.path.insert(0, str(ROOT.parents[2]))   # 让 tools 可 import
        from tools.video import showcase_align
        showcase_align.gate(blocks, ROOT/"probe"/"vocal_analysis.json",
                            consts=dict(POST=POST, DIG=DIG),
                            plan_path=ROOT/"build"/"showcase_plan.json")
    """
    vmap = vocals if isinstance(vocals, dict) else _load_vocals(vocals)
    songs, results, n_fail, n_warn = [], [], 0, 0
    for b in blocks:
        clip = b["clip"]
        mseek = b.get("mseek", 0.0)
        s = dict(
            key=b.get("key"), clip=clip,
            narr_end_src=round(mseek + (b["narr_end"] - b["start"]), 2),
            show_start_src=round(mseek + (b["full_start"] - b["start"]), 2),
            show_end_src=round(mseek + (b["end"] - b["start"]), 2),
        )
        songs.append(s)
        segs = vmap.get(clip)
        if segs is None:
            results.append((s["key"] or clip, "MISS",
                            [f"vocal_analysis.json 缺 clip『{clip}』→ 先跑 vocal_segments.py"], None))
            n_fail += 1
            continue
        v = verify_song(segs, **s)
        results.append((v["key"] or clip, v["status"], v["reasons"], v["metrics"]))
        if v["status"] == "FAIL":
            n_fail += 1
        elif v["status"] == "WARN":
            n_warn += 1

    if plan_path is not None:
        dump_plan(songs, plan_path, consts)

    if verbose:
        print("展示段对齐闸门（showcase_align.gate）")
        for name, status, reasons, metrics in results:
            mark = {"OK": "✓", "FAIL": "✗", "WARN": "⚠", "MISS": "?"}.get(status, "?")
            print(f"  [{mark} {status}] {name}")
            for r in reasons:
                print(f"        - {r}")
        print(f"  → FAIL={n_fail} WARN={n_warn} OK={len(results)-n_fail-n_warn}/{len(results)}")

    import os
    if n_fail and not os.environ.get(override_env):
        raise SystemExit(
            f"✗ 展示段对齐闸门未过（{n_fail} 首）。修 ch_off/show（可跑 "
            f"`showcase_align.py plan` 反推），或确属误报时设 {override_env}=1 跳过。")
    if n_warn and verbose:
        print(f"  ⚠ {n_warn} 首人声检测不可靠，导 26s mp3 人工耳验后才算过。")
    return results


def _load_vocals(vocals_path):
    data = json.loads(Path(vocals_path).read_text())
    # 兼容两种：{clip: {vocal_segments:...}} 或 {clip: [...segments...]}
    out = {}
    for k, v in data.items():
        if isinstance(v, dict) and "vocal_segments" in v:
            out[k] = v["vocal_segments"]
        elif isinstance(v, list):
            out[k] = v
    return out


def _mp3_hint(clip, show_start_src, clips_dir):
    src = f"{clips_dir}/{clip}.mp4" if clips_dir else f"clips/{clip}.mp4"
    ss = max(0.0, show_start_src - 2.0)
    return (f"ffmpeg -ss {ss:.2f} -i {src} -t 26 -vn "
            f"-af loudnorm out_{clip}.mp3 -y   # 导 26s 试听人工耳验")


def cmd_check(args):
    vocals = _load_vocals(args.vocals)
    plan = json.loads(Path(args.plan).read_text())
    songs = plan["songs"] if isinstance(plan, dict) else plan

    rows, n_fail, n_warn = [], 0, 0
    for s in songs:
        clip = s.get("clip") or s.get("key")
        segs = vocals.get(clip)
        if segs is None:
            rows.append((s.get("key") or clip, "MISS",
                         [f"vocal_analysis.json 里找不到 clip『{clip}』的人声数据 → 先跑 vocal_segments.py"]))
            n_fail += 1
            continue
        v = verify_song(segs, key=s.get("key"), clip=clip,
                        narr_end_src=s["narr_end_src"],
                        show_start_src=s["show_start_src"],
                        show_end_src=s["show_end_src"])
        rows.append((v["key"] or clip, v["status"], v["reasons"], v["metrics"], clip))
        if v["status"] == "FAIL":
            n_fail += 1
        elif v["status"] == "WARN":
            n_warn += 1

    print("展示段对齐校验（showcase_align）")
    print("=" * 64)
    for row in rows:
        name, status = row[0], row[1]
        mark = {"OK": "✓", "FAIL": "✗", "WARN": "⚠", "MISS": "?"}.get(status, "?")
        print(f"[{mark} {status}] {name}")
        for r in row[2]:
            print(f"      - {r}")
        if status == "WARN" and len(row) >= 5:
            print(f"      $ {_mp3_hint(row[4], row[3]['show_start_src'], args.clips)}")
    print("=" * 64)
    print(f"FAIL={n_fail}  WARN={n_warn}  OK={len(rows)-n_fail-n_warn}/{len(rows)}")
    if n_warn:
        print("⚠ WARN 项必须导 26s mp3 人工耳验后才算过（人声检测对该源不可靠）。")
    if n_fail:
        print("✗ 闸门未过：按上面修 ch_off / show（或跑 `plan` 反推正确切点）后重建。")
        return 1
    print("✓ 闸门通过。")
    return 0


def cmd_plan(args):
    vocals = _load_vocals(args.vocals)
    segs = vocals.get(args.clip)
    if segs is None:
        print(f"找不到 clip『{args.clip}』，可用：{list(vocals)}", file=sys.stderr)
        return 2
    segs = sorted([[float(s), float(e)] for s, e in segs])

    narr_end_offset = args.post + args.dig          # show_start_src - narr_end_src
    voice_span = args.lead + args.voice_dur         # 旁白在段内占用

    # 选副歌：只在实质乐句(≥5s)里挑，避免命中 2-3s 碎片当副歌。
    # --near 指定就取离它最近的实质段；否则取最长的。
    SUBSTANTIAL = 5.0
    big = [se for se in segs if se[1] - se[0] >= SUBSTANTIAL] or segs
    if args.near is not None:
        cand = min(big, key=lambda se: abs(se[0] - args.near))
    else:
        cand = max(big, key=lambda se: se[1] - se[0])
    onset = cand[0]

    # 让人声入点落在旁白收尾前 2s：show_start_src = onset + (POST+DIG) + 2
    show_start = round(onset + narr_end_offset + 2.0, 2)
    narr_end_src = round(show_start - narr_end_offset, 2)

    # 选结尾：找 >= MIN_SHOW 且落在某句结束(后接 gap)的点
    ends = [e for s, e in segs if e >= show_start + args.min_show]
    if ends:
        show_end = round(min(ends) + 0.8, 2)        # 句末 +0.8s 余量
    else:
        show_end = round(max(show_start + args.min_show, segs[-1][1] + 0.8), 2)
    show = round(show_end - show_start, 2)

    # ch_off 即 show_start（full_build 语义）；mseek 由 build 自行算
    print(f"clip={args.clip}  候选副歌段 [{cand[0]:.1f},{cand[1]:.1f}] ({cand[1]-cand[0]:.1f}s)")
    print(f"  人声入点 onset = {onset:.2f}s  (= 旁白收尾前 2s)")
    print(f"  → 建议 ch_off (show_start_src) = {show_start}")
    print(f"  → 建议 show = {show}   (show_end_src = {show_end})")
    print(f"  → narr_end_src = {narr_end_src}   (POST+DIG={narr_end_offset})")
    print("  自检：")
    v = verify_song(segs, narr_end_src=narr_end_src,
                    show_start_src=show_start, show_end_src=show_end, clip=args.clip)
    print(f"    [{v['status']}] " + "; ".join(v["reasons"]))
    print(f"  把这两个数填进 build 的该首 items：ch_off={show_start}, show={show}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="展示段对齐机械闸门")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="按 showcase_plan.json 校验全部歌曲（违规 exit 1）")
    c.add_argument("--plan", required=True, help="showcase_plan.json 路径")
    c.add_argument("--vocals", required=True, help="vocal_analysis.json 路径")
    c.add_argument("--clips", default="clips", help="clips 目录（仅用于 WARN 时拼 mp3 试听命令）")
    c.set_defaults(func=cmd_check)

    p = sub.add_parser("plan", help="反推某首的 ch_off / show 建议值")
    p.add_argument("--vocals", required=True)
    p.add_argument("--clip", required=True, help="vocal_analysis.json 里的 clip key，如 vert_p4_wait")
    p.add_argument("--voice-dur", type=float, required=True, help="该首转场旁白 wav 时长(s)")
    p.add_argument("--lead", type=float, default=0.35)
    p.add_argument("--post", type=float, default=0.25)
    p.add_argument("--dig", type=float, default=1.45)
    p.add_argument("--near", type=float, default=None, help="副歌大概在源里第几秒(可选，帮选段)")
    p.add_argument("--min-show", type=float, default=MIN_SHOW)
    p.set_defaults(func=cmd_plan)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
