#!/usr/bin/env python3
"""
逐步測試 RAG Pipeline 模組
"""

import sys
import os
import traceback

# 設定 Python 路徑
sys.path.insert(0, '/app')

def test_step(step_name, test_func):
    """執行測試步驟"""
    print(f"\n{'='*50}")
    print(f"測試步驟: {step_name}")
    print(f"{'='*50}")
    
    try:
        result = test_func()
        print(f"✅ {step_name} - 成功")
        return True
    except Exception as e:
        print(f"❌ {step_name} - 失敗")
        print(f"錯誤: {e}")
        print(f"詳細錯誤: {traceback.format_exc()}")
        return False

def test_1_basic_imports():
    """測試基礎套件導入"""
    import pandas as pd
    import numpy as np
    import yaml
    print(f"pandas 版本: {pd.__version__}")
    print(f"numpy 版本: {np.__version__}")
    return True

def test_2_config_module():
    """測試配置模組"""
    from config.integrated_config import PodwiseIntegratedConfig, get_config
    config = get_config()
    print(f"配置載入成功: {config.environment}")
    return True

def test_3_core_modules():
    """測試核心模組"""
    # 測試 enhanced_vector_search
    from core.enhanced_vector_search import RAGVectorSearch
    print("RAGVectorSearch 導入成功")
    
    # 測試其他核心模組
    from core.agent_manager import AgentManager
    print("AgentManager 導入成功")
    
    return True

def test_4_tools_modules():
    """測試工具模組"""
    from tools.cross_db_text_fetcher import CrossDBTextFetcher
    print("CrossDBTextFetcher 導入成功")
    
    from tools.summary_generator import SummaryGenerator
    print("SummaryGenerator 導入成功")
    
    from tools.similarity_matcher import SimilarityMatcher
    print("SimilarityMatcher 導入成功")
    
    return True

def test_5_app_modules():
    """測試應用模組"""
    from app.main_crewai import app
    print("FastAPI app 導入成功")
    
    return True

def test_6_full_import():
    """測試完整導入"""
    # 測試完整的 main 模組
    import app.main
    print("完整 main 模組導入成功")
    
    return True

def main():
    """主測試函數"""
    print("🚀 開始逐步測試 RAG Pipeline 模組")
    
    tests = [
        ("基礎套件導入", test_1_basic_imports),
        ("配置模組", test_2_config_module),
        ("核心模組", test_3_core_modules),
        ("工具模組", test_4_tools_modules),
        ("應用模組", test_5_app_modules),
        ("完整導入", test_6_full_import),
    ]
    
    results = []
    for step_name, test_func in tests:
        success = test_step(step_name, test_func)
        results.append((step_name, success))
        
        if not success:
            print(f"\n⚠️  步驟 '{step_name}' 失敗，是否繼續？(y/n): ", end="")
            response = input().strip().lower()
            if response != 'y':
                break
    
    # 總結
    print(f"\n{'='*50}")
    print("測試總結:")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for step_name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"{step_name}: {status}")
    
    print(f"\n總計: {passed}/{total} 個步驟通過")
    
    if passed == total:
        print("🎉 所有模組測試通過！可以啟動完整服務。")
    else:
        print("⚠️  部分模組有問題，建議使用簡化版本或逐步修復。")

if __name__ == "__main__":
    main() 