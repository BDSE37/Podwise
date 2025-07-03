import os
import logging
import pandas as pd
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
from io import StringIO
from analysis import load_config

# Load environment variables from .env file
load_dotenv()

# Initialize logger for the current module
logger = logging.getLogger(__name__)


class MinioConnection:
    """
    A class representing a connection to a MinIO server.

    Attributes:
        client (Minio): The MinIO client used for interacting with the server.

    Methods:
        __init__: Initialize the MinioConnection object by setting up the MinIO client with the provided credentials.
        get_csv: Retrieve a CSV file from the specified bucket on the MinIO server and return its contents as a Pandas DataFrame.
        get_images_and_labels: Load all images within the specific bucket in pairs of numpy arrays alongside their corresponding image labels.
    """

    def __init__(self) -> None:
        """
        Initialize a MinioConnection object.

        Sets up the MinIO client with the provided configuration in config.yaml.
        """
        # 加載配置文件
        config = load_config()
        minio_config = config.get("minio", {})

        # 獲取配置中的 MinIO 參數
        endpoint_url = minio_config.get("endpoint_url")
        access_key = minio_config.get("access_key")
        secret_key = minio_config.get("secret_key")

        # 驗證參數
        if not endpoint_url or not access_key or not secret_key:
            raise ValueError("MinIO configuration is incomplete. Please check config.yaml.")

        # 初始化 MinIO 客戶端
        self.client = Minio(
            endpoint_url.replace("http://", ""),
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
    
    def get_csv(self, bucket_name: str, object_name: str) -> pd.DataFrame:
        """
        Retrieve a CSV file from the specified bucket on the MinIO server.

        Args:
            bucket_name: The name of the bucket containing the CSV file.
            object_name: The name of the CSV file object.

        Returns:
            A Pandas DataFrame containing the contents of the CSV file.
        """
        try:
            # Get the object from the MinIO server
            csv_file = self.client.get_object(bucket_name, object_name)

            # Read the CSV data
            csv_data = csv_file.read().decode('utf-8')

            # Convert CSV data to Pandas DataFrame
            df = pd.read_csv(StringIO(csv_data))
            # logger.info(f"The CSV file was retrieved and loaded as dataframe:\n {df}")
            return df

        except S3Error as err:
            logger.error(f"Error while retrieving CSV from MinIO: {err}")
