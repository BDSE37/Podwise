#!/usr/bin/env python3
"""
Podcast 推薦系統基礎模組
提供協同過濾和內容式推薦功能
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PodcastRecommender:
    """
    基礎 Podcast 推薦系統
    整合協同過濾和內容式推薦
    """
    
    def __init__(self, podcast_data: pd.DataFrame, user_history: pd.DataFrame):
        """
        初始化推薦系統
        
        Args:
            podcast_data: Podcast 資料，包含 id, title, category, description, tags 等欄位
            user_history: 使用者收聽紀錄，包含 user_id, podcast_id, rating, listen_time 等欄位
        """
        self.podcast_data = podcast_data.copy()
        self.user_history = user_history.copy()
        
        # 初始化向量化器
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        # 計算相似度矩陣
        self._compute_similarity_matrices()
        
        logger.info("Podcast 推薦系統初始化完成")
    
    def _compute_similarity_matrices(self):
        """計算相似度矩陣"""
        try:
            # 內容相似度矩陣
            content_features = self._extract_content_features()
            self.content_similarity = cosine_similarity(content_features)
            
            # 使用者相似度矩陣
            user_features = self._extract_user_features()
            self.user_similarity = cosine_similarity(user_features)
            
            logger.info("相似度矩陣計算完成")
            
        except Exception as e:
            logger.error(f"相似度矩陣計算失敗: {str(e)}")
    
    def _extract_content_features(self) -> np.ndarray:
        """提取內容特徵"""
        try:
            # 合併標題、描述和標籤
            content_text = (
                self.podcast_data['title'].fillna('') + ' ' +
                self.podcast_data['description'].fillna('') + ' ' +
                self.podcast_data['tags'].fillna('')
            )
            
            # TF-IDF 向量化
            content_features = self.tfidf_vectorizer.fit_transform(content_text)
            return content_features.toarray()
            
        except Exception as e:
            logger.error(f"內容特徵提取失敗: {str(e)}")
            return np.zeros((len(self.podcast_data), 1000))
    
    def _extract_user_features(self) -> np.ndarray:
        """提取使用者特徵"""
        try:
            # 建立使用者-Podcast 評分矩陣
            user_podcast_matrix = self.user_history.pivot_table(
                index='user_id',
                columns='podcast_id',
                values='rating',
                fill_value=0
            )
            
            # 標準化
            scaler = StandardScaler()
            user_features = scaler.fit_transform(user_podcast_matrix)
            
            return user_features
            
        except Exception as e:
            logger.error(f"使用者特徵提取失敗: {str(e)}")
            return np.zeros((len(self.user_history['user_id'].unique()), 1))
    
    def get_recommendations(self, user_id: str, top_k: int = 5, 
                          category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        取得推薦結果
        
        Args:
            user_id: 使用者 ID
            top_k: 推薦數量
            category_filter: 類別篩選
            
        Returns:
            推薦 Podcast 清單
        """
        try:
            # 檢查使用者是否存在
            if user_id not in self.user_history['user_id'].unique():
                logger.warning(f"使用者 {user_id} 不存在，使用熱門推薦")
                return self._get_popular_recommendations(top_k, category_filter)
            
            # 混合推薦
            cf_recommendations = self._collaborative_filtering_recommend(user_id, top_k * 2, category_filter)
            cb_recommendations = self._content_based_recommend(user_id, top_k * 2, category_filter)
            
            # 合併並排序
            all_recommendations = cf_recommendations + cb_recommendations
            
            # 去重並保持順序
            seen = set()
            unique_recommendations = []
            for rec in all_recommendations:
                if rec[0] not in seen:
                    seen.add(rec[0])
                    unique_recommendations.append(rec)
            
            # 取前 top_k 個
            top_recommendations = unique_recommendations[:top_k]
            
            # 豐富推薦結果
            recommendations = self._enrich_recommendations([podcast_id for podcast_id, _ in top_recommendations])
            
            logger.info(f"為使用者 {user_id} 生成 {len(recommendations)} 個推薦")
            return recommendations
            
        except Exception as e:
            logger.error(f"推薦生成失敗: {str(e)}")
            return []
    
    def _collaborative_filtering_recommend(self, user_id: str, top_k: int, 
                                         category_filter: Optional[str] = None) -> List[Tuple[str, float]]:
        """協同過濾推薦"""
        try:
            # 取得使用者索引
            user_idx = self.user_history[self.user_history['user_id'] == user_id].index[0]
            
            # 計算與其他使用者的相似度
            user_similarities = self.user_similarity[user_idx]
            
            # 找出最相似的使用者
            similar_users = np.argsort(user_similarities)[::-1][1:6]  # 前5個最相似使用者
            
            # 收集推薦候選
            candidate_scores = {}
            
            for similar_user_idx in similar_users:
                similar_user_id = self.user_history.iloc[similar_user_idx]['user_id']
                similarity = user_similarities[similar_user_idx]
                
                # 取得相似使用者的高評分 Podcast
                similar_user_podcasts = self.user_history[
                    (self.user_history['user_id'] == similar_user_id) &
                    (self.user_history['rating'] >= 4.0)
                ]
                
                for _, row in similar_user_podcasts.iterrows():
                    podcast_id = row['podcast_id']
                    
                    # 檢查類別篩選
                    if category_filter:
                        podcast_category = self.podcast_data[
                            self.podcast_data['id'] == podcast_id
                        ]['category'].iloc[0]
                        if podcast_category != category_filter:
                            continue
                    
                    # 計算推薦分數
                    score = similarity * row['rating']
                    candidate_scores[podcast_id] = candidate_scores.get(podcast_id, 0) + score
            
            # 排序並返回
            sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_candidates[:top_k]
            
        except Exception as e:
            logger.error(f"協同過濾推薦失敗: {str(e)}")
            return []
    
    def _content_based_recommend(self, user_id: str, top_k: int, 
                               category_filter: Optional[str] = None) -> List[Tuple[str, float]]:
        """內容式推薦"""
        try:
            # 取得使用者喜歡的 Podcast
            user_liked_podcasts = self.user_history[
                (self.user_history['user_id'] == user_id) &
                (self.user_history['rating'] >= 4.0)
            ]['podcast_id'].values
            
            if len(user_liked_podcasts) == 0:
                return []
            
            # 計算使用者偏好向量
            user_preference = np.zeros(len(self.podcast_data))
            
            for podcast_id in user_liked_podcasts:
                podcast_idx = self.podcast_data[self.podcast_data['id'] == podcast_id].index[0]
                user_preference += self.content_similarity[podcast_idx]
            
            user_preference /= len(user_liked_podcasts)
            
            # 找出最相似的 Podcast
            candidate_scores = []
            
            for idx, podcast in self.podcast_data.iterrows():
                podcast_id = podcast['id']
                
                # 跳過已聽過的 Podcast
                if podcast_id in user_liked_podcasts:
                    continue
                
                # 檢查類別篩選
                if category_filter and podcast['category'] != category_filter:
                    continue
                
                # 計算相似度分數
                similarity_score = user_preference[idx]
                candidate_scores.append((podcast_id, similarity_score))
            
            # 排序並返回
            candidate_scores.sort(key=lambda x: x[1], reverse=True)
            return candidate_scores[:top_k]
            
        except Exception as e:
            logger.error(f"內容式推薦失敗: {str(e)}")
            return []
    
    def _get_popular_recommendations(self, top_k: int, 
                                   category_filter: Optional[str] = None) -> List[Tuple[str, float]]:
        """取得熱門推薦"""
        try:
            # 計算 Podcast 受歡迎程度
            popularity = self.user_history.groupby('podcast_id').agg({
                'rating': 'mean',
                'listen_time': 'sum',
                'user_id': 'count'
            }).reset_index()
            
            popularity['popularity_score'] = (
                popularity['rating'] * 0.4 + 
                np.log1p(popularity['listen_time']) * 0.3 + 
                np.log1p(popularity['user_id']) * 0.3
            )
            
            # 篩選類別
            if category_filter:
                category_podcasts = self.podcast_data[
                    self.podcast_data['category'] == category_filter
                ]['id'].values
                popularity = popularity[popularity['podcast_id'].isin(category_podcasts)]
            
            # 排序並取前 top_k 個
            top_popular = popularity.nlargest(top_k, 'popularity_score')
            
            return [(row['podcast_id'], row['popularity_score']) 
                   for _, row in top_popular.iterrows()]
            
        except Exception as e:
            logger.error(f"熱門推薦失敗: {str(e)}")
            return []
    
    def _enrich_recommendations(self, podcast_ids: List[str]) -> List[Dict[str, Any]]:
        """豐富推薦結果資訊"""
        try:
            recommendations = []
            
            for podcast_id in podcast_ids:
                podcast_info = self.podcast_data[
                    self.podcast_data['id'] == podcast_id
                ].iloc[0]
                
                # 計算統計資訊
                podcast_history = self.user_history[
                    self.user_history['podcast_id'] == podcast_id
                ]
                
                average_rating = podcast_history['rating'].mean() if len(podcast_history) > 0 else 0
                listen_count = len(podcast_history)
                
                # 計算推薦理由
                reason = self._get_recommendation_reason(podcast_info['category'])
                
                recommendation = {
                    'podcast_id': podcast_id,
                    'title': podcast_info['title'],
                    'category': podcast_info['category'],
                    'description': podcast_info['description'],
                    'tags': podcast_info['tags'],
                    'average_rating': round(average_rating, 2),
                    'listen_count': listen_count,
                    'recommendation_reason': reason,
                    'model_type': 'Hybrid'
                }
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"推薦結果豐富失敗: {str(e)}")
            return []
    
    def _get_recommendation_reason(self, category: str) -> str:
        """取得推薦理由"""
        reasons = {
            '財經': '基於您的財經興趣和協同過濾分析，推薦此財經 Podcast',
            '自我成長': '根據您的自我成長偏好和內容相似度，推薦此成長類 Podcast'
        }
        return reasons.get(category, '基於混合推薦算法分析推薦')
    
    def update_user_preference(self, user_id: str, podcast_id: str, rating: float, listen_time: int = 0):
        """更新使用者偏好"""
        try:
            # 新增或更新使用者歷史
            new_record = pd.DataFrame([{
                'user_id': user_id,
                'podcast_id': podcast_id,
                'rating': rating,
                'listen_time': listen_time
            }])
            
            # 移除舊記錄（如果存在）
            self.user_history = self.user_history[
                ~((self.user_history['user_id'] == user_id) & 
                  (self.user_history['podcast_id'] == podcast_id))
            ]
            
            # 新增新記錄
            self.user_history = pd.concat([self.user_history, new_record], ignore_index=True)
            
            # 重新計算相似度矩陣
            self._compute_similarity_matrices()
            
            logger.info(f"使用者 {user_id} 的偏好已更新")
            
        except Exception as e:
            logger.error(f"偏好更新失敗: {str(e)}") 