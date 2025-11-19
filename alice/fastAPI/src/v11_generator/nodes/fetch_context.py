# LangGraph 상태를 기반으로 RAG를 수행하여 기획서 작성에 필요한 핵심 컨텍스트를 가져오는 노드 함수를 정의합니다.

# 파일: v11_generator.py (또는 노드 구현 파일)

# 파일: v11_generator.py (또는 노드 구현 파일)

from ..state_types import ProposalGenerationState 
from typing import Dict, Any
import logging # logging import 추가

# 노드 함수의 반환 타입은 State의 부분 집합 (Dict[str, Any])이어야 합니다.
def fetch_context_for_proposal(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    FastAPI에서 주입된 anal.json과 result.json 컨텍스트를 LangGraph 상태에 맞게 분리/정리하고
    정보 수집 루프의 초기 목표를 설정합니다. (하위 목차 추출 로직 추가됨)
    """
    logging.info(f"⚙️ fetch_context 노드 실행: project_idx={state['project_idx']}")

    print("fetch_context_for_proposal 실행")
    
    context_data = state.get("fetched_context", {})
    

    # 1. --- result.json (목차 구조) 추출 및 정리 ---
    result_toc = context_data.get('result_toc', {})

    toc_structure = result_toc.get("sections", [])
    
    # 2. --- anal.json (분석 전략) 추출 및 정리 ---
    # anal_guide = context_data.get('anal_guide', {})
    # generation_strategy = anal_guide.get(
    #     "generation_strategy", 
    #     "공고문 분석 전략이 없으므로, 목차를 작성하는 데 필요한 일반적인 정보를 수집합니다."
    # )
    
    # 3. --- 루프 초기 목표 및 하위 항목 목록 설정 (수정된 부분) ---
    initial_chapter_index = 0
    
    if toc_structure and initial_chapter_index < len(toc_structure):
        current_chapter_data = toc_structure[initial_chapter_index]
        initial_target_chapter = current_chapter_data.get("title", "목차 제목 없음")
        
        # 🔑 하위 항목 리스트 추출
        # 'subsections' 키에 하위 항목 리스트가 있다고 가정하며, 각 항목에서 'title'을 추출합니다.
        # subchapters_raw = current_chapter_data.get("subsections", [])
        subchapters_raw = current_chapter_data.get("title", [])
        # initial_subchapters_list = [
        #     sub.get("title") for sub in subchapters_raw if sub.get("title")
        # ]
    else:
        # 목차가 비어있다면 바로 종료로 분기
        return {"next_step": "FINISH", "current_draft": "목차 구조 파일을 찾을 수 없어 기획서 생성을 시작할 수 없습니다."}


    # 4. --- 상태 업데이트 및 반환 ---
    return {
        # 📚 정리된 데이터
        "draft_toc_structure": toc_structure,
        # "draft_strategy": generation_strategy,
        
        # 🔑 루프 초기화
        "current_chapter_index": initial_chapter_index,
        "target_chapter": initial_target_chapter,
        # ✨ 신규 필드 추가: 하위 목차 리스트 (generate_query에서 사용)
        # "target_subchapters": initial_subchapters_list, 
        
        "collected_data": "", 
        "sufficiency": False, 
        "attempt_count": 0,
        
        # ➡️ 다음 노드 결정: 질문 생성으로 루프 시작
        "next_step": "GENERATE_QUERY" 
    }