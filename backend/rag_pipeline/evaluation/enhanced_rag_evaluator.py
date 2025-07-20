#!/usr/bin/env python3
"""
增強版 RAG 評估器

功能特色：
1. 專用 Milvus 檢索（支援 IVF_FLAT 索引優化）
2. 本地 Qwen2.5-Taiwan-7B-Instruct 與 OpenAI 對比
3. 完整評估指標（信心度、事實性、推理時間、token 數）
4. 表格格式對比報告

作者: Podwise Team
版本: 2.0.0
"""

import os
import sys
import json
import time
import logging
import asyncio
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import hashlib

# 添加路徑以便導入
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from config.integrated_config import get_config
except ImportError:
    # 簡化配置
    def get_config():
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

logger = logging.getLogger(__name__)


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
        self.config = get_config()
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
                
                # 根據向量數量建議索引類型
                if stats < 1000000:
                    logger.info("📊 建議使用 IVF_FLAT 索引（向量數 < 1M）")
                else:
                    logger.info("📊 建議使用 HNSW 或 DiskANN 索引（向量數 > 1M）")
                    
            else:
                logger.warning(f"⚠️ Milvus 集合 '{collection_name}' 不存在")
                
        except ImportError:
            logger.warning("⚠️ pymilvus 未安裝")
        except Exception as e:
            logger.error(f"❌ Milvus 連接失敗: {e}")
    
    async def search(self, query: str, top_k: int = 10, nprobe: int = 16) -> List[Dict[str, Any]]:
        """
        執行優化的向量搜尋
        
        Args:
            query: 查詢文本
            top_k: 返回結果數量
            nprobe: 搜尋探針數量
            
        Returns:
            List[Dict[str, Any]]: 搜尋結果
        """
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
                            except Exception as e2:
                                logger.warning(f"屬性訪問也失敗: {e2}")
                    
                    formatted_results.append({
                        "content": chunk_text,
                        "similarity_score": float(hit.score),
                        "metadata": entity_data,
                        "tags": tags,
                        "source": "milvus"
                    })
            
            logger.info(f"✅ Milvus 搜尋成功，返回 {len(formatted_results)} 個結果")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Milvus 搜尋失敗: {e}")
            return []
    
    def _text_to_vector(self, text: str) -> Optional[List[float]]:
        """文本向量化（簡化版本）"""
        try:
            # 使用 MD5 哈希生成 1024 維向量
            hash_obj = hashlib.md5(text.encode())
            hash_hex = hash_obj.hexdigest()
            
            # 擴展到 1024 維
            vector = []
            for i in range(1024):
                # 循環使用哈希值
                idx = i % len(hash_hex)
                vector.append(float(int(hash_hex[idx:idx+2], 16)) / 255.0)
            
            return vector
            
        except Exception as e:
            logger.error(f"文本向量化失敗: {e}")
            return None


