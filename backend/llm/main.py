"""
LLM 服務主程式
整合 Qwen3、bge-m3 和 Deepseek R1 模型
"""

import os
import logging
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModel
import torch
from dotenv import load_dotenv
import httpx
from langfuse import Langfuse

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化 FastAPI
app = FastAPI(title="LLM Service")

# 初始化 Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
)

class LLMRequest(BaseModel):
    """LLM 請求模型"""
    prompt: str
    model: str = "qwen"  # 預設使用 Qwen
    max_tokens: int = 2048
    temperature: float = 0.7

class EmbeddingRequest(BaseModel):
    """向量嵌入請求模型"""
    text: str
    model: str = "bge-m3"  # 預設使用 bge-m3

# 載入模型
def load_models():
    """載入所有模型"""
    models = {}
    
    # 檢查模型路徑是否存在
    qwen_path = os.getenv("QWEN_MODEL_PATH", "/app/models/external/qwen")
    bge_path = os.getenv("BGE_MODEL_PATH", "/app/models/external/bge-m3")
    deepseek_path = os.getenv("DEEPSEEK_MODEL_PATH", "/app/models/external/deepseek")
    
    # 載入 Qwen 模型（如果存在）
    if os.path.exists(qwen_path) and os.path.exists(os.path.join(qwen_path, "config.json")):
        try:
            models["qwen"] = {
                "tokenizer": AutoTokenizer.from_pretrained(qwen_path),
                "model": AutoModel.from_pretrained(qwen_path)
            }
            logging.info(f"Qwen 模型載入成功: {qwen_path}")
        except Exception as e:
            logging.error(f"Qwen 模型載入失敗: {e}")
    else:
        logging.warning(f"Qwen 模型路徑不存在或無效: {qwen_path}")
    
    # 載入 BGE-M3 模型（如果存在）
    if os.path.exists(bge_path) and os.path.exists(os.path.join(bge_path, "config.json")):
        try:
            models["bge-m3"] = {
                "tokenizer": AutoTokenizer.from_pretrained(bge_path),
                "model": AutoModel.from_pretrained(bge_path)
            }
            logging.info(f"BGE-M3 模型載入成功: {bge_path}")
        except Exception as e:
            logging.error(f"BGE-M3 模型載入失敗: {e}")
    else:
        logging.warning(f"BGE-M3 模型路徑不存在或無效: {bge_path}")
    
    # 載入 Deepseek 模型（如果存在）
    if os.path.exists(deepseek_path) and os.path.exists(os.path.join(deepseek_path, "config.json")):
        try:
            models["deepseek"] = {
                "tokenizer": AutoTokenizer.from_pretrained(deepseek_path),
                "model": AutoModel.from_pretrained(deepseek_path)
            }
            logging.info(f"Deepseek 模型載入成功: {deepseek_path}")
        except Exception as e:
            logging.error(f"Deepseek 模型載入失敗: {e}")
    else:
        logging.warning(f"Deepseek 模型路徑不存在或無效: {deepseek_path}")
    
    if not models:
        logging.warning("沒有載入任何模型，服務將使用默認配置")
    
    return models

# 初始化模型
models = load_models()

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "models": list(models.keys())}

@app.post("/generate")
async def generate_text(request: LLMRequest):
    """生成文字端點"""
    try:
        with langfuse.trace(name="generate_text") as trace:
            # 使用 Ollama API
            async with httpx.AsyncClient() as client:
                # 修正模型名稱格式
                model_name = request.model
                if model_name == "qwen":
                    model_name = "qwen3:8b"  # 使用實際的模型名稱
                
                response = await client.post(
                    f"http://{os.getenv('OLLAMA_HOST', 'localhost')}:{os.getenv('OLLAMA_PORT', '11434')}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": request.prompt,
                        "stream": False,
                        "options": {
                            "num_predict": request.max_tokens,
                            "temperature": request.temperature
                        }
                    },
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Ollama API 錯誤")

                result = response.json()
                trace.span(
                    name="ollama_generation",
                    input={"prompt": request.prompt},
                    output={"response": result}
                )

                return result

    except Exception as e:
        logger.error(f"生成文字失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed")
async def get_embedding(request: EmbeddingRequest):
    """獲取向量嵌入端點"""
    try:
        with langfuse.trace(name="get_embedding") as trace:
            # 檢查模型是否可用
            if request.model not in models:
                raise HTTPException(status_code=400, detail=f"模型 {request.model} 不可用")

            model = models[request.model]
            inputs = model["tokenizer"](
                request.text,
                return_tensors="pt",
                padding=True,
                truncation=True
            )

            with torch.no_grad():
                outputs = model["model"](**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1)

            trace.span(
                name="embedding_generation",
                input={"text": request.text},
                output={"embedding_shape": embeddings.shape}
            )

            return {"embedding": embeddings.tolist()}

    except Exception as e:
        logger.error(f"生成向量嵌入失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 