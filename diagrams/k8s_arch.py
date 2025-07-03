# diagrams/k8s_arch.py

from diagrams import Cluster, Diagram
from diagrams.k8s.compute import Pod
from diagrams.k8s.group import Namespace
from diagrams.k8s.network import Ingress
from diagrams.onprem.database import PostgreSQL, Mongodb
from diagrams.onprem.mlops import MLflow
from diagrams.onprem.monitoring import Grafana, Prometheus
from diagrams.custom import Custom

with Diagram("Podwise 系統節點部署架構", show=False, outformat="png", filename="output/podwise_k8s_arch"):

    ingress = Ingress("Ingress / Frontend Access")

    with Cluster("Kubernetes Namespace: podwise"):

        with Cluster("worker1: STT + TTS"):
            stt = Pod("STT")
            tts = Pod("TTS")

        with Cluster("worker2: LLM + RAG + MinIO"):
            llm = Pod("LLM")
            rag2 = Pod("RAG Pipeline (副本)")
            minio = Custom("MinIO", "./icons/minio.png")

        with Cluster("worker3: ML + MongoDB + Milvus + AnythingLLM"):
            anythingllm = Custom("AnythingLLM", "./icons/anythingllm.png")
            mongo = Mongodb("MongoDB")
            ml = MLflow("ML Pipeline")
            milvus = Custom("Milvus", "./icons/milvus.png")

        with Cluster("worker4: PostgreSQL + n8n + pgAdmin + Podri"):
            postgres = PostgreSQL("PostgreSQL")
            pgadmin = Custom("pgAdmin", "./icons/pgadmin.png")
            n8n = Pod("n8n")
            podri_chat = Pod("Podri Chat")

        with Cluster("worker5: Frontend + Ollama + Grafana + RAG"):
            frontend = Pod("Frontend")
            grafana = Grafana("Grafana")
            ollama = Pod("Ollama")
            rag = Pod("RAG Pipeline")

    # Service Links
    ingress >> frontend >> [podri_chat, rag]
    podri_chat >> [tts, stt, llm]
    rag >> [milvus, postgres, mongo]
    ml >> [milvus, postgres, mongo]
    anythingllm >> llm
    stt >> mongo
    tts >> minio
    grafana >> Prometheus("Prometheus")
    pgadmin >> postgres
