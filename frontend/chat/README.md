# Podri Chat - 智慧助理

## 專案概述

Podri Chat 是一個基於 AI 的智慧助理系統，整合了 CrewAI 三層代理人機制、LangChain 檢索增強生成、語音合成 (TTS) 和語音識別 (STT) 功能。

## 系統架構

### 1. 資料處理流程
- **MongoDB 長文本處理**: 根據換行符 (`\n`) 和空白進行文本切斷
- **TAG 生成**: 優先使用參考資料中的 TAG，不足時使用 Word2Vec 和 Transformer 生成
- **向量化**: 使用 BGE-M3 模型生成嵌入向量
- **儲存**: 符合 Milvus Collections 格式儲存

### 2. 前端設計
- **側邊欄 (1/4 版面)**:
  - 用戶 ID 驗證 (PostgreSQL 自定義 ID)
  - 語音回覆設定 (Edge TTS)
  - 四種台灣語音選擇 (Podria, Podrisa, Podrio, Podriu)
  - 試聽功能
  - 音量和播放速度調整

- **主聊天版面 (3/4 版面)**:
  - 聊天對話框 (聊天泡泡形式)
  - 快速問答 (2x2 網格佈局)
  - 輸入區域 (文字/語音輸入)
  - CrewAI 三層代理人回應
  - 信心值顯示 (> 0.7)

## 技術棧

### 前端
- **Streamlit**: 主要前端框架
- **CSS**: 自定義樣式，聊天泡泡設計
- **JavaScript**: 互動功能

### 後端
- **CrewAI**: 三層代理人機制
- **LangChain**: 檢索增強生成
- **PostgreSQL**: 用戶資料和互動記錄
- **Milvus**: 向量資料庫
- **Edge TTS**: 語音合成
- **BGE-M3**: 文本嵌入模型

### 資料處理
- **jieba**: 中文分詞
- **sentence-transformers**: 文本嵌入
- **Word2Vec/Transformer**: TAG 生成

## 安裝與執行

### 1. 環境準備
```bash
# 檢查 Python 環境
python3 --version

# 創建虛擬環境
python3 -m venv venv
source venv/bin/activate
```

### 2. 安裝依賴
```bash
pip install -r requirements.txt
```

### 3. 啟動必要服務
```bash
# PostgreSQL
docker-compose up -d postgresql

# Milvus
docker-compose up -d milvus

# 檢查服務狀態
docker-compose ps
```

### 4. 執行應用
```bash
# 使用執行腳本
./run_podri_chat.sh

# 或直接執行
streamlit run podri_chat.py --server.port 8501
```

## 功能特色

### 1. 智能對話
- **CrewAI 三層代理人**:
  - 研究員代理人: 分析 Podcast 內容
  - 分析師代理人: 分析用戶偏好
  - 回應者代理人: 生成個性化回答

### 2. 語音功能
- **四種台灣語音**: Podria, Podrisa, Podrio, Podriu
- **試聽功能**: 即時語音預覽
- **音量和速度控制**: 自定義播放設定
- **語音輸入**: 支援音訊檔案上傳

### 3. 用戶體驗
- **用戶識別**: PostgreSQL 自定義 ID 驗證
- **訪客模式**: 未登入用戶的基礎功能
- **偏好追蹤**: 記錄用戶互動和偏好
- **快速問答**: 常用問題一鍵提問

### 4. 資料處理
- **智能文本切斷**: 基於語義的文本分割
- **多層 TAG 生成**: 參考資料 + AI 生成
- **向量化儲存**: Milvus 高效檢索
- **信心值評估**: 回答品質保證

## 資料庫結構

### PostgreSQL 表格
```sql
-- 用戶表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    custom_id VARCHAR(50) UNIQUE,
    username VARCHAR(100),
    category_preference VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用戶互動表
CREATE TABLE user_interactions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50),
    question TEXT,
    answer TEXT,
    confidence FLOAT,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### Milvus Collections
```python
# 集合結構
{
    "id": "chunk_id",
    "content": "文本內容",
    "tags": ["tag1", "tag2", "tag3"],
    "source_id": "來源ID",
    "embedding": [0.1, 0.2, ...],  # BGE-M3 向量
    "metadata": {
        "total_chunks": 5,
        "chunk_index": 0,
        "processing_method": "newline_and_space_split"
    }
}
```

## 開發指南

### 1. 代碼風格
- 遵循 Google Python Style Guide
- 使用 OOP 設計模式
- 完整的類型註解
- 詳細的文檔字串

### 2. 模組化設計
- 單一資料夾 = 單一功能
- 清晰的依賴關係
- 易於測試和維護

### 3. 錯誤處理
- 完整的異常捕獲
- 用戶友好的錯誤訊息
- 優雅的降級處理

## 部署說明

### 1. Docker 部署
```bash
# 建置映像
docker build -t podri-chat .

# 執行容器
docker run -p 8501:8501 podri-chat
```

### 2. 生產環境
- 使用 Nginx 反向代理
- 配置 SSL 證書
- 設定環境變數
- 監控和日誌記錄

## 故障排除

### 常見問題
1. **資料庫連接失敗**: 檢查 PostgreSQL 服務狀態
2. **Milvus 連接失敗**: 確認向量資料庫運行狀態
3. **語音生成失敗**: 檢查網路連接和 Edge TTS 服務
4. **依賴安裝失敗**: 更新 pip 和 Python 版本

### 日誌查看
```bash
# Streamlit 日誌
streamlit run podri_chat.py --logger.level debug

# Docker 日誌
docker-compose logs -f
```

## 貢獻指南

1. Fork 專案
2. 創建功能分支
3. 提交變更
4. 發起 Pull Request

## 授權

本專案採用 MIT 授權條款。

## 聯絡資訊

- 專案維護者: PodWise Team
- 電子郵件: information@podwise.com
- 專案網址: https://github.com/podwise/podri-chat 