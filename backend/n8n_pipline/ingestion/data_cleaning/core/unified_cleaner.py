import re

class UnifiedCleaner:
    """
    提供文字清理功能：
      - 去除 emoji
      - 移除不必要的雜訊字元，但保留基本標點 (.,!?:;-'\"()[])
      - 統一多重空白
    """

    # 允許的字元：中文字、英文字母、數字，以及基本標點符號，包括 () [] {} 、。？！；：（）“”‘’
    ALLOWED_RE = re.compile(
        r"[^\w\u4e00-\u9fff\(\)\[\]\{\}\.\,\!\?\:\;\'\"\-\u3000-\u303F]+"
    )

    # 多重空白正則
    MULTISPACE_RE = re.compile(r"\s{2,}")

    def clean_text(self, text: str) -> str:
        """
        清理文字：
        1. 移除 emoji（透過 ALLOWED_RE）
        2. 將多重空白縮成單一空格
        3. 修剪首尾空白
        """
        # 1. 去掉不符合規則的雜訊字元（保留括號）
        cleaned = UnifiedCleaner.ALLOWED_RE.sub(" ", text)

        # 2. 縮成單一空白
        cleaned = UnifiedCleaner.MULTISPACE_RE.sub(" ", cleaned)

        # 3. 去掉首尾空白
        return cleaned.strip()
