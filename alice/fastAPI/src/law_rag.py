import json
import re
import os
import traceback
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from collections import defaultdict

load_dotenv()

# ============================
# 1. VectorDB / LLM 세팅
# ============================

BASE_DIR = Path(__file__).resolve().parent
VECTORDB_DIR = BASE_DIR / "law_pipeline_data" / "vectordb"
LAW_COLLECTION_NAME = "law_articles"

emb = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENAI_API_KEY"),
)

db = Chroma(
    persist_directory=str(VECTORDB_DIR),
    collection_name=LAW_COLLECTION_NAME,
    embedding_function=emb,
)

retriever = db.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)

model = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0,
)


# ============================
# 2. 유틸 함수들
# ============================

def docs_to_text(docs, max_chars: int = 8000) -> str:
    """
    여러 문서를 하나의 문자열로 합치되,
    전체 길이가 max_chars를 넘지 않도록 잘라준다.
    (법령 컨텍스트용)
    """
    chunks = []
    total = 0

    for d in docs:
        if not d or not getattr(d, "page_content", None):
            continue

        content = d.page_content
        remain = max_chars - total
        if remain <= 0:
            break

        if len(content) > remain:
            content = content[:remain]

        chunks.append(content)
        total += len(content)

    if not chunks:
        return "관련 법령을 찾지 못했습니다."

    return "\n\n---\n\n".join(chunks)


def build_related_laws_from_docs(docs, max_items: int = 5, max_per_law: int = 2):
    """
    - 한 법령(law_name)에서 너무 많은 조문이 몰리지 않게 max_per_law로 제한.
    - 예: max_items=5, max_per_law=2 →
      정보통신망법 2개 + 개인정보보호법 2개 + SW진흥법 1개 이런 식으로 diversity 확보.
    """
    related = []
    seen_articles = set()
    count_by_law = defaultdict(int)

    for d in docs or []:
        meta = getattr(d, "metadata", {}) or {}
        law_name = meta.get("law_name")
        article_title = meta.get("title") or meta.get("article_title")

        if not law_name or not article_title:
            continue

        # 같은 법령에서 너무 많이 뽑히는 것 방지
        if count_by_law[law_name] >= max_per_law:
            continue

        key = (law_name, article_title)
        if key in seen_articles:
            continue

        seen_articles.add(key)
        count_by_law[law_name] += 1

        snippet = (getattr(d, "page_content", "") or "")[:200]

        related.append(
            {
                "law_name": law_name,
                "article_title": article_title,
                "snippet": snippet,
                "source": "rag",
            }
        )

        if len(related) >= max_items:
            break

    return related


# 🔹 focus에 따라 쿼리 강화 (예산/성과/참여제한 등 키워드 힌트)
def build_query(text: str, focus: str | None) -> str:
    if not focus:
        return text

    extra = ""
    f = focus or ""

    if "예산" in f or "연구개발비" in f:
        extra = "연구개발비, 예산, 직접비, 간접비, 자부담"
    elif "성과지표" in f or "평가" in f or "성과관리" in f:
        extra = "성과지표, 평가 기준, 성과평가, 성과관리 관련 법령"
    elif "수행체계" in f or "책임" in f or "참여제한" in f:
        extra = "참여제한, 제재, 책임, 제재 조항"
    elif "개인정보" in f or "보호" in f:
        extra = "개인정보 보호법, 개인정보 보호법 시행령"
    # 필요하면 여기 다른 focus 케이스도 추가 가능

    if extra:
        return f"{text}\n\n[검증 관점]: {focus}\n[관련 키워드]: {extra}"
    else:
        return f"{text}\n\n[검증 관점]: {focus}"


# ============================
# 3. 프롬프트
# ============================

