# 🎵 MusicGen 音樂生成功能整合指南

## 📋 功能概述

本專案整合了 Meta 的 MusicGen 音樂生成功能到 Podri 聊天系統中，並新增了智能 API Key 管理功能。

### 🆕 新增功能

1. **API Key 管理**
   - OpenAI API Key 管理
   - Google Search API Key 管理
   - Gemini API Key 管理
   - Anthropic API Key 管理
   - 智能 API 選擇機制

2. **MusicGen 音樂生成**
   - 多種音樂風格（古典、流行、電子、民族、放鬆、激勵）
   - 可調整節奏（慢、中、快、極快）
   - 可設定音樂長度（5-30秒）
   - 支援多種 MusicGen 模型

## 🏗️ 架構設計

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Podri Chat    │    │   MusicGen      │    │   API Manager   │
│   (Streamlit)   │◄──►│   Service       │    │   (智能選擇)     │
│                 │    │   (FastAPI)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TTS/STT       │    │   MusicGen      │    │   OpenAI        │
│   Services      │    │   Models        │    │   Google        │
│                 │    │                 │    │   Gemini        │
└─────────────────┘    └─────────────────┘    │   Anthropic     │
                                              └─────────────────┘
```

## 🚀 部署方式

### 方式一：Kubernetes 部署（推薦）

```bash
# 1. 進入部署目錄
cd deploy/k8s/musicgen

# 2. 執行部署腳本
./build-and-deploy-musicgen.sh

# 3. 設定 port-forward 來存取服務
kubectl port-forward -n podwise svc/podri-chat-service 8501:8501

# 4. 開啟瀏覽器
# http://localhost:8501
```

### 方式二：Docker Compose 部署

```bash
# 1. 進入部署目錄
cd deploy/docker

# 2. 執行部署腳本
./deploy-musicgen.sh

# 3. 開啟瀏覽器
# http://localhost:8501
```

## 🔧 配置說明

### API Key 配置

在 Kubernetes 中，API Keys 透過 Secret 管理：

```bash
# 建立 API Keys Secret
kubectl create secret generic api-keys-secret \
    --from-literal=openai-api-key="your-openai-key" \
    --from-literal=google-search-api-key="your-google-key" \
    --from-literal=gemini-api-key="your-gemini-key" \
    --from-literal=anthropic-api-key="your-anthropic-key" \
    -n podwise
```

### MusicGen 配置

MusicGen 服務支援以下配置：

- **模型選擇**：melody, medium, small, large, long
- **音樂長度**：5-30秒（可調整）
- **生成參數**：top_k, top_p, temperature, classifier_free_guidance

## 📖 使用指南

### 1. API Key 管理

1. 開啟聊天介面
2. 在側邊欄找到「🔑 API Key 管理」
3. 輸入您的 API Keys
4. 點擊「🧪 測試 API 連接」驗證

### 2. 音樂生成

1. 在側邊欄找到「🎵 音樂生成」
2. 勾選「啟用音樂生成」
3. 選擇音樂風格和節奏
4. 調整音樂長度
5. 點擊「🎼 生成背景音樂」

### 3. 智能 API 選擇

系統會根據您的查詢內容自動選擇最適合的 API：

- **搜尋相關**：使用 Google Search API
- **程式碼相關**：使用 OpenAI 或 Anthropic API
- **一般對話**：優先使用 Anthropic，其次是 OpenAI

## 🛠️ 開發指南

### 本地開發

```bash
# 1. 安裝依賴
cd frontend/chat
pip install -r requirements.txt

# 2. 啟動 MusicGen 服務
cd ../../backend/musicgen
python app.py

# 3. 啟動聊天服務
cd ../../frontend/chat
# streamlit run podri_chat.py  # 已移除，不再使用
```

### 新增音樂風格

在 `musicgen_service.py` 中修改 `MusicPromptGenerator` 類別：

```python
self.music_styles = {
    "古典": ["classical", "orchestral", "symphony"],
    "流行": ["pop", "rock", "jazz"],
    # 新增您的風格
    "新風格": ["new_style_keywords"]
}
```

### 新增 API 支援

在 `api_key_manager.py` 中新增 API 類型：

```python
class APIType(Enum):
    OPENAI = "openai"
    GOOGLE_SEARCH = "google_search"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    # 新增您的 API
    NEW_API = "new_api"
```

## 🔍 故障排除

### 常見問題

1. **MusicGen 服務無法啟動**
   ```bash
   # 檢查 GPU 支援
   nvidia-smi
   
   # 查看日誌
   kubectl logs -n podwise deployment/musicgen-service
   ```

2. **API Key 無效**
   ```bash
   # 檢查 Secret 是否正確設定
   kubectl get secret api-keys-secret -n podwise -o yaml
   ```

3. **音樂生成失敗**
   ```bash
   # 檢查 MusicGen 服務狀態
   kubectl exec -n podwise deployment/musicgen-service -- curl http://localhost:8005/health
   ```

### 效能優化

1. **GPU 加速**：確保 MusicGen 服務使用 GPU
2. **記憶體配置**：根據模型大小調整記憶體限制
3. **快取策略**：使用 PersistentVolume 儲存模型快取

## 📊 監控與日誌

### 查看日誌

```bash
# MusicGen 服務日誌
kubectl logs -f deployment/musicgen-service -n podwise

# 聊天服務日誌
kubectl logs -f deployment/podri-chat-service -n podwise
```

### 監控指標

- MusicGen 服務響應時間
- 音樂生成成功率
- API 調用次數和成功率
- 系統資源使用率

## 🔒 安全性考量

1. **API Key 保護**：使用 Kubernetes Secret 儲存
2. **網路隔離**：使用 ClusterIP 服務類型
3. **資源限制**：設定 CPU 和記憶體限制
4. **存取控制**：使用 RBAC 控制存取權限

## 📈 未來規劃

1. **更多音樂模型**：支援更多 MusicGen 變體
2. **音樂編輯功能**：支援音樂後處理
3. **批次生成**：支援多首音樂同時生成
4. **音樂推薦**：基於用戶偏好推薦音樂風格
5. **整合更多 API**：支援更多 AI 服務

## 🤝 貢獻指南

1. Fork 專案
2. 建立功能分支
3. 提交變更
4. 建立 Pull Request

## 📄 授權

本專案採用 MIT 授權條款。 