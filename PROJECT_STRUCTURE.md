# Podwise 專案結構說明

## 專案架構概述

本專案採用 **frontend/backend** 主架構，結合 **MLOps** 最佳實踐進行組織，確保可擴展性、可維護性和穩定性。

## 目錄結構

```
Podwise/
├── frontend/                    # 前端應用程式
│   ├── pages/                   # 頁面檔案
│   │   ├── index.html          # 主頁面
│   │   ├── login.html          # 登入頁面
│   │   ├── elements.html       # 元件頁面
│   │   ├── generic.html        # 通用頁面
│   │   ├── main.py             # 主應用程式
│   │   └── podri_chat_main.py  # 聊天主頁面 (Streamlit)
│   ├── components/             # UI 元件
│   ├── utils/                  # 前端工具函數
│   ├── assets/                 # 靜態資源
│   │   ├── css/               # 樣式檔案
│   │   ├── js/                # JavaScript 檔案
│   │   ├── sass/              # Sass 檔案
│   │   └── webfonts/          # 字體檔案
│   ├── images/                 # 圖片資源
│   ├── chat/                   # 聊天相關檔案
│   │   ├── assets/            # 聊天專用資源
│   │   ├── Dockerfile         # 聊天服務容器
│   │   ├── requirements.txt   # 聊天服務依賴
│   │   └── k8s-deployment.yaml # K8s 部署配置
│   ├── Dockerfile             # 前端容器
│   ├── nginx-default.conf     # Nginx 配置
│   ├── requirements.txt       # 前端依賴
│   └── Makefile               # 建置腳本
│
├── backend/                    # 後端服務
│   ├── services/              # 服務層
│   │   ├── service_manager.py        # 服務管理器
│   │   ├── intelligent_processor.py  # 智能處理器
│   │   ├── musicgen_service.py       # MusicGen 服務
│   │   ├── minio_audio_service.py    # MinIO 音訊服務
│   │   └── intelligent_audio_search.py # 智能音訊搜尋
│   ├── core/                  # 核心功能
│   │   └── base_service.py    # 基礎服務類別
│   ├── utils/                 # 工具函數
│   │   ├── api_key_manager.py # API 金鑰管理
│   │   └── env_config.py      # 環境配置
│   ├── models/                # 模型管理
│   ├── data/                  # 資料管理
│   ├── monitoring/            # 監控系統
│   ├── deployment/            # 部署配置
│   ├── api/                   # API 介面
│   ├── config/                # 配置管理
│   ├── llm/                   # LLM 服務
│   ├── tts/                   # TTS 服務
│   ├── stt/                   # STT 服務
│   ├── musicgen/              # MusicGen 服務
│   ├── rag_pipeline/          # RAG 管道
│   └── ml_pipeline/           # ML 管道
│
├── deploy/                    # 部署相關
│   ├── docker/               # Docker 配置
│   └── k8s/                  # Kubernetes 配置
│
├── monitoring/                # 監控系統
│   ├── grafana/              # Grafana 儀表板
│   └── prometheus/           # Prometheus 監控
│
├── docs/                     # 文件
├── data/                     # 資料檔案
├── models/                   # 模型檔案
├── notebooks/                # Jupyter 筆記本
└── n8n_data/                 # N8N 工作流程資料
```

## MLOps 架構說明

### 1. 服務層 (Services Layer)
- **ServiceManager**: 管理所有服務的生命週期
- **IntelligentProcessor**: 智能處理器，整合多個 AI 服務
- **MusicGenService**: AI 音樂生成服務
- **MinioAudioService**: 音訊儲存服務
- **IntelligentAudioSearch**: 智能音訊搜尋服務

### 2. 核心層 (Core Layer)
- **BaseService**: 所有服務的基礎抽象類別
- **ModelService**: 專門用於 ML 模型管理的服務類別

### 3. 工具層 (Utils Layer)
- **APIKeyManager**: API 金鑰管理，支援多種 LLM 提供商
- **EnvironmentConfig**: 環境配置管理

### 4. 前端架構
- **Pages**: 所有頁面檔案集中管理
- **Components**: UI 元件模組化
- **Utils**: 前端工具函數
- **Assets**: 靜態資源管理

## 設計原則

### 1. 可擴展性 (Scalability)
- 模組化設計，易於添加新功能
- 服務解耦，獨立部署
- 支援水平擴展

### 2. 可維護性 (Maintainability)
- 清晰的目錄結構
- 統一的命名規範
- 完整的文件說明

### 3. 穩定性 (Stability)
- 健康檢查機制
- 錯誤處理和日誌記錄
- 監控和警報系統

## API 金鑰優先順序

1. **OpenAI** - 主要 LLM 提供商
2. **Gemini** - Google AI 服務
3. **Google Search** - 搜尋功能
4. **Anthropic** - Claude 模型
5. **本地 LLM** - 無金鑰時的備選方案

## 部署架構

### Kubernetes 部署
- 使用 K8s 進行容器編排
- 支援自動擴縮
- 健康檢查和故障恢復

### Docker 容器化
- 每個服務獨立容器化
- 微服務架構
- 易於部署和維護

## 監控和日誌

### 監控系統
- **Grafana**: 視覺化監控儀表板
- **Prometheus**: 指標收集和警報
- **健康檢查**: 服務狀態監控

### 日誌管理
- 結構化日誌記錄
- 集中式日誌收集
- 錯誤追蹤和分析

## 開發工作流程

1. **開發**: 在對應的服務目錄中開發功能
2. **測試**: 使用單元測試和整合測試
3. **建置**: Docker 容器化建置
4. **部署**: K8s 部署到測試/生產環境
5. **監控**: 監控服務運行狀態

## 注意事項

- 所有服務都繼承自 `BaseService`
- 使用 OOP 設計模式
- 遵循 MLOps 最佳實踐
- 支援多種 LLM 提供商
- 具備完整的錯誤處理機制 