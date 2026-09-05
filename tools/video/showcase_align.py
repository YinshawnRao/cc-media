#!/usr/bin/env python3
"""展示段对齐机械闸门：用多证据人声数据校验「副歌入点」和「安全乐句出点」。

解决旁白与歌曲展示交接、完整乐句出点两个问题：
  问题1（旁白盖副歌）：转场配音把副歌人声大片盖住，旁白一结束副歌也快唱完了，
                       展示段推满音量时反而落在间奏/前奏/outro 纯器乐 —— 观众听不到"炸点"。
                       理想：配音快结束时副歌人声正好进来，并贯穿整个展示段。
  问题2（暴力裁切）  ：展示段因时长限制硬切在一句唱到半路的地方，人声戛然而止。
                       理想：结尾落在唱完一句之后或纯器乐 gap 上。

时间基准（全部用「源时间码」，即 vocal_segments 所在的那条 vert clip 的时间轴）：
  narr_end_src   —— 转场旁白收尾对应的源时间；无旁白时等于 show_start_src，作为展示入点锚点
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
      --vocals probe/vocal_analysis.json --clip vert_p4_wait \
      [--post 0.25 --dig 1.45 --near 105 --min-show 60 --through 175]

plan 只建议源内展示窗口，不根据旁白 WAV 计算章节长度；实际预滚/duck 时长由 build 绑定 WAV。
无旁白歌曲直接填写 show_start_src = narr_end_src 的真实展示窗并运行 check。

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
就是歌词/乐句边界。此类数据只允许得到 REVIEW；先补 multi 分析，再按失败原因修复窗口或来源。
Live 等检测能力限制且硬 FAIL=0 时，本地可用真实证据与 hash/window-bound agent observation 得到
OBSERVED，无须重复必定 REVIEW 的候选；发布 ``--require-human-review`` 仍只接受 human APPROVED。新版分析可提供
``lead_segments``、``safe_cut_intervals`` 和 ``evidence_level`` 后再自动 OK。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime
from pathlib import Path

# ---- 可调阈值（改这里即可全局调松紧）----
ENTRY_BEFORE = 1.0      # 人声入点最早可早于旁白收尾多少秒仍算"正好进来"
ENTRY_AFTER = 4.0       # 人声入点最晚可晚于旁白收尾多少秒（再晚=展示段开头空器乐）
COVER_MIN = 0.50        # 展示段被主唱覆盖的最低比例
END_ACTIVE_TOL = 0.12   # 仅容忍检测分帧误差；不再允许切掉 1.2s 唱声
END_RELEASE = 0.30      # 确认尾音结束后保留的释放余量
END_LOOKAHEAD = 3.0     # 候选出点后至少这么久无新主唱 onset；覆盖慢歌句间气口
RELIABLE_PAD = 10.0     # showcase 前后检测活动检查窗
MIN_SHOW = 60.0         # plan 初筛预留量，可按完整段落调整；不是 check 硬下限或总长限制
PLAN_ENTRY_PAD = 1.0    # full volume 从目标首字前开始，保留入点铺垫
PLAN_END_PAD = 1.0      # 规划比检测最低释放容差留更多余韵；仍须核对真实尾音
APPROVAL_TIME_TOL = 0.02  # 批准绑定到具体时间窗；时间码变化即失效

TRUSTED_EVIDENCE = {"multi_evidence", "manual", "verified"}
TRUSTED_BOUNDARY_ACTIVITY = {"whisper_word_timestamps", "manual", "verified"}

AUTO_RECOVERY_GUIDANCE = (
    "先运行 vocal_segments.py --mode multi，再按根因处理：窗口问题换窗，素材问题换同版本源；"
    "Live 等检测能力限制且硬 FAIL=0 时，本地可直接使用真实证据与绑定当前窗口/hash 的 "
    "reviewer_kind=agent 工具辅助观察（结果仅为 OBSERVED，不是真人批准）；"
    "发布模式仍只接受 human，代理不得代签 human。")


def _reject_json_constant(value):
    raise ValueError(f"JSON 不能包含非有限数值 {value}")


def _reject_duplicate_keys(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError("JSON 不能包含重复字段")
        data[key] = value
    return data


def _load_json(path):
    """按标准 JSON 读取，拒绝 Python 默认容忍的 NaN/Infinity 和重复字段。"""
    return json.loads(
        Path(path).read_text(encoding="utf-8"),
        parse_constant=_reject_json_constant,
        object_pairs_hook=_reject_duplicate_keys,
    )


def _finite_number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _aware_datetime(value):
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None and parsed.utcoffset() is not None else None


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
            "主唱检测证据不足（showcase 邻域几乎无活动；满编曲可能漏报）"
            "→ 先自动重跑 multi 多证据分析")
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
            f"仅有 {evidence_level} 区间，不能证明是目标歌手而非乐器/观众；"
            "先自动重跑 multi 多证据分析"]
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
    data = _load_json(path)
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
        approvals = _load_json(path)
    if isinstance(approvals, dict) and "approvals" in approvals:
        approvals = approvals["approvals"]
    return approvals if isinstance(approvals, dict) else {}


def _analysis_fingerprint(analysis):
    """把实际用于判定的分析对象绑定进用户复核批准，防止重跑检测后沿用旧记录。"""
    canonical = json.dumps(
        analysis, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        default=str, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_approval(
        approvals, key, clip, expected_window=None, expected_analysis=None,
        *, require_human_review=False):
    item = approvals.get(key) or approvals.get(clip)
    if item is None:
        return None, None
    if not isinstance(item, dict):
        return None, "复核项必须是对象"
    reviewer_kind = item.get("reviewer_kind")
    if reviewer_kind not in {"agent", "human"}:
        return None, "复核项 reviewer_kind 必须明确为 agent 或 human"
    expected_status = "observed" if reviewer_kind == "agent" else "approved"
    if item.get("status") != expected_status:
        return None, (
            f"复核项 reviewer_kind={reviewer_kind} 时 status 必须为 {expected_status}"
        )
    if require_human_review and reviewer_kind != "human":
        return None, "发布模式要求 reviewer_kind=human；agent observation 不能冒充真人批准"
    reviewer = item.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        return None, "复核项 reviewer 必须是非空复核者标识"
    if _aware_datetime(item.get("reviewed_at")) is None:
        return None, "复核项 reviewed_at 必须是带时区的 ISO-8601 时间"
    reason = str(item.get("reason", "")).strip()
    evidence = item.get("evidence", [])
    if isinstance(evidence, str):
        evidence = [evidence]
    evidence = [str(x).strip() for x in evidence if str(x).strip()]
    if not reason or not evidence:
        return None, "复核项缺 reason 或 evidence"
    if str(item.get("clip", "")).strip() != str(clip):
        return None, f"复核项 clip 与当前不一致（应为 {clip}）"

    # 复核记录必须绑定具体剪辑窗口，防止改了 ch_off/show 后沿用旧记录误放行。
    bound = item.get("window", item)
    if not isinstance(bound, dict):
        return None, "复核项 window 必须是对象"
    if expected_window is not None:
        for name in ("narr_end_src", "show_start_src", "show_end_src"):
            if name not in bound:
                return None, f"复核项缺 window.{name}，无法确认是否对应当前剪辑"
            approved_value = _finite_number(bound[name])
            expected_value = _finite_number(expected_window.get(name))
            if approved_value is None:
                return None, f"复核项 window.{name} 必须是有限数值"
            if expected_value is None:
                return None, f"当前 window.{name} 必须是有限数值"
            delta = abs(approved_value - expected_value)
            if delta > APPROVAL_TIME_TOL:
                return None, (f"复核项已过期：window.{name}={approved_value:.2f}，"
                              f"当前为 {expected_value:.2f}")
    if expected_analysis is not None:
        expected_hash = _analysis_fingerprint(expected_analysis)
        actual_hash = str(item.get("analysis_sha256", "")).strip().lower()
        if not actual_hash:
            return None, "复核项缺 analysis_sha256，无法确认是否对应当前检测结果"
        if actual_hash != expected_hash:
            return None, "复核项已过期：analysis_sha256 与当前检测结果不一致"
    return {
        "reason": reason,
        "evidence": evidence,
        "reviewer_kind": reviewer_kind,
    }, None


def _valid_approval(approvals, key, clip, expected_window=None, expected_analysis=None):
    """兼容布尔式调用；详细错误由 ``_validate_approval`` 返回。"""
    return _validate_approval(
        approvals, key, clip, expected_window, expected_analysis)[0]


def gate(blocks, vocals, consts=None, plan_path=None, clips_dir="clips",
         approvals=None, override_env="SHOWCASE_OVERRIDE", verbose=True,
         require_human_review=False):
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
    approvals: 显式复核 JSON 路径或 dict。每项必须绑定 clip、analysis_sha256、三个时间码，
               并有 reviewer_kind、reason、evidence。默认本地模式允许
               status=observed/reviewer_kind=agent 的工具辅助观察；发布模式只接受
               status=approved/reviewer_kind=human。
    REVIEW 可凭绑定时间窗的复核记录闭环；硬边界 FAIL 不可批准跳过。
    未获证明即 raise SystemExit。全局 SHOWCASE_OVERRIDE 不再跳过。

    用法（build 算完 blocks、建 master 之前）：
        import os, sys; sys.path.insert(0, str(ROOT.parents[2]))   # 让 tools 可 import
        from tools.video import showcase_align
        showcase_align.gate(blocks, ROOT/"probe"/"vocal_analysis.json",
                            consts=dict(POST=POST, DIG=DIG),
                            plan_path=ROOT/"build"/"showcase_plan.json")
    """
    if not isinstance(blocks, (list, tuple)) or not blocks:
        raise SystemExit("✗ 展示段闸门拒绝空 blocks：没有歌曲不能视为通过。")
    vmap = vocals if isinstance(vocals, dict) else _load_analysis(vocals)
    if isinstance(vmap, dict) and "clips" in vmap:
        vmap = vmap["clips"]
    approval_map = _load_approvals(approvals)
    gate_mode = (consts or {}).get("mode") if isinstance(consts, dict) else None
    songs, results = [], []
    counts = {
        "OK": 0, "FAIL": 0, "REVIEW": 0,
        "OBSERVED": 0, "APPROVED": 0, "MISS": 0,
    }
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
                            [f"vocal_analysis.json 缺 clip『{clip}』→ 先自动跑 "
                             "vocal_segments.py --mode multi"], None))
            counts["MISS"] += 1
            continue
        v = verify_song(analysis, mode=b.get("mode", gate_mode), **s)
        status, reasons = v["status"], list(v["reasons"])
        approval, approval_error = _validate_approval(
            approval_map, s.get("key"), clip, expected_window=s,
            expected_analysis=analysis,
            require_human_review=require_human_review)
        if status == "REVIEW" and approval:
            if approval["reviewer_kind"] == "human":
                status = "APPROVED"
                reasons.append("真人逐曲复核批准：" + approval["reason"])
            else:
                status = "OBSERVED"
                reasons.append("代理工具辅助观察（仅本地，不是发布级真人批准）：" + approval["reason"])
            reasons.append("证据：" + ", ".join(approval["evidence"]))
        elif status == "FAIL" and approval:
            reasons.append("逐曲复核记录不能覆盖硬边界 FAIL；请修切点或写入校正后的主唱/安全边界分析")
        elif status in {"FAIL", "REVIEW"} and approval_error:
            reasons.append("逐曲复核记录未生效：" + approval_error)
        results.append((v["key"] or clip, status, reasons, v["metrics"]))
        counts[status] += 1

    if plan_path is not None:
        dump_plan(songs, plan_path, consts)

    if verbose:
        print("展示段对齐闸门（showcase_align.gate）")
        for name, status, reasons, metrics in results:
            mark = {
                "OK": "✓", "OBSERVED": "✓", "APPROVED": "✓",
                "FAIL": "✗", "REVIEW": "⚠", "MISS": "?",
            }.get(status, "?")
            print(f"  [{mark} {status}] {name}")
            for r in reasons:
                print(f"        - {r}")
        print("  → " + " ".join(
            f"{k}={counts[k]}"
            for k in ("FAIL", "REVIEW", "MISS", "OBSERVED", "APPROVED", "OK")))

    import os
    if os.environ.get(override_env) and verbose:
        print(f"  ⚠ {override_env} 已废弃：全局跳过会掩盖其他歌曲问题。{AUTO_RECOVERY_GUIDANCE}")
    n_block = counts["FAIL"] + counts["REVIEW"] + counts["MISS"]
    if n_block:
        raise SystemExit(
            f"✗ 展示段闸门仍有 {n_block} 首未获证明。{AUTO_RECOVERY_GUIDANCE}")
    return results


