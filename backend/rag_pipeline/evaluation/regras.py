import os
import pandas as pd
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel
import math
import asyncio

# -- 1. 環境設定與初始化 (Setup & Initialization) --

# 取得此腳本檔案 (regras.py) 所在的目錄並載入 .env
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
dotenv_path = os.path.join(backend_root, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(f"成功從 {dotenv_path} 載入 .env 檔案。")
else:
    print(f"警告：在 {dotenv_path} 找不到 .env 檔案。")

# 從環境變數讀取設定
braintrust_api_key = os.getenv("BRAINTRUST_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")
milvus_host = os.getenv("MILVUS_HOST")
milvus_port = os.getenv("MILVUS_PORT")

# 抑制 Huggingface tokenizers 並行化警告
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# 初始化 Braintrust Logger 和 OpenAI Client
from braintrust import init_logger, traced, wrap_openai, EvalAsync
from openai import OpenAI

logger = init_logger(project="Podwise-QA-Evaluation", api_key=braintrust_api_key)
client = wrap_openai(OpenAI(api_key=openai_api_key))

# 初始化 Milvus Client 和 Sentence Transformer 模型
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer

try:
    print(f"正在連線至 Milvus ({milvus_host}:{milvus_port})...")
    connections.connect("default", host=milvus_host, port=milvus_port)
    print("Milvus 連線成功。")
except Exception as e:
    print(f"錯誤：無法連線至 Milvus。請檢查主機、埠號以及網路連線: {e}")
    exit()

collection_name = "podcast_chunks"
try:
    collection = Collection(name=collection_name)
    collection.load()
    print(f"成功載入 Milvus collection: '{collection_name}'")
except Exception as e:
    print(f"錯誤：無法載入 Milvus collection '{collection_name}'。請確認 collection 是否存在: {e}")
    exit()

embedding_model = SentenceTransformer("BAAI/bge-m3")
print("環境設定完成。")


# -- 2. 載入人工建置的評估資料集 --
eval_dataset = []
try:
    csv_filename = "test1.csv"
    csv_path = os.path.join(script_dir, csv_filename)
    print(f"正在從 {csv_path} 讀取評估資料...")
    df = pd.read_csv(csv_path)
    print(f"成功讀取 {csv_filename} 檔案。")

    required_cols = ["question", "answer"]
    if not all(col in df.columns for col in required_cols):
        raise KeyError(f"CSV 檔案中缺少必要的欄位。請確認至少包含 {required_cols}。")

    print("資料預覽:")
    print(df.head())
    
    for index, row in df.iterrows():
        if pd.isna(row["question"]) or pd.isna(row["answer"]):
            continue
        eval_dataset.append(
            {
                "input": row["question"],
                "expected": row["answer"],
                "metadata": {
                    "row_index": index,
                    "asker": row.get("user"),
                    "category": row.get("category"),
                    "mapped_tag": row.get("tags"),
                },
            }
        )
    print(f"\n成功從 CSV 建立 {len(eval_dataset)} 筆評估資料。")
except FileNotFoundError:
    print(f"錯誤：找不到 '{csv_path}' 檔案。請確認檔案路徑是否正確。")
except KeyError as e:
    print(f"錯誤： {e}")


# -- 3. 定義 RAG 任務函式 --
class QueryResult(BaseModel):
    relevant_quotes: List[str]
    answer: str
    following_questions: List[str]

def get_embeddings(text: str) -> List[float]:
    embedding = embedding_model.encode(text)
    return embedding.tolist()

def fetch_top_k_relevant_sections(question: str, top_k: int = 10) -> List[str]:
    query_embedding = get_embeddings(question)
    search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        output_fields=["chunk_text"]
    )
    documents = []
    if results and len(results) > 0:
        for hit in results[0]:
            doc_text = hit.entity.chunk_text
            if doc_text:
                documents.append(doc_text)
    return documents

def generate_answer_from_docs(question: str, retrieved_content: List[str]) -> QueryResult:
    context = "\n".join("* " + doc for doc in retrieved_content if doc)
    user_prompt = f"""
    我將提供您一份文件，然後針對它提出一個問題。請依照以下步驟回應：
    <document>
    {context if context else "沒有提供相關文件。"}
    </document>
    Question: {question}
    請使用以下格式回答：
    1. 首先，從文件中找出最有助於回答問題的相關引文並列出。每段引文都應該相對簡短。
       如果沒有相關引文，請寫「無相關引文」。
    2. 接著，使用這些引文中的事實來回答問題，回答時不要直接引用文件內容。
    3. 最後，根據原始問題和文件內容，提供3個相關的後續問題，以幫助進一步探討該主題。
    如果文件未包含足夠的資訊來回答問題，請在答案欄位中說明，但仍然提供任何相關的引文（如果有的話）和可能的後續問題。
    請以台灣繁體中文回應。
    """
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": user_prompt}],
            response_format=QueryResult,
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! OpenAI API Call FAILED !!!!!!!!!!!!!!!")
        print(f"Error details: {e}")
        print(f"Question that caused the error: {question}")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return QueryResult(
            relevant_quotes=["API 呼叫失敗"], 
            answer="抱歉，由於發生錯誤，無法生成答案。", 
            following_questions=[]
        )

