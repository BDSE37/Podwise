#!/usr/bin/env python3
"""
統一 RAG 評估器 - Podwise 專案

整合功能：
1. 基礎 RAG 評估（Baseline、Naive RAG、Ragas）
2. 增強版評估（Milvus 檢索、本地/OpenAI LLM 對比）
3. Podwise 專用功能（向量資料庫整合）
4. ihower 框架整合
5. 提示詞模板整合

作者: Podwise Team
版本: 3.0.0
"""

import os
import sys
import json
import time
import logging
import asyncio
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import hashlib
from pathlib import Path

# 添加路徑以便導入
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 嘗試導入 Podwise 專案相關模組
try:
    from config.integrated_config import get_config
    PODWISE_CONFIG_AVAILABLE = True
except ImportError:
    PODWISE_CONFIG_AVAILABLE = False
    logger.warning("Podwise 配置模組未找到，使用預設配置")

try:
    from config.prompt_templates import get_prompt_template, format_prompt
    PROMPT_TEMPLATES_AVAILABLE = True
except ImportError:
    PROMPT_TEMPLATES_AVAILABLE = False
    logger.warning("提示詞模板模組未找到，使用預設模板")

# 預設配置
def get_default_config():
    class Config:
        class Database:
            milvus_host = os.getenv("MILVUS_HOST", "worker3")
            milvus_port = int(os.getenv("MILVUS_PORT", "19530"))
            milvus_collection = os.getenv("MILVUS_COLLECTION", "podcast_chunks")
        class API:
            openai_api_key = os.getenv("OPENAI_API_KEY", "")
        database = Database()
        api = API()
    return Config()

@dataclass
class EvaluationResult:
    """評估結果數據類別"""
    question: str
    answer: str
    confidence: float
    factuality: float
    relevance: float
    coherence: float
    inference_time: float
    token_count: int
    model_name: str
    retrieval_method: str
    sources: List[Dict[str, Any]]

@dataclass
class ComparisonResult:
    """對比結果數據類別"""
    question: str
    local_llm_result: EvaluationResult
    openai_result: EvaluationResult
    comparison_metrics: Dict[str, float]

