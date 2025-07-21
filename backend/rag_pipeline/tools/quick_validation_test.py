#!/usr/bin/env python3
"""
Podwise RAG Pipeline - 快速驗證測試

快速驗證安全工具的基本功能，確認在您的環境中能正常運作

作者: Podwise Team
版本: 1.0.0
"""

import os
import sys
import time
from typing import Dict, Any

# 添加路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 導入安全工具
from security_tool import (
    create_security_tool, SecurityLevel,
    GUARDRAILS_AVAILABLE
)


def quick_validation_test():
    """快速驗證測試"""
    print("🚀 Podwise 安全工具快速驗證測試")
    print("=" * 50)
    
    # 檢查 Guardrails AI 可用性
    print(f"\n📦 Guardrails AI 可用性: {'✅ 可用' if GUARDRAILS_AVAILABLE else '⚠️ 不可用'}")
    
    if not GUARDRAILS_AVAILABLE:
        print("💡 建議安裝: pip install guardrails-ai>=0.3.0")
    
    # 創建安全工具
    print("\n🔧 創建安全工具...")
    try:
        security_tool = create_security_tool(
            security_level=SecurityLevel.HIGH,
            blocked_keywords=["惡意", "攻擊", "病毒"],
            custom_patterns=[r"<script>.*</script>"]
        )
        print("✅ 安全工具創建成功")
    except Exception as e:
        print(f"❌ 安全工具創建失敗: {e}")
        return False
    
    # 測試用例
    test_cases = [
        {
            "name": "安全內容",
            "content": "這是一個正常的測試內容",
            "expected": True
        },
        {
            "name": "惡意關鍵字",
            "content": "這是一個惡意攻擊的內容",
            "expected": False
        },
        {
            "name": "XSS 攻擊",
            "content": "正常內容 <script>alert('xss')</script>",
            "expected": False
        },
        {
            "name": "長內容",
            "content": "測試內容 " * 1000,
            "expected": True
        }
    ]
    
    # 執行測試
    print("\n🧪 執行驗證測試...")
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  測試 {i}/{total_tests}: {test_case['name']}")
        
        try:
            start_time = time.time()
            result = security_tool.validate_content(test_case['content'])
            end_time = time.time()
            
            processing_time = end_time - start_time
            is_correct = result.is_valid == test_case['expected']
            
            if is_correct:
                print(f"    ✅ 通過 (處理時間: {processing_time:.4f}s)")
                passed_tests += 1
            else:
                print(f"    ❌ 失敗 - 期望: {test_case['expected']}, 實際: {result.is_valid}")
                if result.violations:
                    print(f"      違規項目: {result.violations}")
            
        except Exception as e:
            print(f"    ❌ 錯誤: {e}")
    
    # 顯示結果
    print("\n" + "=" * 50)
    print("📊 測試結果")
    print("=" * 50)
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"總測試數: {total_tests}")
    print(f"通過測試: {passed_tests}")
    print(f"失敗測試: {total_tests - passed_tests}")
    print(f"成功率: {success_rate:.1f}%")
    
    # 獲取統計資訊
    stats = security_tool.get_stats()
    print(f"\n📈 統計資訊:")
    print(f"  總驗證次數: {stats['total_validations']}")
    print(f"  平均處理時間: {stats['average_processing_time']:.4f}秒")
    
    # 建議
    print(f"\n💡 建議:")
    if success_rate >= 90:
        print("  ✅ 安全工具運作正常，可以投入使用")
    elif success_rate >= 70:
        print("  ⚠️ 安全工具基本可用，建議進一步測試")
    else:
        print("  ❌ 安全工具存在問題，需要檢查配置")
    
    if not GUARDRAILS_AVAILABLE:
        print("  📦 建議安裝 Guardrails AI 以獲得完整功能")
    
    return success_rate >= 70


def test_integration_scenarios():
    """測試整合場景"""
    print("\n🔗 測試整合場景...")
    
    try:
        # 測試 FastAPI 中間件
        from security_tool import create_fastapi_middleware
        middleware = create_fastapi_middleware(security_level=SecurityLevel.HIGH)
        print("  ✅ FastAPI 中間件創建成功")
        
        # 測試 LangChain 驗證器
        from security_tool import create_langchain_validator
        langchain_validator = create_langchain_validator(security_level=SecurityLevel.MEDIUM)
        print("  ✅ LangChain 驗證器創建成功")
        
        # 測試 CrewAI 驗證器
        from security_tool import create_crewai_validator
        crewai_validator = create_crewai_validator(security_level=SecurityLevel.HIGH)
        print("  ✅ CrewAI 驗證器創建成功")
        
        print("  ✅ 所有整合場景測試通過")
        return True
        
    except Exception as e:
        print(f"  ❌ 整合場景測試失敗: {e}")
        return False


def main():
    """主函數"""
    print("開始快速驗證測試...\n")
    
    # 基本功能測試
    basic_test_passed = quick_validation_test()
    
    # 整合場景測試
    integration_test_passed = test_integration_scenarios()
    
    # 最終結果
    print("\n" + "=" * 50)
    print("🎯 最終驗證結果")
    print("=" * 50)
    
    if basic_test_passed and integration_test_passed:
        print("✅ 所有測試通過！安全工具可以投入使用")
        print("\n📚 下一步:")
        print("  1. 查看 security_examples.py 了解使用方式")
        print("  2. 查看 SECURITY_INTEGRATION_GUIDE.md 了解整合方法")
        print("  3. 在您的專案中整合安全工具")
    else:
        print("❌ 部分測試失敗，請檢查配置和環境")
        print("\n🔧 故障排除:")
        print("  1. 檢查 Python 環境和依賴")
        print("  2. 確認 Guardrails AI 安裝狀態")
        print("  3. 查看錯誤日誌")
    
    print("\n📄 詳細測試報告請運行: python security_validation_test.py")


if __name__ == "__main__":
    main() 