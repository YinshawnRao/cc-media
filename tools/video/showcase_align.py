#!/usr/bin/env python3
"""展示段对齐机械闸门：用多证据人声数据校验「副歌入点」和「安全乐句出点」。

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
  from tools.video.showcase_align import gate
  gate(blocks, ROOT/"probe"/"vocal_analysis.json",
       consts={"POST": POST, "DIG": DIG},
       plan_path=ROOT/"build"/"showcase_plan.json")

旧版 ``vocal_segments.py`` 只有频带能量区间，不能证明是目标歌手本人演唱，也不能证明区间端点
就是歌词/乐句边界。此类数据只允许得到 REVIEW，必须有逐曲人工批准记录，不能再靠全局环境变量
跳过。新版分析可提供 ``lead_segments``、``safe_cut_intervals`` 和 ``evidence_level`` 后再自动 OK。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# ---- 可调阈值（改这里即可全局调松紧）----
ENTRY_BEFORE = 1.0      # 人声入点最早可早于旁白收尾多少秒仍算"正好进来"
ENTRY_AFTER = 4.0       # 人声入点最晚可晚于旁白收尾多少秒（再晚=展示段开头空器乐）
COVER_MIN = 0.50        # 展示段被主唱覆盖的最低比例
END_ACTIVE_TOL = 0.12   # 仅容忍检测分帧误差；不再允许切掉 1.2s 唱声
END_RELEASE = 0.30      # 确认尾音结束后保留的释放余量
END_LOOKAHEAD = 3.0     # 候选出点后至少这么久无新主唱 onset；覆盖慢歌句间气口
RELIABLE_PAD = 10.0     # showcase 前后检测活动检查窗
MIN_SHOW = 25.0         # plan 反推时展示段的最短目标（解说盘点类，见硬规则 (B)）
MAX_AUTO_EXTEND = 24.0  # 为吞并下一小句允许自动延长的最大秒数；再长转 REVIEW
APPROVAL_TIME_TOL = 0.02  # 批准绑定到具体时间窗；时间码变化即失效

TRUSTED_EVIDENCE = {"multi_evidence", "manual", "verified"}
TRUSTED_BOUNDARY_ACTIVITY = {"whisper_word_timestamps", "manual", "verified"}


def _overlap(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def _coerce_analysis(data):
    """兼容旧 ``[[start,end], ...]`` 与新版分析对象。

    新版对象可包含：
      - lead_segments: 目标主唱区间
      - boundary_segments: 所有有效 word/咬字区间（可比主唱证据更保守）
      - vocal_segments: 兼容字段
      - safe_cut_intervals: 已由歌词/多证据确认的安全出点区间
      - evidence_level: multi_evidence | manual | verified | candidate | legacy_energy
    """
    if isinstance(data, dict):
        segs = data.get("lead_segments")
        if segs is None:
            segs = data.get("vocal_segments", [])
        level = data.get("evidence_level")
        if not level:
            level = "candidate" if data.get("schema_version", 1) >= 2 else "legacy_energy"
        safe = data.get("safe_cut_intervals", [])
        if "boundary_segments" in data:
            boundary = data.get("boundary_segments") or []
        else:
            boundary = segs
        boundary_evidence = data.get("boundary_evidence")
        if not boundary_evidence:
            boundary_evidence = (
                "manual" if level in {"manual", "verified"} else "legacy_energy")
        return {
            "segments": sorted([[float(s), float(e)] for s, e in segs]),
            "boundary_segments": sorted([[float(s), float(e)] for s, e in boundary]),
            "boundary_evidence": str(boundary_evidence),
            "safe_cut_intervals": sorted([[float(s), float(e)] for s, e in safe]),
            "evidence_level": str(level),
            "detector": data.get("detector", "unknown"),
        }
    return {
        "segments": sorted([[float(s), float(e)] for s, e in (data or [])]),
        "boundary_segments": sorted([[float(s), float(e)] for s, e in (data or [])]),
        "boundary_evidence": "legacy_energy",
        "safe_cut_intervals": [],
        "evidence_level": "legacy_energy",
        "detector": "legacy_band_energy",
    }


def _next_onset(segs, t):
    return next((s for s, _ in segs if s > t), None)


def _previous_end(segs, t):
    ends = [e for _, e in segs if e <= t]
    return max(ends) if ends else None


def _safe_interval_for(intervals, t):
    return next(([s, e] for s, e in intervals if s <= t <= e), None)


def verify_song(vocal_segments, narr_end_src, show_start_src, show_end_src,
                key=None, clip=None, mode=None, **_ignore):
    """对一首歌做机械校验，返回 verdict dict。

    vocal_segments: 旧二维区间，或新版分析对象（源时间码，与 show_* 同基准）
    返回 {status: OK|FAIL|REVIEW, reasons:[...], metrics:{...}, key, clip}
    """
    analysis = _coerce_analysis(vocal_segments)
    intro_hard_restart = mode == "intro_hard_restart"
    segs = analysis["segments"]
    boundary_segs = analysis["boundary_segments"]
    boundary_evidence = analysis["boundary_evidence"]
    safe_cut_intervals = analysis["safe_cut_intervals"]
    evidence_level = analysis["evidence_level"]
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
    # 身份/覆盖看 lead_segments；是否仍在咬字以及下一 onset 看更保守的 boundary_segments。
    end_seg = next(([s, e] for s, e in boundary_segs if s <= show_end_src <= e), None)
    next_onset = _next_onset(boundary_segs, show_end_src)
    previous_end = _previous_end(boundary_segs, show_end_src)
    gap_to_next = None if next_onset is None else next_onset - show_end_src
    release_after_tail = None if previous_end is None else show_end_src - previous_end
    safe_interval = _safe_interval_for(safe_cut_intervals, show_end_src)
    manual_boundary_override = bool(
        safe_interval is not None and evidence_level in {"manual", "verified"})

    if end_seg is not None:
        tail_remaining = end_seg[1] - show_end_src
        end_ok = tail_remaining <= END_ACTIVE_TOL
        end_reason = ("active_tail_tolerance" if end_ok else "active_vocal")
    else:
        tail_remaining = 0.0
        # 自动 Whisper gap 仍必须过 3s 前向保护；只有显式 manual/verified
        # 乐句边界可覆盖启发式。但 active segment 中的硬 FAIL 永不覆盖。
        released = (manual_boundary_override or release_after_tail is None or
                    release_after_tail >= END_RELEASE - 1e-6)
        no_imminent_onset = (manual_boundary_override or gap_to_next is None or
                             gap_to_next >= END_LOOKAHEAD)
        end_ok = released and no_imminent_onset
        if not released:
            end_reason = "tail_release_too_short"
        elif not no_imminent_onset:
            end_reason = "imminent_next_onset"
        else:
            end_reason = "quiet_gap"

    trusted_identity = evidence_level in TRUSTED_EVIDENCE
    trusted_boundary = safe_interval is not None
    trusted_boundary_activity = boundary_evidence in TRUSTED_BOUNDARY_ACTIVITY

    end_problem = None
    if not end_ok:
        if end_seg is not None:
            end_problem = (
                f"问题2 结尾切在唱声中：show_end {show_end_src:.1f}s 落在人声段 "
                f"[{end_seg[0]:.1f},{end_seg[1]:.1f}]，后面仍有 {tail_remaining:.1f}s")
        elif gap_to_next is not None and gap_to_next < END_LOOKAHEAD:
            end_problem = (
                f"问题2 把句内气口当句末：show_end {show_end_src:.1f}s 后 {gap_to_next:.1f}s "
                f"又有主唱 onset（要求至少 {END_LOOKAHEAD:.1f}s 前向保护）")
        else:
            end_problem = (
                f"问题2 尾音释放不足：show_end {show_end_src:.1f}s 距检测尾音不足 {END_RELEASE:.2f}s")

    hard_problems = []
    review_problems = []
    if intro_hard_restart and abs(show_start_src) > 0.05:
        hard_problems.append(
            f"前奏硬起模式要求 show_start_src=0，当前为 {show_start_src:.2f}s")
    if not reliable:
        review_problems.append(
            "主唱检测证据不足（showcase 邻域几乎无活动；满编曲可能漏报）→ 必须人工复核")
    elif not intro_hard_restart:
        if not entry_ok:
            target = hard_problems if trusted_identity else review_problems
            target.append(
                f"问题1 人声入点没对上旁白收尾：旁白 {narr_end_src:.1f}s 收，"
                f"附近 [{entry_lo:.1f},{entry_hi:.1f}] 无人声入点（副歌可能被旁白盖走/展示段开头是空器乐）")
        if not coverage_ok:
            target = hard_problems if trusted_identity else review_problems
            target.append(
                f"问题1 展示段人声覆盖仅 {coverage*100:.0f}%（< {COVER_MIN*100:.0f}%）：大段没人唱，像在放伴奏")
    if end_problem:
        target = hard_problems if trusted_boundary_activity else review_problems
        target.append(end_problem)

    if hard_problems:
        status = "FAIL"
        reasons = hard_problems + review_problems
    elif review_problems:
        status = "REVIEW"
        reasons = review_problems
    elif not trusted_identity:
        status = "REVIEW"
        reasons = [
            f"仅有 {evidence_level} 区间，不能证明是目标歌手而非乐器/观众；需新版多证据分析或人工批准"]
    elif not trusted_boundary:
        status = "REVIEW"
        reasons = [
            "主唱覆盖通过，但没有歌词/乐句证据确认 safe_cut_intervals；不得仅凭能量 gap 自动放行"]
    else:
        status = "OK"
        prefix = ("前奏从源 0 秒硬起 ✓ " if intro_hard_restart
                  else f"入点对齐 ✓ 覆盖 {coverage*100:.0f}% ✓ ")
        reasons = [
            prefix + "结尾"
            + ("落已确认安全区间 ✓" if safe_interval else f"在句末 {tail_remaining:.1f}s 内 ✓")]

    return {
        "key": key, "clip": clip, "status": status, "reasons": reasons,
        "metrics": {
            "coverage": round(coverage, 3),
            "narr_end_src": round(narr_end_src, 2),
            "show_start_src": round(show_start_src, 2),
            "show_end_src": round(show_end_src, 2),
            "tail_remaining": round(tail_remaining, 2),
            "next_onset": None if next_onset is None else round(next_onset, 2),
            "gap_to_next_onset": None if gap_to_next is None else round(gap_to_next, 2),
            "release_after_tail": None if release_after_tail is None else round(release_after_tail, 2),
            "end_reason": end_reason,
            "evidence_level": evidence_level,
            "trusted_identity": trusted_identity,
            "trusted_boundary": trusted_boundary,
            "boundary_evidence": boundary_evidence,
            "trusted_boundary_activity": trusted_boundary_activity,
            "reliable": reliable,
            "mode": mode,
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
    payload = {"schema_version": 2, "consts": consts or {}, "songs": songs}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load_analysis(vocals_path):
    path = Path(vocals_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "clips" in data:
        data = data["clips"]
    # 单文件模式：vocal_segments.py 会直接写 {name,duration,vocal_segments}，
    # 不能把 vocal_segments 误当成 clip key。
    if isinstance(data, dict) and ("vocal_segments" in data or "lead_segments" in data):
        key = str(data.get("name") or path.stem.removesuffix(".vocal"))
        return {key: data}
    if not isinstance(data, dict):
        return {}
    return {
        k: v for k, v in data.items()
        if isinstance(v, list) or (isinstance(v, dict) and
                                   ("vocal_segments" in v or "lead_segments" in v))
    }


def _load_vocals(vocals_path):
    """旧调用方兼容：只返回区间；新 gate 应使用 ``_load_analysis``。"""
    out = {}
    for k, v in _load_analysis(vocals_path).items():
        out[k] = _coerce_analysis(v)["segments"]
    return out


def _load_approvals(approvals):
    if approvals is None:
        return {}
    if not isinstance(approvals, dict):
        path = Path(approvals)
        if not path.exists():
            return {}
        approvals = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(approvals, dict) and "approvals" in approvals:
        approvals = approvals["approvals"]
    return approvals if isinstance(approvals, dict) else {}


def _analysis_fingerprint(analysis):
    """把实际用于判定的分析对象绑定进人工批准，防止重跑检测后沿用旧记录。"""
    canonical = json.dumps(
        analysis, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_approval(approvals, key, clip, expected_window=None, expected_analysis=None):
    item = approvals.get(key) or approvals.get(clip)
    if item is None:
        return None, None
    if not isinstance(item, dict) or item.get("status") != "approved":
        return None, "批准项必须是对象且 status=approved"
    reason = str(item.get("reason", "")).strip()
    evidence = item.get("evidence", [])
    if isinstance(evidence, str):
        evidence = [evidence]
    evidence = [str(x).strip() for x in evidence if str(x).strip()]
    if not reason or not evidence:
        return None, "批准项缺 reason 或 evidence"
    if str(item.get("clip", "")).strip() != str(clip):
        return None, f"批准项 clip 与当前不一致（应为 {clip}）"

    # 批准必须绑定具体剪辑窗口，防止改了 ch_off/show 后沿用旧批准误放行。
    bound = item.get("window", item)
    if expected_window is not None:
        for name in ("narr_end_src", "show_start_src", "show_end_src"):
            if name not in bound:
                return None, f"批准项缺 window.{name}，无法确认是否对应当前剪辑"
            try:
                delta = abs(float(bound[name]) - float(expected_window[name]))
            except (TypeError, ValueError):
                return None, f"批准项 window.{name} 不是数字"
            if delta > APPROVAL_TIME_TOL:
                return None, (f"批准项已过期：window.{name}={float(bound[name]):.2f}，"
                              f"当前为 {float(expected_window[name]):.2f}")
    if expected_analysis is not None:
        expected_hash = _analysis_fingerprint(expected_analysis)
        actual_hash = str(item.get("analysis_sha256", "")).strip().lower()
        if not actual_hash:
            return None, "批准项缺 analysis_sha256，无法确认是否对应当前检测结果"
        if actual_hash != expected_hash:
            return None, "批准项已过期：analysis_sha256 与当前检测结果不一致"
    return {"reason": reason, "evidence": evidence}, None


def _valid_approval(approvals, key, clip, expected_window=None, expected_analysis=None):
    """兼容布尔式调用；详细错误由 ``_validate_approval`` 返回。"""
    return _validate_approval(
        approvals, key, clip, expected_window, expected_analysis)[0]


def gate(blocks, vocals, consts=None, plan_path=None, clips_dir="clips",
         approvals=None, override_env="SHOWCASE_OVERRIDE", verbose=True):
    """build 内联强制闸门：对齐不过就不出 master（最强约束）。一行接入。

    blocks: full_build 风格的 list，每首至少含
        clip / start / narr_end / full_start / end，可选 mseek（预切 -ss，默认 0）。
        源时间码自动换算：
            narr_end_src   = mseek + (narr_end   - start)
            show_start_src = mseek + (full_start  - start)
            show_end_src   = mseek + (end         - start)
    vocals: vocal_analysis.json 路径，或 {clip: analysis} dict。
            新版分析对象应带 lead_segments/evidence_level/safe_cut_intervals。
    consts/plan_path: 落盘 showcase_plan.json（可复核/留档）。
    approvals: 逐曲人工批准 JSON 路径或 dict。每项必须绑定 clip、analysis_sha256、
               三个时间码，并有 status=approved、reason、evidence。
    REVIEW 可凭绑定时间窗的逐曲批准放行；硬边界 FAIL 不可批准跳过。
    未获证明即 raise SystemExit。全局 SHOWCASE_OVERRIDE 不再跳过。

    用法（build 算完 blocks、建 master 之前）：
        import os, sys; sys.path.insert(0, str(ROOT.parents[2]))   # 让 tools 可 import
        from tools.video import showcase_align
        showcase_align.gate(blocks, ROOT/"probe"/"vocal_analysis.json",
                            consts=dict(POST=POST, DIG=DIG),
                            plan_path=ROOT/"build"/"showcase_plan.json")
    """
    vmap = vocals if isinstance(vocals, dict) else _load_analysis(vocals)
    if isinstance(vmap, dict) and "clips" in vmap:
        vmap = vmap["clips"]
    if approvals is None and plan_path is not None:
        auto_approvals = Path(plan_path).with_name("showcase_approvals.json")
        approvals = auto_approvals if auto_approvals.exists() else None
    approval_map = _load_approvals(approvals)
    gate_mode = (consts or {}).get("mode") if isinstance(consts, dict) else None
    songs, results = [], []
    counts = {"OK": 0, "FAIL": 0, "REVIEW": 0, "APPROVED": 0, "MISS": 0}
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
        analysis = vmap.get(clip)
        if analysis is None:
            results.append((s["key"] or clip, "MISS",
                            [f"vocal_analysis.json 缺 clip『{clip}』→ 先跑 vocal_segments.py"], None))
            counts["MISS"] += 1
            continue
        v = verify_song(analysis, mode=b.get("mode", gate_mode), **s)
        status, reasons = v["status"], list(v["reasons"])
        approval, approval_error = _validate_approval(
            approval_map, s.get("key"), clip, expected_window=s,
            expected_analysis=analysis)
        if status == "REVIEW" and approval:
            status = "APPROVED"
            reasons.append("逐曲人工批准：" + approval["reason"])
            reasons.append("证据：" + ", ".join(approval["evidence"]))
        elif status == "FAIL" and approval:
            reasons.append("逐曲批准不能覆盖硬边界 FAIL；请修切点或写入校正后的主唱/安全边界分析")
        elif status in {"FAIL", "REVIEW"} and approval_error:
            reasons.append("逐曲批准未生效：" + approval_error)
        results.append((v["key"] or clip, status, reasons, v["metrics"]))
        counts[status] += 1

    if plan_path is not None:
        dump_plan(songs, plan_path, consts)

    if verbose:
        print("展示段对齐闸门（showcase_align.gate）")
        for name, status, reasons, metrics in results:
            mark = {"OK": "✓", "APPROVED": "✓", "FAIL": "✗", "REVIEW": "⚠", "MISS": "?"}.get(status, "?")
            print(f"  [{mark} {status}] {name}")
            for r in reasons:
                print(f"        - {r}")
        print("  → " + " ".join(f"{k}={counts[k]}" for k in ("FAIL", "REVIEW", "MISS", "APPROVED", "OK")))

    import os
    if os.environ.get(override_env) and verbose:
        print(f"  ⚠ {override_env} 已废弃：全局跳过会掩盖其他歌曲问题，请写逐曲 showcase_approvals.json。")
    n_block = counts["FAIL"] + counts["REVIEW"] + counts["MISS"]
    if n_block:
        raise SystemExit(
            f"✗ 展示段闸门仍有 {n_block} 首未获证明。修切点/重跑多证据检测；"
            "REVIEW 经逐曲试听后在 showcase_approvals.json 记录 reason + evidence。")
    return results


def _mp3_hint(clip, show_start_src, clips_dir):
    src = f"{clips_dir}/{clip}.mp4" if clips_dir else f"clips/{clip}.mp4"
    ss = max(0.0, show_start_src - 2.0)
    return (f"ffmpeg -ss {ss:.2f} -i {src} -t 26 -vn "
            f"-af loudnorm out_{clip}.mp3 -y   # 导 26s 试听人工耳验")


def cmd_check(args):
    vocals = _load_analysis(args.vocals)
    approvals_path = args.approvals
    if approvals_path is None:
        candidate = Path(args.plan).with_name("showcase_approvals.json")
        approvals_path = candidate if candidate.exists() else None
    approvals = _load_approvals(approvals_path)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    songs = plan["songs"] if isinstance(plan, dict) else plan
    plan_mode = (plan.get("consts", {}).get("mode")
                 if isinstance(plan, dict) else None)

    rows = []
    counts = {"OK": 0, "FAIL": 0, "REVIEW": 0, "APPROVED": 0, "MISS": 0}
    for s in songs:
        clip = s.get("clip") or s.get("key")
        analysis = vocals.get(clip)
        if analysis is None:
            rows.append((s.get("key") or clip, "MISS",
                         [f"vocal_analysis.json 里找不到 clip『{clip}』的人声数据 → 先跑 vocal_segments.py"]))
            counts["MISS"] += 1
            continue
        v = verify_song(analysis, key=s.get("key"), clip=clip,
                        narr_end_src=s["narr_end_src"],
                        show_start_src=s["show_start_src"],
                        show_end_src=s["show_end_src"],
                        mode=s.get("mode", plan_mode))
        status, reasons = v["status"], list(v["reasons"])
        approval, approval_error = _validate_approval(
            approvals, s.get("key"), clip, expected_window=s,
            expected_analysis=analysis)
        if status == "REVIEW" and approval:
            status = "APPROVED"
            reasons.append("逐曲人工批准：" + approval["reason"])
            reasons.append("证据：" + ", ".join(approval["evidence"]))
        elif status == "FAIL" and approval:
            reasons.append("逐曲批准不能覆盖硬边界 FAIL；请修切点或写入校正后的主唱/安全边界分析")
        elif status in {"FAIL", "REVIEW"} and approval_error:
            reasons.append("逐曲批准未生效：" + approval_error)
        rows.append((v["key"] or clip, status, reasons, v["metrics"], clip))
        counts[status] += 1

    print("展示段对齐校验（showcase_align）")
    print("=" * 64)
    for row in rows:
        name, status = row[0], row[1]
        mark = {"OK": "✓", "APPROVED": "✓", "FAIL": "✗", "REVIEW": "⚠", "MISS": "?"}.get(status, "?")
        print(f"[{mark} {status}] {name}")
        for r in row[2]:
            print(f"      - {r}")
        if status == "REVIEW" and len(row) >= 5:
            print(f"      $ {_mp3_hint(row[4], row[3]['show_start_src'], args.clips)}")
    print("=" * 64)
    print("  ".join(f"{k}={counts[k]}" for k in ("FAIL", "REVIEW", "MISS", "APPROVED", "OK")))
    n_block = counts["FAIL"] + counts["REVIEW"] + counts["MISS"]
    if n_block:
        print("✗ 闸门未过：修切点/重跑分析，或为确属误报的单曲补逐曲批准记录。")
        return 1
    print("✓ 闸门通过。")
    return 0


def _find_safe_end(segs, show_start, min_show):
    """从最短展示目标开始，只向后找不会截在下一次 onset 前的候选出点。"""
    target = show_start + min_show
    if not segs:
        return target, False, "没有 word/咬字边界证据，不能自动规划出点"
    candidates = [(idx, e) for idx, (_, e) in enumerate(segs) if e >= target]
    if not candidates:
        fallback = max(target, segs[-1][1] + END_RELEASE)
        return fallback, False, "最短展示后没有可用人声段终点"

    for idx, end in candidates:
        cut = end + END_RELEASE
        next_onset = next((s for s, _ in segs[idx + 1:] if s > end), None)
        if next_onset is not None and next_onset - cut < END_LOOKAHEAD:
            continue  # 句内气口：吞并下一小句后继续找
        extension = cut - target
        if extension > MAX_AUTO_EXTEND:
            return cut, False, f"安全出点需额外延长 {extension:.1f}s，超过自动上限 {MAX_AUTO_EXTEND:.1f}s"
        return cut, True, "尾音释放后且前向保护窗内无新 onset"

    cut = segs[-1][1] + END_RELEASE
    extension = cut - target
    return cut, extension <= MAX_AUTO_EXTEND, "连续人声延伸到最后检测段"


def cmd_approval_template(args):
    """从已落盘 plan 生成逐曲批准骨架；默认拒绝覆盖已有人工记录。"""
    plan_path = Path(args.plan)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    songs = plan["songs"] if isinstance(plan, dict) else plan
    analyses = _load_analysis(args.vocals)
    out = Path(args.out) if args.out else plan_path.with_name("showcase_approvals.json")
    if out.exists() and not args.force:
        print(f"拒绝覆盖已有批准文件：{out}（确需重建请加 --force）", file=sys.stderr)
        return 2
    approvals = {}
    for s in songs:
        name = s.get("key") or s.get("clip")
        clip = s.get("clip") or name
        analysis = analyses.get(clip)
        if analysis is None:
            print(f"无法生成批准项：分析文件缺 clip『{clip}』", file=sys.stderr)
            return 2
        approvals[name] = {
            "status": "pending",
            "clip": clip,
            "analysis_sha256": _analysis_fingerprint(analysis),
            "window": {
                "narr_end_src": s["narr_end_src"],
                "show_start_src": s["show_start_src"],
                "show_end_src": s["show_end_src"],
            },
            "reason": "",
            "evidence": [],
        }
    payload = {
        "schema_version": 1,
        "instructions": (
            "逐曲试听并核对主唱身份、观众声和完整乐句；确认后改 status=approved，"
            "填写具体 reason 与 evidence。任一时间码或分析内容变化都会让批准失效。"),
        "approvals": approvals,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {out}（全部为 pending，不会自动放行）")
    return 0


def cmd_plan(args):
    vocals = _load_analysis(args.vocals)
    raw_analysis = vocals.get(args.clip)
    if raw_analysis is None:
        print(f"找不到 clip『{args.clip}』，可用：{list(vocals)}", file=sys.stderr)
        return 2
    analysis = _coerce_analysis(raw_analysis)
    segs = analysis["segments"]
    boundary_segs = analysis["boundary_segments"]
    if not segs:
        print(f"clip『{args.clip}』没有任何候选主唱区间，无法自动 plan", file=sys.stderr)
        return 2

    narr_end_offset = args.post + args.dig          # show_start_src - narr_end_src

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

    # 选结尾：最短展示之后只向后找；短气口后若仍有 onset，吞并下一小句。
    show_end_raw, auto_safe, end_note = _find_safe_end(boundary_segs, show_start, args.min_show)
    show_end = round(show_end_raw, 2)
    show = round(show_end - show_start, 2)

    # ch_off 即 show_start（full_build 语义）；mseek 由 build 自行算
    print(f"clip={args.clip}  候选副歌段 [{cand[0]:.1f},{cand[1]:.1f}] ({cand[1]-cand[0]:.1f}s)")
    print(f"  人声入点 onset = {onset:.2f}s  (= 旁白收尾前 2s)")
    print(f"  → 建议 ch_off (show_start_src) = {show_start}")
    print(f"  → 建议 show = {show}   (show_end_src = {show_end})")
    print(f"  → narr_end_src = {narr_end_src}   (POST+DIG={narr_end_offset})")
    print(f"  → 出点搜索：{'自动候选' if auto_safe else '需 REVIEW'}；{end_note}")
    print("  自检：")
    v = verify_song(raw_analysis, narr_end_src=narr_end_src,
                    show_start_src=show_start, show_end_src=show_end, clip=args.clip)
    print(f"    [{v['status']}] " + "; ".join(v["reasons"]))
    print(f"  把这两个数填进 build 的该首 items：ch_off={show_start}, show={show}")
    if not auto_safe or v["status"] == "FAIL":
        print("  ✗ 未找到能通过边界自检的自动切点，请人工复核后再写入 build。", file=sys.stderr)
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description="展示段对齐机械闸门")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="按 showcase_plan.json 校验全部歌曲（违规 exit 1）")
    c.add_argument("--plan", required=True, help="showcase_plan.json 路径")
    c.add_argument("--vocals", required=True, help="vocal_analysis.json 路径")
    c.add_argument("--clips", default="clips", help="clips 目录（仅用于 REVIEW 时拼 mp3 试听命令）")
    c.add_argument("--approvals", help="逐曲人工批准 JSON（默认取 plan 同目录）")
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

    a = sub.add_parser("approval-template", help="按 plan 生成逐曲人工批准骨架")
    a.add_argument("--plan", required=True, help="showcase_plan.json 路径")
    a.add_argument("--vocals", required=True, help="与 plan 对应的 vocal_analysis.json")
    a.add_argument("--out", help="输出路径；默认写到 plan 同目录 showcase_approvals.json")
    a.add_argument("--force", action="store_true", help="覆盖已有批准文件")
    a.set_defaults(func=cmd_approval_template)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
