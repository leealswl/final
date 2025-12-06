import os
import json
import re
import traceback
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

model = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0,
)

# ============================
# 1) 공고문 평가기준 기반 자동 평가 프롬프트
# ============================

EVAL_FROM_NOTICE_PROMPT = """
당신은 공공AX 프로젝트 사업 평가위원입니다.

[공고문 평가기준 원문]
{criteria_text}

[검토 대상 초안 내용]
{text}

역할:
- 위 평가기준 원문에서 '평가항목명'과 '배점'을 모두 추출하세요.
  예: "확산 가능성 5", "사업관리 적정성 5", "품질관리 우수성 10", "일자리 창출 5" 등
- 각 항목에 대해 다음 정보를 작성하세요:
  - name: 평가항목명 (공고문 표현 그대로 또는 자연스럽게 정리)
  - max_score: 공고문에 제시된 배점 (정수)
  - score: 0 ~ max_score 사이의 정수 점수 (초안 내용을 보고 판단)
  - status: "우수" | "보통" | "미흡" 중 하나
  - reason: 왜 이런 점수와 상태를 줬는지 요약 설명
  - suggestion: 미흡하거나 보완이 필요한 부분에 대한 개선 제안

추가 규칙:
- 공고문에 명시된 평가항목만 사용하고, 새로운 항목을 만들지 마세요.
- 총점은 보통 100점이지만, 여기서는 추출된 항목들의 배점을 그대로 사용합니다.
- 점수(score)는 반드시 0 이상 max_score 이하의 정수만 사용하세요.

출력 형식 (JSON만 출력):
{{
  "items": [
    {{
      "name": "확산 가능성",
      "max_score": 5,
      "score": 3,
      "status": "보통",
      "reason": "판단 근거",
      "suggestion": "보완 제안"
    }}
  ],
  "total_score": 3,
  "total_max_score": 5
}}
""".strip()


def evaluate_using_notice_criteria(draft_text: str, criteria_raw_text: str) -> dict:
    """
    공고문 평가기준 원문(criteria_raw_text)을 그대로 넣고,
    거기서 평가항목/배점을 추출해서 초안(draft_text)을 점수화하는 함수.
    """
    try:
        prompt = EVAL_FROM_NOTICE_PROMPT.format(
            criteria_text=criteria_raw_text,
            text=draft_text,
        )

        resp = model.invoke(prompt)
        raw = (resp.content or "").strip()

        # ```json ... ``` 래핑 제거
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-zA-Z0-9]*\s*", "", raw)
            if raw.endswith("```"):
                raw = raw[: raw.rfind("```")].strip()

        data = json.loads(raw)

        # 안전장치: 기본 구조 보정
        items = data.get("items") or []
        if not isinstance(items, list):
            items = []

        total_score = 0
        total_max = 0
        cleaned_items = []

        for item in items:
            name = item.get("name", "")
            max_score = int(item.get("max_score", 0) or 0)
            score = int(item.get("score", 0) or 0)

            if max_score < 0:
                max_score = 0
            if score < 0:
                score = 0
            if score > max_score:
                score = max_score

            total_score += score
            total_max += max_score

            cleaned_items.append(
                {
                    "name": name,
                    "max_score": max_score,
                    "score": score,
                    "status": item.get("status", "미흡"),
                    "reason": item.get("reason", "") or "",
                    "suggestion": item.get("suggestion", "") or "",
                }
            )

        if total_max == 0:
            percent = 0
        else:
            percent = round(total_score / total_max * 100)

        return {
            "block_name": "공고문 평가기준 자가진단",
            "total_score": total_score,
            "total_max_score": total_max,
            "percent": percent,  # 총점 100 기준 환산 느낌
            "items": cleaned_items,
        }

    except Exception as e:
        print("❌ evaluate_using_notice_criteria 예외:", e)
        traceback.print_exc()
        return {
            "block_name": "공고문 평가기준 자가진단",
            "total_score": 0,
            "total_max_score": 0,
            "percent": 0,
            "items": [],
            "error": str(e),
        }
def find_eval_section(extracted_features: list[dict]) -> str | None:
    """
    /api/analysis/get-context 에서 내려주는 extracted_features 리스트 중에서
    '평가기준' 섹션(full_content)을 찾아서 돌려준다.

    - feature_name / feature_code 에 평가 관련 키워드가 들어있으면 우선 반환
    - 그래도 못 찾으면 full_content 내부에서 키워드 검색
    """
    if not extracted_features:
        return None

    keywords = ["평가기준", "평가 기준", "평가항목", "평가 항목", "배점", "심사기준", "심사 기준"]

    def has_keyword(text: str) -> bool:
        return any(k in text for k in keywords)

    # 1차: feature_name / feature_code 기준으로 찾기
    for f in extracted_features:
        name = (f.get("feature_name") or "").strip()
        code = (f.get("feature_code") or "").strip()
        label = f"{name} {code}"

        if has_keyword(label):
            return f.get("full_content", "") or ""

    # 2차: full_content 안에서 키워드 검색
    for f in extracted_features:
        full = (f.get("full_content") or "").strip()
        if not full:
            continue
        if has_keyword(full):
            return full

    # 그래도 없으면 None
    return None
