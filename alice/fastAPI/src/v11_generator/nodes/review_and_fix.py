# 생성된 초안의 품질을 검토하여 다음 단계(FINISH 또는 REVISE)를 결정하고, 수정이 필요할 경우 수정 작업을 수행하는 노드 함수를 정의합니다.

from ..state_types import ProposalGenerationState # 클래스명 변경 적용
import logging
from typing import Literal

def review_draft(state: ProposalGenerationState) -> ProposalGenerationState:
    """
    초안을 검토하고 다음 단계를 결정합니다. (LangGraph 조건부 엣지용)
    """
    # ... (로직 및 로그 메시지 내의 상태명 변경 적용) ...
    print("노드 실행: review_draft")
    
    return {"next_step": "FINISH" }


def fix_draft_via_llm(state: ProposalGenerationState) -> ProposalGenerationState:
    """
    수정 지시를 LLM에게 전달하여 초안을 수정합니다.
    """
    # ... (로직 및 로그 메시지 내의 상태명 변경 적용) ...
    
    return new_state