@traced
async def generate_answer_e2e(question: str) -> dict:
    """
    這是主要的RAG任務函式，Braintrust會呼叫它來處理每一筆資料。
    """
    try:
        retrieved_content = fetch_top_k_relevant_sections(question)
        result = generate_answer_from_docs(question, retrieved_content)
        # 回傳一個包含標準 key 名稱的字典，以供評分函式使用
        return {
            "output": result.answer,
            "context": retrieved_content
        }
    except Exception as e:
        print(f"!!!!!!!!!!!!!!! TASK FAILED !!!!!!!!!!!!!!!")
        print(f"Error details: {e}")
        print(f"Question that caused the error: {question}")
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return {
            "output": f"任務執行失敗: {e}",
            "context": []
        }

# -- 4. 定義 RAGAS 評估指標 (手動對應最終健壯版) --
from autoevals import AnswerCorrectness, ContextRecall, ContextPrecision, Faithfulness
from braintrust_core.score import Score # 為了能回傳自定義的錯誤分數，需要導入 Score

async def context_recall(output: dict, expected: str, **kwargs):
    # 此函式已是正確的
    return await ContextRecall(model="gpt-4.1").eval_async(
        input=kwargs["input"],
        output=output["output"],
        expected=expected,
        context=output["context"]
    )

async def context_precision(output: dict, expected: str, **kwargs):
    # 此函式已是正確的
    return await ContextPrecision(model="gpt-4.1").eval_async(
        input=kwargs["input"],
        output=output["output"],
        expected=expected,
        context=output["context"]
    )

async def faithfulness(output: dict, **kwargs):
    # ✨【最終修正】✨：為 Faithfulness 增加錯誤處理安全外殼
    try:
        # 嘗試正常執行評分
        score_result = await Faithfulness(model="gpt-4.1").eval_async(
            input=kwargs["input"],
            output=output["output"],
            context=output["context"]
        )
        return score_result
    except TypeError as e:
        # 如果捕捉到特定的 TypeError，就處理它而不是讓程式崩潰
        if "string indices must be integers" in str(e):
            print("\n" + "="*20)
            print("⚠️  Faithfulness Scorer Warning ⚠️")
            print("捕捉到內部 TypeError，可能是評分模型未回傳 JSON。")
            print("此筆資料的 Faithfulness 分數將被記為 0.0，評估將繼續。")
            print(f"正在評分的回答: {output.get('output', '')[:100]}...")
            print("="*20 + "\n")
            # 回傳一個預設的失敗分數物件
            return Score(name="Faithfulness", score=0.0, metadata={"error": "Internal TypeError"})
        else:
            # 如果是其他類型的 TypeError，則重新拋出
            raise e
    except Exception as e:
        # 捕捉其他所有可能的錯誤
        print(f"\nFaithfulness scorer 發生未知錯誤: {e}\n")
        return Score(name="Faithfulness", score=0.0, metadata={"error": str(e)})


async def answer_correctness(output: dict, expected: str, **kwargs):
    # 此函式已是正確的
    return await AnswerCorrectness(model="gpt-4.1").eval_async(
        input=kwargs["input"],
        output=output["output"],
        expected=expected
    )
# -- 5. 執行評估 (Run Evaluation) --
async def run_evaluation():
    if not eval_dataset:
        print("評估資料集為空，無法執行評估。請檢查 CSV 檔案及其欄位名稱。")
        return

    print("\n即將開始 RAGAS 評估...")
    
    eval_result = await EvalAsync(
        name="Podwise-QA-Evaluation",
        experiment_name="RAGAS_with_Human_Data_v9_final",  # 更新實驗版本名稱
        data=eval_dataset,
        task=generate_answer_e2e,
        scores=[
            context_recall,
            context_precision,
            faithfulness, # ✨【最終修正】✨：重新啟用 faithfulness
            answer_correctness
        ],
        metadata=dict(model="gpt-4.1-mini", embedding_model="bge-m3", top_k=10),
    )
    
    print("\n評估完成！")
    
    if hasattr(eval_result, 'url'):
        print(f"您可以在 Braintrust 儀表板上查看結果: {eval_result.url}")
    
    return eval_result

# -- 主程式執行點 --
if __name__ == "__main__":
    asyncio.run(run_evaluation())