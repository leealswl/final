"""
목차 추출 유틸리티 함수 모듈
기능 위주의 헬퍼 함수들
"""

import re
import json
import unicodedata
from datetime import datetime
from typing import List, Dict, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv

from ..state_types import BatchState

# OpenAI 클라이언트 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def find_proposal_template(templates: List[Dict]) -> Optional[Dict]:
    """
    제안서 양식 찾기 (우선순위: 계획서 > 제안서 > 신청서)
    
    여러 첨부 파일 중에서 목차가 있는 양식 파일을 찾는 함수입니다.
    파일명 키워드와 첨부 번호를 기반으로 우선순위를 계산합니다.
    
    우선순위 규칙:
    1. '계획서'가 포함된 파일 → 최우선
    2. 첨부 번호가 2 (붙임2) → 추가 가중치 +0.3
    3. 파일명 키워드 가중치:
       - '계획서': +1.0
       - '제안서': +0.8
       - '신청서': +0.6
       - '양식': +0.2
    
    Args:
        templates: List[Dict] - 첨부 파일 템플릿 리스트
        각 템플릿은 다음 필드를 포함:
        - file_name: 파일명
        - has_template: 양식 여부 (True인 것만 필터링)
        - confidence_score: 신뢰도 점수
        - attachment_number: 첨부 번호 (1, 2, 3...)
        
    Returns:
        Optional[Dict]: 찾은 양식 템플릿 정보
        - 양식이 없으면 None 반환
    """
    if not templates:
        return None

    # 양식으로 감지된 것만 필터링 (None이나 dict가 아닌 항목 제외)
    valid_templates = [
        t for t in templates 
        if isinstance(t, dict) and t.get('has_template')
    ]

    if not valid_templates:
        return None

    # 우선순위/가중치 계산
    def template_priority(template: Dict) -> float:
        file_name = template.get('file_name', '')
        score = template.get('confidence_score', 0.0)

        # 파일명 키워드 가중치
        keyword_weights = {
            '계획서': 1.0,
            '제안서': 0.8,
            '신청서': 0.6,
            '양식': 0.2
        }
        for keyword, weight in keyword_weights.items():
            if keyword in file_name:
                score += weight

        # 첨부 번호가 2 (붙임2)면 추가 가중치
        attachment_num = template.get('attachment_number')
        if attachment_num == 2:
            score += 0.3

        return score

    # 계획서가 포함된 템플릿이 있으면 최우선 반환
    for template in valid_templates:
        if '계획서' in template.get('file_name', ''):
            return template

    # 그 외는 최고 점수 템플릿 반환
    return max(valid_templates, key=template_priority)


def find_toc_table(tables: List[Dict]) -> Optional[Dict]:
    """
    목차 관련 표 찾기
    
    PDF에서 추출한 여러 표 중에서 목차가 포함된 표를 찾는 함수입니다.
    두 가지 방법으로 목차 표를 식별합니다.
    
    식별 방법:
    1. 키워드 기반: 첫 번째 행에 목차 관련 키워드가 있는지 확인
       - 키워드: '목차', '작성항목', '구성', '항목', '내용', '제출서류'
       
    2. 패턴 기반: 번호 패턴이 많이 포함된 표인지 확인
       - 패턴: "1.", "2.", "가.", "나.", "①", "②" 등
       - 행의 30% 이상이 번호 패턴이면 목차 표로 판단
    
    Args:
        tables: List[Dict] - PDF에서 추출한 표 리스트
        각 표는 다음 구조:
        - data: 2차원 리스트 [[cell, cell, ...], ...]
        
    Returns:
        Optional[Dict]: 목차가 포함된 표 정보
        - 목차 표를 찾지 못하면 None 반환
    """
    TOC_KEYWORDS = ['목차', '작성항목', '구성', '항목', '내용', '제출서류']

    for table in tables:
        if not isinstance(table, dict) or 'data' not in table:
            continue
        
        data = table.get('data', [])
        if not data or len(data) < 2:
            continue

        # 첫 번째 행 검사
        first_row = ' '.join([str(cell) for cell in data[0] if cell])

        if any(kw in first_row for kw in TOC_KEYWORDS):
            return table

        # 전체 데이터에서 번호 패턴 비율 체크
        all_text = '\n'.join([' '.join([str(cell) for cell in row if cell]) for row in data])
        number_pattern_count = len(re.findall(r'\d+\.|가\.|나\.|다\.|①|②|③', all_text))

        if number_pattern_count >= len(data) * 0.3:  # 행의 30% 이상이 번호 패턴
            return table

    return None


