# Podwise RAG Pipeline 問題修復指南

## 問題概述

您遇到的兩個主要問題：

1. **向量維度不匹配錯誤**
   - 錯誤：`vector dimension mismatch, expected vector size(byte) 4096, actual 6144`
   - 原因：系統配置使用 1024 維向量，但實際生成的是 1536 維向量

2. **LLM 模型不存在錯誤**
   - 錯誤：`The model 'qwen2.5-taiwan-7b-instruct' does not exist`
   - 原因：Ollama 服務中缺少必要的模型

## 修復方案

### 1. 向量維度問題修復

#### 已修復的代碼
- `backend/rag_pipeline/tools/enhanced_podcast_recommender.py`
  - 改進嵌入向量生成邏輯
  - 自動處理不同維度的向量
  - 優先使用 BGE-M3 (1024維) 模型

#### 環境變數配置
- `backend/rag_pipeline/env.local`
  - 添加向量嵌入配置
  - 設定正確的維度參數

### 2. LLM 模型問題修復

#### 已修復的代碼
- 改進 LLM 客戶端初始化
- 添加多模型 Fallback 機制
- 修復模型名稱映射

#### 模型下載腳本
- `backend/rag_pipeline/scripts/fix_ollama_models.sh` (本地版本)
- `backend/rag_pipeline/scripts/fix_k8s_ollama_models.sh` (Kubernetes 版本)

## 快速修復步驟

### 方法 1: 使用修復腳本 (推薦)

#### 本地環境
```bash
cd backend/rag_pipeline/scripts
./fix_ollama_models.sh
```

#### Kubernetes 環境
```bash
cd backend/rag_pipeline/scripts
./fix_k8s_ollama_models.sh
```

### 方法 2: 手動修復

#### 1. 檢查 Ollama 服務
```bash
# 本地
curl http://localhost:11434/api/tags

# Kubernetes
kubectl exec -n podwise <ollama-pod> -- curl http://localhost:11434/api/tags
```

#### 2. 下載必要模型
```bash
# 嵌入模型 (解決向量維度問題)
ollama pull BAAI/bge-m3          # 1024維
ollama pull nomic-embed-text     # 備用
ollama pull all-minilm           # 備用

# LLM 模型 (解決模型不存在問題)
ollama pull weiren119/Qwen2.5-Taiwan-8B-Instruct
ollama pull Qwen/Qwen2.5-8B-Instruct
ollama pull qwen2.5:8b
ollama pull gpt-3.5-turbo
```

#### 3. 驗證修復
```bash
# 檢查模型列表
ollama list

# 測試台灣版本模型
ollama run qwen2.5-taiwan-7b-instruct "你好"

# 測試嵌入模型
curl -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "bge-m3", "prompt": "測試"}' | jq '.embedding | length'
```

## 檢查腳本

使用檢查腳本來診斷問題：

```bash
cd backend/rag_pipeline/scripts
python check_ollama_models.py
```

這個腳本會：
- 檢查 Ollama 服務狀態
- 驗證所有必要模型
- 測試模型功能
- 提供修復建議

## 配置說明

### 環境變數
```bash
# 向量嵌入配置
EMBEDDING_MODEL=bge-m3
EMBEDDING_DIMENSION=1024
EMBEDDING_DEVICE=cpu

# Ollama 配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-taiwan-7b-instruct
```

### 模型優先級
1. **嵌入模型**：BGE-M3 (1024維) → Nomic → All-MiniLM
2. **LLM 模型**：台灣版本 → Qwen2.5 → Qwen3 → GPT-3.5

## 故障排除

### 常見問題

#### 1. Ollama 服務無法連接
```bash
# 檢查服務狀態
systemctl status ollama

# 重啟服務
sudo systemctl restart ollama
```

#### 2. 模型下載失敗
```bash
# 檢查網路連接
ping ollama.ai

# 使用代理 (如果需要)
export https_proxy=http://proxy:port
export http_proxy=http://proxy:port
```

#### 3. 向量維度仍然不匹配
```bash
# 檢查 Milvus 集合配置
# 確保集合使用 1024 維度
```

### 日誌檢查
```bash
# 檢查 RAG Pipeline 日誌
tail -f backend/rag_pipeline/logs/rag_pipeline.log

# 檢查 Ollama 日誌
journalctl -u ollama -f
```

## 驗證修復

修復完成後，運行以下測試：

```bash
# 1. 檢查模型狀態
python backend/rag_pipeline/scripts/check_ollama_models.py

# 2. 測試 RAG Pipeline
cd backend/rag_pipeline
python -m pytest tests/ -v

# 3. 測試推薦功能
python -c "
import asyncio
from tools.enhanced_podcast_recommender import test_enhanced_recommender
asyncio.run(test_enhanced_recommender())
"
```

## 聯繫支援

如果問題仍然存在，請提供：
1. 完整的錯誤日誌
2. Ollama 模型列表 (`ollama list`)
3. 環境變數配置
4. 系統環境資訊

---

**修復完成後，您的 RAG Pipeline 應該能夠正常運行，不再出現向量維度不匹配和 LLM 模型不存在的錯誤。** 