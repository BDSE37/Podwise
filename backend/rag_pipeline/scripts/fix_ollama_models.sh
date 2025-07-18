#!/bin/bash

# 快速修復 Ollama 模型腳本
# 解決向量維度不匹配和 LLM 模型不存在問題

set -e

echo "🔧 開始修復 Ollama 模型..."

# 檢查 Ollama 服務
echo "🔍 檢查 Ollama 服務狀態..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama 服務未啟動，請先啟動 Ollama"
    exit 1
fi

echo "✅ Ollama 服務正常"

# 下載必要的嵌入模型
echo "📥 下載嵌入模型..."

echo "📥 下載 BGE-M3 嵌入模型 (1024維)..."
ollama pull BAAI/bge-m3

echo "📥 下載 Nomic 嵌入模型 (備用)..."
ollama pull nomic-embed-text

echo "📥 下載 All-MiniLM 嵌入模型 (備用)..."
ollama pull all-minilm

# 下載必要的 LLM 模型
echo "📥 下載 LLM 模型..."

echo "📥 下載台灣版本模型..."
ollama pull weiren119/Qwen2.5-Taiwan-8B-Instruct

echo "📥 下載 Qwen2.5 模型..."
ollama pull Qwen/Qwen2.5-8B-Instruct

echo "📥 下載 Qwen3 模型..."
ollama pull qwen2.5:8b

echo "📥 下載 GPT-3.5 模型..."
ollama pull gpt-3.5-turbo

# 驗證模型
echo "✅ 驗證模型..."
ollama list

echo "🧪 測試台灣版本模型..."
ollama run qwen2.5-taiwan-7b-instruct "你好，請用繁體中文回答：你是誰？" --timeout 30

echo "🧪 測試 BGE-M3 嵌入模型..."
curl -X POST http://localhost:11434/api/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model": "bge-m3", "prompt": "測試文本"}' | jq '.embedding | length'

echo "🎉 模型修復完成！"
echo ""
echo "📋 可用模型:"
ollama list
echo ""
echo "🌐 Ollama 服務: http://localhost:11434"
echo "📚 主要模型:"
echo "   - qwen2.5-taiwan-7b-instruct (台灣版本)"
echo "   - bge-m3 (1024維嵌入)"
echo ""
echo "🧪 測試命令:"
echo "   ollama run qwen2.5-taiwan-7b-instruct '你好'"
echo "   curl -X POST http://localhost:11434/api/embeddings -H 'Content-Type: application/json' -d '{\"model\": \"bge-m3\", \"prompt\": \"測試\"}'" 