def _mp3_hint(clip, show_start_src, clips_dir):
    src = f"{clips_dir}/{clip}.mp4" if clips_dir else f"clips/{clip}.mp4"
    ss = max(0.0, show_start_src - 2.0)
    return (f"ffmpeg -ss {ss:.2f} -i {src} -t 26 -vn "
            f"-af loudnorm out_{clip}.mp3 -y   # 导出 26s 诊断片段；不得据此代签用户批准")


def cmd_check(args):
    vocals = _load_analysis(args.vocals)
    approvals = _load_approvals(args.approvals)
    plan = _load_json(args.plan)
    songs = plan["songs"] if isinstance(plan, dict) else plan
    if not isinstance(songs, list) or not songs:
        print("✗ 展示段闸门拒绝空 songs：没有歌曲不能视为通过。", file=sys.stderr)
        return 2
    plan_mode = (plan.get("consts", {}).get("mode")
                 if isinstance(plan, dict) else None)

    rows = []
    counts = {
        "OK": 0, "FAIL": 0, "REVIEW": 0,
        "OBSERVED": 0, "APPROVED": 0, "MISS": 0,
    }
    for s in songs:
        clip = s.get("clip") or s.get("key")
        analysis = vocals.get(clip)
        if analysis is None:
            rows.append((s.get("key") or clip, "MISS",
                         [f"vocal_analysis.json 里找不到 clip『{clip}』的人声数据 "
                          "→ 先自动跑 vocal_segments.py --mode multi"]))
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
            expected_analysis=analysis,
            require_human_review=getattr(args, "require_human_review", False))
        if status == "REVIEW" and approval:
            if approval["reviewer_kind"] == "human":
                status = "APPROVED"
                reasons.append("真人逐曲复核批准：" + approval["reason"])
            else:
                status = "OBSERVED"
                reasons.append("代理工具辅助观察（仅本地，不是发布级真人批准）：" + approval["reason"])
            reasons.append("证据：" + ", ".join(approval["evidence"]))
        elif status == "FAIL" and approval:
            reasons.append("逐曲复核记录不能覆盖硬边界 FAIL；请修切点或写入校正后的主唱/安全边界分析")
        elif status in {"FAIL", "REVIEW"} and approval_error:
            reasons.append("逐曲复核记录未生效：" + approval_error)
        rows.append((v["key"] or clip, status, reasons, v["metrics"], clip))
        counts[status] += 1

    print("展示段对齐校验（showcase_align）")
    print("=" * 64)
    for row in rows:
        name, status = row[0], row[1]
        mark = {
            "OK": "✓", "OBSERVED": "✓", "APPROVED": "✓",
            "FAIL": "✗", "REVIEW": "⚠", "MISS": "?",
        }.get(status, "?")
        print(f"[{mark} {status}] {name}")
        for r in row[2]:
            print(f"      - {r}")
        if status == "REVIEW" and len(row) >= 5:
            print(f"      $ {_mp3_hint(row[4], row[3]['show_start_src'], args.clips)}")
    print("=" * 64)
    print("  ".join(
        f"{k}={counts[k]}"
        for k in ("FAIL", "REVIEW", "MISS", "OBSERVED", "APPROVED", "OK")))
    n_block = counts["FAIL"] + counts["REVIEW"] + counts["MISS"]
    if n_block:
        print(f"✗ 闸门未过：{AUTO_RECOVERY_GUIDANCE}")
        return 1
    print("✓ 闸门通过。")
    return 0


