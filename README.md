# 📡 Podwise: 模組化 Podcast 智慧推薦系統

Podwise 是一個基於語音互動與語義理解的 Podcast 智慧推薦系統，融合 RAG 架構、向量檢索、協同過濾推薦與語音合成等功能，支援完整 MLOps 工作流程並以 Kubernetes 架構部署，具備高度模組化、可擴充性與可維護性。

---

## 🔧 系統特色 Features

- 🎙️ **語音互動介面**：整合 Whisper STT + Breeze2 / Qwen2.5-TW TTS，支援多語系語音輸入與輸出。
- 🧠 **RAG-based 問答系統**：使用 Milvus 向量檢索 + Qwen LLM 完成精準知識問答。
- 🎧 **Podcast 智慧推薦引擎**：
  - 協同過濾推薦（Collaborative Filtering）
  - 語意嵌入推薦（Embedding-based Recommendation）
- 🧱 **模組化設計**：每個模組皆可獨立開發與部署，降低耦合度。
- 🛠️ **MLOps 整合**：包含 Dagster 工作排程、n8n 自動化流程、GitLab CI/CD、Prometheus + Grafana 監控。
- ☁️ **Kubernetes 部署**：支援多節點部署、GPU 推論、Podman 容器化。

---

## 🧩 系統模組架構

frontend/
├── index.html # Podri 聊天入口頁
└── chat/ # Streamlit 語音互動 UI

backend/
├── app.py # FastAPI 入口
├── asr/ # Whisper STT 模組
├── tts/ # Breeze2 / Qwen TTS 模組
├── rag_pipeline/ # RAG 問答流程（Ollama, LangChain, Milvus）
├── ml_pipeline/ # 推薦模型訓練與推論
├── config/ # 模組初始化與參數設定
└── websocket/ # 語音串流與即時對話管理

data/
├── crawl/ # Apple/Spotify 資料爬蟲
├── storage/ # 音檔與 transcript 儲存
└── ingestion/ # PostgreSQL, MinIO, Milvus 轉存邏輯

deploy/
├── kubernetes/ # 各服務部署 YAML
├── docker-compose.yml # 簡化測試部署
└── environments/ # dev / prod configmap

yaml
複製
編輯

---

## 🚀 快速開始 Quick Start

### 1. Clone 專案

```bash
git clone https://github.com/your-org/Podwise.git
cd Podwise
2. 建立 .env
bash
複製
編輯
cp .env.example .env
並填入以下環境參數：

dotenv
複製
編輯
POSTGRES_HOST=xxx
MINIO_ENDPOINT=xxx
MILVUS_HOST=xxx
OLLAMA_BASE_URL=http://localhost:11434
...
3. 使用 Docker Compose 快速部署
bash
複製
編輯
podman-compose up --build
📊 系統部署架構圖
mermaid
複製
編輯
graph TD
  subgraph User
    A1[🎧 使用者語音]
    A2[🖱️ 網頁互動]
  end

  subgraph Frontend
    B1[Streamlit / index.html]
  end

  subgraph FastAPI Backend
    C1[📥 /ask 問答 API]
    C2[🔊 /speak TTS API]
    C3[🧠 RAG 檢索]
    C4[🗣️ STT 模組]
    C5[🗣️ TTS 模組]
  end

  subgraph AI Modules
    D1[LangChain]
    D2[Ollama + Qwen2.5-TW]
    D3[BGE Embedding]
    D4[Milvus 向量 DB]
    D5[PostgreSQL]
    D6[MinIO 音檔儲存]
    D7[MongoDB Transcript]
  end

  A1 --> B1 --> C1
  A2 --> B1 --> C2
  C1 --> C3 --> D4 --> D2
  C2 --> C5 --> D6
  C1 --> C4 --> D6
👥 組員分工 Roles & Responsibilities
姓名	工作內容
張書婷	系統建置、程式開發撰寫、TTS 實作開發、特徵工程、專案整合、RAG 實作評估、專案版本控管
謝理心	RAG Prompt 設計、資料庫設計與建置、資料清整與處理、特徵工程
焦亞妗	前端頁面設計、TTS 實作、資料清整與處理、特徵工程
黃品茹	RAG Prompt 設計、資料清整與處理、特徵工程
揭芷羽	爬蟲開發、n8n 自動化流程設計、資料清整與處理、特徵工程
藍昱昕	爬蟲開發、n8n 自動化流程設計、資料清整與處理、特徵工程

📝 授權 License
本專案使用 MIT License，詳見 LICENSE 檔案。
