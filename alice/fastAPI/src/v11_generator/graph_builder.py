# 기획서 생성을 위한 LangGraph의 구조를 정의하고, 노드들을 연결하여 컴파일하는 함수를 정의합니다.

# 파일: v11_generator/graph_builder.py

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END, START
from .state_types import ProposalGenerationState 

# --- A. 노드 함수 임포트 (모두 유지) ---
from .nodes.fetch_context import fetch_context_for_proposal
from .nodes.generate_query import generate_query
from .nodes.ask_user_and_update_data import ask_user_and_update_data 
from .nodes.assess_sufficiency import assess_info
from .nodes.confirm_generation import confirm_generation
from .nodes.generate_draft import generate_proposal_draft
from .nodes.review_and_fix import review_draft, fix_draft_via_llm # review_draft를 라우터로 사용

# 💡 [안정성 상수] 한 챕터당 최대 질문/답변 루프 횟수
MAX_ATTEMPTS = 5

def update_attempt_count(state: ProposalGenerationState) -> Dict[str, Any]:
    """질문 루프가 시작될 때마다 attempt_count를 증가시킵니다."""
    new_count = state.get("attempt_count", 0) + 1
    return {
        "attempt_count": new_count
    }


def router_handle_override(state: ProposalGenerationState) -> str:
    """
    ASK_USER 노드 이후, ask_user_and_update_data.py에서 설정한 강제 오버라이드 플래그를 처리합니다.
    (예: 부적합 답변 시 바로 GENERATE_QUERY로 회귀)
    """
    # [추후연결] ask_user_and_update_data.py에서 설정된 강제 이동 플래그
    override_step = state.get("next_step_override", "ASSESS_INFO") 
    
    # 🔑 플래그를 읽었으니 초기화하여 다음 턴에 영향을 주지 않도록 합니다.
    state["next_step_override"] = "ASSESS_INFO" 
    
    return override_step


def router_next_step(state: ProposalGenerationState) -> str:
    """
    충분성 판단 후, 다음 챕터로 진행할지, 다시 질문할지, 루프를 탈출할지 결정합니다.
    (MAX_ATTEMPTS를 활용하여 무한 루프를 방지합니다.)
    """
    is_sufficient = state.get("sufficiency", False)
    current_idx = state.get("current_chapter_index", 0)
    toc_structure = state.get("draft_toc_structure", [])
    attempt_count = state.get("attempt_count", 0)

    # 🛑 [핵심 안정성]: 무한 루프 방지 (최대 횟수 초과 시 강제 탈출)
    if not is_sufficient and attempt_count >= MAX_ATTEMPTS:
        print(f"🛑 챕터 {current_idx}에 대한 최대 질문 횟수({MAX_ATTEMPTS}회) 초과. 강제 초안 생성으로 이동.")
        return "CONFIRM_GEN" # 강제로 초안 생성 확인 단계로 이동

    # 1. 충분성 판단
    if is_sufficient:
        # 2. 다음 챕터가 남아 있는지 확인
        if current_idx + 1 < len(toc_structure):
            return "UPDATE_CHAPTER" # ✅ 다음 챕터로 목표 업데이트
        else:
            return "CONFIRM_GEN" # ✅ 모든 챕터 완료: 최종 생성 확인으로 이동
    else:
        # ❌ 불충분: 다시 질문 생성 루프 (Attempt Count 증가 필요)
        return "GENERATE_QUERY"


