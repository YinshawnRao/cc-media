export const meta = {
  name: 'tyl-sourcing-research',
  description: '谭咏麟被低估5首 — 每首并行研究 YouTube+B站 候选视觉源与音频源',
  phases: [{ title: 'Research', detail: '5首并行选源研究' }],
}

const ROOT = '/Users/yinshawnrao/explorer/cc-media'

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['song','album','year','candidates','recommended_visual','recommended_audio','chorus_hint','risks'],
  properties: {
    song: { type: 'string' },
    album: { type: 'string' },
    year: { type: 'string' },
    language: { type: 'string' },
    songwriter: { type: 'string' },
    metadata_notes: { type: 'string' },
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['platform','ref','title','content_type','burned_lyrics','face_quality','notes'],
        properties: {
          platform: { type: 'string', description: 'YouTube 或 Bilibili' },
          ref: { type: 'string', description: 'B站 bvid 或 YouTube video id / 完整 URL' },
          title: { type: 'string' },
          uploader: { type: 'string' },
          duration: { type: 'string' },
          resolution: { type: 'string', description: '如 1080p / 720p / 480p；不确定写 unknown' },
          vcodec: { type: 'string' },
          audio_channels: { type: 'string', description: 'stereo / mono / unknown' },
          content_type: { type: 'string', description: '官方MV / 演唱会Live / 综艺Live / Topic音频 / 歌词视频 / 翻唱 / 静态图音轨' },
          burned_lyrics: { type: 'string', description: '无 / 底部 / 中部 / 双语条；不确定写 unknown' },
          watermark: { type: 'string' },
          face_quality: { type: 'string', description: '是否有谭咏麟本人连续特写；多机位切镜密集要说明' },
          verified_by_ytdlp: { type: 'boolean' },
          notes: { type: 'string' },
        },
      },
    },
    recommended_visual: {
      type: 'object', additionalProperties: false, required: ['platform','ref','why'],
      properties: { platform: { type: 'string' }, ref: { type: 'string' }, why: { type: 'string' } },
    },
    recommended_audio: {
      type: 'object', additionalProperties: false, required: ['platform','ref','mode','why'],
      properties: { platform: { type: 'string' }, ref: { type: 'string' }, mode: { type: 'string', description: 'synced 或 decoupled' }, why: { type: 'string' } },
    },
    chorus_hint: { type: 'string', description: '该曲副歌/代表段大致位置或结构提示' },
    risks: { type: 'string' },
  },
}

const SONGS = [
  { key: 'p5_hhdsy', no: '05', name: '《黄昏的声音》', album: '《再见吧!?浪漫》(亦作《留住明天》电视剧主题曲)', year: '约1987', lang: '粤语',
    facts: '谭咏麟收录于《再见吧!?浪漫》(1987)；同专辑Dont Say Goodbye、《知心当玩偶》、《再见吧！浪漫》更醒目，本曲被埋。旋律氛围黄昏感、耐听。' },
  { key: 'p4_cknzhc', no: '04', name: '《此刻你在何处》', album: '《爱情陷阱》', year: '1985', lang: '粤语',
    facts: '收录于谭咏麟巅峰专辑《爱情陷阱》(1985)；被同名主打《爱情陷阱》《幸运星》《情是永远着迷》盖住。电影情歌、完整。' },
  { key: 'p3_ybxn', no: '03', name: '《永不想你》', album: '《第一滴泪》', year: '1986', lang: '粤语',
    facts: '收录于《第一滴泪》(1986)；林敏骢包办曲词。同专辑《无言感激》是大热。中后期成熟情歌质感。' },
  { key: 'p2_qsdxx', no: '02', name: '《墙上的肖像》', album: '《墙上的肖像》(请核实确切年份)', year: '约1989', lang: '粤语',
    facts: '专辑《墙上的肖像》同名作；同碟《痴心的废墟》《曾经》《无边的思忆》更被记住。带阴郁/艺术/都市感的暗色情歌。请核实专辑年份与是否真有此同名曲。' },
  { key: 'p1_hsndd', no: '01', name: '《还是你懂得爱我》', album: '《笑看人生》', year: '1991', lang: '粤语',
    facts: '收录于《笑看人生》(1991)；乐评称其为唱片慢歌首选佳作(与《我永远都爱你》并列最感人)。成熟情歌的厚度，越听越有味。' },
]

phase('Research')

