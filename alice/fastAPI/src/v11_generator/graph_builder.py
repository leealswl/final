from typing import Dict, Any, List
from langgraph.graph import StateGraph, END, START
from .state_types import ProposalGenerationState 

# --- 사용하는 노드만 임포트 ---
from .nodes.fetch_context import fetch_context_for_proposal
from .nodes.generate_query import generate_query
from .nodes.ask_user_and_update_data import ask_user_and_update_data 
from .nodes.assess_sufficiency import assess_info
from .nodes.manage_progression import manage_progression
from .nodes.histroy_checker import history_checker


# ---------------------------------------------------------
# 1. [라우터] 판결에 따라 갈림길 (ASSESS_INFO의 결과에 따라 분기)
# ---------------------------------------------------------
def route_after_assessment(state: ProposalGenerationState) -> str:
    """판단 결과: 충분하면 다음 섹션으로, 부족하면 추가 질문으로"""
    # sufficiency: True (70점 이상) -> 다음 섹션으로 이동해야 함
    if state.get("sufficiency", False):
        # MANAGE_PROGRESSION 노드가 다음 섹션 인덱스를 설정하고 accumulated_data를 정리함
        return "MANAGE_PROGRESSION" 
    
    # sufficiency: False (70점 미만) -> 추가 질문 필요
    return "GENERATE_QUERY"         

# ---------------------------------------------------------
# 2. 그래프 구축 (섹션 단위 진행 버전)
# ---------------------------------------------------------

def create_proposal_graph() -> StateGraph:
    workflow = StateGraph(ProposalGenerationState)

    # === 1. 노드 추가 ===
    # A. 초기화 (Context 설정)
    workflow.add_node("FETCH_CONTEXT", fetch_context_for_proposal)
    # B. 데이터 저장 (사용자 답변 기록)
    workflow.add_node("SAVE_USER", ask_user_and_update_data)
    # C. 평가 (70점 이상인지 판단)
    workflow.add_node("ASSESS_INFO", assess_info)
    # D. 진행 관리 (다음 섹션으로 인덱스 이동)
    workflow.add_node("MANAGE_PROGRESSION", manage_progression) 
    # E. 질문 생성 (질문자 역할)
    workflow.add_node("GENERATE_QUERY", generate_query)
    # F. 목차 관리
    workflow.add_node("HISTORY_CHECKER", history_checker)
    
    
    # === 2. 엣지 연결 (섹션 단위 반복 루프) ===
    
    # 1. 시작: Start -> 설정
    workflow.add_edge(START, "FETCH_CONTEXT")
    
    # 2. 첫 루프 시작: 설정 -> 저장
    # (FastAPI에서 이미 user_prompt가 들어왔으므로 바로 저장 후 평가로 넘어갑니다)
    workflow.add_edge("FETCH_CONTEXT", "SAVE_USER")
    
    # 목차 관리하는 히스토리 체커 노드 추가
    workflow.add_edge("SAVE_USER", "HISTORY_CHECKER")


    # 3. 평가: 저장 -> 평가
    workflow.add_edge("HISTORY_CHECKER", "ASSESS_INFO")
    
    # 4. 조건부 분기: 평가 -> (합격) 매니저 OR (불합격) 질문자
    workflow.add_conditional_edges(
        "ASSESS_INFO",
        route_after_assessment,
        {
            "MANAGE_PROGRESSION": "MANAGE_PROGRESSION", # 합격 시 -> 다음 섹션으로 인덱스 변경
            "GENERATE_QUERY": "GENERATE_QUERY"          # 불합격 시 -> 현재 섹션에 대한 추가 질문 생성
        }
    )
    # 5. 다음 질문: 매니저(인덱스 이동 완료) -> 질문자
    # (새로운 섹션에 대한 첫 질문을 생성하도록 루프 재시작)
    workflow.add_edge("MANAGE_PROGRESSION", "GENERATE_QUERY")
    
    # 6. 종료: 질문 생성 -> END
    # (GENERATE_QUERY는 사용자에게 질문을 던지고 LangGraph 실행을 일시 중단하는 역할)
    workflow.add_edge("GENERATE_QUERY", END)
    
    return workflow