# PodWise Podri TTS 語音合成服務

基於 Microsoft Podri TTS 的高品質語音合成服務，專為台灣語音優化設計。

## 🎯 功能特色

- **四種台灣語音**：溫柔女聲、活潑女聲、穩重男聲、專業男聲
- **高品質合成**：基於 Microsoft Podri TTS 技術
- **RESTful API**：提供完整的 HTTP API 介面
- **OOP 設計**：符合 Google Code Style 的物件導向設計
- **完整測試**：包含單元測試和整合測試

## 🏗️ 系統架構

```
tts/
├── main.py                 # FastAPI 主程式
├── tts_service.py          # TTS 服務核心類別
├── test_edge_tts.py        # 測試腳本
├── requirements.txt        # 依賴套件
├── Dockerfile             # Docker 配置
├── README.md              # 說明文件
├── config/
│   └── voice_config.py    # 語音配置管理
├── providers/
│   └── edge_tts_provider.py # Podri TTS 提供者
├── constants/
│   └── constants.py       # 系統常數
└── utils/
    └── logging_config.py  # 日誌配置
```

## 🎵 支援語音

### Podri TTS 語音
- **Podrina (溫柔女聲)**：溫柔親切的女聲，適合日常對話和情感表達
- **Podrisa (活潑女聲)**：活潑開朗的女聲，適合娛樂內容和輕鬆話題
- **Podrino (穩重男聲)**：穩重可靠的男聲，適合正式場合和專業內容
- **Podriso (專業男聲)**：專業權威的男聲，適合新聞播報和學術內容

## 🚀 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 啟動服務

```bash
python main.py
```

服務將在 `http://localhost:8501` 啟動

### 3. API 文檔

訪問 `http://localhost:8501/docs` 查看互動式 API 文檔

## 📋 API 參考

### 主要端點

- `GET /` - 服務狀態檢查
- `GET /health` - 健康檢查
- `GET /voices` - 獲取可用語音列表
- `POST /synthesize` - 語音合成
- `GET /voice/{voice_id}` - 獲取特定語音信息
- `GET /status` - 獲取服務狀態

### 語音合成請求範例

```bash
curl -X POST "http://localhost:8501/synthesize" \
     -H "Content-Type: application/json" \
     -d '{
       "文字": "您好，我是 Podrina，您的智能語音助手。",
       "語音": "podrina",
       "語速": "+0%",
       "音量": "+0%",
       "音調": "+0%"
     }'
```

## 🔧 主要設定

### 語音配置

在 `config/voice_config.py` 中定義四種台灣語音：

```python
{
    "id": "podrina",
    "name": "Podrina (溫柔女聲)",
    "voice_id": "zh-TW-HsiaoChenNeural",
    "description": "溫柔親切的女聲，適合日常對話和情感表達",
    "type": "podri_tts",
    "language": "zh-TW",
    "gender": "female",
    "style": "friendly"
}
```

### 系統常數

在 `constants/constants.py` 中定義音訊配置：

```python
class AudioConfig:
    INPUT_SAMPLE_RATE = 16000   # 輸入採樣率
    OUTPUT_SAMPLE_RATE = 24000  # 輸出採樣率
    CHANNELS = 1                # 單聲道
```

## 🐳 Docker 部署

### 建置映像

```bash
docker build -t podwise-tts .
```

### 執行容器

```bash
docker run -p 8501:8501 podwise-tts
```

## 🛠️ 依賴項目

- fastapi
- uvicorn
- edge-tts
- pydantic
- python-multipart

## ⚠️ 重要注意事項

- 確保網路連接正常（需要連接到 Microsoft TTS 服務）
- 語音合成需要一定的處理時間
- 大量請求時注意 API 限制
- 音訊檔案會暫存在記憶體中
- 定期檢查服務健康狀態 