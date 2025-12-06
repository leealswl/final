from __future__ import annotations
from typing import TypedDict, Dict, Any, List, Optional
import os
import requests

from langgraph.graph import StateGraph, END

from .comparison import (
    extract_text_from_tiptap,
    extract_section_headings,
    get_toc_titles,
    get_features,
    is_section_covered_by_headings,
    map_sections_ai,
    refine_missing_sections_ai,
    generate_suggestion,
    match_features_ai,
)
from .law_rag import verify_law_compliance
from .evaluation_criteria import evaluate_using_notice_criteria, find_eval_section

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8081")


class VerifyState(TypedDict, total=False):
    project_idx: int
    draft_json: Dict[str, Any]
    law_focus: Optional[str]
    law_focuses: Optional[List[str]]

    # working data
    ctx_data: Dict[str, Any]
    draft_text: str
    draft_headings: List[str]
    toc_titles: List[str]
    features: List[Dict[str, Any]]

    # results
    compare_result: Dict[str, Any]
    law_result: Dict[str, Any]          # 단일 포커스(호환용)
    law_results: Dict[str, Any]         # 복수 포커스 결과 맵
    notice_result: Dict[str, Any]
    summary: Dict[str, Any]

    errors: List[str]


def load_context_node(state: VerifyState) -> VerifyState:
    errors = state.get("errors", [])
    project_idx = state["project_idx"]
    draft_json = state["draft_json"]

    # 1) Spring context
    try:
        res = requests.get(
            f"{BACKEND_URL}/api/analysis/get-context",
            params={"projectIdx": project_idx},
            timeout=10,
        )
        if res.status_code != 200:
            msg = f"get-context HTTP {res.status_code}"
            errors.append(msg)
            state["ctx_data"] = {}
        else:
            body = res.json()
            ctx = body.get("data") or body
            state["ctx_data"] = ctx
    except Exception as e:
        msg = f"get-context 요청 실패: {e}"
        errors.append(msg)
        state["ctx_data"] = {}

    # 2) 초안 파싱
    state["draft_text"] = extract_text_from_tiptap(draft_json)
    state["draft_headings"] = extract_section_headings(draft_json)

    # 3) 컨텍스트에서 목차/feature 뽑기
    ctx_data = state.get("ctx_data") or {}
    state["toc_titles"] = get_toc_titles(ctx_data)
    state["features"] = get_features(ctx_data)

    state["errors"] = errors
    return state


def compare_node(state: VerifyState) -> VerifyState:
    errors = state.get("errors", [])
    draft_text = state.get("draft_text", "") or ""
    draft_sections = state.get("draft_headings", []) or []
    toc_titles = state.get("toc_titles", []) or []
    features = state.get("features", []) or []

    section_mapping = (
        map_sections_ai(draft_sections, toc_titles) if (draft_sections and toc_titles) else []
    )

    effective_toc_titles = toc_titles[:]
    written_sections: List[str] = []
    strict_missing_sections: List[str] = []

    for title in effective_toc_titles:
        if is_section_covered_by_headings(title, draft_sections):
            written_sections.append(title)
        else:
            strict_missing_sections.append(title)

    total_toc_count = len(effective_toc_titles)
    written_count = len(written_sections)
    toc_progress_percent = int(round(written_count / total_toc_count * 100)) if total_toc_count else 0

    section_eval = (
        refine_missing_sections_ai(draft_text, strict_missing_sections) if strict_missing_sections else []
    )
    section_eval_map = {item.get("section"): item for item in section_eval}

    final_missing_sections: List[str] = []
    section_details: List[Dict[str, Any]] = []

    for sec in strict_missing_sections:
        info = section_eval_map.get(sec) or {}
        reason = info.get("reason") or f"초안에 '{sec}' 항목이 반영되지 않았습니다."
        section_details.append(
            {
                "section": sec,
                "status": "missing",
                "reason": reason,
                "suggestion": generate_suggestion(sec),
            }
        )
        final_missing_sections.append(sec)

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
            feature_details.append(
                {
                    "feature": feature_name,
                    "status": status,
                    "reason": f.get("reason"),
                    "suggestion": generate_suggestion(feature_name),
                }
            )

    state["compare_result"] = {
        "mapped_sections": section_mapping,
        "missing_sections": final_missing_sections,
        "feature_mismatch": missing_features,
        "toc_progress": {
            "total_sections": total_toc_count,
            "written_sections": written_count,
            "progress_percent": toc_progress_percent,
        },
        "section_analysis": {"missing_sections": final_missing_sections, "details": section_details},
        "feature_analysis": {"missing_features": missing_features, "details": feature_details},
        "draft_sections": draft_sections,
    }
    state["errors"] = errors
    return state


