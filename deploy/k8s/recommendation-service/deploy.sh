#!/bin/bash

# Podwise 推薦服務部署腳本
# 用於在 K8s 集群中部署推薦服務

set -e

echo "🚀 開始部署 Podwise 推薦服務..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 檢查 kubectl 是否可用
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl 未安裝或不在 PATH 中${NC}"
    exit 1
fi

# 檢查集群連接
echo -e "${BLUE}📋 檢查 K8s 集群連接...${NC}"
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ 無法連接到 K8s 集群${NC}"
    exit 1
fi
echo -e "${GREEN}✅ K8s 集群連接正常${NC}"

# 檢查 namespace 是否存在
echo -e "${BLUE}📋 檢查 podwise namespace...${NC}"
if ! kubectl get namespace podwise &> /dev/null; then
    echo -e "${YELLOW}⚠️ podwise namespace 不存在，正在創建...${NC}"
    kubectl create namespace podwise
    echo -e "${GREEN}✅ podwise namespace 創建成功${NC}"
else
    echo -e "${GREEN}✅ podwise namespace 已存在${NC}"
fi

# 檢查依賴服務
echo -e "${BLUE}📋 檢查依賴服務...${NC}"

# 檢查 PostgreSQL
if kubectl get svc postgres -n podwise &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL 服務存在${NC}"
else
    echo -e "${YELLOW}⚠️ PostgreSQL 服務不存在，請確保已部署${NC}"
fi

# 檢查 MinIO
if kubectl get svc minio -n podwise &> /dev/null; then
    echo -e "${GREEN}✅ MinIO 服務存在${NC}"
else
    echo -e "${YELLOW}⚠️ MinIO 服務不存在，請確保已部署${NC}"
fi

# 創建 ConfigMap 包含推薦服務代碼
echo -e "${BLUE}📋 創建推薦服務 ConfigMap...${NC}"

# 讀取推薦服務代碼
RECOMMENDATION_SERVICE_CODE=$(cat ../../../backend/api/recommendation_service.py)

# 創建臨時的 ConfigMap YAML
cat > temp-configmap.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: recommendation-service-code
  namespace: podwise
data:
  recommendation_service.py: |
$(echo "$RECOMMENDATION_SERVICE_CODE" | sed 's/^/    /')
EOF

# 應用 ConfigMap
kubectl apply -f temp-configmap.yaml
echo -e "${GREEN}✅ ConfigMap 創建成功${NC}"

# 清理臨時文件
rm temp-configmap.yaml

# 部署推薦服務
echo -e "${BLUE}📋 部署推薦服務...${NC}"
kubectl apply -f recommendation-deployment.yaml
echo -e "${GREEN}✅ 推薦服務部署成功${NC}"

# 等待 Pod 啟動
echo -e "${BLUE}📋 等待 Pod 啟動...${NC}"
kubectl wait --for=condition=ready pod -l app=recommendation-service -n podwise --timeout=300s
echo -e "${GREEN}✅ Pod 啟動完成${NC}"

# 檢查服務狀態
echo -e "${BLUE}📋 檢查服務狀態...${NC}"
kubectl get pods -n podwise -l app=recommendation-service
kubectl get svc -n podwise -l app=recommendation-service

# 測試服務健康狀態
echo -e "${BLUE}📋 測試服務健康狀態...${NC}"
kubectl port-forward svc/recommendation-service 8005:8005 -n podwise &
PORT_FORWARD_PID=$!

# 等待端口轉發啟動
sleep 5

# 測試健康檢查
if curl -s http://localhost:8005/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ 服務健康檢查通過${NC}"
else
    echo -e "${RED}❌ 服務健康檢查失敗${NC}"
fi

# 停止端口轉發
kill $PORT_FORWARD_PID 2>/dev/null || true

# 顯示服務信息
echo -e "${BLUE}📋 服務信息...${NC}"
echo -e "${GREEN}✅ 推薦服務部署完成！${NC}"
echo ""
echo -e "${YELLOW}📊 服務詳情:${NC}"
echo "  - 服務名稱: recommendation-service"
echo "  - 命名空間: podwise"
echo "  - 端口: 8005"
echo "  - API 端點: http://recommendation-service.podwise.svc.cluster.local:8005"
echo ""
echo -e "${YELLOW}🔗 可用的 API 端點:${NC}"
echo "  - GET  /health                    - 健康檢查"
echo "  - POST /recommendations           - 獲取推薦"
echo "  - POST /feedback                  - 記錄反饋"
echo "  - GET  /user/preferences/{user_id} - 獲取用戶偏好"
echo "  - GET  /minio/audio/{bucket}/{file} - 獲取音檔 URL"
echo ""
echo -e "${YELLOW}🧪 測試命令:${NC}"
echo "  kubectl port-forward svc/recommendation-service 8005:8005 -n podwise"
echo "  curl http://localhost:8005/health"
echo ""
echo -e "${YELLOW}📝 日誌查看:${NC}"
echo "  kubectl logs -f deployment/recommendation-service -n podwise"
echo ""
echo -e "${GREEN}🎉 部署完成！推薦服務已準備就緒。${NC}" 