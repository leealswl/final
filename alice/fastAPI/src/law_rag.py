import json
import re

from pathlib import Path
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma

import os
from dotenv import load_dotenv
load_dotenv()

# VectorDB 로딩

# === 경로 설정 ===
BASE_DIR = Path(__file__).resolve().parent
VECTORDB_DIR = BASE_DIR / "law_pipeline_data" / "vectordb"
LAW_COLLECTION_NAME = "law_articles"

# === 임베딩 로더(OpenAI) ===
emb = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY")
)

# === VectorDB 로드 ===
db = Chroma(
    persist_directory=str(VECTORDB_DIR),
    collection_name=LAW_COLLECTION_NAME,
    embedding_function=emb
)

# === Retriever ===
retriever = db.as_retriever(search_kwargs={"k": 3})

# === LLM ===
model = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

def docs_to_text(docs):
    return "\n\n---\n\n".join([d.page_content for d in docs])


VERIFY_PROMPT = """
    당신은 국가연구개발사업(R&D) 법령 및 지침 준수 검토 전문가입니다.

    [법령 검색 결과]
    {context}

    [검토 대상 텍스트]
    {text}

    [검증 관점]
    {focus}

    요구사항:
    - 반드시 아래 JSON 형식으로만 한국어로 출력하세요.
    - JSON 밖에 다른 텍스트는 절대 쓰지 마세요.
    - 법령 검색 결과에 근거하지 않는 추측은 하지 말고, 근거가 없으면 '근거 부족'이라고 쓰세요.

    JSON 스키마:
    {{
    "status": "적합" | "보완" | "부적합",
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "reason": "전체 판단 근거 요약",
    "missing": ["부족한 요소1", "부족한 요소2"],
    "evidence": "기획서에서 문제로 지적한 부분(또는 '근거 부족')",
    "suggestion": "어떻게 보완해야 하는지 구체적인 제안",
    "related_laws": [
        {{
        "law_name": "법령명",
        "article_title": "조문 제목",
        "snippet": "법령 내용 요약 또는 관련 부분 발췌"
        }}
    ]
    }}
    """


def verify_law_compliance(text: str, focus: str | None = None) -> dict:
    """
    초안의 일부(예산, 수행계획 등)를 넣으면
    법령 RAG 기반 '법령준수' JSON을 반환하는 함수.

    - text: 검증할 초안 섹션 텍스트
    - focus: 검사 관점 (예: '연구개발비', '기관요건')
    """
    # 1) RAG로 관련 법령 검색
    query = f"{text}\n(검증 관점: {focus})" if focus else text
    # ⚠️ 경고 제거용: get_relevant_documents 대신 invoke 사용
    docs = retriever.invoke(query)
    context = docs_to_text(docs) if docs else "관련 법령을 찾지 못했습니다."

    # 2) 프롬프트 구성
    prompt_text = VERIFY_PROMPT.format(
        context=context,
        text=text,
        focus=focus or "법령 준수 전반"
    )

    # 3) LLM 호출
    resp = model.invoke(prompt_text)
    raw = resp.content or ""

    # 4) ```json ... ``` 코드블록 껍데기 제거
    raw_clean = raw.strip()

    if raw_clean.startswith("```"):
        # 첫 줄의 ``` / ```json 제거
        # ^```json\s*  또는 ^```\s* 같은 패턴 처리
        raw_clean = re.sub(r"^```[a-zA-Z0-9]*\s*", "", raw_clean)
        # 끝부분 ``` 잘라내기
        if raw_clean.endswith("```"):
            raw_clean = raw_clean[: raw_clean.rfind("```")].strip()

    # 5) JSON 파싱
    try:
        parsed = json.loads(raw_clean)
        return parsed
    except Exception:
        # JSON 형식이 깨지면 raw를 같이 보내서 디버깅 가능하도록 함
        return {
            "status": "error",
            "risk_level": "UNKNOWN",
            "reason": "LLM JSON 파싱 실패",
            "raw": raw
        }
    
if __name__ == "__main__":
    from pprint import pprint

    text = "연구개발비에서 간접비와 직접비를 어떻게 구분해서 편성해야 하는지 설명하는 문단"
    result = verify_law_compliance(text, focus="연구개발비")

    pprint(result, width=120, compact=True)