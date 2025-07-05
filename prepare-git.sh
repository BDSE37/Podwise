#!/bin/bash

# ===============================
# 本腳本不會刪除或動到 .env 檔案
# .env 僅本地保留，永不上傳 GitHub
# ===============================

# 準備 Git 提交腳本
echo "🚀 準備 Git 提交..."

# 添加新檔案
echo "📁 添加新檔案..."
git add README.md
git add .gitignore
git add deploy/k8s/ollama/
git add backend/rag_pipeline/
git add deploy/k8s/rag-pipeline/
git add deploy/podman/
git add frontend/chat/services/
git add frontend/pages/assets/
git add frontend/pages/LICENSE.txt

# 添加修改的檔案
echo "📝 添加修改的檔案..."
git add backend/stt/
git add backend/tts/
git add frontend/chat/
git add frontend/pages/
git add deploy/k8s/n8n/

# 刪除不需要的檔案
echo "🗑️ 刪除不需要的檔案..."
git rm -f backend/rag_pipeline/app/progressive_integration.py
git rm -f backend/rag_pipeline/app/simple_test.py
git rm -f backend/rag_pipeline/run_local_test.py
git rm -f backend/rag_pipeline/start_local.py
git rm -f backend/rag_pipeline/start_local_port8005.py
git rm -f backend/rag_pipeline/start_local_port8006.py
git rm -f backend/rag_pipeline/start_progressive.py
git rm -f backend/rag_pipeline/start_simple_test.py
git rm -f backend/rag_pipeline/test_config.py
git rm -f backend/rag_pipeline/test_langfuse.py
git rm -f backend/rag_pipeline/test_with_langfuse.py
git rm -f backend/stt/streamlit_app.py
git rm -f backend/stt/stt_service.py
git rm -f backend/stt/whisper_stt.py
git rm -f backend/tts/application.py
git rm -f backend/tts/test_tts.json
git rm -f docker-compose.tts-training.yaml
git rm -f frontend/Makefile
git rm -f main.py
git rm -f models/taiwan/Modelfile
git rm -f project_audit_report.md

# 刪除不需要的圖片檔案
git rm -f frontend/images/arrow-left.png
git rm -f frontend/images/delete.png
git rm -f frontend/images/financial-profit.png
git rm -f frontend/images/financial-profit_golden.png
git rm -f frontend/images/home.png
git rm -f frontend/images/logo_black.png
git rm -f frontend/images/logo_red.png
git rm -f frontend/images/logo_white.png
git rm -f frontend/images/pic*.jpg
git rm -f frontend/images/play_blue.png
git rm -f frontend/images/play_gray.png
git rm -f frontend/images/podcasts.png
git rm -f frontend/images/podcasts_golden.png
git rm -f frontend/images/podcasts_pink.png
git rm -f frontend/images/previous.png
git rm -f frontend/images/school.png
git rm -f frontend/images/school_golden.png
git rm -f "frontend/images/天下雜誌.png"
git rm -f "frontend/images/導入.png"
git rm -f "frontend/images/科技新聞.png"
git rm -f "frontend/images/科技新聞Techwav.png"
git rm -f "frontend/images/財經.png"

# 刪除不需要的部署檔案
git rm -f deploy/k8s/n8n/my-n8n-deployment.yaml
git rm -f deploy/k8s/n8n/my-n8n-live.yaml
git rm -f deploy/k8s/n8n/n8n-ingress.yaml
git rm -f deploy/k8s/n8n/n8n-serviceaccount.yaml
git rm -f deploy/k8s/podri_chat/podri-chat-deployment.yaml
git rm -f deploy/k8s/podri_chat/podri-chat-pvc.yaml

echo "✅ Git 準備完成！"
echo ""
echo "📋 下一步："
echo "1. 檢查狀態: git status"
echo "2. 提交變更: git commit -m '整理專案結構，移除不必要檔案'"
echo "3. 推送到 GitHub: git push origin main" 