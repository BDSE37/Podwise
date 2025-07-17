#!/bin/bash

# 台灣模型轉換腳本
# 將 Qwen2.5-Taiwan-7B-Instruct 轉換為 GGUF 格式

set -e

echo "🚀 開始轉換台灣模型..."

# 檢查模型目錄
MODEL_DIR="../Qwen2.5-Taiwan-7B-Instruct"
if [ ! -d "$MODEL_DIR" ]; then
    echo "❌ 模型目錄不存在: $MODEL_DIR"
    exit 1
fi

# 檢查模型檔案
echo "📁 檢查模型檔案..."
if [ ! -f "$MODEL_DIR/model-00001-of-00004.safetensors" ]; then
    echo "⚠️  模型檔案可能還在下載中，請等待 LFS 下載完成"
    echo "💡 可以執行: cd $MODEL_DIR && git lfs pull"
    exit 1
fi

# 安裝依賴
echo "📦 安裝轉換依賴..."
pip install -r requirements.txt

# 執行轉換
echo "🔄 開始轉換為 GGUF 格式..."
python3 convert_hf_to_gguf.py \
    --model-dir "$MODEL_DIR" \
    --outfile "qwen2.5-taiwan-7b-instruct.gguf" \
    --outtype q4_k_m

echo "✅ 轉換完成！"

# 創建 Modelfile
echo "📝 創建 Modelfile..."
cat > qwen2.5-taiwan-7b-instruct.modelfile << 'EOF'
FROM ./qwen2.5-taiwan-7b-instruct.gguf

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""

PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>"
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

SYSTEM """你是一個專門針對台灣繁體中文優化的 AI 助手。你擅長：
1. 使用正確的繁體中文用詞和語法
2. 理解台灣的文化背景和社會脈絡
3. 提供符合台灣本地需求的建議和解答
4. 使用台灣常用的表達方式和慣用語

請用友善、專業且符合台灣文化的態度來回應。"""
EOF

echo "✅ Modelfile 創建完成！"

# 顯示檔案大小
echo "📊 轉換結果："
ls -lh qwen2.5-taiwan-7b-instruct.gguf
ls -la qwen2.5-taiwan-7b-instruct.modelfile

echo "🎉 轉換流程完成！"
echo "📋 下一步："
echo "1. 將 .gguf 檔案複製到 Ollama 容器"
echo "2. 將 .modelfile 複製到 Ollama 容器"
echo "3. 在 Ollama 容器中執行：ollama create qwen2.5-taiwan-7b-instruct -f /path/to/modelfile" 