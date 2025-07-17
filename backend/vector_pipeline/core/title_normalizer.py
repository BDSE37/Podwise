#!/usr/bin/env python3
"""
標題標準化核心模組
統一處理 podcast 節目標題格式，確保資料庫與檔案標題一致
"""

import os
import json
import re
import shutil
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

logger = logging.getLogger(__name__)

class TitleNormalizer:
    """
    標題標準化處理器
    統一處理 stage3、stage4 檔案與資料庫的標題格式
    """
    
    def __init__(self, base_dir: Optional[Path] = None, db_config: Optional[Dict] = None):
        """
        初始化標題標準化器
        
        Args:
            base_dir: 資料目錄路徑，預設為當前目錄的 data 資料夾
            db_config: 資料庫連線設定
        """
        self.base_dir = base_dir or Path(__file__).parent.parent / "data"
        self.stage3_dir = self.base_dir / "stage3_tagging"
        self.stage4_dir = self.base_dir / "stage4_embedding_prep"
        
        # 預設資料庫連線設定 (k8s worker1)
        self.db_config = db_config or {
            'host': '192.168.32.56',
            'port': 32432,
            'database': 'podcast',
            'user': 'bdse37',
            'password': '111111'
        }
        
        # 統計資訊
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'updated_titles': 0,
            'db_updates': 0
        }
    
    def get_db_connection(self):
        """建立資料庫連線"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"資料庫連線失敗: {e}")
            return None
    
    def normalize_title(self, title: str) -> str:
        """
        統一處理標題格式
        1. 將空白一律改成底線
        2. 統一 EP/ep 格式為大寫 EP
        3. 處理特殊字符
        4. 移除多餘的底線
        
        Args:
            title: 原始標題
            
        Returns:
            標準化後的標題
        """
        if not title:
            return title
            
        # 1. 將空白改成底線
        normalized = title.replace(' ', '_')
        
        # 2. 統一 EP/ep 格式為大寫 EP（必須在移除特殊字符之前）
        # 處理 Ep.2 這種格式
        normalized = re.sub(r'\b(ep|Ep|EP)\.(\d+)', r'EP\2', normalized, flags=re.IGNORECASE)
        # 處理 ep_2 這種格式
        normalized = re.sub(r'\b(ep|Ep|EP)_(\d+)', r'EP\2', normalized, flags=re.IGNORECASE)
        # 處理 ep2 這種格式
        normalized = re.sub(r'\b(ep|Ep|EP)(\d+)', r'EP\2', normalized, flags=re.IGNORECASE)
        
        # 3. 處理特殊字符
        # 移除或替換特殊字符
        normalized = re.sub(r'[^\w\-_\.]', '', normalized)  # 只保留字母、數字、底線、連字號、點
        
        # 4. 處理常見的特殊情況
        normalized = normalized.replace('feat.', 'feat')
        normalized = normalized.replace('ft.', 'ft')
        
        # 5. 移除多餘的底線
        normalized = re.sub(r'_+', '_', normalized)  # 多個連續底線變成一個
        normalized = normalized.strip('_')  # 移除開頭和結尾的底線
        
        return normalized
    
    def extract_info_from_filename(self, filename: str) -> Tuple[Optional[int], Optional[str]]:
        """
        從檔案名提取 podcast_id 和 episode_title
        
        Args:
            filename: 檔案名
            
        Returns:
            (podcast_id, episode_title) 或 (None, None)
        """
        try:
            # 範例: RSS_262026947_podcast_1304_Bitter food better health_.json
            match = re.match(r'RSS_(\d+)_podcast_\d+_(.+?)\.json', filename)
            if match:
                podcast_id = int(match.group(1))
                episode_title = match.group(2).strip()
                return podcast_id, episode_title
            return None, None
        except Exception as e:
            logger.error(f"解析檔案名失敗 {filename}: {e}")
            return None, None
    
    def update_database_titles(self) -> bool:
        """
        更新資料庫中的 episode 標題
        
        Returns:
            是否成功更新
        """
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 查詢所有 episode 標題
                cursor.execute("""
                    SELECT episode_id, episode_title, podcast_id 
                    FROM episodes 
                    WHERE episode_title IS NOT NULL
                """)
                episodes = cursor.fetchall()
                
                logger.info(f"找到 {len(episodes)} 個 episode 需要處理")
                
                updated_count = 0
                for episode in episodes:
                    original_title = episode['episode_title']
                    normalized_title = self.normalize_title(original_title)
                    
                    if original_title != normalized_title:
                        try:
                            # 更新資料庫
                            cursor.execute("""
                                UPDATE episodes 
                                SET episode_title = %s, updated_at = NOW()
                                WHERE episode_id = %s
                            """, (normalized_title, episode['episode_id']))
                            
                            updated_count += 1
                            logger.info(f"更新 episode {episode['episode_id']}: '{original_title}' -> '{normalized_title}'")
                            
                        except Exception as e:
                            logger.error(f"更新 episode {episode['episode_id']} 失敗: {e}")
                
                conn.commit()
                logger.info(f"資料庫更新完成，共更新 {updated_count} 個標題")
                self.stats['db_updates'] = updated_count
                return True
                
        except Exception as e:
            logger.error(f"更新資料庫標題失敗: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def process_stage3_files(self) -> bool:
        """
        處理 stage3 檔案，更新標題並重新命名檔案
        
        Returns:
            是否成功處理
        """
        logger.info("開始處理 stage3 檔案...")
        
        # 掃描所有 stage3 檔案
        stage3_files = []
        for rss_dir in self.stage3_dir.iterdir():
            if rss_dir.is_dir() and rss_dir.name.startswith('RSS_'):
                for json_file in rss_dir.glob('*.json'):
                    if json_file.name.endswith('.json'):
                        stage3_files.append(json_file)
        
        logger.info(f"找到 {len(stage3_files)} 個 stage3 檔案")
        self.stats['total_files'] = len(stage3_files)
        
        success_count = 0
        for file_path in stage3_files:
            try:
                logger.info(f"處理檔案: {file_path.name}")
                
                # 提取原始資訊
                podcast_id, original_title = self.extract_info_from_filename(file_path.name)
                if not podcast_id or not original_title:
                    logger.error(f"無法解析檔案名: {file_path.name}")
                    self.stats['failed_files'] += 1
                    continue
                
                # 標準化標題
                normalized_title = self.normalize_title(original_title)
                
                if original_title != normalized_title:
                    logger.info(f"標題標準化: '{original_title}' -> '{normalized_title}'")
                    self.stats['updated_titles'] += 1
                
                # 讀取檔案內容
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 更新檔案內容中的標題（如果有）
                if isinstance(data, dict) and 'chunks' in data:
                    for chunk in data['chunks']:
                        if isinstance(chunk, dict) and 'episode_title' in chunk:
                            chunk['episode_title'] = normalized_title
                
                # 建立新的檔案名
                new_filename = f"RSS_{podcast_id}_podcast_1304_{normalized_title}.json"
                new_file_path = file_path.parent / new_filename
                
                # 如果檔案名有變化，重新命名
                if file_path.name != new_filename:
                    # 先備份原檔案
                    backup_path = file_path.with_suffix('.json.backup')
                    shutil.copy2(file_path, backup_path)
                    
                    # 寫入更新後的內容
                    with open(new_file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    # 刪除原檔案
                    file_path.unlink()
                    
                    logger.info(f"檔案重新命名: {file_path.name} -> {new_filename}")
                else:
                    # 檔案名沒變，只更新內容
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                success_count += 1
                self.stats['processed_files'] += 1
                
            except Exception as e:
                logger.error(f"處理檔案失敗 {file_path.name}: {e}")
                self.stats['failed_files'] += 1
        
        logger.info(f"stage3 處理完成，成功: {success_count}, 失敗: {self.stats['failed_files']}")
        return success_count > 0
    
    def process_stage4_files(self) -> bool:
        """
        處理 stage4 檔案，更新標題並重新命名檔案
        
        Returns:
            是否成功處理
        """
        logger.info("開始處理 stage4 檔案...")
        
        # 掃描所有 stage4 檔案
        stage4_files = []
        for json_file in self.stage4_dir.glob('*_milvus.json'):
            stage4_files.append(json_file)
        
        logger.info(f"找到 {len(stage4_files)} 個 stage4 檔案")
        
        success_count = 0
        for file_path in stage4_files:
            try:
                logger.info(f"處理 stage4 檔案: {file_path.name}")
                
                # 提取原始資訊（移除 _milvus 後綴）
                base_filename = file_path.name.replace('_milvus.json', '.json')
                podcast_id, original_title = self.extract_info_from_filename(base_filename)
                if not podcast_id or not original_title:
                    logger.error(f"無法解析檔案名: {file_path.name}")
                    continue
                
                # 標準化標題
                normalized_title = self.normalize_title(original_title)
                
                if original_title != normalized_title:
                    logger.info(f"標題標準化: '{original_title}' -> '{normalized_title}'")
                
                # 讀取檔案內容
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 更新檔案內容中的標題
                if isinstance(data, dict) and 'chunks' in data:
                    for chunk in data['chunks']:
                        if isinstance(chunk, dict) and 'episode_title' in chunk:
                            chunk['episode_title'] = normalized_title
                
                # 建立新的檔案名
                new_filename = f"RSS_{podcast_id}_podcast_1304_{normalized_title}_milvus.json"
                new_file_path = file_path.parent / new_filename
                
                # 如果檔案名有變化，重新命名
                if file_path.name != new_filename:
                    # 先備份原檔案
                    backup_path = file_path.with_suffix('.milvus.json.backup')
                    shutil.copy2(file_path, backup_path)
                    
                    # 寫入更新後的內容
                    with open(new_file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    # 刪除原檔案
                    file_path.unlink()
                    
                    logger.info(f"檔案重新命名: {file_path.name} -> {new_filename}")
                else:
                    # 檔案名沒變，只更新內容
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"處理 stage4 檔案失敗 {file_path.name}: {e}")
        
        logger.info(f"stage4 處理完成，成功: {success_count}")
        return success_count > 0
    
    def generate_report(self) -> str:
        """
        生成處理報告
        
        Returns:
            報告內容
        """
        report = f"""