function buildPrompt(s) {
  return [
    '你是资深华语老歌选源研究员，为一期竖屏短视频盘点「谭咏麟最被低估的5首歌」研究其中一首的素材源。',
    '',
    '## 目标曲',
    '- 歌名：' + s.name,
    '- 专辑：' + s.album + '（' + s.year + '，' + s.lang + '）',
    '- 背景：' + s.facts,
    '',
    '## 你的任务',
    '为这首歌找到：(A) 视觉源——含谭咏麟本人画面的官方MV或演唱会/综艺Live；(B) 音频源——能用于展示段的干净录音(优先立体声)。两个平台都要搜：YouTube + B站(哔哩哔哩)并行。',
    '',
    '## 工具(Bash 用绝对路径)',
    '- 项目根：' + ROOT,
    '- B站搜索(已封装WBI签名,读cookie)：' + ROOT + '/tools/tts/venv/bin/python ' + ROOT + '/tools/video/bili_search.py "关键词" 8 — 输出 bvid|时长|up主|标题。多换关键词(歌名、谭咏麟+歌名、谭咏麟+专辑名、谭咏麟+演唱会、谭咏麟+Live)。',
    '- YouTube/通识：用 WebSearch(搜 youtube 谭咏麟 歌名 live/MV/演唱会；核实专辑年份、词曲作者、是否有官方MV、谭咏麟哪几场演唱会唱过它)。',
    '- 规格核实(只读元数据,绝不下载整片)：对最看好的最多3个候选跑 yt-dlp --skip-download --print "%(id)s|%(duration)s|%(resolution)s|%(vcodec)s" --cookies ' + ROOT + '/sandbox/www.bilibili.com_cookies.txt "https://www.bilibili.com/video/BVID"(YouTube换cookie为www.youtube.com_cookies.txt、URL为 https://www.youtube.com/watch?v=ID)。能跑通就 verified_by_ytdlp=true 并回填分辨率/编码。不要加 download-sections、不要真下载。失败就跳过靠搜索判断。',
    '- 并发提示：有5个agent同时跑，最多跑3次 yt-dlp --print，避免风控。',
    '',
    '## 选源判据(按优先级)',
    '1. 干净度：无烧死歌词字幕/台标/平台水印/UP主水印/双语条。MV中部歌词比底部难裁,优先无歌词版。',
    '2. 本人画面：要有谭咏麟本人连续特写(非演员替身、非纯静态专辑图、非Topic静图、非翻唱)。多机位综艺常每2-4秒切镜难锁长特写,要标注。',
    '3. 清晰度：分辨率+码率越高越好。',
    '4. 音频：立体声>单声道；B站4K流常配单声道,遇到4K单声道vs1080P立体声优先立体声。',
    '5. 可用连续段：至少一段连续可用副歌(≥25s不被切镜打断)。',
    '6. 版本质量：官方MV>官方Live/直拍>综艺Live>翻唱/二创。',
    '',
    '## 关键现实(老粤语deep cut)',
    '这些都是冷门专辑曲。很可能 YouTube 只有 Topic 音频/歌词视频(无人物画面),而人物画面只在 B站(演唱会修复版、综艺现场)。也可能根本没有任何现场画面——若如此如实说明,并标出最接近替代(如同期演唱会其他曲目的谭咏麟特写可作蒙太奇救场,注明解耦救场)。',
    '音频策略：若视觉源自带干净立体声且有连续副歌→synced(同源)。若视觉源是多机位/音频差/需蒙太奇→decoupled：另找干净棚版录音(YouTube Topic 或 B站无损)当音频,画面单独剪。两种都给推荐。',
    '',
    '## 输出',
    '通过 StructuredOutput 返回。candidates 列所有值得记录的候选(每平台至少2-3个,含判断为不可用的也列上并在notes说明原因)。recommended_visual/recommended_audio 给明确推荐与理由。chorus_hint 给副歌大致位置。ref 用真实 B站bvid 或 YouTube id。',
  ].join('\n')
}

const results = await parallel(SONGS.map(s => () =>
  agent(buildPrompt(s), { label: 'src:' + s.no + '-' + s.key, phase: 'Research', schema: SCHEMA })
    .then(r => ({ key: s.key, no: s.no, name: s.name, research: r }))
    .catch(e => ({ key: s.key, no: s.no, name: s.name, error: String(e) }))))

return { results }
