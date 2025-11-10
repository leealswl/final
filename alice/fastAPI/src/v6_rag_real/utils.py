"""
유틸리티 함수들
"""

import re
from typing import Optional, List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter


# ========================================
# 🔖 MVP2: 분석 대시보드 (근거 추적)
# ========================================
# 목적: 공고문에서 "붙임 1 참조" 등의 언급이 있을 때,
#       해당 첨부 문서를 자동으로 연결하여 분석 대시보드에서
#       근거로 표시하기 위한 첨부번호 추출
# ========================================

def extract_attachment_number(filename: str) -> Optional[int]:
    """
    [MVP2] 파일명에서 첨부번호 추출 (분석 대시보드 근거 추적용)

    Args:
        filename: 파일명

    Returns:
        첨부번호 (예: "붙임1" → 1) 또는 None

    Examples:
        >>> extract_attachment_number("붙임1_연구계획서.hwp")
        1
        >>> extract_attachment_number("별첨2_동의서.pdf")
        2
        >>> extract_attachment_number("공고문.pdf")
        None
    """
    patterns = [
        r'붙임\s*(\d+)',
        r'별첨\s*(\d+)',
        r'첨부\s*(\d+)',
        r'attachment\s*(\d+)',
        r'부록\s*(\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def detect_section_headers(text: str) -> List[Dict[str, Any]]:
    """
    텍스트에서 섹션 헤더 감지

    Args:
        text: 분석할 텍스트

    Returns:
        섹션 헤더 목록 [{"level": 1, "title": "...", "position": ...}]
    """
    headers = []
    lines = text.split('\n')

    # [2025-01-10 suyeon] 패턴 확장 + 우선순위 최적화
    # 변경 이유:
    # 1. 패턴 우선순위 명확화: 구체적 패턴(대괄호, 로마숫자) → 일반적 패턴(숫자)
    # 2. 로마숫자 패턴 강화: 잘못된 조합 방지 (IIIII → 최대 4글자 제한)
    # 3. 한글 범위 명시: 가~하로 제한 (정부 공고문 표준)
    # 근거: 실제 공고문 분석 결과 다양한 번호 매김 방식 사용 확인
    patterns = [
        # 레벨 1: 대제목 (구체적 패턴 우선)
        (r'^【([^】]+)】\s*(.+)$', 1),                      # 【공고】 제목
        (r'^\[([^\]]+)\]\s*(.+)$', 1),                     # [별첨] 제목
        (r'^([IVX]{1,4})\.\s+(.+)$', 1),                   # I. ~ XIV. (영문 로마숫자, 최대 14)
        (r'^([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ])\.\s+(.+)$', 1),              # Ⅰ. ~ Ⅹ. (한글 로마숫자, 최대 10)
        (r'^([0-9]{1,2})\.\s+(.+)$', 1),                   # 1. ~ 99. 제목

        # 레벨 2: 중제목
        (r'^([가-하])\.\s+(.+)$', 2),                      # 가. ~ 하. (8개 제한)
        (r'^([가-하])\)\s+(.+)$', 2),                      # 가) ~ 하)
        (r'^([0-9]{1,2})\)\s+(.+)$', 2),                   # 1) ~ 99)
        (r'^[■●○]\s+(.+)$', 2),                            # 불릿 포인트

        # 레벨 3: 소제목
        (r'^\(([0-9]{1,2})\)\s+(.+)$', 3),                 # (1) ~ (99)
        (r'^\(([가-하])\)\s+(.+)$', 3),                    # (가) ~ (하)
        (r'^[▪▫]\s+(.+)$', 3),                             # 작은 불릿
    ]

    # [2025-01-10 suyeon] 최소 제목 길이 상수 추가
    # 이유: "1. " (제목 없음) 같은 빈 헤더 방지
    MIN_TITLE_LENGTH = 2

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        for pattern, level in patterns:
            match = re.match(pattern, line)
            if match:
                # [2025-01-10 suyeon] 제목 추출 로직 개선
                # 이유: 불릿 포인트(■●○) 패턴은 그룹이 1개만 있어서 group(2) 호출 시 에러 발생
                # 해결: 매칭 그룹 수에 따라 제목 추출 방식 분기
                if len(match.groups()) == 2:
                    title = match.group(2).strip()
                else:
                    title = match.group(1).strip()

                # [2025-01-10 suyeon] 빈 제목 검증 추가
                # 이유: "1. " (제목 없음) 같은 경우 섹션 헤더로 인식하면 안됨
                # 근거: 최소 2글자 이상의 의미있는 제목만 섹션으로 간주
                if len(title) < MIN_TITLE_LENGTH:
                    continue

                headers.append({
                    'level': level,
                    'title': title,
                    'position': i,
                    'raw': line
                })
                break

    return headers


def chunk_by_sections(text: str, page_num: int, max_chunk_size: int = 1000, overlap_size: int = 200) -> List[Dict[str, Any]]:
    """
    [2025-01-10 suyeon] Recursive 청킹 + 섹션 감지 하이브리드

    변경 이유:
    - 기존 180줄 수동 청킹 로직이 과도하게 복잡하고 버그 리스크 높음
    - LangChain RecursiveCharacterTextSplitter는 검증된 라이브러리로 안정적
    - 섹션 감지 기능은 유지하여 출처 추적 가능

    장점:
    - 코드 복잡도 대폭 감소 (180줄 → 60줄)
    - 유지보수 용이
    - 날짜/약어 오분리 문제를 separator 우선순위로 자연스럽게 해결

    Args:
        text: 청킹할 텍스트
        page_num: 페이지 번호
        max_chunk_size: 최대 청크 크기 (문자 수)
        overlap_size: 오버랩 크기 (문자 수, 문맥 보존용)

    Returns:
        청크 리스트 [{"text": "...", "section": "...", "page": ..., "is_sectioned": bool}]
    """
    # Recursive Splitter 초기화
    # separator 우선순위: 단락 > 줄바꿈 > 문장 > 단어
    # → 날짜(2024.12.31), 약어(Ph.D.)는 자연스럽게 보존됨
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chunk_size,
        chunk_overlap=overlap_size,
        separators=[
            "\n\n",    # 단락 (가장 안전)
            "\n",      # 줄바꿈
            ". ",      # 문장 끝
            "? ",
            "! ",
            " ",       # 단어
            ""         # 최후의 수단
        ],
        length_function=len,
    )

    # 섹션 헤더 감지
    headers = detect_section_headers(text)
    chunks = []

    if not headers:
        # 섹션이 없으면 Recursive로 청킹
        text_chunks = splitter.split_text(text)
        for idx, chunk_text in enumerate(text_chunks):
            chunks.append({
                'text': chunk_text,
                'section': f'페이지 {page_num}',
                'page': page_num,
                'is_sectioned': False
            })
    else:
        # 섹션별로 Recursive 청킹 적용
        lines = text.split('\n')

        for i, header in enumerate(headers):
            section_title = header['title']
            start_pos = header['position']
            end_pos = headers[i + 1]['position'] if i + 1 < len(headers) else len(lines)

            # [2025-01-10 suyeon] 헤더 제외 로직 추가
            # 변경 이유:
            # 1. 정보 중복 방지: 헤더는 section_label에 이미 저장되므로 텍스트에서 제외
            # 2. 임베딩 품질 향상: 순수 내용만 임베딩하여 RAG 검색 정확도 향상
            # 3. 토큰 효율: OpenAI API 비용 절감 (중복 텍스트 제거)
            # 근거: 헤더는 메타데이터로만 관리하고, 청크 텍스트는 순수 내용만 포함

            # 섹션 내용 추출 (헤더 다음 줄부터 시작)
            section_lines = lines[start_pos + 1:end_pos]
            section_text = '\n'.join(section_lines).strip()

            if not section_text:
                continue

            # 섹션을 Recursive로 청킹
            section_chunks = splitter.split_text(section_text)

            for idx, chunk_text in enumerate(section_chunks):
                # 섹션이 분할된 경우 part 번호 추가
                if len(section_chunks) > 1:
                    section_label = f'{section_title} (part {idx+1})'
                else:
                    section_label = section_title

                chunks.append({
                    'text': chunk_text,
                    'section': section_label,
                    'page': page_num,
                    'is_sectioned': True
                })

    # 빈 청크 제거 + 최소 길이 체크
    MIN_CHUNK_LENGTH = 50
    chunks = [c for c in chunks if len(c['text'].strip()) >= MIN_CHUNK_LENGTH]

    return chunks