VERIFY_PROMPT = """
당신은 정부 지원 사업(일반회계 비R&D 사업 및 R&D 사업을 포함)의 법령 및 지침 준수 검토 전문가입니다.

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
- related_laws 항목에 적는 법령명과 조문 제목은 반드시 [법령 검색 결과]에 실제로 등장한 것만 사용하세요.
  새로운 법령명이나 조문을 만들어내지 마세요.

각 필드의 의미:
- status: 전반적인 판정 (적합/보완/부적합)
- risk_level: 리스크 수준 (LOW/MEDIUM/HIGH)
- reason: 왜 이런 판정이 나왔는지에 대한 **요약 설명**
- missing: 기획서에서 **부족하거나 빠진 요소 목록**
- evidence: 기획서에서 **실제로 근거가 되는 문장** 또는 **문제되는 문장**
- suggestion: 어떻게 고치면 좋을지에 대한 **구체적인 보완 제안**
- violation_judgment:
  - "NO_ISSUE" : 현재 텍스트에서 법령 위반 리스크가 뚜렷하게 보이지 않는 경우
  - "POTENTIAL_VIOLATION" : 특정 법령·조항과 충돌할 가능성이 있는 경우
  - "POSSIBLE_ISSUE" : 바로 위반이라고 보긴 어렵지만, 해석 또는 추후 검토가 필요한 애매한 리스크가 있는 경우
  - "UNCLEAR" : 법령 검색 결과나 기획서 내용이 부족해서 판단이 어려운 경우
- violation_summary: 주요 위반/리스크 가능성을 한 줄로 요약
- violations: 위반 또는 리스크가 있다고 판단한 법령·조항별 상세 목록

evidence 작성 규칙 (중요):
- evidence 필드는 다음 두 가지 중 하나만 허용합니다.
  1) [검토 대상 텍스트]에서 그대로 발췌한 한두 문장
  2) 명확한 근거가 없을 때: 문자열 전체를 정확히 '근거 부족' 네 글자로만 작성
- '기획서에서 문제로 지적한 부분(또는 '근거 부족')' 같은 설명 문장은 evidence에 절대 쓰지 마세요.
- focus 문장(예: '연구개발비·예산 관점에서 이 초안을 검토하라.')을 evidence에 반복해서 쓰지 마세요.

reason, suggestion 문체 규칙:
- reason, suggestion 은 보고서용 공손한 문체로 작성하고, 문장 끝은 되도록
  "~인 것으로 보입니다.", "~인 것으로 판단됩니다." 와 같은 형태로 통일하세요.
- 반말 또는 명사형 어미("~함")로 끝나는 표현은 사용하지 마세요.

JSON 스키마:
{{
  "status": "적합" | "보완" | "부적합",
  "risk_level": "LOW" | "MEDIUM" | "HIGH",
  "reason": "전체 판단 근거 요약",
  "missing": ["부족한 요소1", "부족한 요소2"],
  "evidence": "기획서에서 문제로 지적한 실제 문장 또는 '근거 부족'",
  "suggestion": "어떻게 보완해야 하는지 구체적인 제안",
  "related_laws": [
    {{
      "law_name": "법령명",
      "article_title": "조문 제목",
      "snippet": "법령 내용 요약 또는 관련 부분 발췌"
    }}
  ],
  "violation_judgment": "NO_ISSUE" | "POTENTIAL_VIOLATION" | "POSSIBLE_ISSUE" | "UNCLEAR",
  "violation_summary": "법령 위반/리스크에 대한 한 줄 요약",
  "violations": [
    {{
      "law_name": "법령명",
      "article_no": "조문 번호 (예: 제32조)",
      "article_title": "조문 제목",
      "violation_type": "어떤 유형의 위반/리스크인지 간단한 이름",
      "severity": "LOW" | "MEDIUM" | "HIGH",
      "reason": "왜 이 법령에 위배될 가능성이 있는지",
      "recommendation": "어떻게 보완하면 좋을지"
    }}
  ]
}}
"""


# ============================
# 4. 메인 함수
# ============================

