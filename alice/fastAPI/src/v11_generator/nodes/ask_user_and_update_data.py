from ..state_types import ProposalGenerationState
from typing import Dict, Any

def ask_user_and_update_data(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    [서기 노드]
    사용자의 최신 발언(user_prompt)을 확인하고,
    기존 대화록(collected_data) 뒤에 이어 붙여서 저장합니다.
    """
    print("--- 노드 실행: 데이터 저장 (ask_user_and_update_data) ---")
    
    # 1. [핵심 수정] FastAPI가 보낸 'user_prompt'를 가져와야 합니다!
    # (이전에는 current_response를 찾아서 저장이 안 됐던 것임)
    user_input = state.get("user_prompt", "").strip()
    
    # 기존 데이터 가져오기
    existing_data = state.get("collected_data", "")
    
    # 2. 데이터 업데이트 로직
    updated_data = existing_data
    
    print(f"DEBUG: 📝 기존 데이터 길이 (DB 로드): {len(existing_data)}자")
    print(f"DEBUG: 📩 새 사용자 입력 길이: {len(user_input)}자")

    new_entry = f"\n[사용자]: {user_input}"
    updated_data = existing_data + new_entry

    # 3. 결과 반환
    return {
        "collected_data": updated_data,
        # 다음 단계를 위해 user_prompt는 유지하거나 비울 수 있음 (여기선 유지)
    }