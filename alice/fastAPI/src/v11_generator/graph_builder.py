from typing import Dict, Any
from langgraph.graph import StateGraph, END, START
from .state_types import ProposalGenerationState

from .nodes.fetch_context import fetch_context_for_proposal
from .nodes.generate_query import generate_query
from .nodes.ask_user_and_update_data import ask_user_and_update_data
from .nodes.assess_sufficiency import assess_info
from .nodes.history_checker import history_checker
from .nodes.generate_draft import generate_proposal_draft
from .nodes.edit_draft import edit_proposal_draft
from .nodes.classify_intent import classify_user_intent

# ----------------------------
# 라우터 함수
# ----------------------------
# 질문이지 판단하는걸 LLM한테
def route_after_save_user(state: ProposalGenerationState) -> str:
    """사용자 요청이 수정 요청인지 질문인지 판단"""
    user_prompt = state.get("user_prompt", "").lower()
    
    # 수정 요청 키워드 확인
    edit_keywords = ["바꿔", "수정", "변경", "고쳐", "교체", "다시 써", "재작성", "바꾸", "수정해", "변경해", "고쳐줘"]
    is_edit_request = any(keyword in user_prompt for keyword in edit_keywords)
    
    if is_edit_request:
        print(f"🔍 수정 요청 감지: {user_prompt}")
        return "edit_draft"
    
    # 일반 요청 (정보 제공 또는 질문)
    return "history_checker"

def route_after_classification(state: ProposalGenerationState) -> str:
    """LLM이 판단한 의도(user_intent)에 따라 분기"""
    intent = state.get("user_intent", "INFO")
    
    if intent == "EDIT":
        return "edit_draft"
    else:
        return "history_checker"


def route_after_history_check(state: ProposalGenerationState) -> str:
    """이미 작성된 섹션이면 바로 generate_draft, 아니면 평가로 진행"""
    if state.get("target_already_completed", False):
        return "generate_draft"
    return "ASSESS_INFO"


def route_after_assessment(state: ProposalGenerationState) -> str:
    """필요 정보 충분 여부 -> (draft 생성 or 질문 생성)"""
    if state.get("sufficiency", False):
        return "generate_draft"
    return "GENERATE_QUERY"


# ----------------------------
# 그래프 생성
# ----------------------------

def create_proposal_graph() -> StateGraph:
    workflow = StateGraph(ProposalGenerationState)

    # 노드 등록
    workflow.add_node("FETCH_CONTEXT", fetch_context_for_proposal)
    workflow.add_node("SAVE_USER", ask_user_and_update_data)
    workflow.add_node("history_checker", history_checker)
    workflow.add_node("ASSESS_INFO", assess_info)
    workflow.add_node("classify_intent", classify_user_intent)
    workflow.add_node("GENERATE_QUERY", generate_query)
    workflow.add_node("generate_draft", generate_proposal_draft)
    workflow.add_node("edit_draft", edit_proposal_draft)

    # 엣지 연결
    workflow.add_edge(START, "FETCH_CONTEXT")
    workflow.add_edge("FETCH_CONTEXT", "SAVE_USER")
    workflow.add_edge("SAVE_USER", "classify_intent")

    # SAVE_USER 다음 분기: 수정 요청이면 edit_draft, 아니면 history_checker
    workflow.add_conditional_edges(
        "classify_intent",
        route_after_classification,
        {
            "edit_draft": "edit_draft",  # 수정 요청 시
            "history_checker": "history_checker"  # 일반 요청 시
        }
    )

    workflow.add_edge("history_checker", "ASSESS_INFO")

    workflow.add_conditional_edges(
        "ASSESS_INFO",
        route_after_assessment,
        {
            "generate_draft": "generate_draft",
            "GENERATE_QUERY": "GENERATE_QUERY",
        }
    )

    # 질문 생성 후 → 사용자 입력을 받고 다시 저장으로!
    workflow.add_edge("GENERATE_QUERY", END)

    # Draft 생성 후 → 다음 섹션 질문 생성
    workflow.add_edge("generate_draft", END)

    # 수정 완료 후 → END
    workflow.add_edge("edit_draft", END)

    return workflow

