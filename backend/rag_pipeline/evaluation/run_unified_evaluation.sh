#!/bin/bash

# 統一 RAG 評估執行腳本

echo "=== 統一 RAG 評估系統 ==="
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
    "unified_rag_evaluator.py"
    "enhanced_rag_evaluator.py"
    "requirements.txt"
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
mkdir -p unified_results
echo "✅ 輸出目錄已創建"
echo ""

# 選擇執行模式
echo "請選擇執行模式:"
echo "1. 快速測試 (推薦)"
echo "2. 完整評估"
echo "3. Podwise 專用評估"
echo "4. 自定義評估"
echo ""

read -p "請輸入選項 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🚀 執行快速測試..."
        python3 -c "
import asyncio
from unified_rag_evaluator import test_unified_evaluator
asyncio.run(test_unified_evaluator())
"
        ;;
    2)
        echo ""
        echo "🚀 執行完整評估..."
        echo "注意: 這可能需要較長時間和較多 API 調用"
        read -p "確認繼續? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            python3 -c "
import asyncio
from unified_rag_evaluator import UnifiedRAGEvaluator

async def full_evaluation():
    evaluator = UnifiedRAGEvaluator(use_mock_services=True)
    
    # 創建 Podwise 合成資料集
    qa_pairs = evaluator.create_podwise_synthetic_dataset(num_questions=10)
    
    if qa_pairs:
        # 轉換為評估資料集格式
        eval_dataset = []
        for qa in qa_pairs:
            eval_dataset.append({
                'input': qa['question'],
                'expected': qa['answer'],
                'metadata': {'reference': qa['reference']}
            })
        
        # 執行各種評估
        print('🔍 執行 Baseline 評估...')
        baseline_results = evaluator.baseline_evaluation(eval_dataset)
        
        print('🔍 執行 Naive RAG 評估...')
        naive_results = evaluator.naive_rag_evaluation(eval_dataset)
        
        print('🔍 執行增強版評估...')
        enhanced_results = await evaluator.evaluate_batch([qa['question'] for qa in qa_pairs])
        
        # 生成報告
        evaluator.generate_comparison_report(enhanced_results, 'unified_results/full_evaluation_report.txt')
        
        print('✅ 完整評估完成')
    else:
        print('❌ 無法創建合成資料集')

asyncio.run(full_evaluation())
"
        else
            echo "已取消"
            exit 0
        fi
        ;;
    3)
        echo ""
        echo "🚀 Podwise 專用評估模式"
        python3 -c "
import asyncio
from unified_rag_evaluator import UnifiedRAGEvaluator

async def podwise_evaluation():
    evaluator = UnifiedRAGEvaluator(use_mock_services=True)
    
    # 創建 Podwise 合成資料集
    qa_pairs = evaluator.create_podwise_synthetic_dataset(num_questions=5)
    
    if qa_pairs:
        print(f'✅ 成功創建 {len(qa_pairs)} 個問答對')
        
        # 執行評估
        questions = [qa['question'] for qa in qa_pairs]
        results = await evaluator.evaluate_batch(questions)
        
        # 生成報告
        evaluator.generate_comparison_report(results, 'unified_results/podwise_evaluation_report.txt')
        
        print('✅ Podwise 評估完成')
    else:
        print('❌ 無法創建 Podwise 合成資料集')

asyncio.run(podwise_evaluation())
"
        ;;
    4)
        echo ""
        echo "🚀 自定義評估模式"
        echo "請手動執行以下命令:"
        echo ""
        echo "python3 -c \""
        echo "import asyncio"
        echo "from unified_rag_evaluator import UnifiedRAGEvaluator"
        echo ""
        echo "async def custom_evaluation():"
        echo "    evaluator = UnifiedRAGEvaluator(use_mock_services=True)"
        echo "    # 在這裡添加您的自定義評估邏輯"
        echo "    pass"
        echo ""
        echo "asyncio.run(custom_evaluation())"
        echo "\""
        ;;
    *)
        echo "❌ 無效選項"
        exit 1
        ;;
esac

echo ""
echo "=== 評估完成 ==="
echo "結果保存在 unified_results/ 目錄中"
echo ""

# 檢查是否有結果文件
if [ -f "unified_results/unified_rag_evaluation_report.txt" ]; then
    echo "📊 評估結果摘要:"
    python3 -c "
import json
try:
    with open('unified_results/unified_rag_evaluation_report.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    print(content)
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