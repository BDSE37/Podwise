#!/usr/bin/env python3
"""
統一向量搜尋工具

整合所有向量搜尋相關功能：
- 增強型向量搜尋
- KNN 推薦算法
- 智能標籤提取
- 混合檢索策略
- 語意相似度計算

作者: Podwise Team
版本: 2.0.0
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    print("警告：pandas 未安裝，標籤匹配功能將不可用")
    pd = None

try:
    from pymilvus import connections, Collection, utility
except ImportError:
    print("警告：pymilvus 未安裝，向量搜尋功能將不可用")
    connections = None

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜尋結果數據類別"""
    id: str
    title: str
    content: str
    score: float
    category: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""


@dataclass
class PodcastItem:
    """Podcast 項目數據類別"""
    rss_id: str
    title: str
    description: str
    category: str
    vector: np.ndarray
    updated_at: str
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class RecommendationResult:
    """推薦結果數據類別"""
    recommendations: List[PodcastItem]
    total_found: int
    confidence: float
    reasoning: str
    processing_time: float


@dataclass
class TagMapping:
    """標籤映射結果"""
    original_tag: str
    mapped_tags: List[str]
    confidence: float
    method: str  # "exact", "similarity", "fuzzy"


@dataclass
class SmartTagResult:
    """智能標籤提取結果"""
    extracted_tags: List[str]
    mapped_tags: List[TagMapping]
    confidence: float
    processing_time: float
    method_used: List[str]


