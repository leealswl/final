# LangGraph 상태를 기반으로 RAG를 수행하여 기획서 작성에 필요한 
# 핵심 컨텍스트를 가져오는 노드 함수를 정의합니다.
# fetch_context_for_proposal 함수 전체 (수정)
from ..state_types import ProposalGenerationState 
from typing import Dict, Any, List 
import logging 

def fetch_context_for_proposal(state: ProposalGenerationState) -> ProposalGenerationState:
    logging.info(f"⚙️ fetch_context 노드 실행: project_idx={state['project_idx']}")
    print("fetch_context_for_proposal 실행")
    context_data = state.get("fetched_context", {})
    
    result_toc = context_data.get('result_toc', {})
    raw_sections: List[Dict[str, Any]] = result_toc.get("sections", [])

    # print('raw_sections: ', raw_sections)
    
    # 🔑 핵심 수정: 소수점(.)이 있는 하위 섹션만 필터링하여 toc_structure에 담습니다.
    # toc_structure = []
    # for item in raw_sections:
    #     num = item.get("number", "")
    #     if '.' in num:
    #         toc_structure.append(item)
    
    anal_guide = context_data.get('anal_guide', {})
    generation_strategy = anal_guide.get("generation_strategy", "공고문 분석 전략이 없으므로, 목차를 작성하는 데 필요한 일반적인 정보를 수집합니다.")

    # print('generation_strategy: ', generation_strategy)
    
    # # 3. --- 루프 초기 목표 및 인덱스 설정 (필터링된 리스트의 0번 인덱스부터 시작) ---
    # initial_chapter_index = 0
    # initial_target_chapter = ""
    
    # if toc_structure:
    #     current_item = toc_structure[initial_chapter_index]
    #     initial_target_chapter = current_item.get("title", "목표 제목 없음")
    # else:
    #     return {"next_step": "FINISH", "current_draft": "유효한 하위 목차 구조를 찾을 수 없어 기획서 생성을 시작할 수 없습니다."}

    return {
        "draft_toc_structure": raw_sections,
        "draft_strategy": generation_strategy,
        
        # "current_chapter_index": initial_chapter_index,
        # "target_chapter": initial_target_chapter, # ⬅️ 첫 목표 제목 설정
        
        # "collected_data": "", 
        "sufficiency": False, 
        "attempt_count": 0,
        "section_scores": {}, 
        # "next_step": "GENERATE_QUERY" 
    }