def parse_toc_table(table_data: List[List[str]]) -> List[Dict]:
    """
    목차 표에서 섹션 정보 추출
    
    목차 표의 각 행을 파싱하여 섹션 번호, 제목, 페이지 번호를 추출합니다.
    
    파싱 과정:
    1. 헤더 행 스킵 (첫 번째 행)
    2. 각 행에서 섹션 번호 추출
       - 패턴: "1.", "1.1.", "가.", "①", "I." 등
    3. 제목과 페이지 번호 분리
       - 패턴: "제목 ... 페이지번호" 또는 "제목"
    4. 필터링: 너무 짧거나 의미 없는 제목 제외
       - 제외: '합계', '계', '비고', 빈 문자열
    
    Args:
        table_data: List[List[str]] - 표 데이터 (2차원 리스트)
        예: [['번호', '제목', '페이지'], ['1', '연구목적', '3'], ...]
        
    Returns:
        List[Dict]: 추출된 섹션 리스트
        각 섹션은 다음 필드를 포함:
        - number: 섹션 번호 (예: "1", "1.1", "가")
        - title: 섹션 제목
        - page: 페이지 번호 (있는 경우)
        - row_index: 원본 표에서의 행 인덱스
    """
    sections = []

    # 헤더 스킵 (첫 번째 행)
    for row_idx, row in enumerate(table_data[1:], start=1):
        if not row or not any(row):  # 빈 행 스킵
            continue

        row_text = ' '.join([str(cell).strip() for cell in row if cell])

        # 섹션 번호 추출 (패턴: 1., 1.1., 가., ①, I., 등)
        number_match = re.search(
            r'^(\d+\.?\d*\.?|[가-힣]\.?|[①-⑳]|[IVX]+\.?)',
            row_text
        )

        if not number_match:
            continue

        section_number = number_match.group(1).strip('.')
        remaining_text = row_text[number_match.end():].strip()

        # 제목과 페이지 번호 분리
        # 패턴: "제목 ... 페이지번호" 또는 "제목"
        page_match = re.search(r'(\d+)\s*$', remaining_text)

        if page_match:
            page_number = int(page_match.group(1))
            title = remaining_text[:page_match.start()].strip()
        else:
            page_number = None
            title = remaining_text

        # 너무 짧거나 의미 없는 제목 필터링
        if len(title) < 2 or title in ['합계', '계', '비고', '']:
            continue

        sections.append({
            'number': section_number,
            'title': title,
            'page': page_number,
            'row_index': row_idx
        })

    return sections