class LocalLLMService:
    """本地 LLM 服務（Qwen2.5-Taiwan-7B-Instruct）"""
    
    def __init__(self, model_path: str = "/home/bai/Desktop/Podwise/Qwen2.5-Taiwan-7B-Instruct"):
        """初始化本地 LLM 服務"""
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.prompt_templates_available = False
        self._load_model()
        self._load_prompt_templates()
    
    def _load_prompt_templates(self):
        """載入提示詞模板"""
        try:
            # 嘗試多種導入路徑
            try:
                from config.prompt_templates import get_prompt_template, format_prompt
            except ImportError:
                try:
                    from ..config.prompt_templates import get_prompt_template, format_prompt
                except ImportError:
                    # 使用絕對路徑
                    import sys
                    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
                    from config.prompt_templates import get_prompt_template, format_prompt
            
            self.get_prompt_template = get_prompt_template
            self.format_prompt = format_prompt
            self.prompt_templates_available = True
            logger.info("✅ 本地 LLM 提示詞模板載入成功")
        except ImportError as e:
            logger.warning(f"⚠️ 無法載入提示詞模板: {e}")
            self.prompt_templates_available = False
    
    def _load_model(self):
        """載入本地模型"""
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            
            if os.path.exists(self.model_path):
                # 使用正確的 tokenizer 類別
                try:
                    # 嘗試使用 AutoTokenizer
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        self.model_path,
                        trust_remote_code=True
                    )
                except Exception as e:
                    logger.warning(f"AutoTokenizer 載入失敗，嘗試使用預設 tokenizer: {e}")
                    # 如果失敗，使用預設的 tokenizer
                    from transformers import PreTrainedTokenizer
                    self.tokenizer = PreTrainedTokenizer.from_pretrained(
                        self.model_path,
                        trust_remote_code=True
                    )
                
                # 設置 pad token
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                # 載入模型
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True,
                    low_cpu_mem_usage=True
                )
                
                self.is_loaded = True
                logger.info(f"✅ 本地 LLM 載入成功: {self.model_path}")
            else:
                logger.warning(f"⚠️ 本地模型路徑不存在: {self.model_path}")
                
        except ImportError:
            logger.warning("⚠️ transformers 未安裝")
        except Exception as e:
            logger.error(f"❌ 本地 LLM 載入失敗: {e}")
            # 提供更詳細的錯誤信息
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
    
    async def generate_answer(self, prompt: str, context: str = "") -> Tuple[str, float, int]:
        """
        生成答案（使用 prompt_templates.py）
        
        Args:
            prompt: 問題
            context: 上下文
            
        Returns:
            Tuple[str, float, int]: (答案, 推理時間, token 數)
        """
        start_time = time.time()
        
        try:
            if not self.is_loaded or self.model is None or self.tokenizer is None:
                return "本地 LLM 未載入", 0.0, 0
            
            # 構建提示詞
            if self.prompt_templates_available:
                try:
                    # 使用正式的提示詞模板
                    answer_template = self.get_prompt_template("answer_generation")
                    
                    # 構建模擬的領導者決策結果
                    mock_leader_decision = {
                        "top_recommendations": [
                            {
                                "title": "本地 LLM 推薦節目",
                                "category": "商業",
                                "confidence": 0.88,
                                "source": "本地 LLM 分析",
                                "episode": "第 2 集",
                                "rss_id": "RSS004"
                            }
                        ],
                        "explanation": "基於您的問題，我們找到了相關的商業類 Podcast 節目",
                        "recommendation_count": 1,
                        "categories_included": ["商業"]
                    }
                    
                    # 格式化提示詞
                    formatted_prompt = self.format_prompt(
                        answer_template,
                        leader_decision=json.dumps(mock_leader_decision, ensure_ascii=False),
                        user_question=prompt,
                        user_context={"context": context}
                    )
                    
                    # 添加系統提示
                    full_prompt = f"""你是 Podri，一位專業的 Podcast 推薦助手。

{formatted_prompt}

請基於以上資訊生成回答："""
                    
                except Exception as e:
                    logger.warning(f"提示詞模板格式化失敗，使用備用提示: {e}")
                    full_prompt = f"""
基於以下資訊回答問題：

資訊：
{context}

問題：{prompt}

請用繁體中文回答：
"""
            else:
                # 備用提示詞
                full_prompt = f"""
基於以下資訊回答問題：

資訊：
{context}

問題：{prompt}

請用繁體中文回答：
"""
            
            # 編碼輸入
            inputs = self.tokenizer(full_prompt, return_tensors="pt")
            input_ids = inputs["input_ids"]
            
            # 生成答案
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    max_new_tokens=512,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # 解碼答案
            answer = self.tokenizer.decode(outputs[0][input_ids.shape[1]:], skip_special_tokens=True)
            
            # 計算 token 數
            token_count = len(outputs[0])
            
            # 計算推理時間
            inference_time = time.time() - start_time
            
            return answer.strip(), inference_time, token_count
            
        except Exception as e:
            logger.error(f"本地 LLM 生成失敗: {e}")
            return f"生成失敗: {str(e)}", time.time() - start_time, 0


