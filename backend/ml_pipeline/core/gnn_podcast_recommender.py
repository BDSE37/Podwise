#!/usr/bin/env python3
"""
GNN Podcast 推薦系統
基於圖神經網路的智能推薦引擎
整合使用者-內容圖結構，提供更精準的推薦
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, SAGEConv, GATConv
from torch_geometric.data import Data, DataLoader
import networkx as nx
from typing import List, Dict, Any, Optional, Tuple
import logging
from sklearn.preprocessing import LabelEncoder, StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GNNPodcastRecommender:
    """
    基於圖神經網路的 Podcast 推薦系統
    使用 GCN (Graph Convolutional Network) 進行圖結構學習
    """
    
    def __init__(self, podcast_data: pd.DataFrame, user_history: pd.DataFrame, 
                 embedding_dim: int = 128, hidden_dim: int = 64):
        """
        初始化 GNN 推薦系統
        
        Args:
            podcast_data: Podcast 資料，包含 id, title, category, description, tags 等欄位
            user_history: 使用者收聽紀錄，包含 user_id, podcast_id, rating, listen_time 等欄位
            embedding_dim: 嵌入維度
            hidden_dim: 隱藏層維度
        """
        self.podcast_data = podcast_data
        self.user_history = user_history
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        
        # 編碼器
        self.user_encoder = LabelEncoder()
        self.podcast_encoder = LabelEncoder()
        self.category_encoder = LabelEncoder()
        
        # 圖結構
        self.graph = None
        self.graph_data = None
        
        # GNN 模型
        self.gnn_model = None
        
        # 初始化
        self._prepare_data()
        self._build_graph()
        self._init_gnn_model()
        
        logger.info("GNN Podcast 推薦系統初始化完成")
    
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
    
    def _build_graph(self):
        """建立使用者-Podcast 圖結構"""
        try:
            # 建立 NetworkX 圖
            self.graph = nx.Graph()
            
            # 添加節點
            for _, user in self.user_history[['user_idx', 'user_id']].drop_duplicates().iterrows():
                self.graph.add_node(user['user_idx'], type='user', id=user['user_id'])
            
            for _, podcast in self.podcast_data[['podcast_idx', 'id', 'category']].iterrows():
                self.graph.add_node(
                    podcast['podcast_idx'], 
                    type='podcast', 
                    id=podcast['id'],
                    category=podcast['category']
                )
            
            # 添加邊（使用者-內容互動）
            for _, interaction in self.user_history.iterrows():
                weight = interaction['rating'] * np.log1p(interaction['listen_time'])
                self.graph.add_edge(
                    interaction['user_idx'], 
                    interaction['podcast_idx'], 
                    weight=weight,
                    rating=interaction['rating'],
                    listen_time=interaction['listen_time']
                )
            
            # 添加同類別 Podcast 之間的邊
            for category in self.podcast_data['category'].unique():
                category_podcasts = self.podcast_data[self.podcast_data['category'] == category]['podcast_idx'].values
                for i in range(len(category_podcasts)):
                    for j in range(i + 1, len(category_podcasts)):
                        self.graph.add_edge(
                            category_podcasts[i], 
                            category_podcasts[j], 
                            weight=0.5,
                            type='category_similarity'
                        )
            
            logger.info(f"圖結構建立完成，包含 {self.graph.number_of_nodes()} 個節點和 {self.graph.number_of_edges()} 條邊")
            
        except Exception as e:
            logger.error(f"圖結構建立失敗: {str(e)}")
    
    def _init_gnn_model(self):
        """初始化 GNN 模型"""
        try:
            num_nodes = self.graph.number_of_nodes()
            
            # 建立節點特徵
            node_features = self._create_node_features()
            
            # 建立邊索引
            edge_index = self._create_edge_index()
            
            # 建立 PyTorch Geometric Data 物件
            self.graph_data = Data(
                x=torch.FloatTensor(node_features),
                edge_index=torch.LongTensor(edge_index),
                num_nodes=num_nodes
            )
            
            # 初始化 GNN 模型
            self.gnn_model = GNNModel(
                input_dim=node_features.shape[1],
                hidden_dim=self.hidden_dim,
                output_dim=self.embedding_dim
            )
            
            logger.info("GNN 模型初始化完成")
            
        except Exception as e:
            logger.error(f"GNN 模型初始化失敗: {str(e)}")
    
    def _create_node_features(self) -> np.ndarray:
        """建立節點特徵矩陣"""
        try:
            num_nodes = self.graph.number_of_nodes()
            feature_dim = 50  # 基礎特徵維度
            
            # 初始化特徵矩陣
            features = np.zeros((num_nodes, feature_dim))
            
            for node in self.graph.nodes():
                node_data = self.graph.nodes[node]
                
                if node_data['type'] == 'user':
                    # 使用者特徵：基於收聽歷史
                    user_interactions = self.user_history[
                        self.user_history['user_idx'] == node
                    ]
                    
                    # 平均評分
                    features[node, 0] = user_interactions['rating'].mean() if len(user_interactions) > 0 else 0
                    # 收聽時長
                    features[node, 1] = user_interactions['listen_time'].sum() if len(user_interactions) > 0 else 0
                    # 互動數量
                    features[node, 2] = len(user_interactions)
                    # 類別偏好（one-hot 編碼）
                    if len(user_interactions) > 0:
                        user_podcasts = user_interactions['podcast_idx'].values
                        user_categories = self.podcast_data[
                            self.podcast_data['podcast_idx'].isin(user_podcasts)
                        ]['category_idx'].values
                        for cat_idx in user_categories:
                            if cat_idx < feature_dim - 3:
                                features[node, 3 + cat_idx] = 1
                
                elif node_data['type'] == 'podcast':
                    # Podcast 特徵
                    podcast_info = self.podcast_data[
                        self.podcast_data['podcast_idx'] == node
                    ].iloc[0]
                    
                    # 類別編碼
                    features[node, 0] = podcast_info['category_idx']
                    # 受歡迎程度（互動次數）
                    interactions = self.user_history[
                        self.user_history['podcast_idx'] == node
                    ]
                    features[node, 1] = len(interactions)
                    features[node, 2] = interactions['rating'].mean() if len(interactions) > 0 else 0
                    features[node, 3] = interactions['listen_time'].sum() if len(interactions) > 0 else 0
            
            # 標準化特徵
            scaler = StandardScaler()
            features = scaler.fit_transform(features)
            
            return features
            
        except Exception as e:
            logger.error(f"節點特徵建立失敗: {str(e)}")
            return np.zeros((self.graph.number_of_nodes(), 50))
    
    def _create_edge_index(self) -> np.ndarray:
        """建立邊索引矩陣"""
        try:
            edges = list(self.graph.edges())
            edge_index = np.array(edges).T
            return edge_index
            
        except Exception as e:
            logger.error(f"邊索引建立失敗: {str(e)}")
            return np.array([])
    
    def train_gnn(self, epochs: int = 100, lr: float = 0.01):
        """訓練 GNN 模型"""
        try:
            if self.gnn_model is None or self.graph_data is None:
                logger.error("GNN 模型未初始化")
                return
            
            # 設定優化器
            optimizer = torch.optim.Adam(self.gnn_model.parameters(), lr=lr)
            
            # 訓練迴圈
            self.gnn_model.train()
            for epoch in range(epochs):
                optimizer.zero_grad()
                
                # 前向傳播
                embeddings = self.gnn_model(self.graph_data.x, self.graph_data.edge_index)
                
                # 計算損失（基於圖結構重建）
                loss = self._compute_reconstruction_loss(embeddings)
                
                # 反向傳播
                loss.backward()
                optimizer.step()
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}, Loss: {loss.item():.4f}")
            
            logger.info("GNN 模型訓練完成")
            
        except Exception as e:
            logger.error(f"GNN 訓練失敗: {str(e)}")
    
    def _compute_reconstruction_loss(self, embeddings: torch.Tensor) -> torch.Tensor:
        """計算重建損失"""
        try:
            # 計算節點間的相似度
            similarity = torch.mm(embeddings, embeddings.t())
            
            # 建立鄰接矩陣
            adj_matrix = torch.zeros(self.graph_data.num_nodes, self.graph_data.num_nodes)
            edge_index = self.graph_data.edge_index
            adj_matrix[edge_index[0], edge_index[1]] = 1
            adj_matrix[edge_index[1], edge_index[0]] = 1
            
            # 計算重建損失
            loss = F.binary_cross_entropy_with_logits(similarity, adj_matrix.float())
            
            return loss
            
        except Exception as e:
            logger.error(f"損失計算失敗: {str(e)}")
            return torch.tensor(0.0, requires_grad=True)
    
    def get_recommendations(self, user_id: str, top_k: int = 5, 
                          category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        基於 GNN 的推薦
        
        Args:
            user_id: 使用者 ID
            top_k: 推薦數量
            category_filter: 類別篩選
            
        Returns:
            推薦 Podcast 清單
        """
        try:
            if self.gnn_model is None:
                logger.error("GNN 模型未訓練")
                return []
            
            # 取得使用者索引
            if user_id not in self.user_encoder.classes_:
                logger.warning(f"使用者 {user_id} 不存在，使用熱門推薦")
                return self._get_popular_recommendations(top_k, category_filter)
            
            user_idx = self.user_encoder.transform([user_id])[0]
            
            # 取得節點嵌入
            self.gnn_model.eval()
            with torch.no_grad():
                embeddings = self.gnn_model(self.graph_data.x, self.graph_data.edge_index)
            
            # 計算使用者與所有 Podcast 的相似度
            user_embedding = embeddings[user_idx]
            podcast_indices = []
            
            for node in self.graph.nodes():
                node_data = self.graph.nodes[node]
                if node_data['type'] == 'podcast':
                    podcast_indices.append(node)
            
            podcast_embeddings = embeddings[podcast_indices]
            similarities = F.cosine_similarity(user_embedding.unsqueeze(0), podcast_embeddings)
            
            # 過濾已聽過的 Podcast
            listened_podcasts = set(self.user_history[
                self.user_history['user_id'] == user_id
            ]['podcast_id'].values)
            
            # 建立候選清單
            candidates = []
            for i, podcast_idx in enumerate(podcast_indices):
                podcast_id = self.podcast_encoder.inverse_transform([podcast_idx])[0]
                
                if podcast_id not in listened_podcasts:
                    # 檢查類別篩選
                    if category_filter:
                        podcast_category = self.podcast_data[
                            self.podcast_data['id'] == podcast_id
                        ]['category'].iloc[0]
                        if podcast_category != category_filter:
                            continue
                    
                    candidates.append((podcast_id, similarities[i].item()))
            
            # 排序並取前 top_k 個
            candidates.sort(key=lambda x: x[1], reverse=True)
            top_candidates = candidates[:top_k]
            
            # 豐富推薦結果
            recommendations = self._enrich_recommendations([podcast_id for podcast_id, _ in top_candidates])
            
            logger.info(f"為使用者 {user_id} 生成 {len(recommendations)} 個 GNN 推薦")
            return recommendations
            
        except Exception as e:
            logger.error(f"GNN 推薦失敗: {str(e)}")
            return []
    
    def _get_popular_recommendations(self, top_k: int, 
                                   category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """取得熱門推薦（新使用者）"""
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
            top_popular = popularity.nlargest(top_k, 'popularity_score')['podcast_id'].values
            
            return self._enrich_recommendations(top_popular)
            
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
                
                # 計算推薦理由
                reason = self._get_recommendation_reason(podcast_info['category'])
                
                recommendation = {
                    'podcast_id': podcast_id,
                    'title': podcast_info['title'],
                    'category': podcast_info['category'],
                    'description': podcast_info['description'],
                    'tags': podcast_info['tags'],
                    'recommendation_reason': reason,
                    'model_type': 'GNN'
                }
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"推薦結果豐富失敗: {str(e)}")
            return []
    
    def _get_recommendation_reason(self, category: str) -> str:
        """取得推薦理由"""
        reasons = {
            '財經': '基於您的財經興趣和圖神經網路分析，推薦此財經 Podcast',
            '自我成長': '根據您的自我成長偏好和圖結構學習，推薦此成長類 Podcast'
        }
        return reasons.get(category, '基於圖神經網路分析推薦')
    
    def visualize_graph(self, save_path: Optional[str] = None):
        """視覺化圖結構"""
        try:
            plt.figure(figsize=(12, 8))
            
            # 設定節點顏色
            node_colors = []
            for node in self.graph.nodes():
                if self.graph.nodes[node]['type'] == 'user':
                    node_colors.append('lightblue')
                else:
                    node_colors.append('lightcoral')
            
            # 繪製圖
            pos = nx.spring_layout(self.graph, k=1, iterations=50)
            nx.draw(
                self.graph, pos,
                node_color=node_colors,
                node_size=100,
                with_labels=False,
                alpha=0.7
            )
            
            plt.title('Podcast 推薦系統圖結構')
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"圖結構已儲存至 {save_path}")
            
            plt.show()
            
        except Exception as e:
            logger.error(f"圖結構視覺化失敗: {str(e)}")


class GNNModel(nn.Module):
    """
    圖神經網路模型
    使用 GCN (Graph Convolutional Network) 架構
    """
    
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        """
        初始化 GNN 模型
        
        Args:
            input_dim: 輸入特徵維度
            hidden_dim: 隱藏層維度
            output_dim: 輸出嵌入維度
        """
        super(GNNModel, self).__init__()
        
        # GCN 層
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.conv3 = GCNConv(hidden_dim, output_dim)
        
        # Dropout
        self.dropout = nn.Dropout(0.2)
        
        # 批次正規化
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        前向傳播
        
        Args:
            x: 節點特徵矩陣
            edge_index: 邊索引矩陣
            
        Returns:
            節點嵌入
        """
        # 第一層 GCN
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # 第二層 GCN
        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # 第三層 GCN
        x = self.conv3(x, edge_index)
        
        return x 