"""
快速測試腳本
測試切斷、貼標、轉向量的基本功能
"""

import logging
import sys
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

from vector_pipeline.utils.text_cleaner import TextCleaner
from vector_pipeline.core import TextChunker, VectorProcessor

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def quick_test():
    """快速測試基本功能"""
    logger.info("=== 快速測試開始 ===")
    
    # 1. 測試文本清理
    logger.info("1. 測試文本清理")
    cleaner = TextCleaner()
    
    test_text = "🎧 AI科技新知：人工智慧在商業中的應用 🔥"
    cleaned_text = cleaner.clean_text(test_text)
    
    logger.info(f"原始文本: {test_text}")
    logger.info(f"清理後文本: {cleaned_text}")
    
    # 2. 測試文本切分
    logger.info("\n2. 測試文本切分")
    chunker = TextChunker(max_chunk_size=200, overlap_size=50)
    
    long_text = """
    人工智慧（AI）是當今科技發展的重要趨勢。在商業應用中，AI技術正在改變企業的運營方式，
    從客戶服務到產品開發，從市場分析到決策制定，AI都發揮著越來越重要的作用。
    
    在教育領域，AI技術為學習者提供了個性化的學習體驗，智能導師系統可以根據學生的學習進度
    和興趣調整教學內容，提高學習效率。同時，AI也在幫助教師更好地管理課堂和評估學生表現。
    """
    
    chunks = chunker.chunk_text(long_text)
    logger.info(f"切分出 {len(chunks)} 個文本塊")
    
    for i, chunk in enumerate(chunks):
        logger.info(f"文本塊 {i+1}: {chunk.text[:100]}...")
    
    # 3. 測試向量化
    logger.info("\n3. 測試向量化")
    try:
        vector_processor = VectorProcessor(model_name="BAAI/bge-m3")
        
        # 測試文本向量
        text_embedding = vector_processor.generate_embedding("AI技術發展")
        logger.info(f"文本向量維度: {len(text_embedding)}")
        
        # 測試標籤向量
        tag_embedding = vector_processor.generate_embedding("科技技術")
        logger.info(f"標籤向量維度: {len(tag_embedding)}")
        
    except Exception as e:
        logger.error(f"向量化測試失敗: {e}")
    
    # 4. 測試標籤提取
    logger.info("\n4. 測試標籤提取")
    
    def extract_simple_tags(text):
        """簡單標籤提取"""
        tags = []
        text_lower = text.lower()
        
        keyword_mapping = {
            'ai': 'AI人工智慧',
            '人工智慧': 'AI人工智慧',
            '科技': '科技技術',
            '技術': '科技技術',
            '商業': '商業管理',
            '企業': '商業管理',
            '教育': '教育學習',
            '學習': '教育學習'
        }
        
        for keyword, tag in keyword_mapping.items():
            if keyword in text_lower and tag not in tags:
                tags.append(tag)
                if len(tags) >= 3:
                    break
        
        return tags if tags else ['一般內容']
    
    # 測試標籤提取
    for i, chunk in enumerate(chunks[:2]):  # 只測試前2個塊
        tags = extract_simple_tags(chunk.text)
        logger.info(f"文本塊 {i+1} 標籤: {tags}")
    
    logger.info("\n=== 快速測試完成 ===")


if __name__ == "__main__":
    quick_test() 