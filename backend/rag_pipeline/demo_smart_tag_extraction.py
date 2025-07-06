#!/usr/bin/env python3
"""
智能 TAG 提取功能演示

此腳本展示智能 TAG 提取功能的使用方式和效果

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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_smart_tag_extraction():
    """演示智能 TAG 提取功能"""
    print("🚀 智能 TAG 提取功能演示")
    print("=" * 50)
    
    # 初始化智能提取器
    extractor = SmartTagExtractor()
    
    # 演示查詢列表
    demo_queries = [
        "我想了解 NVIDIA 的投資機會",
        "請推薦關於機器學習的 Podcast",
        "我想聽聽關於 TSMC 的分析",
        "請推薦職涯發展相關的節目",
        "我想了解人工智慧的發展趨勢",
        "請推薦關於深度學習的內容",
        "我想聽聽關於區塊鏈技術的討論",
        "請推薦關於加密貨幣投資的節目"
    ]
    
    print("\n📋 演示查詢:")
    for i, query in enumerate(demo_queries, 1):
        print(f"{i}. {query}")
    
    print("\n" + "=" * 50)
    print("🔍 智能 TAG 提取結果:")
    print("=" * 50)
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{i}. 查詢: {query}")
        print("-" * 40)
        
        # 執行智能 TAG 提取
        result = extractor.extract_smart_tags(query)
        
        print(f"提取的 TAG: {result.extracted_tags}")
        print(f"信心度: {result.confidence:.2f}")
        print(f"使用的方法: {result.method_used}")
        print(f"處理時間: {result.processing_time:.3f}秒")
        
        # 顯示映射詳情
        if result.mapped_tags:
            print("映射詳情:")
            for mapping in result.mapped_tags:
                print(f"  {mapping.original_tag} → {mapping.mapped_tags} (方法: {mapping.method}, 信心度: {mapping.confidence:.2f})")


def demo_podcast_formatter_integration():
    """演示與 PodcastFormatter 的整合"""
    print("\n" + "=" * 50)
    print("🎧 PodcastFormatter 整合演示")
    print("=" * 50)
    
    # 初始化格式化器
    formatter = PodcastFormatter()
    
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
    
    # 複雜查詢示例
    complex_query = "我想了解 NVIDIA 和 TSMC 在 AI 晶片市場的競爭"
    
    print(f"\n查詢: {complex_query}")
    print("-" * 40)
    
    # 使用 PodcastFormatter 進行格式化
    result = formatter.format_podcast_recommendations(
        test_podcasts, 
        complex_query, 
        max_recommendations=3
    )
    
    print(f"提取的 TAG: {result.tags_used}")
    print(f"信心度: {result.confidence:.2f}")
    print(f"處理時間: {result.processing_time:.3f}秒")
    
    # 生成推薦文字
    recommendation_text = formatter.generate_recommendation_text(result)
    print("\n推薦結果:")
    print(recommendation_text)


def demo_advanced_features():
    """演示進階功能"""
    print("\n" + "=" * 50)
    print("⚡ 進階功能演示")
    print("=" * 50)
    
    extractor = SmartTagExtractor()
    
    # 演示不同類型的查詢
    advanced_queries = [
        # 科技相關
        "我想了解量子計算的發展前景",
        "請推薦關於元宇宙的 Podcast",
        "我想聽聽關於 5G 技術的討論",
        
        # 商業相關
        "我想了解創業投資的機會",
        "請推薦關於企業管理的節目",
        "我想聽聽關於市場行銷的策略",
        
        # 教育相關
        "我想了解線上學習的趨勢",
        "請推薦關於技能培訓的 Podcast",
        "我想聽聽關於語言學習的方法"
    ]
    
    print("\n🔬 進階查詢測試:")
    for i, query in enumerate(advanced_queries, 1):
        print(f"\n{i}. {query}")
        
        result = extractor.extract_smart_tags(query)
        
        print(f"   TAG: {result.extracted_tags}")
        print(f"   信心度: {result.confidence:.2f}")
        print(f"   方法: {', '.join(result.method_used)}")
        
        # 顯示智能映射
        if result.mapped_tags:
            mappings = []
            for mapping in result.mapped_tags:
                mappings.append(f"{mapping.original_tag}→{mapping.mapped_tags[0]}({mapping.method})")
            print(f"   映射: {', '.join(mappings)}")


def main():
    """主函數"""
    try:
        # 演示基礎功能
        demo_smart_tag_extraction()
        
        # 演示整合功能
        demo_podcast_formatter_integration()
        
        # 演示進階功能
        demo_advanced_features()
        
        print("\n" + "=" * 50)
        print("✅ 演示完成！")
        print("=" * 50)
        
        print("\n📝 功能總結:")
        print("• 智能 TAG 提取: 結合 Word2Vec + Transformer")
        print("• 多層次映射: 語義相似度 + 模糊匹配")
        print("• 自動降級: 機器學習組件不可用時自動降級")
        print("• 完整整合: 與 PodcastFormatter 無縫整合")
        print("• 高性能: 支援批次處理和快取優化")
        
        print("\n🚀 使用建議:")
        print("• 安裝必要套件: pip install gensim transformers torch jieba")
        print("• 訓練 Word2Vec 模型: python tools/train_word2vec_model.py")
        print("• 調整相似度閾值: 根據需求調整 confidence 設定")
        print("• 監控性能: 定期檢查處理時間和記憶體使用")
        
    except Exception as e:
        logger.error(f"演示過程中發生錯誤: {str(e)}")
        print(f"\n❌ 演示失敗: {str(e)}")


if __name__ == "__main__":
    main() 