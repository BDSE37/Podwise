#!/usr/bin/env python3 

"""
診斷原本的 RAG Pipeline 問題
檢查所有模組導入狀況
"""

import sys
import os
import traceback
from typing import Dict, Any

def test_import(module_name: str, description: str = "") -> Dict[str, Any]:
    """測試模組導入"""
    try:
        module = __import__(module_name)
        return {
            "module": module_name,
            "status": "✅ 成功",
            "description": description,
            "error": None
        }
    except Exception as e:
        return {
            "module": module_name,
            "status": "❌ 失敗",
            "description": description,
            "error": str(e)
        }

def test_core_modules():
    """測試核心模組"""
    print("🔍 測試核心模組導入...")
    print("=" * 60)
    
    core_modules = [
        ("fastapi", "FastAPI 框架"),
        ("uvicorn", "ASGI 伺服器"),
        ("pydantic", "數據驗證"),
        ("numpy", "數值計算"),
        ("pandas", "數據處理"),
        ("sqlalchemy", "資料庫 ORM"),
        ("psycopg2", "PostgreSQL 驅動"),
        ("requests", "HTTP 請求"),
        ("aiohttp", "異步 HTTP"),
        ("asyncio", "異步 IO"),
        ("logging", "日誌系統"),
        ("datetime", "日期時間"),
        ("typing", "類型提示"),
        ("dataclasses", "數據類別"),
        ("contextlib", "上下文管理"),
    ]
    
    results = []
    for module_name, description in core_modules:
        result = test_import(module_name, description)
        results.append(result)
        print(f"{result['status']} {module_name} - {description}")
        if result['error']:
            print(f"   錯誤: {result['error']}")
    
    return results

def test_rag_modules():
    """測試 RAG Pipeline 模組"""
    print("\n🔍 測試 RAG Pipeline 模組...")
    print("=" * 60)
    
    # 設定路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    rag_modules = [
        ("config.integrated_config", "整合配置"),
        ("core.enhanced_vector_search", "向量搜尋"),
        ("core.agent_manager", "代理管理器"),
        ("core.api_models", "API 模型"),
        ("core.hierarchical_rag_pipeline", "層級化 RAG"),
        ("core.apple_podcast_ranking", "Apple Podcast 排名"),
        ("core.content_categorizer", "內容分類器"),
        ("core.qwen3_llm_manager", "Qwen LLM 管理器"),
        ("core.chat_history_service", "聊天歷史服務"),
        ("tools.web_search_tool", "Web 搜尋工具"),
        ("tools.podcast_formatter", "Podcast 格式化工具"),
    ]
    
    results = []
    for module_name, description in rag_modules:
        result = test_import(module_name, description)
        results.append(result)
        print(f"{result['status']} {module_name} - {description}")
        if result['error']:
            print(f"   錯誤: {result['error']}")
    
    return results

def test_main_import():
    """測試 main.py 導入"""
    print("\n🔍 測試 main.py 導入...")
    print("=" * 60)
    
    try:
        # 測試導入 main.py 中的關鍵類別
        from main import PodwiseRAGPipeline, get_rag_pipeline
        print("✅ PodwiseRAGPipeline 類別導入成功")
        print("✅ get_rag_pipeline 函數導入成功")
        return True
    except Exception as e:
        print(f"❌ main.py 導入失敗: {str(e)}")
        print("詳細錯誤:")
        traceback.print_exc()
        return False

def test_app_import():
    """測試 app/main_crewai.py 導入"""
    print("\n🔍 測試 app/main_crewai.py 導入...")
    print("=" * 60)
    
    try:
        from app.main_crewai import app, app_manager
        print("✅ FastAPI app 導入成功")
        print("✅ ApplicationManager 導入成功")
        return True
    except Exception as e:
        print(f"❌ app/main_crewai.py 導入失敗: {str(e)}")
        print("詳細錯誤:")
        traceback.print_exc()
        return False

def check_file_structure():
    """檢查檔案結構"""
    print("\n🔍 檢查檔案結構...")
    print("=" * 60)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    required_files = [
        "main.py",
        "app/main_crewai.py",
        "config/integrated_config.py",
        "core/__init__.py",
        "tools/__init__.py",
    ]
    
    for file_path in required_files:
        full_path = os.path.join(current_dir, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - 檔案不存在")

def check_python_path():
    """檢查 Python 路徑"""
    print("\n🔍 檢查 Python 路徑...")
    print("=" * 60)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    
    print(f"當前目錄: {current_dir}")
    print(f"Backend 目錄: {backend_dir}")
    print(f"Python 路徑:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")

def main():
    """主診斷函數"""
    print("🚀 Podwise RAG Pipeline 診斷工具")
    print("=" * 60)
    
    # 檢查檔案結構
    check_file_structure()
    
    # 檢查 Python 路徑
    check_python_path()
    
    # 測試核心模組
    core_results = test_core_modules()
    
    # 測試 RAG 模組
    rag_results = test_rag_modules()
    
    # 測試 main.py 導入
    main_success = test_main_import()
    
    # 測試 app 導入
    app_success = test_app_import()
    
    # 總結
    print("\n📊 診斷總結")
    print("=" * 60)
    
    core_success = sum(1 for r in core_results if "成功" in r['status'])
    rag_success = sum(1 for r in rag_results if "成功" in r['status'])
    
    print(f"核心模組: {core_success}/{len(core_results)} 成功")
    print(f"RAG 模組: {rag_success}/{len(rag_results)} 成功")
    print(f"main.py 導入: {'✅ 成功' if main_success else '❌ 失敗'}")
    print(f"app 導入: {'✅ 成功' if app_success else '❌ 失敗'}")
    
    if core_success == len(core_results) and rag_success == len(rag_results) and main_success and app_success:
        print("\n🎉 所有模組導入成功！原本的 RAG Pipeline 應該可以正常運行。")
    else:
        print("\n⚠️  發現問題！建議使用修復版本或安裝缺失的套件。")
        
        # 顯示失敗的模組
        print("\n❌ 失敗的模組:")
        for result in core_results + rag_results:
            if "失敗" in result['status']:
                print(f"  - {result['module']}: {result['error']}")

if __name__ == "__main__":
    main() 