"""
Episodes 處理測試腳本

測試表情符號清理和資料處理功能
"""

import json
import os
import sys
from episode_processor import EpisodeProcessor


def test_emoji_cleaning():
    """測試表情符號清理功能"""
    print("=== 測試表情符號清理 ===")
    
    processor = EpisodeProcessor()
    
    # 測試案例
    test_cases = [
        {
            "input": "EP001 | AI智慧工廠的天時地利人和即將到來？！🚀",
            "expected": "EP001 | AI智慧工廠的天時地利人和即將到來？！"
        },
        {
            "input": "Can climate change affect our mental health? 😰",
            "expected": "Can climate change affect our mental health?"
        },
        {
            "input": "How important is politeness? 😊",
            "expected": "How important is politeness?"
        },
        {
            "input": "What's your favourite kind of noodle? 🍜",
            "expected": "What's your favourite kind of noodle?"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = processor.clean_emoji(case["input"])
        success = result == case["expected"]
        status = "✅" if success else "❌"
        print(f"{status} 測試 {i}: {result}")
        
        if not success:
            print(f"   預期: {case['expected']}")
            print(f"   實際: {result}")


def test_description_cleaning():
    """測試描述清理功能"""
    print("\n=== 測試描述清理 ===")
    
    processor = EpisodeProcessor()
    
    # 測試案例
    test_description = """
    <p>(01:40) Jeff與JJ的第一個交集：上市公司91-APP掛牌與投資小故事 <br /> <br />
    (06:30) Jeff加入AVA趨折離奇的故事 <br /> <br />
    IG:final36x <br />
    https://www.instagram.com/final36x?igsh=MXBuamlxZWJ2eTB2bQ%3D%3D&amp;utm_source=qr <br />
    留言告訴我你對這一集的想法： <a href="https://open.firstory.me/user/cmb39unbh0haz01y3f2gp7c1p/comments">https://open.firstory.me/user/cmb39unbh0haz01y3f2gp7c1p/comments</a></p> <br /> <br />
    Powered by <a href="https://firstory.me/zh">Firstory Hosting</a>
    """
    
    result = processor.clean_description(test_description)
    print(f"清理前: {test_description[:100]}...")
    print(f"清理後: {result[:100]}...")


def test_episode_number_extraction():
    """測試集數提取功能"""
    print("\n=== 測試集數提取 ===")
    
    processor = EpisodeProcessor()
    
    test_cases = [
        "EP001 | AI智慧工廠的天時地利人和即將到來？！",
        "EP002 | 川普關稅戰解碼：成因揭秘與結局猜想",
        "EP003 | V轉後的股匯債投資 Feat.財經M平方",
        "EP004 | 一集搞懂天使投資！ Feat. AVA天使投資創辦人JJ方俊傑",
        "Can climate change affect our mental health?",
        "How important is politeness?"
    ]
    
    for title in test_cases:
        episode_number = processor.extract_episode_number(title)
        print(f"標題: {title}")
        print(f"集數: {episode_number or '無'}")
        print()


def test_date_parsing():
    """測試日期解析功能"""
    print("=== 測試日期解析 ===")
    
    processor = EpisodeProcessor()
    
    test_dates = [
        "Wed, 25 Jun 2025 04:32:47 GMT",
        "Thu, 12 Jun 2025 07:14:00 +0000",
        "Thu, 05 Jun 2025 09:56:00 +0000",
        "2025-06-25 04:32:47",
        "2025-06-25"
    ]
    
    for date_str in test_dates:
        parsed_date = processor.parse_published_date(date_str)
        if parsed_date:
            print(f"原始: {date_str}")
            print(f"解析: {parsed_date}")
            print(f"年: {parsed_date.year}, 月: {parsed_date.month}, 日: {parsed_date.day}")
        else:
            print(f"無法解析: {date_str}")
        print()


def test_sample_processing():
    """測試樣本資料處理"""
    print("=== 測試樣本資料處理 ===")
    
    processor = EpisodeProcessor()
    
    # 建立測試資料
    test_episode = {
        "id": "test_episode_001",
        "title": "EP001 | AI智慧工廠的天時地利人和即將到來？！🚀",
        "published": "Wed, 25 Jun 2025 04:32:47 GMT",
        "description": "<p>(01:40) Jeff與JJ的第一個交集：上市公司91-APP掛牌與投資小故事 <br /> <br />IG:final36x <br />Powered by <a href=\"https://firstory.me/zh\">Firstory Hosting</a></p>",
        "audio_url": "https://example.com/audio.mp3"
    }
    
    channel_info = {
        'channel_id': '1304',
        'channel_name': '商業頻道',
        'category': 'business'
    }
    
    processed = processor.process_episode_data(test_episode, channel_info)
    
    print("處理結果:")
    for key, value in processed.items():
        print(f"  {key}: {value}")


def test_file_loading():
    """測試檔案載入功能"""
    print("\n=== 測試檔案載入 ===")
    
    processor = EpisodeProcessor()
    
    # 檢查 episodes 目錄
    episodes_dir = "episodes"
    if not os.path.exists(episodes_dir):
        print(f"❌ episodes 目錄不存在: {episodes_dir}")
        return
    
    # 檢查各頻道目錄
    for channel_name in ['business', 'evucation']:
        channel_dir = os.path.join(episodes_dir, channel_name)
        if os.path.exists(channel_dir):
            json_files = [f for f in os.listdir(channel_dir) if f.endswith('.json')]
            print(f"✅ {channel_name} 頻道: {len(json_files)} 個 JSON 檔案")
            
            # 測試載入第一個檔案
            if json_files:
                test_file = os.path.join(channel_dir, json_files[0])
                episodes = processor.load_json_file(test_file)
                print(f"   測試檔案 {json_files[0]}: {len(episodes)} 筆 episodes")
        else:
            print(f"❌ {channel_name} 頻道目錄不存在")


def main():
    """主測試函數"""
    print("Episodes 處理功能測試")
    print("=" * 50)
    
    # 執行各項測試
    test_emoji_cleaning()
    test_description_cleaning()
    test_episode_number_extraction()
    test_date_parsing()
    test_sample_processing()
    test_file_loading()
    
    print("\n" + "=" * 50)
    print("測試完成！")


if __name__ == "__main__":
    main() 