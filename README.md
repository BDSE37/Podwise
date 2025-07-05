# Podwise - 智能播客推薦系統

Podwise 是一個基於 AI 的智能播客推薦系統，整合了多種先進的技術來提供個性化的播客推薦服務。

## 🚀 功能特色

- **智能推薦**: 基於圖神經網路 (GNN) 的混合推薦系統
- **多語言支援**: 支援繁體中文和英文
- **語音處理**: 整合 STT (語音轉文字) 和 TTS (文字轉語音)
- **RAG 系統**: 分層檢索增強生成系統
- **Kubernetes 部署**: 完整的容器化部署方案
- **台灣版本模型**: 整合 Qwen2.5-Taiwan-7B-Instruct 模型

## 🏗️ 系統架構

```
Podwise/
├── backend/           # 後端服務
│   ├── api/          # API 服務
│   ├── llm/          # 語言模型服務
│   ├── rag_pipeline/ # RAG 檢索系統
│   ├── ml_pipeline/  # 機器學習管道
│   ├── stt/          # 語音轉文字
│   └── tts/          # 文字轉語音
├── frontend/         # 前端介面
├── deploy/           # 部署配置
│   ├── k8s/         # Kubernetes 配置
│   └── docker/      # Docker 配置
└── data/            # 資料目錄
```

## 🛠️ 技術棧

- **後端**: Python, FastAPI, SQLAlchemy
- **前端**: HTML, CSS, JavaScript
- **AI/ML**: PyTorch, Transformers, LangChain
- **資料庫**: PostgreSQL, Milvus (向量資料庫)
- **容器化**: Docker, Kubernetes
- **監控**: Prometheus, Grafana

## 📦 快速開始

### 前置需求

- Docker 或 Podman
- Kubernetes 集群
- Python 3.8+

### 部署步驟

1. **克隆專案**
   ```bash
   git clone <repository-url>
   cd Podwise
   ```

2. **使用 Podman 部署**
   ```bash
   chmod +x deploy-podman.sh
   ./deploy-podman.sh
   ```

3. **使用 Kubernetes 部署**
   ```bash
   # 部署基礎服務
   kubectl apply -f deploy/k8s/
   
   # 推送模型到 Ollama
   ./deploy/k8s/ollama/push-models.sh
   ```

## 🤖 AI 模型

### 支援的模型

- **Qwen2.5-Taiwan-7B-Instruct**: 台灣版本語言模型
- **Qwen3-8B**: 通用語言模型
- **自定義模型**: 支援 GGUF 格式

### 模型轉換

如需將 HuggingFace 模型轉換為 GGUF 格式：

```bash
# 安裝轉換工具
pip install huggingface_hub sentencepiece

# 下載並轉換模型
python3 convert_hf_to_gguf.py <model_path> --outtype q8_0 --outfile <output.gguf>
```

## 🔧 配置

### 環境變數

創建 `.env` 檔案：

```env
# 資料庫配置
DATABASE_URL=postgresql://user:password@localhost:5432/podwise

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 模型配置
MODEL_PATH=/path/to/models
```

### Kubernetes 配置

修改 `deploy/k8s/` 目錄下的配置檔案以適應您的環境。

## 📊 監控

系統提供完整的監控解決方案：

- **Prometheus**: 指標收集
- **Grafana**: 視覺化儀表板
- **Langfuse**: AI 模型監控

## ⚠️ .env 檔案管理

- `.env` 僅供本地開發使用，**請勿上傳至 GitHub**。
- `.env` 已被 .gitignore 排除，確保敏感資訊不會外洩。
- 如需團隊協作，建議建立 `.env.example` 作為格式範本，不含真實密碼。

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

本專案採用 Apache 2.0 授權條款。

## 📞 支援

如有問題，請提交 Issue 或聯繫開發團隊。 