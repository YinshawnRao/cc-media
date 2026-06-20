#!/usr/bin/env node
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import sharp from "../vendor/hyperframes-local/node_modules/sharp/lib/index.js";

const ROOT = path.resolve(import.meta.dirname, "..");
const A = path.join(ROOT, "audio");
const C = path.join(ROOT, "clips");
const BUILD = path.join(ROOT, "build");
const OVERLAY_DIR = path.join(BUILD, "overlays");
const RENDERS = path.join(ROOT, "renders");

const SHOW = 31.0;
const LEAD = 0.35;
const DIG = 1.5;
const INTRO_VOICE_START = 0.45;
const INTRO_GAP = 1.15;
const CTA_GAP = 1.0;
const OUTRO_TAIL = 1.8;
const INTRO_CLIP = "vert_p2_sleep";
const OUTRO_CLIP = "vert_p1_right";

const meta = JSON.parse(readFileSync(path.join(ROOT, "narration.json"), "utf8"));
const q = (n) => Math.round(Number(n) * 1000) / 1000;
const xml = (s) => String(s)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

const items = [
  {
    key: "p5_laibuji", clip: "vert_p5_laibuji", no: "05",
    name: "《来不及》", plain: "来不及",
    tag: "慢半拍才意识到失去",
    note: "被《那么骄傲》专辑光芒盖住的耐听遗珠",
  },
  {
    key: "p4_bitian", clip: "vert_p4_bitian", no: "04",
    name: "《比天空还远的季节》", plain: "比天空还远的季节",
    tag: "安静、内向、远远的孤独",
    note: "《独立日》里更适合夜里重听的一首",
  },
  {
    key: "p3_duian", clip: "vert_p3_duian", no: "03",
    name: "《对岸》", plain: "对岸",
    tag: "看得见，却很难抵达",
    note: "透明声线唱有距离的情绪，后劲更深",
  },
  {
    key: "p2_sleep", clip: "vert_p2_sleep", no: "02",
    name: "《睡不着的海》", plain: "睡不着的海",
    tag: "海、夜与不安",
    note: "早期被标题曲压住的氛围宝藏",
  },
  {
    key: "p1_right", clip: "vert_p1_right", no: "01",
    name: "《右手戒指》", plain: "右手戒指",
    tag: "明亮的自我解放",
    note: "《独立日》第二波概念主打，却很少被路人提起",
  },
].map((item) => ({ ...item, voiceDur: meta[item.key].dur }));

const introEnd = q(INTRO_VOICE_START + meta.intro.dur + INTRO_GAP);
let t = introEnd;
const blocks = items.map((item) => {
  const narrStart = q(t + LEAD);
  const narrEnd = q(narrStart + item.voiceDur);
  const fullStart = q(narrEnd + 0.25 + DIG);
  const end = q(fullStart + SHOW);
  const block = { ...item, start: q(t), fullStart, end };
  t = end;
  return block;
});
const outroStart = q(t);
const ctaStartLocal = q(LEAD + meta.outro.dur + CTA_GAP);
const ctaAbs = q(outroStart + ctaStartLocal);
const total = q(outroStart + ctaStartLocal + meta.cta.dur + OUTRO_TAIL);

function textBlock(lines, x, y, opts = {}) {
  const {
    size = 40,
    fill = "#f4efe4",
    weight = 800,
    family = "STHeiti, Songti SC, sans-serif",
    line = Math.round(size * 1.25),
    anchor = "start",
    opacity = 1,
  } = opts;
  return `<text x="${x}" y="${y}" text-anchor="${anchor}" font-family="${family}" font-size="${size}" font-weight="${weight}" fill="${fill}" opacity="${opacity}">${
    lines.map((value, index) => `<tspan x="${x}" dy="${index === 0 ? 0 : line}">${xml(value)}</tspan>`).join("")
  }</text>`;
}

function svg(parts) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920">
  <rect width="1080" height="1920" fill="none"/>
  ${parts.join("\n")}
