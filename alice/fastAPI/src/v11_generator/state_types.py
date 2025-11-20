from typing import TypedDict, Optional, List, Dict, Any

class ProposalGenerationState(TypedDict):
    """기획서 생성 LangGraph에서 사용되는 공유 상태"""
    
    # === 1. 초기 입력 ===
    user_id: str
    project_idx: int
    user_prompt: str 
    
    # === 2. 컨텍스트 데이터 ===
    fetched_context: Dict[str, Any] 
    
    # 📚 3. 핵심 구조 및 전략
    draft_toc_structure: List[Dict[str, Any]] 
    draft_strategy: str 
    
    # === 4. 생성 및 검토 결과 ===
    generated_text: str 
    current_draft: str 
    
    # === 5. 챗봇 주도 정보 수집 플로우 필드 ===
    current_chapter_index: int 
    target_chapter: str 
    
    # 🚨 [핵심 추가] 이전 챕터 데이터 백업용 필드
    accumulated_data: str 
    
    # 현재 챕터 수집 데이터(어떤챕터 작업할건지)
    collected_data: str 
    
    # 답변 충족도 점수( 0~100점), 채점기준 피드백
    completeness_score: int
    grading_reason: str      

    # 하위 목차 관리 (Assess/Query 노드용)
    target_subchapters: List[Dict[str, Any]]
    missing_subsections: List[str]
    major_chapter_titles: List[str] # fetch_context에서 생성됨
    
    current_query: str 
    current_response: str # 사용자 답변
    sufficiency: bool 
    
    # === 6. 그래프 분기 및 제어 ===
    next_step: str 
    attempt_count: int
    
    # 부적절 답변 처리용 오버라이드 플래그
    next_step_override: str 
    
    # === 7. 기타 ===
    messages: List[Dict[str, str]]
