"""
前端 FastAPI 反向代理主程式
- /         服務首頁 index.html
- /chat     反向代理 Streamlit 聊天介面
"""

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import httpx
import os

app = FastAPI(title="Podwise 前端 FastAPI 反向代理")

# 靜態檔案服務（assets, images, ...）
if os.path.isdir("assets"):
    app.mount("/assets", StaticFiles(directory="assets"), name="assets")
if os.path.isdir("images"):
    app.mount("/images", StaticFiles(directory="images"), name="images")

# 首頁 index.html
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """回傳首頁 index.html"""
    return FileResponse("index.html")

# 反向代理 /chat 到 Streamlit
@app.api_route("/chat/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy_chat(request: Request, path: str = ""):
    """
    反向代理 /chat 路徑到本地 Streamlit 服務
    """
    streamlit_url = f"http://localhost:8501/{path}"
    async with httpx.AsyncClient() as client:
        proxy_req = client.build_request(
            request.method, streamlit_url,
            headers=request.headers.raw,
            content=await request.body()
        )
        proxy_resp = await client.send(proxy_req, stream=True)
        return StreamingResponse(
            proxy_resp.aiter_raw(),
            status_code=proxy_resp.status_code,
            headers=proxy_resp.headers
        )

# 直接跳轉 /chat 到 Streamlit 首頁
@app.get("/chat", response_class=HTMLResponse)
async def chat_redirect():
    """跳轉 /chat 到 Streamlit 首頁"""
    return RedirectResponse(url="/chat/")

# 其他靜態頁面
@app.get("/{page_name}.html", response_class=HTMLResponse)
async def serve_page(page_name: str):
    """回傳其他靜態頁面"""
    file_path = f"{page_name}.html"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(content="找不到頁面", status_code=404) 