"""
유틸리티 함수들
"""

import re
from typing import Optional, List, Dict, Any


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

    # 패턴: "1. ", "가. ", "1) ", "(1) " 등
    patterns = [
        (r'^([0-9]+)\.\s+(.+)$', 1),           # 1. 제목
        (r'^([가-힣])\.\s+(.+)$', 2),          # 가. 제목
        (r'^([0-9]+)\)\s+(.+)$', 2),           # 1) 제목
        (r'^\(([0-9]+)\)\s+(.+)$', 3),         # (1) 제목
    ]

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        for pattern, level in patterns:
            match = re.match(pattern, line)
            if match:
                headers.append({
                    'level': level,
                    'title': match.group(2).strip(),
                    'position': i,
                    'raw': line
                })
                break

    return headers


def chunk_by_sections(text: str, page_num: int, max_chunk_size: int = 1000, overlap_size: int = 200) -> List[Dict[str, Any]]:
    """
    텍스트를 섹션 기반으로 청킹 (오버랩 포함)

    Args:
        text: 청킹할 텍스트
        page_num: 페이지 번호
        max_chunk_size: 최대 청크 크기 (문자 수)
        overlap_size: 오버랩 크기 (문자 수, 문맥 보존용)

    Returns:
        청크 리스트 [{"text": "...", "section": "...", "page": ..., "is_sectioned": bool}]
    """
    # 섹션 헤더 감지
    headers = detect_section_headers(text)

    chunks = []

    if not headers:
        # 섹션이 없으면 문장 단위로 청킹 (오버랩 포함)
        # 문장 분리 (., !, ? 기준)
        sentences = re.split(r'([.!?]\s+)', text)
        # 구분자를 문장에 다시 붙임
        full_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                full_sentences.append(sentences[i] + sentences[i + 1])
            else:
                full_sentences.append(sentences[i])
        if len(sentences) % 2 == 1:
            full_sentences.append(sentences[-1])

        current_chunk = []
        current_length = 0
        previous_overlap = ""

        for sentence in full_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            if current_length + sentence_length > max_chunk_size and current_chunk:
                # 현재 청크 저장
                chunk_text = ' '.join(current_chunk).strip()
                if chunk_text:
                    chunks.append({
                        'text': chunk_text,
                        'section': f'페이지 {page_num}',
                        'page': page_num,
                        'is_sectioned': False
                    })

                    # 오버랩 준비: 마지막 몇 문장 저장
                    overlap_text = chunk_text[-overlap_size:] if len(chunk_text) > overlap_size else chunk_text
                    # 문장 경계에서 자르기
                    overlap_start = overlap_text.rfind('. ')
                    if overlap_start > 0:
                        previous_overlap = overlap_text[overlap_start + 2:]
                    else:
                        previous_overlap = overlap_text

                # 새 청크 시작 (오버랩 포함)
                if previous_overlap and previous_overlap not in sentence:
                    current_chunk = [previous_overlap, sentence]
                    current_length = len(previous_overlap) + sentence_length
                else:
                    current_chunk = [sentence]
                    current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # 마지막 청크
        if current_chunk:
            chunk_text = ' '.join(current_chunk).strip()
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'section': f'페이지 {page_num}',
                    'page': page_num,
                    'is_sectioned': False
                })

    else:
        # 섹션 기반 청킹
        lines = text.split('\n')

        # 각 섹션별로 청크 생성
        for i, header in enumerate(headers):
            section_title = header['title']
            start_pos = header['position']
            end_pos = headers[i + 1]['position'] if i + 1 < len(headers) else len(lines)

            # 섹션 내용 추출
            section_lines = lines[start_pos:end_pos]
            section_text = '\n'.join(section_lines).strip()

            # 섹션이 너무 크면 분할 (오버랩 포함)
            if len(section_text) > max_chunk_size:
                # 큰 섹션을 문장 단위로 분할 (오버랩 포함)
                sentences = re.split(r'([.!?]\s+)', section_text)
                full_sentences = []
                for j in range(0, len(sentences) - 1, 2):
                    if j + 1 < len(sentences):
                        full_sentences.append(sentences[j] + sentences[j + 1])
                    else:
                        full_sentences.append(sentences[j])
                if len(sentences) % 2 == 1:
                    full_sentences.append(sentences[-1])

                sub_chunks = []
                current_sub = []
                current_length = 0
                previous_overlap = ""

                for sentence in full_sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue

                    sentence_length = len(sentence)

                    if current_length + sentence_length > max_chunk_size and current_sub:
                        sub_text = ' '.join(current_sub).strip()
                        if sub_text:
                            sub_chunks.append(sub_text)

                            # 오버랩 준비
                            overlap_text = sub_text[-overlap_size:] if len(sub_text) > overlap_size else sub_text
                            overlap_start = overlap_text.rfind('. ')
                            if overlap_start > 0:
                                previous_overlap = overlap_text[overlap_start + 2:]
                            else:
                                previous_overlap = overlap_text

                        # 새 청크 시작 (오버랩 포함)
                        if previous_overlap and previous_overlap not in sentence:
                            current_sub = [previous_overlap, sentence]
                            current_length = len(previous_overlap) + sentence_length
                        else:
                            current_sub = [sentence]
                            current_length = sentence_length
                    else:
                        current_sub.append(sentence)
                        current_length += sentence_length

                if current_sub:
                    sub_text = ' '.join(current_sub).strip()
                    if sub_text:
                        sub_chunks.append(sub_text)

                # 각 서브 청크를 추가
                for idx, sub_text in enumerate(sub_chunks):
                    chunks.append({
                        'text': sub_text,
                        'section': f'{section_title} (part {idx+1})',
                        'page': page_num,
                        'is_sectioned': True
                    })
            else:
                # 섹션이 적당한 크기면 그대로 청크로
                if section_text:
                    chunks.append({
                        'text': section_text,
                        'section': section_title,
                        'page': page_num,
                        'is_sectioned': True
                    })

    # 빈 청크 제거
    chunks = [c for c in chunks if c['text'].strip()]

    return chunks


def clean_text(text: str) -> str:
    """
    텍스트 정제

    Args:
        text: 원본 텍스트

    Returns:
        정제된 텍스트
    """
    # 연속된 공백 제거
    text = re.sub(r'\s+', ' ', text)

    # 특수문자 제거 (일부 보존)
    # text = re.sub(r'[^\w\s가-힣.,!?()[\]{}\-:]', '', text)

    return text.strip()


def merge_short_chunks(chunks: List[str], min_length: int = 100) -> List[str]:
    """
    짧은 청크를 병합

    Args:
        chunks: 원본 청크 리스트
        min_length: 최소 청크 길이

    Returns:
        병합된 청크 리스트
    """
    merged = []
    buffer = ""

    for chunk in chunks:
        if len(buffer) + len(chunk) < min_length:
            buffer += " " + chunk
        else:
            if buffer:
                merged.append(buffer.strip())
            buffer = chunk

    if buffer:
        merged.append(buffer.strip())

    return merged
