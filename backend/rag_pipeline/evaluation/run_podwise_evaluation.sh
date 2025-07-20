#!/bin/bash

# Podwise RAG 評估執行腳本

echo "=== Podwise RAG 評估系統 ==="
echo ""

# 檢查環境變數
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ 錯誤: 未設定 OPENAI_API_KEY 環境變數"
    echo "請執行: export OPENAI_API_KEY='your_api_key'"
    exit 1
fi

echo "✅ OpenAI API Key 已設定"
echo ""

# 檢查 Python 環境
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤: 未找到 python3"
    exit 1
fi

echo "✅ Python3 已安裝"
echo ""

# 檢查必要文件
required_files=(
    "rag_evaluator.py"
    "podwise_vector_search.py"
    "podwise_rag_evaluation.py"
    "lightweight_podwise_test.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 錯誤: 缺少必要文件 $file"
        exit 1
    fi
done

echo "✅ 所有必要文件都存在"
echo ""

# 創建輸出目錄
mkdir -p podwise_results
echo "✅ 輸出目錄已創建"
echo ""

# 選擇執行模式
echo "請選擇執行模式:"
echo "1. 快速測試 (推薦)"
echo "2. 完整評估"
echo "3. 自定義評估"
echo ""

read -p "請輸入選項 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 執行快速測試..."
        python3 lightweight_podwise_test.py
        ;;
    2)
        echo ""
        echo "🚀 執行完整評估..."
        echo "注意: 這可能需要較長時間和較多 API 調用"
        read -p "確認繼續? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            python3 podwise_rag_evaluation.py
        else
            echo "已取消"
            exit 0
        fi
        ;;
    3)
        echo ""
        echo "🚀 自定義評估模式"
        echo "請手動執行以下命令:"
        echo ""
        echo "python3 -c \""
        echo "from podwise_rag_evaluation import PodwiseRAGEvaluator;"
        echo "evaluator = PodwiseRAGEvaluator();"
        echo "results = evaluator.evaluate_podwise_rag(num_questions=3);"
        echo "print(results)"
        echo "\""
        ;;
    *)
        echo "❌ 無效選項"
        exit 1
        ;;
esac

echo ""
echo "=== 評估完成 ==="
echo "結果保存在 podwise_results/ 目錄中"
echo ""

# 檢查是否有結果文件
if [ -f "podwise_results/podwise_rag_evaluation_results.json" ]; then
    echo "📊 評估結果摘要:"
    python3 -c "
import json
try:
    with open('podwise_results/podwise_rag_evaluation_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    summary = data.get('summary', {})
    for method, metrics in summary.items():
        print(f'\n{method.upper()}:')
        for metric, value in metrics.items():
            if isinstance(value, float):
                print(f'  {metric}: {value:.4f}')
            else:
                print(f'  {metric}: {value}')
except Exception as e:
    print(f'無法讀取結果文件: {e}')
"
fi

echo ""
echo "🎯 下一步建議:"
echo "1. 查看詳細結果文件"
echo "2. 調整評估參數"
echo "3. 分析評估指標"
echo "4. 優化 RAG 系統" 