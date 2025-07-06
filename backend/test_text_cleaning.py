"""
文本清理功能測試腳本
專門測試表情符號和特殊字元的處理
"""

import logging
import sys
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

from vector_pipeline.utils.text_cleaner import TextCleaner

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_text_cleaning():
    """測試文本清理功能"""
    cleaner = TextCleaner()
    
    # 測試案例
    test_cases = [
        # 基本表情符號測試
        "🎧 科技新知：AI 人工智慧最新發展 🔥",
        "商業管理：企業經營策略與領導力 💼",
        "教育學習：如何提升學習效率 📚",
        "創業故事：從零到一的創業歷程 🚀",
        "健康生活：營養與運動的平衡 ⚖️",
        
        # 特殊字符測試
        "AI技術® 版權所有 © 2024",
        "企業商標™ 服務標記℠",
        "溫度變化：25°C 到 30°C",
        "數學公式：∑(x²) = ∞",
        
        # 混合測試
        "🎯 投資理財：股票市場分析 📈 2024年趨勢",
        "🏥 醫療科技：AI診斷系統 ⚕️ 最新突破",
        "🎨 文化藝術：現代藝術展覽 🖼️ 精彩回顧",
        
        # 複雜表情符號
        "🇹🇼 台灣科技：本土AI發展 🇯🇵 與日本合作",
        "👨‍💻 程式開發：全端工程師 👩‍💼 與產品經理",
        "🏢 企業文化：團隊合作 🤝 與創新思維",
        
        # 長文本測試
        """
        🎧 播客節目：深度訪談系列
        🔥 熱門話題：人工智慧在商業中的應用
        💡 創新思維：如何運用AI提升企業效率
        📊 數據分析：市場趨勢與投資機會
        🌟 成功案例：從創業到上市的完整歷程
        """,
        
        # 特殊情況
        "  多餘空白  和換行\n\n處理  ",
        "Unicode標準化：café vs café",
        "混合語言：AI技術 + 人工智慧 + Artificial Intelligence"
    ]
    
    logger.info("=== 開始文本清理測試 ===")
    
    for i, text in enumerate(test_cases, 1):
        logger.info(f"\n--- 測試案例 {i} ---")
        logger.info(f"原始文本: {text}")
        
        # 基本清理
        cleaned = cleaner.clean_text(text)
        logger.info(f"清理後: {cleaned}")
        
        # 標題標準化
        normalized = cleaner.normalize_title(text)
        logger.info(f"標準化標題: {normalized}")
        
        # 搜索變體
        variants = cleaner.create_search_variants(text)
        logger.info(f"搜索變體: {variants}")
        
        # 相似度測試（與清理後的文本比較）
        similarity = cleaner.is_similar_title(text, cleaned)
        logger.info(f"與清理後文本相似度: {similarity}")
        
        logger.info("-" * 50)