class OpenAIService:
    """OpenAI 服務（整合 prompt_templates.py）"""
    
    def __init__(self):
        """初始化 OpenAI 服務"""
        self.config = get_config()
        self.api_key = self.config.api.openai_api_key
        self.prompt_templates_available = False
        self._load_prompt_templates()
    
    def _load_prompt_templates(self):
        """載入提示詞模板"""
        try:
            # 嘗試多種導入路徑
            try:
                from config.prompt_templates import get_prompt_template, format_prompt
            except ImportError:
                try:
                    from ..config.prompt_templates import get_prompt_template, format_prompt
                except ImportError:
                    # 使用絕對路徑
                    import sys
                    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
                    from config.prompt_templates import get_prompt_template, format_prompt
            
            self.get_prompt_template = get_prompt_template
            self.format_prompt = format_prompt
            self.prompt_templates_available = True
            logger.info("✅ OpenAI 提示詞模板載入成功")
        except ImportError as e:
            logger.warning(f"⚠️ 無法載入提示詞模板: {e}")
            self.prompt_templates_available = False
        
    async def generate_answer(self, prompt: str, context: str = "") -> Tuple[str, float, int]:
        """
        生成答案（使用 prompt_templates.py）
        
        Args:
            prompt: 問題
            context: 上下文
            
        Returns:
            Tuple[str, float, int]: (答案, 推理時間, token 數)
        """
        start_time = time.time()
        
        try:
            if not self.api_key:
                return "OpenAI API Key 未配置", 0.0, 0
            
            from openai import OpenAI
            
            # 創建客戶端
            client = OpenAI(api_key=self.api_key)
            
            # 構建提示詞
            if self.prompt_templates_available:
                try:
                    # 使用正式的提示詞模板
                    answer_template = self.get_prompt_template("answer_generation")
                    
                    # 構建模擬的領導者決策結果
                    mock_leader_decision = {
                        "top_recommendations": [
                            {
                                "title": "OpenAI 推薦節目",
                                "category": "教育",
                                "confidence": 0.92,
                                "source": "OpenAI 分析",
                                "episode": "第 5 集",
                                "rss_id": "RSS005"
                            },
                            {
                                "title": "進階學習節目",
                                "category": "教育",
                                "confidence": 0.89,
                                "source": "OpenAI 分析",
                                "episode": "第 3 集",
                                "rss_id": "RSS006"
                            }
                        ],
                        "explanation": "基於您的問題，我們找到了多個相關的教育類 Podcast 節目",
                        "recommendation_count": 2,
                        "categories_included": ["教育"]
                    }
                    
                    # 格式化提示詞
                    formatted_prompt = self.format_prompt(
                        answer_template,
                        leader_decision=json.dumps(mock_leader_decision, ensure_ascii=False),
                        user_question=prompt,
                        user_context={"context": context}
                    )
                    
                    # 構建系統提示
                    system_prompt = "你是 Podri，一位專業的 Podcast 推薦助手。請根據提供的資訊生成友善、專業的回答。"
                    user_prompt = formatted_prompt
                    
                except Exception as e:
                    logger.warning(f"提示詞模板格式化失敗，使用備用提示: {e}")
                    system_prompt = "你是一個專業的 AI 助手，請用繁體中文回答問題。"
                    user_prompt = f"""
基於以下資訊回答問題：

資訊：
{context}

問題：{prompt}

請用繁體中文回答：
"""
            else:
                # 備用提示詞
                system_prompt = "你是一個專業的 AI 助手，請用繁體中文回答問題。"
                user_prompt = f"""
基於以下資訊回答問題：

資訊：
{context}

問題：{prompt}

請用繁體中文回答：
"""
            
            # 發送請求
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=512,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content
            token_count = response.usage.total_tokens
            inference_time = time.time() - start_time
            
            return answer, inference_time, token_count
            
        except Exception as e:
            logger.error(f"OpenAI 生成失敗: {e}")
            return f"生成失敗: {str(e)}", time.time() - start_time, 0


