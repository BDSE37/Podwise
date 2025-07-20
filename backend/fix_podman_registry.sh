#!/bin/bash

# Podman 容器註冊表配置修復腳本
# 解決 "short-name did not resolve to an alias" 錯誤

echo "🔧 修復 Podman 容器註冊表配置..."

# 檢查是否為 root 用戶
if [ "$EUID" -eq 0 ]; then
    echo "✅ 以 root 權限執行"
else
    echo "⚠️  需要 root 權限來修改系統配置"
    echo "請使用 sudo 執行此腳本"
    exit 1
fi

# 創建或修改 containers-registries.conf
REGISTRY_CONF="/etc/containers/registries.conf"

echo "📝 配置容器註冊表..."

# 備份現有配置
if [ -f "$REGISTRY_CONF" ]; then
    cp "$REGISTRY_CONF" "${REGISTRY_CONF}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 已備份現有配置"
fi

# 創建新的配置
cat > "$REGISTRY_CONF" << 'EOF'
# 容器註冊表配置
# 允許使用短名稱拉取映像檔

unqualified-search-registries = ["docker.io", "quay.io"]

[[registry]]
prefix = "docker.io"
location = "docker.io"
insecure = false
blocked = false

[[registry]]
prefix = "quay.io"
location = "quay.io"
insecure = false
blocked = false

[[registry]]
prefix = "minio"
location = "docker.io/minio"
insecure = false
blocked = false

[[registry]]
prefix = "postgres"
location = "docker.io/library/postgres"
insecure = false
blocked = false

[[registry]]
prefix = "mongo"
location = "docker.io/library/mongo"
insecure = false
blocked = false

[[registry]]
prefix = "portainer"
location = "docker.io/portainer"
insecure = false
blocked = false

[[registry]]
prefix = "milvusdb"
location = "docker.io/milvusdb"
insecure = false
blocked = false

[[registry]]
prefix = "pgadmin"
location = "docker.io/dpage"
insecure = false
blocked = false

[[registry]]
prefix = "grafana"
location = "docker.io/grafana"
insecure = false
blocked = false

[[registry]]
prefix = "prometheus"
location = "docker.io/prom"
insecure = false
blocked = false
EOF

echo "✅ 容器註冊表配置已更新"

# 重新載入 Podman 配置
if command -v podman &> /dev/null; then
    echo "🔄 重新載入 Podman 配置..."
    podman system reset --force > /dev/null 2>&1
    echo "✅ Podman 配置已重新載入"
fi

echo ""
echo "🎉 Podman 容器註冊表配置修復完成！"
echo ""
echo "現在您可以："
echo "1. 重新執行 ./start_fastapi_proxy.sh start"
echo "2. 或使用 ./quick_fastapi_start.sh 只啟動 FastAPI 反向代理"
echo ""
echo "💡 提示：如果仍有問題，可以嘗試："
echo "   podman pull docker.io/minio/minio:latest"
echo "   podman pull docker.io/library/postgres:15"
echo "   podman pull docker.io/library/mongo:7" 