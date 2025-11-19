# law_rag.py
from pathlib import Path
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

import os
from dotenv import load_dotenv
load_dotenv()

# VectorDB 로딩 → rag_chain export

# === 경로 설정 ===
BASE_DIR = Path(__file__).resolve().parent
VECTORDB_DIR = BASE_DIR / "law_pipeline_data" / "vectordb"
LAW_COLLECTION_NAME = "law_articles"

# === 1) 임베딩 로더(OpenAI) ===
emb = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY")
)

# === 2) VectorDB 로드 ===
db = Chroma(
    persist_directory=str(VECTORDB_DIR),
    collection_name=LAW_COLLECTION_NAME,
    embedding_function=emb
)

# === 3) Retriever ===
retriever = db.as_retriever(search_kwargs={"k": 3})

# === 4) LLM ===
model = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# === 5) Prompt ===
prompt = PromptTemplate.from_template("""
법령 검색 결과:

{context}

사용자 질문: {question}

규칙:
- context 안에서만 답변할 것
- 추측, 생성 금지
- 존재하지 않으면 '관련 법령 없음'이라고 말할 것
""")

def docs_to_text(docs):
    return "\n\n---\n\n".join([d.page_content for d in docs])

# === 6) RAG 체인 ===
rag_chain = (
    {
        "context": retriever | docs_to_text,
        "question": RunnablePassthrough()
    }
    | prompt
    | model
)
# ============================
# 🔍 테스트 실행
# ============================
# if __name__ == "__main__":
#     print("🔍 법령 RAG 테스트 시작")

#     query = "연구개발비의 직접비와 간접비 차이를 알려줘"
#     print("📌 질문:", query)

#     try:
#         result = rag_chain.invoke(query)
#         print("\n=== RAG 응답 ===")
#         print(result.content)
#     except Exception as e:
#         print("❌ 오류 발생:", e)