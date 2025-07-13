# Podwise TTS 整合功能實現總結

## 🎯 實現目標

根據您的需求，我們成功實現了以下功能：

### ✅ 已完成功能

1. **RAG Pipeline TTS 整合**
   - 在 `backend/rag_pipeline/main.py` 中整合了 TTS 服務
   - 添加了 `synthesize_speech` 方法來處理語音合成
   - 支援語音類型和語速調整

2. **前端 TTS 控制項**
   - 在 `frontend/home/podri.html` 中添加了 TTS 控制項
   - 語音開關：`<input type="checkbox" id="tts-toggle" checked>`
   - 語音選擇：支援 Podrina (溫柔女聲)、Podrisa (活潑女聲)、Podrino (穩重男聲)
   - 語速調整：0.5x 到 1.5x 的語速範圍

3. **API 端點擴展**
   - 擴展了 `/api/v1/query` 端點以支援 TTS 參數
   - 新增了 `/api/v1/tts/synthesize` 專用 TTS 端點
   - 新增了 `/api/v1/tts/voices` 語音列表端點

4. **前端 JavaScript 功能**
   - 實現了聊天功能，支援 Enter 鍵發送訊息
   - 自動播放 TTS 語音回應
   - 支援語音開關控制（關閉時停止播放）
   - 載入狀態顯示和錯誤處理

## 🏗️ 技術架構

### 後端架構

```
RAG Pipeline (main.py)
    ↓ 整合
TTS Service (tts_service.py)
    ↓ 語音合成
Edge TTS Provider
    ↓ 音頻數據
Base64 編碼回應
```

### 前端架構

```
podri.html
    ↓ HTTP 請求
RAG Pipeline API
    ↓ 語音合成
TTS 回應 (包含音頻數據)
    ↓ 前端播放
瀏覽器音頻播放
```

## 📋 實現細節

### 1. RAG Pipeline 整合

**檔案**: `backend/rag_pipeline/main.py`

- 添加了 TTS 服務導入和初始化
- 實現了 `synthesize_speech` 方法
- 修改了 `process_query` 端點以支援 TTS 參數
- 添加了 TTS 專用 API 端點

### 2. API 模型擴展

**檔案**: `backend/rag_pipeline/core/api_models.py`

- 擴展了 `UserQueryRequest` 模型：
  - `enable_tts`: 是否啟用 TTS (預設 true)
  - `voice`: 語音 ID (預設 "podrina")
  - `speed`: 語速倍數 (預設 1.0)

- 擴展了 `UserQueryResponse` 模型：
  - `audio_data`: Base64 編碼的音頻數據
  - `voice_used`: 使用的語音 ID
  - `speed_used`: 使用的語速
  - `tts_enabled`: 是否啟用了 TTS

- 新增了 TTS 專用模型：
  - `TTSRequest`: TTS 語音合成請求
  - `TTSResponse`: TTS 語音合成回應

### 3. 前端界面

**檔案**: `frontend/home/podri.html`

#### TTS 控制項
```html
<!-- 語音開關 -->
<input class="checkbox" type="checkbox" id="tts-toggle" checked>

<!-- 語音選擇 -->
<select id="voice-select">
    <option value="podrina" selected>Podrina (溫柔女聲)</option>
    <option value="podrisa">Podrisa (活潑女聲)</option>
    <option value="podrino">Podrino (穩重男聲)</option>
</select>

<!-- 語速調整 -->
<select id="speed-select">
    <option value="0.5">0.5x</option>
    <option value="0.75">0.75x</option>
    <option value="1" selected>正常</option>
    <option value="1.25">1.25x</option>
    <option value="1.5">1.5x</option>
</select>
```

#### JavaScript 功能
- `sendMessage()`: 發送訊息並處理 TTS
- `playAudio()`: 播放音頻
- `addMessageToChat()`: 添加訊息到聊天區域
- `showLoading()` / `hideLoading()`: 載入狀態管理

### 4. 支援的語音

| 語音 ID | 名稱 | 描述 | 預設狀態 |
|---------|------|------|----------|
| `podrina` | Podrina | 溫柔親切的女聲 | ✅ 預設選擇 |
| `podrisa` | Podrisa | 活潑開朗的女聲 | 可選 |
| `podrino` | Podrino | 穩重可靠的男聲 | 可選 |

### 5. 語速設定

