"""
監控 RAG 評估腳本進度
每 10 分鐘檢查一次
"""

import os
import time
import subprocess
import json
from datetime import datetime

def check_progress():
    """檢查進度"""
    print(f"\n{'='*60}")
    print(f"進度檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # 1. 檢查腳本是否還在運行
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        regar_processes = [line for line in lines if 'regar_complete.py' in line and 'grep' not in line]
        
        if regar_processes:
            print("✅ RAG 評估腳本正在運行")
            for process in regar_processes:
                parts = process.split()
                if len(parts) >= 10:
                    pid = parts[1]
                    cpu = parts[2]
                    mem = parts[3]
                    time_str = parts[8]
                    print(f"   PID: {pid}, CPU: {cpu}%, 記憶體: {mem}%, 運行時間: {time_str}")
        else:
            print("❌ RAG 評估腳本已停止")
            return False
    except Exception as e:
        print(f"❌ 檢查進程時出錯: {e}")
        return False
    
    # 2. 檢查輸出文件
    runs_dir = "runs"
    if os.path.exists(runs_dir):
        files = os.listdir(runs_dir)
        json_files = [f for f in files if f.endswith('.json')]
        if json_files:
            print(f"✅ 發現輸出文件: {len(json_files)} 個")
            for file in json_files:
                file_path = os.path.join(runs_dir, file)
                file_size = os.path.getsize(file_path)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"   📄 {file} ({file_size} bytes, 修改時間: {file_time.strftime('%H:%M:%S')})")
                
                # 嘗試讀取文件內容摘要
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'metadata' in data:
                            total_questions = data['metadata'].get('total_questions', 0)
                            print(f"      📊 總問題數: {total_questions}")
                        
                        # 檢查各評估方法的進度
                        for method in ['baseline', 'naive_rag', 'ragas_style']:
                            if method in data:
                                count = len(data[method])
                                print(f"      📈 {method}: {count}/{total_questions} 完成")
                except Exception as e:
                    print(f"      ⚠️ 讀取文件時出錯: {e}")
        else:
            print("⏳ 尚未生成輸出文件")
    else:
        print("❌ runs 目錄不存在")
    
    # 3. 檢查系統資源
    try:
        result = subprocess.run(['free', '-h'], capture_output=True, text=True)
        print("\n💾 系統記憶體使用情況:")
        print(result.stdout)
    except Exception as e:
        print(f"❌ 檢查記憶體時出錯: {e}")
    
    # 4. 檢查磁碟空間
    try:
        result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True)
        print("\n💿 磁碟空間使用情況:")
        print(result.stdout)
    except Exception as e:
        print(f"❌ 檢查磁碟空間時出錯: {e}")
    
    return True

def main():
    """主函數"""
    print("🔍 開始監控 RAG 評估進度")
    print("⏰ 每 10 分鐘檢查一次")
    
    check_count = 0
    while True:
        check_count += 1
        print(f"\n🔄 第 {check_count} 次檢查")
        
        is_running = check_progress()
        
        if not is_running:
            print("\n🎉 RAG 評估已完成或已停止！")
            break
        
        print(f"\n⏳ 等待 10 分鐘後進行下次檢查...")
        print(f"下次檢查時間: {(datetime.now().timestamp() + 600):.0f}")
        
        # 等待 10 分鐘
        time.sleep(600)

if __name__ == "__main__":
    main() 