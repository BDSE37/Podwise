#!/usr/bin/env python3
"""
整合推薦引擎
整合所有推薦演算法：協同過濾、內容式、GNN、混合推薦
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Any, Optional, Tuple
import logging
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import train_test_split
import networkx as nx

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RecommenderEngine:
    """
    整合推薦引擎
    整合協同過濾、內容式、GNN、混合推薦等多種演算法
    """
    
    def __init__(self, podcast_data: pd.DataFrame, user_history: pd.DataFrame, 
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化推薦引擎
        
        Args:
            podcast_data: Podcast 資料
            user_history: 使用者收聽紀錄
            config: 配置參數
        """
        self.podcast_data = podcast_data.copy()
        self.user_history = user_history.copy()
        self.config = config or {}
        
        # 初始化編碼器
        self.user_encoder = LabelEncoder()
        self.podcast_encoder = LabelEncoder()
        self.category_encoder = LabelEncoder()
        
        # 初始化模型
        self.knn_model: Optional[KNeighborsRegressor] = None
        self.gnn_model = None
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        
        # 相似度矩陣
        self.content_similarity: Optional[np.ndarray] = None
        self.user_similarity: Optional[np.ndarray] = None
        
        # 圖結構（GNN用）
        self.graph = None
        self.graph_data = None
        
        # 使用者-Podcast 矩陣（KNN用）
        self.user_podcast_matrix: Optional[pd.DataFrame] = None
        self.user_features: Optional[np.ndarray] = None
        
        # 初始化
        self._prepare_data()
        self._init_models()
        
        logger.info("整合推薦引擎初始化完成")
    
    def _prepare_data(self):
        """準備和預處理資料"""
        try:
            # 編碼使用者 ID
            unique_users = self.user_history['user_id'].unique()
            self.user_encoder.fit(unique_users)
            
            # 編碼 Podcast ID
            unique_podcasts = self.podcast_data['id'].unique()
            self.podcast_encoder.fit(unique_podcasts)
            
            # 編碼類別
            unique_categories = self.podcast_data['category'].unique()
            self.category_encoder.fit(unique_categories)
            
            # 轉換編碼
            self.user_history['user_idx'] = self.user_encoder.transform(self.user_history['user_id'])
            self.user_history['podcast_idx'] = self.podcast_encoder.transform(self.user_history['podcast_id'])
            self.podcast_data['podcast_idx'] = self.podcast_encoder.transform(self.podcast_data['id'])
            self.podcast_data['category_idx'] = self.category_encoder.transform(self.podcast_data['category'])
            
            logger.info("資料預處理完成")
            
        except Exception as e:
            logger.error(f"資料預處理失敗: {str(e)}")
    
    def _init_models(self):
        """初始化各種模型"""
        try:
            # 初始化 TF-IDF 向量化器
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # 計算相似度矩陣
            self._compute_similarity_matrices()
            
            # 初始化 KNN 模型
            self._init_knn_model()
            
            logger.info("所有模型初始化完成")
            
        except Exception as e:
            logger.error(f"模型初始化失敗: {str(e)}")
    
    def _init_knn_model(self):
        """初始化 KNN 模型"""
        try:
            # 建立使用者-Podcast 評分矩陣
            self.user_podcast_matrix = self.user_history.pivot_table(
                index='user_id',
                columns='podcast_id',
                values='rating',
                fill_value=0
            )
            
            # 標準化使用者特徵
            scaler = StandardScaler()
            self.user_features = scaler.fit_transform(self.user_podcast_matrix)
            
            # 初始化 KNN 回歸器
            k_neighbors = self.config.get('k_neighbors', 5)
            self.knn_model = KNeighborsRegressor(
                n_neighbors=k_neighbors,
                weights='distance',
                metric='cosine'
            )
            
            # 準備訓練數據
            X_train, X_test, y_train, y_test = self._prepare_knn_training_data()
            
            # 訓練 KNN 模型
            if len(X_train) > 0:
                self.knn_model.fit(X_train, y_train)
                logger.info(f"KNN 模型訓練完成，k={k_neighbors}")
            else:
                logger.warning("訓練數據不足，無法訓練 KNN 模型")
                
        except Exception as e:
            logger.error(f"KNN 模型初始化失敗: {str(e)}")
    
    def _prepare_knn_training_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """準備 KNN 訓練數據"""
        try:
            # 檢查矩陣是否已初始化
            if self.user_podcast_matrix is None or self.user_features is None:
                return np.array([]), np.array([]), np.array([]), np.array([])
            
            # 將評分矩陣轉換為訓練數據
            X = []
            y = []
            
            for user_idx, user_id in enumerate(self.user_podcast_matrix.index):
                user_ratings = self.user_podcast_matrix.iloc[user_idx]
                
                for podcast_id in self.user_podcast_matrix.columns:
                    rating = user_ratings[podcast_id]
                    if rating > 0:  # 只使用有評分的數據
                        # 使用者特徵（排除當前 podcast 的評分）
                        user_feature = self.user_features[user_idx].copy()
                        podcast_idx = list(self.user_podcast_matrix.columns).index(podcast_id)
                        user_feature[podcast_idx] = 0  # 排除當前 podcast
                        
                        X.append(user_feature)
                        y.append(rating)
            
            if len(X) > 10:  # 確保有足夠的訓練數據
                X_array = np.array(X)
                y_array = np.array(y)
                X_train, X_test, y_train, y_test = train_test_split(X_array, y_array, test_size=0.2, random_state=42)
                return X_train, X_test, y_train, y_test
            else:
                return np.array([]), np.array([]), np.array([]), np.array([])
                
        except Exception as e:
            logger.error(f"KNN 訓練數據準備失敗: {str(e)}")
            return np.array([]), np.array([]), np.array([]), np.array([])
    
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
            if self.tfidf_vectorizer is not None:
                tfidf_matrix = self.tfidf_vectorizer.fit_transform(content_text)
                return tfidf_matrix.toarray()
            else:
                return np.zeros((len(self.podcast_data), 1000))
            
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
        strategy: str = 'hybrid',
                          category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        取得推薦結果
        
        Args:
            user_id: 使用者 ID
            top_k: 推薦數量
            strategy: 推薦策略 ('collaborative', 'content', 'gnn', 'hybrid')
            category_filter: 類別篩選
            
        Returns:
            推薦 Podcast 清單
        """
        try:
            # 檢查使用者是否存在
            if user_id not in self.user_history['user_id'].unique():
                logger.warning(f"使用者 {user_id} 不存在，使用熱門推薦")
                return self._get_popular_recommendations(top_k, category_filter)
            
            # 根據策略選擇推薦方法
            if strategy == 'collaborative':
                recommendations = self._collaborative_filtering_recommend(user_id, top_k, category_filter)
            elif strategy == 'content':
                recommendations = self._content_based_recommend(user_id, top_k, category_filter)
            elif strategy == 'hybrid':
                recommendations = self._hybrid_recommend(user_id, top_k, category_filter)
            else:
                logger.warning(f"未知策略 {strategy}，使用混合推薦")
                recommendations = self._hybrid_recommend(user_id, top_k, category_filter)
            
            # 豐富推薦結果
            enriched_recommendations = self._enrich_recommendations(
                [rec['podcast_id'] for rec in recommendations], 
                strategy
            )
            
            logger.info(f"為使用者 {user_id} 生成 {len(enriched_recommendations)} 個 {strategy} 推薦")
            return enriched_recommendations
            
        except Exception as e:
            logger.error(f"推薦生成失敗: {str(e)}")
            return []
    
    def _collaborative_filtering_recommend(self, user_id: str, top_k: int, 
                                         category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """協同過濾推薦（使用 KNN）"""
        try:
            # 如果 KNN 模型可用，使用 KNN 協同過濾
            if self.knn_model is not None and self.user_podcast_matrix is not None:
                return self._knn_collaborative_filtering_recommend(user_id, top_k, category_filter)
            else:
                return self._traditional_collaborative_filtering_recommend(user_id, top_k, category_filter)
                
        except Exception as e:
            logger.error(f"協同過濾推薦失敗: {str(e)}")
            return []
    
    def _knn_collaborative_filtering_recommend(self, user_id: str, top_k: int, 
                                             category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """KNN 協同過濾推薦"""
        try:
            if (self.user_podcast_matrix is None or 
                user_id not in self.user_podcast_matrix.index or
                self.user_features is None or
                self.knn_model is None):
                logger.warning(f"使用者 {user_id} 不在訓練數據中")
                return self._traditional_collaborative_filtering_recommend(user_id, top_k, category_filter)
            
            # 取得使用者特徵
            user_idx = list(self.user_podcast_matrix.index).index(user_id)
            user_feature = self.user_features[user_idx]
            
            # 預測所有 Podcast 的評分
            predicted_ratings = {}
            
            for podcast_id in self.user_podcast_matrix.columns:
                # 檢查類別篩選
                if category_filter:
                    podcast_matches = self.podcast_data[self.podcast_data['id'] == podcast_id]
                    if len(podcast_matches) > 0:
                        podcast_category = podcast_matches.iloc[0]['category']
                        if podcast_category != category_filter:
                            continue
                
                # 檢查使用者是否已經評分過
                current_rating = self.user_podcast_matrix.loc[user_id, podcast_id]
                if current_rating > 0:
                    continue  # 跳過已評分的 Podcast
                
                # 使用 KNN 預測評分
                try:
                    # 創建預測特徵（將當前 podcast 的評分設為 0）
                    predict_feature = user_feature.copy()
                    podcast_idx = list(self.user_podcast_matrix.columns).index(podcast_id)
                    predict_feature[podcast_idx] = 0
                    
                    # 預測評分
                    predicted_rating = self.knn_model.predict([predict_feature])[0]
                    predicted_ratings[podcast_id] = max(0, predicted_rating)  # 確保評分非負
                    
                except Exception as e:
                    logger.warning(f"預測 {podcast_id} 評分失敗: {str(e)}")
                    continue
            
            # 排序並返回前 top_k 個
            sorted_predictions = sorted(predicted_ratings.items(), key=lambda x: x[1], reverse=True)
            logger.info(f"KNN 為使用者 {user_id} 預測了 {len(sorted_predictions)} 個評分")
            
            # 轉換為標準格式
            recommendations = []
            for podcast_id, score in sorted_predictions[:top_k]:
                recommendations.append({
                    'podcast_id': podcast_id,
                    'score': score,
                    'model_type': 'KNN_Collaborative'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"KNN 協同過濾推薦失敗: {str(e)}")
            return self._traditional_collaborative_filtering_recommend(user_id, top_k, category_filter)
    
    def _traditional_collaborative_filtering_recommend(self, user_id: str, top_k: int, 
                                                     category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """傳統協同過濾推薦（基於相似度）"""
        try:
            # 取得使用者索引
            user_matches = self.user_history[self.user_history['user_id'] == user_id]
            if len(user_matches) == 0:
                return []
                
            user_idx = user_matches.index[0]
            
            # 計算與其他使用者的相似度
            if self.user_similarity is None:
                return []
                
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
                        podcast_matches = self.podcast_data[self.podcast_data['id'] == podcast_id]
                        if len(podcast_matches) > 0:
                            podcast_category = podcast_matches['category'].iloc[0]
                            if podcast_category != category_filter:
                                continue
                    
                    # 計算推薦分數
                    score = similarity * row['rating']
                    candidate_scores[podcast_id] = candidate_scores.get(podcast_id, 0) + score
            
            # 排序並返回
            sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
            
            recommendations = []
            for podcast_id, score in sorted_candidates[:top_k]:
                recommendations.append({
                    'podcast_id': podcast_id,
                    'score': score,
                    'model_type': 'Traditional_Collaborative'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"傳統協同過濾推薦失敗: {str(e)}")
            return []
    
    def _content_based_recommend(self, user_id: str, top_k: int, 
                               category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """內容式推薦"""
        try:
            # 取得使用者喜歡的 Podcast
            user_liked_podcasts_df = self.user_history[
                (self.user_history['user_id'] == user_id) &
                (self.user_history['rating'] >= 4.0)
            ]
            
            if len(user_liked_podcasts_df) == 0:
                return []
                
            user_liked_podcasts = user_liked_podcasts_df['podcast_id'].tolist()
            
            # 計算使用者偏好向量
            if self.content_similarity is None:
                return []
                
            user_preference = np.zeros(len(self.podcast_data))
            
            for podcast_id in user_liked_podcasts:
                podcast_matches = self.podcast_data[self.podcast_data['id'] == podcast_id]
                if len(podcast_matches) > 0:
                    podcast_idx = podcast_matches.index[0]
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
            
            recommendations = []
            for podcast_id, score in candidate_scores[:top_k]:
                recommendations.append({
                    'podcast_id': podcast_id,
                    'score': score,
                    'model_type': 'Content_Based'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"內容式推薦失敗: {str(e)}")
            return []
    
    def _hybrid_recommend(self, user_id: str, top_k: int, 
                         category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """混合推薦"""
        try:
            # 取得各推薦器的結果
            cf_recs = self._collaborative_filtering_recommend(user_id, top_k * 2, category_filter)
            cb_recs = self._content_based_recommend(user_id, top_k * 2, category_filter)
            
            # 建立評分字典
            scores = {}
            
            # 協同過濾推薦評分
            for i, rec in enumerate(cf_recs):
                podcast_id = rec['podcast_id']
                score = 0.6 * (1.0 - i / max(len(cf_recs), 1))  # 協同過濾權重較高
                scores[podcast_id] = scores.get(podcast_id, 0) + score
            
            # 內容式推薦評分
            for i, rec in enumerate(cb_recs):
                podcast_id = rec['podcast_id']
                score = 0.4 * (1.0 - i / max(len(cb_recs), 1))  # 內容式權重較低
                scores[podcast_id] = scores.get(podcast_id, 0) + score
            
            # 排序並取前 top_k 個
            sorted_podcasts = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            recommendations = []
            for podcast_id, score in sorted_podcasts[:top_k]:
                recommendations.append({
                    'podcast_id': podcast_id,
                    'score': score,
                    'model_type': 'Hybrid'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"混合推薦失敗: {str(e)}")
            return []
    
    def _get_popular_recommendations(self, top_k: int, 
                                   category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
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
                category_podcasts_df = self.podcast_data[
                    self.podcast_data['category'] == category_filter
                ]
                category_podcasts = category_podcasts_df['id'].tolist()
                popularity = popularity[popularity['podcast_id'].isin(category_podcasts)]
            
            # 排序並取前 top_k 個
            top_popular = popularity.nlargest(top_k, 'popularity_score')
            
            recommendations = []
            for _, row in top_popular.iterrows():
                recommendations.append({
                    'podcast_id': row['podcast_id'],
                    'score': row['popularity_score'],
                    'model_type': 'Popularity'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"熱門推薦失敗: {str(e)}")
            return []
    
    def _enrich_recommendations(self, podcast_ids: List[str], strategy: str) -> List[Dict[str, Any]]:
        """豐富推薦結果資訊"""
        try:
            recommendations = []
            
            for podcast_id in podcast_ids:
                podcast_matches = self.podcast_data[self.podcast_data['id'] == podcast_id]
                if len(podcast_matches) == 0:
                    continue
                    
                podcast_info = podcast_matches.iloc[0]
                
                # 計算統計資訊
                podcast_history = self.user_history[
                    self.user_history['podcast_id'] == podcast_id
                ]
                
                average_rating = podcast_history['rating'].mean() if len(podcast_history) > 0 else 0
                listen_count = len(podcast_history)
                
                # 計算推薦理由
                reason = self._get_recommendation_reason(podcast_info['category'], strategy)
                
                recommendation = {
                    'podcast_id': podcast_id,
                    'title': podcast_info['title'],
                    'category': podcast_info['category'],
                    'description': podcast_info['description'],
                    'tags': podcast_info['tags'],
                    'average_rating': round(average_rating, 2),
                    'listen_count': listen_count,
                    'recommendation_reason': reason,
                    'model_type': strategy.capitalize()
                }
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"推薦結果豐富失敗: {str(e)}")
            return []
    
    def _get_recommendation_reason(self, category: str, strategy: str) -> str:
        """取得推薦理由"""
        reasons = {
            'collaborative': {
                '財經': '基於相似用戶的財經偏好推薦',
                '自我成長': '根據相似用戶的成長類偏好推薦'
            },
            'content': {
                '財經': '基於您的財經內容偏好推薦',
                '自我成長': '根據您的成長類內容偏好推薦'
            },
            'gnn': {
                '財經': '基於圖神經網路的財經分析推薦',
                '自我成長': '根據圖結構學習的成長類推薦'
            },
            'hybrid': {
                '財經': '基於多種算法的財經綜合推薦',
                '自我成長': '結合多種算法的成長類推薦'
            }
        }
        
        strategy_reasons = reasons.get(strategy, {})
        return strategy_reasons.get(category, f'基於{strategy}算法分析推薦')
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        try:
            return {
                'status': 'healthy',
                'knn_model_ready': self.knn_model is not None,
                'gnn_model_ready': self.gnn_model is not None,
                'total_users': len(self.user_history['user_id'].unique()),
                'total_podcasts': len(self.podcast_data),
                'total_interactions': len(self.user_history),
                'config': self.config
            }
            
        except Exception as e:
            logger.error(f"狀態查詢失敗: {str(e)}")
            return {'status': 'error', 'error': str(e)}


# 為了向後相容，保留舊的類別名稱
class Data:
    """簡化的 Data 類別，用於 GNN"""
    def __init__(self, x, edge_index, num_nodes):
        self.x = x
        self.edge_index = edge_index
        self.num_nodes = num_nodes 