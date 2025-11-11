"""
v6_rag 패키지 (프로덕션)
공고 및 첨부서류 분석을 위한 LangGraph 기반 시스템

✅ MVP1: 사용자 입력 폼 자동 생성
🔖 MVP2: 분석 대시보드 (근거 추적)
"""

from .graph import create_batch_graph
from .state_types import BatchState

__version__ = "1.0.0"
__all__ = ['create_batch_graph', 'BatchState']
