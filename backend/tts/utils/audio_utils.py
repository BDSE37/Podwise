"""
音頻處理工具模組
提供音頻檔案處理和轉換功能
"""

import os
import tempfile
import soundfile as sf
import numpy as np
from config.settings import AUDIO_CONFIG

def save_audio(audio_data, output_path, sample_rate=None, format=None):
    """
    儲存音頻數據到檔案
    
    Args:
        audio_data (numpy.ndarray): 音頻數據
        output_path (str): 輸出檔案路徑
        sample_rate (int, optional): 採樣率，預設使用配置值
        format (str, optional): 音頻格式，預設使用配置值
    """
    if sample_rate is None:
        sample_rate = AUDIO_CONFIG["sample_rate"]
    if format is None:
        format = AUDIO_CONFIG["format"]
        
    sf.write(output_path, audio_data, sample_rate, format=format)

def create_temp_audio_file(suffix=".wav"):
    """
    創建臨時音頻檔案
    
    Args:
        suffix (str): 檔案副檔名
        
    Returns:
        str: 臨時檔案路徑
    """
    return tempfile.NamedTemporaryFile(suffix=suffix, delete=False).name

def load_audio(file_path):
    """
    載入音頻檔案
    
    Args:
        file_path (str): 音頻檔案路徑
        
    Returns:
        tuple: (音頻數據, 採樣率)
    """
    return sf.read(file_path)

def normalize_audio(audio_data):
    """
    正規化音頻數據
    
    Args:
        audio_data (numpy.ndarray): 音頻數據
        
    Returns:
        numpy.ndarray: 正規化後的音頻數據
    """
    return audio_data / np.max(np.abs(audio_data))

def resample_audio(audio_data, original_rate, target_rate):
    """
    重採樣音頻數據
    
    Args:
        audio_data (numpy.ndarray): 音頻數據
        original_rate (int): 原始採樣率
        target_rate (int): 目標採樣率
        
    Returns:
        numpy.ndarray: 重採樣後的音頻數據
    """
    if original_rate == target_rate:
        return audio_data
        
    duration = len(audio_data) / original_rate
    new_length = int(duration * target_rate)
    return np.interp(
        np.linspace(0, len(audio_data), new_length),
        np.arange(len(audio_data)),
        audio_data
    )

def convert_audio_format(input_path, output_path, target_format=None):
    """
    轉換音頻檔案格式
    
    Args:
        input_path (str): 輸入檔案路徑
        output_path (str): 輸出檔案路徑
        target_format (str, optional): 目標格式，預設使用配置值
    """
    if target_format is None:
        target_format = AUDIO_CONFIG["format"]
        
    audio_data, sample_rate = load_audio(input_path)
    save_audio(audio_data, output_path, sample_rate, target_format)

def stream_audio(file_path, chunk_size=None):
    """
    串流讀取音頻檔案
    
    Args:
        file_path (str): 音頻檔案路徑
        chunk_size (int, optional): 區塊大小，預設使用配置值
        
    Yields:
        bytes: 音頻數據區塊
    """
    if chunk_size is None:
        chunk_size = AUDIO_CONFIG["chunk_size"]
        
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk 