# Podri Chat 模組架構說明

## 概述

Podri Chat 採用 OOP（物件導向程式設計）模組化架構，將原本單一的 `podri_chat.py` 檔案重構為多個獨立模組，提升程式碼的可維護性、可測試性和可擴展性。

## 模組架構

```
Podwise/frontend/chat/
├── podri_chat.py              # 原始檔案（保留）
├── podri_chat_simple.py       # 簡化版本（推薦使用）
├── podri_chat_new.py          # 新版本（完整 OOP）
├── run_simple_chat.sh         # 執行腳本
├── requirements.txt           # 依賴套件
├── ARCHITECTURE.md           # 架構說明
├── ui/                       # UI 介面模組
│   ├── __init__.py
│   ├── chat_interface.py     # 聊天介面
│   ├── sidebar_interface.py  # 側邊欄介面
│   ├── voice_interface.py    # 語音介面
│   └── main_interface.py     # 主介面整合
├── services/                 # 服務模組
│   ├── tts_service.py        # TTS 語音合成服務
│   ├── rag_service.py        # RAG 知識檢索服務
│   ├── minio_audio_service.py
│   ├── intelligent_audio_search.py
│   ├── service_manager.py
│   ├── intelligent_processor.py
│   └── voice_recorder.py
├── core/                     # 核心模組
│   ├── __init__.py
│   ├── podri_controller.py   # 主控制器
│   ├── session_manager.py    # 會話管理
│   └── message_handler.py    # 訊息處理
└── utils/                    # 工具模組
    ├── api_key_manager.py    # API Key 管理
    └── env_config.py         # 環境配置
```

## 模組說明

### 1. UI 介面模組 (`ui/`)

#### `chat_interface.py`
- **功能**：處理聊天對話相關的 UI 功能
- **主要類別**：`ChatInterface`
- **職責**：
  - 渲染聊天訊息氣泡
  - 處理輸入區域
  - 顯示聊天歷史
  - 顯示使用統計

#### `sidebar_interface.py`
- **功能**：處理側邊欄相關的 UI 功能
- **主要類別**：`SidebarInterface`
- **職責**：
  - API Key 管理介面
  - 服務狀態顯示
  - 熱門推薦
  - 每日聲音小卡

#### `voice_interface.py`
- **功能**：處理語音相關的 UI 功能
- **主要類別**：`VoiceInterface`
- **職責**：
  - 語音設定介面
  - 語音選項管理
  - 語音試聽功能
  - 語音參數調整

#### `main_interface.py`
- **功能**：整合所有 UI 介面
- **主要類別**：`MainInterface`
- **職責**：
  - 統一介面管理
  - 三欄式佈局
  - 頁面配置
  - 樣式管理

### 2. 服務模組 (`services/`)

#### `tts_service.py`
- **功能**：TTS 語音合成服務
- **主要類別**：`TTSService`
- **職責**：
  - 語音生成
  - 語音列表管理
  - 服務狀態檢查
  - 語音資訊管理

#### `rag_service.py`
- **功能**：RAG 知識檢索服務
- **主要類別**：`RAGService`
- **職責**：
  - 訊息處理
  - 文件搜尋
  - 聊天歷史管理
  - 服務狀態檢查

### 3. 核心模組 (`core/`)

#### `podri_controller.py`
- **功能**：主控制器，整合所有服務和介面
- **主要類別**：`PodriController`
- **職責**：
  - 應用程式初始化
  - 會話狀態管理
  - 訊息處理流程
  - 服務整合

### 4. 工具模組 (`utils/`)

#### `api_key_manager.py`
- **功能**：API Key 管理
- **主要類別**：`APIKeyManager`
- **職責**：
  - API Key 儲存
  - API 狀態檢查
  - 最佳 API 選擇

## 使用方式

### 1. 簡化版本（推薦）

```bash
# 執行簡化版本
./run_simple_chat.sh

# 或直接執行
streamlit run podri_chat_simple.py
```

### 2. 完整 OOP 版本

```bash
# 執行完整版本
streamlit run podri_chat_new.py
```

### 3. 原始版本

```bash
# 執行原始版本
streamlit run podri_chat.py
```

## 優勢

### 1. 可維護性
- **模組化設計**：每個模組負責特定功能，易於理解和修改
- **清晰的職責分離**：UI、服務、核心邏輯分離
- **統一的程式碼風格**：遵循 Google Python Style Guide

### 2. 可測試性
- **獨立模組**：每個模組可以獨立測試
- **Mock 支援**：可以輕鬆模擬外部依賴
- **單元測試**：可以為每個類別編寫單元測試

### 3. 可擴展性
- **插件式架構**：可以輕鬆添加新的服務或介面
- **配置驅動**：透過配置檔案管理設定
- **版本控制**：可以同時維護多個版本

### 4. 開發效率
- **重用性**：模組可以在不同專案中重用
- **並行開發**：不同開發者可以同時開發不同模組
- **文檔化**：每個模組都有清晰的文檔說明

## 遷移指南

### 從原始版本遷移

1. **備份原始檔案**：
   ```bash
   cp podri_chat.py podri_chat_backup.py
   ```

2. **選擇版本**：
   - 簡單功能：使用 `podri_chat_simple.py`
   - 完整功能：使用 `podri_chat_new.py`

3. **更新依賴**：
   ```bash
   pip install -r requirements.txt
   ```

4. **測試功能**：
   ```bash
   streamlit run podri_chat_simple.py
   ```

## 未來發展

### 1. 計劃中的功能
- [ ] 完整的單元測試套件
- [ ] 自動化部署腳本
- [ ] 監控和日誌系統
- [ ] 多語言支援

### 2. 架構優化
- [ ] 微服務架構
- [ ] 容器化部署
- [ ] 負載平衡
- [ ] 快取機制

### 3. 使用者體驗
- [ ] 響應式設計
- [ ] 無障礙功能
- [ ] 主題切換
- [ ] 個人化設定

## 貢獻指南

### 1. 程式碼規範
- 遵循 Google Python Style Guide
- 使用繁體中文註解
- 完整的型別提示
- 詳細的文檔字串

### 2. 提交規範
- 清晰的提交訊息
- 單一職責原則
- 完整的測試覆蓋
- 文檔更新

### 3. 審查流程
- 程式碼審查
- 功能測試
- 效能測試
- 安全性檢查

## 聯絡資訊

如有問題或建議，請聯繫開發團隊或提交 Issue。 