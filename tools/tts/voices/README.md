# 编号角色声音库

本目录保存每个正式角色的原创参考母带与实际试听样例。编号是长期接口：**永不重排、永不复用已废弃编号**。新增角色只追加新编号。

| 编号 | 正式名称 | 目录 | 定位 |
| --- | --- | --- | --- |
| CV001 | 元气萌妹 | `CV001-moe-spark/` | 明亮、活泼、甜系 |
| **CV002** | **治愈少女（默认）** | `CV002-soft-healer/` | 柔软、温暖、陪伴感 |
| CV003 | 傲娇吐槽姬 | `CV003-tsundere-comic/` | 清脆、机灵、吐槽感 |
| CV004 | 清冷学姐 | `CV004-cool-senpai/` | 清冷、克制、高级感 |
| CV005 | 慵懒猫系 | `CV005-sleepy-cat/` | 松弛、猫系、稍慢 |
| CV006 | 热血少年 | `CV006-hotblood-youth/` | 明亮、有冲劲、少年感 |
| CV007 | 神秘宿敌 | `CV007-mystic-rival/` | 中低音、神秘、戏剧感 |
| CV008 | 空灵精灵 | `CV008-airy-spirit/` | 空灵、中性、梦幻 |

每个角色目录固定包含：

```text
reference.wav                 # Qwen Base 克隆使用的原创参考母带
examples/ranking.wav          # 同一段中文盘点文案，统一试听响度
examples/mixed-language.wav   # 中英日混读人工检查样例
```

角色元数据、允许匹配的别名、参考母带 SHA 和样例路径统一写在 `registry.json`。不要只改目录名或 README；任何编号/别名变化必须同时通过 `tools/tts/tests/`。

打开 [`listen.html`](listen.html) 可一次试听 8 个角色和 8 个 Kokoro 基线。自动技术 QA 不能判断“萌不萌、耐不耐听”，新增/替换母带仍需人工试听确认。
