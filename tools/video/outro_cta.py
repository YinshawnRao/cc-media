#!/usr/bin/env python3
"""固定结尾引流 CTA —— 单一来源（硬约束，优先级高于 brief / 任务提示词）。

见 CONVENTIONS.md「固定结尾配音」。规则：
- 这句逐字固定，永远是成片**最后一句**旁白，排在每期「作品自身 outro」（内容总结 + 升华）之后。
- brief / 提示词**不得覆盖**它；唯一改法是改本文件 + CONVENTIONS。
- 不提供项目级可换槽；改变文字必须作为一次全局规范变更，并同步文档与测试。

用法（每期 narrate 脚本）：
    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
    from outro_cta import FIXED_OUTRO_CTA
"""

FIXED_OUTRO_CTA = (
    "你最想为哪一首投票？评论区告诉我。"
    "记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。"
)


if __name__ == "__main__":
    print(FIXED_OUTRO_CTA)
