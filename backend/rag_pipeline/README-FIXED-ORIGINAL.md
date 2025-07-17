# Podwise RAG Pipeline 修復指南

## 問題診斷

原本的 RAG Pipeline 無法執行的主要原因：

1. **模組導入失敗** - 某些核心模組無法正確導入
2. **配置問題** - Pydantic 配置驗證錯誤
3. **依賴缺失** - 缺少必要的 Python 套件
4. **路徑問題** - Python 路徑設定不正確

## 解決方案

### 方案一：診斷原本問題

使用診斷工具檢查具體問題：

```bash
# 在容器內執行
cd /app/rag_pipeline
python3 diagnose-original.py
```

診斷工具會檢查：
- 檔案結構完整性
- Python 路徑設定
- 核心模組導入狀況
- RAG Pipeline 模組導入狀況
- main.py 和 app 導入狀況

### 方案二：使用修復版本

修復版本跳過了有問題的模組，提供基本功能：

```bash
# 啟動修復版本
chmod +x run-fixed-original.sh
./run-fixed-original.sh
```

或者直接執行：

```bash
python3 start-fixed-original.py
```

### 方案三：測試修復版本

```bash
# 測試修復版本功能
python3 test-fixed-original.py
```

## 修復版本功能

### 可用功能
- ✅ 基本 API 端點
- ✅ 健康檢查
- ✅ 用戶驗證
- ✅ 簡單查詢處理
- ✅ 系統資訊
- ✅ 錯誤處理

### 暫時不可用功能
- ❌ 向量搜尋
- ❌ Web 搜尋
- ❌ TTS 語音合成
- ❌ 複雜的 RAG 處理
- ❌ 資料庫連接

## API 端點

### 基本端點
- `GET /` - 根端點
- `GET /health` - 健康檢查
- `GET /docs` - API 文檔

### 用戶端點
- `POST /api/v1/validate-user` - 用戶驗證
- `POST /api/v1/query` - 查詢處理

### 系統端點
- `GET /api/v1/system-info` - 系統資訊
- `GET /api/v1/tts/voices` - TTS 語音列表
- `POST /api/v1/tts/synthesize` - TTS 語音合成

## 查詢處理邏輯

修復版本使用簡單的關鍵字匹配：

- **播客相關** - 回應播客推薦
- **投資理財** - 回應財經內容
- **學習教育** - 回應教育內容
- **其他查詢** - 通用回應

## 使用範例

### 啟動服務
```bash
# 在容器內
cd /app/rag_pipeline
python3 start-fixed-original.py
```

### 測試連接
```bash
# 健康檢查
curl http://localhost:8010/health

# 查詢測試
curl -X POST http://localhost:8010/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "推薦一些播客", "user_id": "test_user"}'
```

### 前端連接
前端可以連接到 `http://localhost:8010` 使用修復版本的 API。

## 故障排除

### 端口被佔用
腳本會自動尋找可用端口（8010-8015）。

### 模組導入錯誤
確保已安裝基本套件：
```bash
pip3 install fastapi uvicorn pydantic requests
```

### 服務無法啟動
檢查日誌輸出，確認錯誤訊息。

## 下一步

1. **診斷原本問題** - 使用診斷工具找出具體問題
2. **修復缺失模組** - 根據診斷結果修復模組
3. **逐步恢復功能** - 一個一個恢復完整功能
4. **測試驗證** - 確保所有功能正常

## 檔案說明

- `diagnose-original.py` - 診斷原本問題
- `start-fixed-original.py` - 修復版本啟動腳本
- `run-fixed-original.sh` - 啟動腳本
- `test-fixed-original.py` - 測試腳本
- `README-FIXED-ORIGINAL.md` - 本說明文件 