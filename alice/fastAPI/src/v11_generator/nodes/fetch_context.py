from ..state_types import ProposalGenerationState 
from typing import Dict, Any, List # List 임포트 추가
import logging 

# 노드 함수의 반환 타입은 State의 부분 집합 (Dict[str, Any])이어야 합니다.
def fetch_context_for_proposal(state: ProposalGenerationState) -> Dict[str, Any]:
    """
    FastAPI에서 주입된 anal.json과 result.json 컨텍스트를 LangGraph 상태에 맞게 분리/정리하고
    정보 수집 루프의 초기 목표를 설정합니다. (하위 목차 추출 로직 추가됨)
    """
    logging.info(f"⚙️ fetch_context 노드 실행: project_idx={state['project_idx']}")

    print("fetch_context_for_proposal 실행")
    
    context_data = state.get("fetched_context", {})

    print(f"DEBUG: fetched_context 키 확인: {list(context_data.keys())}")
    
    history = state.get("messages", [])

    #새 사용자 메시지 추가
    if state.get("user_prompt"):
        user_msg = {"role": "user", "content": state["user_prompt"]}
        history.append(user_msg)

    # 1. --- result.json (목차 구조) 추출 및 정리 ---
    result_toc = context_data.get('result_toc', {})

    toc_structure = result_toc.get("sections", [])
    
    print(f"DEBUG: toc_structure 길이 확인: {len(toc_structure)}")

    # 2. --- anal.json (분석 전략) 추출 및 정리 ---
    anal_guide = context_data.get('anal_guide', {})
    generation_strategy = anal_guide.get(
        "generation_strategy", 
        "공고문 분석 전략이 없으므로, 목차를 작성하는 데 필요한 일반적인 정보를 수집합니다."
    )
    
    # 3. --- 루프 초기 목표 및 하위 항목 목록 설정 ---
    initial_chapter_index = 0
    
    # 🔑 필수 필드 초기화 (State에 주입될 값)
    target_subchapters = []
    missing_subsections = []
    major_chapter_titles = [] 
    initial_target_chapter = ""
    
    if toc_structure and initial_chapter_index < len(toc_structure):
        current_chapter_data = toc_structure[initial_chapter_index]
        initial_target_chapter = current_chapter_data.get("title", "목차 제목 없음")
        initial_chapter_number = current_chapter_data.get("number", "") # 🔑 현재 챕터 번호 (예: "1")
        
        # 🔑 하위 항목 리스트 추출 (기존 코드 주석 처리/교체)
        # 'subsections' 키에 하위 항목 리스트가 있다고 가정하며, 각 항목에서 'title'을 추출합니다.
        # subchapters_raw = current_chapter_data.get("subsections", [])
        # subchapters_raw = current_chapter_data.get("title", [])

        # ✅ [핵심 교체]: 플랫 리스트에서 번호를 기준으로 하위 목차 필터링
        subsections_raw = [
            item for item in toc_structure 
            if item.get("number", "").startswith(f"{initial_chapter_number}.")
        ]

        # ✅ [필수 계산]: target_subchapters 및 missing_subsections 계산
        # description을 리스트 형태로 넣어 generate_query의 criteria_list[0] 접근을 맞춥니다.
        target_subchapters = [
            {"title": sub.get("title"), "description": [sub.get("description")], "number": sub.get("number")} 
            for sub in subsections_raw if sub.get("title")
        ]
        
        # missing_subsections 초기화
        missing_subsections = [sub['title'] for sub in target_subchapters] 
        
        # major_chapter_titles 계산 (Level 1 제목 리스트)
        major_chapter_titles = [
            c.get("title") for c in toc_structure if len(c.get("number", "")) == 1
        ]
        
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
        
        # ✅ [필수 추가]: generate_query 및 assess_info가 사용할 핵심 필드 주입
        # ✨ 신규 필드 추가: 하위 목차 리스트 (generate_query에서 사용)
        "major_chapter_titles": major_chapter_titles, 
        "target_subchapters": target_subchapters,     
        "missing_subsections": missing_subsections,   
        
        # 5. --- 기타 필드 초기화 ---
        "collected_data": "", 
        "sufficiency": False, 
        "attempt_count": 0,
        
        # ➡️ 다음 노드 결정: 질문 생성으로 루프 시작
        "next_step": "GENERATE_QUERY",

        "messages": history
    }