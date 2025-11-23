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
    target_chapter: str # 타겟 목차
    
    # 작성완료된 타겟 목차들
    accumulated_data: List[str] 
    
    # 현재 챕터 수집 데이터(어떤챕터 작업할건지)
    collected_data: str 
    
    # 현재 작업 중인 섹션의 인덱스. toc_structure 내 위치 추적.
    current_chapter_index: int 
    
    # 현재 작업 중인 섹션의 제목.
    target_chapter: str 
    
    # [핵심 필드] 완료된 섹션의 '요약된 최종 내용' 리스트. (List[str] 타입으로 변경됨)
    accumulated_data: List[str] 
    
    # [핵심 필드] 현재 작업 중인 섹션의 '가공되지 않은 원본 입력' 임시 저장소. (Assess/Save 노드의 입력)
    collected_data: str 
    
    # [핵심 필드] 현재 섹션의 최종 평가 점수 (70점 이상이면 합격).
    completeness_score: int

    # [핵심 필드] LLM이 계산한 평가 사유 (프론트 출력용).
    grading_reason: str

    # 🔑 추가: 상세 평가 항목별 점수 저장 (예: {"RATER_1": 90, "RATER_2": 70})
    assessment_breakdown: Dict[str, int] 

    # 하위 챕터별 누적 점수 기록 (점수 하락 방지용 및 진행 여부 판단 기준).
    section_scores: Dict[str, int] # 예: {"1.1": 85, "1.2": 40}
    
    # 🔑 추가: 이전 섹션 완료 여부를 저장하는 플래그
    section_just_completed: Optional[str] # 포맷: "1.1 사업 배경 및 필요성"
    
    # 🔑 추가: '완료된 목차에 대한 질문' 플래그
    target_already_completed: Optional[str] # 포맷: "1.1 사업 배경 및 필요성"

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
