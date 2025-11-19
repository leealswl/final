#LangGraph를 사용하는 기획서 생성 에이전트의 데이터 구조(공유 상태)를 정의
#변수값 구축이나 데이터 허브 구축 분기결정하는 라우터랑은 다름 워크플로우 구현위해 존재
from typing import TypedDict, Optional, List, Dict, Any

class ProposalGenerationState(TypedDict):
    """기획서 생성 LangGraph에서 사용되는 공유 상태 (수정 및 보완)"""
    
    # === 1. 초기 입력 (라우터에서 주입) ===
    user_id: str
    project_idx: int
    user_prompt: str 
    
    # === 2. 컨텍스트 데이터 (확정된 파일 반영) ===
    # 🔑 FastAPI에서 로드된 'anal.json' 및 'result.json' 원본 데이터를 담는 컨테이너
    fetched_context: Dict[str, Any] 
    
    # 📚 3. 핵심 구조 및 전략 (FETCH_CONTEXT 노드에서 정리/추출)
    # result.json에서 추출된, 루프의 목표가 되는 목차 구조
    draft_toc_structure: List[Dict[str, Any]] 
    # anal.json에서 추출된, 질문 생성 및 충분성 판단의 기준
    draft_strategy: str 
    
    # === 4. 생성 및 검토 결과 ===
    generated_text: str 
    current_draft: str # (선택적: generated_text와 통합 가능하나, 명확성을 위해 분리 유지)
    
    # === 5. 챗봇 주도 정보 수집 플로우 필드 ===
    current_chapter_index: int # 현재 작성 중인 목차의 인덱스 (루프 진행 상태 추적)
    target_chapter: str 
    collected_data: str # 사용자 응답 누적
    
    current_query: str 
    # sufficiency는 불리언(True/False) 타입으로 명확히 지정
    sufficiency: bool 
    
    # === 6. 그래프 분기 및 제어 ===
    next_step: str 
    attempt_count: int
    
    # === 7. 기타 루프 제어 (옵션) ===
    messages: List[Dict[str, str]] # (선택적) 챗봇과 사용자 간의 대화 히스토리 저장