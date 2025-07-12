#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷音檔播放問題
"""

import requests
import json
import subprocess
import sys

def check_backend_service():
    """檢查後端服務狀態"""
    print("🔍 檢查後端服務狀態...")
    try:
        response = requests.get("http://localhost:8006/health", timeout=5)
        if response.status_code == 200:
            print("✅ 後端服務正常運行")
            return True
        else:
            print(f"❌ 後端服務異常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 無法連接到後端服務: {e}")
        return False

def check_minio_connection():
    """檢查 MinIO 連接"""
    print("\n🔍 檢查 MinIO 連接...")
    try:
        # 檢查 MinIO 是否可訪問
        response = requests.get("http://localhost:9000/minio/health/live", timeout=5)
        if response.status_code == 200:
            print("✅ MinIO 服務可訪問")
        else:
            print(f"⚠️ MinIO 服務回應異常: {response.status_code}")
    except Exception as e:
        print(f"❌ 無法連接到 MinIO: {e}")
        return False
    
    # 檢查 bucket 是否存在
    try:
        response = requests.post(
            "http://localhost:8006/api/category/recommendations",
            headers={"Content-Type": "application/json"},
            json={"category": "business"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('total_count', 0) > 0:
                print("✅ MinIO bucket 可正常訪問，有推薦節目")
                return True
            else:
                print("⚠️ MinIO bucket 可訪問，但沒有推薦節目")
                return True
        else:
            print(f"❌ 推薦 API 失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 檢查 MinIO bucket 失敗: {e}")
        return False

def test_audio_stream():
    """測試音檔串流"""
    print("\n🔍 測試音檔串流...")
    try:
        response = requests.post(
            "http://localhost:8006/api/audio/stream",
            headers={"Content-Type": "application/json"},
            json={
                "rss_id": "1488295306",
                "episode_title": "關稅倒數",
                "category": "business"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('audio_url'):
                print("✅ 音檔串流 API 正常")
                print(f"   音檔 URL: {data['audio_url'][:80]}...")
                
                # 測試音檔是否可訪問
                try:
                    audio_response = requests.head(data['audio_url'], timeout=10)
                    if audio_response.status_code == 200:
                        print("✅ 音檔可正常訪問")
                        return True
                    else:
                        print(f"❌ 音檔訪問失敗: {audio_response.status_code}")
                        return False
                except Exception as e:
                    print(f"❌ 音檔訪問測試失敗: {e}")
                    return False
            else:
                print("❌ 音檔串流 API 返回錯誤")
                return False
        else:
            print(f"❌ 音檔串流 API 失敗: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 音檔串流測試失敗: {e}")
        return False

def check_frontend_access():
    """檢查前端訪問"""
    print("\n🔍 檢查前端訪問...")
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服務可訪問")
            return True
        else:
            print(f"❌ 前端服務異常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 無法連接到前端服務: {e}")
        return False

def check_processes():
    """檢查相關進程"""
    print("\n🔍 檢查相關進程...")
    
    processes = [
        ("user_preference_service", "後端服務"),
        ("http.server", "前端服務器"),
        ("minio", "MinIO 服務")
    ]
    
    for process_name, description in processes:
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ {description} 正在運行")
            else:
                print(f"❌ {description} 未運行")
        except Exception as e:
            print(f"❌ 檢查 {description} 失敗: {e}")

def main():
    """主診斷函數"""
    print("🚀 開始診斷 Podwise 音檔播放問題")
    print("="*60)
    
    # 檢查進程
    check_processes()
    
    # 檢查後端服務
    backend_ok = check_backend_service()
    
    # 檢查 MinIO
    minio_ok = check_minio_connection()
    
    # 測試音檔串流
    audio_ok = test_audio_stream()
    
    # 檢查前端
    frontend_ok = check_frontend_access()
    
    print("\n" + "="*60)
    print("📊 診斷結果總結:")
    print(f"   後端服務: {'✅ 正常' if backend_ok else '❌ 異常'}")
    print(f"   MinIO 連接: {'✅ 正常' if minio_ok else '❌ 異常'}")
    print(f"   音檔串流: {'✅ 正常' if audio_ok else '❌ 異常'}")
    print(f"   前端服務: {'✅ 正常' if frontend_ok else '❌ 異常'}")
    
    if all([backend_ok, minio_ok, audio_ok, frontend_ok]):
        print("\n🎉 所有組件都正常！音檔播放應該可以工作。")
        print("\n💡 請在瀏覽器中訪問:")
        print("   - 主頁面: http://localhost:8080/index.html")
        print("   - 測試頁面: http://localhost:8080/test_audio.html")
    else:
        print("\n⚠️ 發現問題，請檢查上述異常項目。")
        
        if not backend_ok:
            print("\n🔧 後端服務問題解決方案:")
            print("   1. 確保在 backend/api 目錄下運行: python user_preference_service.py")
            print("   2. 檢查端口 8006 是否被佔用")
            
        if not minio_ok:
            print("\n🔧 MinIO 問題解決方案:")
            print("   1. 確保 MinIO 服務正在運行")
            print("   2. 檢查端口 9000 是否可訪問")
            print("   3. 確認 bucket 名稱正確")
            
        if not audio_ok:
            print("\n🔧 音檔串流問題解決方案:")
            print("   1. 檢查 MinIO 認證配置")
            print("   2. 確認音檔檔案存在")
            print("   3. 檢查檔案名稱格式")

if __name__ == "__main__":
    main() 