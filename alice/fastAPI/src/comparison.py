# comparison.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from openai import OpenAI
import json
import re
import requests

router = APIRouter()
client = OpenAI()


class DraftCompareRequest(BaseModel):
    project_idx: int
    draft_json: dict


# -------------------------------
# JSON / TEXT UTILITIES
# -------------------------------
def extract_json_from_response(text: str) -> str:
    codeblock = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return codeblock.group(1).strip() if codeblock else text.strip()


def extract_text_from_tiptap(doc_json):
    texts = []
    for block in doc_json.get("content", []):
        if "content" in block:
            for item in block["content"]:
                if "text" in item:
                    texts.append(item["text"].strip())
    return "\n".join(texts)


def extract_section_headings(doc_json):
    headings = []
    for block in doc_json.get("content", []):
        if block.get("type") == "heading":
            text_items = [
                c.get("text") for c in block.get("content", [])
                if "text" in c
            ]
            if text_items:
                headings.append(" ".join(text_items))
    return headings


# -------------------------------
# GPT: 섹션 매핑
# -------------------------------
def map_sections_ai(draft_sections: List[str], toc_sections: List[str]) -> List[dict]:
    prompt = {
        "role": "user",
        "content": f"""
아래는 공고문의 목차입니다:
{toc_sections}

아래는 초안의 섹션 제목입니다:
{draft_sections}

초안 섹션이 공고문 목차의 어떤 항목과 의미적으로 매칭되는지 분석해주세요.

JSON ONLY:
[
  {{
    "draft_title": "...",
    "matched": "... 또는 null",
    "score": 0.0
  }}
]
"""
    }

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[prompt],
        temperature=0
    )
    clean = extract_json_from_response(res.choices[0].message.content)

    try:
        return json.loads(clean)
    except:
        print("❌ 매핑 JSON 파싱 실패:", clean)
        return []


# -------------------------------
# GPT: Feature 포함 여부 체크
# -------------------------------
def match_features_ai(draft_text: str, features: List[Dict[str, Any]]) -> List[dict]:
    titles = [f.get("title") for f in features]

    prompt = {
        "role": "user",
        "content": f"""
초안 내용:
{draft_text}

공고문 Feature:
{titles}

각 feature가 초안에 포함되어 있는지 검사하세요.

JSON ONLY:
[
  {{
    "feature": "...",
    "included": true/false,
    "reason": "..."
  }}
]
"""
    }

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[prompt],
        temperature=0
    )

    clean = extract_json_from_response(res.choices[0].message.content)

    try:
        return json.loads(clean)
    except:
        print("❌ Feature JSON 파싱 실패:", clean)
        return []


# -------------------------------
# GPT: 실무형 보완 가이드 생성
# -------------------------------
def generate_suggestion(feature_or_section: str) -> str:
    """
    해당 항목이 어떤 내용을 포함해야 하는지
    2~4줄의 실무형 기획서 보완 가이드를 생성.
    """
    prompt = {
        "role": "user",
        "content": f"""
다음 항목을 기획서에 보완해야 합니다:
항목: {feature_or_section}

이 항목은 정부지원사업 기획서에서 일반적으로 어떤 내용을 포함해야 하는지
실무자가 참고할 수 있도록 2~4줄로 핵심 가이드라인만 정리해 주세요.

'-' 리스트 없이 문장형으로만 작성하고,
'~을 포함해야 합니다.' 형식으로 작성하세요.
"""
    }

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[prompt],
        temperature=0.2
    )

    return res.choices[0].message.content.strip()


# -------------------------------
# Main Compare API
# -------------------------------
@router.post("/draft")
def compare_draft_ai(request: DraftCompareRequest):
    # 초안 텍스트 추출
    draft_text = extract_text_from_tiptap(request.draft_json)
    draft_sections = extract_section_headings(request.draft_json)

    # Spring 공고문 분석 데이터 가져오기
    spring_url = f"http://localhost:8081/api/analysis/get-context?projectIdx={request.project_idx}"
    spring_res = requests.get(spring_url).json()

    if spring_res.get("data") is None:
        return {"status": "error", "message": "공고문 분석 데이터 없음"}

    toc = spring_res["data"]["result_toc"]
    features = spring_res["data"]["extracted_features"]

    toc_titles = [sec["title"] for sec in toc["sections"]]

    # 1) 섹션 매핑
    section_mapping = map_sections_ai(draft_sections, toc_titles)
    matched_titles = [
        m["matched"]
        for m in section_mapping
        if m.get("matched") and m["matched"] not in ("null", "")
    ]
    missing_sections = [t for t in toc_titles if t not in matched_titles]

    # 2) Feature 매칭
    feature_eval = match_features_ai(draft_text, features)
    missing_features = [
        f["feature"] for f in feature_eval
        if str(f.get("included")).lower() == "false"
    ]

    # --------------------------
    # 3) 상세 분석 + 보완 가이드
    # --------------------------
    section_details = []
    for sec in missing_sections:
        section_details.append({
            "section": sec,
            "reason": f"초안에 '{sec}' 항목이 존재하지 않습니다.",
            "suggestion": generate_suggestion(sec)
        })

    feature_details = []
    for f in feature_eval:
        if str(f.get("included")).lower() == "false":
            feature_details.append({
                "feature": f["feature"],
                "reason": f.get("reason"),
                "suggestion": generate_suggestion(f["feature"])
            })

    # --------------------------
    # 최종 Response
    # --------------------------
    return {
        "status": "success",

        "mapped_sections": section_mapping,
        "missing_sections": missing_sections,
        "feature_mismatch": missing_features,

        "section_analysis": {
            "missing_sections": missing_sections,
            "details": section_details
        },
        "feature_analysis": {
            "missing_features": missing_features,
            "details": feature_details
        },

        "draft_sections": draft_sections
    }