class BaseVectorSearch(ABC):
    """向量搜尋基礎抽象類別"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.collection_name = config.get("collection_name", "podcast_embeddings")
        self.host = config.get("host", "milvus")
        self.port = config.get("port", 19530)
        self.dimension = config.get("dimension", 1536)
        self.collection = None
    
    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """執行搜尋"""
        pass
    
    @abstractmethod
    def get_embedding(self, text: str) -> np.ndarray:
        """獲取文本嵌入向量"""
        pass


class MilvusVectorSearch(BaseVectorSearch):
    """Milvus 向量搜尋實現"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._connect_to_milvus()
    
    def _connect_to_milvus(self):
        """連接到 Milvus"""
        if connections is None:
            logger.warning("pymilvus 未安裝，無法使用 Milvus 向量搜尋")
            return
        
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info("成功連接到 Milvus")
            
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                self.collection.load()
                logger.info(f"載入集合: {self.collection_name}")
            else:
                logger.warning(f"集合不存在: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"連接到 Milvus 失敗: {str(e)}")
    
    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """執行 Milvus 向量搜尋"""
        if self.collection is None:
            return []
        
        try:
            query_vector = self.get_embedding(query)
            
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["title", "content", "category", "tags", "metadata"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append(SearchResult(
                        id=str(hit.id),
                        title=hit.entity.get("title", ""),
                        content=hit.entity.get("content", ""),
                        score=hit.score,
                        category=hit.entity.get("category", ""),
                        tags=hit.entity.get("tags", []),
                        metadata=hit.entity.get("metadata", {}),
                        source="milvus"
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Milvus 搜尋失敗: {str(e)}")
            return []
    
    def get_embedding(self, text: str) -> np.ndarray:
        """獲取文本嵌入向量（簡化實現）"""
        # 簡化的向量生成邏輯
        words = text.lower().split()
        vector = np.zeros(self.dimension)
        
        # 簡單的關鍵詞權重
        business_keywords = ["股票", "投資", "理財", "財經", "市場", "經濟"]
        education_keywords = ["學習", "技能", "成長", "職涯", "發展", "教育"]
        
        for word in words:
            if word in business_keywords:
                vector[0:self.dimension//2] += 0.1
            if word in education_keywords:
                vector[self.dimension//2:] += 0.1
        
        # 正規化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector


class KNNRecommender:
    """KNN 推薦器"""
    
    def __init__(self, k: int = 5, metric: str = "cosine"):
        self.k = k
        self.metric = metric
        self.podcast_items: List[PodcastItem] = []
        self.category_statistics: Dict[str, int] = {}
    
    def add_podcast_items(self, items: List[PodcastItem]) -> None:
        """添加 Podcast 項目"""
        self.podcast_items.extend(items)
        self._update_category_statistics()
    
    def _update_category_statistics(self) -> None:
        """更新分類統計"""
        self.category_statistics = {}
        for item in self.podcast_items:
            category = item.category
            self.category_statistics[category] = self.category_statistics.get(category, 0) + 1
    
    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """計算相似度"""
        if self.metric == "cosine":
            dot_product = float(np.dot(vec1, vec2))
            norm1 = float(np.linalg.norm(vec1))
            norm2 = float(np.linalg.norm(vec2))
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)
        elif self.metric == "euclidean":
            return 1.0 / (1.0 + float(np.linalg.norm(vec1 - vec2)))
        else:
            return 0.0
    
    def recommend(self, 
                 query_vector: np.ndarray, 
                 top_k: int = 5,
                 category_filter: Optional[str] = None) -> RecommendationResult:
        """執行推薦"""
        start_time = datetime.now()
        
        # 過濾項目
        filtered_items = self.podcast_items
        if category_filter:
            filtered_items = [item for item in self.podcast_items if item.category == category_filter]
        
        if not filtered_items:
            return RecommendationResult(
                recommendations=[],
                total_found=0,
                confidence=0.0,
                reasoning="沒有找到符合條件的項目",
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        
        # 計算相似度
        similarities = []
        for item in filtered_items:
            similarity = self._calculate_similarity(query_vector, item.vector)
            similarities.append((item, similarity))
        
        # 排序並取前 k 個
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_items = similarities[:top_k]
        
        # 轉換為 PodcastItem 並設置信心度
        recommendations = []
        for item, similarity in top_items:
            item.confidence = similarity
            recommendations.append(item)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return RecommendationResult(
            recommendations=recommendations,
            total_found=len(recommendations),
            confidence=top_items[0][1] if top_items else 0.0,
            reasoning=f"使用 {self.metric} 相似度計算，找到 {len(recommendations)} 個推薦",
            processing_time=processing_time
        )
    
    def get_category_statistics(self) -> Dict[str, int]:
        """獲取分類統計"""
        return self.category_statistics.copy()


class SmartTagExtractor:
    """智能標籤提取器"""
    
    def __init__(self, 
                 existing_tags_file: Optional[str] = None,
                 similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold
        self.existing_tags = self._load_existing_tags(existing_tags_file)
    
    def _load_existing_tags(self, tags_file: Optional[str]) -> Dict[str, List[str]]:
        """載入現有標籤"""
        if tags_file and os.path.exists(tags_file) and pd is not None:
            try:
                df = pd.read_csv(tags_file, encoding='utf-8')
                tags_dict = {}
                for _, row in df.iterrows():
                    category = str(row['類別'])
                    tag = str(row['TAG'])
                    if category not in tags_dict:
                        tags_dict[category] = []
                    tags_dict[category].append(tag)
                return tags_dict
            except Exception as e:
                logger.error(f"載入標籤檔案失敗: {e}")
        
        # 預設標籤
        return {
            "商業": ["股票", "投資", "理財", "財經", "市場", "經濟", "創業", "職場"],
            "教育": ["學習", "成長", "職涯", "心理", "溝通", "語言", "親子", "技能"]
        }
    
    def extract_basic_tags(self, query: str) -> List[str]:
        """提取基本標籤"""
        query_lower = query.lower()
        extracted_tags = []
        
        for category, tags in self.existing_tags.items():
            for tag in tags:
                if tag.lower() in query_lower:
                    extracted_tags.append(tag)
        
        return extracted_tags
    
    def find_missing_tags(self, extracted_tags: List[str]) -> List[str]:
        """找出缺失的標籤"""
        all_tags = []
        for tags in self.existing_tags.values():
            all_tags.extend(tags)
        
        missing_tags = []
        for tag in all_tags:
            if tag not in extracted_tags:
                missing_tags.append(tag)
        
        return missing_tags
    
    def fuzzy_match(self, query_tag: str) -> List[str]:
        """模糊匹配"""
        matches = []
        query_lower = query_tag.lower()
        
        for category, tags in self.existing_tags.items():
            for tag in tags:
                tag_lower = tag.lower()
                # 簡單的字符相似度計算
                similarity = self._calculate_char_similarity(query_lower, tag_lower)
                if similarity >= self.similarity_threshold:
                    matches.append(tag)
        
        return matches
    
    def _calculate_char_similarity(self, str1: str, str2: str) -> float:
        """計算字符相似度"""
        if not str1 or not str2:
            return 0.0
        
        # 使用編輯距離計算相似度
        len1, len2 = len(str1), len(str2)
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if str1[i-1] == str2[j-1]:
                    matrix[i][j] = matrix[i-1][j-1]
                else:
                    matrix[i][j] = min(
                        matrix[i-1][j] + 1,    # 刪除
                        matrix[i][j-1] + 1,    # 插入
                        matrix[i-1][j-1] + 1   # 替換
                    )
        
        max_len = max(len1, len2)
        if max_len == 0:
            return 1.0
        
        return 1.0 - (matrix[len1][len2] / max_len)
    
    def extract_smart_tags(self, query: str, context: str = "") -> SmartTagResult:
        """提取智能標籤"""
        start_time = datetime.now()
        
        # 提取基本標籤
        basic_tags = self.extract_basic_tags(query)
        
        # 找出缺失標籤
        missing_tags = self.find_missing_tags(basic_tags)
        
        # 模糊匹配
        mapped_tags = []
        for missing_tag in missing_tags[:10]:  # 限制數量
            fuzzy_matches = self.fuzzy_match(missing_tag)
            if fuzzy_matches:
                mapped_tags.append(TagMapping(
                    original_tag=missing_tag,
                    mapped_tags=fuzzy_matches,
                    confidence=0.8,
                    method="fuzzy"
                ))
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return SmartTagResult(
            extracted_tags=basic_tags,
            mapped_tags=mapped_tags,
            confidence=len(basic_tags) / 10.0,  # 簡化的信心度計算
            processing_time=processing_time,
            method_used=["basic_extraction", "fuzzy_matching"]
        )


class UnifiedVectorSearch:
    """統一向量搜尋工具"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # 初始化各組件
        self.milvus_search = MilvusVectorSearch(config.get("milvus", {}))
        self.knn_recommender = KNNRecommender(
            k=config.get("knn_k", 5),
            metric=config.get("knn_metric", "cosine")
        )
        self.tag_extractor = SmartTagExtractor(
            existing_tags_file=config.get("tags_file"),
            similarity_threshold=config.get("similarity_threshold", 0.7)
        )
        
        # 載入示例數據
        self._load_sample_data()
        
        logger.info("統一向量搜尋工具初始化完成")
    
    def _load_sample_data(self):
        """載入示例數據"""
        sample_items = [
            PodcastItem(
                rss_id="rss_001",
                title="股癌 EP310",
                description="台股投資分析與市場趨勢",
                category="商業",
                tags=["股票", "投資", "台股", "財經"],
                vector=np.array([0.8, 0.6, 0.9, 0.7, 0.8, 0.6, 0.9, 0.7]),
                updated_at="2025-01-15",
                confidence=0.9
            ),
            PodcastItem(
                rss_id="rss_002",
                title="大人學 EP110",
                description="職涯發展與個人成長指南",
                category="教育",
                tags=["職涯", "成長", "技能", "學習"],
                vector=np.array([0.3, 0.8, 0.4, 0.9, 0.3, 0.8, 0.4, 0.9]),
                updated_at="2025-01-14",
                confidence=0.85
            ),
            PodcastItem(
                rss_id="rss_003",
                title="財報狗 Podcast",
                description="財報分析與投資策略",
                category="商業",
                tags=["財報", "投資", "分析", "策略"],
                vector=np.array([0.9, 0.5, 0.8, 0.6, 0.9, 0.5, 0.8, 0.6]),
                updated_at="2025-01-13",
                confidence=0.88
            )
        ]
        
        self.knn_recommender.add_podcast_items(sample_items)
    
    async def search(self, 
                    query: str, 
                    top_k: int = 5,
                    use_milvus: bool = True,
                    use_knn: bool = True,
                    use_tags: bool = True) -> Dict[str, Any]:
        """
        執行統一搜尋
        
        Args:
            query: 查詢文字
            top_k: 返回結果數量
            use_milvus: 是否使用 Milvus 搜尋
            use_knn: 是否使用 KNN 推薦
            use_tags: 是否使用標籤提取
            
        Returns:
            Dict[str, Any]: 搜尋結果
        """
        results = {
            "query": query,
            "milvus_results": [],
            "knn_results": None,
            "tag_results": None,
            "combined_results": [],
            "processing_time": 0.0
        }
        
        start_time = datetime.now()
        
        # 1. Milvus 向量搜尋
        if use_milvus:
            results["milvus_results"] = await self.milvus_search.search(query, top_k)
        
        # 2. KNN 推薦
        if use_knn:
            query_vector = self.milvus_search.get_embedding(query)
            knn_result = self.knn_recommender.recommend(query_vector, top_k=top_k)
            results["knn_results"] = knn_result
        
        # 3. 智能標籤提取
        if use_tags:
            tag_result = self.tag_extractor.extract_smart_tags(query)
            results["tag_results"] = tag_result
        
        # 4. 合併結果
        results["combined_results"] = self._combine_results(
            results["milvus_results"],
            results["knn_results"],
            results["tag_results"]
        )
        
        results["processing_time"] = (datetime.now() - start_time).total_seconds()
        
        return results
    
    def _combine_results(self, 
                        milvus_results: List[SearchResult],
                        knn_result: Optional[RecommendationResult],
                        tag_result: Optional[SmartTagResult]) -> List[Dict[str, Any]]:
        """合併搜尋結果"""
        combined = []
        
        # 添加 Milvus 結果
        for result in milvus_results:
            combined.append({
                "id": result.id,
                "title": result.title,
                "content": result.content,
                "score": result.score,
                "category": result.category,
                "tags": result.tags,
                "source": "milvus",
                "type": "vector_search"
            })
        
        # 添加 KNN 結果
        if knn_result and knn_result.recommendations:
            for item in knn_result.recommendations:
                combined.append({
                    "id": item.rss_id,
                    "title": item.title,
                    "content": item.description,
                    "score": item.confidence,
                    "category": item.category,
                    "tags": item.tags,
                    "source": "knn",
                    "type": "recommendation"
                })
        
        # 按分數排序並去重
        combined.sort(key=lambda x: x["score"], reverse=True)
        
        # 簡單去重（基於 ID）
        seen_ids = set()
        unique_results = []
        for result in combined:
            if result["id"] not in seen_ids:
                seen_ids.add(result["id"])
                unique_results.append(result)
        
        return unique_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        return {
            "milvus_connected": self.milvus_search.collection is not None,
            "knn_items_count": len(self.knn_recommender.podcast_items),
            "category_statistics": self.knn_recommender.get_category_statistics(),
            "available_tags": len(self.tag_extractor.existing_tags)
        }


# 向後相容性別名
EnhancedVectorSearchTool = UnifiedVectorSearch
JobSearchRAG = UnifiedVectorSearch


# 使用範例
if __name__ == "__main__":
    # 配置
    config = {
        "milvus": {
            "collection_name": "podcast_embeddings",
            "host": "localhost",
            "port": 19530,
            "dimension": 8
        },
        "knn_k": 5,
        "knn_metric": "cosine",
        "similarity_threshold": 0.7,
        "tags_file": "scripts/csv/TAG_info.csv"
    }
    
    # 創建統一搜尋工具
    search_tool = UnifiedVectorSearch(config)
    
    # 測試搜尋
    import asyncio
    
    async def test_search():
        query = "我想學習投資理財，有什麼推薦的 Podcast 嗎？"
        results = await search_tool.search(query, top_k=3)
        
        print(f"查詢: {query}")
        print(f"處理時間: {results['processing_time']:.3f} 秒")
        print(f"合併結果數量: {len(results['combined_results'])}")
        
        for i, result in enumerate(results['combined_results'][:3]):
            print(f"\n{i+1}. {result['title']}")
            print(f"   分數: {result['score']:.3f}")
            print(f"   類別: {result['category']}")
            print(f"   來源: {result['source']}")
            print(f"   標籤: {', '.join(result['tags'])}")
    
    asyncio.run(test_search())
