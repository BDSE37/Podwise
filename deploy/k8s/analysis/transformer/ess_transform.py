from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd

class ColumnSelector(BaseEstimator, TransformerMixin):
    """
    动态列选择器，根据固定列和动态前缀选择特定列。
    """
    def __init__(self, selected_cols=None, dynamic_prefixes=None):
        """
        初始化列选择器。

        Parameters:
            selected_cols (list): 固定选择的列名列表。
            dynamic_prefixes (list): 动态列前缀列表。
        """
        self.selected_cols = selected_cols or []
        self.dynamic_prefixes = dynamic_prefixes or []
        self.final_selected_cols_=[]

    def fit(self, X, y=None):
        """
        根据输入数据动态选择列。

        Parameters:
            X (pd.DataFrame): 输入数据。

        Returns:
            self: 返回自身。
        """
        # 获取动态列
        self.dynamic_columns_ = [
            col for col in X.columns
            for prefix in self.dynamic_prefixes
            if col.startswith(prefix)
        ]

        # 合并固定列和动态列，同时保持顺序并去重
        self.final_selected_cols_ = list(pd.unique(self.selected_cols + self.dynamic_columns_))
        return self

    def transform(self, X):
        """
        过滤输入数据，只保留选择的列。

        Parameters:
            X (pd.DataFrame): 输入数据。

        Returns:
            pd.DataFrame: 只包含选择列的 DataFrame。
        """
        return X[self.final_selected_cols_]
    

    def get_selected_columns(self):
        """
        获取选择的列。

        Returns:
            list: 选择的列名列表。
        """
        return self.final_selected_cols_