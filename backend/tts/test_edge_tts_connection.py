#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edge TTS 連接測試腳本

測試 Edge TTS 是否正常工作，診斷可能的問題。
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_edge_tts_import():
    """測試 Edge TTS 導入"""
    print("🔍 測試 Edge TTS 導入...")
    try:
        import edge_tts
        print(f"✅ Edge TTS 導入成功，版本: {edge_tts.__version__}")
        return True
    except ImportError as e:
        print(f"❌ Edge TTS 導入失敗: {e}")
        return False

async def test_edge_tts_voices():
    """測試 Edge TTS 語音列表"""
    print("\n🔍 測試 Edge TTS 語音列表...")
    try:
        import edge_tts
        
        # 獲取所有語音
        voices = await edge_tts.list_voices()
        print(f"✅ 成功獲取 {len(voices)} 個語音")
        
        # 檢查台灣語音
        tw_voices = [v for v in voices if v.get('Locale', '').startswith('zh-TW')]
        print(f"✅ 找到 {len(tw_voices)} 個台灣語音:")
        
        for voice in tw_voices[:5]:  # 只顯示前5個
            print(f"  - {voice.get('ShortName', 'N/A')}: {voice.get('FriendlyName', 'N/A')}")
        
        return True
    except Exception as e:
        print(f"❌ 獲取語音列表失敗: {e}")
        return False

async def test_edge_tts_synthesis():
    """測試 Edge TTS 語音合成"""
    print("\n🔍 測試 Edge TTS 語音合成...")
    try:
        import edge_tts
        import tempfile
        
        # 測試語音
        test_voice = "zh-TW-HsiaoChenNeural"
        test_text = "您好，我是 Podrina，您的智能語音助手。"
        
        print(f"使用語音: {test_voice}")
        print(f"測試文字: {test_text}")
        
        # 創建臨時文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # 執行語音合成
            communicate = edge_tts.Communicate(test_text, test_voice)
            await communicate.save(temp_path)
            
            # 檢查文件
            if Path(temp_path).exists():
                file_size = Path(temp_path).stat().st_size
                print(f"✅ 語音合成成功，文件大小: {file_size} bytes")
                
                # 讀取文件內容
                with open(temp_path, 'rb') as f:
                    audio_data = f.read()
                print(f"✅ 音頻數據讀取成功: {len(audio_data)} bytes")
                
                return True
            else:
                print("❌ 語音合成失敗，文件未創建")
                return False
                
        finally:
            # 清理臨時文件
            if Path(temp_path).exists():
                Path(temp_path).unlink()
                
    except Exception as e:
        print(f"❌ 語音合成測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_provider_initialization():
    """測試提供者初始化"""
    print("\n🔍 測試 Edge TTS 提供者初始化...")
    try:
        from providers.edge_tts_provider import EdgeTTSProvider
        
        provider = EdgeTTSProvider()
        print("✅ Edge TTS 提供者初始化成功")
        
        # 測試語音列表
        voices = provider.get_available_voices()
        print(f"✅ 提供者語音列表: {len(voices)} 個語音")
        
        for voice in voices:
            print(f"  - {voice['name']}: {voice['voice_id']}")
        
        return True
    except Exception as e:
        print(f"❌ 提供者初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_provider_synthesis():
    """測試提供者語音合成"""
    print("\n🔍 測試提供者語音合成...")
    try:
        from providers.edge_tts_provider import EdgeTTSProvider
        
        provider = EdgeTTSProvider()
        
        # 測試語音合成
        test_text = "您好，我是 Podrina，您的智能語音助手。"
        audio_data = await provider.synthesize(test_text, "podrina")
        
        if audio_data:
            print(f"✅ 提供者語音合成成功: {len(audio_data)} bytes")
            return True
        else:
            print("❌ 提供者語音合成失敗")
            return False
            
    except Exception as e:
        print(f"❌ 提供者語音合成測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主測試函數"""
    print("🚀 開始 Edge TTS 連接測試...\n")
    
    # 測試導入
    if not test_edge_tts_import():
        print("\n❌ Edge TTS 導入失敗，請檢查安裝")
        return
    
    # 測試語音列表
    if not await test_edge_tts_voices():
        print("\n❌ Edge TTS 語音列表獲取失敗")
        return
    
    # 測試語音合成
    if not await test_edge_tts_synthesis():
        print("\n❌ Edge TTS 語音合成失敗")
        return
    
    # 測試提供者初始化
    if not test_provider_initialization():
        print("\n❌ Edge TTS 提供者初始化失敗")
        return
    
    # 測試提供者語音合成
    if not await test_provider_synthesis():
        print("\n❌ Edge TTS 提供者語音合成失敗")
        return
    
    print("\n✅ 所有測試通過！Edge TTS 功能正常")

if __name__ == "__main__":
    asyncio.run(main()) 