def verify_law_compliance(text: str, focus: str | None = None) -> dict:
    """
    초안의 일부(예산, 수행계획 등)를 넣으면
    법령 RAG 기반 '법령준수' JSON을 반환하는 함수.

    - text: 검증할 초안 섹션 텍스트
    - focus: 검사 관점 (예: '연구개발비', '기관요건')
    """
    try:
        # -----------------------------
        # 1) RAG로 관련 법령 검색
        # -----------------------------
        query = build_query(text, focus)

        print("query: ", query)

        try:
            docs = retriever.invoke(query)

            print("docs: ", docs)

            # 🔍 디버그: 어떤 법령들이 걸렸는지 확인
            print("🔎 [RAG 결과 요약]")
            for i, d in enumerate(docs or []):
                meta = getattr(d, "metadata", {}) or {}
                print(
                    f"  #{i+1}: law_name={meta.get('law_name')} | "
                    f"title={meta.get('title') or meta.get('article_title')}"
                )

        except Exception as e:
            print("❌ RAG 검색 중 오류:", e)
            traceback.print_exc()
            docs = []

        # 👉 RAG에서 바로 추출한 법령 목록 (fallback용, 전부 실제 문서 기반)
        source_laws = build_related_laws_from_docs(docs)

        print("source_laws: ", source_laws)

        context = docs_to_text(docs) if docs else "관련 법령을 찾지 못했습니다."

        # 🔹 텍스트 전체 사용 (길이 제한 제거)
        text_for_prompt = text

        # -----------------------------
        # 2) 프롬프트 구성
        # -----------------------------
        prompt_text = VERIFY_PROMPT.format(
            context=context,
            text=text_for_prompt,
            focus=focus or "법령 준수 전반",
        )

        # -----------------------------
        # 3) LLM 호출
        # -----------------------------
        try:
            resp = model.invoke(prompt_text)
        except Exception as e:
            print("❌ LLM 호출 중 오류:", e)
            traceback.print_exc()
            return {
                "status": "error",
                "risk_level": "UNKNOWN",
                "reason": "LLM 호출 실패",
                "raw": str(e),
                "related_laws": source_laws,  # 그래도 실제 검색된 조문은 함께 내려줌
            }

        raw = resp.content or ""

        # -----------------------------
        # 4) ```json ... ``` 코드블록 껍데기 제거
        # -----------------------------
        raw_clean = raw.strip()

        if raw_clean.startswith("```"):
            # 첫 줄의 ``` / ```json 제거
            raw_clean = re.sub(r"^```[a-zA-Z0-9]*\s*", "", raw_clean)
            # 끝부분 ``` 잘라내기
            if raw_clean.endswith("```"):
                raw_clean = raw_clean[: raw_clean.rfind("```")].strip()

        # -----------------------------
        # 5) JSON 파싱
        # -----------------------------
        try:
            parsed = json.loads(raw_clean)
        except Exception:
            print("❌ JSON 파싱 실패, raw 응답:", raw_clean[:500])
            traceback.print_exc()
            return {
                "status": "error",
                "risk_level": "UNKNOWN",
                "reason": "LLM JSON 파싱 실패",
                "raw": raw,
                "related_laws": source_laws,  # 여기서도 fallback
            }

        # -----------------------------
        # 6) related_laws 보정 (fallback)
        # -----------------------------
        rl = parsed.get("related_laws")
        if isinstance(rl, list) and len(rl) > 0:
            # LLM이 채워준 항목에 source 표시 (프론트에서 구분하고 싶을 때)
            for item in rl:
                if isinstance(item, dict) and "source" not in item:
                    item["source"] = "llm"
        else:
            # LLM이 related_laws를 안 채웠으면, RAG에서 가져온 실제 조문으로 세팅
            parsed["related_laws"] = source_laws

        # -----------------------------
        # 7) violation_* 필드 기본값 보정
        # -----------------------------
        vj = parsed.get("violation_judgment")
        if vj not in ("NO_ISSUE", "POTENTIAL_VIOLATION", "POSSIBLE_ISSUE", "UNCLEAR"):
            parsed["violation_judgment"] = "UNCLEAR"

        if not isinstance(parsed.get("violation_summary"), str):
            parsed["violation_summary"] = ""

        vlist = parsed.get("violations")
        if not isinstance(vlist, list):
            parsed["violations"] = []
        else:
            cleaned = []
            for v in vlist:
                if not isinstance(v, dict):
                    continue
                # severity 기본값 보정
                if v.get("severity") not in ("LOW", "MEDIUM", "HIGH"):
                    v["severity"] = "MEDIUM"
                cleaned.append(v)
            parsed["violations"] = cleaned

        return parsed

    except Exception as e:
        # 최상위 방어막: 어떤 이유로든 여기까지 오면 dict로 error 상태 리턴
        print("❌ verify_law_compliance 전체에서 예외 발생:", e)
        traceback.print_exc()
        return {
            "status": "error",
            "risk_level": "UNKNOWN",
            "reason": "verify_law_compliance 내부 예외 발생",
            "raw": str(e),
        }


# if __name__ == "__main__":
#     from pprint import pprint

#     text = "연구개발비에서 간접비와 직접비를 어떻게 구분해서 편성해야 하는지 설명하는 문단"
#     result = verify_law_compliance(text, focus="연구개발비")

#     pprint(result, width=120, compact=True)
