#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 TTS 模組對共用工具的引用

驗證 backend/utils 中的共用工具是否能被 TTS 模組正確引用。
"""

import os
import sys

# 添加 backend 路徑
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(backend_path)

def test_utils_import():
    """測試共用工具的引用"""
    try:
        # 測試日誌配置
        from utils.logging_config import get_logger
        logger = get_logger(__name__)
        print("✅ 成功引用 logging_config")
        
        # 測試通用工具
        from utils.common_utils import clean_path, safe_get
        print("✅ 成功引用 common_utils")
        
        # 測試環境配置
        from utils.env_config import PodriConfig
        config = PodriConfig()
        print("✅ 成功引用 env_config")
        
        # 測試 Langfuse 客戶端
        from utils.langfuse_client import langfuse
        print("✅ 成功引用 langfuse_client")
        
        print("\n🎉 所有共用工具引用測試通過！")
        return True
        
    except ImportError as e:
        print(f"❌ 引用失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def test_tts_service_import():
    """測試 TTS 服務是否能正確引用共用工具"""
    try:
        from tts_service import TTSService
        print("✅ TTS 服務引用成功")
        return True
    except Exception as e:
        print(f"❌ TTS 服務引用失敗: {e}")
        return False

if __name__ == "__main__":
    print("🧪 開始測試共用工具引用...\n")
    
    # 測試共用工具引用
    utils_ok = test_utils_import()
    
    # 測試 TTS 服務引用
    tts_ok = test_tts_service_import()
    
    print(f"\n📊 測試結果:")
    print(f"  共用工具引用: {'✅ 通過' if utils_ok else '❌ 失敗'}")
    print(f"  TTS 服務引用: {'✅ 通過' if tts_ok else '❌ 失敗'}")
    
    if utils_ok and tts_ok:
        print("\n🎉 所有測試通過！共用工具已正確配置。")
    else:
        print("\n⚠️  部分測試失敗，請檢查配置。") 