def update_chapter_goal(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    다음 챕터로 목표를 업데이트하고 attempt_count 및 collected_data를 초기화합니다.
    """
    current_idx = state['current_chapter_index']
    toc_structure = state['draft_toc_structure']
    
    next_idx = current_idx + 1
    next_chapter_title = toc_structure[next_idx].get("title", "목차 이름 없음")
    next_chapter_number = toc_structure[next_idx].get("number", str(next_idx + 1))
    
    # 🔑 다음 챕터의 하위 항목 목록 추출 (통일된 'description' 이름 사용)
    next_subchapters_list = []
    for item in toc_structure:
        item_number = item.get('number', '')
        # 다음 챕터 번호로 시작하는 모든 하위 항목을 찾습니다.
        if '.' in item_number and item_number.startswith(next_chapter_number + '.'):
            next_subchapters_list.append({
                "number": item_number,
                "title": item.get('title'),
                "description": item.get('description') 
            })
    
    return {
        "current_chapter_index": next_idx,
        "target_chapter": next_chapter_title,
        "target_subchapters": next_subchapters_list, # 다음 챕터의 요구사항
        "attempt_count": 0, # 🔑 루프 카운터 초기화
        "collected_data": "", # 🔑 새 챕터 데이터 수집을 위해 초기화
        "next_step": "GENERATE_QUERY" 
    }


def router_handle_override(state: ProposalGenerationState) -> str:
    """
    ASK_USER 노드 이후, ask_user_and_update_data.py에서 설정한 강제 오버라이드 플래그를 처리합니다.
    (부적합 답변 시 ASSESS_INFO를 건너뛰고 재질문 루프를 강제합니다.)
    """
    # [추후연결] ask_user_and_update_data.py에서 부적절한 답변(예: "배고파요")을 받았을 때 설정됨.
    override_step = state.get("next_step_override", "ASSESS_INFO") 
    
    # 🔑 [핵심]: 플래그를 읽었으니 초기화하여 다음 턴에 영향을 주지 않도록 즉시 값을 돌려놓습니다.
    state["next_step_override"] = "ASSESS_INFO" 
    
    # 🔑 반환: 만약 부적절했다면 "GENERATE_QUERY"가 반환되어 assess_info를 우회하고 재질문합니다.
    return override_step
    # override step = 부적절한답, ASSESS_INFO = 통과여부 결정자
    # 이 함수는 state에 담긴 부적절한 답을 받았을때 ASSESS_INFO우회하고 재질문루프로 돌아가게함 
    # ASK_USER 노드 이후, ask_user_and_update_data.py에서 설정한 강제 오버라이드 플래그를 처리합니다.
    # 즉 부적합 답변 시 ASSESS_INFO를 건너뛰고 재질문 루프를 강제함


def update_attempt_count(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    질문 루프가 시작될 때마다 attempt_count를 증가시킵니다.
    """
    # 🔑 역할: GENERATE_QUERY 노드 직전에 실행되어, 현재 챕터에 대한 시도 횟수를 new_count에 기록합니다.
    new_count = state.get("attempt_count", 0) + 1
    return {
        "attempt_count": new_count
    }
    # 카운트를 세기 위한 함수

    # 💡 [안정성 상수] 한 챕터당 최대 질문/답변 루프 횟수
MAX_ATTEMPTS = 5 # 🔑 무한 루프 방지: 한 챕터에 대해 최대 5번의 질문/답변만 허용합니다.

def router_next_step(state: ProposalGenerationState) -> str:
    """
    충분성 판단(assess_info) 후, 다음 챕터로 진행할지, 다시 질문할지, 루프를 탈출할지 결정합니다.
    (MAX_ATTEMPTS를 활용하여 무한 루프를 방지하는 최종 결정권자입니다.)
    """
    is_sufficient = state.get("sufficiency", False)
    current_idx = state.get("current_chapter_index", 0)
    toc_structure = state.get("draft_toc_structure", [])
    attempt_count = state.get("attempt_count", 0)

    # 🛑 [핵심 안정성]: 무한 루프 방지 - 5회 질문 후에도 불충분하면 강제 탈출!
    if not is_sufficient and attempt_count >= MAX_ATTEMPTS:
        print(f"🛑 챕터 {current_idx}에 대한 최대 질문 횟수({MAX_ATTEMPTS}회) 초과. 강제 초안 생성으로 이동.")
        # 🔑 LLM이 완벽한 답변을 얻지 못했더라도, 더 이상 시간을 낭비하지 않고 현재 데이터로 초안을 만들도록 강제함.
        return "CONFIRM_GEN" 

    # 1. 충분성 판단
    if is_sufficient:
        # 2. 다음 챕터가 남아 있는지 확인
        if current_idx + 1 < len(toc_structure):
            # 🔑 다음 챕터가 남아있음: 목표 업데이트로 이동
            return "UPDATE_CHAPTER" 
        else:
            # 🔑 모든 챕터 완료: 최종 초안 생성 확인 단계로 이동
            return "CONFIRM_GEN" 
    else:
        # ❌ 불충분: 다시 질문 생성 루프로 회귀 (Attempt Count는 UPDATE_ATTEMPT에서 증가함)
        return "GENERATE_QUERY"
    #무한루프 방지를 위한 함수

def update_chapter_goal(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    챕터가 완료되었을 때 다음 챕터로 목표를 업데이트하고 모든 카운터를 초기화합니다.
    """
    # 🔑 입력 변수 추출 (현재 상태를 기반으로 다음 상태를 계산)
    # 이 두 값은 이전 노드(fetch_context.py)에서 State에 저장된 값을 읽어와 
    # 현재 챕터의 완료 상태를 확인하고 다음 챕터의 목표를 계산하는 데 사용됩니다.
    current_idx = state['current_chapter_index'] # 현재 완료된 챕터의 인덱스 (예: 0) 
    toc_structure = state['draft_toc_structure'] # 전체 목차 구조 (result.json에서 로드됨)

    next_idx = current_idx + 1
    next_chapter_title = toc_structure[next_idx].get("title", "목차 이름 없음")
    next_chapter_number = toc_structure[next_idx].get("number", str(next_idx + 1))
    
    # 🔑 다음 챕터의 하위 항목 목록 추출 (통일된 'description' 이름 사용)
    # result.json에서 다음 챕터의 모든 sub-section 요구사항을 추출합니다.
    next_subchapters_list = []
    for item in toc_structure:
        item_number = item.get('number', '')
        # 다음 챕터 번호로 시작하는 모든 하위 항목(예: "2.1", "2.2")을 찾습니다.
        if '.' in item_number and item_number.startswith(next_chapter_number + '.'):
            next_subchapters_list.append({
                "number": item_number,
                "title": item.get('title'),
                "description": item.get('description') # 🔑 description (작성 요구사항)을 그대로 사용
            })
    
    return {
        "current_chapter_index": next_idx,
        "target_chapter": next_chapter_title,
        "target_subchapters": next_subchapters_list, # 다음 챕터의 요구사항을 새 목표로 설정
        "attempt_count": 0, # 🔑 루프 카운터 초기화 (새 챕터는 0부터 시작)
        "collected_data": "", # 🔑 이전 챕터의 데이터는 이미 저장되었으므로, 새 챕터 데이터 수집을 위해 초기화
        "next_step": "GENERATE_QUERY" 
    }