def extract_sections_from_symbols(full_text: str) -> List[Dict]:
    """
    PDF 텍스트에서 다양한 패턴으로 시작하는 섹션 추출
    
    표 파싱이 실패한 경우, PDF 텍스트에서 직접 섹션을 추출하는 함수입니다.
    다양한 기호와 번호 패턴을 인식하여 목차 구조를 추출합니다.
    
    📋 지원 패턴:
    
    주요 섹션 패턴 (18가지):
    - 기호: □, ■, ●, ○, ◇, ◆, ▲, ▼
    - 숫자: 1., 2., 3. / 1), 2), 3) / (1), (2), (3)
    - 한글: 가., 나., 다. / 가), 나), 다) / (가), (나), (다)
    - 로마숫자: I., II., III. / Ⅰ., Ⅱ., Ⅲ.
    - 대괄호: 【1】, [1]
    - 하이픈: -, ―, ─
    - 원숫자: ①, ②, ③
    
    하위 섹션 패턴 (7가지):
    - 기호: ￭, ▪, ▫
    - 숫자: 1.1., 1.2. / 1.1), 1.2) / (1.1), (1.2)
    
    🔍 추출 과정:
    1. "사업 수행 계획서" 섹션 찾기 (다양한 키워드 지원)
    2. 주요 섹션 패턴 매칭 (□, 1., 가. 등)
    3. 하위 섹션 패턴 매칭 (￭, 1.1. 등)
    4. 개인정보 동의서 섹션에서 중단
    5. 필터링: 개인정보, 신용보증 관련 제외
    
    Args:
        full_text: str - PDF 전체 텍스트
        
    Returns:
        List[Dict]: 추출된 섹션 리스트 (평탄화된 구조)
        각 섹션은 다음 필드를 포함:
        - number: 섹션 번호 (예: "1", "1.1")
        - title: 섹션 제목
        - required: True (필수 항목)
    """
    sections = []
    lines = full_text.split('\n')
    total_lines = len(lines)
    
    # 주요 섹션 패턴 (우선순위 순)
    main_patterns = [
        (r'^□\s*(.+)$', '□'),  # □ 기업 현황
        (r'^■\s*(.+)$', '■'),  # ■ 기업 현황
        (r'^【([^】]+)】\s*(.+)$', '【】'),  # 【1】 기업 현황
        (r'^\[([^\]]+)\]\s*(.+)$', '[]'),  # [1] 기업 현황
        (r'^([0-9]{1,2})\.\s+(.+)$', '숫자.'),  # 1. 기업 현황
        (r'^([0-9]{1,2})\)\s+(.+)$', '숫자)'),  # 1) 기업 현황
        (r'^\(([0-9]{1,2})\)\s+(.+)$', '(숫자)'),  # (1) 기업 현황
        (r'^([가-힣])\.\s+(.+)$', '한글.'),  # 가. 기업 현황
        (r'^([가-힣])\)\s+(.+)$', '한글)'),  # 가) 기업 현황
        (r'^\(([가-힣])\)\s+(.+)$', '(한글)'),  # (가) 기업 현황
        (r'^([IVX]{1,4})\.\s+(.+)$', '로마숫자.'),  # I. 기업 현황
        (r'^([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ])\.\s+(.+)$', '로마숫자한글.'),  # Ⅰ. 기업 현황
        (r'^([①-⑳])\s*(.+)$', '원숫자'),  # ① 기업 현황
        (r'^●\s*(.+)$', '●'),  # ● 기업 현황
        (r'^○\s*(.+)$', '○'),  # ○ 기업 현황
        (r'^◇\s*(.+)$', '◇'),  # ◇ 기업 현황
        (r'^◆\s*(.+)$', '◆'),  # ◆ 기업 현황
        (r'^-\s*(.+)$', '-'),  # - 기업 현황
        (r'^―\s*(.+)$', '―'),  # ― 기업 현황
    ]
    
    # 하위 섹션 패턴
    sub_patterns = [
        (r'^￭\s*(.+)$', '￭'),  # ￭ 제품 서비스의 개요
        (r'^▪\s*(.+)$', '▪'),  # ▪ 제품 서비스의 개요
        (r'^▫\s*(.+)$', '▫'),  # ▫ 제품 서비스의 개요
        (r'^([0-9]{1,2}\.[0-9]{1,2})\.\s+(.+)$', '숫자.숫자.'),  # 1.1. 제품 서비스
        (r'^([0-9]{1,2}\.[0-9]{1,2})\)\s+(.+)$', '숫자.숫자)'),  # 1.1) 제품 서비스
        (r'^\(([0-9]{1,2}\.[0-9]{1,2})\)\s+(.+)$', '(숫자.숫자)'),  # (1.1) 제품 서비스
        (r'^([가-힣]\.[가-힣])\.\s+(.+)$', '한글.한글.'),  # 가.나. 제품 서비스
    ]
    
    # 목차 섹션 찾기 (다양한 키워드)
    proposal_keywords = [
        '사 업 수 행 계 획 서', '사업 수행 계획서', '사업수행계획서',
        '연구 계획서', '연구계획서', '제안서', '신청서',
        '작성 항목', '작성항목', '제출 항목', '제출항목',
        '목 차', '목차', '작성 목차', '작성목차'
    ]
    
    end_keywords = [
        '별지', '개인신용정보', '개인정보', '동의서', '동의',
        '첨부서류', '제출서류', '참고사항', '주의사항'
    ]
    
    in_proposal_section = False
    main_section_counter = 0
    current_main_section = None
    proposal_section_start_line = -1
    
    for idx, line in enumerate(lines):
        line_clean = line.strip()
        
        # 목차 섹션 시작 확인 (공백 무시하고 매칭)
        if not in_proposal_section:
            line_no_spaces = line_clean.replace(' ', '')
            for keyword in proposal_keywords:
                keyword_no_spaces = keyword.replace(' ', '')
                # "붙임", "첨부" 같은 맥락은 제외 (예: "붙임 1. 사업수행계획서")
                if '붙임' in line_clean or '첨부' in line_clean:
                    continue
                if keyword_no_spaces in line_no_spaces or keyword in line_clean:
                    # 키워드를 찾았으면 다음 10줄 안에 □ 패턴이 있는지 확인
                    lookahead_range = min(idx + 10, len(lines))
                    found_section_marker = False
                    for lookahead_idx in range(idx + 1, lookahead_range):
                        if lookahead_idx >= len(lines):
                            break
                        lookahead_line = lines[lookahead_idx].strip()
                        # □, ■, ● 패턴이 있으면 실제 목차 섹션
                        if re.match(r'^[□■●○◇◆▲▼]', lookahead_line):
                            found_section_marker = True
                            break
                    
                    if found_section_marker:
                        in_proposal_section = True
                        proposal_section_start_line = idx
                        break
            if in_proposal_section:
                continue
        
        # 목차 섹션 종료 확인
        if in_proposal_section:
            should_end = False
            # "별지" 키워드가 나타나면 개인정보 동의서 섹션 시작이므로 종료
            if '별지' in line_clean:
                should_end = True
            # "개인신용정보" + "동의서" 조합이 나타나면 종료
            elif '개인신용정보' in line_clean and '동의서' in line_clean:
                should_end = True
            # "개인정보" + "동의서" 조합이 나타나면 종료 (□로 시작하지 않는 경우만)
            elif '개인정보' in line_clean and '동의서' in line_clean and not re.match(r'^[□■●○◇◆▲▼]', line_clean):
                should_end = True
            # □로 시작하는 줄은 목차 섹션이므로 종료하지 않음
            elif re.match(r'^[□■●○◇◆▲▼]', line_clean):
                should_end = False
            # 그 외 end_keywords가 포함된 경우 (단, □로 시작하지 않는 경우만)
            else:
                for keyword in end_keywords:
                    if keyword in line_clean and not re.match(r'^[□■●○◇◆▲▼]', line_clean):
                        # "첨부서류", "제출서류" 등이 나타나면 종료
                        if keyword in ['첨부서류', '제출서류', '참고사항', '주의사항']:
                            should_end = True
                            break
            
            if should_end:
                break
        
        if not in_proposal_section or not line_clean:
            continue
        
        # 주요 섹션 패턴 매칭
        matched_main = False
        for pattern, pattern_type in main_patterns:
            match = re.match(pattern, line_clean)
            if match:
                if pattern_type in ['【】', '[]']:
                    # 대괄호 패턴: 번호와 제목 분리
                    number_part = match.group(1).strip()
                    title = match.group(2).strip()
                else:
                    # 기호나 번호 패턴
                    if len(match.groups()) == 1:
                        title = match.group(1).strip()
                        number_part = None
                    else:
                        number_part = match.group(1).strip()
                        title = match.group(2).strip()
                
                # 필터링: 개인정보, 신용보증 관련 제외
                if (len(title) > 1 and 
                    '동의' not in title and 
                    '수집' not in title and 
                    '제공' not in title and 
                    '신용보증' not in title and
                    '보유' not in title and
                    '거부' not in title and
                    title not in ['합계', '계', '비고', '']):
                    
                    main_section_counter += 1
                    # number_part가 None이 아니고 숫자인 경우에만 사용
                    if number_part and isinstance(number_part, str) and number_part.isdigit():
                        section_number = number_part
                    else:
                        section_number = str(main_section_counter)
                    
                    current_main_section = {
                        'number': section_number,
                        'title': title,
                        'level': 'main',
                        'subs': [],
                        'line_index': idx
                    }
                    sections.append(current_main_section)
                    matched_main = True
                    break
        
        # 하위 섹션 패턴 매칭 (주요 섹션 매칭 실패 시)
        if not matched_main and current_main_section:
            for pattern, pattern_type in sub_patterns:
                match = re.match(pattern, line_clean)
                if match:
                    if len(match.groups()) == 1:
                        sub_title = match.group(1).strip()
                        sub_number = None
                    else:
                        sub_number = match.group(1).strip()
                        sub_title = match.group(2).strip()
                    
                    # 필터링: 보완사항, 별지 관련 제외
                    if (len(sub_title) > 2 and 
                        '보완사항' not in sub_title and 
                        '별지' not in sub_title and
                        '☞' not in sub_title and
                        '참고' not in sub_title):
                        
                        sub_counter = len(current_main_section['subs']) + 1
                        sub_section_number = sub_number if sub_number else f"{current_main_section['number']}.{sub_counter}"
                        
                        current_main_section['subs'].append({
                            'number': sub_section_number,
                            'title': sub_title,
                            'level': 'sub',
                            'line_index': idx,
                            'parent_number': current_main_section['number']
                        })
                    break
    
    flattened_sections = []
    sortable_entries = []
    for section in sections:
        sortable_entries.append({
            'number': section['number'],
            'title': section['title'],
            'required': True,
            'level': section.get('level', 'main'),
            'parent_number': None,
            'line_index': section.get('line_index', 0)
        })
        for sub in section.get('subs', []):
            sortable_entries.append({
                'number': sub['number'],
                'title': sub['title'],
                'required': True,
                'level': sub.get('level', 'sub'),
                'parent_number': sub.get('parent_number', section['number']),
                'line_index': sub.get('line_index', section.get('line_index', 0))
            })

    sortable_entries.sort(key=lambda x: x.get('line_index', 0))
    for idx, item in enumerate(sortable_entries):
        next_idx = sortable_entries[idx + 1]['line_index'] if idx + 1 < len(sortable_entries) else total_lines
        item['next_line_index'] = next_idx
        flattened_sections.append(item)

    return flattened_sections


