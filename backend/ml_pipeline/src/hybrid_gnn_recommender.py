#!/usr/bin/env python3
"""
混合 GNN 推薦系統
整合傳統推薦方法和圖神經網路，提供更全面的推薦解決方案
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# 導入自定義模組
from .podcast_recommender import PodcastRecommender
from .gnn_podcast_recommender import GNNPodcastRecommender

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridGNNRecommender:
    """
    混合 GNN 推薦系統
    結合協同過濾、內容式推薦和圖神經網路
    """
    
    def __init__(self, podcast_data: pd.DataFrame, user_history: pd.DataFrame,
                 gnn_weight: float = 0.4, cf_weight: float = 0.3, cb_weight: float = 0.3):
        """
        初始化混合推薦系統
        
        Args:
            podcast_data: Podcast 資料
            user_history: 使用者收聽紀錄
            gnn_weight: GNN 推薦權重
            cf_weight: 協同過濾權重
            cb_weight: 內容式推薦權重
        """
        self.podcast_data = podcast_data
        self.user_history = user_history
        
        # 權重設定
        self.gnn_weight = gnn_weight
        self.cf_weight = cf_weight
        self.cb_weight = cb_weight
        
        # 初始化各推薦器
        self.traditional_recommender = PodcastRecommender(podcast_data, user_history)
        self.gnn_recommender = GNNPodcastRecommender(podcast_data, user_history)
        
        # 訓練 GNN 模型
        self._train_gnn_model()
        
        logger.info("混合 GNN 推薦系統初始化完成")
    
    def _train_gnn_model(self):
        """訓練 GNN 模型"""
        try:
            logger.info("開始訓練 GNN 模型...")
            self.gnn_recommender.train_gnn(epochs=50, lr=0.01)
            logger.info("GNN 模型訓練完成")
        except Exception as e:
            logger.error(f"GNN 模型訓練失敗: {str(e)}")
    
    def get_recommendations(self, user_id: str, top_k: int = 5, 
                          category_filter: Optional[str] = None,
                          use_ensemble: bool = True) -> List[Dict[str, Any]]:
        """
        取得混合推薦結果
        
        Args:
            user_id: 使用者 ID
            top_k: 推薦數量
            category_filter: 類別篩選
            use_ensemble: 是否使用集成方法
            
        Returns:
            推薦 Podcast 清單
        """
        try:
            if use_ensemble:
                return self._ensemble_recommendations(user_id, top_k, category_filter)
            else:
                return self._weighted_recommendations(user_id, top_k, category_filter)
                
        except Exception as e:
            logger.error(f"混合推薦失敗: {str(e)}")
            return []
    
    def _ensemble_recommendations(self, user_id: str, top_k: int, 
                                category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """集成推薦方法"""
        try:
            # 取得各推薦器的結果
            gnn_recs = self.gnn_recommender.get_recommendations(user_id, top_k * 2, category_filter)
            cf_recs = self.traditional_recommender.get_recommendations(user_id, top_k * 2, category_filter)
            
            # 建立評分字典
            scores = {}
            
            # GNN 推薦評分
            for i, rec in enumerate(gnn_recs):
                podcast_id = rec['podcast_id']
                score = self.gnn_weight * (1.0 - i / len(gnn_recs))  # 排名越前分數越高
                scores[podcast_id] = scores.get(podcast_id, 0) + score
            
            # 協同過濾推薦評分
            for i, rec in enumerate(cf_recs):
                podcast_id = rec['podcast_id']
                score = self.cf_weight * (1.0 - i / len(cf_recs))
                scores[podcast_id] = scores.get(podcast_id, 0) + score
            
            # 排序並取前 top_k 個
            sorted_podcasts = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            top_podcast_ids = [podcast_id for podcast_id, _ in sorted_podcasts[:top_k]]
            
            # 豐富推薦結果
            recommendations = self._enrich_ensemble_recommendations(top_podcast_ids, scores)
            
            logger.info(f"為使用者 {user_id} 生成 {len(recommendations)} 個集成推薦")
            return recommendations
            
        except Exception as e:
            logger.error(f"集成推薦失敗: {str(e)}")
            return []
    
    def _weighted_recommendations(self, user_id: str, top_k: int, 
                                category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """加權推薦方法"""
        try:
            # 根據權重選擇主要推薦器
            if self.gnn_weight >= max(self.cf_weight, self.cb_weight):
                primary_recs = self.gnn_recommender.get_recommendations(user_id, top_k, category_filter)
                secondary_recs = self.traditional_recommender.get_recommendations(user_id, top_k // 2, category_filter)
            else:
                primary_recs = self.traditional_recommender.get_recommendations(user_id, top_k, category_filter)
                secondary_recs = self.gnn_recommender.get_recommendations(user_id, top_k // 2, category_filter)
            
            # 合併推薦結果
            all_recs = primary_recs + secondary_recs
            
            # 去重並保持順序
            seen = set()
            unique_recs = []
            for rec in all_recs:
                if rec['podcast_id'] not in seen:
                    seen.add(rec['podcast_id'])
                    unique_recs.append(rec)
            
            return unique_recs[:top_k]
            
        except Exception as e:
            logger.error(f"加權推薦失敗: {str(e)}")
            return []
    
    def _enrich_ensemble_recommendations(self, podcast_ids: List[str], 
                                       scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """豐富集成推薦結果"""
        try:
            recommendations = []
            
            for podcast_id in podcast_ids:
                podcast_info = self.podcast_data[
                    self.podcast_data['id'] == podcast_id
                ].iloc[0]
                
                # 計算推薦理由
                reason = self._get_ensemble_recommendation_reason(podcast_info['category'], scores[podcast_id])
                
                recommendation = {
                    'podcast_id': podcast_id,
                    'title': podcast_info['title'],
                    'category': podcast_info['category'],
                    'description': podcast_info['description'],
                    'tags': podcast_info['tags'],
                    'recommendation_reason': reason,
                    'model_type': 'Hybrid_GNN',
                    'ensemble_score': scores[podcast_id]
                }
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"集成推薦結果豐富失敗: {str(e)}")
            return []
    
    def _get_ensemble_recommendation_reason(self, category: str, score: float) -> str:
        """取得集成推薦理由"""
        base_reasons = {
            '財經': '基於圖神經網路和傳統推薦算法的綜合分析，推薦此財經 Podcast',
            '自我成長': '結合圖結構學習和協同過濾，推薦此成長類 Podcast'
        }
        
        base_reason = base_reasons.get(category, '基於混合推薦算法分析推薦')
        
        if score > 0.7:
            confidence = "高置信度"
        elif score > 0.4:
            confidence = "中等置信度"
        else:
            confidence = "一般置信度"
        
        return f"{base_reason}（{confidence}）"
    
    def update_weights(self, gnn_weight: float, cf_weight: float, cb_weight: float):
        """更新推薦權重"""
        try:
            total_weight = gnn_weight + cf_weight + cb_weight
            if total_weight != 1.0:
                # 正規化權重
                self.gnn_weight = gnn_weight / total_weight
                self.cf_weight = cf_weight / total_weight
                self.cb_weight = cb_weight / total_weight
            else:
                self.gnn_weight = gnn_weight
                self.cf_weight = cf_weight
                self.cb_weight = cb_weight
            
            logger.info(f"權重已更新: GNN={self.gnn_weight:.2f}, CF={self.cf_weight:.2f}, CB={self.cb_weight:.2f}")
            
        except Exception as e:
            logger.error(f"權重更新失敗: {str(e)}")
    
    def get_recommendation_analysis(self, user_id: str, top_k: int = 5) -> Dict[str, Any]:
        """取得推薦分析報告"""
        try:
            # 取得各推薦器的結果
            gnn_recs = self.gnn_recommender.get_recommendations(user_id, top_k)
            cf_recs = self.traditional_recommender.get_recommendations(user_id, top_k)
            hybrid_recs = self.get_recommendations(user_id, top_k)
            
            # 分析重疊度
            gnn_ids = set(rec['podcast_id'] for rec in gnn_recs)
            cf_ids = set(rec['podcast_id'] for rec in cf_recs)
            hybrid_ids = set(rec['podcast_id'] for rec in hybrid_recs)
            
            overlap_gnn_cf = len(gnn_ids.intersection(cf_ids))
            overlap_gnn_hybrid = len(gnn_ids.intersection(hybrid_ids))
            overlap_cf_hybrid = len(cf_ids.intersection(hybrid_ids))
            
            # 類別分布分析
            gnn_categories = [rec['category'] for rec in gnn_recs]
            cf_categories = [rec['category'] for rec in cf_recs]
            hybrid_categories = [rec['category'] for rec in hybrid_recs]
            
            analysis = {
                'user_id': user_id,
                'recommendation_counts': {
                    'gnn': len(gnn_recs),
                    'collaborative_filtering': len(cf_recs),
                    'hybrid': len(hybrid_recs)
                },
                'overlap_analysis': {
                    'gnn_cf_overlap': overlap_gnn_cf,
                    'gnn_hybrid_overlap': overlap_gnn_hybrid,
                    'cf_hybrid_overlap': overlap_cf_hybrid
                },
                'category_distribution': {
                    'gnn': pd.Series(gnn_categories).value_counts().to_dict(),
                    'collaborative_filtering': pd.Series(cf_categories).value_counts().to_dict(),
                    'hybrid': pd.Series(hybrid_categories).value_counts().to_dict()
                },
                'weights': {
                    'gnn_weight': self.gnn_weight,
                    'cf_weight': self.cf_weight,
                    'cb_weight': self.cb_weight
                }
            }
            
            logger.info(f"為使用者 {user_id} 生成推薦分析報告")
            return analysis
            
        except Exception as e:
            logger.error(f"推薦分析失敗: {str(e)}")
            return {}
    
    def visualize_recommendation_comparison(self, user_id: str, save_path: Optional[str] = None):
        """視覺化推薦比較"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # 取得分析報告
            analysis = self.get_recommendation_analysis(user_id)
            
            if not analysis:
                return
            
            # 建立子圖
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. 推薦數量比較
            counts = analysis['recommendation_counts']
            axes[0, 0].bar(counts.keys(), counts.values(), color=['lightblue', 'lightcoral', 'lightgreen'])
            axes[0, 0].set_title('推薦數量比較')
            axes[0, 0].set_ylabel('推薦數量')
            
            # 2. 重疊度分析
            overlap = analysis['overlap_analysis']
            axes[0, 1].bar(overlap.keys(), overlap.values(), color=['orange', 'purple', 'brown'])
            axes[0, 1].set_title('推薦重疊度分析')
            axes[0, 1].set_ylabel('重疊數量')
            
            # 3. 類別分布比較
            categories = analysis['category_distribution']
            categories_df = pd.DataFrame(categories).fillna(0)
            categories_df.plot(kind='bar', ax=axes[1, 0])
            axes[1, 0].set_title('類別分布比較')
            axes[1, 0].set_ylabel('推薦數量')
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # 4. 權重分布
            weights = analysis['weights']
            axes[1, 1].pie(weights.values(), labels=weights.keys(), autopct='%1.1f%%')
            axes[1, 1].set_title('推薦權重分布')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"推薦比較圖已儲存至 {save_path}")
            
            plt.show()
            
        except Exception as e:
            logger.error(f"推薦比較視覺化失敗: {str(e)}") 