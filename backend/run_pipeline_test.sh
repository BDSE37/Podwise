#!/bin/bash

# 切斷、貼標、轉向量測試執行腳本

echo "=== Podwise 管道測試腳本 ==="
echo "1. 文本清理測試"
echo "2. 簡化管道測試（樣本資料）"
echo "3. 簡化管道測試（MongoDB資料）"
echo "4. 完整管道測試"
echo "5. 所有測試"
echo ""

read -p "請選擇測試類型 (1-5): " choice

case $choice in
    1)
        echo "執行文本清理測試..."
        python test_text_cleaning.py
        ;;
    2)
        echo "執行簡化管道測試（樣本資料）..."
        python test_simple_pipeline.py
        ;;
    3)
        echo "執行簡化管道測試（MongoDB資料）..."
        python test_simple_pipeline.py --mongo
        ;;
    4)
        echo "執行完整管道測試..."
        python test_chunk_tag_vector.py
        ;;
    5)
        echo "執行所有測試..."
        echo "=== 1. 文本清理測試 ==="
        python test_text_cleaning.py
        echo ""
        echo "=== 2. 簡化管道測試（樣本資料）==="
        python test_simple_pipeline.py
        echo ""
        echo "=== 3. 簡化管道測試（MongoDB資料）==="
        python test_simple_pipeline.py --mongo
        ;;
    *)
        echo "無效選擇，請重新運行腳本"
        exit 1
        ;;
esac

echo ""
echo "測試完成！"
echo "請檢查日誌文件："
echo "- test_text_cleaning.py 的輸出"
echo "- simple_pipeline_test.log"
echo "- test_chunk_tag_vector.log" 