# PodWise 統一前端配置

## 概述

本配置基於您原有的 `nginx-proxy.conf` 擴展，提供統一的前端訪問入口，避免頻繁修改端口進行測試。

## 架構

```
用戶訪問 (端口 80)
    ↓
Nginx 代理
    ↓
FastAPI 前端 (端口 8081)
    ├── index.html (主頁面)
    ├── podri.html (聊天頁面)
    └── 其他靜態資源
```

## 文件說明

### 配置文件
- `nginx-unified.conf` - 統一的 nginx 代理配置
- `start_frontend.sh` - 前端服務啟動腳本

### 主要頁面
- `index.html` - 主頁面（onboarding 流程）
- `podri.html` - Podri 聊天頁面
- `fastapi_app.py` - FastAPI 應用服務器

## 使用方法

### 1. 啟動前端服務

```bash
# 進入前端目錄
cd frontend

# 啟動所有前端服務
./start_frontend.sh start

# 或者只檢查狀態
./start_frontend.sh status
```

### 2. 訪問地址

啟動成功後，您可以通過以下地址訪問：

- **主頁面**: http://localhost/
- **Podri 聊天**: http://localhost/podri
- **健康檢查**: http://localhost/health
- **系統狀態**: http://localhost/status

### 3. 管理服務

```bash
# 停止所有服務
./start_frontend.sh stop

# 重新啟動
./start_frontend.sh restart

# 查看幫助
./start_frontend.sh help
```

## 配置詳情

### Nginx 代理規則

1. **主頁面** (`/`)
   - 代理到 FastAPI 前端 (端口 8081)
   - 提供靜態文件服務

2. **Podri 聊天** (`/podri`)
   - 專門代理到 podri.html 頁面
   - 支援聊天功能

3. **API 代理** (`/api/`)
   - 根據路徑分發到不同後端服務
   - 支援推薦、反饋、RAG、TTS、STT 等服務

4. **健康檢查** (`/health`)
   - 提供服務健康狀態檢查

### 後端服務端口

- 8000: 主後端 API
- 8001: RAG Pipeline
- 8002: TTS 服務
- 8003: STT 服務
- 8004: LLM 服務
- 8005: ML Pipeline
- 8006: 推薦服務

## 開發流程

### 1. 本地開發

```bash
# 啟動前端服務
./start_frontend.sh start

# 在瀏覽器中訪問 http://localhost/
# 進行開發和測試
```

### 2. 修改配置

如果需要修改 nginx 配置：

1. 編輯 `nginx-unified.conf`
2. 重新啟動服務：
   ```bash
   ./start_frontend.sh restart
   ```

### 3. 調試

如果遇到問題：

1. 檢查服務狀態：
   ```bash
   ./start_frontend.sh status
   ```

2. 查看 nginx 錯誤日誌：
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. 檢查 FastAPI 日誌：
   ```bash
   # 查看 Python 進程
   ps aux | grep fastapi_app.py
   ```

## 注意事項

1. **權限要求**: 啟動腳本需要 sudo 權限來管理 nginx
2. **端口衝突**: 確保端口 80 和 8081 沒有被其他服務佔用
3. **依賴服務**: 確保後端 API 服務正在運行
4. **瀏覽器快取**: 開發時可能需要清除瀏覽器快取

## 故障排除

### 常見問題

1. **Nginx 啟動失敗**
   - 檢查 nginx 是否已安裝
   - 檢查配置文件語法：`sudo nginx -t`

2. **FastAPI 啟動失敗**
   - 檢查 Python 環境
   - 檢查依賴包是否安裝
   - 檢查端口 8081 是否被佔用

3. **頁面無法訪問**
   - 檢查防火牆設定
   - 確認服務正在運行
   - 檢查瀏覽器控制台錯誤

### 日誌位置

- Nginx 錯誤日誌: `/var/log/nginx/error.log`
- Nginx 訪問日誌: `/var/log/nginx/access.log`
- FastAPI 日誌: 控制台輸出

## 擴展功能

如果需要添加新的頁面或服務：

1. 在 `frontend/` 目錄添加新的 HTML 文件
2. 在 `fastapi_app.py` 添加新的路由
3. 在 `nginx-unified.conf` 添加代理規則
4. 重新啟動服務

這樣您就可以通過統一的端口 80 訪問所有前端功能，而不需要記住不同的端口號！ 