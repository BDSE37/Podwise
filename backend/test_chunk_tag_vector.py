"""
測試腳本：切斷、貼標、轉向量流程
整合文本清理功能，處理表情符號和特殊字元
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
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
from vector_pipeline.pipeline_orchestrator import TagProcessorManager

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_chunk_tag_vector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ChunkTagVectorTester:
    """切斷、貼標、轉向量測試器"""
    
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
            'collection_name': 'podcast_chunks_test',
            'dim': 1024
        }
        
        # 初始化組件
        self.text_cleaner = TextCleaner()
        self.mongo_processor = MongoDBProcessor(self.mongo_config)
        self.text_chunker = TextChunker(max_chunk_size=1024, overlap=100)
        self.vector_processor = VectorProcessor(model_name="BAAI/bge-m3")
        self.milvus_writer = MilvusWriter(self.milvus_config)
        self.tag_manager = TagProcessorManager("TAG_info.csv")
        
        logger.info("測試器初始化完成")
    
    def test_text_cleaning(self, sample_texts: List[str]) -> None:
        """測試文本清理功能"""
        logger.info("=== 測試文本清理功能 ===")
        
        for i, text in enumerate(sample_texts):
            logger.info(f"\n原始文本 {i+1}: {text}")
            
            # 清理文本
            cleaned_text = self.text_cleaner.clean_text(
                text, 
                remove_emojis=True,
                normalize_unicode=True,
                remove_special_chars=False
            )
            
            logger.info(f"清理後文本: {cleaned_text}")
            
            # 測試標題標準化
            normalized_title = self.text_cleaner.normalize_title(text)
            logger.info(f"標準化標題: {normalized_title}")
            
            # 測試搜索變體
            search_variants = self.text_cleaner.create_search_variants(text)
            logger.info(f"搜索變體: {search_variants}")
    
    def test_chunking(self, long_text: str) -> List[TextChunk]:
        """測試文本切分"""
        logger.info("=== 測試文本切分 ===")
        
        # 清理文本
        cleaned_text = self.text_cleaner.clean_text(long_text)
        logger.info(f"清理後文本長度: {len(cleaned_text)}")
        
        # 切分文本
        chunks = self.text_chunker.chunk_text(cleaned_text)
        logger.info(f"切分出 {len(chunks)} 個文本塊")
        
        for i, chunk in enumerate(chunks):
            logger.info(f"文本塊 {i+1}: 長度={len(chunk.text)}, 內容預覽={chunk.text[:100]}...")
        
        return chunks
    
    def test_tagging(self, chunks: List[TextChunk]) -> List[Dict[str, Any]]:
        """測試標籤提取"""
        logger.info("=== 測試標籤提取 ===")
        
        tagged_chunks = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"\n處理文本塊 {i+1}:")
            logger.info(f"文本預覽: {chunk.text[:200]}...")
            
            # 提取標籤
            tags = self.tag_manager.extract_tags(chunk.text)
            logger.info(f"提取標籤: {tags}")
            
            tagged_chunks.append({
                'chunk_index': i,
                'chunk_text': chunk.text,
                'tags': tags
            })
        
        return tagged_chunks
    
    def test_vectorization(self, tagged_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """測試向量化"""
        logger.info("=== 測試向量化 ===")
        
        vectorized_chunks = []
        
        for chunk_data in tagged_chunks:
            logger.info(f"\n向量化文本塊 {chunk_data['chunk_index'] + 1}:")
            
            # 生成文本向量
            text_embedding = self.vector_processor.generate_embedding(chunk_data['chunk_text'])
            logger.info(f"文本向量維度: {len(text_embedding)}")
            
            # 生成標籤向量
            tag_embeddings = []
            for tag in chunk_data['tags']:
                tag_embedding = self.vector_processor.generate_embedding(tag)
                tag_embeddings.append(tag_embedding)
            
            logger.info(f"標籤向量數量: {len(tag_embeddings)}")
            
            vectorized_chunks.append({
                **chunk_data,
                'text_embedding': text_embedding,
                'tag_embeddings': tag_embeddings
            })
        
        return vectorized_chunks
    
    def test_milvus_storage(self, vectorized_chunks: List[Dict[str, Any]]) -> None:
        """測試 Milvus 儲存"""
        logger.info("=== 測試 Milvus 儲存 ===")
        
        try:
            # 準備儲存資料
            storage_data = []
            
            for chunk_data in vectorized_chunks:
                # 準備標籤向量（確保有3個）
                tag_vectors = chunk_data['tag_embeddings']
                while len(tag_vectors) < 3:
                    tag_vectors.append(chunk_data['text_embedding'])  # 用文本向量填充
                
                storage_data.append({
                    'chunk_id': f"test_chunk_{chunk_data['chunk_index']}",
                    'chunk_index': chunk_data['chunk_index'],
                    'chunk_text': chunk_data['chunk_text'],
                    'chunk_length': len(chunk_data['chunk_text']),
                    'episode_id': 999,  # 測試用
                    'podcast_id': 999,  # 測試用
                    'episode_title': '測試節目',
                    'podcast_name': '測試播客',
                    'author': '測試作者',
                    'category': '測試分類',
                    'created_at': datetime.now().isoformat(),
                    'source_model': 'test_model',
                    'language': 'zh-TW',
                    'embedding': chunk_data['text_embedding'],
                    'tag_1': tag_vectors[0],
                    'tag_2': tag_vectors[1],
                    'tag_3': tag_vectors[2],
                    'tags': chunk_data['tags']
                })
            
            # 寫入 Milvus
            success_count = self.milvus_writer.write_chunks(storage_data)
            logger.info(f"成功儲存 {success_count} 個文本塊到 Milvus")
            
        except Exception as e:
            logger.error(f"Milvus 儲存失敗: {e}")
    
    def test_mongo_document_processing(self, limit: int = 3) -> None:
        """測試 MongoDB 文件處理"""
        logger.info("=== 測試 MongoDB 文件處理 ===")
        
        try:
            # 獲取測試文件
            documents = self.mongo_processor.get_documents(limit=limit)
            logger.info(f"獲取到 {len(documents)} 個測試文件")
            
            for i, doc in enumerate(documents):
                logger.info(f"\n處理文件 {i+1}:")
                logger.info(f"標題: {doc.title}")
                logger.info(f"內容長度: {len(doc.content)}")
                
                # 清理標題
                cleaned_title = self.text_cleaner.clean_text(doc.title)
                logger.info(f"清理後標題: {cleaned_title}")
                
                # 清理內容
                cleaned_content = self.text_cleaner.clean_text(doc.content)
                logger.info(f"清理後內容長度: {len(cleaned_content)}")
                
                # 切分
                chunks = self.text_chunker.chunk_text(cleaned_content)
                logger.info(f"切分出 {len(chunks)} 個文本塊")
                
                # 標籤提取
                for j, chunk in enumerate(chunks[:2]):  # 只處理前2個塊
                    tags = self.tag_manager.extract_tags(chunk.text)
                    logger.info(f"文本塊 {j+1} 標籤: {tags}")
                
                break  # 只處理第一個文件作為測試
        
        except Exception as e:
            logger.error(f"MongoDB 處理失敗: {e}")
    
    def run_full_test(self) -> None:
        """執行完整測試"""
        logger.info("開始執行完整測試流程")
        
        # 測試文本清理
        sample_texts = [
            "🎧 科技新知：AI 人工智慧最新發展 🔥",
            "商業管理：企業經營策略與領導力 💼",
            "教育學習：如何提升學習效率 📚",
            "創業故事：從零到一的創業歷程 🚀",
            "健康生活：營養與運動的平衡 ⚖️"
        ]
        self.test_text_cleaning(sample_texts)
        
        # 測試長文本切分
        long_text = """
        人工智慧（Artificial Intelligence，AI）是電腦科學的一個分支，它企圖了解智能的實質，
        並生產出一種新的能以人類智能相似的方式做出反應的智能機器。該領域的研究包括機器人、
        語言識別、圖像識別、自然語言處理和專家系統等。人工智慧從誕生以來，理論和技術日益成熟，
        應用領域也不斷擴大，可以設想，未來人工智慧帶來的科技產品，將會是人類智慧的「容器」。
        
        人工智慧可以對人的意識、思維的信息過程的模擬。人工智慧不是人的智能，但能像人那樣思考、
        也可能超過人的智能。人工智慧是一門極富挑戰性的科學，從事人工智慧工作的人必須懂得電腦知識，
        心理學和哲學。人工智慧是包括十分廣泛的科學，它由不同的領域組成，如機器學習，電腦視覺等等，
        總的說來，人工智慧研究的一個主要目標是使機器能夠勝任一些通常需要人類智能才能完成的複雜工作。
        
        在商業應用方面，人工智慧已經在許多領域發揮重要作用。例如，在客戶服務中，聊天機器人可以
        24小時不間斷地為客戶提供服務；在金融領域，AI可以幫助進行風險評估和投資決策；在醫療領域，
        AI可以協助醫生進行疾病診斷和治療方案制定。這些應用不僅提高了效率，也為企業創造了新的價值。
        """
        
        chunks = self.test_chunking(long_text)
        tagged_chunks = self.test_tagging(chunks)
        vectorized_chunks = self.test_vectorization(tagged_chunks)
        self.test_milvus_storage(vectorized_chunks)
        
        # 測試 MongoDB 文件處理
        self.test_mongo_document_processing()
        
        logger.info("完整測試流程完成")
    
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
    tester = ChunkTagVectorTester()
    
    try:
        tester.run_full_test()
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}")
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main() 