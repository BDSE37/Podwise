#!/bin/bash

# Qwen 模型下載腳本
# 用於在 Ollama 容器中下載所需的 LLM 模型

set -e

echo "🚀 開始下載 Qwen 模型..."

# 等待 Ollama 服務啟動
echo "⏳ 等待 Ollama 服務啟動..."
sleep 30

# 檢查 Ollama 服務狀態
echo "🔍 檢查 Ollama 服務狀態..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama 服務未啟動，請檢查服務狀態"
    exit 1
fi

echo "✅ Ollama 服務正常運行"

# 下載 Qwen2.5-Taiwan-8B-Instruct (第一優先)
echo "📥 下載 Qwen2.5-Taiwan-8B-Instruct..."
ollama pull weiren119/Qwen2.5-Taiwan-8B-Instruct

# 下載 Qwen2.5-8B-Instruct (第二優先)
echo "📥 下載 Qwen2.5-8B-Instruct..."
ollama pull Qwen/Qwen2.5-8B-Instruct

# 下載 Qwen3:8b (備用)
echo "📥 下載 Qwen3:8b..."
ollama pull qwen2.5:8b

# 列出已下載的模型
echo "📋 已下載的模型列表："
ollama list

echo "✅ 所有模型下載完成！" 