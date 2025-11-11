"""
타입 정의
BatchState 및 관련 타입들
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal
import numpy as np


class BatchState(TypedDict):
    """통합 배치 처리용 State (공고문 + 첨부서류)"""

    # ========== 입력 ==========
    # files: 파일 정보 리스트
    #   - bytes 기반 (권장): [{"bytes": b"...", "filename": "...", "folder": 1}]
    #   - path 기반 (하위 호환): [{"path": "...", "filename": "...", "folder": 1}]
    files: List[Dict[str, Any]]
    user_id: str
    project_idx: int

<<<<<<< HEAD
=======
    # ========== 설정 ==========
    storage_mode: Literal["csv", "oracle", "both"]
    oracle_config: Optional[Dict]

>>>>>>> dev
    # ========== 문서 처리 ==========
    documents: List[Dict[str, Any]]  # 각 파일의 메타데이터 및 추출 결과

    # ========== RAG 통합 저장소 ==========
    all_chunks: List[Dict[str, Any]]  # 모든 문서의 청크 통합
<<<<<<< HEAD
    all_embeddings: Optional[np.ndarray] 
    embedding_model: Any  
=======
    all_embeddings: Optional[np.ndarray]  # 통합 임베딩 (N, 384)
    embedding_model: Any  # SentenceTransformer 모델
>>>>>>> dev

    # ========== VectorDB ==========
    chroma_client: Any  # ChromaDB 클라이언트
    chroma_collection: Any  # ChromaDB 컬렉션
    vector_db_path: str  # VectorDB 저장 경로

    # ========== Feature 추출 결과 ==========
    extracted_features: List[Dict[str, Any]]  # 추출된 모든 Feature

    # ========== 참조 관계 (🔖 MVP2: 분석 대시보드) ==========
<<<<<<< HEAD
    # [2025-01-10 suyeon] cross_references 필드 주석 처리
    # 삭제 이유: match_cross_references() 함수 삭제로 데이터 생성 안됨
    # MVP2 재구현 시 새로운 구조로 추가 예정
    # cross_references: List[Dict[str, Any]]  # 공고 ↔ 첨부 참조 정보 (근거 추적용)
=======
    cross_references: List[Dict[str, Any]]  # 공고 ↔ 첨부 참조 정보 (근거 추적용)
>>>>>>> dev

    # ========== 첨부 템플릿 (✅ MVP1: 사용자 입력 폼) ==========
    attachment_templates: List[Dict[str, Any]]  # 첨부 문서 양식 정보 (폼 생성용)

    # ========== 목차 (✨ NEW: 제안서 목차 구조) ==========
    table_of_contents: Optional[Dict[str, Any]]  # 제안서 목차 구조

    # ========== 출력 ==========
<<<<<<< HEAD
    csv_paths: Optional[Dict[str, str]]  # CSV 저장 경로 (개발/테스트용)
=======
    csv_paths: Optional[Dict[str, str]]
    oracle_ids: Optional[Dict[str, Any]]
>>>>>>> dev
    response_data: Dict[str, Any]  # FastAPI 응답용 데이터

    # ========== 메타 ==========
    status: str
    errors: List[str]