</svg>`;
}

async function writeOverlay(name, parts) {
  const file = path.join(OVERLAY_DIR, `${name}.png`);
  await sharp(Buffer.from(svg(parts))).png().toFile(file);
  return file;
}

function labelOverlay(b) {
  const accent = b.no === "01" ? "#ff9488" : "#d8af5f";
  return [
    `<rect x="58" y="1378" width="964" height="364" rx="10" fill="#07090b" opacity="0.82"/>`,
    `<rect x="58" y="1378" width="9" height="364" rx="4" fill="${accent}"/>`,
    textBlock([`第 ${b.no} 名`], 92, 1434, { size: 32, fill: accent, weight: 900 }),
    textBlock([b.name], 92, 1526, { size: b.name.length > 8 ? 60 : 74, fill: "#f4efe4", weight: 900, line: 76 }),
    textBlock([b.tag], 92, 1618, { size: 40, fill: "#efd493", weight: 900 }),
    textBlock([b.note], 92, 1684, { size: 29, fill: "#c9d4d1", weight: 650 }),
  ];
}

function miniOverlay(b) {
  const accent = b.no === "01" ? "#ff9488" : "#d8af5f";
  return [
    `<rect x="56" y="82" width="470" height="82" rx="10" fill="#07090b" opacity="0.76" stroke="${accent}" stroke-opacity="0.65"/>`,
    textBlock([`${b.no}  ${b.plain}`], 82, 136, { size: 38, fill: "#f4efe4", weight: 900 }),
  ];
}

mkdirSync(OVERLAY_DIR, { recursive: true });
mkdirSync(RENDERS, { recursive: true });

const overlays = [];
overlays.push({
  start: 0.35,
  end: introEnd - 0.35,
  file: await writeOverlay("cover", [
    `<rect x="0" y="0" width="1080" height="1920" fill="#07090b" opacity="0.36"/>`,
    `<rect x="72" y="135" width="64" height="5" rx="3" fill="#d8af5f"/>`,
    textBlock(["被大热盖住的透明声线"], 154, 152, { size: 30, fill: "#d8af5f", weight: 900 }),
    textBlock(["金海心最被低估的", "5首歌"], 72, 330, { size: 104, fill: "#f4efe4", weight: 900, line: 126, family: "Songti SC, STHeiti, serif" }),
    textBlock(["不先公布完整名单。", "从第五名开始，听那些被专辑光芒压住、", "却越听越有后劲的歌。"], 72, 680, { size: 38, fill: "#d8e0dc", weight: 750, line: 58 }),
    `<rect x="68" y="1570" width="944" height="86" rx="10" fill="#151b1f" opacity="0.78" stroke="#d8af5f" stroke-opacity="0.54"/>`,
    textBlock(["专辑遗珠    透明感声线    夜里重听    被低估的明亮"], 540, 1624, { size: 30, fill: "#efd493", weight: 900, anchor: "middle" }),
  ]),
});

for (const [idx, b] of blocks.entries()) {
  overlays.push({
    start: b.start + 0.1,
    end: b.fullStart - 0.2,
    file: await writeOverlay(`full_${idx}`, labelOverlay(b)),
  });
  overlays.push({
    start: b.fullStart + 0.1,
    end: b.end - 0.3,
    file: await writeOverlay(`mini_${idx}`, miniOverlay(b)),
  });
}

overlays.push({
  start: outroStart + 0.2,
  end: total - 1.2,
  file: await writeOverlay("outro", [
    `<rect x="0" y="0" width="1080" height="1920" fill="#07090b" opacity="0.46"/>`,
    textBlock(["完整榜单"], 72, 250, { size: 36, fill: "#d8af5f", weight: 900 }),
    textBlock(["这些歌不一定最大声，", "却最能听见金海心声音里的光。"], 72, 355, { size: 56, fill: "#f4efe4", weight: 900, line: 72, family: "Songti SC, STHeiti, serif" }),
    `<rect x="72" y="585" width="936" height="500" rx="12" fill="#07090b" opacity="0.74" stroke="#d8af5f" stroke-opacity="0.35"/>`,
    textBlock(["01  右手戒指", "02  睡不着的海", "03  对岸", "04  比天空还远的季节", "05  来不及"], 116, 665, { size: 39, fill: "#f4efe4", weight: 900, line: 88 }),
    textBlock(["从第五到第一：来不及、比天空还远的季节、对岸、睡不着的海、右手戒指。"], 72, 1200, { size: 30, fill: "#d8e0dc", weight: 700 }),
  ]),
});

overlays.push({
  start: ctaAbs - 0.3,
  end: total - 0.35,
  file: await writeOverlay("cta", [
    `<rect x="58" y="1514" width="964" height="214" rx="18" fill="#11181c" opacity="0.90" stroke="#d8af5f" stroke-opacity="0.72"/>`,
    textBlock(["你最想为哪一首投票？"], 540, 1598, { size: 46, fill: "#f4efe4", weight: 900, anchor: "middle" }),
    textBlock(["点赞    收藏    关注"], 540, 1682, { size: 36, fill: "#efd493", weight: 900, anchor: "middle" }),
  ]),
});

const videoPlan = [
  [path.join(C, `${INTRO_CLIP}.mp4`), introEnd],
  [path.join(C, "vert_p5_laibuji.mp4"), q(blocks[0].end - blocks[0].start)],
  [path.join(C, "vert_p4_bitian.mp4"), q(blocks[1].end - blocks[1].start)],
  [path.join(C, "vert_p3_duian.mp4"), q(blocks[2].end - blocks[2].start)],
  [path.join(C, "vert_p2_sleep.mp4"), q(blocks[3].end - blocks[3].start)],
  [path.join(C, "vert_p1_right.mp4"), q(blocks[4].end - blocks[4].start)],
  [path.join(C, `${OUTRO_CLIP}.mp4`), q(total - outroStart)],
];

const args = ["-v", "error"];
for (const [src] of videoPlan) args.push("-i", src);
args.push("-i", path.join(ROOT, "master.wav"));
for (const overlay of overlays) args.push("-loop", "1", "-i", overlay.file);

const filters = [];
videoPlan.forEach(([, duration], idx) => {
  filters.push(`[${idx}:v]trim=0:${duration},setpts=PTS-STARTPTS,scale=1080:1920,setsar=1[v${idx}]`);
});
const concatInputs = videoPlan.map((_, idx) => `[v${idx}]`).join("");
filters.push(`${concatInputs}concat=n=${videoPlan.length}:v=1:a=0,format=yuv420p[base0]`);

let current = "base0";
const firstOverlayIndex = videoPlan.length + 1;
overlays.forEach((overlay, idx) => {
  const next = `ov${idx}`;
  const inputIndex = firstOverlayIndex + idx;
  filters.push(`[${current}][${inputIndex}:v]overlay=0:0:enable='between(t,${overlay.start},${overlay.end})'[${next}]`);
  current = next;
});

const out = path.join(RENDERS, "jinhaixin-underrated-top5.mp4");
args.push(
  "-filter_complex", filters.join(";"),
  "-map", `[${current}]`,
  "-map", `${videoPlan.length}:a`,
  "-c:v", "libx264",
  "-preset", "medium",
  "-crf", "18",
  "-r", "30",
  "-pix_fmt", "yuv420p",
  "-c:a", "aac",
  "-b:a", "192k",
  "-t", String(total),
  "-shortest",
  out,
  "-y",
);

const result = spawnSync("ffmpeg", args, { cwd: ROOT, stdio: "inherit" });
if (result.status !== 0) process.exit(result.status ?? 1);

writeFileSync(path.join(ROOT, "meta.json"), JSON.stringify({
  id: "main",
  name: "jinhaixin-underrated-top5",
  duration: total,
  renderer: "ffmpeg-overlay-fallback",
}, null, 2), "utf8");

console.log(`wrote ${path.relative(ROOT, out)}`);
console.log("duration:", total);
console.log("blocks:", blocks.map((b) => [b.no, b.plain, b.start, b.fullStart, b.end]));
