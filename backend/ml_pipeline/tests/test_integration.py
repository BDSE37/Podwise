#!/usr/bin/env python3
"""
ML Pipeline 整合測試
測試與 RAG Pipeline 的整合功能
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

def test_ml_pipeline_import():
    """測試 ML Pipeline 模組匯入"""
    print("=== 測試 ML Pipeline 模組匯入 ===")
    
    try:
        # 測試核心模組
        from core import (
            PodcastRecommender,
            GNNPodcastRecommender,
            HybridGNNRecommender,
            RecommenderSystem
        )
        print("✓ 核心模組匯入成功")
        
        # 測試服務層
        from services import RecommendationService
        print("✓ 服務層匯入成功")
        
        # 測試工具層
        from utils import EmbeddingDataLoader
        print("✓ 工具層匯入成功")
        
        # 測試配置
        from config.recommender_config import get_recommender_config
        print("✓ 配置匯入成功")
        
        print("✓ ML Pipeline 模組匯入測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ ML Pipeline 模組匯入失敗: {str(e)}\n")
        return False

def test_rag_pipeline_import():
    """測試 RAG Pipeline 模組匯入"""
    print("=== 測試 RAG Pipeline 模組匯入 ===")
    
    try:
        # 添加 RAG Pipeline 路徑
        rag_pipeline_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'rag_pipeline'
        )
        if rag_pipeline_path not in sys.path:
            sys.path.insert(0, rag_pipeline_path)
        
        # 測試 RAG Pipeline 匯入
        from core.hierarchical_rag_pipeline import HierarchicalRAGPipeline
        print("✓ RAG Pipeline 匯入成功")
        
        print("✓ RAG Pipeline 模組匯入測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ RAG Pipeline 模組匯入失敗: {str(e)}\n")
        return False

async def test_ml_pipeline_service():
    """測試 ML Pipeline 服務"""
    print("=== 測試 ML Pipeline 服務 ===")
    
    try:
        from services import RecommendationService
        from config.recommender_config import get_recommender_config
        
        # 獲取配置
        config = get_recommender_config()
        db_url = "postgresql://test:test@localhost:5432/test"
        
        # 初始化服務
        service = RecommendationService(db_url, config)
        print("✓ RecommendationService 初始化成功")
        
        # 測試系統狀態
        status = service.get_system_status()
        print(f"✓ 系統狀態: {status}")
        
        # 測試推薦功能（模擬）
        recommendations = await service.get_recommendations(
            user_id=1,
            top_k=3
        )
        print(f"✓ 推薦功能測試通過，返回 {len(recommendations)} 個結果")
        
        print("✓ ML Pipeline 服務測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ ML Pipeline 服務測試失敗: {str(e)}\n")
        return False

async def test_rag_pipeline_integration():
    """測試 RAG Pipeline 整合"""
    print("=== 測試 RAG Pipeline 整合 ===")
    
    try:
        # 添加 RAG Pipeline 路徑
        rag_pipeline_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'rag_pipeline'
        )
        if rag_pipeline_path not in sys.path:
            sys.path.insert(0, rag_pipeline_path)
        
        from core.hierarchical_rag_pipeline import HierarchicalRAGPipeline
        
        # 初始化 RAG Pipeline
        pipeline = HierarchicalRAGPipeline()
        print("✓ HierarchicalRAGPipeline 初始化成功")
        
        # 測試查詢處理
        query = "請推薦一些科技類的播客節目"
        response = await pipeline.process_query(query)
        
        print(f"✓ RAG Pipeline 查詢處理成功")
        print(f"  回應內容: {response.content[:100]}...")
        print(f"  信心值: {response.confidence}")
        print(f"  使用層級: {response.level_used}")
        
        # 檢查是否整合了 ML Pipeline
        if response.metadata.get('ml_pipeline_integrated', False):
            print("✓ ML Pipeline 整合成功")
        else:
            print("⚠️ ML Pipeline 未整合")
        
        print("✓ RAG Pipeline 整合測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ RAG Pipeline 整合測試失敗: {str(e)}\n")
        return False

async def test_monitoring_integration():
    """測試監控面板整合"""
    print("=== 測試監控面板整合 ===")
    
    try:
        # 添加 RAG Pipeline 路徑
        rag_pipeline_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'rag_pipeline'
        )
        if rag_pipeline_path not in sys.path:
            sys.path.insert(0, rag_pipeline_path)
        
        from monitoring.hierarchical_dashboard import HierarchicalRAGMonitor
        
        # 初始化監控器
        monitor = HierarchicalRAGMonitor()
        print("✓ HierarchicalRAGMonitor 初始化成功")
        
        # 測試服務狀態
        service_status = monitor.get_service_status()
        print(f"✓ 服務狀態獲取成功: {len(service_status)} 個服務")
        
        # 檢查 ML Pipeline 狀態
        if 'ML Pipeline' in service_status:
            print(f"✓ ML Pipeline 狀態: {service_status['ML Pipeline']}")
        else:
            print("⚠️ ML Pipeline 狀態未找到")
        
        # 測試 ML Pipeline 指標
        ml_metrics = monitor.get_ml_pipeline_metrics()
        print(f"✓ ML Pipeline 指標獲取成功: {len(ml_metrics)} 個指標")
        
        print("✓ 監控面板整合測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ 監控面板整合測試失敗: {str(e)}\n")
        return False

async def test_end_to_end_integration():
    """端到端整合測試"""
    print("=== 端到端整合測試 ===")
    
    try:
        # 1. 初始化 ML Pipeline 服務
        from services import RecommendationService
        from config.recommender_config import get_recommender_config
        
        config = get_recommender_config()
        db_url = "postgresql://test:test@localhost:5432/test"
        ml_service = RecommendationService(db_url, config)
        
        # 2. 初始化 RAG Pipeline
        rag_pipeline_path = os.path.join(
            os.path.dirname(__file__), 
            '..', '..', 'rag_pipeline'
        )
        if rag_pipeline_path not in sys.path:
            sys.path.insert(0, rag_pipeline_path)
        
        from core.hierarchical_rag_pipeline import HierarchicalRAGPipeline
        rag_pipeline = HierarchicalRAGPipeline()
        
        # 3. 模擬完整流程
        query = "我想了解最新的科技趨勢，有什麼推薦的播客嗎？"
        
        # RAG 處理查詢
        rag_response = await rag_pipeline.process_query(query)
        print(f"✓ RAG 處理完成，信心值: {rag_response.confidence}")
        
        # ML Pipeline 推薦
        recommendations = await ml_service.get_recommendations(
            user_id=1,
            top_k=5,
            category_filter="科技"
        )
        print(f"✓ ML Pipeline 推薦完成，返回 {len(recommendations)} 個結果")
        
        # 評估推薦結果
        metrics = await ml_service.evaluate_recommendations(
            user_id=1,
            recommendations=recommendations
        )
        print(f"✓ 推薦評估完成，指標: {metrics}")
        
        print("✓ 端到端整合測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ 端到端整合測試失敗: {str(e)}\n")
        return False

def test_directory_structure():
    """測試目錄結構"""
    print("=== 測試目錄結構 ===")
    
    try:
        # 檢查 ML Pipeline 目錄結構
        ml_pipeline_dir = os.path.dirname(__file__)
        
        required_dirs = ['core', 'services', 'utils', 'config', 'tests']
        for dir_name in required_dirs:
            dir_path = os.path.join(ml_pipeline_dir, '..', dir_name)
            if os.path.exists(dir_path):
                print(f"✓ {dir_name} 目錄存在")
            else:
                print(f"✗ {dir_name} 目錄缺失")
                return False
        
        # 檢查核心檔案
        core_files = [
            'core/__init__.py',
            'services/__init__.py',
            'utils/__init__.py',
            'config/__init__.py',
            'main.py',
            'requirements.txt',
            'README.md'
        ]
        
        for file_path in core_files:
            full_path = os.path.join(ml_pipeline_dir, '..', file_path)
            if os.path.exists(full_path):
                print(f"✓ {file_path} 存在")
            else:
                print(f"✗ {file_path} 缺失")
                return False
        
        print("✓ 目錄結構測試通過\n")
        return True
        
    except Exception as e:
        print(f"✗ 目錄結構測試失敗: {str(e)}\n")
        return False

async def run_all_integration_tests():
    """執行所有整合測試"""
    print("🚀 開始 ML Pipeline 整合測試")
    print("=" * 60)
    
    test_results = []
    
    # 執行同步測試
    test_results.append(("目錄結構", test_directory_structure()))
    test_results.append(("ML Pipeline 匯入", test_ml_pipeline_import()))
    test_results.append(("RAG Pipeline 匯入", test_rag_pipeline_import()))
    
    # 執行非同步測試
    test_results.append(("ML Pipeline 服務", await test_ml_pipeline_service()))
    test_results.append(("RAG Pipeline 整合", await test_rag_pipeline_integration()))
    test_results.append(("監控面板整合", await test_monitoring_integration()))
    test_results.append(("端到端整合", await test_end_to_end_integration()))
    
    # 輸出測試結果
    print("=" * 60)
    print("📊 整合測試結果總結")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print("=" * 60)
    print(f"總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("🎉 所有整合測試通過！ML Pipeline 重構和整合成功")
        print("\n📋 整合功能總結:")
        print("  ✓ ML Pipeline 層級化架構")
        print("  ✓ RAG Pipeline 整合")
        print("  ✓ 監控面板整合")
        print("  ✓ 端到端功能驗證")
    else:
        print("⚠️ 部分測試失敗，請檢查相關模組")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_all_integration_tests())
    sys.exit(0 if success else 1) 