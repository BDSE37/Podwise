#!/usr/bin/env python3
"""
整合文本處理器
- 從 MongoDB 下載長文本
- 從 PostgreSQL 獲取 episode 元資料
- 文本分塊處理 (以空白或\n切分)
- 基於 TAG_info.csv 的標籤匹配
- 智能標籤提取 (僅當tag_info中沒有時)
- 向量嵌入生成
"""

import re
import json
import logging
from typing import List, Dict, Tuple, Set, Optional, Any
from collections import defaultdict
from pathlib import Path
import pandas as pd
from pymongo import MongoClient
import psycopg2
from psycopg2.extras import RealDictCursor
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextProcessor:
    """
    整合文本處理器
    結合文本分塊、標籤匹配和向量化功能
    """
    
    def __init__(self, 
                 mongo_config: Dict[str, Any],
                 postgres_config: Dict[str, Any],
                 tag_csv_path: str = "TAG_info.csv",  # 修正預設路徑
                 embedding_model: str = "BAAI/bge-m3",
                 max_chunk_size: int = 1024) -> None:
        """
        初始化文本處理器
        
        Args:
            mongo_config: MongoDB 配置
            postgres_config: PostgreSQL 配置
            tag_csv_path: 標籤 CSV 檔案路徑
            embedding_model: 嵌入模型名稱
            max_chunk_size: 最大分塊大小
        """
        self.mongo_config = mongo_config
        self.postgres_config = postgres_config
        self.tag_csv_path = tag_csv_path
        self.embedding_model = embedding_model
        self.max_chunk_size = max_chunk_size
        
        # 初始化組件
        self.tag_mappings: Dict[str, str] = {}
        self.keyword_to_tags: Dict[str, Set[str]] = defaultdict(set)
        self.available_tags: Set[str] = set()  # 記錄所有可用的標籤
        self.embedding_model_instance: Optional[SentenceTransformer] = None
        
        # 載入標籤對應關係
        self.load_tag_mappings()
        
        # 初始化資料庫連接
        self.mongo_client: Optional[MongoClient] = None
        self.mongo_db: Optional[Any] = None
        self.postgres_conn: Optional[psycopg2.extensions.connection] = None
        
    def connect_mongodb(self) -> None:
        """連接到 MongoDB"""
        try:
            if self.mongo_config.get("password"):
                uri = f"mongodb://{self.mongo_config['username']}:{self.mongo_config['password']}@{self.mongo_config['host']}:{self.mongo_config['port']}"
            else:
                uri = f"mongodb://{self.mongo_config['host']}:{self.mongo_config['port']}"
            
            self.mongo_client = MongoClient(uri)
            self.mongo_db = self.mongo_client[self.mongo_config['database']]
            logger.info(f"成功連接到 MongoDB: {self.mongo_config['host']}:{self.mongo_config['port']}")
        except Exception as e:
            logger.error(f"MongoDB 連接失敗: {e}")
            raise
    
    def connect_postgres(self) -> None:
        """連接到 PostgreSQL"""
        try:
            self.postgres_conn = psycopg2.connect(
                host=self.postgres_config['host'],
                port=self.postgres_config['port'],
                database=self.postgres_config['database'],
                user=self.postgres_config['user'],
                password=self.postgres_config['password']
            )
            logger.info(f"成功連接到 PostgreSQL: {self.postgres_config['host']}:{self.postgres_config['port']}")
        except Exception as e:
            logger.error(f"PostgreSQL 連接失敗: {e}")
            raise
    
    def get_episode_metadata(self, episode_id: int) -> Dict[str, Any]:
        """
        從 PostgreSQL 獲取 episode 元資料
        
        Args:
            episode_id: Episode ID
            
        Returns:
            Episode 元資料字典
        """
        if self.postgres_conn is None:
            self.connect_postgres()
            
        try:
            with self.postgres_conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 查詢 episode 和 podcast 資訊
                query = """
                SELECT 
                    e.id as episode_id,
                    e.podcast_id,
                    e.title as episode_title,
                    p.name as podcast_name,
                    p.author,
                    p.category,
                    e.created_at
                FROM episodes e
                JOIN podcasts p ON e.podcast_id = p.id
                WHERE e.id = %s
                """
                
                cursor.execute(query, (episode_id,))
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                else:
                    logger.warning(f"找不到 episode_id {episode_id} 的元資料")
                    return {
                        'episode_id': episode_id,
                        'podcast_id': 0,
                        'episode_title': '',
                        'podcast_name': '',
                        'author': '',
                        'category': '',
                        'created_at': None
                    }
                    
        except Exception as e:
            logger.error(f"獲取 episode 元資料失敗: {e}")
            return {
                'episode_id': episode_id,
                'podcast_id': 0,
                'episode_title': '',
                'podcast_name': '',
                'author': '',
                'category': '',
                'created_at': None
            }
    
    def load_tag_mappings(self) -> None:
        """載入標籤對應關係"""
        try:
            if not Path(self.tag_csv_path).exists():
                logger.warning(f"標籤檔案不存在: {self.tag_csv_path}")
                self.create_default_tags()
                return
                
            df = pd.read_csv(self.tag_csv_path, header=1)  # 跳過第一行中文欄位名
            logger.info(f"成功載入標籤檔案: {self.tag_csv_path}")
            
            # 找到 TAG 欄位
            tag_col = None
            for col in df.columns:
                if str(col).strip().lower() == 'tag':
                    tag_col = col
                    break
                    
            if not tag_col:
                raise ValueError('找不到 TAG 欄位')
                
            # 相關詞欄位
            synonym_cols = [col for col in df.columns 
                           if col != tag_col and ("sync" in str(col).lower() or "相關" in str(col))]
            
            for _, row in df.iterrows():
                tag = str(row[tag_col]).strip()
                if not tag or tag == 'nan':
                    continue
                    
                # 將 TAG 本身也視為關鍵字
                self.keyword_to_tags[tag.lower()].add(tag)
                self.tag_mappings[tag] = tag
                self.available_tags.add(tag)  # 記錄可用標籤
                
                # 處理所有同義詞欄位
                for col in synonym_cols:
                    syn = str(row[col]).strip()
                    if syn and syn != 'nan':
                        self.keyword_to_tags[syn.lower()].add(tag)
                        
            logger.info(f"載入 {len(self.tag_mappings)} 個標籤對應關係，{len(self.keyword_to_tags)} 組關鍵字")
            
        except Exception as e:
            logger.error(f"載入標籤檔案失敗: {e}")
            self.create_default_tags()
    
    def create_default_tags(self) -> None:
        """建立預設標籤對應關係"""
        default_tags = {
            '人工智慧': ['AI', '機器學習', '深度學習', '自然語言處理'],
            '科技': ['技術', '創新', '數位化'],
            '商業': ['企業', '管理', '策略', '市場'],
            '教育': ['學習', '培訓', '知識', '技能'],
            '創業': ['新創', '商業模式', '投資'],
            '工作': ['職場', '效率', '生產力'],
            '時間管理': ['效率', '規劃', '優先級'],
            '領導力': ['管理', '團隊', '溝通'],
            '雲端運算': ['雲端', '技術架構', '基礎設施'],
            '區塊鏈': ['加密貨幣', '去中心化', '智能合約'],
            '半導體': ['晶片', '製造', '供應鏈'],
            '新創': ['創業', '創新', '投資'],
            '台灣產業': ['本土', '製造業', '科技業'],
            '全球供應鏈': ['國際', '貿易', '物流'],
            '生態系統': ['環境', '合作', '夥伴關係']
        }
        
        for keyword, tags in default_tags.items():
            self.keyword_to_tags[keyword.lower()] = set(tags)
            self.tag_mappings[keyword] = tags[0]
            self.available_tags.add(tags[0])  # 記錄可用標籤
            
        logger.info("使用預設標籤對應關係")
    
    def split_text_into_chunks(self, text: str) -> List[str]:
        """將文本分割成塊 (以空白或\n切分)"""
        if not text:
            return []
            
        # 先按換行符分割
        lines = text.split('\n')
        chunks = []
        current_chunk = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 如果當前行加上現有chunk超過最大長度，且當前chunk不為空，則保存當前chunk
            if len(current_chunk) + len(line) > self.max_chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                if current_chunk:
                    current_chunk += " " + line
                else:
                    current_chunk = line
                    
        # 處理最後一個chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        logger.info(f"文本切斷成 {len(chunks)} 個 chunks")
        return chunks
    
    def calculate_semantic_similarity(self, chunk: str, tags: List[str]) -> List[Tuple[str, float]]:
        """
        計算文本塊與標籤的語意相似度
        
        Args:
            chunk: 文本塊
            tags: 標籤列表
            
        Returns:
            標籤和相似度的元組列表，按相似度降序排列
        """
        if not tags:
            return []
            
        try:
            # 載入嵌入模型
            if self.embedding_model_instance is None:
                self.load_embedding_model()
            
            # 生成文本塊和標籤的嵌入向量
            texts = [chunk] + tags
            embeddings = self.embedding_model_instance.encode(
                texts, 
                normalize_embeddings=True,
                show_progress_bar=False
            )
            
            # 計算文本塊與每個標籤的相似度
            chunk_embedding = embeddings[0].reshape(1, -1)
            tag_embeddings = embeddings[1:]
            
            similarities = cosine_similarity(chunk_embedding, tag_embeddings)[0]
            
            # 返回標籤和相似度的元組列表，按相似度降序排列
            tag_similarities = list(zip(tags, similarities))
            tag_similarities.sort(key=lambda x: x[1], reverse=True)
            
            return tag_similarities
            
        except Exception as e:
            logger.error(f"計算語意相似度失敗: {e}")
            # 如果計算失敗，返回原始標籤列表
            return [(tag, 0.0) for tag in tags]
    
    def extract_tags_from_chunk(self, chunk: str) -> List[str]:
        """
        從文本塊中提取標籤 (0-3個)
        
        Args:
            chunk: 文本塊
            
        Returns:
            標籤列表 (最多3個，按語意相似度排序)
        """
        matched_tags = set()
        chunk_lower = chunk.lower()
        
        # 基於關鍵字匹配標籤
        for keyword, tags in self.keyword_to_tags.items():
            if keyword and keyword in chunk_lower:
                matched_tags.update(tags)
        
        # 應用標籤規則
        additional_tags = self.apply_tag_rules(chunk)
        matched_tags.update(additional_tags)
        
        # 如果沒有匹配到標籤，且tag_info中沒有相關標籤，才使用智能標籤提取
        if not matched_tags:
            smart_tags = self.extract_smart_tags(chunk)
            matched_tags.update(smart_tags)
        
        # 限制標籤數量為 0-3 個，按語意相似度排序
        tag_list = list(matched_tags)
        if len(tag_list) > 3:
            # 計算語意相似度並保留相似度最高的三個
            tag_similarities = self.calculate_semantic_similarity(chunk, tag_list)
            tag_list = [tag for tag, _ in tag_similarities[:3]]
            
        return tag_list
    
    def apply_tag_rules(self, chunk: str) -> Set[str]:
        """應用標籤規則"""
        additional_tags = set()
        chunk_lower = chunk.lower()
        
        rules = {
            r'\bai\b|\b人工智慧\b|\b機器學習\b': ['人工智慧', 'AI'],
            r'\b雲端\b|\bcloud\b': ['雲端運算'],
            r'\b區塊鏈\b|\bblockchain\b': ['區塊鏈'],
            r'\b創業\b|\b新創\b': ['創業', '新創'],
            r'\b領導\b|\b管理\b': ['領導力', '管理'],
            r'\b時間\b|\b效率\b': ['時間管理', '效率'],
            r'\b半導體\b|\b晶片\b': ['半導體'],
            r'\b台灣\b|\b本土\b': ['台灣產業'],
            r'\b全球\b|\b國際\b': ['全球供應鏈'],
            r'\b教育\b|\b學習\b': ['教育', '學習'],
            r'\b商業\b|\b企業\b': ['商業', '企業']
        }
        
        for pattern, tags in rules.items():
            if re.search(pattern, chunk_lower):
                additional_tags.update(tags)
                
        return additional_tags
    
    def extract_smart_tags(self, chunk: str) -> List[str]:
        """智能標籤提取 (僅當tag_info中沒有相關標籤時使用)"""
        # 檢查是否已有相關標籤
        chunk_lower = chunk.lower()
        for keyword in self.keyword_to_tags.keys():
            if keyword in chunk_lower:
                # 如果找到相關關鍵字，不進行智能標籤提取
                return []
        
        # 基於詞頻和關鍵詞的簡單智能標籤提取
        smart_tags = []
        
        # 常見主題關鍵詞
        topic_keywords = {
            '技術': ['技術', '科技', '創新', '開發', '程式', '軟體', '硬體'],
            '商業': ['商業', '企業', '市場', '營銷', '銷售', '客戶', '產品'],
            '管理': ['管理', '領導', '團隊', '組織', '策略', '規劃'],
            '創業': ['創業', '新創', '投資', '融資', '商業模式'],
            '教育': ['教育', '學習', '培訓', '知識', '技能', '發展'],
            '工作': ['工作', '職場', '職業', '就業', '薪資', '升遷']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in chunk_lower for keyword in keywords):
                smart_tags.append(topic)
                
        return smart_tags
    
    def load_embedding_model(self) -> None:
        """載入嵌入模型"""
        if self.embedding_model_instance is None:
            try:
                logger.info(f"載入嵌入模型: {self.embedding_model}")
                self.embedding_model_instance = SentenceTransformer(self.embedding_model)
                logger.info("嵌入模型載入成功")
            except Exception as e:
                logger.error(f"載入嵌入模型失敗: {e}")
                raise
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """生成文本嵌入向量"""
        self.load_embedding_model()
        
        try:
            embeddings = self.embedding_model_instance.encode(
                texts, 
                normalize_embeddings=True,
                show_progress_bar=True
            )
            logger.info(f"生成 {len(embeddings)} 個嵌入向量，維度: {embeddings.shape[1]}")
            return embeddings
        except Exception as e:
            logger.error(f"生成嵌入向量失敗: {e}")
            raise
    
    def fetch_mongodb_documents(self, collection_name: str, query: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """從 MongoDB 獲取文檔"""
        if self.mongo_db is None:
            self.connect_mongodb()
            
        try:
            collection = self.mongo_db[collection_name]
            query = query or {}
            
            if limit:
                documents = list(collection.find(query).limit(limit))
            else:
                documents = list(collection.find(query))
                
            logger.info(f"從 MongoDB 獲取 {len(documents)} 個文檔")
            return documents
        except Exception as e:
            logger.error(f"獲取 MongoDB 文檔失敗: {e}")
            raise
    
    def process_document(self, document: Dict[str, Any], text_field: str = 'content') -> List[Dict[str, Any]]:
        """處理單個文檔"""
        if text_field not in document:
            logger.warning(f"文檔缺少 {text_field} 欄位")
            return []
            
        text = document[text_field]
        chunks = self.split_text_into_chunks(text)
        processed_chunks = []
        
        # 獲取 episode 元資料
        episode_id = document.get('episode_id')
        episode_metadata = {}
        if episode_id:
            episode_metadata = self.get_episode_metadata(episode_id)
        
        for i, chunk in enumerate(chunks):
            tags = self.extract_tags_from_chunk(chunk)
            
            processed_chunk = {
                'chunk_id': f"{document.get('_id', 'unknown')}_{i}",
                'chunk_index': i,
                'chunk_text': chunk,
                'tags': tags,
                'source_document_id': str(document.get('_id')),
                'source_field': text_field,
                'chunk_length': len(chunk),
                'tag_count': len(tags),
                'metadata': {
                    'episode_id': episode_metadata.get('episode_id', episode_id),
                    'podcast_id': episode_metadata.get('podcast_id', 0),
                    'episode_title': episode_metadata.get('episode_title', ''),
                    'podcast_name': episode_metadata.get('podcast_name', ''),
                    'author': episode_metadata.get('author', ''),
                    'category': episode_metadata.get('category', ''),
                    'created_at': episode_metadata.get('created_at')
                }
            }
            processed_chunks.append(processed_chunk)
            
        logger.info(f"處理文檔 {document.get('_id')}，產生 {len(processed_chunks)} 個 chunks")
        return processed_chunks
    
    def process_collection(self, collection_name: str, text_field: str = 'content', 
                          query: Optional[Dict[str, Any]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """處理整個集合的文檔"""
        documents = self.fetch_mongodb_documents(collection_name, query, limit)
        all_processed_chunks = []
        
        for doc in documents:
            processed_chunks = self.process_document(doc, text_field)
            all_processed_chunks.extend(processed_chunks)
            
        logger.info(f"總共處理 {len(all_processed_chunks)} 個文本塊")
        return all_processed_chunks
    
    def get_tag_statistics(self) -> Dict[str, Any]:
        """獲取標籤統計資訊"""
        tag_counts = defaultdict(int)
        for tags in self.keyword_to_tags.values():
            for tag in tags:
                tag_counts[tag] += 1
                
        return {
            'total_keywords': len(self.keyword_to_tags),
            'total_unique_tags': len(tag_counts),
            'available_tags': list(self.available_tags),
            'tag_frequency': dict(tag_counts),
            'keyword_to_tags': dict(self.keyword_to_tags)
        }
    
    def export_tag_mappings(self, output_file: str = 'tag_mappings.json') -> None:
        """匯出標籤對應關係"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.tag_mappings, f, ensure_ascii=False, indent=2)
            logger.info(f"標籤對應關係已匯出到 {output_file}")
        except Exception as e:
            logger.error(f"匯出標籤對應關係失敗: {e}")
    
    def close(self) -> None:
        """關閉連接"""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("MongoDB 連接已關閉")
        
        if self.postgres_conn:
            self.postgres_conn.close()
            logger.info("PostgreSQL 連接已關閉")


def test_text_processor() -> None:
    """測試文本處理器"""
    # 測試配置
    mongo_config = {
        "host": "localhost",
        "port": 27017,
        "database": "podwise",
        "username": "bdse37",
        "password": "111111"
    }
    
    postgres_config = {
        "host": "localhost",
        "port": 5432,
        "database": "podcast",
        "user": "bdse37",
        "password": "111111"
    }
    
    processor = TextProcessor(mongo_config, postgres_config)
    
    # 測試文本處理
    test_text = """
    人工智慧技術正在快速發展，機器學習和深度學習已經成為現代科技的核心。
    企業需要擁抱這些新技術來提升競爭力。創業者應該關注AI領域的機會。
    雲端運算和區塊鏈技術也在改變商業模式。台灣的半導體產業在全球供應鏈中扮演重要角色。
    """
    
    chunks = processor.split_text_into_chunks(test_text)
    print(f"分塊結果: {len(chunks)} 個塊")
    
    for i, chunk in enumerate(chunks):
        tags = processor.extract_tags_from_chunk(chunk)
        print(f"塊 {i+1}: {tags} (數量: {len(tags)})")
    
    # 測試標籤統計
    stats = processor.get_tag_statistics()
    print(f"標籤統計: {stats['total_unique_tags']} 個唯一標籤")
    
    processor.close()


if __name__ == "__main__":
    test_text_processor() 