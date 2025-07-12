#!/usr/bin/env python3
"""
Podcast 情感分析與綜合評分系統主程式
整合情感分析、排名分析、評論分析與綜合評分功能
"""

import argparse
import logging
import sys
from pathlib import Path

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.sentiment_analyzer import SentimentAnalyzer
from src.core.podcast_ranking import PodcastRankingAnalyzer
from src.core.comment_analyzer import CommentAnalyzer
from src.core.rating_system import RatingSystem, RatingWeights
from src.utils.data_processor import DataProcessor
from src.utils.report_generator import ReportGenerator

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PodcastAnalysisSystem:
    """Podcast 分析系統主類別"""
    
    def __init__(self):
        """初始化分析系統"""
        self.sentiment_analyzer = SentimentAnalyzer()
        self.ranking_analyzer = PodcastRankingAnalyzer()
        self.comment_analyzer = CommentAnalyzer()
        self.rating_system = RatingSystem()
        self.data_processor = DataProcessor()
        self.report_generator = ReportGenerator()
        
        logger.info("Podcast 分析系統初始化完成")
    
    def run_sentiment_analysis(self, category: str = None) -> None:
        """
        執行情感分析
        
        Args:
            category: 指定分類（商業/教育），None 表示分析全部
        """
        logger.info(f"開始執行情感分析，分類: {category or '全部'}")
        
        try:
            # 執行情感分析
            results = self.sentiment_analyzer.analyze_all_podcasts(category)
            
            # 生成報告
            self.report_generator.generate_sentiment_report(results, category)
            
            logger.info("情感分析完成")
            
        except Exception as e:
            logger.error(f"情感分析失敗: {e}")
            raise
    
    def run_ranking_analysis(self) -> None:
        """執行排名分析"""
        logger.info("開始執行排名分析")
        
        try:
            # 執行排名分析
            results = self.ranking_analyzer.analyze_rankings()
            
            # 生成報告
            self.report_generator.generate_ranking_report(results)
            
            logger.info("排名分析完成")
            
        except Exception as e:
            logger.error(f"排名分析失敗: {e}")
            raise
    
    def run_comment_analysis(self) -> None:
        """執行評論分析"""
        logger.info("開始執行評論分析")
        
        try:
            # 執行評論分析
            results = self.comment_analyzer.analyze_all_comments()
            
            # 生成報告
            self.report_generator.generate_comment_report(results)
            
            logger.info("評論分析完成")
            
        except Exception as e:
            logger.error(f"評論分析失敗: {e}")
            raise
    
    def run_rating_analysis(self) -> None:
        """執行綜合評分分析"""
        logger.info("開始執行綜合評分分析")
        
        try:
            # 生成評分報告
            self.rating_system.save_rating_report()
            
            # 按分類分析
            category_analysis = self.rating_system.get_category_analysis()
            
            # 顯示分類分析結果
            for category, df in category_analysis.items():
                print(f"\n=== {category} 分類評分排行榜 ===")
                print(df.head(5).to_string(index=False))
            
            logger.info("綜合評分分析完成")
            
        except Exception as e:
            logger.error(f"綜合評分分析失敗: {e}")
            raise
    
    def run_complete_analysis(self) -> None:
        """執行完整分析流程"""
        logger.info("開始執行完整分析流程")
        
        try:
            # 1. 情感分析
            self.run_sentiment_analysis()
            
            # 2. 排名分析
            self.run_ranking_analysis()
            
            # 3. 評論分析
            self.run_comment_analysis()
            
            # 4. 綜合評分分析
            self.run_rating_analysis()
            
            logger.info("完整分析流程完成")
            
        except Exception as e:
            logger.error(f"完整分析流程失敗: {e}")
            raise
    
    def run_test(self) -> None:
        """執行測試"""
        logger.info("開始執行測試")
        
        try:
            # 測試情感分析
            test_result = self.sentiment_analyzer.test_sentiment_analysis()
            print(f"情感分析測試結果: {test_result}")
            
            # 測試評分系統
            test_podcast = {
                'apple_rating': 4.5,
                'comment_sentiment': 0.3,
                'user_engagement': 4.0,
                'comment_count': 500
            }
            
            weighted_score = self.rating_system.calculate_weighted_score(
                test_podcast['apple_rating'],
                test_podcast['comment_sentiment'],
                test_podcast['user_engagement'],
                test_podcast['comment_count']
            )
            
            print(f"評分系統測試結果: {weighted_score}")
            
            logger.info("測試完成")
            
        except Exception as e:
            logger.error(f"測試失敗: {e}")
            raise


def main():
    """主程式入口"""
    parser = argparse.ArgumentParser(
        description="Podcast 情感分析與綜合評分系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python main.py --mode sentiment                    # 執行情感分析
  python main.py --mode sentiment --category 商業    # 執行商業類情感分析
  python main.py --mode ranking                      # 執行排名分析
  python main.py --mode comment                      # 執行評論分析
  python main.py --mode rating                       # 執行綜合評分分析
  python main.py --mode complete                     # 執行完整分析
  python main.py --mode test                         # 執行測試
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['sentiment', 'ranking', 'comment', 'rating', 'complete', 'test'],
        default='complete',
        help='執行模式 (預設: complete)'
    )
    
    parser.add_argument(
        '--category',
        choices=['商業', '教育'],
        help='指定分類（僅適用於情感分析模式）'
    )
    
    parser.add_argument(
        '--output',
        default='reports',
        help='輸出目錄 (預設: reports)'
    )
    
    args = parser.parse_args()
    
    try:
        # 初始化分析系統
        system = PodcastAnalysisSystem()
        
        # 根據模式執行相應功能
        if args.mode == 'sentiment':
            system.run_sentiment_analysis(args.category)
        elif args.mode == 'ranking':
            system.run_ranking_analysis()
        elif args.mode == 'comment':
            system.run_comment_analysis()
        elif args.mode == 'rating':
            system.run_rating_analysis()
        elif args.mode == 'complete':
            system.run_complete_analysis()
        elif args.mode == 'test':
            system.run_test()
        
        print(f"\n✅ {args.mode} 模式執行完成！")
        
    except KeyboardInterrupt:
        print("\n❌ 使用者中斷執行")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 執行失敗: {e}")
        logger.error(f"程式執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 