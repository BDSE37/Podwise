#!/bin/bash

# 播客標題更新執行腳本

echo "=== 播客標題更新工具 ==="
echo "將 collection 1500839292 中的節目標題改為 EPXXX_股癌 格式"
echo ""

# 預設配置
COLLECTION_ID="1500839292"
COLLECTION_NAME="股癌"
MONGO_HOST="localhost"
MONGO_PORT="27017"
MONGO_DB="podwise"
MONGO_COLLECTION="podcasts"

echo "當前配置："
echo "  Collection ID: $COLLECTION_ID"
echo "  Collection 名稱: $COLLECTION_NAME"
echo "  MongoDB: $MONGO_HOST:$MONGO_PORT/$MONGO_DB.$MONGO_COLLECTION"
echo ""

echo "請選擇操作："
echo "1. 預覽更新內容（不執行實際更新）"
echo "2. 執行更新"
echo "3. 自訂配置"
echo ""

read -p "請選擇 (1-3): " choice

case $choice in
    1)
        echo "執行預覽模式..."
        python update_podcast_titles.py \
            --collection-id "$COLLECTION_ID" \
            --collection-name "$COLLECTION_NAME" \
            --host "$MONGO_HOST" \
            --port "$MONGO_PORT" \
            --database "$MONGO_DB" \
            --collection "$MONGO_COLLECTION" \
            --preview
        ;;
    2)
        echo "執行更新..."
        python update_podcast_titles.py \
            --collection-id "$COLLECTION_ID" \
            --collection-name "$COLLECTION_NAME" \
            --host "$MONGO_HOST" \
            --port "$MONGO_PORT" \
            --database "$MONGO_DB" \
            --collection "$MONGO_COLLECTION"
        ;;
    3)
        echo "自訂配置："
        read -p "Collection ID (預設: $COLLECTION_ID): " input_collection_id
        read -p "Collection 名稱 (預設: $COLLECTION_NAME): " input_collection_name
        read -p "MongoDB 主機 (預設: $MONGO_HOST): " input_host
        read -p "MongoDB 端口 (預設: $MONGO_PORT): " input_port
        read -p "資料庫名稱 (預設: $MONGO_DB): " input_db
        read -p "Collection 名稱 (預設: $MONGO_COLLECTION): " input_collection
        
        # 使用輸入值或預設值
        COLLECTION_ID=${input_collection_id:-$COLLECTION_ID}
        COLLECTION_NAME=${input_collection_name:-$COLLECTION_NAME}
        MONGO_HOST=${input_host:-$MONGO_HOST}
        MONGO_PORT=${input_port:-$MONGO_PORT}
        MONGO_DB=${input_db:-$MONGO_DB}
        MONGO_COLLECTION=${input_collection:-$MONGO_COLLECTION}
        
        echo ""
        echo "更新後配置："
        echo "  Collection ID: $COLLECTION_ID"
        echo "  Collection 名稱: $COLLECTION_NAME"
        echo "  MongoDB: $MONGO_HOST:$MONGO_PORT/$MONGO_DB.$MONGO_COLLECTION"
        echo ""
        
        read -p "是否執行更新？(y/N): " confirm
        if [[ $confirm == "y" || $confirm == "Y" ]]; then
            python update_podcast_titles.py \
                --collection-id "$COLLECTION_ID" \
                --collection-name "$COLLECTION_NAME" \
                --host "$MONGO_HOST" \
                --port "$MONGO_PORT" \
                --database "$MONGO_DB" \
                --collection "$MONGO_COLLECTION"
        else
            echo "取消更新"
        fi
        ;;
    *)
        echo "無效選擇"
        exit 1
        ;;
esac

echo ""
echo "操作完成！"
echo "請檢查日誌文件：update_titles.log" 