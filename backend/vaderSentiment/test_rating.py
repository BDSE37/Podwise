#!/usr/bin/env python3
"""
綜合評分系統測試腳本
"""

import sys
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import pandas as pd

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RatingWeights:
    """評分權重配置"""
    apple_rating: float = 0.40      # Apple podcast 星等 40%
    comment_sentiment: float = 0.35 # Apple podcast 評論文字分析 35%
    user_engagement: float = 0.15   # 使用者點擊率（問卷喜好度）15%
    comment_count: float = 0.10     # Apple podcast 評論數 10%


class SimpleRatingSystem:
    """簡化版綜合評分系統"""
    
    def __init__(self, weights: Optional[RatingWeights] = None):
        """初始化評分系統"""
        self.weights = weights or RatingWeights()
        self.podcast_info_dir = Path("Podcast_info")
        self.testdata_dir = Path("../testdata")
        
        logger.info("簡化評分系統初始化完成")
    
    def extract_apple_rating(self, rating_text: str) -> Tuple[float, int]:
        """從 Apple podcast 評分文字中提取星等和評論數"""
        try:
            # 提取星等
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            rating = float(rating_match.group(1)) if rating_match else 0.0
            
            # 提取評論數
            count_match = re.search(r'（(\d+)則評分）', rating_text)
            count = int(count_match.group(1)) if count_match else 0
            
            return rating, count
        except Exception as e:
            logger.warning(f"提取 Apple 評分失敗: {rating_text}, 錯誤: {e}")
            return 0.0, 0
    
    def get_user_engagement_score(self, podcast_id: str) -> float:
        """從 testdata 獲取使用者參與度分數"""
        try:
            # 讀取使用者回饋資料
            feedback_file = self.testdata_dir / "user_feedback.csv"
            if not feedback_file.exists():
                logger.warning(f"使用者回饋檔案不存在: {feedback_file}")
                return 3.0  # 預設中等分數
            
            df = pd.read_csv(feedback_file)
            
            # 如果沒有找到對應資料，返回整體平均分數
            if 'satisfaction_score' in df.columns:
                return df['satisfaction_score'].mean()
            elif 'rating' in df.columns:
                return df['rating'].mean()
            else:
                return 3.0
                
        except Exception as e:
            logger.error(f"獲取使用者參與度分數失敗: {e}")
            return 3.0
    
    def calculate_weighted_score(self, 
                               apple_rating: float,
                               comment_sentiment: float,
                               user_engagement: float,
                               comment_count: int) -> float:
        """計算加權綜合分數"""
        # 將評論情感分數從 (-1,1) 轉換為 (0,5)
        sentiment_score = (comment_sentiment + 1) * 2.5
        
        # 評論數標準化 (假設 1000 評論為滿分)
        comment_score = min(comment_count / 1000.0, 1.0) * 5.0
        
        # 計算加權分數
        weighted_score = (
            apple_rating * self.weights.apple_rating +
            sentiment_score * self.weights.comment_sentiment +
            user_engagement * self.weights.user_engagement +
            comment_score * self.weights.comment_count
        )
        
        return round(weighted_score, 2)
    
    def load_podcast_data(self) -> List[Dict]:
        """載入所有 Podcast 資料"""
        podcasts = []
        
        try:
            for json_file in self.podcast_info_dir.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 提取基本資訊
                    podcast_id = json_file.stem
                    title = data.get('title', '')
                    category = data.get('category', '')
                    rating_text = data.get('rating', '0.0（0則評分）')
                    comments = data.get('comments', [])
                    
                    # 提取 Apple 評分
                    apple_rating, comment_count = self.extract_apple_rating(rating_text)
                    
                    # 簡單的情感分析（基於評論數量）
                    sentiment_score = 0.0  # 簡化版本，實際應該使用 VADER
                    
                    # 獲取使用者參與度
                    user_engagement = self.get_user_engagement_score(podcast_id)
                    
                    # 計算加權分數
                    weighted_score = self.calculate_weighted_score(
                        apple_rating, sentiment_score, user_engagement, comment_count
                    )
                    
                    podcast_data = {
                        'podcast_id': podcast_id,
                        'title': title,
                        'category': category,
                        'apple_rating': apple_rating,
                        'apple_rating_count': comment_count,
                        'comment_sentiment_score': sentiment_score,
                        'user_engagement_score': user_engagement,
                        'comment_count': len(comments),
                        'weighted_score': weighted_score
                    }
                    
                    podcasts.append(podcast_data)
                    
                except Exception as e:
                    logger.error(f"載入 Podcast 資料失敗 {json_file}: {e}")
                    continue
            
            logger.info(f"成功載入 {len(podcasts)} 個 Podcast 資料")
            return podcasts
            
        except Exception as e:
            logger.error(f"載入 Podcast 資料目錄失敗: {e}")
            return []
    
    def generate_rating_report(self) -> pd.DataFrame:
        """生成評分報告"""
        podcasts = self.load_podcast_data()
        
        if not podcasts:
            logger.warning("沒有找到 Podcast 資料")
            return pd.DataFrame()
        
        # 轉換為 DataFrame
        df = pd.DataFrame(podcasts)
        
        # 按加權分數排序
        df = df.sort_values('weighted_score', ascending=False)
        
        # 添加排名
        df['rank'] = range(1, len(df) + 1)
        
        # 重新排列欄位順序
        columns_order = [
            'rank', 'podcast_id', 'title', 'category', 'weighted_score',
            'apple_rating', 'comment_sentiment_score', 'user_engagement_score', 
            'comment_count', 'apple_rating_count'
        ]
        
        df = df[columns_order]
        
        logger.info(f"生成評分報告，包含 {len(df)} 個 Podcast")
        return df
    
    def save_rating_report(self, output_file: str = "podcast_rating_report.csv") -> None:
        """儲存評分報告"""
        try:
            df = self.generate_rating_report()
            if not df.empty:
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                logger.info(f"評分報告已儲存至: {output_file}")
                
                # 顯示前 10 名
                print("\n=== Podcast 綜合評分排行榜 (前 10 名) ===")
                print(df.head(10).to_string(index=False))
                
                # 顯示評分權重說明
                print(f"\n=== 評分權重配置 ===")
                print(f"Apple podcast 星等: {self.weights.apple_rating * 100}%")
                print(f"Apple podcast 評論文字分析: {self.weights.comment_sentiment * 100}%")
                print(f"使用者點擊率（問卷喜好度）: {self.weights.user_engagement * 100}%")
                print(f"Apple podcast 評論數: {self.weights.comment_count * 100}%")
                
            else:
                logger.warning("沒有資料可儲存")
                
        except Exception as e:
            logger.error(f"儲存評分報告失敗: {e}")
    
    def get_category_analysis(self) -> Dict[str, pd.DataFrame]:
        """按分類分析評分"""
        df = self.generate_rating_report()
        
        if df.empty:
            return {}
        
        category_analysis = {}
        
        for category in df['category'].unique():
            category_df = df[df['category'] == category].copy()
            category_df = category_df.sort_values('weighted_score', ascending=False)
            category_df['category_rank'] = range(1, len(category_df) + 1)
            category_analysis[category] = category_df
        
        return category_analysis


def main():
    """主函數"""
    print("🎯 Podcast 綜合評分系統測試")
    print("=" * 50)
    
    try:
        # 初始化評分系統
        rating_system = SimpleRatingSystem()
        
        # 生成評分報告
        rating_system.save_rating_report()
        
        # 按分類分析
        category_analysis = rating_system.get_category_analysis()
        
        # 顯示分類分析結果
        for category, df in category_analysis.items():
            print(f"\n=== {category} 分類評分排行榜 ===")
            print(df.head(5).to_string(index=False))
        
        print(f"\n✅ 綜合評分分析完成！")
        
    except Exception as e:
        print(f"\n❌ 執行失敗: {e}")
        logger.error(f"程式執行失敗: {e}")


if __name__ == "__main__":
    main() 