import os
import json
import jieba
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')
from matplotlib import font_manager

# 嘗試自動設定中文字體
# 只用plt，不需import matplotlib

def set_chinese_font():
    font_candidates = [
        'Noto Sans CJK TC', 'Microsoft JhengHei', 'PingFang TC', 'Heiti TC', 'STHeiti', 'SimHei', 'Arial Unicode MS'
    ]
    available_fonts = set(f.name for f in font_manager.fontManager.ttflist)
    for font in font_candidates:
        if font in available_fonts:
            plt.rcParams['font.sans-serif'] = [font]
            plt.rcParams['axes.unicode_minus'] = False
            return font
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    return 'Arial Unicode MS'
set_chinese_font()
# 主題關鍵詞（擴充版）
BUSINESS_KEYWORDS = [
    '公司', '職場', '老闆', '面試', '薪水', '創業', '行銷', '客戶', '業務', '商業', '品牌', '產品', '銷售', 
    '主管', '同事', '會議', '績效', '加班', '投資', '經營', '市場', '企業', '工作', '職位', '升遷', '獎金',
    '競爭', '策略', '管理', '領導', '團隊', '專案', '業績', '目標', '計劃', '執行', '分析', '報告', '提案'
]
EDU_KEYWORDS = [
    '學校', '老師', '學生', '教學', '課程', '學習', '考試', '作業', '教育', '補習', '教室', '校園', '報告', 
    '成績', '升學', '指導', '課堂', '教材', '論文', '研究', '學分', '大學', '研究所', '畢業', '學位', '專業',
    '知識', '技能', '訓練', '實習', '實驗', '討論', '分享', '交流', '合作', '創新', '思考', '理解', '應用'
]
# 現代化配色方案
TOPIC_COLORS = {
    '商業': '#FF6B35',      # 活力橙色
    '教育': '#4ECDC4',      # 清新青綠
    '商業+教育': '#9B59B6', # 優雅紫色
    '其他': '#3498DB'       # 專業藍色
}

# 八大情感對應極性分類
EMOTION_POLARITY = {
    'Joy': '正向',
    'Trust': '正向',
    'Anticipation': '正向',
    'Surprise': '中立',
    'Fear': '負向',
    'Sadness': '負向',
    'Disgust': '負向',
    'Anger': '負向',
}

# Plutchik 八大情感對應詞彙（擴充版）
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

# 取得所有 json 檔案
def get_json_files(folder):
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.json')]

# 主題分類
def classify_topic(text):
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

# 八大情感分類
def classify_emotions(tokens):
    emo_count = {k:0 for k in PLUTCHIK_EMOTIONS}
    for token in tokens:
        for emo, words in PLUTCHIK_EMOTIONS.items():
            if token in words:
                emo_count[emo] += 1
    return emo_count

# 新增甜甜圈圖函數

