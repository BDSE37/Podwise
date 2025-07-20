# Podwise FastAPI 反向代理啟動指南

## 概述

Podwise 使用 FastAPI 作為統一的反向代理，整合所有前端頁面功能和後端微服務。這種架構提供了：

- **統一入口點**：所有請求都通過 `http://localhost:8008`
- **靜態檔案服務**：前端頁面、圖片、CSS、JS 等
- **API 代理**：將請求轉發到對應的微服務
- **用戶管理**：統一的用戶註冊、偏好設定等
- **音檔管理**：音檔播放、下載等服務

## 啟動腳本

### 1. 快速啟動腳本 (推薦)

```bash
# 進入後端目錄
cd backend

# 執行快速啟動
./quick_fastapi_start.sh
```

**特點：**
- 只啟動 FastAPI 反向代理
- 檢查其他服務狀態但不強制啟動
- 適合開發和測試環境
- 啟動速度快

### 2. 完整啟動腳本

```bash
# 進入後端目錄
cd backend

# 執行完整啟動
./start_fastapi_proxy.sh start
```

**特點：**
- 啟動基礎設施服務 (PostgreSQL, MinIO, Milvus)
- 啟動所有後端微服務
- 最後啟動 FastAPI 反向代理
- 適合生產環境

## 服務架構

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 反向代理 (8008)                   │
├─────────────────────────────────────────────────────────────┤
│ 前端頁面 │ 靜態檔案 │ API 代理 │ 用戶管理 │ 音檔管理 │ 其他    │
└─────────────────┬───────────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌────▼────┐   ┌────▼────┐
│ TTS   │   │ STT     │   │ RAG     │
│ 8002  │   │ 8003    │   │ 8005    │
└───────┘   └─────────┘   └─────────┘
    │             │             │
┌───▼───┐   ┌────▼────┐   ┌────▼────┐
│ LLM   │   │ ML      │   │ 其他    │
│ 8006  │   │ 8004    │   │ 服務    │
└───────┘   └─────────┘   └─────────┘
```

## 訪問地址

啟動成功後，可以通過以下地址訪問：

- **前端頁面**: http://localhost:8008
- **API 文檔**: http://localhost:8008/docs
- **ReDoc 文檔**: http://localhost:8008/redoc
- **健康檢查**: http://localhost:8008/health
- **服務狀態**: http://localhost:8008/api/v1/services

## 主要功能

### 1. 前端頁面服務
- `/` - 主頁面
- `/index.html` - 首頁
- `/podri.html` - Podri 頁面
- `/assets/*` - 靜態資源 (CSS, JS)
- `/images/*` - 圖片資源

### 2. API 代理
- `/api/tts/*` → TTS 服務 (8002)
- `/api/stt/*` → STT 服務 (8003)
- `/api/rag/*` → RAG Pipeline (8005)
- `/api/ml/*` → ML Pipeline (8004)
- `/api/llm/*` → LLM 服務 (8006)

### 3. 用戶管理
- `/api/user/register` - 用戶註冊
- `/api/user/preferences` - 偏好設定
- `/api/user/context/{user_id}` - 用戶上下文
- `/api/user/feedback` - 用戶反饋

### 4. 音檔管理
- `/api/audio/presigned-url` - 獲取音檔下載連結
- `/api/audio/play` - 記錄播放行為
- `/api/audio/heart-like` - 記錄喜歡行為

## 環境變數配置

可以在啟動前設定環境變數來自定義服務地址：

```bash
export TTS_SERVICE_URL="http://localhost:8002"
export STT_SERVICE_URL="http://localhost:8003"
export RAG_PIPELINE_URL="http://localhost:8005"
export ML_PIPELINE_URL="http://localhost:8004"
export LLM_SERVICE_URL="http://localhost:8006"
```

## 管理命令

### 完整啟動腳本管理

```bash
# 啟動所有服務
./start_fastapi_proxy.sh start

# 停止所有服務
./start_fastapi_proxy.sh stop

# 重新啟動
./start_fastapi_proxy.sh restart

# 查看服務狀態
./start_fastapi_proxy.sh status

# 查看服務日誌
./start_fastapi_proxy.sh logs
```

## 故障排除

### 1. 端口被佔用
```bash
# 檢查端口使用情況
lsof -i :8008

# 或使用 netstat
netstat -tlnp | grep :8008
```

### 2. 依賴問題
```bash
# 重新安裝依賴
pip3 install -r requirements_unified_api.txt
```

### 3. 服務無法連接
```bash
# 檢查服務健康狀態
curl http://localhost:8008/health

# 檢查各微服務狀態
curl http://localhost:8002/health  # TTS
curl http://localhost:8003/health  # STT
curl http://localhost:8005/health  # RAG
```

### 4. 前端資源無法載入
```bash
# 檢查前端目錄結構
ls -la ../frontend/
ls -la ../frontend/assets/
ls -la ../frontend/images/
```

## 開發模式

### 1. 單獨啟動 FastAPI 反向代理
```bash
cd backend
python3 unified_api_gateway.py
```

### 2. 啟用自動重載
修改 `unified_api_gateway.py` 最後的啟動部分：
```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8008,
    reload=True,  # 改為 True
    log_level="debug"  # 改為 debug
)
```

## 注意事項

1. **服務依賴**：FastAPI 反向代理可以獨立運行，但某些功能需要其他微服務
2. **端口配置**：確保 8008 端口未被其他服務佔用
3. **檔案權限**：確保腳本有執行權限 (`chmod +x *.sh`)
4. **Python 環境**：建議使用虛擬環境
5. **日誌管理**：服務日誌保存在 `backend/logs/` 目錄

## 進階配置

### 自定義配置
可以修改 `unified_api_gateway.py` 中的配置：

```python
# 服務配置
SERVICE_CONFIGS = {
    "tts": {
        "url": os.getenv("TTS_SERVICE_URL", "http://localhost:8002"),
        "health_endpoint": "/health"
    },
    # ... 其他服務配置
}
```

### 添加新的代理路由
在 `unified_api_gateway.py` 中添加新的路由：

```python
@app.api_route("/api/new-service/{path:path}", methods=["GET", "POST"])
async def proxy_to_new_service(path: str, request: Request):
    # 實現代理邏輯
    pass
``` 