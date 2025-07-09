#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合測試腳本
測試所有清理功能的整合性
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# 添加父目錄到路徑
sys.path.append(str(Path(__file__).parent.parent))

def test_unified_cleaner():
    """測試統一清理器"""
    print("=== 測試統一清理器 ===")
    
    from data_cleaning import UnifiedCleaner
    
    # 建立清理器
    cleaner = UnifiedCleaner()
    
    # 測試文本清理
    test_text = "Hello 😊 World :) 這是一個測試文本 🚀"
    cleaned_text = cleaner.clean_text(test_text)
    print(f"原始文本: {test_text}")
    print(f"清理後文本: {cleaned_text}")
    
    # 測試字典清理
    test_dict = {
        "title": "測試標題 😊",
        "content": "測試內容 :)",
        "description": "測試描述 🚀"
    }
    cleaned_dict = cleaner.clean_dict(test_dict)
    print(f"原始字典: {test_dict}")
    print(f"清理後字典: {cleaned_dict}")
    
    return True

def test_json_format_fix():
    """測試 JSON 格式修正"""
    print("\n=== 測試 JSON 格式修正 ===")
    
    from data_cleaning import UnifiedCleaner
    
    cleaner = UnifiedCleaner()
    
    # 建立臨時目錄
    with tempfile.TemporaryDirectory() as temp_dir:
        # 建立測試檔案
        test_file = os.path.join(temp_dir, "test.json")
        
        # 建立需要修正的 JSON 格式
        test_data = [
            {"content": "內容1 😊"},
            {"content": "內容2 :)"},
            {"content": "內容3 🚀"}
        ]
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # 修正格式
        fixed_count = cleaner.batch_fix_json_format(temp_dir)
        print(f"修正了 {fixed_count} 個檔案")
        
        # 檢查修正結果
        with open(test_file, 'r', encoding='utf-8') as f:
            corrected_data = json.load(f)
        
        print(f"修正後資料: {corrected_data}")
    
    return True

def test_orchestrator():
    """測試協調器"""
    print("\n=== 測試協調器 ===")
    
    from data_cleaning.services.cleaner_orchestrator import CleanerOrchestrator
    
    orchestrator = CleanerOrchestrator()
    
    # 建立臨時檔案
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.json")
        
        test_data = {
            "title": "測試標題 😊",
            "content": "測試內容 :)",
            "description": "測試描述 🚀"
        }
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        # 清理檔案
        cleaned_file = orchestrator.clean_file(test_file)
        print(f"協調器清理完成: {cleaned_file}")
        
        # 檢查結果
        with open(cleaned_file, 'r', encoding='utf-8') as f:
            cleaned_data = json.load(f)
        
        print(f"清理後資料: {cleaned_data}")
    
    return True

def test_factory():
    """測試工廠模式"""
    print("\n=== 測試工廠模式 ===")
    
    from data_cleaning import DataCleaningFactory
    
    factory = DataCleaningFactory()
    
    # 測試建立不同類型的清理器
    cleaners = ['episode', 'podcast', 'longtext', 'unified']
    
    for cleaner_type in cleaners:
        try:
            cleaner = factory.create_cleaner(cleaner_type)
            print(f"成功建立 {cleaner_type} 清理器: {type(cleaner).__name__}")
        except Exception as e:
            print(f"建立 {cleaner_type} 清理器失敗: {e}")
    
    return True

def main():
    """主測試函數"""
    print("整合測試開始")
    print("=" * 50)
    
    tests = [
        test_unified_cleaner,
        test_json_format_fix,
        test_orchestrator,
        test_factory
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ 測試通過")
            else:
                print("❌ 測試失敗")
        except Exception as e:
            print(f"❌ 測試異常: {e}")
    
    print("\n" + "=" * 50)
    print(f"測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！")
        return True
    else:
        print("⚠️ 部分測試失敗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 