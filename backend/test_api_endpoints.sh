#!/bin/bash

# FastAPI 反向代理端點測試腳本

BASE_URL="http://localhost:8008"

echo "🧪 FastAPI 反向代理端點測試"
echo "================================"

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 測試函數
test_endpoint() {
    local endpoint=$1
    local description=$2
    local method=${3:-GET}
    
    echo -n "測試 $description... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$BASE_URL$endpoint")
    fi
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ 成功 (HTTP $response)${NC}"
    elif [ "$response" = "404" ]; then
        echo -e "${YELLOW}⚠️  未找到 (HTTP $response)${NC}"
    elif [ "$response" = "500" ]; then
        echo -e "${RED}❌ 服務器錯誤 (HTTP $response)${NC}"
    else
        echo -e "${YELLOW}⚠️  其他狀態 (HTTP $response)${NC}"
    fi
}

# 檢查服務是否運行
echo "🔍 檢查服務狀態..."
if curl -s "$BASE_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ FastAPI 反向代理正在運行${NC}"
else
    echo -e "${RED}❌ FastAPI 反向代理未運行，請先啟動服務${NC}"
    echo "使用命令: ./test_fastapi_local.sh"
    exit 1
fi

echo ""
echo "📋 開始端點測試..."
echo ""

# 基本端點測試
echo "=== 基本端點測試 ==="
test_endpoint "/" "主頁面"
test_endpoint "/index.html" "首頁"
test_endpoint "/podri.html" "Podri 頁面"
test_endpoint "/health" "健康檢查"
test_endpoint "/api/v1/services" "服務狀態"

echo ""
echo "=== 靜態檔案測試 ==="
test_endpoint "/assets/css/main.css" "CSS 檔案"
test_endpoint "/assets/js/jquery.min.js" "JavaScript 檔案"
test_endpoint "/images/favicon.ico" "Favicon"

echo ""
echo "=== API 端點測試 ==="
test_endpoint "/api/user/check/test123" "用戶檢查"
test_endpoint "/api/generate-podwise-id" "生成用戶 ID" "POST"
test_endpoint "/api/category-tags/business" "類別標籤"
test_endpoint "/api/one-minutes-episodes?category=business" "一分鐘節目"

echo ""
echo "=== 代理端點測試 (預期失敗，因為後端服務未運行) ==="
test_endpoint "/api/tts/health" "TTS 服務代理"
test_endpoint "/api/stt/health" "STT 服務代理"
test_endpoint "/api/rag/health" "RAG 服務代理"
test_endpoint "/api/ml/health" "ML 服務代理"

echo ""
echo "=== 文檔端點測試 ==="
test_endpoint "/docs" "API 文檔"
test_endpoint "/redoc" "ReDoc 文檔"
test_endpoint "/openapi.json" "OpenAPI 規範"

echo ""
echo "================================"
echo "🧪 測試完成！"
echo ""
echo "💡 測試結果說明："
echo "  ✅ 成功 - 端點正常響應"
echo "  ⚠️  未找到 - 端點不存在或路徑錯誤"
echo "  ❌ 服務器錯誤 - 內部錯誤"
echo "  ⚠️  其他狀態 - 需要進一步檢查"
echo ""
echo "🌐 可以在瀏覽器中訪問以下地址進行手動測試："
echo "  主頁面: $BASE_URL"
echo "  API 文檔: $BASE_URL/docs"
echo "  健康檢查: $BASE_URL/health" 