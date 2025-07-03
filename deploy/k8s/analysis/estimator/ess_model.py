import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import mlflow
import joblib
import hdbscan
import os


class ClusteringModel:
    """
    通用分群模型類別，支持多種分群算法並整合模型儲存與 MLflow 日誌記錄。

    Attributes:
        model_name (str): 分群模型名稱（kmeans, dbscan, hdbscan）。
        model_params (dict): 模型參數。
        output_path (str): 模型與結果儲存的基礎路徑。
        use_mlflow (bool): 是否記錄到 MLflow。
    """
    def __init__(self, model_name: str, model_params: dict = None, output_path: str = "./output", use_mlflow: bool = True):
        self.model_name = model_name.lower()
        self.model_params = model_params or {}
        self.output_path = output_path
        self.use_mlflow = use_mlflow
        self.model = self._initialize_model()

    def _initialize_model(self):
        """
        根據名稱初始化分群模型。

        Returns:
            model: 分群模型對象。
        """
        supported_models = {
            "kmeans": KMeans,
            "dbscan": DBSCAN,
            "hdbscan": hdbscan.HDBSCAN,
        }

        if self.model_name not in supported_models:
            raise ValueError(f"不支援的模型名稱: {self.model_name}")

        # 過濾無效參數
        valid_params = supported_models[self.model_name]().get_params()
        model_params = {k: v for k, v in self.model_params.items() if k in valid_params}

        return supported_models[self.model_name](**model_params)

    def fit(self, X: np.ndarray, Y=None):
        """
        訓練模型並記錄到 MLflow（如果啟用）。

        Parameters:
            X (np.ndarray): 標準化後的數據。
            y (np.ndarray, optional): 標籤數據，對某些模型可能無需提供。
        """
        if hasattr(self.model, 'fit'):
            self.model.fit(X)
        else:
            raise AttributeError(f"The model {self.model_name} does not have a 'fit' method.")

        # 保存模型並記錄到 MLflow
        self._save_and_log_model(X,Y)

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """
        訓練模型並進行分群。

        Parameters:
            X (np.ndarray): 標準化後的數據。

        Returns:
            np.ndarray: 分群結果。
        """
        if self.model is None:
            self.model = self._initialize_model()
        return self.model.fit_predict(X)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        使用已訓練模型進行分群預測。

        Parameters:
            X (np.ndarray): 標準化後的數據。

        Returns:
            np.ndarray: 分群結果。
        """
        if self.model is None:
            raise ValueError("模型尚未訓練或加載，請先執行 fit 或 load_model。")
        if hasattr(self.model, "predict"):
            return self.model.predict(X)
        elif hasattr(self.model, "fit_predict"):
            return self.model.fit_predict(X)
        else:
            raise NotImplementedError(f"{self.model_name} 模型不支持 predict 功能。")

    def _save_and_log_model(self, X: np.ndarray, Y: pd.Series = None):
            """
            保存模型並記錄到 MLflow。

            Parameters:
                X (np.ndarray): 用於分群的數據。
                y (pd.Series, optional): 真實標籤，用於驗證結果記錄。
            """
            model_file = os.path.join(self.output_path, f"{self.model_name}_model.joblib")
            os.makedirs(self.output_path, exist_ok=True)
            joblib.dump(self.model, model_file)

            if self.use_mlflow:
                with mlflow.start_run():
                    # 記錄參數
                    mlflow.log_param("Clustering Algorithm", self.model_name)
                    mlflow.log_params(self.model_params)

                    # 記錄分群結果
                    if hasattr(self.model, "labels_"):
                        clusters = self.model.labels_
                        num_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
                        mlflow.log_metric("Number of Clusters", num_clusters)

                    # 如果提供了真實標籤，計算並記錄平均正確率
                    if Y is not None:
                        cluster_to_label_mapping = {}
                        data = pd.DataFrame(X, columns=[f"Feature_{i}" for i in range(X.shape[1])])
                        data["Cluster"] = self.model.labels_
                        data["TrueLabel"] = Y.reset_index(drop=True)

                        # 建立分群標籤與真實標籤的對應
                        for cluster, group in data[data["Cluster"] != -1].groupby("Cluster"):
                            cluster_to_label_mapping[cluster] = group["TrueLabel"].mode()[0]

                        # 映射分群到真實標籤
                        data["MappedCluster"] = data["Cluster"].map(cluster_to_label_mapping).fillna("Noise")
                        data["Matched"] = (data["MappedCluster"] == data["TrueLabel"]).astype(int)

                        # 計算平均正確率
                        overall_accuracy = data["Matched"].mean()

                        # 記錄平均正確率
                        mlflow.log_metric("Overall Accuracy", overall_accuracy)

                        # 保存驗證結果
                        accuracy_file = os.path.join(self.output_path, f"{self.model_name}_accuracy.csv")
                        data[["Cluster", "MappedCluster", "TrueLabel", "Matched"]].to_csv(
                            accuracy_file, index=False, encoding="utf-8-sig"
                        )
                        mlflow.log_artifact(accuracy_file)

                    print(f"模型 {self.model_name} 已保存到 {model_file} 並記錄到 MLflow。")
                
    def save(self, path: str):
        """
        保存模型到指定路徑。

        Parameters:
            path (str): 模型保存路徑。
        """
        if self.model is None:
            raise ValueError("無法保存尚未訓練的模型。")
        joblib.dump(self.model, path)

    def load_model(self, path: str):
        """
        加載已保存的模型。

        Parameters:
            path (str): 模型檔案路徑。
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"模型檔案不存在: {path}")
        self.model = joblib.load(path)