def plot_sentiment_polarity_doughnut(topic_emotion_counter):
    """繪製全體評論的正負中立甜甜圈圖（美化配色與標籤）"""
    polarity_counter = Counter({'正向':0, '中立':0, '負向':0})
    for topic, emo_counter in topic_emotion_counter.items():
        for emo, count in emo_counter.items():
            polarity = EMOTION_POLARITY.get(emo, '中立')
            polarity_counter[polarity] += count
    total = sum(polarity_counter.values())
    if total == 0:
        print('❌ 沒有可用的情感數據')
        return
    labels = list(polarity_counter.keys())
    sizes = [polarity_counter[k] for k in labels]
    colors = ['#4ECDC4', '#FFD93D', '#FF6B6B']
    explode = [0.03, 0.03, 0.03]
    fig, ax = plt.subplots(figsize=(7,7))
    wedges, texts = ax.pie(
        sizes, labels=None, autopct=None,
        startangle=90, colors=colors, explode=explode,
        wedgeprops={'width':0.4, 'edgecolor':'white'}, textprops={'fontsize':16, 'fontweight':'bold'}
    )
    # 自訂標籤顏色與位置
    for i, (w, label, color) in enumerate(zip(wedges, labels, colors)):
        ang = (w.theta2 + w.theta1)/2
        x = np.cos(np.deg2rad(ang)) * 1.1
        y = np.sin(np.deg2rad(ang)) * 1.1
        ax.text(x, y, f"{label}\n{sizes[i]} ({sizes[i]/total:.1%})", ha='center', va='center', fontsize=18, fontweight='bold', color=color, bbox=dict(facecolor='white', edgecolor=color, boxstyle='round,pad=0.3', alpha=0.7))
    # 圖中央主題
    ax.text(0, 0, '全部評論', ha='center', va='center', fontsize=22, fontweight='bold', color='#2C3E50')
    ax.set_title('全體評論情感正負中立分布', fontsize=20, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig('sentiment_polarity_doughnut.png', dpi=300, bbox_inches='tight', facecolor='white')
    print('🍩 甜甜圈圖已保存為 sentiment_polarity_doughnut.png')
    plt.show()

def plot_topic_sentiment_polarity_doughnut(topic_emotion_counter, topic):
    """針對單一主題繪製正負中立甜甜圈圖（美化配色與標籤）"""
    polarity_counter = Counter({'正向':0, '中立':0, '負向':0})
    emo_counter = topic_emotion_counter.get(topic, {})
    for emo, count in emo_counter.items():
        polarity = EMOTION_POLARITY.get(emo, '中立')
        polarity_counter[polarity] += count
    total = sum(polarity_counter.values())
    if total == 0:
        print(f'❌ {topic} 沒有可用的情感數據')
        return
    labels = list(polarity_counter.keys())
    sizes = [polarity_counter[k] for k in labels]
    colors = ['#4ECDC4', '#FFD93D', '#FF6B6B']
    explode = [0.03, 0.03, 0.03]
    fig, ax = plt.subplots(figsize=(7,7))
    wedges, texts = ax.pie(
        sizes, labels=None, autopct=None,
        startangle=90, colors=colors, explode=explode,
        wedgeprops={'width':0.4, 'edgecolor':'white'}, textprops={'fontsize':16, 'fontweight':'bold'}
    )
    for i, (w, label, color) in enumerate(zip(wedges, labels, colors)):
        ang = (w.theta2 + w.theta1)/2
        x = np.cos(np.deg2rad(ang)) * 1.1
        y = np.sin(np.deg2rad(ang)) * 1.1
        ax.text(x, y, f"{label}\n{sizes[i]} ({sizes[i]/total:.1%})", ha='center', va='center', fontsize=18, fontweight='bold', color=color, bbox=dict(facecolor='white', edgecolor=color, boxstyle='round,pad=0.3', alpha=0.7))
    ax.text(0, 0, topic, ha='center', va='center', fontsize=22, fontweight='bold', color='#2C3E50')
    ax.set_title(f'{topic} 主題情感正負中立分布', fontsize=20, fontweight='bold', pad=20)
    plt.tight_layout()
    fname = f'sentiment_polarity_doughnut_{topic}.png'
    plt.savefig(fname, dpi=300, bbox_inches='tight', facecolor='white')
    print(f'🍩 甜甜圈圖已保存為 {fname}')
    plt.show()

if __name__ == '__main__':
    folder = './comment_data'
    files = get_json_files(folder)
    topic_emotion_counter = defaultdict(lambda: Counter({k:0 for k in PLUTCHIK_EMOTIONS}))
    topic_total = Counter()

    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception:
                continue
            # 支援多種格式
            if isinstance(data, dict):
                texts = [v for v in data.values() if isinstance(v, str)]
            elif isinstance(data, list):
                texts = []
                for item in data:
                    if isinstance(item, dict):
                        texts += [v for v in item.values() if isinstance(v, str)]
            else:
                continue
            for text in texts:
                tokens = list(jieba.cut(text))
                topic = classify_topic(text)
                emo_count = classify_emotions(tokens)
                topic_emotion_counter[topic].update(emo_count)
                topic_total[topic] += 1

    # 統計比例
    topic_emo_ratio = {}
    for topic, emo_counter in topic_emotion_counter.items():
        total = sum(emo_counter.values())
        if total == 0:
            topic_emo_ratio[topic] = [0]*8
        else:
            topic_emo_ratio[topic] = [emo_counter[emo]/total for emo in PLUTCHIK_EMOTIONS]

    # 畫圖
    labels = list(PLUTCHIK_EMOTIONS.keys())
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    plt.figure(figsize=(8,8))
    ax = plt.subplot(111, polar=True)
    for topic, ratios in topic_emo_ratio.items():
        values = ratios + ratios[:1]
        ax.plot(angles, values, label=topic, color=TOPIC_COLORS.get(topic,'#888'), linewidth=2)
        ax.fill(angles, values, color=TOPIC_COLORS.get(topic,'#888'), alpha=0.15)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    plt.title('多主題八大情感分布圖譜', fontsize=16)
    plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    plt.tight_layout()
    plt.show()

    # 新增：繪製正負中立甜甜圈圖
    plot_sentiment_polarity_doughnut(topic_emotion_counter)
    # 商業與教育主題細看
    for t in ['商業', '教育']:
        plot_topic_sentiment_polarity_doughnut(topic_emotion_counter, t) 