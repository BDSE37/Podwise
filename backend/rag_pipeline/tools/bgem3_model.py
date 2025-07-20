#!/usr/bin/env python3
"""
Text2Vec Model

文字向量化工具，用於將文字轉為向量，亦可將向量反解為文字輔助除錯

功能：
- 文字向量化
- 向量反解為文字
- 批量向量化
- 向量正規化

作者: Podwise Team
版本: 1.0.0
"""

import logging
import numpy as np
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
import asyncio

# 嘗試導入 text2vec 相關庫
try:
    from sentence_transformers import SentenceTransformer
    TEXT2VEC_AVAILABLE = True
except ImportError:
    TEXT2VEC_AVAILABLE = False
    logging.warning("sentence_transformers 未安裝，將使用備援向量化方法")

logger = logging.getLogger(__name__)


@dataclass
class VectorizationResult:
    """向量化結果"""
    success: bool
    vector: Optional[List[float]] = None
    text: str = ""
    dimension: int = 0
    error_message: str = ""
    processing_time: float = 0.0


class Text2VecModel:
    """BGE-M3 模型"""
    
    def __init__(self, 
                 model_name: str = "bge-m3",
                 model_path: str = "BAAI/bge-m3",
                 max_length: int = 512,
                 batch_size: int = 32,
                 normalize_embeddings: bool = True,
                 pooling_strategy: str = "mean",
                 device: str = "auto"):
        """
        初始化 Text2Vec 模型
        
        Args:
            model_name: 模型名稱
            model_path: 模型路徑
            max_length: 最大長度
            batch_size: 批次大小
            normalize_embeddings: 是否正規化嵌入
            pooling_strategy: 池化策略
            device: 設備
        """
        self.model_name = model_name
        self.model_path = model_path
        self.max_length = max_length
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        self.pooling_strategy = pooling_strategy
        self.device = device
        self.model = None
        
        # 初始化模型
        self._initialize_model()
    
    def _initialize_model(self):
        """初始化模型"""
        try:
            if TEXT2VEC_AVAILABLE:
                # 修復設備配置問題
                device = self.device
                if device == "auto":
                    import torch
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                
                # 使用 sentence_transformers 載入 BGE-M3 模型
                self.model = SentenceTransformer(
                    self.model_path,
                    device=device
                )
                logger.info(f"✅ Text2Vec 模型初始化成功: {self.model_name} (設備: {device})")
            else:
                logger.warning("sentence_transformers 未安裝，將使用備援向量化方法")
                self.model = None
                
        except Exception as e:
            logger.error(f"Text2Vec 模型初始化失敗: {e}")
            self.model = None
    
    async def encode(self, text: str) -> VectorizationResult:
        """
        將文字轉為向量
        
        Args:
            text: 輸入文字
            
        Returns:
            VectorizationResult: 向量化結果
        """
        import time
        start_time = time.time()
        
        try:
            # 文字預處理
            processed_text = self._preprocess_text(text)
            
            if not processed_text:
                return VectorizationResult(
                    success=False,
                    text=text,
                    error_message="文字預處理失敗",
                    processing_time=time.time() - start_time
                )
            
            # 向量化
            if self.model is not None:
                vector = await self._encode_with_model(processed_text)
            else:
                vector = self._encode_fallback(processed_text)
            
            if vector is None:
                return VectorizationResult(
                    success=False,
                    text=text,
                    error_message="向量化失敗",
                    processing_time=time.time() - start_time
                )
            
            return VectorizationResult(
                success=True,
                vector=vector,
                text=text,
                dimension=len(vector),
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"文字向量化失敗: {e}")
            return VectorizationResult(
                success=False,
                text=text,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    async def encode_batch(self, texts: List[str]) -> List[VectorizationResult]:
        """
        批量向量化
        
        Args:
            texts: 文字列表
            
        Returns:
            List[VectorizationResult]: 向量化結果列表
        """
        results = []
        
        for text in texts:
            try:
                result = await self.encode(text)
                results.append(result)
            except Exception as e:
                logger.error(f"批量向量化失敗: {e}")
                results.append(VectorizationResult(
                    success=False,
                    text=text,
                    error_message=str(e)
                ))
        
        return results
    
    async def decode(self, vector: List[float]) -> str:
        """
        將向量反解為文字（輔助除錯功能）
        
        Args:
            vector: 輸入向量
            
        Returns:
            str: 反解的文字（簡化版本）
        """
        try:
            # 這是一個簡化的反解功能，實際的 text2vec 模型通常不支援直接反解
            # 這裡提供一個基於向量特徵的描述性文字
            
            vector_array = np.array(vector)
            
            # 計算向量特徵
            magnitude = np.linalg.norm(vector_array)
            mean_value = np.mean(vector_array)
            std_value = np.std(vector_array)
            
            # 生成描述性文字
            description = f"向量特徵: 維度={len(vector)}, 模長={magnitude:.3f}, 均值={mean_value:.3f}, 標準差={std_value:.3f}"
            
            return description
            
        except Exception as e:
            logger.error(f"向量反解失敗: {e}")
            return f"向量反解失敗: {str(e)}"
    
    def _preprocess_text(self, text: str) -> str:
        """
        文字預處理
        
        Args:
            text: 原始文字
            
        Returns:
            str: 處理後的文字
        """
        if not text or not text.strip():
            return ""
        
        # 移除多餘空白
        text = text.strip()
        
        # 限制長度
        if len(text) > self.max_length:
            text = text[:self.max_length]
        
        return text
    
    async def _encode_with_model(self, text: str) -> Optional[List[float]]:
        """
        使用模型進行向量化
        
        Args:
            text: 輸入文字
            
        Returns:
            Optional[List[float]]: 向量化結果
        """
        try:
            if self.model is None:
                return None
                
            # 使用 sentence_transformers 進行向量化
            embedding = self.model.encode(
                text,
                normalize_embeddings=self.normalize_embeddings
            )
            
            # 轉換為列表 - 修正向量處理
            import numpy as np
            
            # 直接轉換為 numpy 陣列然後轉為列表
            embedding_array = np.array(embedding, dtype=np.float64)
            vector = embedding_array.tolist()
            
            return vector
            
        except Exception as e:
            logger.error(f"模型向量化失敗: {e}")
            return None
    
    def _encode_fallback(self, text: str) -> List[float]:
        """
        備援向量化方法
        
        Args:
            text: 輸入文字
            
        Returns:
            List[float]: 簡化的向量表示
        """
        try:
            # 使用簡單的字符頻率作為向量特徵
            vector_size = 1024  # 修正為 1024 維以匹配 Milvus 期望
            vector = [0.0] * vector_size
            
            # 基於字符的簡單特徵提取
            for i, char in enumerate(text):
                if i >= vector_size:
                    break
                # 使用字符的 Unicode 值作為特徵
                vector[i] = ord(char) / 65536.0  # 正規化到 [0, 1]
            
            # 填充剩餘位置
            for i in range(len(text), vector_size):
                vector[i] = 0.0
            
            return vector
            
        except Exception as e:
            logger.error(f"備援向量化失敗: {e}")
            return [0.0] * 1024
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型資訊"""
        return {
            "model_name": self.model_name,
            "max_length": self.max_length,
            "normalize_embeddings": self.normalize_embeddings,
            "model_available": self.model is not None,
            "text2vec_available": TEXT2VEC_AVAILABLE
        }


def get_bgem3_model():
    """獲取 BGE-M3 模型實例"""
    return Text2VecModel()


async def test_bgem3_model():
    """測試 BGE-M3 模型"""
    model = get_bgem3_model()
    
    # 測試向量化
    test_text = "這是一個測試文字"
    result = await model.encode(test_text)
    
    print(f"向量化結果: {result}")
    
    # 測試反解
    if result.success and result.vector:
        decoded_text = await model.decode(result.vector)
        print(f"反解結果: {decoded_text}")
    
    # 測試批量向量化
    test_texts = ["第一個文字", "第二個文字", "第三個文字"]
    batch_results = await model.encode_batch(test_texts)
    
    print(f"批量向量化結果: {len(batch_results)} 個成功")


if __name__ == "__main__":
    asyncio.run(test_bgem3_model()) 