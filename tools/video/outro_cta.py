#!/usr/bin/env python3
"""默认结尾 CTA 的文字来源；用户可以在单期选择改写或省略。

project-manifest.json 的 editorial.cta 为 fixed（默认）、custom 或 omit。
修改单期 CTA 时更新该期旁白、音轨和 QA，不修改这里的默认文本。

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
