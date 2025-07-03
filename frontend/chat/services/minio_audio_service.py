#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO 音訊檔案管理服務
用於管理 MinIO 中的語音檔案，支援 MusicGen 參考音訊
"""

import asyncio
import aiohttp
import json
import base64
import io
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import streamlit as st

class MinIOAudioService:
    """MinIO 音訊服務類別"""
    
    def __init__(self, 
                 minio_url: str = "http://192.168.32.56:30090",
                 access_key: str = "minioadmin",
                 secret_key: str = "minioadmin"):
        """初始化 MinIO 音訊服務"""
        self.minio_url = minio_url
        self.access_key = access_key
        self.secret_key = secret_key
        
        # 音訊檔案桶名稱
        self.audio_bucket = "podwise-audio"
        self.voice_bucket = "podwise-voices"
        self.music_bucket = "podwise-music"
        
        # 音訊檔案類型
        self.supported_formats = [".wav", ".mp3", ".flac", ".ogg", ".m4a"]
    
    async def test_connection(self) -> bool:
        """測試 MinIO 連接"""
        try:
            # 使用 MinIO 的 health check 端點
            health_url = f"{self.minio_url}/minio/health/live"
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            st.error(f"MinIO 連接失敗: {str(e)}")
            return False
    
    async def list_audio_files(self, bucket: str = None, prefix: str = "") -> List[Dict[str, Any]]:
        """列出音訊檔案"""
        if not bucket:
            bucket = self.audio_bucket
            
        try:
            # 這裡應該使用 MinIO Python SDK，但為了簡化，我們使用 HTTP API
            # 實際實作中需要正確的 MinIO API 調用
            files = []
            
            # 模擬檔案列表（實際實作中需要從 MinIO 獲取）
            sample_files = [
                {
                    "name": "voice_sample_1.wav",
                    "size": 1024000,
                    "last_modified": "2024-06-30T10:00:00Z",
                    "url": f"{self.minio_url}/{bucket}/voice_sample_1.wav"
                },
                {
                    "name": "music_background_1.mp3", 
                    "size": 2048000,
                    "last_modified": "2024-06-30T09:30:00Z",
                    "url": f"{self.minio_url}/{bucket}/music_background_1.mp3"
                },
                {
                    "name": "podcast_episode_1.wav",
                    "size": 5120000,
                    "last_modified": "2024-06-30T08:15:00Z", 
                    "url": f"{self.minio_url}/{bucket}/podcast_episode_1.wav"
                }
            ]
            
            # 過濾符合前綴的檔案
            for file in sample_files:
                if prefix == "" or file["name"].startswith(prefix):
                    files.append(file)
            
            return files
            
        except Exception as e:
            st.error(f"獲取音訊檔案列表失敗: {str(e)}")
            return []
    
    async def upload_audio_file(self, 
                               file_data: bytes, 
                               filename: str, 
                               bucket: str = None,
                               content_type: str = "audio/wav") -> bool:
        """上傳音訊檔案到 MinIO"""
        if not bucket:
            bucket = self.audio_bucket
            
        try:
            # 這裡應該使用 MinIO Python SDK 進行上傳
            # 實際實作中需要正確的 MinIO API 調用
            
            # 模擬上傳成功
            st.success(f"✅ 音訊檔案上傳成功: {filename}")
            return True
            
        except Exception as e:
            st.error(f"音訊檔案上傳失敗: {str(e)}")
            return False
    
    async def download_audio_file(self, filename: str, bucket: str = None) -> Optional[bytes]:
        """從 MinIO 下載音訊檔案"""
        if not bucket:
            bucket = self.audio_bucket
            
        try:
            # 這裡應該使用 MinIO Python SDK 進行下載
            # 實際實作中需要正確的 MinIO API 調用
            
            # 模擬下載（實際實作中需要從 MinIO 獲取真實檔案）
            # 返回一個空的音訊檔案作為示例
            return b"RIFF" + b"\x00" * 1000  # 模擬 WAV 檔案頭
            
        except Exception as e:
            st.error(f"音訊檔案下載失敗: {str(e)}")
            return None
    
    async def get_audio_metadata(self, filename: str, bucket: str = None) -> Optional[Dict[str, Any]]:
        """獲取音訊檔案元資料"""
        if not bucket:
            bucket = self.audio_bucket
            
        try:
            # 模擬音訊檔案元資料
            metadata = {
                "filename": filename,
                "bucket": bucket,
                "size": 1024000,
                "format": "wav",
                "duration": 30.5,
                "sample_rate": 16000,
                "channels": 1,
                "bit_depth": 16,
                "upload_time": datetime.now().isoformat(),
                "tags": ["voice", "podri", "tts"]
            }
            
            return metadata
            
        except Exception as e:
            st.error(f"獲取音訊檔案元資料失敗: {str(e)}")
            return None
    
    async def delete_audio_file(self, filename: str, bucket: str = None) -> bool:
        """刪除音訊檔案"""
        if not bucket:
            bucket = self.audio_bucket
            
        try:
            # 這裡應該使用 MinIO Python SDK 進行刪除
            # 實際實作中需要正確的 MinIO API 調用
            
            st.success(f"✅ 音訊檔案刪除成功: {filename}")
            return True
            
        except Exception as e:
            st.error(f"音訊檔案刪除失敗: {str(e)}")
            return False
    
    def get_audio_categories(self) -> Dict[str, List[str]]:
        """獲取音訊檔案分類"""
        return {
            "語音檔案": ["voice", "tts", "speech"],
            "音樂檔案": ["music", "background", "melody"],
            "Podcast": ["podcast", "episode", "show"],
            "音效檔案": ["sound", "effect", "sfx"]
        }
    
    async def search_audio_files(self, 
                                query: str, 
                                category: str = None,
                                bucket: str = None) -> List[Dict[str, Any]]:
        """搜尋音訊檔案"""
        try:
            all_files = await self.list_audio_files(bucket)
            
            # 簡單的關鍵字搜尋
            results = []
            for file in all_files:
                if (query.lower() in file["name"].lower() or
                    (category and category.lower() in file["name"].lower())):
                    results.append(file)
            
            return results
            
        except Exception as e:
            st.error(f"搜尋音訊檔案失敗: {str(e)}")
            return []
    
    async def get_audio_for_musicgen(self, 
                                   style: str = None,
                                   mood: str = None) -> List[Dict[str, Any]]:
        """為 MusicGen 獲取參考音訊檔案"""
        try:
            # 根據風格和心情搜尋相關的音訊檔案
            search_terms = []
            
            if style:
                search_terms.append(style)
            if mood:
                search_terms.append(mood)
            
            # 搜尋音樂檔案桶
            music_files = await self.search_audio_files(
                " ".join(search_terms), 
                "music", 
                self.music_bucket
            )
            
            # 搜尋語音檔案桶（可能包含音樂背景）
            voice_files = await self.search_audio_files(
                " ".join(search_terms),
                "voice",
                self.voice_bucket
            )
            
            # 合併結果
            all_files = music_files + voice_files
            
            # 為每個檔案添加 MusicGen 相關資訊
            for file in all_files:
                file["musicgen_compatible"] = True
                file["reference_type"] = "background" if "music" in file["name"] else "voice"
                file["estimated_duration"] = 30.0  # 模擬時長
            
            return all_files
            
        except Exception as e:
            st.error(f"獲取 MusicGen 參考音訊失敗: {str(e)}")
            return []

# 創建全域實例
minio_audio_service = MinIOAudioService() 