"""
統一的標籤管理器
整合 TAG_info.csv、tag_processor.py 和 smart_tag_extractor.py 的功能
提供分層的標籤提取策略：CSV優先 → 智能提取 → 備援提取
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 嘗試導入相關模組
try:
    from rag_pipeline.utils.tag_processor import TagProcessor
    TAG_PROCESSOR_AVAILABLE = True
except ImportError:
    TAG_PROCESSOR_AVAILABLE = False
    logging.warning("無法載入 TagProcessor")

try:
    from rag_pipeline.tools.smart_tag_extractor import SmartTagExtractor as RAGSmartTagExtractor
    SMART_TAG_EXTRACTOR_AVAILABLE = True
except ImportError:
    SMART_TAG_EXTRACTOR_AVAILABLE = False
    logging.warning("無法載入 SmartTagExtractor")

logger = logging.getLogger(__name__)


@dataclass
class TagExtractionResult:
    """標籤提取結果"""
    tags: List[str]
    confidence: float
    method: str  # "csv", "smart", "fallback"
    processing_time: float


class BaseTagExtractor(ABC):
    """標籤提取器抽象基類"""
    
    @abstractmethod
    def extract_tags(self, text: str, title: Optional[str] = None) -> TagExtractionResult:
        """提取標籤"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """檢查是否可用"""
        pass


class CSVTagExtractor(BaseTagExtractor):
    """基於 CSV 的標籤提取器"""
    
    def __init__(self, tag_csv_path: str):
        """
        初始化 CSV 標籤提取器
        
        Args:
            tag_csv_path: TAG_info.csv 檔案路徑
        """
        self.tag_csv_path = Path(tag_csv_path)
        self.tag_processor = None
        self._initialize()
    
    def _initialize(self):
        """初始化標籤處理器"""
        if TAG_PROCESSOR_AVAILABLE and self.tag_csv_path.exists():
            try:
                self.tag_processor = TagProcessor(str(self.tag_csv_path))
                logger.info(f"成功載入 CSV 標籤處理器: {self.tag_csv_path}")
            except Exception as e:
                logger.error(f"載入 CSV 標籤處理器失敗: {e}")
                self.tag_processor = None
        else:
            logger.warning(f"CSV 標籤處理器不可用或檔案不存在: {self.tag_csv_path}")
    
    def extract_tags(self, text: str, title: Optional[str] = None) -> TagExtractionResult:
        """從 CSV 提取標籤"""
        import time
        start_time = time.time()
        
        if not self.tag_processor:
            return TagExtractionResult(
                tags=[],
                confidence=0.0,
                method="csv",
                processing_time=time.time() - start_time
            )
        
        try:
            # 使用 TagProcessor 進行分類
            result = self.tag_processor.categorize_content(text, title)
            
            # 提取標籤（最多3個）
            tags = result.get('tags', [])[:3]
            confidence = result.get('confidence', 0.0)
            
            return TagExtractionResult(
                tags=tags,
                confidence=confidence,
                method="csv",
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"CSV 標籤提取失敗: {e}")
            return TagExtractionResult(
                tags=[],
                confidence=0.0,
                method="csv",
                processing_time=time.time() - start_time
            )
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        return self.tag_processor is not None


class SmartTagExtractor(BaseTagExtractor):
    """智能標籤提取器"""
    
    def __init__(self, existing_tags_file: Optional[str] = None):
        """
        初始化智能標籤提取器
        
        Args:
            existing_tags_file: 現有標籤檔案路徑
        """
        self.smart_extractor = None
        self._initialize(existing_tags_file)
    
    def _initialize(self, existing_tags_file: Optional[str]):
        """初始化智能提取器"""
        if SMART_TAG_EXTRACTOR_AVAILABLE:
            try:
                self.smart_extractor = RAGSmartTagExtractor(existing_tags_file)
                logger.info("成功載入智能標籤提取器")
            except Exception as e:
                logger.error(f"載入智能標籤提取器失敗: {e}")
                self.smart_extractor = None
        else:
            logger.warning("智能標籤提取器不可用")
    
    def extract_tags(self, text: str, title: Optional[str] = None) -> TagExtractionResult:
        """智能提取標籤"""
        import time
        start_time = time.time()
        
        if not self.smart_extractor:
            return TagExtractionResult(
                tags=[],
                confidence=0.0,
                method="smart",
                processing_time=time.time() - start_time
            )
        
        try:
            # 合併標題和內容
            query = f"{title} {text}" if title else text
            
            # 使用智能提取器
            result = self.smart_extractor.extract_smart_tags(query, text)
            
            # 提取標籤（最多3個）
            tags = result.extracted_tags[:3]
            confidence = result.confidence
            
            return TagExtractionResult(
                tags=tags,
                confidence=confidence,
                method="smart",
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"智能標籤提取失敗: {e}")
            return TagExtractionResult(
                tags=[],
                confidence=0.0,
                method="smart",
                processing_time=time.time() - start_time
            )
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        return self.smart_extractor is not None


class FallbackTagExtractor(BaseTagExtractor):
    """備援標籤提取器"""
    
    def __init__(self):
        """初始化備援提取器"""
        self.keyword_patterns = self._load_keyword_patterns()
    
    def _load_keyword_patterns(self) -> Dict[str, List[str]]:
        """載入關鍵字模式"""
        return {
            # 商業相關
            "商業": ["股票", "投資", "理財", "財經", "基金", "期貨", "外匯", "房地產", "創業", "企業", "管理"],
            "科技": ["AI", "人工智慧", "機器學習", "大數據", "雲端", "區塊鏈", "5G", "物聯網", "電動車"],
            "教育": ["學習", "教育", "培訓", "課程", "學校", "大學", "技能", "證照", "知識"],
            "職涯": ["職涯", "工作", "職場", "求職", "面試", "履歷", "薪資", "升遷", "轉職"],
            "生活": ["健康", "運動", "飲食", "旅遊", "美食", "攝影", "音樂", "電影", "書籍"],
            "時事": ["政治", "經濟", "社會", "環境", "疫情", "國際", "外交", "貿易"]
        }
    
    def extract_tags(self, text: str, title: Optional[str] = None) -> TagExtractionResult:
        """備援標籤提取"""
        import time
        start_time = time.time()
        
        try:
            # 合併標題和內容
            full_text = f"{title} {text}" if title else text
            full_text_lower = full_text.lower()
            
            # 基於關鍵字匹配
            matched_tags = []
            for category, keywords in self.keyword_patterns.items():
                for keyword in keywords:
                    if keyword.lower() in full_text_lower:
                        matched_tags.append(category)
                        break  # 每個類別只取一個標籤
            
            # 限制為最多3個標籤
            tags = matched_tags[:3]
            confidence = min(len(tags) / 3.0, 1.0)  # 基於匹配數量計算信心度
            
            return TagExtractionResult(
                tags=tags,
                confidence=confidence,
                method="fallback",
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"備援標籤提取失敗: {e}")
            return TagExtractionResult(
                tags=[],
                confidence=0.0,
                method="fallback",
                processing_time=time.time() - start_time
            )
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        return True  # 備援提取器總是可用


class UnifiedTagManager:
    """統一的標籤管理器"""
    
    def __init__(self, tag_csv_path: str = "TAG_info.csv"):
        """
        初始化統一標籤管理器
        
        Args:
            tag_csv_path: TAG_info.csv 檔案路徑
        """
        self.extractors = [
            CSVTagExtractor(tag_csv_path),      # 優先：CSV 標籤
            SmartTagExtractor(tag_csv_path),    # 次選：智能提取
            FallbackTagExtractor()              # 備援：關鍵字匹配
        ]
        
        logger.info("統一標籤管理器初始化完成")
        self._log_available_extractors()
    
    def _log_available_extractors(self):
        """記錄可用的提取器"""
        available = []
        for extractor in self.extractors:
            if extractor.is_available():
                available.append(extractor.__class__.__name__)
        
        logger.info(f"可用的標籤提取器: {', '.join(available)}")
    
    def extract_tags(self, text: str, title: Optional[str] = None) -> List[str]:
        """
        提取標籤（分層策略）
        
        Args:
            text: 文本內容
            title: 標題（可選）
            
        Returns:
            標籤列表（最多3個）
        """
        if not text.strip():
            return []
        
        # 按優先順序嘗試提取標籤
        for extractor in self.extractors:
            if not extractor.is_available():
                continue
            
            try:
                result = extractor.extract_tags(text, title)
                
                if result.tags and result.confidence > 0.3:  # 信心度閾值
                    logger.debug(f"使用 {result.method} 提取標籤: {result.tags} (信心度: {result.confidence:.2f})")
                    return result.tags
                    
            except Exception as e:
                logger.warning(f"{extractor.__class__.__name__} 提取失敗: {e}")
                continue
        
        # 如果所有提取器都失敗，返回空列表
        logger.warning("所有標籤提取器都失敗，返回空標籤列表")
        return []
    
    def extract_tags_with_details(self, text: str, title: Optional[str] = None) -> TagExtractionResult:
        """
        提取標籤並返回詳細資訊
        
        Args:
            text: 文本內容
            title: 標題（可選）
            
        Returns:
            標籤提取結果
        """
        if not text.strip():
            return TagExtractionResult(
                tags=[],
                confidence=0.0,
                method="none",
                processing_time=0.0
            )
        
        # 按優先順序嘗試提取標籤
        for extractor in self.extractors:
            if not extractor.is_available():
                continue
            
            try:
                result = extractor.extract_tags(text, title)
                
                if result.tags and result.confidence > 0.3:
                    return result
                    
            except Exception as e:
                logger.warning(f"{extractor.__class__.__name__} 提取失敗: {e}")
                continue
        
        # 返回空結果
        return TagExtractionResult(
            tags=[],
            confidence=0.0,
            method="none",
            processing_time=0.0
        )
    
    def get_extractor_status(self) -> Dict[str, bool]:
        """獲取提取器狀態"""
        return {
            extractor.__class__.__name__: extractor.is_available()
            for extractor in self.extractors
        } 