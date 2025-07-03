#!/usr/bin/env python3
"""
A/B 測試模組
用於比較不同代理組合、模型配置、參數設定的效果
"""

import logging
import random
import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics
import os

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ABTestConfig:
    """A/B 測試配置"""
    test_id: str
    name: str
    description: str
    variants: List[Dict[str, Any]]
    traffic_split: List[float]  # 各變體的流量分配比例
    start_date: datetime
    end_date: Optional[datetime] = None
    is_active: bool = True
    min_sample_size: int = 100
    confidence_level: float = 0.95

@dataclass
class ABTestResult:
    """A/B 測試結果"""
    test_id: str
    variant_name: str
    sample_size: int
    success_rate: float
    average_response_time: float
    average_confidence: float
    fallback_rate: float
    user_satisfaction: Optional[float] = None

class ABTestingManager:
    """
    A/B 測試管理器
    管理多個 A/B 測試，分配流量，收集結果，進行統計分析
    """
    
    def __init__(self, 
                 tests_file: str = "ab_tests.json",
                 results_file: str = "ab_test_results.json"):
        """
        初始化 A/B 測試管理器
        
        Args:
            tests_file: 測試配置檔案路徑
            results_file: 測試結果檔案路徑
        """
        self.tests_file = tests_file
        self.results_file = results_file
        
        # 測試配置和結果儲存
        self.active_tests: Dict[str, ABTestConfig] = {}
        self.test_results: Dict[str, List[ABTestResult]] = defaultdict(list)
        self.user_assignments: Dict[str, str] = {}  # user_id -> variant_name
        
        # 載入現有測試
        self._load_tests()
        self._load_results()
        
        logger.info("✅ A/B 測試管理器初始化完成")
    
    def _load_tests(self):
        """載入測試配置"""
        try:
            if os.path.exists(self.tests_file):
                with open(self.tests_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for test_data in data.get('tests', []):
                        test = ABTestConfig(
                            test_id=test_data['test_id'],
                            name=test_data['name'],
                            description=test_data['description'],
                            variants=test_data['variants'],
                            traffic_split=test_data['traffic_split'],
                            start_date=datetime.fromisoformat(test_data['start_date']),
                            end_date=datetime.fromisoformat(test_data['end_date']) if test_data.get('end_date') else None,
                            is_active=test_data.get('is_active', True),
                            min_sample_size=test_data.get('min_sample_size', 100),
                            confidence_level=test_data.get('confidence_level', 0.95)
                        )
                        if test.is_active and (test.end_date is None or test.end_date > datetime.now()):
                            self.active_tests[test.test_id] = test
                
                logger.info(f"✅ 載入 {len(self.active_tests)} 個活躍 A/B 測試")
        except Exception as e:
            logger.warning(f"⚠️ 載入測試配置失敗: {e}")
    
    def _load_results(self):
        """載入測試結果"""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for test_id, results_data in data.get('results', {}).items():
                        for result_data in results_data:
                            result = ABTestResult(
                                test_id=result_data['test_id'],
                                variant_name=result_data['variant_name'],
                                sample_size=result_data['sample_size'],
                                success_rate=result_data['success_rate'],
                                average_response_time=result_data['average_response_time'],
                                average_confidence=result_data['average_confidence'],
                                fallback_rate=result_data['fallback_rate'],
                                user_satisfaction=result_data.get('user_satisfaction')
                            )
                            self.test_results[test_id].append(result)
                
                logger.info(f"✅ 載入 {sum(len(results) for results in self.test_results.values())} 個測試結果")
        except Exception as e:
            logger.warning(f"⚠️ 載入測試結果失敗: {e}")
    
    def _save_tests(self):
        """儲存測試配置"""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'tests': [asdict(test) for test in self.active_tests.values()]
            }
            
            with open(self.tests_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ 儲存測試配置失敗: {e}")
    
    def _save_results(self):
        """儲存測試結果"""
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'results': {
                    test_id: [asdict(result) for result in results]
                    for test_id, results in self.test_results.items()
                }
            }
            
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ 儲存測試結果失敗: {e}")
    
    def create_test(self, 
                   name: str,
                   description: str,
                   variants: List[Dict[str, Any]],
                   traffic_split: Optional[List[float]] = None,
                   duration_days: int = 7,
                   min_sample_size: int = 100) -> str:
        """
        創建新的 A/B 測試
        
        Args:
            name: 測試名稱
            description: 測試描述
            variants: 變體配置列表
            traffic_split: 流量分配比例
            duration_days: 測試持續天數
            min_sample_size: 最小樣本大小
            
        Returns:
            測試 ID
        """
        test_id = str(uuid.uuid4())
        
        # 驗證變體數量
        if len(variants) < 2:
            raise ValueError("至少需要 2 個變體進行 A/B 測試")
        
        # 設定流量分配
        if traffic_split is None:
            traffic_split = [1.0 / len(variants)] * len(variants)
        
        if len(traffic_split) != len(variants):
            raise ValueError("流量分配比例數量必須與變體數量相同")
        
        if abs(sum(traffic_split) - 1.0) > 0.01:
            raise ValueError("流量分配比例總和必須為 1.0")
        
        # 創建測試配置
        test = ABTestConfig(
            test_id=test_id,
            name=name,
            description=description,
            variants=variants,
            traffic_split=traffic_split,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=duration_days),
            is_active=True,
            min_sample_size=min_sample_size
        )
        
        self.active_tests[test_id] = test
        self._save_tests()
        
        logger.info(f"✅ 創建 A/B 測試: {name} (ID: {test_id})")
        return test_id
    
    def get_variant_for_user(self, test_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        為用戶分配測試變體
        
        Args:
            test_id: 測試 ID
            user_id: 用戶 ID
            
        Returns:
            變體配置
        """
        if test_id not in self.active_tests:
            return None
        
        test = self.active_tests[test_id]
        
        # 檢查測試是否仍在進行
        if not test.is_active or (test.end_date and test.end_date < datetime.now()):
            return None
        
        # 檢查用戶是否已有分配
        assignment_key = f"{test_id}:{user_id}"
        if assignment_key in self.user_assignments:
            variant_name = self.user_assignments[assignment_key]
            return next((v for v in test.variants if v['name'] == variant_name), None)
        
        # 根據流量分配隨機選擇變體
        variant_index = self._select_variant_by_traffic(test.traffic_split)
        selected_variant = test.variants[variant_index]
        
        # 記錄用戶分配
        self.user_assignments[assignment_key] = selected_variant['name']
        
        logger.info(f"📊 用戶 {user_id} 分配到測試 {test_id} 的變體: {selected_variant['name']}")
        
        return selected_variant
    
    def _select_variant_by_traffic(self, traffic_split: List[float]) -> int:
        """根據流量分配選擇變體"""
        rand = random.random()
        cumulative = 0.0
        
        for i, split in enumerate(traffic_split):
            cumulative += split
            if rand <= cumulative:
                return i
        
        return len(traffic_split) - 1
    
    def record_test_result(self, 
                          test_id: str,
                          user_id: str,
                          variant_name: str,
                          success: bool,
                          response_time: float,
                          confidence: float,
                          fallback_used: bool,
                          user_satisfaction: Optional[float] = None):
        """
        記錄測試結果
        
        Args:
            test_id: 測試 ID
            user_id: 用戶 ID
            variant_name: 變體名稱
            success: 是否成功
            response_time: 響應時間
            confidence: 信心值
            fallback_used: 是否使用備援
            user_satisfaction: 用戶滿意度
        """
        if test_id not in self.active_tests:
            return
        
        # 這裡可以擴展為更詳細的結果記錄
        # 目前簡化為定期統計
        logger.info(f"📊 記錄測試結果: {test_id} - {variant_name} - {'成功' if success else '失敗'}")
    
    def get_test_statistics(self, test_id: str) -> Dict[str, Any]:
        """
        獲取測試統計數據
        
        Args:
            test_id: 測試 ID
            
        Returns:
            測試統計數據
        """
        if test_id not in self.active_tests:
            return {"error": "測試不存在"}
        
        test = self.active_tests[test_id]
        results = self.test_results[test_id]
        
        # 按變體分組結果
        variant_stats = defaultdict(list)
        for result in results:
            variant_stats[result.variant_name].append(result)
        
        # 計算各變體的統計數據
        variant_analysis = {}
        for variant_name, variant_results in variant_stats.items():
            if not variant_results:
                continue
            
            # 計算平均值
            avg_success_rate = statistics.mean(r.success_rate for r in variant_results)
            avg_response_time = statistics.mean(r.average_response_time for r in variant_results)
            avg_confidence = statistics.mean(r.average_confidence for r in variant_results)
            avg_fallback_rate = statistics.mean(r.fallback_rate for r in variant_results)
            
            variant_analysis[variant_name] = {
                "sample_size": sum(r.sample_size for r in variant_results),
                "avg_success_rate": avg_success_rate,
                "avg_response_time": avg_response_time,
                "avg_confidence": avg_confidence,
                "avg_fallback_rate": avg_fallback_rate,
                "total_results": len(variant_results)
            }
        
        return {
            "test_id": test_id,
            "test_name": test.name,
            "description": test.description,
            "start_date": test.start_date.isoformat(),
            "end_date": test.end_date.isoformat() if test.end_date else None,
            "is_active": test.is_active,
            "variants": test.variants,
            "traffic_split": test.traffic_split,
            "variant_analysis": variant_analysis,
            "total_results": len(results)
        }
    
    def is_test_significant(self, test_id: str) -> Dict[str, Any]:
        """
        檢查測試結果是否具有統計顯著性
        
        Args:
            test_id: 測試 ID
            
        Returns:
            顯著性分析結果
        """
        if test_id not in self.active_tests:
            return {"error": "測試不存在"}
        
        test = self.active_tests[test_id]
        results = self.test_results[test_id]
        
        if len(results) < 2:
            return {"error": "結果數據不足"}
        
        # 簡單的顯著性檢驗（可以擴展為更複雜的統計檢驗）
        variant_stats = defaultdict(list)
        for result in results:
            variant_stats[result.variant_name].append(result)
        
        # 比較各變體的成功率
        success_rates = {}
        for variant_name, variant_results in variant_stats.items():
            if variant_results:
                avg_success_rate = statistics.mean(r.success_rate for r in variant_results)
                success_rates[variant_name] = avg_success_rate
        
        # 找出最佳和最差變體
        if len(success_rates) >= 2:
            best_variant = max(success_rates.items(), key=lambda x: x[1])
            worst_variant = min(success_rates.items(), key=lambda x: x[1])
            
            improvement = best_variant[1] - worst_variant[1]
            
            return {
                "is_significant": improvement > 0.05,  # 5% 的改善閾值
                "best_variant": best_variant[0],
                "best_success_rate": best_variant[1],
                "worst_variant": worst_variant[0],
                "worst_success_rate": worst_variant[1],
                "improvement": improvement,
                "confidence_level": test.confidence_level
            }
        
        return {"error": "變體數據不足"}
    
    def end_test(self, test_id: str) -> bool:
        """
        結束測試
        
        Args:
            test_id: 測試 ID
            
        Returns:
            是否成功結束
        """
        if test_id not in self.active_tests:
            return False
        
        test = self.active_tests[test_id]
        test.is_active = False
        test.end_date = datetime.now()
        
        self._save_tests()
        
        logger.info(f"✅ 結束 A/B 測試: {test.name} (ID: {test_id})")
        return True
    
    def get_active_tests(self) -> List[Dict[str, Any]]:
        """
        獲取所有活躍的測試
        
        Returns:
            活躍測試列表
        """
        return [
            {
                "test_id": test.test_id,
                "name": test.name,
                "description": test.description,
                "start_date": test.start_date.isoformat(),
                "end_date": test.end_date.isoformat() if test.end_date else None,
                "variants": test.variants,
                "traffic_split": test.traffic_split
            }
            for test in self.active_tests.values()
            if test.is_active
        ]
    
    def cleanup_old_tests(self, days: int = 30):
        """
        清理舊的測試數據
        
        Args:
            days: 保留天數
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 清理過期的測試
        expired_tests = [
            test_id for test_id, test in self.active_tests.items()
            if test.end_date and test.end_date < cutoff_date
        ]
        
        for test_id in expired_tests:
            del self.active_tests[test_id]
            if test_id in self.test_results:
                del self.test_results[test_id]
        
        # 清理用戶分配
        expired_assignments = [
            key for key in self.user_assignments.keys()
            if key.split(':')[0] in expired_tests
        ]
        
        for key in expired_assignments:
            del self.user_assignments[key]
        
        if expired_tests:
            self._save_tests()
            self._save_results()
            logger.info(f"🧹 清理了 {len(expired_tests)} 個過期測試") 