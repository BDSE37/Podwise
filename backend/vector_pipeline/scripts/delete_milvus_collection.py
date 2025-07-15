"""
刪除 Milvus 集合腳本
用於刪除現有的 podwise_chunks 集合，以便重新建立新的 schema
"""

import logging
from pymilvus import connections, utility

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Milvus 連線設定
MILVUS_CONFIG = {
    'host': '192.168.32.86',  # worker3 IP
    'port': '19530'
}

# 集合名稱
COLLECTION_NAME = 'podwise_chunks'


def delete_collection():
    """刪除 Milvus 集合"""
    try:
        # 連線到 Milvus
        logger.info(f"🔄 正在連線到 Milvus ({MILVUS_CONFIG['host']}:{MILVUS_CONFIG['port']})...")
        connections.connect(
            alias="default",
            host=MILVUS_CONFIG['host'],
            port=MILVUS_CONFIG['port']
        )
        logger.info("✅ 成功連線到 Milvus")
        
        # 檢查集合是否存在
        if utility.has_collection(COLLECTION_NAME):
            logger.info(f"🔄 正在刪除集合 {COLLECTION_NAME}...")
            utility.drop_collection(COLLECTION_NAME)
            logger.info(f"✅ 成功刪除集合 {COLLECTION_NAME}")
        else:
            logger.info(f"ℹ️ 集合 {COLLECTION_NAME} 不存在，無需刪除")
            
    except Exception as e:
        logger.error(f"❌ 刪除集合失敗: {e}")
        raise


def main():
    """主函數"""
    try:
        delete_collection()
        logger.info("🎉 集合刪除完成，可以重新執行 embedding 腳本建立新集合")
    except Exception as e:
        logger.error(f"❌ 執行失敗: {e}")
        raise


if __name__ == "__main__":
    main() 