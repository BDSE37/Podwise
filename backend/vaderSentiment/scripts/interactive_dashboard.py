#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
互動式多主題情感分析儀表板
- 使用 Plotly 創建現代化互動式視覺化
- 專業UI/UX設計，適合商業展示
"""
import os
import json
import jieba
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# Plutchik 八大情感對應詞彙
PLUTCHIK_EMOTIONS = {
    'Joy':     ['快樂', '開心', '喜悅', '滿意', '幸福', '愉快', '歡樂', '欣喜', '高興', '希望'],
    'Trust':   ['信任', '安心', '可靠', '支持', '信心', '依賴', '尊重', '誠實', '穩定', '安全'],
    'Fear':    ['害怕', '恐懼', '擔心', '焦慮', '緊張', '不安', '擔憂', '恐慌', '畏懼', '擔憂'],
    'Surprise':['驚訝', '意外', '驚喜', '驚奇', '出乎意料', '震驚', '訝異', '驚愕'],
    'Sadness': ['難過', '悲傷', '失望', '沮喪', '痛苦', '哀傷', '悲哀', '傷心', '無助', '孤單'],
    'Disgust': ['厭惡', '反感', '噁心', '討厭', '排斥', '不滿', '反胃', '嫌棄', '惡心'],
    'Anger':   ['生氣', '憤怒', '氣憤', '不滿', '激動', '暴躁', '怒氣', '發火', '怒罵', '氣惱'],
    'Anticipation': ['期待', '盼望', '預期', '希望', '渴望', '想像', '預料', '預感', '預想']
}

# 主題關鍵詞
BUSINESS_KEYWORDS = [
    '公司', '職場', '老闆', '面試', '薪水', '創業', '行銷', '客戶', '業務', '商業', '品牌', '產品', '銷售', 
    '主管', '同事', '會議', '績效', '加班', '投資', '經營', '市場', '企業', '工作', '職位', '升遷', '獎金'
]

EDU_KEYWORDS = [
    '學校', '老師', '學生', '教學', '課程', '學習', '考試', '作業', '教育', '補習', '教室', '校園', '報告', 
    '成績', '升學', '指導', '課堂', '教材', '論文', '研究', '學分', '大學', '研究所', '畢業', '學位', '專業'
]

# 現代化配色方案
TOPIC_COLORS = {
    '商業': '#FF6B35',      # 活力橙色
    '教育': '#4ECDC4',      # 清新青綠
    '商業+教育': '#9B59B6', # 優雅紫色
    '其他': '#3498DB'       # 專業藍色
}

class InteractiveAnalyzer:
    """互動式情感分析器"""
    
    def __init__(self):
        self.topic_emotion_counter = defaultdict(lambda: Counter({k:0 for k in PLUTCHIK_EMOTIONS}))
        self.topic_total = Counter()
    
    def analyze_data(self, folder):
        """分析數據"""
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.json')]
        
        for file in files:
            with open(file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except Exception:
                    continue
                
                texts = self.extract_texts(data)
                
                for text in texts:
                    tokens = list(jieba.cut(text))
                    topic = self.classify_topic(text)
                    emo_count = self.classify_emotions(tokens)
                    self.topic_emotion_counter[topic].update(emo_count)
                    self.topic_total[topic] += 1
        
        return self.calculate_ratios()
    
    def extract_texts(self, data):
        """提取文本內容"""
        texts = []
        if isinstance(data, dict):
            if 'content' in data:
                texts.append(data['content'])
            else:
                texts = [v for v in data.values() if isinstance(v, str)]
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    if 'content' in item:
                        texts.append(item['content'])
                    else:
                        texts += [v for v in item.values() if isinstance(v, str)]
        return texts
    
    def classify_topic(self, text):
        """主題分類"""
        is_business = any(kw in text for kw in BUSINESS_KEYWORDS)
        is_edu = any(kw in text for kw in EDU_KEYWORDS)
        
        if is_business and is_edu:
            return '商業+教育'
        elif is_business:
            return '商業'
        elif is_edu:
            return '教育'
        else:
            return '其他'
    
    def classify_emotions(self, tokens):
        """八大情感分類"""
        emo_count = {k:0 for k in PLUTCHIK_EMOTIONS}
        for token in tokens:
            for emo, words in PLUTCHIK_EMOTIONS.items():
                if token in words:
                    emo_count[emo] += 1
        return emo_count
    
    def calculate_ratios(self):
        """計算情感比例"""
        topic_emo_ratio = {}
        for topic, emo_counter in self.topic_emotion_counter.items():
            total = sum(emo_counter.values())
            if total == 0:
                topic_emo_ratio[topic] = [0]*8
            else:
                topic_emo_ratio[topic] = [emo_counter[emo]/total for emo in PLUTCHIK_EMOTIONS]
        return topic_emo_ratio

class InteractiveVisualizer:
    """互動式視覺化器"""
    
    def create_polar_chart(self, topic_emo_ratio):
        """創建互動式極座標圖"""
        emotions = list(PLUTCHIK_EMOTIONS.keys())
        
        fig = go.Figure()
        
        for topic, ratios in topic_emo_ratio.items():
            values = ratios + ratios[:1]
            angles = np.linspace(0, 2*np.pi, len(emotions), endpoint=False).tolist()
            angles += angles[:1]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=[f"{angle*180/np.pi:.0f}°" for angle in angles],
                fill='toself',
                name=topic,
                line_color=TOPIC_COLORS.get(topic, '#888'),
                fillcolor=TOPIC_COLORS.get(topic, '#888'),
                opacity=0.6,
                line_width=3,
                hovertemplate=f'<b>{topic}</b><br>比例: <b>%{{r:.3f}}</b><extra></extra>'
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max([max(ratios) for ratios in topic_emo_ratio.values()]) * 1.2]
                ),
                angularaxis=dict(
                    tickmode='array',
                    tickvals=list(range(0, 360, 45)),
                    ticktext=emotions,
                    direction='clockwise'
                )
            ),
            showlegend=True,
            title={
                'text': '多主題八大情感分布圖譜<br><sub>Multi-Topic Eight Emotions Distribution</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#2C3E50'}
            },
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=600
        )
        
        return fig
    
    def create_bar_chart(self, topic_emo_ratio):
        """創建互動式柱狀圖"""
        emotions = list(PLUTCHIK_EMOTIONS.keys())
        topics = list(topic_emo_ratio.keys())
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[f'{topic} 情感分布' for topic in topics],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        for i, topic in enumerate(topics):
            if i < 4:
                row = (i // 2) + 1
                col = (i % 2) + 1
                ratios = topic_emo_ratio[topic]
                
                fig.add_trace(
                    go.Bar(
                        x=emotions,
                        y=ratios,
                        name=topic,
                        marker_color=TOPIC_COLORS[topic],
                        opacity=0.8,
                        hovertemplate=f'<b>{topic}</b><br>比例: <b>%{{y:.3f}}</b><extra></extra>'
                    ),
                    row=row, col=col
                )
        
        fig.update_layout(
            title={
                'text': '各主題情感分布比較',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#2C3E50'}
            },
            showlegend=False,
            height=800,
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        for i in range(1, 3):
            for j in range(1, 3):
                fig.update_xaxes(tickangle=45, row=i, col=j)
        
        return fig
    
    def create_summary_stats(self, topic_emo_ratio, topic_total):
        """創建統計摘要圖表"""
        topics = list(topic_emo_ratio.keys())
        counts = [topic_total[topic] for topic in topics]
        colors = [TOPIC_COLORS[topic] for topic in topics]
        
        fig = go.Figure(data=[
            go.Bar(
                x=topics,
                y=counts,
                marker_color=colors,
                opacity=0.8,
                text=counts,
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>評論數量: <b>%{y}</b><extra></extra>'
            )
        ])
        
        fig.update_layout(
            title={
                'text': '各主題評論數量統計',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#2C3E50'}
            },
            xaxis_title="主題",
            yaxis_title="評論數量",
            font=dict(family="Arial, sans-serif"),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=500
        )
        
        return fig

def export_sunburst_json(topic_emotion_counter, output_path):
    """輸出sunburst結構的JSON，商業/教育加highlight"""
    EMOTION_POLARITY = {
        'Joy': '正向', 'Trust': '正向', 'Anticipation': '正向',
        'Surprise': '中立',
        'Fear': '負向', 'Sadness': '負向', 'Disgust': '負向', 'Anger': '負向',
    }
    # 先收集主題
    all_topics = list(topic_emotion_counter.keys())
    # 商業、教育優先
    ordered_topics = [t for t in ['商業', '教育'] if t in all_topics]
    ordered_topics += [t for t in all_topics if t not in ordered_topics]
    children = []
    for topic in ordered_topics:
        emo_counter = topic_emotion_counter[topic]
        polarity_counter = {'正向':0, '中立':0, '負向':0}
        for emo, count in emo_counter.items():
            polarity = EMOTION_POLARITY.get(emo, '中立')
            polarity_counter[polarity] += count
        node = {
            "name": topic,
            "children": [
                {"name": "正向", "value": polarity_counter['正向']},
                {"name": "中立", "value": polarity_counter['中立']},
                {"name": "負向", "value": polarity_counter['負向']}
            ]
        }
        if topic in ['商業', '教育']:
            node["highlight"] = True
        children.append(node)
    root = {"name": "全部評論", "children": children}
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(root, f, ensure_ascii=False, indent=2)
    print(f'🌞 Sunburst資料已輸出到 {output_path}')

def main():
    """主程式"""
    print("🎯 開始互動式多主題情感分析...")
    
    # 初始化分析器
    analyzer = InteractiveAnalyzer()
    visualizer = InteractiveVisualizer()
    
    # 分析數據
    folder = './comment_data'
    topic_emo_ratio = analyzer.analyze_data(folder)
    
    if not topic_emo_ratio:
        print("❌ 沒有找到有效的數據")
        return
    
    print(f"✅ 分析完成！共處理 {sum(analyzer.topic_total.values())} 條評論")
    
    # 顯示統計信息
    for topic, count in analyzer.topic_total.items():
        print(f"📊 {topic}: {count} 條評論")
    
    # 創建互動式視覺化圖表
    print("🎨 生成互動式視覺化圖表...")
    
    # 1. 極座標圖
    polar_fig = visualizer.create_polar_chart(topic_emo_ratio)
    polar_fig.write_html('interactive_polar_chart.html')
    print("📈 互動式極座標圖已保存為 interactive_polar_chart.html")
    
    # 2. 柱狀圖比較
    bar_fig = visualizer.create_bar_chart(topic_emo_ratio)
    bar_fig.write_html('interactive_bar_chart.html')
    print("📊 互動式柱狀圖已保存為 interactive_bar_chart.html")
    
    # 3. 統計摘要
    summary_fig = visualizer.create_summary_stats(topic_emo_ratio, analyzer.topic_total)
    summary_fig.write_html('interactive_summary.html')
    print("📋 互動式統計摘要已保存為 interactive_summary.html")
    
    print("🎉 分析完成！所有互動式圖表已生成並保存。")
    print("💡 請在瀏覽器中打開 HTML 檔案以查看互動式圖表。")

    # 新增：輸出sunburst資料
    export_sunburst_json(analyzer.topic_emotion_counter, 'sunburst_data.json')

if __name__ == '__main__':
    main() 