#!/usr/bin/env python3
"""
Podwise VADER Sentiment Analysis 主模組

提供統一的 OOP 介面，整合所有情感分析功能：
- 中文情感分析
- VADER 情感分析
- 文本預處理
- 詞彙管理
- 數據處理
- 可視化介面

作者: Podwise Team
版本: 2.0.0
"""

import logging
import os
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 導入核心模組
from .core.sentiment_analyzer import ChineseSentimentAnalyzer, VADERSentimentAnalyzer, SentimentResult
from .core.text_preprocessor import TextPreprocessor
from .core.lexicon_manager import LexiconManager
from .core.data_processor import DataProcessor, ProcessedItem


class PodwiseSentimentAnalysis:
    """
    Podwise 情感分析主類別
    
    提供統一的情感分析介面，整合所有相關功能
    符合 OOP 和 Google Clean Code 原則
    """
    
    def __init__(self, 
                 data_directory: str = "comment_data",
                 enable_chinese_analysis: bool = True,
                 enable_vader_analysis: bool = True,
                 enable_visualization: bool = True):
        """
        初始化情感分析系統
        
        Args:
            data_directory: 數據目錄路徑
            enable_chinese_analysis: 是否啟用中文情感分析
            enable_vader_analysis: 是否啟用 VADER 情感分析
            enable_visualization: 是否啟用可視化功能
        """
        self.data_directory = data_directory
        self.enable_chinese_analysis = enable_chinese_analysis
        self.enable_vader_analysis = enable_vader_analysis
        self.enable_visualization = enable_visualization
        
        # 初始化文本預處理器
        self.text_preprocessor = TextPreprocessor()
        
        # 初始化詞彙管理器
        self.lexicon_manager = LexiconManager()
        
        # 初始化數據處理器
        self.data_processor = DataProcessor(data_directory)
        
        # 初始化情感分析器
        self._initialize_analyzers()
        
        logger.info("✅ Podwise 情感分析系統初始化完成")
    
    def _initialize_analyzers(self):
        """初始化情感分析器"""
        self.analyzers = {}
        
        if self.enable_chinese_analysis:
            self.analyzers['chinese'] = ChineseSentimentAnalyzer()
            logger.info("✅ 中文情感分析器已初始化")
        
        if self.enable_vader_analysis:
            self.analyzers['vader'] = VADERSentimentAnalyzer()
            logger.info("✅ VADER 情感分析器已初始化")
    
    def analyze_text(self, 
                    text: str, 
                    analyzer_type: str = "chinese",
                    preprocess: bool = True) -> SentimentResult:
        """
        分析單一文本的情感
        
        Args:
            text: 要分析的文本
            analyzer_type: 分析器類型 ('chinese' 或 'vader')
            preprocess: 是否進行文本預處理
            
        Returns:
            SentimentResult: 情感分析結果
        """
        try:
            if not text.strip():
                raise ValueError("文本內容不能為空")
            
            # 文本預處理
            if preprocess:
                text = self.text_preprocessor.clean_text(text)
            
            # 選擇分析器
            if analyzer_type not in self.analyzers:
                raise ValueError(f"不支援的分析器類型: {analyzer_type}")
            
            analyzer = self.analyzers[analyzer_type]
            result = analyzer.analyze(text)
            
            logger.info(f"✅ 文本情感分析完成 - 類型: {analyzer_type}, 情感: {result.label}")
            return result
            
        except Exception as e:
            logger.error(f"文本情感分析失敗: {e}")
            # 返回預設結果
            return SentimentResult(
                compound=0.0,
                positive=0.0,
                negative=0.0,
                neutral=1.0,
                label="neutral",
                confidence=0.0
            )
    
    def analyze_multiple_texts(self, 
                             texts: List[str], 
                             analyzer_type: str = "chinese",
                             preprocess: bool = True) -> List[SentimentResult]:
        """
        分析多個文本的情感
        
        Args:
            texts: 要分析的文本列表
            analyzer_type: 分析器類型
            preprocess: 是否進行文本預處理
            
        Returns:
            List[SentimentResult]: 情感分析結果列表
        """
        results = []
        
        for i, text in enumerate(texts):
            try:
                result = self.analyze_text(text, analyzer_type, preprocess)
                results.append(result)
                logger.info(f"✅ 文本 {i+1}/{len(texts)} 分析完成")
            except Exception as e:
                logger.error(f"文本 {i+1} 分析失敗: {e}")
                # 添加預設結果
                results.append(SentimentResult(
                    compound=0.0,
                    positive=0.0,
                    negative=0.0,
                    neutral=1.0,
                    label="neutral",
                    confidence=0.0
                ))
        
        return results
    
    def analyze_json_files(self, 
                          output_file: str = "sentiment_analysis_results.csv",
                          analyzer_type: str = "chinese") -> Dict[str, Any]:
        """
        分析 JSON 檔案中的數據
        
        Args:
            output_file: 輸出檔案名稱
            analyzer_type: 分析器類型
            
        Returns:
            Dict[str, Any]: 分析結果摘要
        """
        try:
            # 處理目錄中的所有 JSON 檔案
            processed_items = self.data_processor.process_directory()
            
            if not processed_items:
                logger.warning("沒有找到可處理的 JSON 檔案")
                return {"success": False, "message": "沒有找到可處理的檔案"}
            
            # 分析每個處理後的項目
            analysis_results = []
            for item in processed_items:
                sentiment_result = self.analyze_text(
                    item.content, 
                    analyzer_type, 
                    preprocess=True
                )
                
                analysis_results.append({
                    'filename': item.filename,
                    'field_type': item.field_type,
                    'content': item.content,
                    'compound': sentiment_result.compound,
                    'positive': sentiment_result.positive,
                    'negative': sentiment_result.negative,
                    'neutral': sentiment_result.neutral,
                    'label': sentiment_result.label,
                    'confidence': sentiment_result.confidence
                })
            
            # 保存結果到 CSV
            import pandas as pd
            df = pd.DataFrame(analysis_results)
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            # 計算統計資訊
            stats = self._calculate_statistics(analysis_results)
            
            logger.info(f"✅ JSON 檔案分析完成，結果已保存到 {output_file}")
            return {
                "success": True,
                "total_files": len(processed_items),
                "output_file": output_file,
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"JSON 檔案分析失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算分析結果統計資訊"""
        if not results:
            return {}
        
        # 情感標籤統計
        label_counts = {}
        compound_scores = []
        positive_scores = []
        negative_scores = []
        neutral_scores = []
        
        for result in results:
            label = result['label']
            label_counts[label] = label_counts.get(label, 0) + 1
            
            compound_scores.append(result['compound'])
            positive_scores.append(result['positive'])
            negative_scores.append(result['negative'])
            neutral_scores.append(result['neutral'])
        
        # 計算平均值
        avg_compound = sum(compound_scores) / len(compound_scores)
        avg_positive = sum(positive_scores) / len(positive_scores)
        avg_negative = sum(negative_scores) / len(negative_scores)
        avg_neutral = sum(neutral_scores) / len(neutral_scores)
        
        return {
            "total_analyzed": len(results),
            "label_distribution": label_counts,
            "average_scores": {
                "compound": round(avg_compound, 3),
                "positive": round(avg_positive, 3),
                "negative": round(avg_negative, 3),
                "neutral": round(avg_neutral, 3)
            },
            "score_ranges": {
                "compound": {"min": min(compound_scores), "max": max(compound_scores)},
                "positive": {"min": min(positive_scores), "max": max(positive_scores)},
                "negative": {"min": min(negative_scores), "max": max(negative_scores)},
                "neutral": {"min": min(neutral_scores), "max": max(neutral_scores)}
            }
        }
    
    def fix_data_format(self) -> int:
        """
        修復數據格式問題
        
        Returns:
            int: 修復的檔案數量
        """
        try:
            fixed_count = self.data_processor.batch_fix_json_format()
            logger.info(f"✅ 數據格式修復完成，共修復 {fixed_count} 個檔案")
            return fixed_count
        except Exception as e:
            logger.error(f"數據格式修復失敗: {e}")
            return 0
    
    def get_lexicon_info(self) -> Dict[str, int]:
        """獲取詞彙庫資訊"""
        try:
            positive_words = self.lexicon_manager.get_positive_words()
            negative_words = self.lexicon_manager.get_negative_words()
            intensifiers = self.lexicon_manager.get_intensifiers()
            negations = self.lexicon_manager.get_negations()
            
            return {
                "positive_words": len(positive_words),
                "negative_words": len(negative_words),
                "intensifiers": len(intensifiers),
                "negations": len(negations),
                "total_words": len(positive_words) + len(negative_words) + len(intensifiers) + len(negations)
            }
        except Exception as e:
            logger.error(f"獲取詞彙庫資訊失敗: {e}")
            return {}
    
    def create_visualization(self, 
                           results_file: str = "sentiment_analysis_results.csv",
                           output_dir: str = "visualizations") -> Dict[str, Any]:
        """
        創建可視化圖表
        
        Args:
            results_file: 結果檔案路徑
            output_dir: 輸出目錄
            
        Returns:
            Dict[str, Any]: 可視化結果
        """
        if not self.enable_visualization:
            return {"success": False, "message": "可視化功能已停用"}
        
        try:
            # 確保輸出目錄存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 導入可視化腳本
            from .scripts.interactive_dashboard import InteractiveAnalyzer, InteractiveVisualizer
            
            # 創建分析器
            analyzer = InteractiveAnalyzer()
            
            # 分析數據
            data = analyzer.analyze_data(self.data_directory)
            
            # 創建可視化器
            visualizer = InteractiveVisualizer()
            
            # 生成圖表
            polar_chart = visualizer.create_polar_chart(data)
            bar_chart = visualizer.create_bar_chart(data)
            
            # 保存圖表
            polar_chart_path = os.path.join(output_dir, "sentiment_polarity_chart.html")
            bar_chart_path = os.path.join(output_dir, "sentiment_bar_chart.html")
            
            with open(polar_chart_path, 'w', encoding='utf-8') as f:
                f.write(polar_chart)
            
            with open(bar_chart_path, 'w', encoding='utf-8') as f:
                f.write(bar_chart)
            
            logger.info(f"✅ 可視化圖表已生成並保存到 {output_dir}")
            return {
                "success": True,
                "output_directory": output_dir,
                "files": [polar_chart_path, bar_chart_path]
            }
            
        except Exception as e:
            logger.error(f"創建可視化失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "text_preprocessor": self.text_preprocessor is not None,
                "lexicon_manager": self.lexicon_manager is not None,
                "data_processor": self.data_processor is not None,
                "chinese_analyzer": "chinese" in self.analyzers,
                "vader_analyzer": "vader" in self.analyzers
            },
            "config": {
                "data_directory": self.data_directory,
                "enable_chinese_analysis": self.enable_chinese_analysis,
                "enable_vader_analysis": self.enable_vader_analysis,
                "enable_visualization": self.enable_visualization
            },
            "lexicon_info": self.get_lexicon_info()
        }
        
        # 檢查各組件健康狀態
        for component, status in health_status["components"].items():
            if not status:
                health_status["status"] = "degraded"
        
        return health_status
    
    def get_system_info(self) -> Dict[str, Any]:
        """獲取系統資訊"""
        return {
            "version": "2.0.0",
            "name": "Podwise VADER Sentiment Analysis",
            "description": "整合中文和 VADER 情感分析的智能系統",
            "features": [
                "中文情感分析",
                "VADER 情感分析",
                "文本預處理",
                "詞彙管理",
                "數據處理",
                "可視化介面"
            ],
            "supported_analyzers": list(self.analyzers.keys())
        }


# 全域實例
_sentiment_analysis_instance: Optional[PodwiseSentimentAnalysis] = None


def get_sentiment_analysis() -> PodwiseSentimentAnalysis:
    """獲取情感分析實例（單例模式）"""
    global _sentiment_analysis_instance
    if _sentiment_analysis_instance is None:
        _sentiment_analysis_instance = PodwiseSentimentAnalysis()
    return _sentiment_analysis_instance


def main():
    """主函數 - 用於測試"""
    # 創建情感分析實例
    analyzer = PodwiseSentimentAnalysis()
    
    # 測試文本分析
    test_text = "這個 Podcast 真的很棒，內容很有深度！"
    print(f"測試文本: {test_text}")
    
    # 中文情感分析
    chinese_result = analyzer.analyze_text(test_text, "chinese")
    print(f"中文分析結果: {chinese_result.label} (信心度: {chinese_result.confidence:.3f})")
    
    # VADER 情感分析
    vader_result = analyzer.analyze_text(test_text, "vader")
    print(f"VADER 分析結果: {vader_result.label} (信心度: {vader_result.confidence:.3f})")
    
    # 健康檢查
    health = analyzer.health_check()
    print(f"健康狀態: {health['status']}")
    
    # 詞彙庫資訊
    lexicon_info = analyzer.get_lexicon_info()
    print(f"詞彙庫資訊: {lexicon_info}")


if __name__ == "__main__":
    main() 