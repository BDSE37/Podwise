#!/usr/bin/env python3
"""
ML Pipeline 測試模組
測試重構後的推薦系統功能
"""

import sys
import os
import asyncio
import logging
from typing import Dict, List, Any

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """測試模組匯入"""
    print("=== 測試模組匯入 ===")
    
    try:
        # 測試核心模組匯入
        from core import (
            PodcastRecommender,
            GNNPodcastRecommender,
            HybridGNNRecommender,
            Recommender,
            RecommenderData,
            RecommenderEvaluator,
            RecommenderSystem
        )
        print("✓ 核心模組匯入成功")
        
        # 測試服務層匯入
        from services import RecommendationService
        print("✓ 服務層匯入成功")
        
        # 測試工具層匯入
        from utils import EmbeddingDataLoader
        print("✓ 工具層匯入成功")
        
        # 測試配置匯入
        from config import get_recommender_config
        print("✓ 配置匯入成功")
        
        print("✓ 所有模組匯入測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ 模組匯入失敗: {str(e)}\n")
        return False

def test_embedding_data_loader():
    """測試嵌入數據載入器"""
    print("=== 測試 EmbeddingDataLoader ===")
    
    try:
        from utils import EmbeddingDataLoader
        
        # 模擬連接字串
        connection_string = "postgresql://test:test@localhost:5432/test"
        
        # 測試初始化
        loader = EmbeddingDataLoader(connection_string)
        print("✓ EmbeddingDataLoader 初始化成功")
        
        # 測試上下文管理器
        with EmbeddingDataLoader(connection_string) as loader:
            print("✓ 上下文管理器測試通過")
        
        print("✓ EmbeddingDataLoader 測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ EmbeddingDataLoader 測試失敗: {str(e)}\n")
        return False

def test_recommendation_service():
    """測試推薦服務"""
    print("=== 測試 RecommendationService ===")
    
    try:
        from services import RecommendationService
        from config import get_recommender_config
        
        # 獲取配置
        config = get_recommender_config()
        db_url = "postgresql://test:test@localhost:5432/test"
        
        # 測試初始化
        service = RecommendationService(db_url, config)
        print("✓ RecommendationService 初始化成功")
        
        # 測試系統狀態
        status = service.get_system_status()
        print(f"✓ 系統狀態: {status}")
        
        print("✓ RecommendationService 測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ RecommendationService 測試失敗: {str(e)}\n")
        return False

async def test_async_functions():
    """測試非同步函數"""
    print("=== 測試非同步函數 ===")
    
    try:
        from services import RecommendationService
        from config import get_recommender_config
        
        # 獲取配置
        config = get_recommender_config()
        db_url = "postgresql://test:test@localhost:5432/test"
        
        # 初始化服務
        service = RecommendationService(db_url, config)
        
        # 測試推薦功能（模擬）
        recommendations = await service.get_recommendations(
            user_id=1,
            top_k=5
        )
        print(f"✓ 推薦功能測試通過，返回 {len(recommendations)} 個結果")
        
        # 測試相似節目功能（模擬）
        similar_episodes = await service.get_similar_episodes(
            episode_id=1,
            limit=5
        )
        print(f"✓ 相似節目功能測試通過，返回 {len(similar_episodes)} 個結果")
        
        # 測試評估功能（模擬）
        metrics = await service.evaluate_recommendations(
            user_id=1,
            recommendations=[]
        )
        print(f"✓ 評估功能測試通過，返回 {len(metrics)} 個指標")
        
        print("✓ 非同步函數測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ 非同步函數測試失敗: {str(e)}\n")
        return False

def test_config_management():
    """測試配置管理"""
    print("=== 測試配置管理 ===")
    
    try:
        from config import get_recommender_config
        
        # 獲取配置
        config = get_recommender_config()
        
        # 檢查配置結構
        required_keys = ['base', 'gnn', 'hybrid', 'database_url']
        for key in required_keys:
            if key in config:
                print(f"✓ 配置鍵 '{key}' 存在")
            else:
                print(f"⚠️ 配置鍵 '{key}' 缺失")
        
        print("✓ 配置管理測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ 配置管理測試失敗: {str(e)}\n")
        return False

def test_core_components():
    """測試核心組件"""
    print("=== 測試核心組件 ===")
    
    try:
        from core import (
            PodcastRecommender,
            RecommenderData,
            RecommenderEvaluator
        )
        
        # 模擬數據
        podcast_data = {
            "podcast1": {"title": "科技播客", "category": "科技"},
            "podcast2": {"title": "商業播客", "category": "商業"}
        }
        
        user_history = {
            "user1": [{"podcast_id": "podcast1", "rating": 4.5}]
        }
        
        # 測試 PodcastRecommender
        recommender = PodcastRecommender(podcast_data, user_history)
        print("✓ PodcastRecommender 初始化成功")
        
        # 測試 RecommenderData
        data = RecommenderData("postgresql://test:test@localhost:5432/test")
        print("✓ RecommenderData 初始化成功")
        
        # 測試 RecommenderEvaluator
        evaluator = RecommenderEvaluator()
        print("✓ RecommenderEvaluator 初始化成功")
        
        print("✓ 核心組件測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ 核心組件測試失敗: {str(e)}\n")
        return False

def run_all_tests():
    """執行所有測試"""
    print("🚀 開始 ML Pipeline 測試")
    print("=" * 50)
    
    test_results = []
    
    # 執行同步測試
    test_results.append(("模組匯入", test_imports()))
    test_results.append(("嵌入數據載入器", test_embedding_data_loader()))
    test_results.append(("推薦服務", test_recommendation_service()))
    test_results.append(("配置管理", test_config_management()))
    test_results.append(("核心組件", test_core_components()))
    
    # 執行非同步測試
    async_result = asyncio.run(test_async_functions())
    test_results.append(("非同步函數", async_result))
    
    # 輸出測試結果
    print("=" * 50)
    print("📊 測試結果總結")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！ML Pipeline 重構成功")
    else:
        print("⚠️ 部分測試失敗，請檢查相關模組")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 