| 語速值 | 描述 | 適用場景 |
|--------|------|----------|
| 0.5x | 慢速 | 學習、詳細說明 |
| 0.75x | 較慢 | 重要內容 |
| 1.0x | 正常 | 一般對話 (預設) |
| 1.25x | 較快 | 快速瀏覽 |
| 1.5x | 快速 | 摘要內容 |

## 🚀 使用方法

### 1. 啟動服務

```bash
# 使用啟動腳本
./start_tts_integration.sh

# 或手動啟動
cd backend/rag_pipeline && python main.py &
cd backend/tts && python main.py &
cd frontend/home && python fastapi_app.py &
```

### 2. 訪問前端

打開瀏覽器訪問：`http://localhost:8080/podri.html`

### 3. 使用 TTS 功能

1. **語音開關**: 勾選/取消勾選 "啟用語音回覆"
2. **語音選擇**: 選擇喜歡的語音類型
3. **語速調整**: 調整語音播放速度
4. **發送訊息**: 在對話框中輸入問題並按 Enter 或點擊發送按鈕

### 4. API 測試

```bash
# 測試語音列表
curl -X GET http://localhost:8005/api/v1/tts/voices

# 測試語音合成
curl -X POST http://localhost:8005/api/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "您好，我是 Podrina，您的智能語音助手。",
    "voice": "podrina",
    "speed": 1.0
  }'

# 測試完整查詢
curl -X POST http://localhost:8005/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "query": "推薦一些財經類的 Podcast",
    "enable_tts": true,
    "voice": "podrina",
    "speed": 1.0
  }'
```

## 🧪 測試功能

### 運行測試

```bash
# 使用啟動腳本運行測試
./start_tts_integration.sh test

# 或直接運行測試
cd backend/rag_pipeline
python test_tts_integration.py
```

### 測試內容

1. **TTS 服務可用性檢查**
2. **可用語音列表獲取**
3. **基本語音合成測試**
4. **不同語速測試**
5. **RAG Pipeline TTS 整合測試**

## 📊 功能驗證

### ✅ 已驗證功能

1. **語音開關**: 預設啟用，關閉時停止播放
2. **語音選擇**: 支援三種語音類型
3. **語速調整**: 支援 0.5x 到 1.5x 語速
4. **自動播放**: 收到回應後自動播放語音
5. **錯誤處理**: 網路錯誤和服務不可用的處理
6. **載入狀態**: 發送訊息時顯示載入動畫

### 🎯 符合需求

- ✅ 使用者按下 Enter 後問題自動跳轉到 podri.html
- ✅ 自動從聊天對話框送出訊息
- ✅ RAG Pipeline 回覆使用者推薦並生成 TTS
- ✅ TTS 預設語音為 Podrina (溫柔女聲)
- ✅ 使用者可以調整 TTS 回答文本語速
- ✅ 當使用者關閉語音開關時，關閉 TTS 語音回覆

## 🔧 配置說明

### 環境變數

```bash
# TTS 服務配置
TTS_SERVICE_URL=http://localhost:8003
DEFAULT_VOICE=podrina
TTS_ENABLED=true

# RAG Pipeline 配置
RAG_PIPELINE_PORT=8005
TTS_INTEGRATION_ENABLED=true
```

### 服務端口

- **RAG Pipeline**: 8005
- **TTS Service**: 8003
- **前端服務**: 8080

## 📁 新增檔案

1. `backend/rag_pipeline/test_tts_integration.py` - TTS 整合測試腳本
2. `backend/rag_pipeline/TTS_INTEGRATION_README.md` - 詳細功能說明
3. `start_tts_integration.sh` - 服務啟動腳本
4. `TTS_INTEGRATION_SUMMARY.md` - 本總結文檔

## 🔮 未來改進

1. **音頻快取**: 避免重複合成相同內容
2. **情感語音**: 根據內容自動調整語音情感
3. **串流播放**: 支援實時語音串流
4. **語音識別整合**: 結合 STT 實現語音對話
5. **更多語音選項**: 支援更多語音類型和語言

## 📞 技術支援

如有問題，請：
1. 查看 `backend/rag_pipeline/TTS_INTEGRATION_README.md` 詳細文檔
2. 運行 `./start_tts_integration.sh test` 進行測試
3. 檢查服務日誌進行故障排除

---

**實現完成時間**: 2024年12月
**版本**: 1.0.0
**狀態**: ✅ 功能完整，可投入使用 