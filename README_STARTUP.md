# Podwise 全棧啟動指南

本指南將幫助您啟動 Podwise 的完整前後端服務。

## 🚀 快速開始

### 1. 安裝依賴

首先安裝所有必要的 Python 依賴：

```bash
# 方法 1: 使用安裝腳本（推薦）
python install_dependencies.py

# 方法 2: 直接安裝
pip install -r requirements_podwise.txt
```

### 2. 選擇啟動方式

我們提供了三種啟動腳本：

#### 方式一：穩健啟動（推薦）
啟動所有服務，即使某些服務失敗也會繼續啟動其他服務：

```bash
python start_podwise_robust.py
```

#### 方式二：完整啟動
啟動所有服務，包括所有微服務：

```bash
python start_podwise_fullstack.py
```

#### 方式三：簡化啟動
只啟動核心的前後端服務：

```bash
python start_podwise_simple.py
```

## 📊 服務架構

### 核心服務
- **前端服務** (端口: 8000) - FastAPI + HTML 界面
- **後端 RAG Pipeline** (端口: 8005) - 智能問答和推薦系統

### 微服務
- **TTS 服務** (端口: 8002) - 文字轉語音
- **STT 服務** (端口: 8003) - 語音轉文字
- **LLM 服務** (端口: 8004) - 大語言模型
- **ML Pipeline** (端口: 8006) - 機器學習推薦
- **統一 API 網關** (端口: 8008) - API 統一管理

## 🌐 訪問地址

啟動成功後，您可以訪問以下地址：

- **📱 前端界面**: http://localhost:8000
- **🔧 後端 API**: http://localhost:8005
- **📖 API 文檔**: http://localhost:8005/docs
- **🎵 TTS 服務**: http://localhost:8002
- **🎤 STT 服務**: http://localhost:8003
- **🧠 LLM 服務**: http://localhost:8004
- **📊 ML Pipeline**: http://localhost:8006
- **🌐 API 網關**: http://localhost:8008

## ⚠️ 注意事項

### 端口衝突
如果遇到端口被佔用的錯誤，腳本會自動嘗試終止佔用端口的進程。

### 服務啟動順序
服務會按照以下順序啟動：
1. LLM 服務
2. TTS 服務
3. STT 服務
4. ML Pipeline 服務
5. 後端 RAG Pipeline 服務
6. 統一 API 網關
7. 前端服務

### 啟動時間
- 核心服務：約 30-60 秒
- 完整服務：約 2-5 分鐘
- 首次啟動可能需要更長時間（下載模型等）

## 🔧 故障排除

### 常見問題

1. **端口被佔用**
   ```bash
   # 查看端口佔用
   lsof -i :8000
   # 終止進程
   kill -9 <PID>
   ```

2. **依賴安裝失敗**
   ```bash
   # 升級 pip
   pip install --upgrade pip
   # 重新安裝
   python install_dependencies.py
   ```

3. **服務啟動失敗**
   - 檢查日誌輸出
   - 確認 Python 版本 >= 3.8
   - 確認所有依賴已安裝

### 日誌查看
啟動腳本會顯示詳細的日誌信息，包括：
- 服務啟動狀態
- 錯誤信息
- 訪問地址

## 🛑 停止服務

使用 `Ctrl+C` 停止所有服務，腳本會自動清理所有進程。

## 📝 開發模式

### 單獨啟動服務
如果您只想啟動特定服務進行開發：

```bash
# 啟動後端 RAG Pipeline
cd backend/rag_pipeline
uvicorn main:app --host 0.0.0.0 --port 8005 --reload

# 啟動前端
cd frontend
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

### 環境變數
創建 `.env` 文件來配置環境變數：

```env
# 數據庫配置
DATABASE_URL=postgresql://podwise_user:podwise_password@localhost:5432/podwise

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

## 🎯 功能測試

啟動完成後，您可以：

1. **訪問前端界面**: http://localhost:8000
2. **測試聊天功能**: 在 Podri 頁面進行對話
3. **查看 API 文檔**: http://localhost:8005/docs
4. **測試 TTS**: 使用語音合成功能

## 📞 支援

如果遇到問題，請：
1. 查看啟動日誌
2. 檢查服務狀態
3. 確認依賴版本
4. 查看錯誤信息

---

**祝您使用愉快！** 🎉 