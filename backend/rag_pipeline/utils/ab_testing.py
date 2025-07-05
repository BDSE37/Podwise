#!/usr/bin/env python3
"""
A/B 測試模組

提供 A/B 測試功能，用於比較不同配置和策略的效果。

作者: Podwise Team
版本: 1.0.0
"""

import json
import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path

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
    """A/B 測試管理器"""
    
    def __init__(self, 
                 tests_file: str = "ab_tests.json",
                 results_file: str = "ab_test_results.json"):
        """初始化 A/B 測試管理器"""
        self.tests_file = tests_file
        self.results_file = results_file
        
        # 測試配置和結果
        self.tests: Dict[str, ABTestConfig] = {}
        self.results: Dict[str, List[ABTestResult]] = {}
        
        # 載入現有數據
        self._load_tests()
        self._load_results()
        
        logger.info("✅ A/B 測試管理器初始化完成")
    
    def _load_tests(self) -> None:
        """載入測試配置"""
        try:
            if Path(self.tests_file).exists():
                with open(self.tests_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for test_data in data.get("tests", []):
                    test = ABTestConfig(
                        test_id=test_data["test_id"],
                        name=test_data["name"],
                        description=test_data["description"],
                        variants=test_data["variants"],
                        traffic_split=test_data["traffic_split"],
                        start_date=datetime.fromisoformat(test_data["start_date"]),
                        end_date=datetime.fromisoformat(test_data["end_date"]) if test_data.get("end_date") else None,
                        is_active=test_data.get("is_active", True),
                        min_sample_size=test_data.get("min_sample_size", 100),
                        confidence_level=test_data.get("confidence_level", 0.95)
                    )
                    self.tests[test.test_id] = test
                
                logger.info(f"✅ 載入 {len(self.tests)} 個 A/B 測試配置")
            else:
                logger.info("📝 沒有找到現有的 A/B 測試配置檔案")
                
        except Exception as e:
            logger.error(f"❌ 載入 A/B 測試配置失敗: {e}")
    
    def _load_results(self) -> None:
        """載入測試結果"""
        try:
            if Path(self.results_file).exists():
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for test_id, results_data in data.get("results", {}).items():
                    results = []
                    for result_data in results_data:
                        result = ABTestResult(
                            test_id=result_data["test_id"],
                            variant_name=result_data["variant_name"],
                            sample_size=result_data["sample_size"],
                            success_rate=result_data["success_rate"],
                            average_response_time=result_data["average_response_time"],
                            average_confidence=result_data["average_confidence"],
                            fallback_rate=result_data["fallback_rate"],
                            user_satisfaction=result_data.get("user_satisfaction")
                        )
                        results.append(result)
                    
                    self.results[test_id] = results
                
                logger.info(f"✅ 載入 {len(self.results)} 個 A/B 測試結果")
            else:
                logger.info("📝 沒有找到現有的 A/B 測試結果檔案")
                
        except Exception as e:
            logger.error(f"❌ 載入 A/B 測試結果失敗: {e}")
    
    def _save_tests(self) -> None:
        """儲存測試配置"""
        try:
            data = {
                "tests": [
                    {
                        "test_id": test.test_id,
                        "name": test.name,
                        "description": test.description,
                        "variants": test.variants,
                        "traffic_split": test.traffic_split,
                        "start_date": test.start_date.isoformat(),
                        "end_date": test.end_date.isoformat() if test.end_date else None,
                        "is_active": test.is_active,
                        "min_sample_size": test.min_sample_size,
                        "confidence_level": test.confidence_level
                    }
                    for test in self.tests.values()
                ]
            }
            
            with open(self.tests_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ 儲存 A/B 測試配置失敗: {e}")
    
    def _save_results(self) -> None:
        """儲存測試結果"""
        try:
            data = {
                "results": {
                    test_id: [
                        {
                            "test_id": result.test_id,
                            "variant_name": result.variant_name,
                            "sample_size": result.sample_size,
                            "success_rate": result.success_rate,
                            "average_response_time": result.average_response_time,
                            "average_confidence": result.average_confidence,
                            "fallback_rate": result.fallback_rate,
                            "user_satisfaction": result.user_satisfaction
                        }
                        for result in results
                    ]
                    for test_id, results in self.results.items()
                }
            }
            
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ 儲存 A/B 測試結果失敗: {e}")
    
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
        # 生成測試 ID
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        
        # 設定流量分配
        if traffic_split is None:
            traffic_split = [1.0 / len(variants)] * len(variants)
        
        # 驗證流量分配
        if abs(sum(traffic_split) - 1.0) > 0.01:
            raise ValueError("流量分配比例總和必須等於 1.0")
        
        if len(traffic_split) != len(variants):
            raise ValueError("流量分配比例數量必須與變體數量相同")
        
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
        
        # 儲存測試
        self.tests[test_id] = test
        self.results[test_id] = []
        self._save_tests()
        self._save_results()
        
        logger.info(f"✅ 創建 A/B 測試: {test_id} - {name}")
        return test_id
    
    def get_variant_for_user(self, test_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        為用戶分配變體
        
        Args:
            test_id: 測試 ID
            user_id: 用戶 ID
            
        Returns:
            變體配置
        """
        if test_id not in self.tests:
            logger.warning(f"⚠️ 測試 {test_id} 不存在")
            return None
        
        test = self.tests[test_id]
        
        # 檢查測試是否活躍
        if not test.is_active:
            logger.info(f"📝 測試 {test_id} 已停用")
            return None
        
        # 檢查測試時間
        now = datetime.now()
        if now < test.start_date:
            logger.info(f"📝 測試 {test_id} 尚未開始")
            return None
        
        if test.end_date and now > test.end_date:
            logger.info(f"📝 測試 {test_id} 已結束")
            return None
        
        # 基於用戶 ID 和流量分配選擇變體
        variant_index = self._select_variant_by_traffic(test.traffic_split, user_id)
        
        if 0 <= variant_index < len(test.variants):
            variant = test.variants[variant_index]
            logger.info(f"🎯 用戶 {user_id} 分配到測試 {test_id} 變體 {variant_index}")
            return variant
        else:
            logger.error(f"❌ 變體索引超出範圍: {variant_index}")
            return None
    
    def _select_variant_by_traffic(self, traffic_split: List[float], user_id: str) -> int:
        """
        根據流量分配選擇變體
        
        Args:
            traffic_split: 流量分配比例
            user_id: 用戶 ID
            
        Returns:
            變體索引
        """
        # 使用用戶 ID 的雜湊值確保一致性
        import hashlib
        user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        random.seed(user_hash)
        
        # 根據流量分配選擇變體
        rand_val = random.random()
        cumulative_prob = 0.0
        
        for i, prob in enumerate(traffic_split):
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                return i
        
        # 如果沒有匹配，返回最後一個變體
        return len(traffic_split) - 1
    
    def record_test_result(self, 
                          test_id: str,
                          user_id: str,
                          variant_name: str,
                          success: bool,
                          response_time: float,
                          confidence: float,
                          fallback_used: bool,
                          user_satisfaction: Optional[float] = None) -> None:
        """
        記錄測試結果
        
        Args:
            test_id: 測試 ID
            user_id: 用戶 ID
            variant_name: 變體名稱
            success: 是否成功
            response_time: 回應時間
            confidence: 信心度
            fallback_used: 是否使用備援
            user_satisfaction: 用戶滿意度
        """
        if test_id not in self.tests:
            logger.warning(f"⚠️ 測試 {test_id} 不存在")
            return
        
        # 這裡可以實現更複雜的結果記錄邏輯
        # 目前簡化為記錄到日誌
        logger.info(f"📊 記錄測試結果: {test_id} - {variant_name} - 用戶 {user_id}")
        logger.info(f"   成功: {success}, 回應時間: {response_time:.3f}s, 信心度: {confidence:.3f}")
    
    def get_test_statistics(self, test_id: str) -> Dict[str, Any]:
        """
        獲取測試統計資訊
        
        Args:
            test_id: 測試 ID
            
        Returns:
            測試統計
        """
        if test_id not in self.tests:
            return {"error": "測試不存在"}
        
        test = self.tests[test_id]
        results = self.results.get(test_id, [])
        
        # 計算統計資訊
        total_results = len(results)
        variant_stats = {}
        
        for result in results:
            variant_name = result.variant_name
            if variant_name not in variant_stats:
                variant_stats[variant_name] = {
                    "sample_size": 0,
                    "success_count": 0,
                    "total_response_time": 0.0,
                    "total_confidence": 0.0,
                    "fallback_count": 0,
                    "total_satisfaction": 0.0,
                    "satisfaction_count": 0
                }
            
            stats = variant_stats[variant_name]
            stats["sample_size"] += result.sample_size
            stats["success_count"] += int(result.success_rate * result.sample_size)
            stats["total_response_time"] += result.average_response_time * result.sample_size
            stats["total_confidence"] += result.average_confidence * result.sample_size
            stats["fallback_count"] += int(result.fallback_rate * result.sample_size)
            
            if result.user_satisfaction is not None:
                stats["total_satisfaction"] += result.user_satisfaction * result.sample_size
                stats["satisfaction_count"] += result.sample_size
        
        # 計算平均值
        for variant_name, stats in variant_stats.items():
            if stats["sample_size"] > 0:
                stats["success_rate"] = stats["success_count"] / stats["sample_size"]
                stats["avg_response_time"] = stats["total_response_time"] / stats["sample_size"]
                stats["avg_confidence"] = stats["total_confidence"] / stats["sample_size"]
                stats["fallback_rate"] = stats["fallback_count"] / stats["sample_size"]
                
                if stats["satisfaction_count"] > 0:
                    stats["avg_satisfaction"] = stats["total_satisfaction"] / stats["satisfaction_count"]
                else:
                    stats["avg_satisfaction"] = None
        
        return {
            "test_id": test_id,
            "name": test.name,
            "description": test.description,
            "is_active": test.is_active,
            "start_date": test.start_date.isoformat(),
            "end_date": test.end_date.isoformat() if test.end_date else None,
            "total_results": total_results,
            "variants": test.variants,
            "traffic_split": test.traffic_split,
            "variant_statistics": variant_stats
        }
    
    def is_test_significant(self, test_id: str) -> Dict[str, Any]:
        """
        檢查測試結果是否具有統計顯著性
        
        Args:
            test_id: 測試 ID
            
        Returns:
            顯著性分析結果
        """
        if test_id not in self.tests:
            return {"error": "測試不存在"}
        
        test = self.tests[test_id]
        results = self.results.get(test_id, [])
        
        if len(results) < 2:
            return {
                "is_significant": False,
                "reason": "樣本數量不足",
                "confidence_level": test.confidence_level
            }
        
        # 這裡可以實現更複雜的統計顯著性檢定
        # 目前簡化為檢查樣本大小
        total_sample_size = sum(result.sample_size for result in results)
        
        if total_sample_size < test.min_sample_size:
            return {
                "is_significant": False,
                "reason": f"樣本數量不足 (需要 {test.min_sample_size}, 實際 {total_sample_size})",
                "confidence_level": test.confidence_level
            }
        
        return {
            "is_significant": True,
            "reason": "樣本數量充足",
            "confidence_level": test.confidence_level,
            "total_sample_size": total_sample_size
        }
    
    def end_test(self, test_id: str) -> bool:
        """
        結束測試
        
        Args:
            test_id: 測試 ID
            
        Returns:
            是否成功結束
        """
        if test_id not in self.tests:
            logger.warning(f"⚠️ 測試 {test_id} 不存在")
            return False
        
        test = self.tests[test_id]
        test.is_active = False
        test.end_date = datetime.now()
        
        self._save_tests()
        
        logger.info(f"✅ 測試 {test_id} 已結束")
        return True
    
    def get_active_tests(self) -> List[Dict[str, Any]]:
        """
        獲取活躍的測試列表
        
        Returns:
            活躍測試列表
        """
        active_tests = []
        
        for test in self.tests.values():
            if test.is_active:
                now = datetime.now()
                if test.start_date <= now and (test.end_date is None or now <= test.end_date):
                    active_tests.append({
                        "test_id": test.test_id,
                        "name": test.name,
                        "description": test.description,
                        "start_date": test.start_date.isoformat(),
                        "end_date": test.end_date.isoformat() if test.end_date else None,
                        "variants_count": len(test.variants)
                    })
        
        return active_tests
    
    def cleanup_old_tests(self, days: int = 30) -> None:
        """
        清理舊的測試數據
        
        Args:
            days: 保留天數
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 清理過期的測試配置
        expired_tests = [
            test_id for test_id, test in self.tests.items()
            if test.end_date and test.end_date < cutoff_date
        ]
        
        for test_id in expired_tests:
            del self.tests[test_id]
            if test_id in self.results:
                del self.results[test_id]
        
        if expired_tests:
            self._save_tests()
            self._save_results()
            logger.info(f"🧹 清理了 {len(expired_tests)} 個過期測試")


def get_ab_testing_manager() -> ABTestingManager:
    """獲取 A/B 測試管理器實例"""
    return ABTestingManager() 