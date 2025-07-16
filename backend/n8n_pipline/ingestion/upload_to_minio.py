import os
import time
import re
from typing import List

from minio import Minio
from minio.error import S3Error

# —— 配置区 —— 
MINIO_ENDPOINT = "192.168.32.66:30090"
ACCESS_KEY     = "bdse37"
SECRET_KEY     = "11111111"
BUCKET_NAME    = "n8n-file"

# 把原来的 AUDIO_DIR Windows 路径改成 result 目录的挂载点
TARGET_DIR = "/data"
BATCH_SIZE = 10
SLEEP_TIME = 0.1
# ——————————

client = Minio(
    MINIO_ENDPOINT,
    access_key=ACCESS_KEY,
    secret_key=SECRET_KEY,
    secure=False
)

if not client.bucket_exists(BUCKET_NAME):
    client.make_bucket(BUCKET_NAME)


def get_all_files_within_folder(folder: str) -> List[str]:
    """
    遍历 folder 下所有文件，返回相对于 folder 的相对路径列表。
    """
    result = []
    for root, _, files in os.walk(folder):
        for fn in files:
            full_path = os.path.join(root, fn)
            relative = os.path.relpath(full_path, folder)
            result.append(relative)
    return result


def upload_file(relative_path: str):
    """
    上传单文件：根据文件名前缀决定存放到 bucket 的哪个“目录”。
    """
    local_path = os.path.join(TARGET_DIR, relative_path)

    # 如果文件名以 RSS_ 开头，就用它作为对象名前缀
    base = os.path.basename(relative_path)
    m = re.match(r"(RSS_\d+)", base)
    if m:
        obj_name = f"{m.group(1)}/{base}"
    else:
        obj_name = base

    try:
        client.fput_object(
            BUCKET_NAME,
            obj_name,
            local_path,
            content_type="application/octet-stream"
        )
        print(f"✅ 成功上傳: {obj_name}")
    except S3Error as e:
        print(f"❌ 上傳失敗 {obj_name}: {e}")


def upload_in_batches(file_list: List[str], batch_size: int):
    total = len(file_list)
    for i in range(0, total, batch_size):
        batch = file_list[i : i + batch_size]
        print(f"\n🚀 上傳批次 {i//batch_size+1}，共 {len(batch)} 檔案")
        for rel in batch:
            upload_file(rel)
            time.sleep(SLEEP_TIME)
        print("⏸️ 批次完成，短暫休息")


if __name__ == "__main__":
    files = get_all_files_within_folder(TARGET_DIR)
    if not files:
        print("⚠️ 在 /data 目录未找到任何文件")
    else:
        upload_in_batches(files, BATCH_SIZE)
