# Podwise TTS Pipeline

## 概述

Podwise TTS Pipeline 是語音合成服務模組，負責將文本轉換為高品質的語音輸出。支援多種語音模型和語言，提供統一的 OOP 介面。

## 架構設計

### 核心組件

#### 1. 語音合成器 (Speech Synthesizer)
- **職責**：核心語音合成功能
- **實現**：`SpeechSynthesizer` 類別
- **功能**：
  - 文本預處理
  - 語音合成
  - 音頻後處理

#### 2. 語音模型管理器 (Voice Model Manager)
- **職責**：管理不同的語音模型
- **實現**：`VoiceModelManager` 類別
- **功能**：
  - 模型載入和切換
  - 模型性能優化
  - 模型版本管理

#### 3. 音頻處理器 (Audio Processor)
- **職責**：音頻格式處理和轉換
- **實現**：`AudioProcessor` 類別
- **功能**：
  - 音頻格式轉換
  - 音頻品質優化
  - 音頻壓縮

#### 4. 快取管理器 (Cache Manager)
- **職責**：語音合成結果快取
- **實現**：`CacheManager` 類別
- **功能**：
  - 結果快取
  - 快取清理
  - 快取統計

## 統一服務管理器

### TTSPipelineManager 類別
- **職責**：整合所有 TTS 功能，提供統一的 OOP 介面
- **主要方法**：
  - `synthesize_speech()`: 語音合成
  - `get_available_voices()`: 獲取可用語音
  - `health_check()`: 健康檢查
  - `clear_cache()`: 清理快取

### 合成流程
1. **文本預處理**：清理和標準化文本
2. **語音選擇**：選擇合適的語音模型
3. **語音合成**：生成語音音頻
4. **音頻後處理**：優化音頻品質
5. **結果快取**：快取合成結果

## 配置系統

### TTS 配置
- **檔案**：`config/tts_config.py`
- **功能**：
  - 語音模型配置
  - 音頻格式設定
  - 快取配置

### 語音配置
- **檔案**：`config/voice_config.py`
- **功能**：
  - 語音模型參數
  - 語音特性設定
  - 語言支援配置

## 數據模型

### 核心數據類別
- `SynthesisRequest`: 合成請求
- `SynthesisResult`: 合成結果
- `VoiceModel`: 語音模型
- `AudioFormat`: 音頻格式

### 工廠函數
- `create_synthesis_request()`: 創建合成請求
- `create_synthesis_result()`: 創建合成結果
- `create_voice_model()`: 創建語音模型

## OOP 設計原則

### 單一職責原則 (SRP)
- 每個類別只負責特定的 TTS 功能
- 清晰的職責分離

### 開放封閉原則 (OCP)
- 支援新的語音模型
- 可擴展的合成流程

### 依賴反轉原則 (DIP)
- 依賴抽象介面而非具體實現
- 支援不同的語音引擎

### 介面隔離原則 (ISP)
- 精確的方法簽名
- 避免不必要的依賴

### 里氏替換原則 (LSP)
- 所有合成器都可以替換其基類
- 保持行為一致性

## 主要入口點

### main.py
- **職責**：FastAPI 應用程式入口
- **功能**：
  - 提供 RESTful API 端點
  - 整合 TTS 管道管理器
  - 語音合成服務控制
  - 健康檢查和語音資訊

### 使用方式
```python
# 創建 TTS 管道實例
from core.tts_pipeline_manager import TTSPipelineManager

pipeline = TTSPipelineManager()

# 語音合成
result = await pipeline.synthesize_speech(
    text="歡迎使用 Podwise 語音合成服務",
    voice="podrina",
    speed=1.0
)

# 獲取可用語音
voices = pipeline.get_available_voices()

# 清理快取
pipeline.clear_cache()
```

## 監控和健康檢查

### 健康檢查
- 檢查所有組件狀態
- 驗證語音模型可用性
- 監控合成性能
- 檢查快取狀態

### 性能指標
- 合成速度
- 音頻品質
- 快取命中率
- 錯誤率統計

## 技術棧

- **框架**：FastAPI
- **語音引擎**：OpenAI TTS, Azure Speech
- **音頻處理**：librosa, pydub
- **快取**：Redis
- **容器化**：Docker

## 部署

```bash
# 構建 Docker 映像
docker build -t podwise-tts-pipeline .

# 運行容器
docker run -p 8003:8003 podwise-tts-pipeline
```

## API 端點

- `GET /health` - 健康檢查
- `POST /api/v1/synthesize` - 語音合成
- `GET /api/v1/voices` - 獲取可用語音
- `POST /api/v1/cache/clear` - 清理快取
- `GET /api/v1/statistics` - 統計資訊

## 架構優勢

1. **高品質**：支援多種高品質語音模型
2. **可擴展性**：支援新的語音引擎和模型
3. **可維護性**：清晰的模組化設計
4. **可監控性**：完整的性能指標
5. **一致性**：統一的數據模型和介面設計 