=== 標題標準化處理報告 ===
處理時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

統計資訊:
- 總檔案數: {self.stats['total_files']}
- 成功處理: {self.stats['processed_files']}
- 處理失敗: {self.stats['failed_files']}
- 標題更新: {self.stats['updated_titles']}
- 資料庫更新: {self.stats['db_updates']}

處理規則:
1. 空白字符一律改成底線 (_)
2. 移除特殊字符 (只保留字母、數字、底線、連字號、點)
3. 處理常見縮寫 (feat. -> feat, ft. -> ft)
4. 移除多餘的底線
5. 統一 EP/ep 格式為大寫 EP

處理範圍:
- PostgreSQL episodes 表
- stage3_tagging 目錄
- stage4_embedding_prep 目錄
"""
        
        # 寫入報告檔案
        report_file = Path(__file__).parent.parent / 'title_normalization_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"處理報告已寫入 {report_file}")
        return report
    
    def run(self) -> bool:
        """
        執行完整的標題標準化流程
        
        Returns:
            是否全部成功
        """
        logger.info("開始標題標準化處理...")
        
        success = True
        
        # 1. 更新資料庫標題
        logger.info("步驟 1: 更新資料庫標題")
        if not self.update_database_titles():
            success = False
        
        # 2. 處理 stage3 檔案
        logger.info("步驟 2: 處理 stage3 檔案")
        if not self.process_stage3_files():
            success = False
        
        # 3. 處理 stage4 檔案
        logger.info("步驟 3: 處理 stage4 檔案")
        if not self.process_stage4_files():
            success = False
        
        # 4. 生成報告
        logger.info("步驟 4: 生成處理報告")
        self.generate_report()
        
        logger.info("標題標準化處理完成！")
        return success 