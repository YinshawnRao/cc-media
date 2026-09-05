#!/usr/bin/env python3
"""固定简短结尾 CTA 的文字来源；只有用户明确要求才可改写或省略。

project-manifest.json 的 editorial.cta 为 fixed（默认）、custom 或 omit。
custom/omit 必须记录 editorial.cta_user_request 中的用户原话。
历史长版仅供已有项目通过 cta_text_version=legacy-v1 显式固定后复现。
修改单期 CTA 时更新该期旁白、音轨和 QA，不修改这里的默认文本。

用法（每期 narrate 脚本）：
    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools" / "video"))
    from outro_cta import FIXED_OUTRO_CTA
"""

FIXED_OUTRO_CTA = "喜欢这期内容，记得点赞、收藏、关注我。"
DEFAULT_CTA_TEXT_VERSION = "short-v1"
LEGACY_FIXED_OUTRO_CTA = (
    "你最想为哪一首投票？评论区告诉我。"
    "记得点赞、收藏、关注我，下一期，可能就盘到你单曲循环过的那一首。"
)
FIXED_CTA_TEXTS = {
    DEFAULT_CTA_TEXT_VERSION: FIXED_OUTRO_CTA,
    "legacy-v1": LEGACY_FIXED_OUTRO_CTA,
}


def fixed_cta_text(version: str = DEFAULT_CTA_TEXT_VERSION) -> str:
    if not isinstance(version, str) or version not in FIXED_CTA_TEXTS:
        raise ValueError("editorial.cta_text_version must be short-v1 or legacy-v1")
    return FIXED_CTA_TEXTS[version]


if __name__ == "__main__":
    print(FIXED_OUTRO_CTA)
