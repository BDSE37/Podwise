# 🚀 Podwise 快速啟動指南

## 📋 概述

Podwise 是一個完整的播客推薦系統，包含前端和後端多個服務。現在您可以使用統一的啟動腳本來一鍵啟動整個專案！

## 🎯 一鍵啟動

### 啟動所有服務
```bash
./start_podwise.sh start
```

### 檢查服務狀態
```bash
./start_podwise.sh status
```

### 停止所有服務
```bash
./start_podwise.sh stop
```

### 重新啟動所有服務
```bash
./start_podwise.sh restart
```

### 查看服務日誌
```bash
./start_podwise.sh logs frontend      # 查看前端日誌
./start_podwise.sh logs api_gateway   # 查看 API Gateway 日誌
./start_podwise.sh logs tts           # 查看 TTS 服務日誌
```

## 🌐 服務訪問地址

### 前端服務 (端口 8081)
- **主頁面**: http://localhost:8081/
- **聊天頁面**: http://localhost:8081/podri.html
- **登入頁面**: http://localhost:8081/login.html
- **健康檢查**: http://localhost:8081/health

### 統一 API Gateway (端口 8008)
- **主頁面**: http://localhost:8008/
- **聊天頁面**: http://localhost:8008/podri.html
- **API 文檔**: http://localhost:8008/docs
- **健康檢查**: http://localhost:8008/health

### 各後端服務
- **TTS 服務**: http://localhost:8002
- **STT 服務**: http://localhost:8003
- **ML Pipeline**: http://localhost:8004
- **RAG Pipeline**: http://localhost:8005
- **LLM 服務**: http://localhost:8006

## 🔧 服務說明

### 前端服務
- 提供用戶界面
- 包含 onboarding 流程
- 聊天功能
- 音頻播放

### 後端服務
- **TTS**: 文字轉語音
- **STT**: 語音轉文字
- **RAG Pipeline**: 檢索增強生成
- **ML Pipeline**: 機器學習推薦
- **LLM**: 語言模型服務
- **API Gateway**: 統一 API 入口

## 📊 啟動流程

1. **環境檢查**: 檢查 Python 版本和依賴
2. **目錄檢查**: 確認專案結構完整
3. **依賴安裝**: 自動安裝缺少的 Python 包
4. **環境設定**: 設定服務端口和配置
5. **後端啟動**: 啟動所有後端服務
6. **前端啟動**: 啟動前端服務
7. **狀態顯示**: 顯示所有服務的訪問地址

## 🛠️ 故障排除

### 端口被佔用
如果某個端口被佔用，腳本會跳過該服務並繼續啟動其他服務。

### 服務啟動失敗
檢查日誌文件：
```bash
./start_podwise.sh logs [service_name]
```

### 依賴問題
腳本會自動檢查並安裝缺少的依賴，如果仍有問題，請手動安裝：
```bash
pip3 install fastapi uvicorn httpx
```

## 📝 日誌文件

所有服務的日誌都保存在 `logs/` 目錄下：
- `logs/frontend.log` - 前端服務日誌
- `logs/api_gateway.log` - API Gateway 日誌
- `logs/tts.log` - TTS 服務日誌
- `logs/stt.log` - STT 服務日誌
- `logs/rag_pipeline.log` - RAG Pipeline 日誌
- `logs/ml_pipeline.log` - ML Pipeline 日誌
- `logs/llm.log` - LLM 服務日誌

## 🔄 開發模式

如果您需要單獨啟動某個服務進行開發：

### 只啟動前端
```bash
cd frontend
python3 fastapi_app.py
```

### 只啟動 API Gateway
```bash
cd backend
python3 unified_api_gateway.py
```

### 只啟動特定後端服務
```bash
cd backend/[service_name]
python3 main.py
```

## 📋 系統要求

- **Python**: 3.8+
- **作業系統**: Linux/macOS/Windows (WSL)
- **記憶體**: 建議 4GB+
- **磁碟空間**: 建議 2GB+

## 🎉 開始使用

1. 確保您在專案根目錄
2. 執行啟動命令：
   ```bash
   ./start_podwise.sh start
   ```
3. 等待所有服務啟動完成
4. 在瀏覽器中訪問 http://localhost:8081/
5. 開始使用 Podwise！

---

**享受您的 Podwise 體驗！** 🎵📚 