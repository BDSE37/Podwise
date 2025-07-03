# GPT-SoVITS Web UI 部署指南

## 概述

GPT-SoVITS Web UI 是一個用於訓練和推理語音合成模型的 Web 介面，整合了以下功能：

- **語音訓練**: 使用自訂音頻訓練個人化語音模型
- **人聲分離**: UVR5 工具進行音頻處理
- **語音轉文字**: ASR 功能進行語音識別
- **模型推理**: 即時語音合成測試

## 系統需求

### 硬體需求
- **GPU**: NVIDIA GPU (建議 RTX 3060 或更高)
- **記憶體**: 至少 16GB RAM
- **儲存空間**: 至少 100GB 可用空間

### 軟體需求
- Kubernetes 集群
- Podman 或 Docker
- NVIDIA Container Runtime
- kubectl

## 快速部署

### 1. 建置和部署

```bash
# 進入部署目錄
cd deploy/k8s/gpt-sovits-webui

# 執行完整建置和部署
./build-and-deploy-gpt-sovits.sh
```

### 2. 只建置映像

```bash
./build-and-deploy-gpt-sovits.sh --build-only
```

### 3. 只部署服務

```bash
./build-and-deploy-gpt-sovits.sh --deploy-only
```

## 訪問地址

部署完成後，您可以通過以下地址訪問服務：

- **主 Web UI**: http://192.168.32.38:30786
- **主服務**: http://192.168.32.38:30974
- **UVR5 工具**: http://192.168.32.38:30973
- **推理 TTS**: http://192.168.32.38:30972
- **子服務**: http://192.168.32.38:30971

## 訓練流程

### 1. 準備音頻檔案

1. 進入 Web UI 主介面
2. 上傳高品質的音頻檔案到 `raw` 目錄
3. 建議音頻格式：WAV, 44.1kHz, 16bit
4. 建議音頻長度：5-30 分鐘

### 2. 音頻預處理

1. 使用 UVR5 進行人聲分離
2. 移除背景音樂和噪音
3. 確保音頻品質

### 3. 語音轉文字

1. 使用 ASR 功能進行語音識別
2. 生成對應的文字檔案
3. 檢查文字準確性

### 4. 模型訓練

#### SoVITS 模型訓練
1. 設定訓練參數
2. 選擇預訓練模型
3. 開始訓練
4. 監控訓練進度

#### GPT 模型訓練
1. 設定 GPT 訓練參數
2. 選擇預訓練模型
3. 開始訓練
4. 等待訓練完成

### 5. 推理測試

1. 載入訓練好的模型
2. 輸入測試文字
3. 生成語音檔案
4. 評估語音品質

## 配置說明

### 環境變數

| 變數名稱 | 預設值 | 說明 |
|---------|--------|------|
| `version` | `v2Pro` | GPT-SoVITS 版本 |
| `language` | `zh` | 介面語言 |
| `CUDA_VISIBLE_DEVICES` | `0` | 使用的 GPU 設備 |

### 端口配置

| 服務 | 容器端口 | NodePort | 說明 |
|------|----------|----------|------|
| Web UI | 7860 | 30786 | 主介面 |
| 主服務 | 9874 | 30974 | 主要功能 |
| UVR5 | 9873 | 30973 | 音頻處理 |
| 推理 TTS | 9872 | 30972 | 語音合成 |
| 子服務 | 9871 | 30971 | 輔助功能 |

## 儲存配置

### PVC 配置

| PVC 名稱 | 大小 | 用途 |
|----------|------|------|
| `gpt-sovits-data-pvc` | 50Gi | 主要數據存儲 |
| `gpt-sovits-models-pvc` | 20Gi | 預訓練模型 |
| `gpt-sovits-weights-pvc` | 30Gi | SoVITS 權重 |
| `gpt-sovits-gpt-weights-pvc` | 30Gi | GPT 權重 |
| `gpt-sovits-logs-pvc` | 10Gi | 日誌檔案 |
| `gpt-sovits-output-pvc` | 20Gi | 輸出檔案 |

## 故障排除

### 常見問題

#### 1. Pod 無法啟動
```bash
# 檢查 Pod 狀態
kubectl get pods -n podwise -l app=gpt-sovits-webui

# 查看 Pod 日誌
kubectl logs -n podwise -l app=gpt-sovits-webui
```

#### 2. GPU 無法使用
```bash
# 檢查 GPU 驅動
nvidia-smi

# 檢查 NVIDIA Container Runtime
kubectl get nodes -o json | jq '.items[].status.allocatable'
```

#### 3. 儲存空間不足
```bash
# 檢查 PVC 狀態
kubectl get pvc -n podwise

# 檢查儲存使用情況
kubectl describe pvc -n podwise
```

### 日誌查看

```bash
# 查看 Pod 日誌
kubectl logs -f -n podwise -l app=gpt-sovits-webui

# 查看服務日誌
kubectl logs -f -n podwise deployment/gpt-sovits-webui
```

## 維護操作

### 更新部署

```bash
# 重新建置映像
./build-and-deploy-gpt-sovits.sh --build-only

# 重新部署
kubectl rollout restart deployment/gpt-sovits-webui -n podwise
```

### 備份模型

```bash
# 備份訓練好的模型
kubectl cp podwise/gpt-sovits-webui-xxx:/app/GPT-SoVITS/SoVITS_weights_v2Pro ./backup/sovits
kubectl cp podwise/gpt-sovits-webui-xxx:/app/GPT-SoVITS/GPT_weights_v2Pro ./backup/gpt
```

### 清理資源

```bash
# 刪除部署
kubectl delete -f gpt-sovits-webui-deployment.yaml

# 刪除 PVC (注意：會刪除所有數據)
kubectl delete -f gpt-sovits-pvcs.yaml
```

## 最佳實踐

### 訓練建議

1. **音頻品質**: 使用高品質、清晰的音頻檔案
2. **音頻長度**: 建議 10-20 分鐘的訓練音頻
3. **環境安靜**: 確保錄音環境安靜無噪音
4. **語音一致**: 使用同一個人的語音進行訓練

### 性能優化

1. **GPU 記憶體**: 根據 GPU 記憶體調整批次大小
2. **儲存空間**: 定期清理不需要的檔案
3. **網路頻寬**: 確保網路連接穩定

### 安全注意事項

1. **模型保護**: 定期備份訓練好的模型
2. **訪問控制**: 限制 Web UI 的訪問權限
3. **數據隱私**: 注意訓練數據的隱私保護

## 技術支援

如果遇到問題，請檢查：

1. Kubernetes 集群狀態
2. GPU 驅動和 Container Runtime
3. 網路連接和防火牆設定
4. 儲存空間和權限

更多技術文檔請參考 [GPT-SoVITS 官方文檔](https://github.com/RVC-Boss/GPT-SoVITS)。 