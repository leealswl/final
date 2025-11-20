from typing import TypedDict, Optional, List, Dict, Any

class ProposalGenerationState(TypedDict):
    """기획서 생성 LangGraph에서 사용되는 공유 상태"""
    
    # === 1. 초기 입력 ===
    user_id: str
    project_idx: int
    user_prompt: str 
    
    # === 2. 컨텍스트 데이터 ===
    fetched_context: Dict[str, Any] 
    
    # === 3. 핵심 구조 및 전략 ===
    draft_toc_structure: List[Dict[str, Any]] 
    draft_strategy: str 
    
    # === 4. 생성 및 검토 결과 ===
    generated_text: str 
    current_draft: str
    
    # === 5. 챗봇 주도 정보 수집 플로우 필드 ===
    current_chapter_index: int
    target_chapter: str 
    collected_data: str
    
    current_query: str 
    sufficiency: bool 
    
    # === 6. 그래프 분기 및 제어 ===
    next_step: str 
    attempt_count: int
    
    # === 7. 대화 히스토리 ===
    messages: List[Dict[str, str]]
    
    # === 8. 질문 관리 (상태 지속성을 위해 추가) ===
    pending_questions: List[str]  # 생성된 질문 목록
    answered_questions: List[str]  # 이미 답변받은 질문 목록
    
    # === 9. 가이드 및 도메인 ===
    guide: List[Dict[str, Any]]
    domain: str
    
    # === 10. 목차 진행 상태 추적 (상태 지속성을 위해 추가) ===
    completed_chapters: List[str]  # 완료된 목차 목록