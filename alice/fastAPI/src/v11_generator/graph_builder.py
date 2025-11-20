from typing import Dict, Any, List
from langgraph.graph import StateGraph, END, START
from .state_types import ProposalGenerationState 

# --- 사용하는 노드만 임포트 ---
from .nodes.fetch_context import fetch_context_for_proposal
from .nodes.generate_query import generate_query
from .nodes.ask_user_and_update_data import ask_user_and_update_data 
from .nodes.assess_sufficiency import assess_info
from .nodes.manage_progression import manage_progression

# --- 사용하지 않는 노드들은 주석 처리 (나중에 복구 가능) ---
# from .nodes.generate_draft import generate_proposal_draft
# from .nodes.review_and_fix import review_draft, fix_draft_via_llm
# from .nodes.confirm_generation import confirm_generation

# ---------------------------------------------------------
# [주석 처리] 1. 엣지 로직 (데이터 백업 및 흐름 제어)
# ---------------------------------------------------------
# MAX_ATTEMPTS = 5 
# 
# def update_attempt_count(state: ProposalGenerationState) -> Dict[str, Any]:
#     """질문 횟수 증가"""
#     return {"attempt_count": state.get("attempt_count", 0) + 1}
# 
# def route_after_assessment(state: ProposalGenerationState) -> str:
#     """판단 결과: 부족하면 질문, 충분하면 챕터넘기기"""
#     is_sufficient = state.get("sufficiency", False)
#     attempt_count = state.get("attempt_count", 0)
#     
#     if is_sufficient or attempt_count >= MAX_ATTEMPTS:
#         return "UPDATE_CHAPTER" # 충분 -> 챕터 넘기기
#     return "GENERATE_QUERY"     # 부족 -> 질문하기
# 
# def update_chapter_and_loop(state: ProposalGenerationState) -> Dict[str, Any]:
#     """챕터 데이터 백업 및 다음 챕터 설정"""
#     current_idx = state.get('current_chapter_index', 0)
#     toc_structure = state.get('draft_toc_structure', [])
#     
#     # 데이터 백업
#     previous_accumulated = state.get("accumulated_data", "")
#     current_collected = state.get("collected_data", "")
#     
#     if current_collected.strip():
#         new_accumulated = f"{previous_accumulated}\n\n=== Chapter {current_idx + 1} Data ===\n{current_collected}"
#     else:
#         new_accumulated = previous_accumulated
# 
#     # 다음 챕터 계산
#     next_idx = current_idx + 1
#     
#     if next_idx >= len(toc_structure):
#         return {
#             "accumulated_data": new_accumulated,
#             "collected_data": "",
#             "next_step": "ALL_DONE" # 끝!
#         }
# 
#     # 다음 챕터 설정
#     next_chapter = toc_structure[next_idx]
#     next_chapter_number = next_chapter.get("number", str(next_idx + 1))
#     
#     next_subchapters_list = []
#     for item in toc_structure:
#         item_number = item.get('number', '')
#         if '.' in item_number and item_number.startswith(next_chapter_number + '.'):
#             next_subchapters_list.append({
#                 "number": item_number,
#                 "title": item.get('title'),
#                 "description": item.get('description')
#             })
# 
#     print(f"🔄 챕터 전환: {next_idx + 1}장 ({next_chapter.get('title')}) 진입")
# 
#     return {
#         "current_chapter_index": next_idx,
#         "target_chapter": next_chapter.get("title"),
#         "target_subchapters": next_subchapters_list,
#         "missing_subsections": [sub['title'] for sub in next_subchapters_list],
#         "attempt_count": 0,
#         "collected_data": "",
#         "sufficiency": False,
#         "accumulated_data": new_accumulated,
#         "next_step": "Assess_Next"
#     }
# 
# def route_chapter_manager(state: ProposalGenerationState) -> str:
#     """모든 챕터 끝났으면 바로 생성"""
#     if state.get("next_step") == "ALL_DONE":
#         return "GENERATE_DRAFT"
#     return "ASSESS_INFO"
# 
# def confirm_router(state: ProposalGenerationState) -> str:
#     return "GENERATE_DRAFT"
# 
# def review_router(state: ProposalGenerationState) -> str:
#     return "FINISH"


