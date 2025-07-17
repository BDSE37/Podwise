#!/usr/bin/env python3
"""
ML Pipeline 資料設定腳本

為 ML Pipeline 準備測試資料和模擬資料
作者: Podwise Team
版本: 1.0.0
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


class MLPipelineDataSetup:
    """ML Pipeline 資料設定器"""
    
    def __init__(self):
        self.podcast_categories = [
            "商業財經", "科技創新", "教育學習", "健康生活", 
            "娛樂休閒", "社會文化", "國際新聞", "科學探索"
        ]
        
        self.podcast_names = [
            "商業週刊", "科技早知道", "學習成長", "健康生活指南",
            "娛樂新聞", "社會觀察", "國際視野", "科學探索"
        ]
    
    def create_mock_podcast_data(self, num_episodes: int = 100) -> pd.DataFrame:
        """創建模擬 Podcast 資料"""
        logger.info(f"創建 {num_episodes} 個模擬 Podcast 資料")
        
        data = []
        for i in range(num_episodes):
            episode = {
                'episode_id': f'episode_{i+1:04d}',
                'episode_title': f'{random.choice(self.podcast_names)} - 第{i+1}集',
                'description': f'這是第{i+1}集的詳細描述，包含豐富的內容和資訊。',
                'category': random.choice(self.podcast_categories),
                'tags': self._generate_random_tags(),
                'duration': random.randint(1800, 7200),  # 30-120分鐘
                'publish_date': datetime.now() - timedelta(days=random.randint(1, 365)),
                'rating': round(random.uniform(3.5, 5.0), 1),
                'view_count': random.randint(100, 10000),
                'like_count': random.randint(10, 1000)
            }
            data.append(episode)
        
        df = pd.DataFrame(data)
        logger.info(f"✅ 創建 Podcast 資料成功: {len(df)} 筆")
        return df
    
    def create_mock_user_history(self, num_users: int = 50, num_interactions: int = 200) -> pd.DataFrame:
        """創建模擬用戶歷史資料"""
        logger.info(f"創建 {num_users} 個用戶的 {num_interactions} 筆互動資料")
        
        data = []
        for i in range(num_interactions):
            interaction = {
                'user_id': f'user_{random.randint(1, num_users):03d}',
                'episode_id': f'episode_{random.randint(1, 100):04d}',
                'rating': random.randint(1, 5),
                'like_count': random.randint(0, 10),
                'preview_play_count': random.randint(0, 50),
                'interaction_date': datetime.now() - timedelta(days=random.randint(1, 90)),
                'interaction_type': random.choice(['play', 'like', 'share', 'comment']),
                'duration_watched': random.randint(60, 3600)  # 1-60分鐘
            }
            data.append(interaction)
        
        df = pd.DataFrame(data)
        logger.info(f"✅ 創建用戶歷史資料成功: {len(df)} 筆")
        return df
    
    def create_mock_user_preferences(self, num_users: int = 50) -> pd.DataFrame:
        """創建模擬用戶偏好資料"""
        logger.info(f"創建 {num_users} 個用戶的偏好資料")
        
        data = []
        for i in range(num_users):
            user_prefs = {
                'user_id': f'user_{i+1:03d}',
                'preferred_categories': random.sample(self.podcast_categories, random.randint(1, 3)),
                'preferred_duration': random.choice(['short', 'medium', 'long']),
                'preferred_language': random.choice(['zh-TW', 'en-US', 'ja-JP']),
                'notification_enabled': random.choice([True, False]),
                'created_at': datetime.now() - timedelta(days=random.randint(1, 365)),
                'last_updated': datetime.now() - timedelta(days=random.randint(1, 30))
            }
            data.append(user_prefs)
        
        df = pd.DataFrame(data)
        logger.info(f"✅ 創建用戶偏好資料成功: {len(df)} 筆")
        return df
    
    def _generate_random_tags(self) -> List[str]:
        """生成隨機標籤"""
        all_tags = [
            "投資理財", "科技創新", "創業故事", "職場發展", "健康養生",
            "心理學", "歷史文化", "國際關係", "環境保護", "藝術設計",
            "音樂欣賞", "電影評論", "美食文化", "旅遊探索", "運動健身",
            "親子教育", "人際關係", "時間管理", "學習方法", "創意思維"
        ]
        
        num_tags = random.randint(2, 5)
        return random.sample(all_tags, num_tags)
    
    def save_mock_data(self, output_dir: str = "data/mock_data"):
        """儲存模擬資料"""
        import os
        
        # 創建輸出目錄
        os.makedirs(output_dir, exist_ok=True)
        
        # 創建各種模擬資料
        podcast_data = self.create_mock_podcast_data()
        user_history = self.create_mock_user_history()
        user_preferences = self.create_mock_user_preferences()
        
        # 儲存為 CSV 檔案
        podcast_data.to_csv(f"{output_dir}/podcast_data.csv", index=False)
        user_history.to_csv(f"{output_dir}/user_history.csv", index=False)
        user_preferences.to_csv(f"{output_dir}/user_preferences.csv", index=False)
        
        logger.info(f"✅ 模擬資料已儲存到 {output_dir}")
        
        return {
            'podcast_data': podcast_data,
            'user_history': user_history,
            'user_preferences': user_preferences
        }
    
    def create_ml_pipeline_config(self) -> Dict[str, Any]:
        """創建 ML Pipeline 配置"""
        config = {
            'data_paths': {
                'podcast_data': 'data/mock_data/podcast_data.csv',
                'user_history': 'data/mock_data/user_history.csv',
                'user_preferences': 'data/mock_data/user_preferences.csv'
            },
            'model_config': {
                'recommendation_algorithm': 'collaborative_filtering',
                'similarity_metric': 'cosine',
                'top_k_recommendations': 10,
                'min_interactions': 5
            },
            'training_config': {
                'test_size': 0.2,
                'random_state': 42,
                'cross_validation_folds': 5
            },
            'evaluation_metrics': [
                'precision_at_k',
                'recall_at_k',
                'ndcg_at_k',
                'map_at_k'
            ]
        }
        
        logger.info("✅ ML Pipeline 配置已創建")
        return config


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ML Pipeline 資料設定")
    parser.add_argument("--output-dir", default="data/mock_data", 
                       help="輸出目錄")
    parser.add_argument("--num-episodes", type=int, default=100,
                       help="Podcast 集數")
    parser.add_argument("--num-users", type=int, default=50,
                       help="用戶數量")
    parser.add_argument("--num-interactions", type=int, default=200,
                       help="互動數量")
    
    args = parser.parse_args()
    
    # 設定日誌
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 創建資料設定器
    setup = MLPipelineDataSetup()
    
    # 創建模擬資料
    data = setup.save_mock_data(args.output_dir)
    
    # 創建配置
    config = setup.create_ml_pipeline_config()
    
    # 顯示統計資訊
    print("\n📊 資料統計:")
    print(f"Podcast 資料: {len(data['podcast_data'])} 筆")
    print(f"用戶歷史: {len(data['user_history'])} 筆")
    print(f"用戶偏好: {len(data['user_preferences'])} 筆")
    
    print("\n🎯 配置資訊:")
    for key, value in config.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main() 