class MilvusOptimizedSearch:
    """優化的 Milvus 搜尋服務"""
    
    def __init__(self):
        """初始化優化的 Milvus 搜尋"""
        self.config = get_config() if PODWISE_CONFIG_AVAILABLE else get_default_config()
        self.collection = None
        self.is_connected = False
        self._connect()
        
    def _connect(self):
        """連接到 Milvus"""
        try:
            from pymilvus import connections, Collection, utility
            
            # 連接到 Milvus
            connections.connect(
                alias="default",
                host=self.config.database.milvus_host,
                port=self.config.database.milvus_port
            )
            
            # 檢查集合是否存在
            collection_name = self.config.database.milvus_collection
            if utility.has_collection(collection_name):
                self.collection = Collection(collection_name)
                self.is_connected = True
                
                # 檢查集合統計資訊
                stats = self.collection.num_entities
                logger.info(f"✅ Milvus 集合 '{collection_name}' 連接成功，向量數量: {stats}")
                
            else:
                logger.warning(f"⚠️ Milvus 集合 '{collection_name}' 不存在")
                
        except ImportError:
            logger.warning("⚠️ pymilvus 未安裝")
        except Exception as e:
            logger.error(f"❌ Milvus 連接失敗: {e}")
    
    async def search(self, query: str, top_k: int = 10, nprobe: int = 16) -> List[Dict[str, Any]]:
        """執行優化的向量搜尋"""
        try:
            if not self.is_connected or self.collection is None:
                logger.warning("Milvus 未連接，返回空結果")
                return []
            
            # 文本向量化（使用簡單的哈希方法作為示例）
            embedding = self._text_to_vector(query)
            if not embedding:
                return []
            
            # 載入集合
            self.collection.load()
            
            # 優化的搜尋參數
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": nprobe}
            }
            
            # 執行搜尋
            results = self.collection.search(
                data=[embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["chunk_id", "chunk_text", "tags", "podcast_name", "episode_title", "category", "language"]
            )
            
            # 格式化結果
            formatted_results = []
            for hits in results:
                for hit in hits:
                    # 解析 tags 欄位
                    tags = []
                    try:
                        if hasattr(hit, 'entity') and hit.entity:
                            tags_data = hit.entity.get("tags")
                            if tags_data:
                                if isinstance(tags_data, str):
                                    tags = json.loads(tags_data)
                                else:
                                    tags = tags_data
                    except:
                        tags = []
                    
                    # 安全獲取實體數據
                    entity_data = {}
                    chunk_text = ""
                    if hasattr(hit, 'entity') and hit.entity:
                        try:
                            entity_data = {
                                "podcast_name": hit.entity.get("podcast_name") or "",
                                "episode_title": hit.entity.get("episode_title") or "",
                                "category": hit.entity.get("category") or "",
                                "language": hit.entity.get("language") or "",
                                "chunk_id": hit.entity.get("chunk_id") or ""
                            }
                            chunk_text = hit.entity.get("chunk_text") or ""
                        except Exception as e:
                            logger.warning(f"獲取實體數據失敗: {e}")
                            # 使用屬性訪問
                            try:
                                entity_data = {
                                    "podcast_name": getattr(hit.entity, "podcast_name", ""),
                                    "episode_title": getattr(hit.entity, "episode_title", ""),
                                    "category": getattr(hit.entity, "category", ""),
                                    "language": getattr(hit.entity, "language", ""),
                                    "chunk_id": getattr(hit.entity, "chunk_id", "")
                                }
                                chunk_text = getattr(hit.entity, "chunk_text", "")
                            except:
                                pass
                    
                    formatted_results.append({
                        "chunk_text": chunk_text,
                        "similarity": float(hit.score),
                        "metadata": entity_data,
                        "tags": tags
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Milvus 搜尋失敗: {e}")
            return []
    
    def _text_to_vector(self, text: str) -> Optional[List[float]]:
        """將文本轉換為向量（簡化版本）"""
        try:
            # 使用簡單的哈希方法作為示例
            # 實際使用時應該使用真正的嵌入模型
            hash_obj = hashlib.md5(text.encode('utf-8'))
            hash_hex = hash_obj.hexdigest()
            
            # 將哈希轉換為 1536 維向量（模擬 OpenAI 嵌入維度）
            vector = []
            for i in range(0, len(hash_hex), 2):
                if len(vector) >= 1536:
                    break
                hex_pair = hash_hex[i:i+2]
                vector.append(int(hex_pair, 16) / 255.0)
            
            # 填充到 1536 維
            while len(vector) < 1536:
                vector.append(0.0)
            
            return vector[:1536]
            
        except Exception as e:
            logger.error(f"文本向量化失敗: {e}")
            return None

class PodwiseVectorSearch:
    """Podwise 向量資料庫搜尋模組"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化向量搜尋引擎
        
        Args:
            data_dir: 向量資料目錄路徑，如果為 None 則自動檢測
        """
        if data_dir is None:
            # 自動檢測路徑
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            data_dir = project_root / "backend" / "vector_pipeline" / "data" / "stage4_embedding_prep"
        
        self.data_dir = Path(data_dir)
        self.chunks_data = []
        self.embeddings = []
        self.chunk_texts = []
        self.metadata = []
        
        # 載入所有向量資料
        self._load_vector_data()
        
    def _load_vector_data(self):
        """載入所有 RSS 目錄中的向量資料"""
        logger.info(f"開始載入向量資料從: {self.data_dir}")
        
        total_chunks = 0
        
        # 遍歷所有 RSS 目錄
        for rss_dir in self.data_dir.iterdir():
            if rss_dir.is_dir() and rss_dir.name.startswith("RSS_"):
                logger.info(f"載入目錄: {rss_dir.name}")
                
                # 載入該目錄下的所有 JSON 文件
                for json_file in rss_dir.glob("*.json"):
                    if not json_file.name.endswith(".backup"):
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                            # 處理每個 chunk
                            for chunk in data:
                                if isinstance(chunk, dict) and 'chunk_text' in chunk and 'embedding' in chunk:
                                    self.chunks_data.append(chunk)
                                    self.chunk_texts.append(chunk['chunk_text'])
                                    self.embeddings.append(chunk['embedding'])
                                    
                                    # 提取元資料
                                    metadata = {
                                        'chunk_id': chunk.get('chunk_id'),
                                        'episode_id': chunk.get('episode_id'),
                                        'podcast_id': chunk.get('podcast_id'),
                                        'podcast_name': chunk.get('podcast_name'),
                                        'episode_title': chunk.get('episode_title'),
                                        'author': chunk.get('author'),
                                        'category': chunk.get('category'),
                                        'published_date': chunk.get('published_date'),
                                        'rss_dir': rss_dir.name
                                    }
                                    self.metadata.append(metadata)
                                    
                                    total_chunks += 1
                                    
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON 解析錯誤，跳過文件 {json_file}: {str(e)}")
                            continue
                        except Exception as e:
                            logger.warning(f"載入文件失敗 {json_file}: {str(e)}")
                            continue
        
        # 轉換為 numpy 陣列以提高效能
        if self.embeddings:
            self.embeddings = np.array(self.embeddings)
            logger.info(f"成功載入 {total_chunks} 個 chunks，向量維度: {self.embeddings.shape}")
        else:
            logger.warning("未找到任何向量資料")
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """執行向量相似性搜尋"""
        if not self.embeddings.size:
            logger.warning("向量資料庫為空")
            return []
        
        try:
            # 計算餘弦相似度
            query_vector = np.array(query_embedding).reshape(1, -1)
            similarities = self._cosine_similarity(query_vector, self.embeddings)
            
            # 獲取 top-k 結果
            top_indices = np.argsort(similarities[0])[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                similarity = similarities[0][idx]
                result = {
                    'chunk_text': self.chunk_texts[idx],
                    'similarity': float(similarity),
                    'metadata': self.metadata[idx]
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"向量搜尋失敗: {str(e)}")
            return []
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """計算餘弦相似度"""
        # 正規化向量
        a_norm = a / np.linalg.norm(a, axis=1, keepdims=True)
        b_norm = b / np.linalg.norm(b, axis=1, keepdims=True)
        
        # 計算相似度
        return np.dot(a_norm, b_norm.T)
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取向量資料庫統計資訊"""
        if not self.embeddings.size:
            return {"total_chunks": 0, "vector_dimension": 0}
        
        # 統計播客數量
        podcast_ids = set()
        episode_ids = set()
        categories = set()
        
        for metadata in self.metadata:
            if metadata.get('podcast_id'):
                podcast_ids.add(metadata['podcast_id'])
            if metadata.get('episode_id'):
                episode_ids.add(metadata['episode_id'])
            if metadata.get('category'):
                categories.add(metadata['category'])
        
        return {
            "total_chunks": len(self.chunks_data),
            "vector_dimension": self.embeddings.shape[1] if self.embeddings.size else 0,
            "total_podcasts": len(podcast_ids),
            "total_episodes": len(episode_ids),
            "categories": list(categories),
            "data_loaded": True
        }

class LocalLLMService:
    """本地 LLM 服務"""
    
    def __init__(self, model_path: str = None):
        """初始化本地 LLM 服務"""
        if model_path is None:
            # 自動檢測路徑
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent.parent
            model_path = project_root / "Qwen2.5-Taiwan-7B-Instruct"
        
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.prompt_templates = {}
        self._load_prompt_templates()
        self._load_model()
    
    def _load_prompt_templates(self):
        """載入提示詞模板"""
        if PROMPT_TEMPLATES_AVAILABLE:
            try:
                # 載入 Podwise 提示詞模板
                self.prompt_templates = {
                    "answer_generation": get_prompt_template("answer_generation"),
                    "faq_fallback": get_prompt_template("faq_fallback"),
                    "default_fallback": get_prompt_template("default_fallback")
                }
                logger.info("✅ 成功載入 Podwise 提示詞模板")
            except Exception as e:
                logger.warning(f"載入 Podwise 提示詞模板失敗: {e}")
                self._load_default_templates()
        else:
            self._load_default_templates()
    
    def _load_default_templates(self):
        """載入預設提示詞模板"""
        self.prompt_templates = {
            "answer_generation": """嗨嗨👋 想了解「{question}」嗎？以下是相關的精彩節目：

🎧《模擬本地 LLM 推薦節目》第 2 集：〈商業分析〉
👉 這是一個模擬的本地 LLM 回應，基於 prompt_templates.py 格式

💡 建議：
- 這是一個模擬回應
- 實際使用時會載入真實的 Qwen2.5-Taiwan-7B-Instruct 模型
- 會根據您的問題提供相關的 Podcast 推薦

希望這個回應對您有幫助！😊""",
            
            "faq_fallback": """嗨嗨👋 關於「{question}」，這是一個常見問題！

📚 常見解答：
- 這是一個 FAQ 備援回應
- 基於 Podwise 的常見問題資料庫
- 提供標準化的解答格式

💡 小提醒：如果需要更詳細的資訊，可以嘗試重新描述您的問題喔！""",
            
            "default_fallback": """嗨嗨👋 抱歉，我目前無法完全理解您的問題「{question}」

🤔 建議您可以：
- 重新描述您的問題
- 提供更多上下文資訊
- 嘗試不同的表達方式

我會努力為您提供更好的服務！😊"""
        }
        logger.info("✅ 載入預設提示詞模板")
    
    def _load_model(self):
        """載入本地模型（模擬版本）"""
        try:
            # 這裡應該是實際的模型載入邏輯
            # 目前使用模擬版本
            logger.info(f"✅ 模擬載入本地模型: {self.model_path}")
            self.model = "mock_model"
            self.tokenizer = "mock_tokenizer"
        except Exception as e:
            logger.warning(f"本地模型載入失敗: {e}")
            self.model = None
            self.tokenizer = None
    
    async def generate_answer(self, prompt: str, context: str = "") -> Tuple[str, float, int]:
        """生成回答"""
        try:
            start_time = time.time()
            
            # 選擇合適的模板
            if "推薦" in prompt or "podcast" in prompt.lower():
                template = self.prompt_templates.get("answer_generation", self.prompt_templates["default_fallback"])
            elif any(keyword in prompt for keyword in ["什麼", "如何", "為什麼"]):
                template = self.prompt_templates.get("faq_fallback", self.prompt_templates["default_fallback"])
            else:
                template = self.prompt_templates.get("default_fallback", self.prompt_templates["default_fallback"])
            
            # 格式化提示詞
            if PROMPT_TEMPLATES_AVAILABLE:
                try:
                    formatted_prompt = format_prompt(template, question=prompt, context=context)
                except:
                    formatted_prompt = template.format(question=prompt, context=context)
            else:
                formatted_prompt = template.format(question=prompt, context=context)
            
            # 模擬生成回答
            answer = formatted_prompt
            
            # 計算時間和 token 數
            inference_time = time.time() - start_time
            token_count = len(answer.split())
            
            return answer, inference_time, token_count
            
        except Exception as e:
            logger.error(f"本地 LLM 生成失敗: {e}")
            return "本地 LLM 未載入", 0.0, 0

class OpenAIService:
    """OpenAI 服務"""
    
    def __init__(self):
        """初始化 OpenAI 服務"""
        self.config = get_config() if PODWISE_CONFIG_AVAILABLE else get_default_config()
        self.client = None
        self.prompt_templates = {}
        self._setup_client()
        self._load_prompt_templates()
    
    def _setup_client(self):
        """設定 OpenAI 客戶端"""
        try:
            from openai import OpenAI
            
            api_key = self.config.api.openai_api_key
            if api_key and api_key != "your_openai_api_key_here":
                self.client = OpenAI(api_key=api_key)
                logger.info("✅ OpenAI 客戶端初始化成功")
            else:
                logger.warning("⚠️ OpenAI API Key 未設定或無效")
                self.client = None
                
        except ImportError:
            logger.warning("⚠️ openai 套件未安裝")
            self.client = None
        except Exception as e:
            logger.error(f"❌ OpenAI 客戶端初始化失敗: {e}")
            self.client = None
    
    def _load_prompt_templates(self):
        """載入提示詞模板"""
        if PROMPT_TEMPLATES_AVAILABLE:
            try:
                # 載入 Podwise 提示詞模板
                self.prompt_templates = {
                    "answer_generation": get_prompt_template("answer_generation"),
                    "faq_fallback": get_prompt_template("faq_fallback"),
                    "default_fallback": get_prompt_template("default_fallback")
                }
                logger.info("✅ 成功載入 Podwise 提示詞模板")
            except Exception as e:
                logger.warning(f"載入 Podwise 提示詞模板失敗: {e}")
                self._load_default_templates()
        else:
            self._load_default_templates()
    
    def _load_default_templates(self):
        """載入預設提示詞模板"""
        self.prompt_templates = {
            "answer_generation": """嗨嗨👋 想了解「{question}」嗎？以下是相關的精彩節目：

🎧《模擬 OpenAI 推薦節目》第 5 集：〈深度學習〉
👉 這是一個模擬的 OpenAI 回應，基於 prompt_templates.py 格式

💡 建議：
- 這是一個模擬回應
- 實際使用時會調用 OpenAI API
- 會根據您的問題提供相關的 Podcast 推薦

希望這個回應對您有幫助！😊""",
            
            "faq_fallback": """嗨嗨👋 關於「{question}」，這是一個常見問題！

📚 常見解答：
- 這是一個 FAQ 備援回應
- 基於 Podwise 的常見問題資料庫
- 提供標準化的解答格式

💡 小提醒：如果需要更詳細的資訊，可以嘗試重新描述您的問題喔！""",
            
            "default_fallback": """嗨嗨👋 抱歉，我目前無法完全理解您的問題「{question}」

🤔 建議您可以：
- 重新描述您的問題
- 提供更多上下文資訊
- 嘗試不同的表達方式

我會努力為您提供更好的服務！😊"""
        }
        logger.info("✅ 載入預設提示詞模板")
    
    async def generate_answer(self, prompt: str, context: str = "") -> Tuple[str, float, int]:
        """生成回答"""
        try:
            if not self.client:
                return "生成失敗: OpenAI 客戶端未初始化", 0.0, 0
            
            start_time = time.time()
            
            # 選擇合適的模板
            if "推薦" in prompt or "podcast" in prompt.lower():
                template = self.prompt_templates.get("answer_generation", self.prompt_templates["default_fallback"])
            elif any(keyword in prompt for keyword in ["什麼", "如何", "為什麼"]):
                template = self.prompt_templates.get("faq_fallback", self.prompt_templates["default_fallback"])
            else:
                template = self.prompt_templates.get("default_fallback", self.prompt_templates["default_fallback"])
            
            # 格式化提示詞
            if PROMPT_TEMPLATES_AVAILABLE:
                try:
                    formatted_prompt = format_prompt(template, question=prompt, context=context)
                except:
                    formatted_prompt = template.format(question=prompt, context=context)
            else:
                formatted_prompt = template.format(question=prompt, context=context)
            
            # 調用 OpenAI API
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個專業的 Podcast 推薦助手，專門為用戶推薦相關的 Podcast 節目。"},
                    {"role": "user", "content": formatted_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            
            # 計算時間和 token 數
            inference_time = time.time() - start_time
            token_count = response.usage.total_tokens if hasattr(response, 'usage') else len(answer.split())
            
            return answer, inference_time, token_count
            
        except Exception as e:
            logger.error(f"OpenAI 生成失敗: {e}")
            return f"生成失敗: {str(e)}", 0.0, 0

class UnifiedRAGEvaluator:
    """統一 RAG 評估器"""
    
    def __init__(self, use_mock_services: bool = True):
        """初始化統一評估器"""
        self.use_mock_services = use_mock_services
        
        # 初始化搜尋服務
        self.milvus_search = MilvusOptimizedSearch()
        self.podwise_search = PodwiseVectorSearch()
        
        # 初始化 LLM 服務
        if use_mock_services:
            self.local_llm_service = LocalLLMService()
            self.openai_service = OpenAIService()
        else:
            # 實際服務初始化
            self.local_llm_service = LocalLLMService()
            self.openai_service = OpenAIService()
        
        logger.info("✅ 統一 RAG 評估器初始化完成")
    
    async def evaluate_single_question(self, question: str) -> ComparisonResult:
        """評估單個問題"""
        try:
            # 執行向量搜尋
            search_results = await self.milvus_search.search(question, top_k=5)
            
            # 構建上下文
            context = self._build_context(search_results)
            
            # 生成回答
            local_answer, local_time, local_tokens = await self.local_llm_service.generate_answer(question, context)
            openai_answer, openai_time, openai_tokens = await self.openai_service.generate_answer(question, context)
            
            # 計算指標
            local_confidence = self._calculate_confidence(local_answer, search_results)
            openai_confidence = self._calculate_confidence(openai_answer, search_results)
            
            local_factuality = self._calculate_factuality(local_answer, search_results)
            openai_factuality = self._calculate_factuality(openai_answer, search_results)
            
            local_relevance = self._calculate_relevance(local_answer, question)
            openai_relevance = self._calculate_relevance(openai_answer, question)
            
            local_coherence = self._calculate_coherence(local_answer)
            openai_coherence = self._calculate_coherence(openai_answer)
            
            # 創建結果對象
            local_result = EvaluationResult(
                question=question,
                answer=local_answer,
                confidence=local_confidence,
                factuality=local_factuality,
                relevance=local_relevance,
                coherence=local_coherence,
                inference_time=local_time,
                token_count=local_tokens,
                model_name="Qwen2.5-Taiwan-7B-Instruct",
                retrieval_method="Milvus",
                sources=search_results
            )
            
            openai_result = EvaluationResult(
                question=question,
                answer=openai_answer,
                confidence=openai_confidence,
                factuality=openai_factuality,
                relevance=openai_relevance,
                coherence=openai_coherence,
                inference_time=openai_time,
                token_count=openai_tokens,
                model_name="GPT-3.5-Turbo",
                retrieval_method="Milvus",
                sources=search_results
            )
            
            # 計算對比指標
            comparison_metrics = {
                "confidence_diff": local_confidence - openai_confidence,
                "factuality_diff": local_factuality - openai_factuality,
                "relevance_diff": local_relevance - openai_relevance,
                "coherence_diff": local_coherence - openai_coherence,
                "speed_ratio": local_time / openai_time if openai_time > 0 else 0,
                "token_ratio": local_tokens / openai_tokens if openai_tokens > 0 else 0
            }
            
            return ComparisonResult(
                question=question,
                local_llm_result=local_result,
                openai_result=openai_result,
                comparison_metrics=comparison_metrics
            )
            
        except Exception as e:
            logger.error(f"評估問題失敗: {e}")
            # 返回錯誤結果
            error_result = EvaluationResult(
                question=question,
                answer=f"評估失敗: {str(e)}",
                confidence=0.0,
                factuality=0.0,
                relevance=0.0,
                coherence=0.0,
                inference_time=0.0,
                token_count=0,
                model_name="Error",
                retrieval_method="Error",
                sources=[]
            )
            
            return ComparisonResult(
                question=question,
                local_llm_result=error_result,
                openai_result=error_result,
                comparison_metrics={}
            )
    
    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """構建上下文"""
        if not search_results:
            return ""
        
        context_parts = []
        for i, result in enumerate(search_results[:3]):  # 只使用前3個結果
            chunk_text = result.get("chunk_text", "")
            metadata = result.get("metadata", {})
            podcast_name = metadata.get("podcast_name", "未知播客")
            episode_title = metadata.get("episode_title", "未知節目")
            
            context_parts.append(f"[{i+1}] {podcast_name} - {episode_title}: {chunk_text[:200]}...")
        
        return "\n\n".join(context_parts)
    
    def _calculate_confidence(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """計算信心度"""
        if not answer or answer.startswith("生成失敗") or answer.startswith("評估失敗"):
            return 0.0
        
        # 基於回答長度和來源數量的簡單信心度計算
        base_confidence = min(1.0, len(answer) / 100.0)
        source_confidence = min(1.0, len(sources) / 5.0)
        
        return (base_confidence + source_confidence) / 2.0
    
    def _calculate_factuality(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """計算事實性"""
        if not answer or answer.startswith("生成失敗") or answer.startswith("評估失敗"):
            return 0.0
        
        # 基於來源數量的簡單事實性計算
        return min(1.0, len(sources) / 3.0)
    
    def _calculate_relevance(self, answer: str, question: str) -> float:
        """計算相關性"""
        if not answer or answer.startswith("生成失敗") or answer.startswith("評估失敗"):
            return 0.0
        
        # 簡單的關鍵詞匹配
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        
        if not question_words:
            return 0.0
        
        overlap = len(question_words.intersection(answer_words))
        return min(1.0, overlap / len(question_words))
    
    def _calculate_coherence(self, answer: str) -> float:
        """計算連貫性"""
        if not answer or answer.startswith("生成失敗") or answer.startswith("評估失敗"):
            return 0.0
        
        # 基於句子數量的簡單連貫性計算
        sentences = answer.split('。')
        if len(sentences) <= 1:
            return 0.5
        
        return min(1.0, len(sentences) / 5.0)
    
    async def evaluate_batch(self, questions: List[str]) -> List[ComparisonResult]:
        """批量評估問題"""
        results = []
        for question in questions:
            result = await self.evaluate_single_question(question)
            results.append(result)
            logger.info(f"✅ 完成評估: {question[:30]}...")
        return results
    
    def generate_comparison_report(self, results: List[ComparisonResult], output_path: str = None) -> str:
        """生成對比報告"""
        try:
            # 準備數據
            data = []
            for result in results:
                row = {
                    "問題": result.question,
                    "本地LLM答案": result.local_llm_result.answer,
                    "OpenAI答案": result.openai_result.answer,
                    "本地信心度": result.local_llm_result.confidence,
                    "OpenAI信心度": result.openai_result.confidence,
                    "本地事實性": result.local_llm_result.factuality,
                    "OpenAI事實性": result.openai_result.factuality,
                    "本地相關性": result.local_llm_result.relevance,
                    "OpenAI相關性": result.openai_result.relevance,
                    "本地連貫性": result.local_llm_result.coherence,
                    "OpenAI連貫性": result.openai_result.coherence,
                    "本地推理時間(秒)": result.local_llm_result.inference_time,
                    "OpenAI推理時間(秒)": result.openai_result.inference_time,
                    "本地Token數": result.local_llm_result.token_count,
                    "OpenAI Token數": result.openai_result.token_count,
                    "信心度差異": result.comparison_metrics.get("confidence_diff", 0),
                    "事實性差異": result.comparison_metrics.get("factuality_diff", 0),
                    "速度比": result.comparison_metrics.get("speed_ratio", 0),
                    "Token比": result.comparison_metrics.get("token_ratio", 0)
                }
                data.append(row)
            
            # 創建 DataFrame
            df = pd.DataFrame(data)
            
            # 生成報告
            report = f"""# RAG 評估對比報告

## 評估概覽
- 評估時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 問題數量: {len(results)}
- 檢索方法: Milvus (IVF_FLAT 索引)
- 本地 LLM: Qwen2.5-Taiwan-7B-Instruct
- OpenAI LLM: GPT-3.5-Turbo

## 詳細對比結果

{df.to_string(index=False)}

## 統計摘要

### 平均指標
- 本地 LLM 平均信心度: {df['本地信心度'].mean():.3f}
- OpenAI 平均信心度: {df['OpenAI信心度'].mean():.3f}
- 本地 LLM 平均事實性: {df['本地事實性'].mean():.3f}
- OpenAI 平均事實性: {df['OpenAI事實性'].mean():.3f}
- 本地 LLM 平均推理時間: {df['本地推理時間(秒)'].mean():.3f} 秒
- OpenAI 平均推理時間: {df['OpenAI推理時間(秒)'].mean():.3f} 秒

### 性能對比
- 平均速度比 (本地/OpenAI): {df['速度比'].mean():.3f}
- 平均 Token 比 (本地/OpenAI): {df['Token比'].mean():.3f}
- 平均信心度差異 (本地-OpenAI): {df['信心度差異'].mean():.3f}
- 平均事實性差異 (本地-OpenAI): {df['事實性差異'].mean():.3f}

## 結論
1. 本地 LLM 在推理時間上 {'優於' if df['速度比'].mean() < 1 else '劣於'} OpenAI
2. 本地 LLM 在信心度上 {'優於' if df['信心度差異'].mean() > 0 else '劣於'} OpenAI
3. 本地 LLM 在事實性上 {'優於' if df['事實性差異'].mean() > 0 else '劣於'} OpenAI
"""
            
            # 保存報告
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                # 保存 CSV
                csv_path = output_path.replace('.txt', '.csv')
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                logger.info(f"✅ 報告已保存: {output_path}")
                logger.info(f"✅ CSV 已保存: {csv_path}")
            
            return report
            
        except Exception as e:
            logger.error(f"生成報告失敗: {e}")
            return f"報告生成失敗: {str(e)}"
    
    # 基礎 RAG 評估方法（整合自 rag_evaluator.py）
    def baseline_evaluation(self, eval_dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Baseline 評估（無 RAG）"""
        results = []
        
        for item in eval_dataset:
            question = item["input"]
            expected = item["expected"]
            
            # 使用 OpenAI 服務生成回答
            answer, inference_time, token_count = asyncio.run(
                self.openai_service.generate_answer(question, "")
            )
            
            # 計算簡單的相似度指標
            similarity = self._calculate_simple_similarity(answer, expected)
            
            result = {
                "method": "Baseline",
                "question": question,
                "expected": expected,
                "answer": answer,
                "similarity_score": similarity,
                "inference_time": inference_time,
                "token_count": token_count
            }
            results.append(result)
        
        return results
    
    def naive_rag_evaluation(self, eval_dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Naive RAG 評估"""
        results = []
        
        for item in eval_dataset:
            question = item["input"]
            expected = item["expected"]
            context = item["metadata"].get("reference", "")
            
            # 使用 OpenAI 服務生成回答
            answer, inference_time, token_count = asyncio.run(
                self.openai_service.generate_answer(question, context)
            )
            
            # 計算指標
            similarity = self._calculate_simple_similarity(answer, expected)
            relevance = self._calculate_relevance(answer, question)
            
            result = {
                "method": "Naive RAG",
                "question": question,
                "expected": expected,
                "answer": answer,
                "context": context,
                "similarity_score": similarity,
                "relevance_score": relevance,
                "inference_time": inference_time,
                "token_count": token_count
            }
            results.append(result)
        
        return results
    
    def _calculate_simple_similarity(self, answer: str, expected: str) -> float:
        """計算簡單相似度"""
        if not answer or not expected:
            return 0.0
        
        # 簡單的詞彙重疊計算
        answer_words = set(answer.lower().split())
        expected_words = set(expected.lower().split())
        
        if not expected_words:
            return 0.0
        
        overlap = len(answer_words.intersection(expected_words))
        return overlap / len(expected_words)
    
    # Podwise 專用功能（整合自 podwise_rag_evaluation.py）
    def create_podwise_synthetic_dataset(self, num_questions: int = 5) -> list:
        """為 Podwise 資料創建合成問答對"""
        try:
            # 獲取統計資訊
            stats = self.podwise_search.get_statistics()
            logger.info(f"📊 向量資料庫統計:")
            logger.info(f"   - 總 chunks: {stats['total_chunks']}")
            logger.info(f"   - 播客數量: {stats['total_podcasts']}")
            logger.info(f"   - 節目數量: {stats['total_episodes']}")
            logger.info(f"   - 分類: {stats['categories']}")
            
            # 從向量資料庫中隨機選擇一些 chunks 作為內容
            if stats['total_chunks'] > 0:
                # 隨機選擇一些 chunks
                import random
                sample_size = min(10, stats['total_chunks'])
                sample_indices = random.sample(range(stats['total_chunks']), sample_size)
                
                # 組合內容
                combined_content = ""
                for idx in sample_indices:
                    chunk_text = self.podwise_search.chunk_texts[idx]
                    metadata = self.podwise_search.metadata[idx]
                    combined_content += f"\n\n播客: {metadata['podcast_name']}\n"
                    combined_content += f"節目: {metadata['episode_title']}\n"
                    combined_content += f"內容: {chunk_text}\n"
                
                # 生成問答對
                qa_pairs = self._produce_questions(combined_content, num_questions)
                
                # 轉換為字典格式
                result = []
                for pair in qa_pairs:
                    if hasattr(pair, 'model_dump'):
                        qa_data = pair.model_dump()
                    else:
                        qa_data = {
                            'reference': pair.reference,
                            'question': pair.question,
                            'answer': pair.answer
                        }
                    result.append(qa_data)
                
                return result
            
            return []
            
        except Exception as e:
            logger.error(f"❌ 創建 Podwise 合成資料集失敗: {str(e)}")
            return []
    
    def _produce_questions(self, content: str, num_questions: int = 2) -> List[Any]:
        """產生問題（簡化版本）"""
        try:
            from pydantic import Field, BaseModel
            from typing import List
            
            class QAPair(BaseModel):
                reference: str = Field(..., description="原始文本段落")
                question: str = Field(..., description="問題")
                answer: str = Field(..., description="答案")
            
            # 簡化的問題生成邏輯
            questions = [
                "我想學習投資理財，有什麼推薦的 Podcast 嗎？",
                "通勤時間想聽一些輕鬆的內容",
                "有什麼關於創業的節目推薦嗎？",
                "如何提高工作效率？",
                "推薦一些商業相關的 Podcast"
            ]
            
            # 選擇指定數量的問題
            selected_questions = questions[:num_questions]
            
            # 生成問答對
            pairs = []
            for question in selected_questions:
                # 簡單的回答生成
                answer = f"基於提供的內容，我為您推薦相關的 Podcast 節目。{content[:100]}..."
                
                pair = QAPair(
                    reference=content[:200] + "...",
                    question=question,
                    answer=answer
                )
                pairs.append(pair)
            
            return pairs
            
        except Exception as e:
            logger.error(f"產生問題失敗: {e}")
            return []

def get_unified_evaluator() -> UnifiedRAGEvaluator:
    """獲取統一評估器實例"""
    return UnifiedRAGEvaluator(use_mock_services=True)

async def test_unified_evaluator():
    """測試統一評估器"""
    print("=== 測試統一 RAG 評估器 ===")
    
    # 初始化評估器
    evaluator = get_unified_evaluator()
    
    # 測試問題
    test_questions = [
        "我想學習投資理財，有什麼推薦的 Podcast 嗎？",
        "通勤時間想聽一些輕鬆的內容",
        "有什麼關於創業的節目推薦嗎？"
    ]
    
    # 執行評估
    results = await evaluator.evaluate_batch(test_questions)
    
    # 生成報告
    report = evaluator.generate_comparison_report(
        results, 
        "unified_rag_evaluation_report.txt"
    )
    
    print("✅ 評估完成")
    print(report)
    
    return results

if __name__ == "__main__":
    asyncio.run(test_unified_evaluator()) 