def _find_safe_end(segs, show_start, min_show, through=None):
    """完整核心段与初筛预留量之后找出点；不因乐段较长缩回早期气口。"""
    target = max(show_start + min_show, through if through is not None else show_start)
    if not segs:
        return target, False, "没有 word/咬字边界证据，不能自动规划出点"
    candidates = [(idx, e) for idx, (_, e) in enumerate(segs) if e >= target]
    if not candidates:
        fallback = max(target, segs[-1][1] + PLAN_END_PAD)
        return fallback, False, "最短展示后没有可用人声段终点"

    for idx, end in candidates:
        cut = end + PLAN_END_PAD
        next_onset = next((s for s, _ in segs[idx + 1:] if s > end), None)
        if next_onset is not None and next_onset - cut < END_LOOKAHEAD:
            continue  # 句内气口：吞并下一小句后继续找
        return cut, True, "尾音释放后且前向保护窗内无新 onset"

    cut = segs[-1][1] + PLAN_END_PAD
    return cut, False, "未找到带前向保护窗的出点，须核对后续源音频"


def cmd_approval_template(args):
    """从已落盘 plan 生成用户复核批准骨架；默认拒绝覆盖已有记录。"""
    plan_path = Path(args.plan)
    plan = _load_json(plan_path)
    songs = plan["songs"] if isinstance(plan, dict) else plan
    if not isinstance(songs, list) or not songs:
        print("拒绝为空 plan 生成批准模板：songs 必须是非空数组", file=sys.stderr)
        return 2
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
            "reviewer_kind": None,
            "reviewer": "",
            "reviewed_at": None,
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
            "本模板仅接受用户已完成逐曲复核后的记录；代理或脚本不得填写、"
            "不得把 pending 改为 status=approved，不得代签。用户须逐曲试听并核对主唱身份、"
            "观众声和完整乐句，确认后把 reviewer_kind 填为 human，并填写 reviewer、"
            "带时区的 reviewed_at、具体 reason 与 evidence。"
            "任一时间码或分析内容变化都会让批准失效。"),
        "approvals": approvals,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成 {out}（全部为 pending；仅供用户已完成复核后填写，代理不得代签）")
    return 0


