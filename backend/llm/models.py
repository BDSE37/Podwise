"""
LLM 模型管理模組
整合 Qwen3、BGE-M3 和 Deepseek R1 模型
"""

from typing import Dict, List, Optional, Any
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
import numpy as np

class LLMManager:
    """LLM 模型管理器"""

    def __init__(self, config: Dict):
        """
        初始化 LLM 管理器
        
        Args:
            config: 配置參數
        """
        self.config = config
        self._init_models()

    def _init_models(self):
        """初始化模型"""
        # 初始化 Qwen3
        self.qwen3_tokenizer = AutoTokenizer.from_pretrained(
            self.config["qwen3_model_path"],
            trust_remote_code=True
        )
        self.qwen3_model = AutoModelForCausalLM.from_pretrained(
            self.config["qwen3_model_path"],
            device_map="auto",
            trust_remote_code=True
        )

        # 初始化 BGE-M3
        self.bge_model = SentenceTransformer(
            self.config["bge_model_path"],
            device="cuda" if torch.cuda.is_available() else "cpu"
        )

        # 初始化 Deepseek R1
        self.deepseek_tokenizer = AutoTokenizer.from_pretrained(
            self.config["deepseek_model_path"],
            trust_remote_code=True
        )
        self.deepseek_model = AutoModelForCausalLM.from_pretrained(
            self.config["deepseek_model_path"],
            device_map="auto",
            trust_remote_code=True
        )

    async def generate_text(
        self,
        prompt: str,
        model: str = "qwen3",
        max_length: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示文本
            model: 模型名稱（qwen3 或 deepseek）
            max_length: 最大生成長度
            temperature: 溫度參數
            top_p: top-p 採樣參數
            
        Returns:
            str: 生成的文本
        """
        try:
            if model == "qwen3":
                tokenizer = self.qwen3_tokenizer
                model = self.qwen3_model
            else:
                tokenizer = self.deepseek_tokenizer
                model = self.deepseek_model

            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=True
            )
            return tokenizer.decode(outputs[0], skip_special_tokens=True)

        except Exception as e:
            print(f"生成文本時發生錯誤: {str(e)}")
            return ""

    async def get_embeddings(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        獲取文本嵌入
        
        Args:
            texts: 文本列表
            batch_size: 批次大小
            
        Returns:
            np.ndarray: 文本嵌入矩陣
        """
        try:
            embeddings = self.bge_model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True
            )
            return embeddings

        except Exception as e:
            print(f"獲取嵌入時發生錯誤: {str(e)}")
            return np.array([])

    async def semantic_search(
        self,
        query: str,
        corpus: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        語義搜索
        
        Args:
            query: 查詢文本
            corpus: 文本語料庫
            top_k: 返回結果數量
            
        Returns:
            List[Dict[str, Any]]: 搜索結果
        """
        try:
            # 獲取查詢和語料庫的嵌入
            query_embedding = await self.get_embeddings([query])
            corpus_embeddings = await self.get_embeddings(corpus)

            # 計算相似度
            similarities = np.dot(corpus_embeddings, query_embedding.T).flatten()

            # 獲取 top-k 結果
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            results = [
                {
                    "text": corpus[idx],
                    "score": float(similarities[idx])
                }
                for idx in top_indices
            ]

            return results

        except Exception as e:
            print(f"語義搜索時發生錯誤: {str(e)}")
            return []

    def update_config(self, new_config: Dict):
        """
        更新配置
        
        Args:
            new_config: 新的配置參數
        """
        self.config.update(new_config)
        self._init_models() 