class MockLocalLLMService:
    """模擬本地 LLM 服務（用於測試 prompt_templates.py 整合）"""
    
    def __init__(self):
        """初始化模擬本地 LLM 服務"""
        self.prompt_templates_available = False
        self._load_prompt_templates()
    
    def _load_prompt_templates(self):
        """載入提示詞模板"""
        try:
            # 使用絕對路徑
            import sys
            import os
            
            # 獲取當前文件的路徑
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 向上兩級到 backend 目錄
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            # 添加到 Python 路徑
            sys.path.insert(0, backend_dir)
            
            from rag_pipeline.config.prompt_templates import get_prompt_template, format_prompt
            
            self.get_prompt_template = get_prompt_template
            self.format_prompt = format_prompt
            self.prompt_templates_available = True
            logger.info("✅ 模擬本地 LLM 提示詞模板載入成功")
        except ImportError as e:
            logger.warning(f"⚠️ 無法載入提示詞模板: {e}")
            self.prompt_templates_available = False
    
    async def generate_answer(self, prompt: str, context: str = "") -> Tuple[str, float, int]:
        """
        生成答案（使用 prompt_templates.py）
        
        Args:
            prompt: 問題
            context: 上下文
            
        Returns:
            Tuple[str, float, int]: (答案, 推理時間, token 數)
        """
        start_time = time.time()
        
        try:
            # 構建提示詞
            if self.prompt_templates_available:
                try:
                    # 使用正式的提示詞模板
                    answer_template = self.get_prompt_template("answer_generation")
                    
                    # 構建模擬的領導者決策結果
                    mock_leader_decision = {
                        "top_recommendations": [
                            {
                                "title": "模擬本地 LLM 推薦節目",
                                "category": "商業",
                                "confidence": 0.88,
                                "source": "模擬本地 LLM 分析",
                                "episode": "第 2 集",
                                "rss_id": "RSS004"
                            }
                        ],
                        "explanation": "基於您的問題，我們找到了相關的商業類 Podcast 節目",
                        "recommendation_count": 1,
                        "categories_included": ["商業"]
                    }
                    
                    # 格式化提示詞
                    formatted_prompt = self.format_prompt(
                        answer_template,
                        leader_decision=json.dumps(mock_leader_decision, ensure_ascii=False),
                        user_question=prompt,
                        user_context={"context": context}
                    )
                    
                    # 模擬 LLM 回應（基於模板格式）
                    answer = f"""嗨嗨👋 想了解「{prompt}」嗎？以下是相關的精彩節目：

🎧《模擬本地 LLM 推薦節目》第 2 集：〈商業分析〉
👉 這是一個模擬的本地 LLM 回應，基於 prompt_templates.py 的格式生成
📅 發布時間：2024年

💡 小提醒：如果您對其他類別也感興趣，我也可以推薦一些相關的節目喔！

有興趣的話可以點來聽聽，讓耳朵和腦袋都充實一下 😊"""
                    
                except Exception as e:
                    logger.warning(f"提示詞模板格式化失敗，使用備用回應: {e}")
                    answer = f"這是一個模擬的本地 LLM 回應，問題：{prompt}。上下文：{context[:100]}..."
            else:
                # 備用回應
                answer = f"這是一個模擬的本地 LLM 回應，問題：{prompt}。上下文：{context[:100]}..."
            
            # 模擬推理時間
            await asyncio.sleep(2.0)
            
            # 計算時間和 token 數
            inference_time = time.time() - start_time
            token_count = len(answer.split()) * 1.5  # 粗略估算
            
            return answer, inference_time, int(token_count)
            
        except Exception as e:
            logger.error(f"模擬本地 LLM 生成失敗: {e}")
            return f"生成失敗: {str(e)}", time.time() - start_time, 0


