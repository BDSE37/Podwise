# Podwise STT Pipeline

## 概述

Podwise STT Pipeline 是語音識別服務模組，負責將語音轉換為文本。支援多種語音識別引擎和語言，提供統一的 OOP 介面。

## 架構設計

### 核心組件

#### 1. 語音識別器 (Speech Recognizer)
- **職責**：核心語音識別功能
- **實現**：`SpeechRecognizer` 類別
- **功能**：
  - 音頻預處理
  - 語音識別
  - 文本後處理

#### 2. 音頻處理器 (Audio Processor)
- **職責**：音頻格式處理和轉換
- **實現**：`AudioProcessor` 類別
- **功能**：
  - 音頻格式轉換
  - 音頻品質優化
  - 音頻分割

#### 3. 語言模型管理器 (Language Model Manager)
- **職責**：管理不同的語言模型
- **實現**：`LanguageModelManager` 類別
- **功能**：
  - 模型載入和切換
  - 模型性能優化
  - 模型版本管理

#### 4. 結果後處理器 (Post Processor)
- **職責**：識別結果的後處理
- **實現**：`PostProcessor` 類別
- **功能**：
  - 文本清理
  - 標點符號添加
  - 格式標準化

## 統一服務管理器

### STTPipelineManager 類別
- **職責**：整合所有 STT 功能，提供統一的 OOP 介面
- **主要方法**：
  - `transcribe_audio()`: 音頻轉錄
  - `get_supported_languages()`: 獲取支援語言
  - `health_check()`: 健康檢查
  - `get_statistics()`: 獲取統計資訊

### 識別流程
1. **音頻預處理**：清理和標準化音頻
2. **語言檢測**：自動檢測或指定語言
3. **語音識別**：將語音轉換為文本
4. **文本後處理**：清理和格式化文本
5. **結果驗證**：驗證識別結果品質

## 配置系統

### STT 配置
- **檔案**：`config/stt_config.py`
- **功能**：
  - 識別引擎配置
  - 音頻格式設定
  - 語言模型配置

### 音頻配置
- **檔案**：`config/audio_config.py`
- **功能**：
  - 音頻處理參數
  - 品質設定
  - 格式支援

## 數據模型

### 核心數據類別
- `TranscriptionRequest`: 轉錄請求
- `TranscriptionResult`: 轉錄結果
- `AudioFormat`: 音頻格式
- `LanguageModel`: 語言模型

### 工廠函數
- `create_transcription_request()`: 創建轉錄請求
- `create_transcription_result()`: 創建轉錄結果
- `create_audio_format()`: 創建音頻格式

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的 STT 功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的識別引擎
- 可擴展的識別流程

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的識別引擎

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有識別器都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合 STT 管道管理器
  - 語音識別服務控制
  - 健康檢查和語言資訊

### 使用方式
```python
# 創建 STT 管道實例
from core.stt_pipeline_manager import STTPipelineManager

pipeline = STTPipelineManager()

# 音頻轉錄
result = await pipeline.transcribe_audio(
    audio_file="audio.wav",
    language="zh-TW",
    format="wav"
)

# 獲取支援語言
languages = pipeline.get_supported_languages()

# 獲取統計資訊
stats = pipeline.get_statistics()
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證語言模型可用性
- 監控識別性能
- 檢查音頻處理能力

### 性能指標
- 識別準確率
- 處理速度
- 支援格式數量
- 錯誤率統計

## 技術棧

- **框架**：FastAPI
- **語音識別**：Whisper, Azure Speech
- **音頻處理**：librosa, pydub
- **語言模型**：多語言支援
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-stt-pipeline .

# 運行容器
docker run -p 8004:8004 podwise-stt-pipeline
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/transcribe` - 音頻轉錄
- `GET /api/v1/languages` - 獲取支援語言
- `GET /api/v1/statistics` - 統計資訊
- `POST /api/v1/batch-transcribe` - 批量轉錄

## 架構優勢

1. **高準確率**：支援多種高品質識別引擎
2. **多語言**：支援多種語言識別
3. **可擴展性**：支援新的識別引擎和模型
4. **可維護性**：清晰的模組化設計
5. **一致性**：統一的數據模型和介面設計 