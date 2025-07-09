#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
繁體中文情感分析系統 - 主程式

整合所有功能模組，提供統一的介面
"""

import os
import sys
import pandas as pd
from typing import List, Dict, Any

# 添加 core 模組到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

from core import (
    TextPreprocessor,
    ChineseSentimentAnalyzer,
    VADERSentimentAnalyzer,
    DataProcessor,
    LexiconManager
)


class SentimentAnalysisSystem:
    """情感分析系統主類別"""
    
    def __init__(self, data_directory: str = "comment_data"):
        """
        初始化系統
        
        Args:
            data_directory: 資料目錄路徑
        """
        self.data_directory = data_directory
        self.data_processor = DataProcessor(data_directory)
        self.chinese_analyzer = ChineseSentimentAnalyzer()
        self.vader_analyzer = VADERSentimentAnalyzer()
        self.lexicon_manager = LexiconManager()
    
    def analyze_single_text(self, text: str, use_chinese: bool = True) -> Dict[str, Any]:
        """
        分析單一文本
        
        Args:
            text: 輸入文本
            use_chinese: 是否使用中文分析器
            
        Returns:
            分析結果
        """
        if use_chinese:
            result = self.chinese_analyzer.analyze(text)
        else:
            result = self.vader_analyzer.analyze(text)
        
        return {
            'compound': result.compound,
            'positive': result.positive,
            'negative': result.negative,
            'neutral': result.neutral,
            'label': result.label,
            'confidence': result.confidence
        }
    
    def analyze_directory(self, output_file: str = "sentiment_analysis_results.csv") -> pd.DataFrame:
        """
        分析整個目錄的檔案
        
        Args:
            output_file: 輸出檔案路徑
            
        Returns:
            分析結果 DataFrame
        """
        print("開始處理資料...")
        
        # 處理資料
        items = self.data_processor.process_directory()
        print(f"處理了 {len(items)} 個資料項目")
        
        if not items:
            print("沒有找到有效的資料項目")
            return pd.DataFrame()
        
        # 分析情感
        results = []
        for i, item in enumerate(items):
            if i % 100 == 0:
                print(f"分析進度: {i}/{len(items)}")
            
            # 中文分析
            chinese_result = self.chinese_analyzer.analyze(item.content)
            
            # VADER 分析
            vader_result = self.vader_analyzer.analyze(item.content)
            
            results.append({
                'filename': item.filename,
                'content': item.content,
                'field_type': item.field_type,
                'chinese_compound': chinese_result.compound,
                'chinese_positive': chinese_result.positive,
                'chinese_negative': chinese_result.negative,
                'chinese_neutral': chinese_result.neutral,
                'chinese_label': chinese_result.label,
                'chinese_confidence': chinese_result.confidence,
                'vader_compound': vader_result.compound,
                'vader_positive': vader_result.positive,
                'vader_negative': vader_result.negative,
                'vader_neutral': vader_result.neutral,
                'vader_label': vader_result.label,
                'vader_confidence': vader_result.confidence
            })
        
        # 轉換為 DataFrame
        df = pd.DataFrame(results)
        
        # 儲存結果
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"分析結果已儲存至: {output_file}")
        
        # 印出統計資訊
        self._print_statistics(df)
        
        return df
    
    def _print_statistics(self, df: pd.DataFrame) -> None:
        """印出統計資訊"""
        print("\n=== 情感分析統計 ===")
        print(f"總分析數: {len(df)}")
        
        print("\n中文分析結果:")
        chinese_counts = df['chinese_label'].value_counts()
        for label, count in chinese_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {label}: {count} ({percentage:.1f}%)")
        
        print("\nVADER 分析結果:")
        vader_counts = df['vader_label'].value_counts()
        for label, count in vader_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {label}: {count} ({percentage:.1f}%)")
        
        print(f"\n平均中文情感分數: {df['chinese_compound'].mean():.3f}")
        print(f"平均 VADER 情感分數: {df['vader_compound'].mean():.3f}")
    
    def fix_data_format(self) -> int:
        """
        修正資料格式
        
        Returns:
            修正的檔案數量
        """
        print("開始修正資料格式...")
        fixed_count = self.data_processor.batch_fix_json_format()
        return fixed_count
    
    def get_lexicon_info(self) -> Dict[str, int]:
        """獲取詞典資訊"""
        return {
            'positive_words': len(self.lexicon_manager.get_positive_words()),
            'negative_words': len(self.lexicon_manager.get_negative_words()),
            'intensifiers': len(self.lexicon_manager.get_intensifiers()),
            'negations': len(self.lexicon_manager.get_negations())
        }


def main():
    """主函數"""
    print("繁體中文情感分析系統")
    print("=" * 50)
    
    # 初始化系統
    system = SentimentAnalysisSystem()
    
    # 檢查資料目錄
    if not os.path.exists(system.data_directory):
        print(f"錯誤: 資料目錄不存在: {system.data_directory}")
        return
    
    # 顯示詞典資訊
    lexicon_info = system.get_lexicon_info()
    print("詞典資訊:")
    for key, count in lexicon_info.items():
        print(f"  {key}: {count} 個詞彙")
    
    print("\n開始分析...")
    
    # 執行分析
    df = system.analyze_directory()
    
    if not df.empty:
        print("\n分析完成！")
    else:
        print("\n分析失敗或沒有資料")


if __name__ == "__main__":
    main() 