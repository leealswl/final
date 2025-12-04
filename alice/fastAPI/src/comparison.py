from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from openai import OpenAI
import json
import re
import requests
import os

router = APIRouter()
client = OpenAI()

# Spring 백엔드 URL (환경변수 없으면 기본값 사용)
SPRING_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8081")


class DraftCompareRequest(BaseModel):
    project_idx: int
    draft_json: Dict[str, Any]


# ===============================
# 공통 상수 / 유틸
# ===============================

# 🔹 섹션에서 아예 무시하고 싶은 키워드들 (사업계획서 작성요령/목차 등)
SECTION_EXCLUDE_KEYWORDS = [
    "사업계획서 작성요령",
    "사업계획서 작성 방법",
    "사업계획서 작성방법",
    "사업계획서 목차",
    "신청서 작성요령",
    "신청서 작성 방법",
    "신청서 작성방법",
    "초안 작성요령",
    "작성 예시",
]

# 🔹 섹션 제목에서 빼고 싶은 흔한 단어들 (핵심 키워드 추출용)
SECTION_STOPWORDS = [
    "사업계획서",
    "신청서",
    "계획",
    "내용",
    "사항",
    "기타",
    "등",
    "및",
    "관련",
    "요약",
    "구성",
    "개요",
    "설명",
]


def should_exclude_section(title: str) -> bool:
    """사업계획서 작성요령/목차 같은 섹션은 비교 대상에서 제외."""
    for kw in SECTION_EXCLUDE_KEYWORDS:
        if kw in title:
            return True
    return False


def normalize_title_text(text: str) -> str:
    """
    섹션 제목/heading을 비교하기 위해 정규화:
    - 앞쪽 번호/기호 제거 (예: '9.1 ', '(1)', '①' 등)
    - 공백/특수문자 제거
    """
    if not text:
        return ""
    s = str(text)
    # 앞의 번호/기호 제거
    s = re.sub(r"^[\d\.\-\)\(①②③④⑤⑥⑦⑧⑨⑩\s]+", "", s)
    # 공백/탭 제거
    s = re.sub(r"\s+", "", s)
    return s


def extract_core_keywords(title: str) -> List[str]:
    """
    섹션 제목에서 핵심 키워드만 뽑기.
    예) '9.1 파급효과 및 활용방안' -> ['파급효과', '활용방안']
    """
    if not title:
        return []
    # 번호 제거 후 토큰화
    s = re.sub(r"^[\d\.\-\)\(①②③④⑤⑥⑦⑧⑨⑩\s]+", "", title).strip()
    tokens = re.split(r"[·,/()\[\]\s]+", s)
    keywords = []
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        if t in SECTION_STOPWORDS:
            continue
        if len(t) < 2:
            continue
        keywords.append(t)
    return keywords


def is_section_covered_by_headings(toc_title: str, draft_headings: List[str]) -> bool:
    """
    '목차 섹션 제목'이 초안의 heading 중 어느 하나와라도
    '충분히 비슷한 제목'이면 해당 섹션을 작성한 것으로 간주.

    - 정확히 같은 문자열일 필요는 없음.
    - 번호(1., 1.1 등) / 공백은 무시.
    - '파급효과 및 활용방안' vs '파급효과' vs '기대효과 및 활용방안' 등 유연하게 처리.
    - 하지만 '본문 내용'만 보고 판단하지 않고, 반드시 heading(제목)에만 의존.
    """
    if not toc_title or not draft_headings:
        return False

    norm_toc = normalize_title_text(toc_title)
    toc_keywords = extract_core_keywords(toc_title)

    for h in draft_headings:
        norm_h = normalize_title_text(h)
        if not norm_h:
            continue

        # 1) 정규화된 문자열끼리 부분 포함 관계면 매칭
        if norm_toc and (norm_toc in norm_h or norm_h in norm_toc):
            return True

        # 2) 핵심 키워드가 heading 안에 하나라도 포함되면 매칭 인정
        if toc_keywords:
            overlap = sum(1 for kw in toc_keywords if kw and kw in norm_h)
            if overlap >= 1:
                return True

    return False


# -------------------------------
# JSON / TEXT UTILITIES
# -------------------------------
def extract_json_from_response(text: str) -> str:
    """GPT 응답에서 ```json``` 블록만 추출"""
    codeblock = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    return codeblock.group(1).strip() if codeblock else text.strip()