# ---------------------------------------------------------
# 1. [라우터] 판결에 따라 갈림길
# ---------------------------------------------------------
def route_after_assessment(state: ProposalGenerationState) -> str:
    if state.get("sufficiency", False):
        return "MANAGE_PROGRESSION" # 합격 -> 바로 매니저에게 (작가는 건너뜀)
    return "GENERATE_QUERY"         # 불합격 -> 더 질문해

# ---------------------------------------------------------
# 2. 그래프 구축 (간소화 버전)
# ---------------------------------------------------------

def create_proposal_graph() -> StateGraph:
    workflow = StateGraph(ProposalGenerationState)

    # === 1. 노드 추가 (사용하는 것만 활성화) ===
    workflow.add_node("FETCH_CONTEXT", fetch_context_for_proposal)
        # 답변 저장 노드 추가 (이름: SAVE_USER)
    workflow.add_node("SAVE_USER", ask_user_and_update_data)
        # 질문 생성 노드 추가
    workflow.add_node("GENERATE_QUERY", generate_query)
        # 판사 노드 추가
    workflow.add_node("ASSESS_INFO", assess_info)
        # 매니저 노드 추가
    workflow.add_node("MANAGE_PROGRESSION", manage_progression) 
    
    
    # [주석 처리된 기존 노드들]
    # workflow.add_node("ASSESS_INFO", assess_info)
    # workflow.add_node("UPDATE_ATTEMPT", update_attempt_count)
    # workflow.add_node("UPDATE_CHAPTER", update_chapter_and_loop)
    # workflow.add_node("CONFIRM_GEN", confirm_generation)
    # workflow.add_node("GENERATE_DRAFT", generate_proposal_draft)
    # workflow.add_node("REVIEW_AND_FIX", review_draft) 
    # workflow.add_node("FIX_DRAFT", fix_draft_via_llm) 

    # === 2. 엣지 연결 (직선 흐름: Start -> Fetch -> Save -> Query -> End) ===
# 시작 -> 설정
    workflow.add_edge(START, "FETCH_CONTEXT")
    
    # 설정 -> 저장
    workflow.add_edge("FETCH_CONTEXT", "SAVE_USER")
    # [핵심] 저장 -> 평가(채점)
    workflow.add_edge("SAVE_USER", "ASSESS_INFO")
    # 평가 -> (조건부) -> 매니저 OR 질문자
    workflow.add_conditional_edges(
        "ASSESS_INFO",
        route_after_assessment,
        {
            "MANAGE_PROGRESSION": "MANAGE_PROGRESSION", # 합격 시 매니저로
            "GENERATE_QUERY": "GENERATE_QUERY"          # 불합격 시 질문자로
        }
    )
    # 매니저(정리 끝) -> 질문자(다음 챕터 질문해)
    workflow.add_edge("MANAGE_PROGRESSION", "GENERATE_QUERY")
    
    workflow.add_edge("GENERATE_QUERY", END)
    
    return workflow

    # [주석 처리된 기존 엣지 연결]
    # workflow.add_edge("FETCH_CONTEXT", "ASSESS_INFO")
    # 
    # workflow.add_conditional_edges(
    #     "ASSESS_INFO",
    #     route_after_assessment,
    #     {
    #         "GENERATE_QUERY": "UPDATE_ATTEMPT",
    #         "UPDATE_CHAPTER": "UPDATE_CHAPTER"
    #     }
    # )
    # 
    # workflow.add_edge("UPDATE_ATTEMPT", "GENERATE_QUERY")
    # workflow.add_edge("GENERATE_QUERY", "ASK_USER")
    # workflow.add_edge("ASK_USER", "ASSESS_INFO")
    # 
    # workflow.add_conditional_edges(
    #     "UPDATE_CHAPTER",
    #     route_chapter_manager,
    #     {
    #         "ASSESS_INFO": "ASSESS_INFO",
    #         "GENERATE_DRAFT": "GENERATE_DRAFT" # 나중에 CONFIRM_GEN으로 변경 가능
    #     }
    # )
    # 
    # # ... 나머지 엣지들도 생략됨
    
    return workflow