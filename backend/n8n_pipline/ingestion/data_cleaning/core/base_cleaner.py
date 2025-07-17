from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseCleaner(ABC):
    """所有清理器的基底類別，定義共用介面。"""

    @abstractmethod
    def clean(self, data: Any) -> Any:
        """清理單筆資料，子類別需實作。"""
        pass

    def batch_clean(self, data_list: List[Any]) -> List[Any]:
        """批次清理資料。"""
        return [self.clean(item) for item in data_list] 