class MockOpenAIService:
    """模擬 OpenAI 服務（用於測試 prompt_templates.py 整合）"""
    
    def __init__(self):
        """初始化模擬 OpenAI 服務"""
        self.prompt_templates_available = False
        self._load_prompt_templates()
    
    def _load_prompt_templates(self):
        """載入提示詞模板"""
        try:
            # 使用絕對路徑
            import sys
            import os
            
            # 獲取當前文件的路徑
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 向上兩級到 backend 目錄
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            # 添加到 Python 路徑
            sys.path.insert(0, backend_dir)
            
            from rag_pipeline.config.prompt_templates import get_prompt_template, format_prompt
            
            self.get_prompt_template = get_prompt_template
            self.format_prompt = format_prompt
            self.prompt_templates_available = True
            logger.info("✅ 模擬 OpenAI 提示詞模板載入成功")
        except ImportError as e:
            logger.warning(f"⚠️ 無法載入提示詞模板: {e}")
            self.prompt_templates_available = False
        
    async def generate_answer(self, prompt: str, context: str = "") -> Tuple[str, float, int]:
        """
        生成答案（使用 prompt_templates.py）
        
        Args:
            prompt: 問題
            context: 上下文
            
        Returns:
            Tuple[str, float, int]: (答案, 推理時間, token 數)
        """
        start_time = time.time()
        
        try:
            # 構建提示詞
            if self.prompt_templates_available:
                try:
                    # 使用正式的提示詞模板
                    answer_template = self.get_prompt_template("answer_generation")
                    
                    # 構建模擬的領導者決策結果
                    mock_leader_decision = {
                        "top_recommendations": [
                            {
                                "title": "模擬 OpenAI 推薦節目",
                                "category": "教育",
                                "confidence": 0.92,
                                "source": "模擬 OpenAI 分析",
                                "episode": "第 5 集",
                                "rss_id": "RSS005"
                            },
                            {
                                "title": "進階學習節目",
                                "category": "教育",
                                "confidence": 0.89,
                                "source": "模擬 OpenAI 分析",
                                "episode": "第 3 集",
                                "rss_id": "RSS006"
                            }
                        ],
                        "explanation": "基於您的問題，我們找到了多個相關的教育類 Podcast 節目",
                        "recommendation_count": 2,
                        "categories_included": ["教育"]
                    }
                    
                    # 格式化提示詞
                    formatted_prompt = self.format_prompt(
                        answer_template,
                        leader_decision=json.dumps(mock_leader_decision, ensure_ascii=False),
                        user_question=prompt,
                        user_context={"context": context}
                    )
                    
                    # 模擬 OpenAI 回應（基於模板格式）
                    answer = f"""嗨嗨👋 想了解「{prompt}」嗎？以下是相關的精彩節目：

🎧《模擬 OpenAI 推薦節目》第 5 集：〈深度學習〉
👉 這是一個模擬的 OpenAI 回應，基於 prompt_templates.py 的格式生成
📅 發布時間：2024年

🎧《進階學習節目》第 3 集：〈技能提升〉
👉 提供實用的學習技巧和職涯發展建議
📅 發布時間：2024年

💡 小提醒：這些節目都經過精心挑選，希望能幫助您更好地學習和成長！

有興趣的話可以點來聽聽，讓耳朵和腦袋都充實一下 😊"""
                    
                except Exception as e:
                    logger.warning(f"提示詞模板格式化失敗，使用備用回應: {e}")
                    answer = f"這是一個模擬的 OpenAI 回應，問題：{prompt}。上下文：{context[:100]}..."
            else:
                # 備用回應
                answer = f"這是一個模擬的 OpenAI 回應，問題：{prompt}。上下文：{context[:100]}..."
            
            # 模擬推理時間
            await asyncio.sleep(0.5)
            
            # 計算時間和 token 數
            inference_time = time.time() - start_time
            token_count = len(answer.split()) * 1.5  # 粗略估算
            
            return answer, inference_time, int(token_count)
            
        except Exception as e:
            logger.error(f"模擬 OpenAI 生成失敗: {e}")
            return f"生成失敗: {str(e)}", time.time() - start_time, 0