def cmd_plan(args):
    through = getattr(args, "through", None)
    for name, value in (("min-show", args.min_show), ("post", args.post),
                        ("dig", args.dig), ("through", through), ("near", args.near)):
        if value is None and name in {"through", "near"}:
            continue
        number = _finite_number(value)
        if number is None or number < 0 or (name == "min-show" and number == 0):
            print(f"--{name} 必须是有效的非负秒数（min-show 须大于 0）", file=sys.stderr)
            return 2
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

    # 先收完旁白、恢复 full volume，再进入目标首字；源首不足预滚时由 build 调整旁白位置。
    show_start = round(max(0.0, onset - PLAN_ENTRY_PAD), 2)
    narr_end_src = round(max(0.0, show_start - narr_end_offset), 2)

    # 选结尾：最短展示之后只向后找；短气口后若仍有 onset，吞并下一小句。
    show_end_raw, auto_safe, end_note = _find_safe_end(
        boundary_segs, show_start, args.min_show, through=through)
    show_end = round(show_end_raw, 2)
    show = round(show_end - show_start, 2)

    # ch_off 即 show_start（full_build 语义）；mseek 由 build 自行算
    print(f"clip={args.clip}  候选副歌段 [{cand[0]:.1f},{cand[1]:.1f}] ({cand[1]-cand[0]:.1f}s)")
    print(f"  人声入点 onset = {onset:.2f}s  (full volume 从首字前开始)")
    print(f"  → 建议 ch_off (show_start_src) = {show_start}")
    print(f"  → 建议 show = {show}   (show_end_src = {show_end})")
    print(f"  → narr_end_src = {narr_end_src}   (POST+DIG={narr_end_offset})")
    print(f"  → 出点搜索：{'自动候选' if auto_safe else '需 REVIEW'}；{end_note}")
    print("  → 仍须核对完整核心段、源前后余量和实际尾音；候选时长不是成片上限")
    print("  自检：")
    v = verify_song(raw_analysis, narr_end_src=narr_end_src,
                    show_start_src=show_start, show_end_src=show_end, clip=args.clip)
    print(f"    [{v['status']}] " + "; ".join(v["reasons"]))
    if not auto_safe or v["status"] != "OK":
        print(f"  ✗ 未找到能通过边界自检的自动切点。{AUTO_RECOVERY_GUIDANCE}", file=sys.stderr)
        return 1
    print(f"  ✓ 自动验证 OK，可写入 build：ch_off={show_start}, show={show}")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="展示段对齐机械闸门；未过时先 multi 分析，再按根因修复或记录真实观察")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser(
        "check", help="按 showcase_plan.json 校验全部歌曲（未过先自动修复，exit 1）")
    c.add_argument("--plan", required=True, help="showcase_plan.json 路径")
    c.add_argument("--vocals", required=True, help="vocal_analysis.json 路径")
    c.add_argument("--clips", default="clips", help="clips 目录（仅用于 REVIEW 时拼诊断 mp3 命令）")
    c.add_argument(
        "--approvals",
        help=("显式传入逐曲复核 JSON；本地可含 reviewer_kind=agent 的工具辅助观察，"
              "不自动读取同目录文件，代理不得代签 human"))
    c.add_argument(
        "--require-human-review",
        action="store_true",
        help="发布级严格模式：REVIEW 只接受 reviewer_kind=human 的真人记录",
    )
    c.set_defaults(func=cmd_check)

    p = sub.add_parser("plan", help="反推某首的 ch_off / show 建议值")
    p.add_argument("--vocals", required=True)
    p.add_argument("--clip", required=True, help="vocal_analysis.json 里的 clip key，如 vert_p4_wait")
    p.add_argument("--voice-dur", type=float, help="历史兼容参数，不参与源窗口建议；WAV 时长由 build 绑定")
    p.add_argument("--lead", type=float, default=0.35, help="历史兼容参数，不参与源窗口建议")
    p.add_argument("--post", type=float, default=0.25)
    p.add_argument("--dig", type=float, default=1.45)
    p.add_argument("--near", type=float, default=None, help="副歌大概在源里第几秒(可选，帮选段)")
    p.add_argument("--min-show", type=float, default=MIN_SHOW,
                   help="初筛展示预留秒数（默认 60，可按完整段落调整；非硬下限/上限）")
    p.add_argument("--through", type=float,
                   help="必须完整保留到的核心段源时间；出点在此之后寻找，不限制延长")
    p.set_defaults(func=cmd_plan)

    approval_help = "仅供已完成逐曲复核的用户生成批准骨架；代理不得代签"
    a = sub.add_parser("approval-template", help=approval_help, description=approval_help)
    a.add_argument("--plan", required=True, help="showcase_plan.json 路径")
    a.add_argument("--vocals", required=True, help="与 plan 对应的 vocal_analysis.json")
    a.add_argument("--out", help="输出路径；默认写到 plan 同目录 showcase_approvals.json")
    a.add_argument("--force", action="store_true", help="覆盖已有批准文件")
    a.set_defaults(func=cmd_approval_template)

    args = ap.parse_args()
    try:
        exit_code = args.func(args)
    except (json.JSONDecodeError, KeyError, OSError, TypeError, ValueError):
        print("SHOWCASE INPUT ERROR: 输入文件不是可用的严格 JSON/结构化数据", file=sys.stderr)
        exit_code = 2
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
