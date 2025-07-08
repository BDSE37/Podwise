#!/usr/bin/env python3
"""
TTS 測試腳本
"""

import asyncio
import edge_tts
import tempfile
import os

async def test_edge_tts():
    """測試 Edge TTS 功能"""
    try:
        # 測試基本語音合成
        text = "你好，這是測試語音"
        voice = "zh-TW-HsiaoChenNeural"
        
        print(f"測試語音合成: {text}")
        print(f"使用語音: {voice}")
        
        # 創建臨時文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # 使用 Edge TTS 合成
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_path)
            
            # 檢查文件大小
            file_size = os.path.getsize(temp_path)
            print(f"語音合成成功！文件大小: {file_size} bytes")
            print(f"文件路徑: {temp_path}")
            
            return True
            
        finally:
            # 清理臨時文件
            try:
                os.unlink(temp_path)
            except:
                pass
                
    except Exception as e:
        print(f"語音合成失敗: {e}")
        return False

async def list_voices():
    """列出可用的語音"""
    try:
        voices = await edge_tts.list_voices()
        print("可用的語音:")
        for voice in voices:
            if "zh-TW" in voice["ShortName"]:
                print(f"  {voice['ShortName']}: {voice['FriendlyName']}")
    except Exception as e:
        print(f"獲取語音列表失敗: {e}")

if __name__ == "__main__":
    print("=== Edge TTS 測試 ===")
    
    # 列出語音
    asyncio.run(list_voices())
    
    print("\n=== 語音合成測試 ===")
    result = asyncio.run(test_edge_tts())
    
    if result:
        print("✅ TTS 測試成功！")
    else:
        print("❌ TTS 測試失敗！") 