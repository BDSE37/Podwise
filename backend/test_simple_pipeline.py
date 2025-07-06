"""
簡化測試腳本：切斷、貼標、轉向量流程
專門測試基本功能，不依賴 PostgreSQL
整合錯誤記錄功能
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
import json
from datetime import datetime

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent))

from vector_pipeline.core import (
    MongoDBProcessor, MongoDocument,
    TextChunker, TextChunk,
    VectorProcessor,
    MilvusWriter
)
from vector_pipeline.utils.text_cleaner import TextCleaner
from vector_pipeline.error_logger import ErrorLogger, ErrorHandler

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_pipeline_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimplePipelineTester:
    """簡化管道測試器"""
    
    def __init__(self):
        # 配置
        self.mongo_config = {
            'host': 'localhost',
            'port': 27017,
            'database': 'podwise',
            'collection': 'podcasts'
        }
        
        self.milvus_config = {
            'host': 'localhost',
            'port': 19530,
            'collection_name': 'podcast_chunks_simple_test',
            'dim': 1024
        }
        
        # 初始化組件
        self.text_cleaner = TextCleaner()
        self.mongo_processor = MongoDBProcessor(self.mongo_config)
        self.text_chunker = TextChunker(max_chunk_size=1024, overlap_size=100)
        self.vector_processor = VectorProcessor(model_name="BAAI/bge-m3")
        self.milvus_writer = MilvusWriter(self.milvus_config)
        
        # 初始化錯誤記錄器
        self.error_logger = ErrorLogger("error_logs")
        self.error_handler = ErrorHandler(self.error_logger)
        
        logger.info("簡化測試器初始化完成")
    
    def extract_simple_tags(self, text: str) -> List[str]:
        """簡單的標籤提取"""
        tags = []
        text_lower = text.lower()
        
        # 簡單關鍵字匹配
        keyword_mapping = {
            'ai': 'AI人工智慧',
            '人工智慧': 'AI人工智慧',
            '科技': '科技技術',
            '技術': '科技技術',
            '商業': '商業管理',
            '企業': '商業管理',
            '管理': '商業管理',
            '創業': '創業創新',
            '創新': '創業創新',
            '教育': '教育學習',
            '學習': '教育學習',
            '健康': '健康生活',
            '生活': '健康生活',
            '投資': '投資理財',
            '理財': '投資理財',
            '娛樂': '娛樂休閒',
            '休閒': '娛樂休閒',
            '政治': '政治社會',
            '社會': '政治社會',
            '文化': '文化藝術',
            '藝術': '文化藝術'
        }
        
        for keyword, tag in keyword_mapping.items():
            if keyword in text_lower:
                if tag not in tags:
                    tags.append(tag)
                if len(tags) >= 3:  # 最多3個標籤
                    break
        
        # 如果沒有找到標籤，使用預設標籤
        if not tags:
            tags = ['一般內容']
        
        return tags[:3]
    
    def process_single_document(self, doc: MongoDocument) -> List[Dict[str, Any]]:
        """處理單個文件（整合錯誤處理）"""
        logger.info(f"處理文件: {doc.title}")
        
        try:
            # 1. 清理文本
            try:
                cleaned_title = self.text_cleaner.clean_text(doc.title)
                cleaned_content = self.text_cleaner.clean_text(doc.content)
            except Exception as e:
                self.error_handler.handle_text_processing_error(
                    collection_id=getattr(doc, 'collection_id', 'unknown'),
                    rss_id=getattr(doc, 'rss_id', 'unknown'),
                    title=doc.title,
                    error=e,
                    stage="text_cleaning"
                )
                raise
            
            logger.info(f"清理後標題: {cleaned_title}")
            logger.info(f"清理後內容長度: {len(cleaned_content)}")
            
            # 2. 切分文本
            try:
                chunks = self.text_chunker.split_text_into_chunks(cleaned_content, str(doc.id))
            except Exception as e:
                self.error_handler.handle_text_processing_error(
                    collection_id=getattr(doc, 'collection_id', 'unknown'),
                    rss_id=getattr(doc, 'rss_id', 'unknown'),
                    title=doc.title,
                    error=e,
                    stage="text_chunking"
                )
                raise
            
            logger.info(f"切分出 {len(chunks)} 個文本塊")
            
            processed_chunks = []
            
            # 3. 處理每個文本塊
            for i, chunk in enumerate(chunks):
                try:
                    logger.info(f"處理文本塊 {i+1}/{len(chunks)}")
                    
                    # 提取標籤
                    tags = self.extract_simple_tags(chunk.chunk_text)
                    logger.info(f"標籤: {tags}")
                    
                    # 生成向量
                    try:
                        text_embedding = self.vector_processor.generate_embedding(chunk.chunk_text)
                    except Exception as e:
                        self.error_handler.handle_vectorization_error(
                            collection_id=getattr(doc, 'collection_id', 'unknown'),
                            rss_id=getattr(doc, 'rss_id', 'unknown'),
                            title=doc.title,
                            error=e,
                            stage="text_vectorization"
                        )
                        raise
                    
                    tag_embeddings = []
                    for tag in tags:
                        try:
                            tag_embedding = self.vector_processor.generate_embedding(tag)
                            tag_embeddings.append(tag_embedding)
                        except Exception as e:
                            self.error_handler.handle_vectorization_error(
                                collection_id=getattr(doc, 'collection_id', 'unknown'),
                                rss_id=getattr(doc, 'rss_id', 'unknown'),
                                title=doc.title,
                                error=e,
                                stage="tag_vectorization"
                            )
                            # 使用文本向量作為標籤向量的備用
                            tag_embeddings.append(text_embedding)
                    
                    # 確保有3個標籤向量
                    while len(tag_embeddings) < 3:
                        tag_embeddings.append(text_embedding)
                    
                    processed_chunk = {
                        'chunk_id': f"{doc.id}_chunk_{i}",
                        'chunk_index': i,
                        'chunk_text': chunk.chunk_text,
                        'chunk_length': len(chunk.chunk_text),
                        'episode_id': getattr(doc, 'episode_id', 999),
                        'podcast_id': getattr(doc, 'podcast_id', 999),
                        'episode_title': cleaned_title,
                        'podcast_name': getattr(doc, 'podcast_name', '未知播客'),
                        'author': getattr(doc, 'author', '未知作者'),
                        'category': getattr(doc, 'category', '一般'),
                        'created_at': datetime.now().isoformat(),
                        'source_model': 'simple_test',
                        'language': 'zh-TW',
                        'embedding': text_embedding,
                        'tag_1': tag_embeddings[0],
                        'tag_2': tag_embeddings[1],
                        'tag_3': tag_embeddings[2],
                        'tags': tags
                    }
                    
                    processed_chunks.append(processed_chunk)
                    
                except Exception as e:
                    self.error_handler.handle_general_error(
                        collection_id=getattr(doc, 'collection_id', 'unknown'),
                        rss_id=getattr(doc, 'rss_id', 'unknown'),
                        title=doc.title,
                        error=e,
                        stage="chunk_processing"
                    )
                    logger.error(f"處理文本塊 {i+1} 失敗: {e}")
                    continue
            
            return processed_chunks
            
        except Exception as e:
            self.error_handler.handle_general_error(
                collection_id=getattr(doc, 'collection_id', 'unknown'),
                rss_id=getattr(doc, 'rss_id', 'unknown'),
                title=doc.title,
                error=e,
                stage="document_processing"
            )
            logger.error(f"處理文件失敗: {e}")
            return []
    
    def test_with_sample_data(self) -> None:
        """使用樣本資料測試"""
        logger.info("=== 使用樣本資料測試 ===")
        
        # 樣本資料
        sample_text = """
        人工智慧（AI）是當今科技發展的重要趨勢。在商業應用中，AI技術正在改變企業的運營方式，
        從客戶服務到產品開發，從市場分析到決策制定，AI都發揮著越來越重要的作用。
        
        在教育領域，AI技術為學習者提供了個性化的學習體驗，智能導師系統可以根據學生的學習進度
        和興趣調整教學內容，提高學習效率。同時，AI也在幫助教師更好地管理課堂和評估學生表現。
        
        在健康醫療方面，AI技術的應用更是廣泛，從醫學影像診斷到藥物研發，從患者護理到疾病預測，
        AI都在為醫療行業帶來革命性的變化。這些技術不僅提高了醫療效率，也為患者提供了更好的醫療服務。
        """
        
        # 創建模擬文件
        mock_doc = MongoDocument(
            id="test_001",
            title="🎧 AI科技新知：人工智慧在商業與教育中的應用 🔥",
            content=sample_text,
            episode_id=1001,
            podcast_id=2001,
            podcast_name="科技新知播客",
            author="科技專家",
            category="科技",
            collection_id="test_collection",
            rss_id="test_rss_001"
        )
        
        # 處理文件
        processed_chunks = self.process_single_document(mock_doc)
        
        # 儲存到 Milvus
        if processed_chunks:
            try:
                success_count = self.milvus_writer.write_chunks(processed_chunks)
                logger.info(f"成功儲存 {success_count} 個文本塊到 Milvus")
            except Exception as e:
                self.error_handler.handle_milvus_error(
                    collection_id="test_collection",
                    rss_id="test_rss_001",
                    title=mock_doc.title,
                    error=e,
                    stage="milvus_write"
                )
                logger.error(f"儲存到 Milvus 失敗: {e}")
    
    def test_with_mongo_data(self, limit: int = 2) -> None:
        """使用 MongoDB 真實資料測試"""
        logger.info("=== 使用 MongoDB 真實資料測試 ===")
        
        try:
            # 獲取文件
            documents = self.mongo_processor.get_documents(limit=limit)
            logger.info(f"獲取到 {len(documents)} 個文件")
            
            total_processed = 0
            
            for i, doc in enumerate(documents):
                logger.info(f"\n處理文件 {i+1}/{len(documents)}")
                
                try:
                    processed_chunks = self.process_single_document(doc)
                    total_processed += len(processed_chunks)
                    
                    # 儲存到 Milvus
                    if processed_chunks:
                        try:
                            success_count = self.milvus_writer.write_chunks(processed_chunks)
                            logger.info(f"文件 {i+1} 成功儲存 {success_count} 個文本塊")
                        except Exception as e:
                            self.error_handler.handle_milvus_error(
                                collection_id=getattr(doc, 'collection_id', 'unknown'),
                                rss_id=getattr(doc, 'rss_id', 'unknown'),
                                title=doc.title,
                                error=e,
                                stage="milvus_write"
                            )
                            logger.error(f"儲存文件 {i+1} 到 Milvus 失敗: {e}")
                    
                except Exception as e:
                    self.error_handler.handle_general_error(
                        collection_id=getattr(doc, 'collection_id', 'unknown'),
                        rss_id=getattr(doc, 'rss_id', 'unknown'),
                        title=doc.title,
                        error=e,
                        stage="document_processing"
                    )
                    logger.error(f"處理文件 {i+1} 失敗: {e}")
                    continue
            
            logger.info(f"總共處理了 {total_processed} 個文本塊")
            
        except Exception as e:
            self.error_handler.handle_general_error(
                collection_id="unknown",
                rss_id="unknown",
                title="unknown",
                error=e,
                stage="mongodb_connection"
            )
            logger.error(f"MongoDB 測試失敗: {e}")
    
    def run_test(self, use_mongo: bool = False) -> None:
        """執行測試"""
        logger.info("開始執行簡化管道測試")
        
        try:
            if use_mongo:
                self.test_with_mongo_data()
            else:
                self.test_with_sample_data()
            
            logger.info("測試完成")
            
        except Exception as e:
            logger.error(f"測試過程中發生錯誤: {e}")
        finally:
            # 儲存錯誤報告
            if self.error_logger.errors:
                logger.info("=== 錯誤報告 ===")
                self.error_logger.print_summary()
                
                reports = self.error_handler.save_error_reports()
                logger.info(f"錯誤報告已儲存:")
                logger.info(f"  JSON: {reports['json_report']}")
                logger.info(f"  CSV: {reports['csv_report']}")
            else:
                logger.info("沒有錯誤記錄")
            
            self.cleanup()
    
    def cleanup(self) -> None:
        """清理資源"""
        try:
            self.mongo_processor.close()
            self.milvus_writer.close()
            logger.info("資源清理完成")
        except Exception as e:
            logger.error(f"清理資源時發生錯誤: {e}")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='簡化管道測試')
    parser.add_argument('--mongo', action='store_true', help='使用 MongoDB 真實資料')
    parser.add_argument('--sample', action='store_true', help='使用樣本資料')
    
    args = parser.parse_args()
    
    tester = SimplePipelineTester()
    
    if args.mongo:
        tester.run_test(use_mongo=True)
    else:
        tester.run_test(use_mongo=False)


if __name__ == "__main__":
    main() 