"""
LLM 服務的 Streamlit 聊天介面
整合 Langfuse 追蹤功能
"""

import streamlit as st
import os
import sys
from datetime import datetime
import json
from typing import Dict, List, Optional
import uuid

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 導入配置
from backend.config.mongo_config import MONGO_CONFIG, MONGO_URI
from backend.config.db_config import POSTGRES_CONFIG

# 導入資料庫連接模組
import pymongo
import psycopg2
from pymilvus import connections, Collection

# 導入 Langfuse
from langfuse import Langfuse

# 設置頁面配置
st.set_page_config(
    page_title="Podwise Chat",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "trace_id" not in st.session_state:
    st.session_state.trace_id = None

class ChatInterface:
    """聊天介面類別"""
    
    def __init__(self):
        """初始化資料庫連接和 Langfuse"""
        # 連接 PostgreSQL
        self.pg_conn = psycopg2.connect(
            host=POSTGRES_CONFIG['host'],
            port=POSTGRES_CONFIG['port'],
            database=POSTGRES_CONFIG['database'],
            user=POSTGRES_CONFIG['user'],
            password=POSTGRES_CONFIG['password']
        )
        
        # 連接 MongoDB
        self.mongo_client = pymongo.MongoClient(MONGO_URI)
        self.mongo_db = self.mongo_client[MONGO_CONFIG['database']]
        
        # 連接 Milvus
        connections.connect(
            alias="default",
            host=os.getenv("MILVUS_HOST", "milvus"),
            port=int(os.getenv("MILVUS_PORT", "19530"))
        )
        
        # 初始化 Langfuse
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "http://langfuse:3000")
        )
    
    def create_chat_trace(self, user_id: str, initial_message: str) -> str:
        """創建聊天追蹤"""
        trace = self.langfuse.trace(
            name="chat_session",
            metadata={
                "user_id": user_id,
                "session_id": str(uuid.uuid4()),
                "initial_message": initial_message[:100]  # 只記錄前100個字符
            }
        )
        return trace.id
    
    def log_user_message(self, trace_id: str, message: str, user_id: str):
        """記錄用戶消息"""
        self.langfuse.span(
            trace_id=trace_id,
            name="user_message",
            input={
                "message": message,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_assistant_response(self, trace_id: str, response: str, model_used: str = "unknown"):
        """記錄助手回應"""
        self.langfuse.span(
            trace_id=trace_id,
            name="assistant_response",
            input={
                "response": response,
                "model_used": model_used,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def get_podcast_suggestions(self, query: str) -> List[Dict]:
        """獲取播客建議"""
        try:
            with self.pg_conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.name, p.description, e.title, e.description
                    FROM podcasts p
                    JOIN episodes e ON p.id = e.podcast_id
                    WHERE p.name ILIKE %s OR e.title ILIKE %s
                    LIMIT 5
                """, (f"%{query}%", f"%{query}%"))
                return [{
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "episode_title": row[3],
                    "episode_description": row[4]
                } for row in cur.fetchall()]
        except Exception as e:
            st.error(f"獲取播客建議時發生錯誤: {str(e)}")
            return []
    
    def get_chat_history(self, user_id: str) -> List[Dict]:
        """獲取聊天歷史"""
        try:
            collection = self.mongo_db["chat_history"]
            return list(collection.find(
                {"user_id": user_id},
                sort=[("timestamp", -1)],
                limit=10
            ))
        except Exception as e:
            st.error(f"獲取聊天歷史時發生錯誤: {str(e)}")
            return []
    
    def save_chat_history(self, user_id: str, message: Dict):
        """保存聊天歷史"""
        try:
            collection = self.mongo_db["chat_history"]
            collection.insert_one({
                "user_id": user_id,
                "message": message,
                "timestamp": datetime.utcnow()
            })
        except Exception as e:
            st.error(f"保存聊天歷史時發生錯誤: {str(e)}")
    
    def close(self):
        """關閉資料庫連接"""
        self.pg_conn.close()
        self.mongo_client.close()
        connections.disconnect("default")

def main():
    """主函數"""
    st.title("🎙️ Podwise Chat")
    
    # 初始化聊天介面
    chat = ChatInterface()
    
    # 側邊欄
    with st.sidebar:
        st.header("設定")
        user_id = st.text_input("用戶 ID", value="bdse37")
        
        st.header("最近對話")
        chat_history = chat.get_chat_history(user_id)
        for history in chat_history:
            st.text(f"{history['timestamp']}: {history['message']['content'][:50]}...")
    
    # 主要聊天區域
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 聊天輸入
    if prompt := st.chat_input("輸入您的問題..."):
        # 創建或使用現有的追蹤
        if not st.session_state.trace_id:
            st.session_state.trace_id = chat.create_chat_trace(user_id, prompt)
        
        # 記錄用戶消息
        chat.log_user_message(st.session_state.trace_id, prompt, user_id)
        
        # 添加用戶消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 獲取播客建議
        suggestions = chat.get_podcast_suggestions(prompt)
        
        # 生成回應
        with st.chat_message("assistant"):
            response = f"我找到以下相關的播客：\n\n"
            for suggestion in suggestions:
                response += f"📻 **{suggestion['name']}**\n"
                response += f"📝 {suggestion['description']}\n"
                response += f"🎧 集數：{suggestion['episode_title']}\n"
                response += f"📄 {suggestion['episode_description']}\n\n"
            
            st.markdown(response)
            
            # 記錄助手回應
            chat.log_assistant_response(st.session_state.trace_id, response, "llm_service")
            
            # 保存聊天歷史
            chat.save_chat_history(user_id, {
                "role": "assistant",
                "content": response,
                "trace_id": st.session_state.trace_id
            })
            
            # 更新 session state
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # 關閉連接
    chat.close()

if __name__ == "__main__":
    main() 