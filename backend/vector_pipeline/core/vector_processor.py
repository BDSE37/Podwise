"""
向量化處理器
負責生成文本嵌入向量
"""

import logging
from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class VectorProcessor:
    """向量化處理器"""
    
    def __init__(self, embedding_model: str = "BAAI/bge-m3", device: Optional[str] = None):
        """
        初始化向量化處理器
        
        Args:
            embedding_model: 嵌入模型名稱
            device: 設備 (cpu/cuda)
        """
        self.embedding_model = embedding_model
        self.device = device
        self.model: Optional[SentenceTransformer] = None
        
    def load_model(self) -> None:
        """載入嵌入模型"""
        if self.model is None:
            try:
                logger.info(f"載入嵌入模型: {self.embedding_model}")
                self.model = SentenceTransformer(self.embedding_model, device=self.device)
                logger.info("嵌入模型載入成功")
            except Exception as e:
                logger.error(f"載入嵌入模型失敗: {e}")
                raise
    
    def generate_embeddings(self, texts: List[str], normalize: bool = True, 
                          show_progress_bar: bool = True) -> np.ndarray:
        """
        生成文本嵌入向量
        
        Args:
            texts: 文本列表
            normalize: 是否正規化
            show_progress_bar: 是否顯示進度條
            
        Returns:
            嵌入向量陣列
        """
        self.load_model()
        
        if self.model is None:
            raise RuntimeError("模型未正確載入")
        
        try:
            embeddings = self.model.encode(
                texts, 
                normalize_embeddings=normalize,
                show_progress_bar=show_progress_bar
            )
            logger.info(f"生成 {len(embeddings)} 個嵌入向量，維度: {embeddings.shape[1]}")
            return embeddings
        except Exception as e:
            logger.error(f"生成嵌入向量失敗: {e}")
            raise
    
    def generate_single_embedding(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        生成單個文本的嵌入向量
        
        Args:
            text: 文本
            normalize: 是否正規化
            
        Returns:
            嵌入向量
        """
        return self.generate_embeddings([text], normalize=normalize, show_progress_bar=False)[0]
    
    def calculate_similarity(self, text1: str, text2: str, normalize: bool = True) -> float:
        """
        計算兩個文本的相似度
        
        Args:
            text1: 第一個文本
            text2: 第二個文本
            normalize: 是否正規化
            
        Returns:
            相似度分數 (0-1)
        """
        embeddings = self.generate_embeddings([text1, text2], normalize=normalize, show_progress_bar=False)
        similarity = cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0]
        return float(similarity)
    
    def calculate_similarities(self, query_text: str, texts: List[str], 
                             normalize: bool = True) -> List[float]:
        """
        計算查詢文本與多個文本的相似度
        
        Args:
            query_text: 查詢文本
            texts: 目標文本列表
            normalize: 是否正規化
            
        Returns:
            相似度分數列表
        """
        all_texts = [query_text] + texts
        embeddings = self.generate_embeddings(all_texts, normalize=normalize, show_progress_bar=False)
        
        query_embedding = embeddings[0:1]
        target_embeddings = embeddings[1:]
        
        similarities = cosine_similarity(query_embedding, target_embeddings)[0]
        return [float(sim) for sim in similarities]
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        獲取模型資訊
        
        Returns:
            模型資訊字典
        """
        self.load_model()
        
        if self.model is None:
            raise RuntimeError("模型未正確載入")
        
        return {
            'model_name': self.embedding_model,
            'max_seq_length': self.model.max_seq_length,
            'embedding_dimension': self.model.get_sentence_embedding_dimension(),
            'device': str(self.model.device)
        }
    
    def batch_generate_embeddings(self, texts: List[str], batch_size: int = 32,
                                 normalize: bool = True) -> np.ndarray:
        """
        批次生成嵌入向量
        
        Args:
            texts: 文本列表
            batch_size: 批次大小
            normalize: 是否正規化
            
        Returns:
            嵌入向量陣列
        """
        self.load_model()
        
        if self.model is None:
            raise RuntimeError("模型未正確載入")
        
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self.generate_embeddings(
                batch_texts, 
                normalize=normalize, 
                show_progress_bar=False
            )
            all_embeddings.append(batch_embeddings)
            
            logger.info(f"處理批次 {len(all_embeddings)}/{total_batches}")
        
        return np.vstack(all_embeddings) 