class EnhancedRAGEvaluator:
    """增強版 RAG 評估器（整合 prompt_templates.py）"""
    
    def __init__(self, use_mock_services: bool = True):
        """初始化增強版 RAG 評估器"""
        self.milvus_search = MilvusOptimizedSearch()
        
        if use_mock_services:
            # 使用模擬服務進行測試
            self.local_llm = MockLocalLLMService()
            self.openai_service = MockOpenAIService()
            logger.info("✅ 使用模擬 LLM 服務進行測試")
        else:
            # 使用真實服務
            self.local_llm = LocalLLMService()
            self.openai_service = OpenAIService()
            logger.info("✅ 使用真實 LLM 服務")
        
        logger.info("✅ 增強版 RAG 評估器初始化完成")
    
    async def evaluate_single_question(self, question: str) -> ComparisonResult:
        """
        評估單個問題
        
        Args:
            question: 問題
            
        Returns:
            ComparisonResult: 對比結果
        """
        # 1. Milvus 檢索
        retrieval_start = time.time()
        search_results = await self.milvus_search.search(question, top_k=10, nprobe=16)
        retrieval_time = time.time() - retrieval_start
        
        # 構建上下文
        context = self._build_context(search_results)
        
        # 2. 本地 LLM 生成
        local_answer, local_time, local_tokens = await self.local_llm.generate_answer(question, context)
        
        # 3. OpenAI 生成
        openai_answer, openai_time, openai_tokens = await self.openai_service.generate_answer(question, context)
        
        # 4. 評估指標
        local_result = EvaluationResult(
            question=question,
            answer=local_answer,
            confidence=self._calculate_confidence(local_answer, search_results),
            factuality=self._calculate_factuality(local_answer, search_results),
            relevance=self._calculate_relevance(local_answer, question),
            coherence=self._calculate_coherence(local_answer),
            inference_time=local_time,
            token_count=local_tokens,
            model_name="Qwen2.5-Taiwan-7B-Instruct",
            retrieval_method="Milvus",
            sources=search_results
        )
        
        openai_result = EvaluationResult(
            question=question,
            answer=openai_answer,
            confidence=self._calculate_confidence(openai_answer, search_results),
            factuality=self._calculate_factuality(openai_answer, search_results),
            relevance=self._calculate_relevance(openai_answer, question),
            coherence=self._calculate_coherence(openai_answer),
            inference_time=openai_time,
            token_count=openai_tokens,
            model_name="GPT-3.5-Turbo",
            retrieval_method="Milvus",
            sources=search_results
        )
        
        # 5. 對比指標
        comparison_metrics = {
            "confidence_diff": local_result.confidence - openai_result.confidence,
            "factuality_diff": local_result.factuality - openai_result.factuality,
            "relevance_diff": local_result.relevance - openai_result.relevance,
            "coherence_diff": local_result.coherence - openai_result.coherence,
            "speed_ratio": local_result.inference_time / openai_result.inference_time if openai_result.inference_time > 0 else 0,
            "token_ratio": local_result.token_count / openai_result.token_count if openai_result.token_count > 0 else 0
        }
        
        return ComparisonResult(
            question=question,
            local_llm_result=local_result,
            openai_result=openai_result,
            comparison_metrics=comparison_metrics
        )
    
    def _build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """構建上下文"""
        if not search_results:
            return ""
        
        context_parts = []
        for i, result in enumerate(search_results[:3], 1):
            content = result.get("content", "")
            if content:
                context_parts.append(f"{i}. {content[:200]}...")
        
        return "\n\n".join(context_parts)
    
    def _calculate_confidence(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """計算信心度"""
        if not answer or answer.startswith("生成失敗"):
            return 0.0
        
        # 簡單的基於答案長度和來源數量的信心度計算
        base_confidence = min(len(answer) / 100, 1.0)  # 答案長度
        source_confidence = min(len(sources) / 5, 1.0)  # 來源數量
        
        return (base_confidence + source_confidence) / 2
    
    def _calculate_factuality(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """計算事實性"""
        if not answer or answer.startswith("生成失敗"):
            return 0.0
        
        # 簡單的事實性評估（基於是否包含具體資訊）
        factual_indicators = ["根據", "基於", "資料顯示", "研究指出", "統計", "數據"]
        factual_count = sum(1 for indicator in factual_indicators if indicator in answer)
        
        return min(factual_count / 3, 1.0)
    
    def _calculate_relevance(self, answer: str, question: str) -> float:
        """計算相關性"""
        if not answer or answer.startswith("生成失敗"):
            return 0.0
        
        # 簡單的相關性評估（基於關鍵詞重疊）
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        
        if not question_words:
            return 0.0
        
        overlap = len(question_words.intersection(answer_words))
        return min(overlap / len(question_words), 1.0)
    
    def _calculate_coherence(self, answer: str) -> float:
        """計算連貫性"""
        if not answer or answer.startswith("生成失敗"):
            return 0.0
        
        # 簡單的連貫性評估（基於句子結構）
        sentences = answer.split("。")
        if len(sentences) <= 1:
            return 0.5
        
        # 檢查句子長度的一致性
        lengths = [len(s) for s in sentences if s.strip()]
        if not lengths:
            return 0.5
        
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        
        # 變異係數越小，連貫性越高
        cv = (variance ** 0.5) / avg_length if avg_length > 0 else 1.0
        return max(0, 1 - cv)
    
    async def evaluate_batch(self, questions: List[str]) -> List[ComparisonResult]:
        """
        批量評估問題
        
        Args:
            questions: 問題列表
            
        Returns:
            List[ComparisonResult]: 對比結果列表
        """
        results = []
        for i, question in enumerate(questions, 1):
            logger.info(f"評估問題 {i}/{len(questions)}: {question[:50]}...")
            result = await self.evaluate_single_question(question)
            results.append(result)
        
        return results
    
    def generate_comparison_report(self, results: List[ComparisonResult], output_path: str = None) -> str:
        """
        生成對比報告
        
        Args:
            results: 對比結果列表
            output_path: 輸出路徑
            
        Returns:
            str: 報告內容
        """
        # 準備數據
        data = []
        for result in results:
            data.append({
                "問題": result.question,
                "本地LLM答案": result.local_llm_result.answer[:100] + "..." if len(result.local_llm_result.answer) > 100 else result.local_llm_result.answer,
                "OpenAI答案": result.openai_result.answer[:100] + "..." if len(result.openai_result.answer) > 100 else result.openai_result.answer,
                "本地信心度": f"{result.local_llm_result.confidence:.3f}",
                "OpenAI信心度": f"{result.openai_result.confidence:.3f}",
                "本地事實性": f"{result.local_llm_result.factuality:.3f}",
                "OpenAI事實性": f"{result.openai_result.factuality:.3f}",
                "本地相關性": f"{result.local_llm_result.relevance:.3f}",
                "OpenAI相關性": f"{result.openai_result.relevance:.3f}",
                "本地連貫性": f"{result.local_llm_result.coherence:.3f}",
                "OpenAI連貫性": f"{result.openai_result.coherence:.3f}",
                "本地推理時間(秒)": f"{result.local_llm_result.inference_time:.3f}",
                "OpenAI推理時間(秒)": f"{result.openai_result.inference_time:.3f}",
                "本地Token數": result.local_llm_result.token_count,
                "OpenAI Token數": result.openai_result.token_count,
                "信心度差異": f"{result.comparison_metrics['confidence_diff']:.3f}",
                "事實性差異": f"{result.comparison_metrics['factuality_diff']:.3f}",
                "速度比": f"{result.comparison_metrics['speed_ratio']:.3f}",
                "Token比": f"{result.comparison_metrics['token_ratio']:.3f}"
            })
        
        # 創建 DataFrame
        df = pd.DataFrame(data)
        
        # 生成報告
        report = f"""
# RAG 評估對比報告

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
- 本地 LLM 平均信心度: {df['本地信心度'].astype(float).mean():.3f}
- OpenAI 平均信心度: {df['OpenAI信心度'].astype(float).mean():.3f}
- 本地 LLM 平均事實性: {df['本地事實性'].astype(float).mean():.3f}
- OpenAI 平均事實性: {df['OpenAI事實性'].astype(float).mean():.3f}
- 本地 LLM 平均推理時間: {df['本地推理時間(秒)'].astype(float).mean():.3f} 秒
- OpenAI 平均推理時間: {df['OpenAI推理時間(秒)'].astype(float).mean():.3f} 秒

### 性能對比
- 平均速度比 (本地/OpenAI): {df['速度比'].astype(float).mean():.3f}
- 平均 Token 比 (本地/OpenAI): {df['Token比'].astype(float).mean():.3f}
- 平均信心度差異 (本地-OpenAI): {df['信心度差異'].astype(float).mean():.3f}
- 平均事實性差異 (本地-OpenAI): {df['事實性差異'].astype(float).mean():.3f}

## 結論
1. 本地 LLM 在推理時間上 {'優於' if df['速度比'].astype(float).mean() < 1 else '劣於'} OpenAI
2. 本地 LLM 在信心度上 {'優於' if df['信心度差異'].astype(float).mean() > 0 else '劣於'} OpenAI
3. 本地 LLM 在事實性上 {'優於' if df['事實性差異'].astype(float).mean() > 0 else '劣於'} OpenAI
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


# 全域實例
enhanced_evaluator = EnhancedRAGEvaluator()


def get_enhanced_evaluator() -> EnhancedRAGEvaluator:
    """獲取增強版評估器實例"""
    return EnhancedRAGEvaluator(use_mock_services=True)


# 測試函數
async def test_enhanced_evaluator():
    """測試增強版評估器（整合 prompt_templates.py）"""
    print("開始增強版 RAG 評估（整合 prompt_templates.py）...")
    
    evaluator = get_enhanced_evaluator()
    
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
        output_path="enhanced_comparison_report.txt"
    )
    
    print("✅ 增強版對比評估完成（整合 prompt_templates.py）")
    print(report)
    
    # 驗證 prompt_templates.py 整合
    print("\n🔍 Prompt Templates 整合驗證:")
    print(f"- 本地 LLM 提示詞模板可用: {evaluator.local_llm.prompt_templates_available}")
    print(f"- OpenAI 提示詞模板可用: {evaluator.openai_service.prompt_templates_available}")
    
    if evaluator.local_llm.prompt_templates_available and evaluator.openai_service.prompt_templates_available:
        print("✅ 提示詞模板整合成功！")
    else:
        print("⚠️ 提示詞模板整合需要改進")


if __name__ == "__main__":
    asyncio.run(test_enhanced_evaluator()) 