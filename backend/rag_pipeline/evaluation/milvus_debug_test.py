from pymilvus import connections, Collection
from regar_complete import RAGEvaluator

if __name__ == "__main__":
    # 先建立連線
    connections.connect(host="192.168.32.86", port="19530", alias="default")
    col = Collection("podcast_chunks")
    print("=== Collection Schema ===")
    print(col.schema)
    print("欄位名稱：", [f.name for f in col.schema.fields])

    print("\n=== 前 5 筆 chunk_text ===")
    col.load()
    results = col.query(expr="", output_fields=["chunk_text", "category"], limit=5)
    for i, r in enumerate(results):
        print(f"{i+1}: chunk_text={r.get('chunk_text')}, category={r.get('category')}")

    print("\n=== 向量查詢測試 ===")
    evaluator = RAGEvaluator()
    evaluator.setup_components()
    test_question = "我很想改善自己職場溝通能力，有什麼節目可以聽聽看？"
    vec = evaluator.get_embeddings(test_question)
    search_results = col.search(
        data=[vec],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"nprobe": 10}},
        limit=5,
        output_fields=["chunk_text", "category"]
    )
    for i, hits in enumerate(search_results):
        print(f"Query {i+1}:")
        for hit in hits:
            entity = hit.entity
            print(f"  chunk_text={entity.get('chunk_text')}, category={entity.get('category')}, score={hit.score}") 