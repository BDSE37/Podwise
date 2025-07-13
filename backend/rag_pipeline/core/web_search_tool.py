#!/usr/bin/env python3
"""
Web Search Tool - 使用 OpenAI API 的完整實現

提供網路搜尋功能，使用 OpenAI API 進行智能搜尋和內容生成。
"""

import logging
import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

# 添加路徑以便導入配置
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from config.integrated_config import get_config
    from openai import OpenAI
except ImportError as e:
    logging.warning(f"無法導入 OpenAI 或配置: {e}")

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Web Search 工具類別 - 使用 OpenAI API"""
    
    def __init__(self):
        """初始化 Web Search 工具"""
        # 確保載入環境變數
        from dotenv import load_dotenv
        import os
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '.env'))
        
        self.config = get_config()
        self._is_configured = self.config.is_openai_configured()
        
        if self._is_configured:
            try:
                self.client = OpenAI(api_key=self.config.api.openai_api_key)
                logger.info("✅ Web Search Tool 初始化成功 (OpenAI API 已配置)")
            except Exception as e:
                logger.error(f"❌ Web Search Tool 初始化失敗: {e}")
                self._is_configured = False
        else:
            logger.warning("⚠️ Web Search Tool 初始化完成 (OpenAI API 未配置)")
    
    def is_configured(self) -> bool:
        """檢查是否已配置"""
        return self._is_configured
    
    async def search_with_openai(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        使用 OpenAI API 進行智能搜尋
        
        Args:
            query: 搜尋查詢
            context: 額外上下文
            
        Returns:
            Dict[str, Any]: 搜尋結果
        """
        if not self._is_configured:
            logger.warning("OpenAI API 未配置，使用模擬搜尋")
            return await self._mock_search(query)
        
        try:
            # 構建搜尋提示詞
            search_prompt = self._build_search_prompt(query, context)
            
            # 使用 OpenAI API 進行搜尋
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "你是一個專業的 Podcast 推薦助手。請根據用戶的查詢，提供相關的 Podcast 推薦和資訊。"
                    },
                    {
                        "role": "user",
                        "content": search_prompt
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # 解析回應
            content = response.choices[0].message.content
            
            # 格式化結果
            results = self._parse_openai_response(content, query)
            
            logger.info(f"✅ OpenAI 搜尋完成: {query}")
            return {
                "success": True,
                "results": results,
                "source": "openai_api",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ OpenAI 搜尋失敗: {e}")
            # 降級到模擬搜尋
            return await self._mock_search(query)
    
    def _build_search_prompt(self, query: str, context: Optional[str] = None) -> str:
        """構建搜尋提示詞"""
        prompt = f"""
請根據以下查詢，提供相關的 Podcast 推薦和資訊：

查詢: {query}

{context if context else ""}

請提供：
1. 相關的 Podcast 推薦（包含標題、簡介、類別）
2. 相關的資訊和建議
3. 為什麼這些推薦適合這個查詢

請以結構化的方式回應，包含具體的 Podcast 名稱和相關資訊。
"""
        return prompt.strip()
    
    def _parse_openai_response(self, content: str, query: str) -> List[Dict[str, Any]]:
        """解析 OpenAI 回應"""
        try:
            # 簡單的解析邏輯，可以根據需要改進
            results = []
            
            # 分割內容為段落
            paragraphs = content.split('\n\n')
            
            for i, paragraph in enumerate(paragraphs[:3]):  # 最多取3個結果
                if paragraph.strip():
                    results.append({
                        "title": f"推薦 {i+1}",
                        "content": paragraph.strip(),
                        "url": "#",
                        "source": "openai_api"
                    })
            
            # 如果沒有解析到結果，使用原始內容
            if not results:
                results.append({
                    "title": "搜尋結果",
                    "content": content,
                    "url": "#",
                    "source": "openai_api"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"解析 OpenAI 回應失敗: {e}")
            return [{
                "title": "搜尋結果",
                "content": content,
                "url": "#",
                "source": "openai_api"
            }]
    
    async def _mock_search(self, query: str) -> Dict[str, Any]:
        """模擬搜尋（當 OpenAI API 不可用時）"""
        logger.info(f"使用模擬搜尋: {query}")
        
        # 根據查詢類型提供不同的模擬結果
        if any(keyword in query.lower() for keyword in ['商業', '財經', '投資', '股票']):
            return {
                "success": True,
                "results": [
                    {
                        "title": "商業週刊 Podcast",
                        "content": "台灣最具影響力的商業媒體，提供最新的財經資訊和市場分析。",
                        "url": "https://www.businessweekly.com.tw",
                        "source": "mock_search"
                    },
                    {
                        "title": "財經 M 平方",
                        "content": "專業的財經分析 Podcast，深入解析全球經濟趨勢。",
                        "url": "#",
                        "source": "mock_search"
                    }
                ],
                "source": "mock_search",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        elif any(keyword in query.lower() for keyword in ['教育', '學習', '成長', '職涯']):
            return {
                "success": True,
                "results": [
                    {
                        "title": "天下雜誌 Podcast",
                        "content": "深度報導台灣與全球商業動態，提供職涯發展建議。",
                        "url": "https://www.cw.com.tw",
                        "source": "mock_search"
                    },
                    {
                        "title": "知識就是力量",
                        "content": "分享學習方法和個人成長經驗的優質 Podcast。",
                        "url": "#",
                        "source": "mock_search"
                    }
                ],
                "source": "mock_search",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": True,
                "results": [
                    {
                        "title": "Podcast 推薦",
                        "content": f"根據您的查詢 '{query}'，我推薦您收聽相關的 Podcast 節目。",
                        "url": "#",
                        "source": "mock_search"
                    }
                ],
                "source": "mock_search",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    async def search_business_topic(self, query: str) -> Dict[str, Any]:
        """搜尋商業主題"""
        logger.info(f"搜尋商業主題: {query}")
        return await self.search_with_openai(query, "請專注於商業、財經相關的 Podcast 推薦。")
    
    async def search_education_topic(self, query: str) -> Dict[str, Any]:
        """搜尋教育主題"""
        logger.info(f"搜尋教育主題: {query}")
        return await self.search_with_openai(query, "請專注於教育、學習、個人成長相關的 Podcast 推薦。")
    
    def get_config_status(self) -> Dict[str, Any]:
        """獲取配置狀態"""
        return {
            "openai_configured": self._is_configured,
            "api_key_available": bool(self.config.api.openai_api_key),
            "model": "gpt-3.5-turbo",
            "fallback_enabled": True
        } 