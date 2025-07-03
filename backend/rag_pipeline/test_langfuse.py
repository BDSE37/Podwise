#!/usr/bin/env python3
"""
測試 Langfuse 配置腳本
驗證您的 Langfuse 設定是否正常運作
"""

import os
import sys
from pathlib import Path

def test_langfuse_config():
    """測試 Langfuse 配置"""
    print("🔧 測試 Langfuse 配置")
    print("=" * 50)
    
    # 檢查環境變數
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    print(f"🔑 Public Key: {'✅ 已設定' if langfuse_public_key else '❌ 未設定'}")
    print(f"🔐 Secret Key: {'✅ 已設定' if langfuse_secret_key else '❌ 未設定'}")
    print(f"🌐 Host: {langfuse_host}")
    
    if not langfuse_public_key or not langfuse_secret_key:
        print("\n⚠️  Langfuse API Key 未設定，追蹤功能將停用")
        print("💡 請設定以下環境變數:")
        print("   export LANGFUSE_PUBLIC_KEY='your_public_key'")
        print("   export LANGFUSE_SECRET_KEY='your_secret_key'")
        return False
    
    # 測試導入 Langfuse
    try:
        import langfuse
        print("✅ Langfuse 套件已安裝")
    except ImportError:
        print("❌ Langfuse 套件未安裝")
        print("💡 請執行: pip install langfuse")
        return False
    
    # 測試您的 Langfuse 客戶端
    try:
        # 添加 backend 目錄到 Python 路徑
        backend_path = Path(__file__).parent.parent
        sys.path.insert(0, str(backend_path))
        
        from utils.langfuse_client import langfuse
        print("✅ 成功導入您的 Langfuse 客戶端")
        
        # 測試連接
        trace = langfuse.trace(
            name="test_connection",
            metadata={"test": True, "source": "rag_pipeline_test"}
        )
        trace.update(metadata={"status": "connected"})
        print("✅ Langfuse 連接測試成功")
        
        return True
        
    except Exception as e:
        print(f"❌ Langfuse 連接測試失敗: {e}")
        return False

def test_rag_pipeline_integration():
    """測試 RAG Pipeline 與 Langfuse 的整合"""
    print("\n🔗 測試 RAG Pipeline 與 Langfuse 整合")
    print("=" * 50)
    
    try:
        # 導入配置
        from config.integrated_config import get_config
        
        config = get_config()
        
        # 檢查 Langfuse 配置
        langfuse_config = config.get_langfuse_config()
        
        print(f"📊 Langfuse 啟用: {langfuse_config['enabled']}")
        print(f"🔍 思考過程追蹤: {langfuse_config['trace_thinking']}")
        print(f"🤖 模型選擇追蹤: {langfuse_config['trace_model_selection']}")
        print(f"👥 代理互動追蹤: {langfuse_config['trace_agent_interactions']}")
        print(f"🔍 向量搜尋追蹤: {langfuse_config['trace_vector_search']}")
        
        # 檢查是否已配置
        is_configured = config.is_langfuse_configured()
        print(f"✅ Langfuse 已配置: {is_configured}")
        
        return is_configured
        
    except Exception as e:
        print(f"❌ RAG Pipeline 整合測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🎯 Podwise RAG Pipeline - Langfuse 配置測試")
    print("=" * 60)
    
    # 測試基本配置
    basic_test = test_langfuse_config()
    
    # 測試 RAG Pipeline 整合
    integration_test = test_rag_pipeline_integration()
    
    print("\n📋 測試結果摘要")
    print("=" * 50)
    print(f"🔧 基本配置: {'✅ 通過' if basic_test else '❌ 失敗'}")
    print(f"🔗 整合測試: {'✅ 通過' if integration_test else '❌ 失敗'}")
    
    if basic_test and integration_test:
        print("\n🎉 所有測試通過！Langfuse 配置正常")
        print("💡 您可以開始使用 RAG Pipeline 進行本地測試")
    else:
        print("\n⚠️  部分測試失敗，請檢查配置")
        print("💡 建議:")
        print("   1. 設定 Langfuse API Key")
        print("   2. 安裝 langfuse 套件")
        print("   3. 檢查網路連接")

if __name__ == "__main__":
    main() 