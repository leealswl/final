# 역할: 정보가 충분하다고 판단되었을 때, 사용자에게 '초안 생성 여부(Y/N)'를 질문하고,
#       응답에 따라 다음 노드('GENERATE_DRAFT' 또는 'GENERATE_QUERY')로 분기할
#       'next_step' 플래그를 State에 설정합니다.

from typing import Dict, Any

# ----------------------------------------------------
# 노드 함수 정의
# ----------------------------------------------------
def confirm_generation(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    정보 충분성 확인 후, 사용자에게 생성 여부를 묻고 다음 단계(생성 또는 추가 질문)를 결정합니다.
    """
    print("--- 노드 실행: confirm_generation ---")
    
    target_chapter = state.get("target_chapter", "미정 목차")
    
    # 1. 사용자에게 질문 제시 (I/O 로직)
    confirmation_query = (
        f"현재까지 입력해주신 정보로 '[{target_chapter}]' 초안 작성이 충분하다고 판단됩니다. "
        "이 정보들을 바탕으로 초안을 **생성**하시겠습니까? (Y/N)"
    )
    
    print(f"사용자에게 제시될 질문: {confirmation_query}")
    
    # *************************************************************
    # ⚠️ 중요: 이 부분은 실제 백엔드 I/O 로직이 들어갈 자리입니다.
    #   사용자의 응답(Y/N)이 State의 임시 필드(예: 'confirmation_response')에 담겨 들어왔다고 가정합니다.
    # *************************************************************
    
    # --- Mock 데이터 설정 (실제 사용자 응답을 시뮬레이션) ---
    # 실제 환경에서는 이 값이 'Y' 또는 'N'으로 사용자로부터 입력받아야 합니다.
    user_response = state.get("confirmation_response_input", "Y").strip().upper() 
    
    # 2. 응답에 따른 next_step 결정
    if user_response == "Y":
        # Y를 선택하면 -> 최종 초안 생성 노드로 이동
        next_action = "GENERATE_DRAFT"
        print("사용자: Y. 다음 단계: 초안 생성 (GENERATE_DRAFT)")
    else:
        # N 또는 다른 입력을 선택하면 -> 추가 정보 수집을 위해 질문 생성 노드로 회귀
        next_action = "GENERATE_QUERY"
        print("사용자: N. 다음 단계: 추가 질문 생성 (GENERATE_QUERY)")

    # 3. State 업데이트
    return {
        "next_step": next_action
    }