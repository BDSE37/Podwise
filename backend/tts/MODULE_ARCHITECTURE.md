# TTS 模組架構說明

## 🏗️ 模組職責分工

### 1. 主要服務層 (Service Layer)

#### `main.py` - FastAPI 應用入口
- **職責**: HTTP API 服務入口點
- **OOP 原則**: 
  - 單一職責原則：只負責 HTTP 路由和請求處理
  - 依賴注入：通過 TTSService 實例處理業務邏輯
- **功能**:
  - RESTful API 端點定義
  - 請求/回應模型驗證
  - 錯誤處理和日誌記錄
  - CORS 配置

#### `tts_service.py` - TTS 服務核心
- **職責**: 統一的 TTS 服務介面
- **OOP 原則**:
  - 單一職責原則：提供統一的語音合成介面
  - 開放封閉原則：支援擴展新的 TTS 提供者
  - 依賴反轉原則：依賴抽象而非具體實現
- **功能**:
  - 語音合成統一介面
  - 語音配置管理
  - 服務狀態監控
  - 音頻文件處理

### 2. 配置管理層 (Configuration Layer)

#### `config/voice_config.py` - 語音配置管理
- **職責**: 語音配置的統一管理
- **OOP 原則**:
  - 單一職責原則：只負責語音配置管理
  - 封裝原則：隱藏配置實現細節
- **功能**:
  - 語音配置定義和驗證
  - 語音查詢和篩選
  - 配置統計信息

#### `constants/constants.py` - 系統常數
- **職責**: 定義系統級常數
- **OOP 原則**:
  - 單一職責原則：只定義常數
  - 不可變性：常數不應被修改
- **功能**:
  - 音訊配置常數
  - 系統參數定義

### 3. 提供者層 (Provider Layer)

#### `providers/edge_tts_provider.py` - Edge TTS 提供者
- **職責**: Microsoft Edge TTS 的具體實現
- **OOP 原則**:
  - 單一職責原則：只負責 Edge TTS 功能
  - 開放封閉原則：支援擴展新的語音
  - 里氏替換原則：可替換為其他 TTS 提供者
- **功能**:
  - Edge TTS 語音合成
  - 語音參數處理
  - 音頻格式轉換

### 4. 工具層 (Utility Layer)

#### `utils/logging_config.py` - 日誌配置
- **職責**: 統一的日誌配置管理
- **OOP 原則**:
  - 單一職責原則：只負責日誌配置
  - 工廠模式：提供統一的 logger 創建介面
- **功能**:
  - 日誌格式配置
  - 顏色輸出支援
  - 日誌級別管理

### 5. 測試層 (Test Layer)

#### `test_edge_tts_connection.py` - 連接測試
- **職責**: Edge TTS 功能測試
- **OOP 原則**:
  - 單一職責原則：只負責測試功能
  - 測試隔離：每個測試獨立執行
- **功能**:
  - Edge TTS 連接測試
  - 語音合成功能測試
  - 提供者初始化測試

## 🔄 模組間依賴關係

```
main.py
├── tts_service.py
│   ├── providers/edge_tts_provider.py
│   ├── config/voice_config.py
│   └── utils/logging_config.py
└── constants/constants.py
```

## 📋 唯一性保證

### 1. 檔案唯一性
- ✅ 已刪除重複的測試檔案 (`test_tts.py`)
- ✅ 已刪除隱藏檔案 (`.DS_Store`, `.__*`)
- ✅ 每個模組只有一個主要實現檔案

### 2. 功能唯一性
- ✅ `main.py`: 唯一的 HTTP API 入口
- ✅ `tts_service.py`: 唯一的 TTS 服務介面
- ✅ `voice_config.py`: 唯一的語音配置管理
- ✅ `edge_tts_provider.py`: 唯一的 Edge TTS 實現
- ✅ `logging_config.py`: 唯一的日誌配置

### 3. 類別唯一性
- ✅ `TTSService`: 唯一的 TTS 服務類別
- ✅ `VoiceConfig`: 唯一的語音配置類別
- ✅ `EdgeTTSProvider`: 唯一的 Edge TTS 提供者類別
- ✅ `EdgeTTSManager`: 唯一的 Edge TTS 管理器類別
- ✅ `EdgeTTSVoice`: 唯一的語音配置數據類別

## 🎯 OOP 原則遵循

### 1. 單一職責原則 (SRP)
- 每個類別只負責一個明確的功能
- 每個模組只處理相關的業務邏輯

### 2. 開放封閉原則 (OCP)
- 支援新增 TTS 提供者而不修改現有代碼
- 支援新增語音配置而不影響現有功能

### 3. 里氏替換原則 (LSP)
- 不同的 TTS 提供者可以互相替換
- 語音配置可以動態切換

### 4. 介面隔離原則 (ISP)
- 每個介面只包含必要的方法
- 避免過大的介面定義

### 5. 依賴反轉原則 (DIP)
- 高層模組不依賴低層模組
- 依賴抽象而非具體實現

## 🔧 擴展性設計

### 1. 新增 TTS 提供者
```python
# 新增 providers/new_tts_provider.py
class NewTTSProvider:
    async def synthesize(self, text: str, **kwargs) -> Optional[bytes]:
        # 實現新的 TTS 功能
        pass
```

### 2. 新增語音配置
```python
# 在 voice_config.py 中新增語音
{
    "id": "new_voice",
    "name": "New Voice",
    "voice_id": "new-voice-id",
    "description": "新的語音描述"
}
```

### 3. 新增 API 端點
```python
# 在 main.py 中新增端點
@app.get("/new-endpoint")
async def new_endpoint():
    # 實現新的 API 功能
    pass
```

## 📊 代碼品質指標

- **模組化程度**: 高 (每個模組職責明確)
- **耦合度**: 低 (模組間依賴最小化)
- **內聚度**: 高 (每個模組功能集中)
- **可測試性**: 高 (每個模組可獨立測試)
- **可維護性**: 高 (清晰的架構和文檔)
- **可擴展性**: 高 (支援新功能擴展) 