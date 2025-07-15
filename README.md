# Podwise Frontend

這是 Podwise 項目的前端部分，包含聊天界面和主頁面。

## 項目結構

```
frontend/
├── assets/          # 靜態資源文件
├── chat/           # 聊天應用
├── home/           # 主頁面
├── Dockerfile      # Docker 配置
├── requirements.txt # Python 依賴
└── nginx-default.conf # Nginx 配置
```

## 功能特性

- **聊天界面**: 基於 FastAPI 的聊天應用
- **主頁面**: 響應式設計的主頁
- **Docker 支持**: 完整的容器化部署
- **Nginx 配置**: 生產環境優化

## 快速開始

### 本地開發

1. 安裝依賴：
```bash
pip install -r requirements.txt
```

2. 運行開發服務器：
```bash
cd chat && python podri_chat.py
```

### Docker 部署

```bash
docker build -t podwise-frontend .
docker run -p 8000:8000 podwise-frontend
```

## 技術棧

- **後端**: FastAPI, Python
- **前端**: HTML, CSS, JavaScript
- **容器**: Docker
- **Web 服務器**: Nginx

## 授權

詳見 [LICENSE.txt](LICENSE.txt) 文件。 