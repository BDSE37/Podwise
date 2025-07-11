#!/usr/bin/env python3
"""
測試增強版標籤處理器整合
驗證 enhanced_tagging.py 與新架構的整合
"""

import logging
import sys
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_enhanced_tagging_direct():
    """直接測試 enhanced_tagging.py"""
    try:
        logger.info("=== 直接測試 enhanced_tagging.py ===")
        
        # 導入增強版標籤處理器
        from enhanced_tagging import EnhancedTagProcessor, MoneyDJWikiExtractor
        
        # 測試 MoneyDJ 百科提取器
        extractor = MoneyDJWikiExtractor()
        terms = extractor.load_moneydj_terms()
        logger.info(f"載入 {len(terms)} 個專業術語")
        
        # 測試文本
        test_texts = [
            "AI人工智慧技術正在改變世界，機器學習演算法越來越強大",
            "特斯拉的電動車技術非常先進，伊隆馬斯克是偉大的創業家",
            "加密貨幣比特幣的價格波動很大，區塊鏈技術很有潛力",
            "ESG永續發展理念越來越重要，企業社會責任不能忽視",
            "美中貿易戰持續升溫，川普政府對中國商品加徵關稅"
        ]
        
        for i, text in enumerate(test_texts, 1):
            tags = extractor.extract_moneydj_tags(text)
            logger.info(f"文本 {i}: {text[:50]}...")
            logger.info(f"標籤: {tags}")
            logger.info("-" * 50)
        
        # 測試增強版標籤處理器
        processor = EnhancedTagProcessor("../utils/TAG_info.csv")
        
        for i, text in enumerate(test_texts, 1):
            tags = processor.extract_enhanced_tags(text)
            logger.info(f"增強版處理器 - 文本 {i}: {text[:50]}...")
            logger.info(f"標籤: {tags}")
            logger.info("-" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"直接測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unified_integration():
    """測試統一架構整合"""
    try:
        logger.info("=== 測試統一架構整合 ===")
        
        # 導入統一標籤處理器
        from core.tag_processor import UnifiedTagProcessor
        
        # 初始化統一標籤處理器
        processor = UnifiedTagProcessor("../utils/TAG_info.csv")
        
        # 顯示提取器狀態
        status = processor.get_extractor_status()
        logger.info(f"提取器狀態: {status}")
        
        # 測試文本
        test_texts = [
            "AI人工智慧技術正在改變世界，機器學習演算法越來越強大",
            "特斯拉的電動車技術非常先進，伊隆馬斯克是偉大的創業家",
            "加密貨幣比特幣的價格波動很大，區塊鏈技術很有潛力",
            "ESG永續發展理念越來越重要，企業社會責任不能忽視",
            "美中貿易戰持續升溫，川普政府對中國商品加徵關稅"
        ]
        
        for i, text in enumerate(test_texts, 1):
            tags = processor.extract_enhanced_tags(text)
            logger.info(f"統一處理器 - 文本 {i}: {text[:50]}...")
            logger.info(f"標籤: {tags}")
            logger.info("-" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"統一架構測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    logger.info("=== 開始測試增強版標籤處理器整合 ===")
    
    # 測試直接使用 enhanced_tagging.py
    direct_success = test_enhanced_tagging_direct()
    
    # 測試統一架構整合
    unified_success = test_unified_integration()
    
    # 總結
    logger.info("=== 測試結果總結 ===")
    logger.info(f"直接測試: {'成功' if direct_success else '失敗'}")
    logger.info(f"統一架構測試: {'成功' if unified_success else '失敗'}")
    
    if direct_success and unified_success:
        logger.info("✅ 所有測試通過！增強版標籤處理器整合成功")
    else:
        logger.error("❌ 部分測試失敗，請檢查錯誤訊息")
    
    return direct_success and unified_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 