# Podwise - 智能語音助手系統

## 📋 系統概覽

Podwise 是一個整合了多種 AI 技術的智能語音助手系統，支援語音合成、語音識別、自然語言處理和職缺推薦等功能。

## ✨ 主要功能

### 🤖 AI 模型整合
- **向量模型**: BGE-M3 (1024維度)
- **LLM 模型**: Qwen3、Qwen2.5-Taiwan、Ollama、OpenAI
- **模型選擇**: 由 CrewAI + LangChain 代理人自動決策

### 🎙️ 語音功能
- **TTS (文字轉語音)**: 4種台灣語音
  - Podria (溫柔女聲)
  - Podlisa (活潑女聲) 
  - Podrick (穩重男聲)
- **STT (語音轉文字)**: 支援語音輸入和文字輸入

### 🔍 RAG 系統
- 智能檢索增強生成
- 向量搜索和語義搜索
- 職缺推薦系統

## 🏗️ 系統架構

### 後端服務模組
```
backend/
├── api/                    # API 服務 (端口: 8006)
├── config/                 # 配置服務 (端口: 8008)
├── core/                   # 核心服務 (端口: 8007)
├── llm/                    # LLM 服務 (端口: 8003)
├── ml_pipeline/            # ML Pipeline (端口: 8004)
├── rag_pipeline/           # RAG Pipeline (端口: 8004)
├── stt/                    # STT 服務 (端口: 8001)
├── tts/                    # TTS 服務 (端口: 8002)
└── utils/                  # 工具模組
```

### 前端模組
```
frontend/
├── assets/                 # 靜態資源
├── chat/                   # 聊天介面
└── images/                 # 圖片資源
```

## 🚀 快速開始

### 1. 環境要求
- Python 3.9+
- Docker/Podman
- Kubernetes (可選)

### 2. 安裝依賴
```bash
# 安裝 Python 依賴
pip install -r requirements.txt

# 安裝後端依賴
cd backend
pip install -r requirements.txt
```

### 3. 配置環境變數
```bash
# 複製環境變數模板
cp ENV_TEMPLATE.md .env

# 編輯 .env 檔案，填入實際配置
nano .env
```

### 4. 啟動服務
```bash
# 使用 Docker Compose
docker-compose up -d

# 或使用 Podman
podman-compose up -d
```

## 🔧 配置說明

### 向量模型配置
```python
# backend/rag_pipeline/config/integrated_config.py
bge_m3_dimension: int = 1024
embedding_dimension: int = 1024
```

### 模型選擇配置
```python
# 模型優先級配置
llm_priority: [
    "qwen3:8b",           # 主要 LLM
    "qwen3:taiwan",       # 台灣優化版本
    "qwen3:7b",           # 備用版本
    "deepseek:7b",        # 備用版本
    "llama3:8b"           # 最後備用
]
```

### TTS 語音配置
```python
# backend/tts/config/voice_config.py
edge_tts_voices = [
    {"id": "zh-TW-HsiaoChenNeural", "name": "Podria (溫柔女聲)"},
    {"id": "zh-TW-HsiaoYuNeural", "name": "Podlisa (活潑女聲)"},
    {"id": "zh-TW-YunJheNeural", "name": "Podrick (穩重男聲)"},
    {"id": "zh-TW-ZhiYuanNeural", "name": "Podvid (專業男聲)"}
]
```

## 🐳 Docker 部署

### 所有模組都有獨立的 Dockerfile

| 模組 | Dockerfile 位置 | 端口 |
|------|----------------|------|
| **TTS** | `backend/tts/Dockerfile` | 8501, 8002, 8003, 7860, 9880 |
| **STT** | `backend/stt/Dockerfile` | 8001 |
| **LLM** | `backend/llm/Dockerfile` | 8003 |
| **RAG Pipeline** | `backend/rag_pipeline/Dockerfile` | 8004 |
| **ML Pipeline** | `backend/ml_pipeline/Dockerfile` | 8004 |
| **API** | `backend/api/Dockerfile` | 8006 |
| **Config** | `backend/config/Dockerfile` | 8008 |
| **Core** | `backend/core/Dockerfile` | 8007 |

### 構建映像
```bash
# 構建所有服務映像
./build-and-push-podman.sh

# 或個別構建
cd backend/tts && podman build -t podwise-tts .
cd backend/stt && podman build -t podwise-stt .
cd backend/rag_pipeline && podman build -t podwise-rag .
```

## 📊 系統狀態檢查

### 配置驗證
```bash
# 檢查系統配置
python backend/rag_pipeline/config/integrated_config.py
```

### 預期輸出
```
🔧 Podwise 整合配置摘要
============================================================
環境：development
除錯模式：True
日誌等級：INFO

🤖 模型配置：
  主要 LLM：qwen3:8b
  台灣優化：qwen3:taiwan
  向量模型：BAAI/bge-m3
  向量維度：1024

📋 API 配置狀態：
  OpenAI：✅
  Anthropic：✅
  Google AI：✅
  Supabase：✅

🗄️ 資料庫配置狀態：
  MongoDB：✅
  PostgreSQL：✅
  Redis：✅
  Milvus：✅

🔍 追蹤配置狀態：
  Langfuse：✅
  思考過程追蹤：✅
  模型選擇追蹤：✅
  代理互動追蹤：✅

🚀 功能配置：
  雙代理機制：✅
  職缺推薦：✅
  向量搜索：✅
  混合搜索：✅
  語義搜索：✅

🔐 安全配置狀態：
  Secret Key：✅
  JWT Secret：✅
```

## 🔗 服務連接

### 內部服務連接
```yaml
rag_pipeline_host: "localhost"
rag_pipeline_port: 8002
tts_host: "localhost" 
tts_port: 8002
stt_host: "localhost"
stt_port: 8003
llm_host: "localhost"
llm_port: 8004
```

### 外部服務連接
```yaml
mongodb_uri: "mongodb://worker3:27017/podwise"
postgres_host: "worker3"
redis_host: "worker3"
milvus_host: "worker3"
ollama_host: "http://localhost:11434"
```

## 📚 文檔

- [系統檢查報告](SYSTEM_CHECK_REPORT.md)
- [GitHub 上傳指南](GITHUB_UPLOAD_GUIDE.md)
- [環境變數配置](ENV_TEMPLATE.md)
- [部署文檔](docs/DEPLOYMENT.md)
- [快速開始指南](docs/QUICK_START.md)

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

本專案採用 MIT 授權條款。

## ⚠️ 注意事項

1. **安全性**: 請妥善保管 API 金鑰和密碼
2. **模型檔案**: 大型模型檔案不會上傳到 Git
3. **環境配置**: 請根據實際環境調整配置
4. **資源需求**: 建議使用 GPU 以獲得更好的性能 