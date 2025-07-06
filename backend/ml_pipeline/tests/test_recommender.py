#!/usr/bin/env python3
"""
ML Pipeline 推薦系統測試腳本
驗證各模組功能是否正常
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Any

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def create_test_data() -> tuple:
    """建立測試資料"""
    # Podcast 資料
    podcast_data = pd.DataFrame([
        {
            'id': 'p1', 'title': '財經早知道', 'category': '財經', 
            'description': '每日財經新聞解析，助您掌握投資先機',
            'tags': '投資,理財,股市,基金', 'popularity': 95
        },
        {
            'id': 'p2', 'title': '自我成長實驗室', 'category': '自我成長',
            'description': '探索個人潛能，實現自我突破',
            'tags': '心理學,成長,目標設定,習慣養成', 'popularity': 88
        },
        {
            'id': 'p3', 'title': '商業思維', 'category': '財經',
            'description': '深度解析商業模式與策略思維',
            'tags': '商業,策略,創業,管理', 'popularity': 92
        },
        {
            'id': 'p4', 'title': '心靈成長指南', 'category': '自我成長',
            'description': '心靈成長與心理健康指南',
            'tags': '心理學,冥想,情緒管理,正念', 'popularity': 85
        },
        {
            'id': 'p5', 'title': '投資理財學院', 'category': '財經',
            'description': '系統性學習投資理財知識',
            'tags': '投資,理財,資產配置,風險管理', 'popularity': 90
        }
    ])
    
    # 使用者歷史資料
    user_history = pd.DataFrame([
        {'user_id': 'user1', 'podcast_id': 'p1', 'rating': 4.5, 'listen_time': 120},
        {'user_id': 'user1', 'podcast_id': 'p3', 'rating': 4.0, 'listen_time': 90},
        {'user_id': 'user1', 'podcast_id': 'p5', 'rating': 4.8, 'listen_time': 150},
        {'user_id': 'user2', 'podcast_id': 'p2', 'rating': 4.2, 'listen_time': 100},
        {'user_id': 'user2', 'podcast_id': 'p4', 'rating': 4.6, 'listen_time': 110},
        {'user_id': 'user3', 'podcast_id': 'p1', 'rating': 4.7, 'listen_time': 130},
        {'user_id': 'user3', 'podcast_id': 'p2', 'rating': 4.1, 'listen_time': 85}
    ])
    
    return podcast_data, user_history

def test_podcast_recommender():
    """測試基礎推薦器"""
    print("=== 測試 PodcastRecommender ===")
    
    try:
        from podcast_recommender import PodcastRecommender
        
        # 建立測試資料
        podcast_data, user_history = create_test_data()
        
        # 初始化推薦器
        recommender = PodcastRecommender(podcast_data, user_history)
        print("✓ PodcastRecommender 初始化成功")
        
        # 測試推薦功能
        recommendations = recommender.get_recommendations("user1", top_k=3)
        print(f"✓ 為 user1 生成 {len(recommendations)} 個推薦")
        
        # 測試類別篩選
        finance_recs = recommender.get_recommendations("user1", top_k=2, category_filter="財經")
        print(f"✓ 財經類別推薦：{len(finance_recs)} 個")
        
        # 測試新使用者
        new_user_recs = recommender.get_recommendations("new_user", top_k=3)
        print(f"✓ 新使用者推薦：{len(new_user_recs)} 個")
        
        print("✓ PodcastRecommender 測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ PodcastRecommender 測試失敗: {str(e)}\n")
        return False

def test_gnn_recommender():
    """測試 GNN 推薦器"""
    print("=== 測試 GNNPodcastRecommender ===")
    
    try:
        from gnn_podcast_recommender import GNNPodcastRecommender
        
        # 建立測試資料
        podcast_data, user_history = create_test_data()
        
        # 初始化 GNN 推薦器
        gnn_recommender = GNNPodcastRecommender(podcast_data, user_history)
        print("✓ GNNPodcastRecommender 初始化成功")
        
        # 測試圖結構建立
        if gnn_recommender.graph is not None:
            print(f"✓ 圖結構建立成功：{gnn_recommender.graph.number_of_nodes()} 個節點")
        
        # 測試 GNN 模型初始化
        if gnn_recommender.gnn_model is not None:
            print("✓ GNN 模型初始化成功")
        
        print("✓ GNNPodcastRecommender 測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ GNNPodcastRecommender 測試失敗: {str(e)}\n")
        return False

def test_hybrid_recommender():
    """測試混合推薦器"""
    print("=== 測試 HybridGNNRecommender ===")
    
    try:
        from hybrid_gnn_recommender import HybridGNNRecommender
        
        # 建立測試資料
        podcast_data, user_history = create_test_data()
        
        # 初始化混合推薦器
        hybrid_recommender = HybridGNNRecommender(podcast_data, user_history)
        print("✓ HybridGNNRecommender 初始化成功")
        
        # 測試集成推薦
        ensemble_recs = hybrid_recommender.get_recommendations("user1", top_k=3, use_ensemble=True)
        print(f"✓ 集成推薦：{len(ensemble_recs)} 個")
        
        # 測試加權推薦
        weighted_recs = hybrid_recommender.get_recommendations("user1", top_k=3, use_ensemble=False)
        print(f"✓ 加權推薦：{len(weighted_recs)} 個")
        
        # 測試權重更新
        hybrid_recommender.update_weights(0.5, 0.3, 0.2)
        print("✓ 權重更新成功")
        
        print("✓ HybridGNNRecommender 測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ HybridGNNRecommender 測試失敗: {str(e)}\n")
        return False

def test_recommender_config():
    """測試配置管理"""
    print("=== 測試 RecommenderConfig ===")
    
    try:
        from recommender_config import get_recommender_config
        
        # 獲取配置
        config = get_recommender_config()
        print("✓ 配置獲取成功")
        
        # 檢查配置結構
        required_keys = ['base', 'content', 'collaborative', 'time', 'topic', 'popularity', 'behavior']
        for key in required_keys:
            if key in config:
                print(f"✓ 配置項 {key} 存在")
            else:
                print(f"✗ 配置項 {key} 缺失")
        
        print("✓ RecommenderConfig 測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ RecommenderConfig 測試失敗: {str(e)}\n")
        return False

def test_recommender_evaluator():
    """測試評估器"""
    print("=== 測試 RecommenderEvaluator ===")
    
    try:
        from recommender_evaluator import RecommenderEvaluator
        
        # 初始化評估器
        evaluator = RecommenderEvaluator()
        print("✓ RecommenderEvaluator 初始化成功")
        
        # 建立測試資料
        recommendations = [
            {'episode_id': 1, 'score': 0.8},
            {'episode_id': 2, 'score': 0.7},
            {'episode_id': 3, 'score': 0.6}
        ]
        
        ground_truth = [
            {'episode_id': 1, 'rating': 4.5},
            {'episode_id': 4, 'rating': 4.2}
        ]
        
        # 測試評估功能
        evaluation = evaluator.evaluate(recommendations, ground_truth)
        print(f"✓ 評估完成，指標數量：{len(evaluation)}")
        
        # 測試策略特定評估
        strategy_eval = evaluator.evaluate_strategy('content', recommendations, ground_truth)
        print(f"✓ 策略評估完成，指標數量：{len(strategy_eval)}")
        
        print("✓ RecommenderEvaluator 測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ RecommenderEvaluator 測試失敗: {str(e)}\n")
        return False

def test_recommender_main():
    """測試主控制器"""
    print("=== 測試 RecommenderSystem ===")
    
    try:
        from recommender_main import RecommenderSystem
        from recommender_config import get_recommender_config
        
        # 獲取配置
        config = get_recommender_config()
        
        # 初始化推薦系統（使用模擬資料庫 URL）
        recommender_system = RecommenderSystem(
            db_url="postgresql://test:test@localhost:5432/test",
            config=config
        )
        print("✓ RecommenderSystem 初始化成功")
        
        # 測試配置更新
        recommender_system.update_config({'test_param': 'test_value'})
        print("✓ 配置更新成功")
        
        print("✓ RecommenderSystem 測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ RecommenderSystem 測試失敗: {str(e)}\n")
        return False

def test_module_imports():
    """測試模組匯入"""
    print("=== 測試模組匯入 ===")
    
    try:
        # 測試 src 模組匯入
        from src import (
            PodcastRecommender,
            GNNPodcastRecommender,
            HybridGNNRecommender,
            Recommender,
            RecommenderData,
            RecommenderEvaluator,
            RecommenderSystem,
            get_recommender_config
        )
        
        print("✓ 所有模組匯入成功")
        print("✓ 模組匯入測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ 模組匯入測試失敗: {str(e)}\n")
        return False

def main():
    """主測試函數"""
    print("開始 ML Pipeline 推薦系統測試\n")
    
    test_results = []
    
    # 執行各項測試
    test_results.append(("模組匯入", test_module_imports()))
    test_results.append(("配置管理", test_recommender_config()))
    test_results.append(("基礎推薦器", test_podcast_recommender()))
    test_results.append(("GNN 推薦器", test_gnn_recommender()))
    test_results.append(("混合推薦器", test_hybrid_recommender()))
    test_results.append(("評估器", test_recommender_evaluator()))
    test_results.append(("主控制器", test_recommender_main()))
    
    # 統計結果
    print("=== 測試結果統計 ===")
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 通過" if result else "✗ 失敗"
        print(f"{test_name}: {status}")
    
    print(f"\n總計: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！ML Pipeline 推薦系統功能正常")
        return 0
    else:
        print("⚠️  部分測試失敗，請檢查相關模組")
        return 1

if __name__ == "__main__":
    exit(main()) 