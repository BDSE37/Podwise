import logging
from sklearn.pipeline import Pipeline
from analysis.loader import MinioConnection
from sklearn.compose import ColumnTransformer
from analysis.transformer import ColumnSelector
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from analysis.estimator import ClusteringModel
from analysis import load_config
import os
import pandas as pd
import yaml
import mlflow
import joblib

logger = logging.getLogger(__name__)

class ClusteringPipeline:
    """A pipeline for clustering analysis.

    Attributes:
        config (dict): Configuration settings for the pipeline.
        pipeline (Pipeline): The constructed scikit-learn pipeline for data preprocessing and clustering.
    """
    def __init__(self) -> None:
        """Initialize ClusteringPipeline."""
        self.config = load_config()
        self.pipeline = self._build_pipeline()

    def _build_pipeline(self) -> Pipeline:
        """Build the preprocessing and clustering pipeline.

        Returns:
            Pipeline: The constructed pipeline.
        """
        transformer_config = self.config["transformer"]
        model_config = self.config["model"]

        # 設定 MLflow
        mlflow_config = config.get("mlflow", {})
        mlflow.set_tracking_uri(mlflow_config.get("tracking_uri"))
        mlflow.set_experiment(mlflow_config.get("experiment_name"))
        
        # 動態選擇特徵
        column_selector = ColumnSelector(
            selected_cols=config["transformer"]["selected_cols"],
            dynamic_prefixes=config["transformer"].get("dynamic_column_prefixes", [])
        )

        # Preprocessing pipeline
        numeric_transformer = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy=transformer_config["numeric"]["imputer"])),
                ("scaler", StandardScaler())
            ]
        )

        # ColumnTransformer: 處理指定列並對其餘列設置 `remainder`
        column_transformer = ColumnTransformer(
            transformers=[
                ("numeric", numeric_transformer, column_selector.get_selected_columns())
            ],
            remainder=StandardScaler()  # 對未指定的列應用標準化處理
        )

        # Complete pipeline
        return Pipeline(
            steps=[
                ("column selector", column_selector),
                ("column preprocess", column_transformer),
                ("clustering", ClusteringModel(
                    model_name=model_config["name"],
                    model_params=model_config["params"],
                    output_path=self.config["output"]["path"],
                    use_mlflow=True
                ))
            ]
        )

    def get_pipeline(self) -> Pipeline:
        """Retrieve the pipeline.

        Returns:
            Pipeline: The constructed pipeline.
        """
        return self.pipeline

if __name__ == "__main__":

    config = load_config()
    
    # Load data from MinIO
    minio_conn = MinioConnection()
    bucket_name = config["data"]["bucket_name"]
    object_name = config["data"]["object_name"]

    try:
        df = minio_conn.get_csv(bucket_name=bucket_name, object_name=object_name)
    except Exception as e:
        logger.error(f"Failed to retrieve data from MinIO: {e}")
        exit(1)

    X = df

    # Initialize the pipeline
    pipeline = ClusteringPipeline().get_pipeline()

    target_column = config["data"].get("target_column", None)
    # Fit the pipeline and perform clustering    
    Y = df[target_column] if target_column in df.columns else None
    pipeline.fit(X,Y)

    mlflow.sklearn.log_model(pipeline, artifact_path="pipeline_model",registered_model_name=config["model"]["name"] )

    # Predict clusters
    clusters = pipeline.predict(X)