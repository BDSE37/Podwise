#!/usr/bin/env python3
"""
模型下載腳本
用於在容器內下載必要的 AI 模型
"""

import os
import sys
import subprocess
from pathlib import Path

def download_model(model_name, model_path):
    """下載指定模型到指定路徑"""
    print(f"正在下載模型: {model_name}")
    
    # 建立模型目錄
    Path(model_path).mkdir(parents=True, exist_ok=True)
    
    # 使用 huggingface-cli 下載模型
    cmd = [
        "huggingface-cli", "download",
        model_name,
        "--local-dir", model_path,
        "--local-dir-use-symlinks", "False"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ 模型 {model_name} 下載完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 模型 {model_name} 下載失敗: {e}")
        print(f"錯誤輸出: {e.stderr}")
        return False

def main():
    """主函數：下載所有必要的模型"""
    print("🚀 開始下載 RAG Pipeline 所需模型...")
    
    # 定義需要下載的模型
    models = [
        {
            "name": "BAAI/bge-m3",
            "path": "/app/models/bge-m3"
        },
        {
            "name": "microsoft/DialoGPT-medium",
            "path": "/app/models/dialogpt"
        },
        {
            "name": "sentence-transformers/all-MiniLM-L6-v2",
            "path": "/app/models/sentence-transformers"
        }
    ]
    
    # 檢查是否安裝了 huggingface-cli
    try:
        subprocess.run(["huggingface-cli", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 未找到 huggingface-cli，正在安裝...")
        subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
    
    # 下載所有模型
    success_count = 0
    for model in models:
        if download_model(model["name"], model["path"]):
            success_count += 1
    
    print(f"\n📊 下載結果: {success_count}/{len(models)} 個模型下載成功")
    
    if success_count == len(models):
        print("✅ 所有模型下載完成！")
        return 0
    else:
        print("⚠️  部分模型下載失敗，請檢查網路連接和磁碟空間")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 