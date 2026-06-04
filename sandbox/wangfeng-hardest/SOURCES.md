# 汪峰最难的5首歌 — 成片归档与复现说明

**成片**：`renders/wangfeng-hardest.mp4`（竖屏 1080×1920，约 4:26，h264+aac）
**形式**：难度盘点，倒数 5→1（最难压轴）。摇滚暗黑 + 猩红/琥珀配色，**女声旁白 `zf_xiaoyi`**。
**封面**：汪峰 studded jacket 正脸特写 + 标题"最难的5首歌"+作品描述，**不剧透排名**（按 brief）。片尾口播+画面**完整难度榜 01–05**。
**用途**：本地测试，未发布。发布前需另行评估 YouTube / B站源素材授权。

## 揭晓顺序与素材来源（素材优先级：官方MV > 官方Live > 网友）

切片：`yt-dlp <URL> --cookies <ck> --download-sections "*<起>-<止>" -f "bv*[height<=1080]+ba/b"`，窗口 = [chorus_start−24s, +30s]≈54–56s（副歌落展示段 SHOW，build 再精切 clips_seg 保口型）。
竖屏：`tools/video/vfill.sh <in> clips/vert_<key>.mp4 <crop>`（letterbox 保原比例，crop=全宽横带裁烧字/角标）。

| # | 歌 | 来源 | 档位 | 切点(原片) | vfill crop | 备注 |
|---|----|------|------|-----------|-----------|------|
| 封面/intro/outro底 | — | B站 `BV1Rg41137BU` 2014鸟巢"峰暴来临"《光明》 | 官方Live | intro底 00:36–01:18(取t14后干净段)；封面取 yonggan源02:00帧 | 1920:890 | 红衣特写，与#1同场 |
| 05 | 一起摇摆 | B站 `BV1Ys4y1D7md` 2013存在巡演上海 4K60 remaster | 网友(无官方MV/官Live带角标) | 02:39–03:35 | 3840:1820:0:0 | 无角标，汪峰特写多 |
| 04 | 勇敢的心 | B站 `BV1oC4y1b7SC` 蓝光修复(QQ音乐) | 官方Live(无棚版MV) | 01:36–02:32 | **1920:760:0:120** | crop顶移裁掉右上QQ音乐角标+底歌词 |
| 03 | 存在 | B站 `BV11R4y1c7Ni` 2013存在Existence巡演 | 官方Live | 01:32–02:26(chorus 116s) | 1920:780:0:120 | ⚠见下「换源说明」 |
| 02 | 等待 | YT `3a2Tudvgnnc`《歌手2018》芒果TV官方 | 官方Live(综艺) | 03:14–04:10 | 1920:550:0:155 | 裁顶台标+底金典奖徽；band较薄 |
| 01 | 光明 | B站 `BV1Rg41137BU` 2014鸟巢"峰暴来临" | 官方Live | 02:44–03:40 | 1920:890:0:0 | 压轴，金色「公认天花板」；含鸟巢儿童合唱团名场面 |

### ⚠ 存在(#3) 换源说明（偏离"官方MV优先"，已征得"质量第一"）
风华秋实**官方MV**(YT `Ri89KOr1Z2I`)是**黑白叙事MV**：汪峰本人仅末段出镜约10s，其余全是工人/拳击手叙事画面 + 720p + 右上红星角标，**无法满足"连续≥25s 汪峰唱副歌"展示段硬规则**。故降级用 2013存在巡演现场(汪峰全程~85%在画面)。若坚持用官方MV可换回(`raw/cunzai.mp4` 重下 + crop 1280:600:0:0 + 右上红星需遮)。

## 复现步骤
1. 重下源切片：`bash build/download.sh`（存在另见 `raw/cunzai.mp4` 用 BV11R4y1c7Ni）。
2. 竖屏+delogo：`bash build/process_clips.sh`（勇敢/存在 crop 已含裁角标）；封面/introbed 见 build 历史命令。
3. 配音（女声 zf_xiaoyi）：`tools/tts/venv/bin/python build/narrate_segments.py` → `audio/*.wav`（已归档）。
4. 合成：`python3 build/full_build.py`（建 clips_seg + master.wav + index.html）。
5. 渲染（本机GPU随机崩 + 总长>240s/≥7video 必崩 → 切两段）：`bash build/render_parts.sh`
   - `WF_PART=A/B python3 build/full_build.py` 生成 partA/partB.html（各<240s、≤4 video）→ render --sdr -w1 重试 → concat → mux master.wav。

## QA 基线（成片已达标）
- 五首副歌 −15.9~−16.5dB（差<0.6dB）；无 >1s 整片静音；旁白段音乐 ducking 到低床。
- 画面无水印/网址/烧死歌词/角标/路径/meta 文案；倒数 05→01，#1 金色「公认天花板」；片尾完整榜单 01–05。
- 女声旁白：intro / 每首转场 / outro 全为 zf_xiaoyi。