def test_specific_emojis():
    """測試特定表情符號"""
    cleaner = TextCleaner()
    
    logger.info("\n=== 特定表情符號測試 ===")
    
    # 測試常見表情符號
    emoji_tests = [
        "😀😃😄😁😆😅😂🤣",  # 笑臉系列
        "😊😇🙂🙃😉😌😍🥰",  # 正面情緒
        "😘😗😙😚😋😛😝😜",  # 親吻系列
        "🤪🤨🧐🤓😎🤩🥳😏",  # 其他表情
        "😒😞😔😟😕🙁☹️😣",  # 負面情緒
        "😖😫😩🥺😢😭😤😠",  # 更多負面情緒
        "😡🤬🤯😳🥵🥶😱😨",  # 極端情緒
        "😰😥😓🤗🤔🤭🤫🤥",  # 複雜情緒
        "😶😐😑😯😦😧😮😲",  # 驚訝系列
        "😴🤤😪😵🤐🥴🤢🤮",  # 身體狀態
        "🤧😷🤒🤕🤑🤠👻👽",  # 其他狀態
        "🤖😈👿👹👺💀☠️💩",  # 特殊角色
        "🤡🎃👾😺😸😹😻😼",  # 動物表情
        "😽🙀😿😾🙈🙉🙊💌",  # 更多動物
        "💘💝💖💗💓💞💕💟",  # 愛心系列
        "❣️💔❤️🧡💛💚💙💜",  # 彩色愛心
        "🖤🤍🤎💯💢💥💫💦",  # 其他符號
        "💨🕳️💬🗨️🗯️💭💤💮",  # 對話框系列
        "♨️💈🛑🛢️🛠️🛡️🛤️🛥️",  # 交通符號
        "🛩️🛫🛬🛰️🛳️🛴🛵🛶",  # 交通工具
        "🛷🛸🛹🛺🛻🛼🟠🟡",  # 更多交通工具
        "🟢🟣🟤⚫⚪🟥🟧🟨",  # 顏色形狀
        "🟩🟦🟪🟫⬛⬜◼️◻️",  # 更多形狀
        "◾◽▪️▫️🔶🔷🔸🔹",  # 鑽石系列
        "🔺🔻💠🔘🔳🔲🏁🚩",  # 旗幟系列
        "🎌🏴🏳️🏳️‍🌈🏴‍☠️🇹🇼🇯🇵🇺🇸🇬🇧",  # 國旗系列
    ]
    
    for i, emoji_text in enumerate(emoji_tests, 1):
        logger.info(f"\n表情符號測試 {i}: {emoji_text}")
        cleaned = cleaner.clean_text(emoji_text)
        logger.info(f"清理後: {cleaned}")


def test_special_characters():
    """測試特殊字符"""
    cleaner = TextCleaner()
    
    logger.info("\n=== 特殊字符測試 ===")
    
    special_char_tests = [
        "註冊商標® 版權© 商標™",
        "服務商標℠ 錄音版權℗ 轉交℅",
        "編號№ 電話℡ 處方℞ 回應℟",
        "溫度：25°C 到 30°F",
        "角度：90° 分′ 秒″",
        "比例：5‰ 萬分比‱",
        "數學：∞ ∅ ∈ ∉ ∋ ∌",
        "運算：∏ ∑ √ ∛ ∜ ± ∓",
        "符號：× ÷ ∕ ∗ ∘ ∙ ⋅ ⋆",
        "邏輯：⋈ ⋉ ⋊ ⋋ ⋌ ⋍ ⋎ ⋏",
        "集合：⋐ ⋑ ⋒ ⋓ ⋔ ⋕ ⋖ ⋗",
        "比較：⋘ ⋙ ⋚ ⋛ ⋜ ⋝ ⋞ ⋟",
        "關係：⋠ ⋡ ⋢ ⋣ ⋤ ⋥ ⋦ ⋧",
        "包含：⋨ ⋩ ⋪ ⋫ ⋬ ⋭ ⋮ ⋯",
        "省略：⋰ ⋱ ⋲ ⋳ ⋴ ⋵ ⋶ ⋷",
        "更多：⋸ ⋹ ⋺ ⋻ ⋼ ⋽ ⋾ ⋿"
    ]
    
    for i, char_text in enumerate(special_char_tests, 1):
        logger.info(f"\n特殊字符測試 {i}: {char_text}")
        cleaned = cleaner.clean_text(char_text, remove_special_chars=True)
        logger.info(f"清理後: {cleaned}")


def test_performance():
    """測試性能"""
    import time
    
    cleaner = TextCleaner()
    
    logger.info("\n=== 性能測試 ===")
    
    # 長文本測試
    long_text = "🎧 " * 1000 + "AI技術發展" * 500 + "🔥 " * 1000
    
    start_time = time.time()
    cleaned = cleaner.clean_text(long_text)
    end_time = time.time()
    
    logger.info(f"長文本清理時間: {end_time - start_time:.4f} 秒")
    logger.info(f"原始長度: {len(long_text)}")
    logger.info(f"清理後長度: {len(cleaned)}")


def main():
    """主函數"""
    logger.info("開始文本清理功能測試")
    
    try:
        # 基本功能測試
        test_text_cleaning()
        
        # 特定表情符號測試
        test_specific_emojis()
        
        # 特殊字符測試
        test_special_characters()
        
        # 性能測試
        test_performance()
        
        logger.info("\n=== 所有測試完成 ===")
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}")


if __name__ == "__main__":
    main() 