def law_node(state: VerifyState) -> VerifyState:
    """법령 RAG 검증 (여러 focus를 순차 수행)"""
    errors = state.get("errors", [])
    text = state.get("draft_text", "") or ""
    focuses = state.get("law_focuses") or []
    single_focus = state.get("law_focus")

    if not text:
        msg = "법령 검증용 텍스트가 비어 있습니다."
        errors.append(msg)
        state["errors"] = errors
        state["law_result"] = {
            "status": "error",
            "risk_level": "UNKNOWN",
            "reason": msg,
        }
        return state

    if not focuses:
        focuses = [single_focus] if single_focus else [None]

    results: Dict[str, Any] = {}
    STATUS_ORDER = {"적합": 1, "보완": 2, "부적합": 3, "error": 4, None: 5}
    RISK_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "UNKNOWN": 4, None: 5}
    worst_status = None
    worst_risk = None

    for idx, fcs in enumerate(focuses):
        key = fcs or f"focus_{idx+1}"
        try:
            result = verify_law_compliance(text, fcs)
        except Exception as e:
            msg = f"법령 검증 실패({key}): {e}"
            print("⚠️ [law_node]", msg)
            errors.append(msg)
            result = {
                "status": "error",
                "risk_level": "UNKNOWN",
                "reason": msg,
            }
        results[key] = result

        st = result.get("status")
        rk = result.get("risk_level")
        if worst_status is None or STATUS_ORDER.get(st, 5) > STATUS_ORDER.get(worst_status, 5):
            worst_status = st
        if worst_risk is None or RISK_ORDER.get(rk, 5) > RISK_ORDER.get(worst_risk, 5):
            worst_risk = rk

    first_result = next(iter(results.values())) if results else {}
    state["law_results"] = results
    state["law_result"] = first_result
    state["law_worst_status"] = worst_status
    state["law_worst_risk"] = worst_risk
    state["errors"] = errors
    return state


def notice_node(state: VerifyState) -> VerifyState:
    errors = state.get("errors", [])
    ctx_data = state.get("ctx_data") or {}
    draft_text = state.get("draft_text", "") or ""
    extracted_features = ctx_data.get("extracted_features") or []

    criteria_raw_text = find_eval_section(extracted_features)
    if not criteria_raw_text:
        msg = "공고문에서 '평가기준' 섹션을 찾지 못했습니다."
        errors.append(msg)
        state["errors"] = errors
        state["notice_result"] = {
            "block_name": "공고문 평가기준 자가진단",
            "total_score": 0,
            "total_max_score": 0,
            "percent": 0,
            "items": [],
            "error": msg,
        }
        return state

    state["notice_result"] = evaluate_using_notice_criteria(
        draft_text=draft_text,
        criteria_raw_text=criteria_raw_text,
    )
    state["errors"] = errors
    return state


def summary_node(state: VerifyState) -> VerifyState:
    compare_result = state.get("compare_result") or {}
    law_result = state.get("law_result") or {}
    law_results = state.get("law_results") or {}
    notice_result = state.get("notice_result") or {}
    errors = state.get("errors") or []

    toc_progress = (compare_result.get("toc_progress") or {}).get("progress_percent", 0)
    notice_percent = notice_result.get("percent", 0)
    law_status = state.get("law_worst_status") or law_result.get("status")
    law_risk = state.get("law_worst_risk") or law_result.get("risk_level")

    state["summary"] = {
        "toc_progress_percent": toc_progress,
        "notice_percent": notice_percent,
        "law_status": law_status,
        "law_risk_level": law_risk,
        "errors": errors,
    }

    for key in ["ctx_data", "features", "toc_titles", "draft_text", "draft_headings"]:
        state.pop(key, None)
    state.pop("law_worst_status", None)
    state.pop("law_worst_risk", None)

    return state


def create_verify_graph():
    graph = StateGraph(VerifyState)

    graph.add_node("load_context", load_context_node)
    graph.add_node("compare", compare_node)
    graph.add_node("law", law_node)
    graph.add_node("notice", notice_node)
    # summary라는 state 키와 이름이 겹치지 않도록 노드 이름은 summary_stage로 분리
    graph.add_node("summary_stage", summary_node)

    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "compare")
    graph.add_edge("compare", "law")
    graph.add_edge("law", "notice")
    graph.add_edge("notice", "summary_stage")
    graph.add_edge("summary_stage", END)

    return graph.compile()
