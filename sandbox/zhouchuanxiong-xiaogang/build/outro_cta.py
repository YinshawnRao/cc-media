#!/usr/bin/env python3
"""固定结尾引流 CTA —— 单一来源（硬约束，优先级高于 brief / 任务提示词）。

见 CONVENTIONS.md「固定结尾配音」。规则：
- 这句逐字固定，永远是成片**最后一句**旁白，排在每期「作品自身 outro」（内容总结 + 升华）之后。
- brief / 提示词**不得覆盖**它；唯一改法是改本文件 + CONVENTIONS。
- 只有两个名词槽可按选题替换：vote_object / next_hook。骨架与「关注我」逐字不动。

用法（每期 narrate 脚本）：
    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
    from outro_cta import FIXED_OUTRO_CTA            # 默认款
    # 或按选题换槽：from outro_cta import outro_cta; outro_cta(vote_object="哪一位")
"""

DEFAULT_VOTE_OBJECT = "哪一首"          # 歌手 PK → "哪一位"；版本对比 → "哪个版本"
DEFAULT_NEXT_HOOK = "单曲循环过的那一首"  # 饭圈向可换 "你的本命"；纯怀旧期可换 "你的青春"


def outro_cta(vote_object: str = DEFAULT_VOTE_OBJECT, next_hook: str = DEFAULT_NEXT_HOOK) -> str:
    """返回固定结尾 CTA 文本。只换 vote_object / next_hook 两个名词，其余逐字固定。"""
    return (
        f"你最想为{vote_object}投票？评论区告诉我。"
        f"记得点赞、收藏、关注我，下一期，可能就盘到你{next_hook}。"
    )


# 默认款（绝大多数歌曲盘点直接用这个）
FIXED_OUTRO_CTA = outro_cta()


if __name__ == "__main__":
    print(FIXED_OUTRO_CTA)