def extract_text_from_tiptap(doc_json: Dict[str, Any]) -> str:
    """tiptap JSON에서 순수 텍스트만 추출"""
    texts: List[str] = []
    for block in doc_json.get("content", []):
        if "content" in block:
            for item in block["content"]:
                if "text" in item:
                    texts.append(item["text"].strip())
    return "\n".join(texts)


def extract_section_headings(doc_json: Dict[str, Any]) -> List[str]:
    """tiptap JSON에서 heading 타입 섹션 제목만 추출"""
    headings: List[str] = []
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
# GPT: 섹션 매핑 (표시용)
# -------------------------------
def map_sections_ai(draft_sections: List[str], toc_sections: List[str]) -> List[dict]:
    """
    초안 섹션 제목 vs 공고문 목차를 의미적으로 매핑.
    - 이건 "표시용" 매핑이라, 누락 판단에는 직접 사용하지 않고
      프론트에서 참고용으로만 사용.
    """
    if not draft_sections or not toc_sections:
        return []

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
    except Exception:
        print("❌ 매핑 JSON 파싱 실패:", clean)
        return []


# -------------------------------
# GPT: Feature 포함 여부 체크 (ok / partial / missing)
# -------------------------------
def match_features_ai(draft_text: str, features: List[Dict[str, Any]]) -> List[dict]:
    """
    각 feature에 대해 초안이
    - ok: 공고문 기준으로 충분히 반영
    - partial: 관련 내용은 있지만 세부 조건/정량 지표 등이 부족
    - missing: 관련 내용이 거의/전혀 없음
    을 판정하도록 GPT에 요청.
    """
    feature_items_for_prompt = []
    for f in features:
        name = (
            f.get("title")
            or f.get("feature_name")
            or f.get("name")
            or f.get("summary")  # 차선책
        )
        if not name:
            continue

        summary = f.get("summary") or ""
        source_section = f.get("source_section") or f.get("section") or ""
        feature_items_for_prompt.append(
            f"- 이름: {name}\n  요약: {summary}\n  출처 섹션: {source_section}"
        )

    if not feature_items_for_prompt:
        print("⚠️ match_features_ai: 사용할 수 있는 feature 제목이 없습니다.")
        return []

    features_block = "\n".join(feature_items_for_prompt)

    prompt = {
        "role": "user",
        "content": f"""
당신은 '정부지원사업 기획서 검토 전문가'입니다.

[초안 내용]
{draft_text}

[공고문에서 추출한 Feature 목록]
{features_block}

각 feature가 초안에 어느 정도로 반영되어 있는지
다음 3단계로만 상태를 판정하세요.

- "ok": 초안에 해당 조건/내용이 공고문 기준으로 충분히 반영되어 있음
- "partial": 관련 내용은 있지만, 세부 일정/정량 지표/조건 일치 등에서 보완이 필요함
- "missing": 초안에 이 feature와 직접적으로 관련된 내용이 거의 또는 전혀 없음

⚠️ 중요:
- 초안에 관련 내용이 '조금이라도' 언급되어 있으면 절대로 "missing"으로 두지 마세요.
- 그 경우 공고문 수준에 미치지 못한다고 판단되면 "partial"로 두고,
  어떤 점이 부족한지 reason에 써 주세요.
- 정말로 관련 내용이 거의/전혀 없을 때만 "missing"으로 두세요.

JSON ONLY 로만 응답하세요:

[
  {{
    "feature": "공고문에서의 feature 이름 그대로",
    "status": "ok" | "partial" | "missing",
    "reason": "두세 문장으로 왜 그렇게 판단했는지 설명"
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
        parsed = json.loads(clean)
        for item in parsed:
            if "status" not in item:
                included_val = str(item.get("included")).lower()
                item["status"] = "ok" if included_val == "true" else "missing"
        return parsed
    except Exception:
        print("❌ Feature JSON 파싱 실패:", clean)
        return []


# -------------------------------
# GPT: 섹션 누락 후보 설명/보완 가이드 생성용
# -------------------------------
def refine_missing_sections_ai(draft_text: str, sections: List[str]) -> List[dict]:
    """
    1차 필터에서 'missing_sections'로 잡힌 섹션들에 대해
    왜 부족한지 / 어떻게 보완하면 좋은지 reason만 받아오기 위한 용도.
    (여기서는 status를 그대로 믿지 않고, 반드시 missing으로 유지함)
    """
    if not sections:
        return []

    sections_block = "\n".join([f"- {s}" for s in sections])

    prompt = {
        "role": "user",
        "content": f"""
당신은 '정부지원사업 기획서 검토 전문가'입니다.

[초안 내용]
{draft_text}

[공고문 섹션 후보 목록]
{sections_block}

각 섹션이 초안에 어떤 점에서 부족한지,
그리고 어떻게 보완하면 좋을지 설명해주세요.

JSON ONLY 로만 응답하세요:

[
  {{
    "section": "공고문 섹션 이름 그대로",
    "status": "ok" | "partial" | "missing",
    "reason": "두세 문장으로 왜 그렇게 판단했는지 설명"
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
        parsed = json.loads(clean)
        return parsed
    except Exception:
        print("❌ 섹션 재평가 JSON 파싱 실패:", clean)
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
# Spring 응답에서 목차/Feature 뽑기
# -------------------------------
def get_toc_titles(ctx_data: Dict[str, Any]) -> List[str]:
    """
    Spring 응답에서 result_toc / sections / toc 등에서 섹션 title을 최대한 뽑아냄.
    - result_toc가 문자열(JSON string)이어도 처리
    - 일부 '사업계획서 작성요령' 같은 건 SECTION_EXCLUDE_KEYWORDS로 필터링
    """
    if not isinstance(ctx_data, dict):
        return []

    sections: Optional[List[Any]] = None

    toc_raw = (
        ctx_data.get("result_toc")
        or ctx_data.get("resultToc")
        or ctx_data.get("toc")
    )

    if isinstance(toc_raw, str):
        try:
            print("📘 result_toc가 str이라 JSON 파싱 시도:", toc_raw[:120], "...")
            toc_raw = json.loads(toc_raw)
        except Exception as e:
            print("❌ result_toc JSON 파싱 실패:", e)

    if isinstance(toc_raw, dict):
        sections = toc_raw.get("sections") or toc_raw.get("toc")
    elif isinstance(toc_raw, list):
        sections = toc_raw

    if sections is None and isinstance(ctx_data.get("sections"), list):
        sections = ctx_data["sections"]

    if not sections:
        print("⚠️ get_toc_titles: sections 데이터를 찾지 못했습니다. result_toc 타입:", type(toc_raw))
        return []

    titles: List[str] = []

    for sec in sections:
        title = None
        if isinstance(sec, dict):
            title = sec.get("title") or sec.get("sectionTitle") or sec.get("name")
        else:
            title = str(sec)

        if not title:
            continue

        # 작성요령/목차 등 불필요 섹션 필터링
        if should_exclude_section(str(title)):
            continue

        titles.append(str(title))

    return titles


def get_features(ctx_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Spring 응답에서 extracted_features 또는 features를 리스트로 반환.
    """
    if not isinstance(ctx_data, dict):
        return []

    features = ctx_data.get("extracted_features")
    if features is None:
        features = ctx_data.get("features")

    if not isinstance(features, list):
        print("⚠️ get_features: features가 list가 아닙니다.", type(features), features)
        return []

    return features


# -------------------------------
# Main Compare API
# -------------------------------
@router.post("/draft")
def compare_draft_ai(request: DraftCompareRequest):
    """
    초안(tiptap JSON)과 공고문 분석 결과를 비교해
    누락 섹션/Feature + 보완 가이드 반환

    ✅ 변경 포인트:
    - 목차 기준으로 "제목이 있는지"를 먼저 strict하게 판단
    - 제목이 전혀 없으면, 본문 내용이 비슷해도 무조건 missing_sections에 포함
    - 단, 제목 매칭은 '정확 일치'가 아니라 핵심 키워드 기반 fuzzy 매칭
    - 별도로 목차 기준 progress(%)도 계산해서 내려줌
    """
    try:
        print(f"📄 /compare/draft 요청 수신: project_idx={request.project_idx}")

        # 1) 초안 텍스트/섹션 추출
        draft_text = extract_text_from_tiptap(request.draft_json)
        draft_sections = extract_section_headings(request.draft_json)
        print("✏️ 초안 heading 목록:", draft_sections)

        # 2) Spring 공고문 분석 데이터 가져오기
        try:
            spring_res = requests.get(
                f"{SPRING_BACKEND_URL}/api/analysis/get-context",
                params={"projectIdx": request.project_idx},
                timeout=10,
            )
        except Exception as e:
            print("❌ Spring 서버 호출 실패:", e)
            return {
                "status": "error",
                "message": f"Spring backend 호출 실패: {e}",
            }

        if spring_res.status_code != 200:
            print("❌ Spring 응답 상태 코드:", spring_res.status_code, spring_res.text)
            return {
                "status": "error",
                "message": f"Spring backend 응답 오류: {spring_res.status_code}",
            }

        spring_json = spring_res.json()
        ctx_data = spring_json.get("data") or spring_json

        if isinstance(ctx_data, dict):
            print("🔎 get-context ctx_data keys:", list(ctx_data.keys()))
        else:
            print("🔎 get-context ctx_data type:", type(ctx_data))

        # 3) 목차 title, feature 리스트 추출
        toc_titles = get_toc_titles(ctx_data)
        features = get_features(ctx_data)

        print("📚 공고문 목차 titles:", toc_titles)

        # -------------------------
        # 4) 섹션 매핑 (표시용)
        # -------------------------
        section_mapping = map_sections_ai(draft_sections, toc_titles)

        # -------------------------
        # 5) "목차 제목 기준" missing 섹션 계산
        # -------------------------
        effective_toc_titles = toc_titles[:]  # 필터링된 상태 그대로 사용

        written_sections: List[str] = []
        strict_missing_sections: List[str] = []

        for title in effective_toc_titles:
            if is_section_covered_by_headings(title, draft_sections):
                written_sections.append(title)
            else:
                strict_missing_sections.append(title)

        print("✅ heading 기준 존재 섹션:", written_sections)
        print("❌ heading 기준 누락 섹션:", strict_missing_sections)

        # 🔹 목차 기준 progress 계산
        total_toc_count = len(effective_toc_titles)
        written_count = len(written_sections)
        toc_progress_percent = (
            int(round(written_count / total_toc_count * 100))
            if total_toc_count > 0 else 0
        )

        # -------------------------
        # 6) GPT로 missing 섹션 상세 reason/suggestion 생성
        #     (status는 항상 missing으로 고정)
        # -------------------------
        section_eval = (
            refine_missing_sections_ai(draft_text, strict_missing_sections)
            if strict_missing_sections else []
        )
        section_eval_map = {item.get("section"): item for item in section_eval}

        final_missing_sections: List[str] = []
        section_details: List[Dict[str, Any]] = []

        for sec in strict_missing_sections:
            info = section_eval_map.get(sec)
            raw_status = (info or {}).get("status", "missing")
            reason = (info or {}).get("reason")

            # ✅ 제목이 아예 없으면, GPT가 status를 ok/partial로 줘도
            #    "형식상 누락"으로 강제 missing 유지
            status = "missing"

            if not reason:
                reason = f"초안에 '{sec}' 항목은 별도의 섹션 제목이나 내용 구조로 거의 반영되어 있지 않습니다."

            section_details.append({
                "section": sec,
                "status": status,
                "reason": reason,
                "suggestion": generate_suggestion(sec),
            })
            final_missing_sections.append(sec)

        missing_sections = final_missing_sections

        # -------------------------
        # 7) Feature 매칭 (Feature가 있을 때만)
        # -------------------------
        feature_eval = match_features_ai(draft_text, features) if features else []

        missing_features: List[str] = []
        feature_details: List[Dict[str, Any]] = []

        for f in feature_eval:
            feature_name = f.get("feature")
            if not feature_name:
                continue

            status = f.get("status")
            if not status:
                included_val = str(f.get("included")).lower()
                status = "ok" if included_val == "true" else "missing"

            status = status.lower()
            if status not in ("ok", "partial", "missing"):
                status = "missing"

            if status == "missing":
                missing_features.append(feature_name)

            if status in ("partial", "missing"):
                feature_details.append({
                    "feature": feature_name,
                    "status": status,
                    "reason": f.get("reason"),
                    "suggestion": generate_suggestion(feature_name),
                })

        # -------------------------
        # 8) 최종 Response
        # -------------------------
        return {
            "status": "success",

            # 섹션 매핑 (표시용)
            "mapped_sections": section_mapping,       # 목차 없으면 []

            # 누락 정보
            "missing_sections": missing_sections,     # 제목 기준으로 진짜 누락된 섹션만
            "feature_mismatch": missing_features,     # 진짜 missing인 feature만

            # 목차 기준 progress 정보
            "toc_progress": {
                "total_sections": total_toc_count,
                "written_sections": written_count,
                "progress_percent": toc_progress_percent,
            },

            "section_analysis": {
                "missing_sections": missing_sections,
                "details": section_details,           # 각 섹션별 reason + suggestion
            },
            "feature_analysis": {
                "missing_features": missing_features,
                "details": feature_details,           # partial/missing만, status 포함
            },

            "draft_sections": draft_sections,
        }

    except Exception as e:
        print("❌ /compare/draft 처리 중 예외:", e)
        return {
            "status": "error",
            "message": f"초안 비교 중 서버 오류 발생: {e}",
        }
