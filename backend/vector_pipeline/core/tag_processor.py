#!/usr/bin/env python3
"""
統一的標籤處理器
整合所有標籤處理邏輯，以 enhanced_tagging.py 為主
符合 Google Clean Code 原則，提供 OOP 介面
"""

import logging
import os
import json
import sys
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
from datetime import datetime
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

# 添加路徑以便匯入模組
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'rag_pipeline', 'scripts'))

logger = logging.getLogger(__name__)


@dataclass
class TagExtractionResult:
    """標籤提取結果"""
    tags: List[str]
    confidence: float
    method: str
    processing_time: float
    source: str


class BaseTagExtractor(ABC):
    """標籤提取器抽象基類"""
    
    @abstractmethod
    def extract_tags(self, text: str) -> TagExtractionResult:
        """提取標籤"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """檢查是否可用"""
        pass


class MoneyDJWikiExtractor(BaseTagExtractor):
    """MoneyDJ 百科專業名詞提取器"""
    
    def __init__(self):
        self.wiki_terms = set()
        self._load_moneydj_terms()
    
    def _load_moneydj_terms(self) -> Set[str]:
        """載入 MoneyDJ 百科專業名詞"""
        try:
            # 金融專業術語
            financial_terms = [
                '本益比', '股價淨值比', '股息殖利率', 'ROE', 'ROA', 'EPS', '營收', '毛利率',
                '營業利益率', '淨利率', '負債比率', '流動比率', '速動比率', '存貨週轉率',
                '應收帳款週轉率', '總資產週轉率', '股東權益報酬率', '資產報酬率',
                '自由現金流量', '營運現金流量', '投資現金流量', '籌資現金流量',
                '每股盈餘', '每股淨值', '每股現金流量', '每股營收', '每股股利',
                '股利發放率', '保留盈餘', '資本公積', '法定盈餘公積', '特別盈餘公積',
                '資產負債表', '損益表', '現金流量表', '股東權益變動表', '財務報表',
                '會計科目', '會計原則', '會計準則', '審計', '內控', '公司治理',
                '股東會', '董事會', '監察人', '獨立董事', '薪酬委員會', '審計委員會',
                '提名委員會', '風險管理委員會', '企業社會責任', '永續發展', 'ESG',
                '環境保護', '社會責任', '利害關係人', '企業價值', '企業文化', '品牌價值',
                '無形資產', '商譽', '專利權', '商標權', '著作權', '營業秘密', '智慧財產權',
                '研發支出', '研發費用', '資本支出', '營運資金', '營運資本', '淨營運資金',
                '營運資金需求', '現金循環', '現金轉換週期', '應收帳款天數', '存貨天數',
                '應付帳款天數', '現金流量折現法', '股利折現模型', '自由現金流量折現法',
                '剩餘收益模型', '經濟附加價值', 'EVA', '市場附加價值', 'MVA', '投資報酬率',
                'ROI', '內部報酬率', 'IRR', '淨現值', 'NPV', '回收期間', '獲利指數',
                '資本預算', '資本結構', '資本成本', '加權平均資本成本', 'WACC',
                '槓桿比率', '財務槓桿', '營運槓桿', '總槓桿', '財務風險', '營運風險',
                '系統性風險', '非系統性風險', '市場風險', '信用風險', '流動性風險',
                '匯率風險', '利率風險', '商品風險', '操作風險', '法律風險', '聲譽風險',
                '策略風險', '監管風險', '政治風險', '國家風險'
            ]
            
            # 投資分析術語
            investment_terms = [
                '技術分析', '基本面分析', '籌碼面分析', 'K線', '均線', 'MACD', 'RSI',
                'KD指標', '布林通道', '成交量', '價量關係', '支撐位', '壓力位',
                '突破', '跌破', '回檔', '反彈', '整理', '盤整', '趨勢', '多頭', '空頭',
                '買超', '賣超', '融資', '融券', '當沖', '信用交易', '除權', '除息',
                '填權', '填息', '貼權', '貼息', '配股', '配息', '股票分割', '合併',
                '價值投資', '成長投資', '動能投資', '反向投資', '套利', '避險',
                '投資組合', '資產配置', '分散投資', '集中投資', '長期投資', '短期投資',
                '波段操作', '當日沖銷', '隔日沖銷', '期貨交易', '選擇權交易',
                '權證交易', '可轉債', '公司債', '政府債', '市政債', '高收益債',
                '投資級債', '垃圾債', '新興市場債', '已開發市場債', '債券殖利率',
                '債券價格', '債券評等', '信用評等', '違約風險', '信用利差',
                '利率風險', '再投資風險', '通膨風險', '匯率風險', '流動性風險',
                '市場風險', '系統性風險', '非系統性風險', '投資風險', '風險報酬',
                '夏普比率', '資訊比率', '崔諾比率', '詹森阿爾法', '貝塔係數',
                '相關係數', '變異數', '標準差', '波動率', '最大回撤', 'VaR',
                '條件風險值', 'CVaR', '期望損失', 'ES', '風險調整後報酬',
                '風險預算', '風險分解', '風險歸因', '風險監控', '風險報告',
                '投資策略', '投資哲學', '投資紀律', '投資心理', '投資行為',
                '行為金融學', '市場效率', '有效市場假說', '隨機漫步', '技術指標',
                '移動平均線', '指數移動平均線', '加權移動平均線', '平滑移動平均線',
                '相對強弱指標', '隨機指標', '威廉指標', '動量指標', '趨勢指標',
                '震盪指標', '成交量指標', '價量指標', '能量指標', '力道指標',
                '乖離率', '背離', '黃金交叉', '死亡交叉', '多頭排列', '空頭排列',
                '頭肩頂', '頭肩底', '雙頂', '雙底', '三重頂', '三重底', '圓頂',
                '圓底', 'V型反轉', '倒V型反轉', 'W底', 'M頭', '旗形', '三角旗',
                '上升三角形', '下降三角形', '對稱三角形', '矩形', '楔形',
                '缺口', '跳空', '島狀反轉', '黃昏之星', '晨星', '十字星',
                '錘子線', '上吊線', '流星線', '倒錘子線', '紡錘線', '十字線',
                '一字線', 'T字線', '倒T字線', '實體', '影線', '開盤價', '收盤價',
                '最高價', '最低價', '漲停價', '跌停價', '漲跌幅', '振幅',
                '換手率', '週轉率', '本益成長比', 'PEG', '股價營收比', 'PSR',
                '股價現金流量比', 'PCFR', '企業價值倍數', 'EV/EBITDA',
                '企業價值營收比', 'EV/Sales', '企業價值自由現金流量比', 'EV/FCF',
                '股東權益報酬率', 'ROE', '資產報酬率', 'ROA', '投資報酬率', 'ROI',
                '資本報酬率', 'ROC', '投入資本報酬率', 'ROIC', '經濟附加價值', 'EVA'
            ]
            
            # 產業專業術語
            industry_terms = [
                '半導體', '晶圓代工', 'IC設計', '封測', '記憶體', '面板', 'LED',
                '太陽能', '風力發電', '電動車', '電池', '5G', 'AI', '雲端運算',
                '大數據', '物聯網', '區塊鏈', '元宇宙', '生技', '製藥', '醫療器材',
                '金融科技', '電子商務', '數位支付', '共享經濟', '平台經濟',
                '晶片', '積體電路', '微處理器', '中央處理器', 'CPU', '圖形處理器', 'GPU',
                '記憶體晶片', 'DRAM', 'SRAM', 'NAND Flash', 'NOR Flash', 'SSD',
                '硬碟', 'HDD', '固態硬碟', '光碟', 'CD', 'DVD', '藍光', 'BD',
                '主機板', '顯示卡', '音效卡', '網路卡', '路由器', '交換器',
                '伺服器', '工作站', '個人電腦', '筆記型電腦', '平板電腦', '智慧型手機',
                '穿戴裝置', '智慧手錶', '智慧眼鏡', '智慧音箱', '智慧家電',
                '物聯網設備', '感測器', '控制器', '執行器', '通訊模組',
                '藍牙', 'WiFi', '4G', '5G', '6G', '衛星通訊', '光纖通訊',
                '有線電視', '數位電視', '網路電視', '串流媒體', 'OTT',
                '社群媒體', '搜尋引擎', '電子郵件', '即時通訊', '視訊會議',
                '遠端工作', '雲端服務', 'SaaS', 'PaaS', 'IaaS', '邊緣運算',
                '量子運算', '超級電腦', '人工智慧', '機器學習', '深度學習',
                '神經網路', '自然語言處理', '電腦視覺', '語音識別', '語音合成',
                '機器人', '自動化', '工業4.0', '智慧製造', '數位轉型',
                '電子商務', 'B2B', 'B2C', 'C2C', 'O2O', '行動商務',
                '數位行銷', '社群行銷', '內容行銷', '搜尋引擎優化', 'SEO',
                '搜尋引擎行銷', 'SEM', '電子郵件行銷', '簡訊行銷', '推播通知',
                '網紅行銷', 'KOL', '意見領袖', '影響者行銷', '口碑行銷',
                '病毒式行銷', '飢餓行銷', '體驗行銷', '情感行銷', '品牌行銷',
                '產品行銷', '服務行銷', '價格行銷', '通路行銷', '促銷行銷',
                '整合行銷', '全通路行銷', '個人化行銷', '精準行銷', '大數據行銷',
                '人工智慧行銷', '聊天機器人', '虛擬助理', '智慧客服',
                '客戶關係管理', 'CRM', '企業資源規劃', 'ERP', '供應鏈管理', 'SCM',
                '知識管理', 'KM', '商業智慧', 'BI', '資料倉儲', '資料探勘',
                '預測分析', '描述性分析', '診斷性分析', '處方性分析',
                'A/B測試', '多變數測試', '使用者體驗', 'UX', '使用者介面', 'UI',
                '可用性測試', '易用性', '可及性', '響應式設計', '適配性設計',
                '行動優先', '漸進式網頁應用', 'PWA', '單頁應用', 'SPA',
                '微服務', '容器化', 'Docker', 'Kubernetes', 'DevOps',
                '敏捷開發', 'Scrum', '看板', '持續整合', 'CI', '持續部署', 'CD',
                '測試驅動開發', 'TDD', '行為驅動開發', 'BDD', '極限程式設計', 'XP',
                '精實開發', 'Lean', '六標準差', 'Six Sigma', '全面品質管理', 'TQM',
                '專案管理', 'PM', '專案經理', '產品經理', '產品負責人',
                'Scrum Master', '敏捷教練', '技術主管', '架構師', '系統分析師',
                '程式設計師', '軟體工程師', '前端工程師', '後端工程師',
                '全端工程師', '資料工程師', '資料科學家', '機器學習工程師',
                '人工智慧工程師', 'DevOps工程師', '測試工程師', '品質保證', 'QA',
                '使用者體驗設計師', 'UI設計師', '視覺設計師', '互動設計師',
                '產品設計師', '服務設計師', '策略設計師', '創新設計師'
            ]
            
            # 經濟指標術語
            economic_terms = [
                'GDP', 'CPI', 'PPI', '失業率', '利率', '匯率', '通膨', '通縮',
                '景氣循環', '經濟成長率', '消費者信心指數', '採購經理人指數',
                '工業生產指數', '零售銷售', '進出口', '貿易順差', '貿易逆差',
                '外匯存底', '貨幣供給', '財政政策', '貨幣政策', '量化寬鬆',
                '升息', '降息', '通膨預期', '經濟軟著陸', '經濟硬著陸'
            ]
            
            # 國際金融術語
            international_terms = [
                '美股', '港股', '日股', '歐股', '新興市場', '成熟市場', '已開發國家',
                '開發中國家', 'G7', 'G20', '歐盟', '歐元區', '亞洲四小龍',
                '金磚四國', 'MSCI', '富時指數', '道瓊指數', '標普500', '納斯達克',
                '恆生指數', '日經指數', '德國DAX', '法國CAC', '英國富時100'
            ]
            
            # 心理學專業術語
            psychology_terms = [
                '認知心理學', '行為心理學', '社會心理學', '發展心理學', '臨床心理學',
                '實驗心理學', '生理心理學', '神經心理學', '人格心理學', '教育心理學',
                '工業心理學', '組織心理學', '諮商心理學', '變態心理學', '健康心理學',
                '正向心理學', '文化心理學', '跨文化心理學', '比較心理學', '進化心理學',
                '注意力', '記憶力', '學習能力', '思考能力', '推理能力', '創造力',
                '知覺', '感覺', '意識', '潛意識', '前意識', '無意識', '自我意識',
                '認知偏差', '認知失調', '認知負荷', '認知資源', '認知風格', '認知策略',
                '元認知', '後設認知', '認知發展', '認知老化', '認知障礙', '認知治療',
                '情緒', '情感', '心情', '心境', '情緒智力', '情緒管理', '情緒調節',
                '情緒表達', '情緒識別', '情緒理解', '情緒共鳴', '情緒感染', '情緒勞動',
                '情緒耗竭', '情緒倦怠', '情緒支持', '情緒安全', '情緒依附', '情緒分離',
                '焦慮', '憂鬱', '憤怒', '恐懼', '快樂', '悲傷', '驚訝', '厭惡',
                '羞愧', '罪惡感', '驕傲', '嫉妒', '愛', '恨', '希望', '絕望',
                '人格', '個性', '性格', '氣質', '特質', '人格特質', '人格類型',
                '人格發展', '人格障礙', '人格測驗', '人格評估', '人格心理學',
                '內向', '外向', '神經質', '開放性', '盡責性', '友善性', '大五人格',
                'MBTI', '九型人格', 'A型人格', 'B型人格', 'C型人格', 'D型人格',
                '社會認知', '社會知覺', '社會態度', '社會影響', '社會學習', '社會化',
                '從眾行為', '服從權威', '社會助長', '社會抑制', '社會懈怠', '團體動力',
                '團體凝聚力', '團體決策', '團體極化', '團體思維', '社會認同', '社會比較',
                '歸因理論', '認知失調理論', '社會交換理論', '社會學習理論', '社會認同理論',
                '心理需求', '心理動機', '心理目標', '心理期望', '心理信念', '心理價值',
                '心理態度', '心理傾向', '心理偏好', '心理習慣', '心理模式', '心理框架',
                '心理腳本', '心理圖式', '心理基模', '心理表徵'
            ]
            
            # 美中貿易戰與國際貿易專業術語
            trade_war_terms = [
                '關稅', 'Tariffs', '貿易戰', 'Trade War', '貿易逆差', 'Trade Deficit',
                '貿易順差', 'Trade Surplus', '關稅配額', 'Tariff Rate Quotas',
                '關稅壁壘', 'Tariff Barriers', '非關稅壁壘', 'Non-Tariff Barriers',
                '最惠國待遇', 'Most Favored Nation Treatment', '反傾銷稅', 'Anti-dumping Duties',
                '補貼', 'Subsidies', '技術性貿易壁壘', 'Technical Barriers to Trade', 'TBT',
                '出口管制', 'Export Controls', '雙邊貿易協定', 'Bilateral Trade Agreement',
                '區域貿易協定', 'Regional Trade Agreement', 'RTA', 'RCEP',
                '對等關稅', '報復性關稅', '懲罰性關稅', '進口關稅', '出口關稅',
                '關稅豁免', '關稅減免', '關稅優惠', '關稅同盟', '自由貿易區',
                '貿易保護主義', '貿易自由化', '貿易平衡', '貿易赤字', '貿易盈餘',
                '貿易爭端', 'Trade Dispute', '世貿組織', 'World Trade Organization', 'WTO',
                '貿易救濟措施', 'Trade Remedy Measures', '知識產權', 'Intellectual Property',
                '產業政策', 'Industrial Policy', '供給鏈', 'Supply Chain',
                '外匯儲備', 'Foreign Exchange Reserves', '資本管制', 'Capital Controls',
                '匯率', 'Exchange Rate', '通脹', 'Inflation', '經濟制裁', 'Economic Sanctions',
                '貿易談判', '貿易協商', '貿易協議', '貿易條約', '貿易規則',
                '國際貿易法', '貿易法規', '貿易政策', '貿易戰略', '貿易夥伴',
                '貿易關係', '貿易合作', '貿易競爭', '貿易衝突', '貿易摩擦',
                '美中貿易戰', '中美貿易戰', 'China-US Trade War', 'US-China Trade War',
                '川普關稅', 'Trump Tariffs', '拜登貿易政策', 'Biden Trade Policy',
                '第一階段貿易協議', 'Phase One Trade Deal', '第二階段貿易協議', 'Phase Two Trade Deal',
                '301調查', 'Section 301 Investigation', '232調查', 'Section 232 Investigation',
                '國家安全關稅', 'National Security Tariffs', '鋼鋁關稅', 'Steel and Aluminum Tariffs',
                '汽車關稅', 'Auto Tariffs', '農產品關稅', 'Agricultural Tariffs',
                '科技產品關稅', 'Technology Tariffs', '消費品關稅', 'Consumer Goods Tariffs',
                '去風險化', 'De-risking', '脫鉤', 'Decoupling', '再全球化', 'Re-globalization',
                '保護主義', 'Protectionism', '公平貿易', 'Fair Trade', '綠色貿易', 'Green Trade',
                '貿易多元化', 'Trade Diversification', '供應鏈重組', 'Supply Chain Restructuring',
                '近岸外包', 'Nearshoring', '友岸外包', 'Friendshoring', '回流', 'Reshoring',
                '貿易轉移', 'Trade Diversion', '貿易創造', 'Trade Creation',
                '貿易壁壘', 'Trade Barriers', '貿易便利化', 'Trade Facilitation',
                '貿易透明度', 'Trade Transparency', '貿易可預測性', 'Trade Predictability',
                '貿易穩定性', 'Trade Stability', '貿易可持續性', 'Trade Sustainability',
                '亞太經合組織', 'APEC', '東盟', 'ASEAN', '歐盟', 'European Union', 'EU',
                '北美自由貿易協定', 'NAFTA', '美墨加貿易協定', 'USMCA',
                '跨太平洋夥伴關係協定', 'TPP', '全面與進步跨太平洋夥伴關係協定', 'CPTPP',
                '跨大西洋貿易與投資夥伴關係協定', 'TTIP', '中歐投資協定', 'EU-China Investment Agreement',
                '一帶一路', 'Belt and Road Initiative', 'BRI', '區域全面經濟夥伴關係協定', 'RCEP',
                '貿易依存度', 'Trade Dependence', '貿易集中度', 'Trade Concentration',
                '貿易彈性', 'Trade Elasticity', '貿易乘數', 'Trade Multiplier',
                '貿易條件', 'Terms of Trade', '貿易成本', 'Trade Costs',
                '貿易收益', 'Trade Gains', '貿易損失', 'Trade Losses',
                '貿易衝擊', 'Trade Shock', '貿易調整', 'Trade Adjustment',
                '貿易適應', 'Trade Adaptation', '貿易轉型', 'Trade Transformation',
                '出口導向型經濟', 'Export-Oriented Economy', '進口替代', 'Import Substitution',
                '出口替代', 'Export Substitution', '產業升級', 'Industrial Upgrading',
                '產業轉移', 'Industrial Transfer', '產業鏈', 'Industrial Chain',
                '價值鏈', 'Value Chain', '全球價值鏈', 'Global Value Chain',
                '跨國企業', 'Multinational Corporations', 'MNCs', '本土企業', 'Local Enterprises',
                '中小企業', 'SMEs', '國有企業', 'State-Owned Enterprises', 'SOEs',
                '民營企業', 'Private Enterprises', '外資企業', 'Foreign-Invested Enterprises'
            ]
            
            # 合併所有術語
            all_terms = (financial_terms + investment_terms + industry_terms + 
                        economic_terms + international_terms + psychology_terms + trade_war_terms)
            
            for term in all_terms:
                self.wiki_terms.add(term)
            
            logger.info(f"成功載入 {len(self.wiki_terms)} 個 MoneyDJ 百科專業名詞")
            return self.wiki_terms
            
        except Exception as e:
            logger.error(f"載入 MoneyDJ 百科專業名詞失敗: {e}")
            return set()
    
    def extract_tags(self, text: str) -> TagExtractionResult:
        """從文本中提取 MoneyDJ 百科專業名詞標籤"""
        start_time = time.time()
        
        if not self.wiki_terms:
            self._load_moneydj_terms()
        
        extracted_tags = []
        text_lower = text.lower()
        
        for term in self.wiki_terms:
            if term.lower() in text_lower:
                extracted_tags.append(term)
        
        processing_time = time.time() - start_time
        
        return TagExtractionResult(
            tags=extracted_tags,
            confidence=0.8 if extracted_tags else 0.0,
            method="moneydj_wiki",
            processing_time=processing_time,
            source="MoneyDJ百科"
        )
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        return len(self.wiki_terms) > 0


class CSVTagExtractor(BaseTagExtractor):
    """基於 CSV 的標籤提取器"""
    
    def __init__(self, tag_csv_path: str):
        self.tag_csv_path = Path(tag_csv_path)
        self.tag_processor = None
        self._initialize()
    
    def _initialize(self):
        """初始化標籤處理器"""
        try:
            from tag_processor import TagProcessor
            if self.tag_csv_path.exists():
                self.tag_processor = TagProcessor(str(self.tag_csv_path))
                logger.info(f"成功載入 CSV 標籤處理器: {self.tag_csv_path}")
            else:
                logger.warning(f"CSV 檔案不存在: {self.tag_csv_path}")
        except Exception as e:
            logger.warning(f"無法載入 CSV 標籤處理器: {e}")
            self.tag_processor = None
    
    def extract_tags(self, text: str) -> TagExtractionResult:
        """從 CSV 提取標籤"""
        start_time = time.time()
        
        if not self.tag_processor:
            return TagExtractionResult(
                tags=[],
                confidence=0.0,
                method="csv",
                processing_time=time.time() - start_time,
                source="TAG_info.csv"
            )
        
        try:
            csv_tags = self.tag_processor.extract_tags_from_chunk(text)
            processing_time = time.time() - start_time
            
            return TagExtractionResult(
                tags=csv_tags,
                confidence=0.9 if csv_tags else 0.0,
                method="csv",
                processing_time=processing_time,
                source="TAG_info.csv"
            )
            
        except Exception as e:
            logger.error(f"CSV 標籤提取失敗: {e}")
            return TagExtractionResult(
                tags=[],
                confidence=0.0,
                method="csv",
                processing_time=time.time() - start_time,
                source="TAG_info.csv"
            )
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        return self.tag_processor is not None


class FallbackTagExtractor(BaseTagExtractor):
    """備援標籤提取器"""
    
    def __init__(self):
        self.keyword_patterns = self._load_keyword_patterns()
    
    def _load_keyword_patterns(self) -> Dict[str, List[str]]:
        """載入關鍵詞模式"""
        return {
            '投資': ['投資', '理財', '股票', '基金', '債券', '期貨', '外匯', '房地產', '資產', '財富', '報酬', '風險', '收益'],
            '職涯': ['工作', '職場', '職業', '事業', '升遷', '薪資', '面試', '履歷', '求職', '轉職', '創業', '企業', '公司'],
            '教育': ['學習', '教育', '培訓', '課程', '學校', '大學', '技能', '知識', '閱讀', '寫作', '語言', '英語'],
            '科技': ['科技', '技術', 'AI', '人工智慧', '機器學習', '大數據', '雲端', '區塊鏈', '5G', '物聯網', '電動車'],
            '健康': ['健康', '運動', '飲食', '營養', '睡眠', '心理', '壓力', '情緒', '生活', '習慣', '養生'],
            '時事': ['新聞', '政治', '經濟', '社會', '國際', '環境', '疫情', '政策', '法規', '趨勢', '發展'],
            '娛樂': ['音樂', '電影', '遊戲', '旅遊', '美食', '攝影', '藝術', '文化', '娛樂', '休閒', '興趣'],
            '家庭': ['家庭', '親子', '婚姻', '愛情', '友誼', '人際', '關係', '溝通', '相處', '教育', '成長']
        }
    
    def extract_tags(self, text: str) -> TagExtractionResult:
        """備援標籤提取"""
        start_time = time.time()
        
        if not text or not text.strip():
            return TagExtractionResult(
                tags=['其他'],
                confidence=0.1,
                method="fallback",
                processing_time=time.time() - start_time,
                source="備援系統"
            )
        
        text_lower = text.lower()
        matched_tags = []
        
        # 檢查每個主題的關鍵詞
        for topic, keywords in self.keyword_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matched_tags.append(topic)
                    break  # 每個主題只取一個標籤
        
        # 如果沒有匹配到任何標籤，使用通用標籤
        if not matched_tags:
            if len(text) < 50:
                matched_tags.append('其他')
            elif any(word in text_lower for word in ['我', '你', '他', '她', '我們', '你們', '他們']):
                matched_tags.append('個人')
            elif any(word in text_lower for word in ['今天', '明天', '昨天', '現在', '過去', '未來']):
                matched_tags.append('時事')
            elif any(word in text_lower for word in ['覺得', '認為', '相信', '希望', '想要', '喜歡']):
                matched_tags.append('觀點')
            else:
                matched_tags.append('其他')
        
        processing_time = time.time() - start_time
        
        return TagExtractionResult(
            tags=matched_tags,
            confidence=0.3 if matched_tags else 0.1,
            method="fallback",
            processing_time=processing_time,
            source="備援系統"
        )
    
    def is_available(self) -> bool:
        """檢查是否可用"""
        return True


class UnifiedTagProcessor:
    """統一的標籤處理器，整合所有貼標邏輯"""
    
    def __init__(self, tag_csv_path: str = "../utils/TAG_info.csv"):
        """
        初始化統一標籤處理器
        
        Args:
            tag_csv_path: TAG_info.csv 檔案路徑
        """
        self.tag_csv_path = tag_csv_path
        
        # 初始化各種提取器
        self.csv_extractor = CSVTagExtractor(tag_csv_path)
        self.moneydj_extractor = MoneyDJWikiExtractor()
        self.fallback_extractor = FallbackTagExtractor()
        
        # 初始化增強版標籤處理器（主程式）
        try:
            sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
            from enhanced_tagging import EnhancedTagProcessor
            self.enhanced_processor = EnhancedTagProcessor(tag_csv_path)
            logger.info("成功載入增強版標籤處理器（主程式）")
        except Exception as e:
            logger.warning(f"無法載入增強版標籤處理器: {e}")
            self.enhanced_processor = None
        
        logger.info("統一標籤處理器初始化完成")
        self._log_available_extractors()
    
    def _log_available_extractors(self):
        """記錄可用的提取器"""
        available_extractors = []
        if self.enhanced_processor:
            available_extractors.append("增強版標籤處理器（主程式）")
        if self.csv_extractor.is_available():
            available_extractors.append("CSV")
        if self.moneydj_extractor.is_available():
            available_extractors.append("MoneyDJ百科")
        if self.fallback_extractor.is_available():
            available_extractors.append("備援系統")
        
        logger.info(f"可用的標籤提取器: {', '.join(available_extractors)}")
    
    def extract_enhanced_tags(self, chunk_text: str) -> List[str]:
        """
        增強版標籤提取
        1. 優先使用增強版標籤處理器（主程式）
        2. 使用 CSV 提取器
        3. 使用 MoneyDJ 百科專業名詞
        4. 使用備援系統作為最後保障
        
        Args:
            chunk_text: 文本內容
            
        Returns:
            List[str]: 標籤列表
        """
        # 優先使用增強版標籤處理器（主程式）
        if self.enhanced_processor:
            try:
                enhanced_tags = self.enhanced_processor.extract_enhanced_tags(chunk_text)
                if enhanced_tags:
                    logger.debug(f"增強版標籤處理器結果: {enhanced_tags}")
                    return enhanced_tags
            except Exception as e:
                logger.warning(f"增強版標籤處理器失敗: {e}")
        
        # 如果增強版處理器不可用或失敗，使用備援方案
        all_tags = set()
        
        # 步驟1: 使用 CSV 提取器
        if self.csv_extractor.is_available():
            try:
                result = self.csv_extractor.extract_tags(chunk_text)
                all_tags.update(result.tags)
                logger.debug(f"CSV 提取器結果: {result.tags}")
            except Exception as e:
                logger.warning(f"CSV 提取器失敗: {e}")
        
        # 步驟2: 使用 MoneyDJ 百科提取器
        if self.moneydj_extractor.is_available():
            try:
                result = self.moneydj_extractor.extract_tags(chunk_text)
                all_tags.update(result.tags)
                logger.debug(f"MoneyDJ 百科提取器結果: {result.tags}")
            except Exception as e:
                logger.warning(f"MoneyDJ 百科提取器失敗: {e}")
        
        # 步驟3: 如果還沒有標籤，使用備援系統
        if not all_tags:
            try:
                result = self.fallback_extractor.extract_tags(chunk_text)
                all_tags.update(result.tags)
                logger.debug(f"備援系統結果: {result.tags}")
            except Exception as e:
                logger.warning(f"備援系統失敗: {e}")
        
        # 如果都沒有標籤，記錄日誌
        if not all_tags:
            logger.info(f"所有貼標方法都無結果，文本: {chunk_text[:50]}...")
            all_tags.add('其他')
        
        return list(all_tags)
    
    def extract_tags_with_details(self, chunk_text: str) -> TagExtractionResult:
        """
        提取標籤並返回詳細資訊
        
        Args:
            chunk_text: 文本內容
            
        Returns:
            TagExtractionResult: 詳細的標籤提取結果
        """
        start_time = time.time()
        
        # 嘗試各種提取器
        results = []
        
        if self.csv_extractor.is_available():
            results.append(self.csv_extractor.extract_tags(chunk_text))
        
        if self.moneydj_extractor.is_available():
            results.append(self.moneydj_extractor.extract_tags(chunk_text))
        
        if not results:  # 如果前兩個都不可用，使用備援
            results.append(self.fallback_extractor.extract_tags(chunk_text))
        
        # 選擇最佳結果
        best_result = max(results, key=lambda x: x.confidence) if results else self.fallback_extractor.extract_tags(chunk_text)
        
        # 合併所有標籤
        all_tags = set()
        for result in results:
            all_tags.update(result.tags)
        
        processing_time = time.time() - start_time
        
        return TagExtractionResult(
            tags=list(all_tags),
            confidence=best_result.confidence,
            method=best_result.method,
            processing_time=processing_time,
            source=best_result.source
        )
    
    def get_extractor_status(self) -> Dict[str, bool]:
        """獲取提取器狀態"""
        return {
            'enhanced_processor': self.enhanced_processor is not None,
            'csv_extractor': self.csv_extractor.is_available(),
            'moneydj_extractor': self.moneydj_extractor.is_available(),
            'fallback_extractor': self.fallback_extractor.is_available()
        } 