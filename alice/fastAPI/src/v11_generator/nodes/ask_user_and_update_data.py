# 역할: State의 'current_query'를 사용자에게 제시합니다.
#       사용자 응답을 받아 기존 'collected_data'에 질문과 답변 쌍을 누적 저장합니다.
#       데이터 수집이 완료되었으므로 다음 노드인 'ASSESS_INFO'로 이동하도록 next_step을 설정합니다.
from ..state_types import ProposalGenerationState
from typing import Dict, Any

def ask_user_and_update_data(state: ProposalGenerationState) -> ProposalGenerationState:
    """
    사용자의 응답을 받아 collected_data에 누적하고, LangGraph의 실행을 일시 정지(END)합니다.
    """
    print("--- 노드 실행: ask_user_and_update_data ---")
    
    # State에서 정보 추출
    current_query = state.get("current_query", "이전 질문 없음")
    user_response = state.get("current_response", "사용자 응답 없음")
    existing_data = state.get("collected_data", "")
    
    # 🚨 [수정 1: 데이터 누적]
    # 턴 1 (최초 실행) 시에는 질문만 생성하고 데이터 누적은 건너뜁니다.
    # 턴 2 이상 (사용자가 답변을 보냈을 때)만 데이터를 누적합니다.
    if user_response and user_response not in ["기획서를 작성하고싶어", "미정"]:
        new_entry = f"\n---\n[질문]: {current_query}\n[응답]: {user_response}"
        updated_data = existing_data + new_entry
        
        print(f"✅ 데이터 누적 완료. 새로운 데이터 길이: {len(updated_data)}")
    else:
        # 최초 턴에는 기존 데이터를 유지
        updated_data = existing_data
        # 로드 해줘
        
    # 2. 상태 업데이트 및 제어권 반환
    return {
        "collected_data": updated_data,
        "current_response": None, # 다음 응답을 위해 초기화
        
        # 🔑 [핵심 수정 2: 강제 정지 신호]
        # 이 필드를 'END'로 설정하면 LangGraph는 이 노드를 거친 후 즉시 종료(정지)됩니다.
        "__end__": "END",
        
    }