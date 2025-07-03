"""
STT 測試應用程式
使用 Streamlit 建立簡單的介面來測試語音轉文字功能
"""

import streamlit as st
import asyncio
import os
from datetime import datetime
from whisper_stt import WhisperSTT
from config.stt_config import STT_CONFIG

# 初始化 STT
stt = WhisperSTT(STT_CONFIG)

# 設定頁面標題
st.title("語音轉文字測試")

# 建立錄音按鈕
if st.button("開始錄音"):
    with st.spinner("正在錄音..."):
        # 錄製音頻
        result = asyncio.run(stt.process_audio())
        
        if result["success"]:
            # 顯示轉錄結果
            st.success("轉錄成功！")
            st.write("轉錄文字：")
            st.write(result["result"]["text"])
            
            # 顯示詳細資訊
            with st.expander("查看詳細資訊"):
                st.json(result["result"])
                
            # 如果配置了保存音頻
            if STT_CONFIG["output"]["save_audio"]:
                # 確保輸出目錄存在
                os.makedirs(STT_CONFIG["output"]["output_dir"], exist_ok=True)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{STT_CONFIG['output']['output_dir']}/audio_{timestamp}.{STT_CONFIG['output']['audio_format']}"
                
                # 保存音頻
                stt.save_audio(
                    result["result"]["audio_data"],
                    filename,
                    STT_CONFIG["audio"]["sample_rate"]
                )
                st.info(f"音頻已保存至：{filename}")
        else:
            st.error(f"轉錄失敗：{result['error']}")

# 顯示配置資訊
with st.sidebar:
    st.header("配置資訊")
    st.json(STT_CONFIG) 