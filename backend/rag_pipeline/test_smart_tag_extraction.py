#!/usr/bin/env python3
"""
智能 TAG 提取測試

此腳本測試智能 TAG 提取功能，包含：
- 基礎 TAG 提取
- Word2Vec 語義相似度
- Transformer 語義理解
- 智能標籤映射
- 與 PodcastFormatter 整合

作者: Podwise Team
版本: 1.0.0
"""

import logging
import sys
from pathlib import Path

# 添加專案路徑
sys.path.append(str(Path(__file__).parent))

from tools.smart_tag_extractor import SmartTagExtractor
from tools.podcast_formatter import PodcastFormatter

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartTagExtractionTester:
    """智能 TAG 提取測試器"""
    
    def __init__(self):
        """初始化測試器"""
        self.smart_extractor = SmartTagExtractor()
        self.podcast_formatter = PodcastFormatter()
        
        # 測試查詢列表
        self.test_queries = [
            # 基礎 TAG 測試
            "我想了解 NVIDIA 的投資機會",
            "請推薦關於 '機器學習' 的 Podcast",
            "我想聽聽關於 TSMC 的分析",
            "請推薦職涯發展相關的節目",
            
            # 智能映射測試
            "我想了解人工智慧的發展趨勢",
            "請推薦關於深度學習的內容",
            "我想聽聽關於區塊鏈技術的討論",
            "請推薦關於加密貨幣投資的節目",
            
            # 複雜查詢測試
            "我想了解 NVIDIA 和 TSMC 在 AI 晶片市場的競爭",
            "請推薦關於機器學習和深度學習在教育領域應用的 Podcast",
            "我想聽聽關於區塊鏈、加密貨幣和 NFT 的綜合討論",
            "請推薦關於職涯發展、創業和投資理財的節目"
        ]
    
    def test_basic_tag_extraction(self):
        """測試基礎 TAG 提取"""
        logger.info("=== 測試基礎 TAG 提取 ===")
        
        for query in self.test_queries[:4]:
            logger.info(f"\n查詢: {query}")
            
            # 使用智能提取器
            smart_result = self.smart_extractor.extract_smart_tags(query)
            
            logger.info(f"提取的 TAG: {smart_result.extracted_tags}")
            logger.info(f"信心度: {smart_result.confidence:.2f}")
            logger.info(f"使用的方法: {smart_result.method_used}")
            logger.info(f"處理時間: {smart_result.processing_time:.3f}秒")
            
            if smart_result.mapped_tags:
                logger.info("映射結果:")
                for mapping in smart_result.mapped_tags:
                    logger.info(f"  {mapping.original_tag} -> {mapping.mapped_tags} (方法: {mapping.method}, 信心度: {mapping.confidence:.2f})")
    
    def test_smart_mapping(self):
        """測試智能映射功能"""
        logger.info("\n=== 測試智能映射功能 ===")
        
        # 測試一些不在預設標籤表中的詞彙
        test_tags = [
            "人工智慧", "深度學習", "區塊鏈", "加密貨幣",
            "量子計算", "元宇宙", "NFT", "自駕車",
            "物聯網", "5G", "雲端運算", "大數據"
        ]
        
        for tag in test_tags:
            logger.info(f"\n測試標籤: {tag}")
            
            # 檢查是否在現有標籤表中
            if tag in self.smart_extractor.existing_tags:
                logger.info(f"  ✓ 已在現有標籤表中")
            else:
                logger.info(f"  ✗ 不在現有標籤表中，嘗試智能映射")
                
                # 嘗試 Word2Vec 映射
                if self.smart_extractor.word2vec_model:
                    word2vec_results = self.smart_extractor.word2vec_similarity(tag)
                    if word2vec_results:
                        logger.info(f"  Word2Vec 映射: {word2vec_results[:3]}")
                
                # 嘗試 Transformer 映射
                if self.smart_extractor.transformer_model:
                    transformer_results = self.smart_extractor.transformer_similarity(tag)
                    if transformer_results:
                        logger.info(f"  Transformer 映射: {transformer_results[:3]}")
                
                # 嘗試模糊匹配
                fuzzy_matches = self.smart_extractor.fuzzy_match(tag)
                if fuzzy_matches:
                    logger.info(f"  模糊匹配: {fuzzy_matches}")
    
    def test_podcast_formatter_integration(self):
        """測試與 PodcastFormatter 的整合"""
        logger.info("\n=== 測試 PodcastFormatter 整合 ===")
        
        # 測試數據
        test_podcasts = [
            {
                'title': '股癌 EP310',
                'description': '台股投資分析與市場趨勢，討論 NVIDIA 的投資機會',
                'rss_id': '123456789',
                'confidence': 0.9,
                'category': '商業',
                'tags': ['股票', '投資', '台股', 'NVIDIA']
            },
            {
                'title': '大人學 EP110',
                'description': '職涯發展與個人成長指南',
                'rss_id': '987654321',
                'confidence': 0.85,
                'category': '教育',
                'tags': ['職涯', '成長', '技能']
            },
            {
                'title': '財報狗 Podcast',
                'description': '財報分析與投資策略，包含 NVIDIA 財報解析',
                'rss_id': '456789123',
                'confidence': 0.88,
                'category': '商業',
                'tags': ['財報', '投資', 'NVIDIA', '分析']
            }
        ]
        
        # 測試複雜查詢
        complex_queries = [
            "我想了解 NVIDIA 和 TSMC 在 AI 晶片市場的競爭",
            "請推薦關於機器學習和深度學習在教育領域應用的 Podcast",
            "我想聽聽關於區塊鏈、加密貨幣和 NFT 的綜合討論"
        ]
        
        for query in complex_queries:
            logger.info(f"\n查詢: {query}")
            
            # 使用 PodcastFormatter 進行格式化
            result = self.podcast_formatter.format_podcast_recommendations(
                test_podcasts, 
                query, 
                max_recommendations=3
            )
            
            logger.info(f"提取的 TAG: {result.tags_used}")
            logger.info(f"信心度: {result.confidence:.2f}")
            logger.info(f"處理時間: {result.processing_time:.3f}秒")
            
            # 生成推薦文字
            recommendation_text = self.podcast_formatter.generate_recommendation_text(result)
            logger.info("推薦文字:")
            logger.info(recommendation_text)
    
    def test_performance(self):
        """測試性能"""
        logger.info("\n=== 測試性能 ===")
        
        import time
        
        # 測試大量查詢的性能
        test_queries = [
            "我想了解 NVIDIA 的投資機會",
            "請推薦關於機器學習的 Podcast",
            "我想聽聽關於 TSMC 的分析",
            "請推薦職涯發展相關的節目",
            "我想了解人工智慧的發展趨勢",
            "請推薦關於深度學習的內容",
            "我想聽聽關於區塊鏈技術的討論",
            "請推薦關於加密貨幣投資的節目"
        ]
        
        total_time = 0
        total_tags = 0
        
        for i, query in enumerate(test_queries, 1):
            start_time = time.time()
            result = self.smart_extractor.extract_smart_tags(query)
            end_time = time.time()
            
            processing_time = end_time - start_time
            total_time += processing_time
            total_tags += len(result.extracted_tags)
            
            logger.info(f"查詢 {i}: {query}")
            logger.info(f"  TAG 數量: {len(result.extracted_tags)}")
            logger.info(f"  處理時間: {processing_time:.3f}秒")
            logger.info(f"  平均每 TAG 時間: {processing_time/len(result.extracted_tags):.3f}秒" if result.extracted_tags else "  無 TAG")
        
        logger.info(f"\n性能總結:")
        logger.info(f"總查詢數: {len(test_queries)}")
        logger.info(f"總處理時間: {total_time:.3f}秒")
        logger.info(f"平均每查詢時間: {total_time/len(test_queries):.3f}秒")
        logger.info(f"總 TAG 數: {total_tags}")
        logger.info(f"平均每查詢 TAG 數: {total_tags/len(test_queries):.1f}")
    
    def run_all_tests(self):
        """執行所有測試"""
        logger.info("🚀 開始智能 TAG 提取測試")
        
        try:
            # 測試基礎功能
            self.test_basic_tag_extraction()
            
            # 測試智能映射
            self.test_smart_mapping()
            
            # 測試整合功能
            self.test_podcast_formatter_integration()
            
            # 測試性能
            self.test_performance()
            
            logger.info("\n✅ 所有測試完成")
            
        except Exception as e:
            logger.error(f"❌ 測試過程中發生錯誤: {str(e)}")
            raise


def main():
    """主函數"""
    tester = SmartTagExtractionTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main() 