def create_default_toc() -> Dict:
    """
    기본 목차 생성 (추출 실패 시)
    
    모든 추출 방법이 실패했을 때 사용되는 기본 목차입니다.
    일반적인 R&D 제안서의 표준 목차 구조를 제공합니다.
    
    ⚠️ 사용 시점:
    - 양식을 찾을 수 없을 때
    - 표 파싱 실패 시
    - 패턴 추출 실패 시
    - LLM 추출 실패 시
    
    Returns:
        Dict: 기본 목차 구조
        - source: 'default'
        - extraction_method: 'fallback'
        - inference_confidence: 0.3 (낮은 신뢰도)
        - sections: 5개의 기본 섹션
          1. 연구개발 과제의 개요
          2. 연구개발 목표 및 내용
          3. 연구개발 추진체계 및 일정
          4. 연구개발 성과 활용방안
          5. 소요예산
    """
    return {
        'source': 'default',
        'extraction_method': 'fallback',
        'inference_confidence': 0.3,
        'sections': [
            {'number': '1', 'title': '연구개발 과제의 개요', 'required': True},
            {'number': '2', 'title': '연구개발 목표 및 내용', 'required': True},
            {'number': '3', 'title': '연구개발 추진체계 및 일정', 'required': True},
            {'number': '4', 'title': '연구개발 성과 활용방안', 'required': True},
            {'number': '5', 'title': '소요예산', 'required': True},
        ],
        'total_sections': 5,
        'extracted_at': datetime.now().isoformat(),
        'note': '목차 추출 실패로 기본 템플릿 사용'
    }



