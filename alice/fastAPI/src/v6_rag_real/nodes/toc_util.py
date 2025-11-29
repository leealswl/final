"""
목차 추출 유틸리티 함수 모듈
기능 위주의 헬퍼 함수들
"""

import re
import json
import unicodedata
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
import os
from dotenv import load_dotenv
import base64
import io

from ..state_types import BatchState

# OpenAI 클라이언트 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def find_toc_page(template_doc: Dict) -> Optional[Dict]:
    """
    "목차" 페이지를 찾아서 해당 페이지의 텍스트와 정보를 반환

    "목 차", "목차" 제목이 있는 페이지를 찾고,
    해당 페이지에서 로마숫자(I., II., III., IV.) 또는 아라비아숫자(1., 2., 3.)로
    시작하는 목차 항목들을 추출합니다.

    Args:
        template_doc: 템플릿 문서 정보

    Returns:
        Optional[Dict]: 목차 페이지 정보
        {
            'page_number': int,  # 페이지 번호
            'text': str,         # 페이지 텍스트
            'found_toc_title': str  # 발견된 목차 제목
        }
    """
    page_texts = template_doc.get('page_texts', {})

    if not page_texts:
        return None

    # 목차 페이지 후보 키워드
    toc_title_keywords = ['목 차', '목차', 'TABLE OF CONTENTS', 'CONTENTS']

    for page_num, page_text in page_texts.items():
        # 페이지 텍스트의 첫 50줄만 검사 (목차 제목은 보통 상단에 있음)
        lines = page_text.split('\n')[:50]

        for idx, line in enumerate(lines):
            line_stripped = line.strip()

            # 목차 제목 찾기
            for keyword in toc_title_keywords:
                if keyword in line_stripped:
                    # 다음 10줄 안에 로마숫자 또는 아라비아숫자 패턴이 있는지 확인
                    lookahead_lines = lines[idx:idx+15]
                    has_toc_pattern = False

                    for lookahead_line in lookahead_lines:
                        # I., II., III., IV. 또는 1., 2., 3. 패턴 확인
                        if re.match(r'^\s*([IVX]{1,5}|[1-9])\.\s+[가-힣\w]{2,}', lookahead_line.strip()):
                            has_toc_pattern = True
                            break

                    if has_toc_pattern:
                        print(f"    ✅ 목차 페이지 발견: 페이지 {page_num}, 제목 '{keyword}'")
                        return {
                            'page_number': page_num,
                            'text': page_text,
                            'found_toc_title': keyword
                        }

    return None


def extract_toc_from_toc_page(toc_page_info: Dict) -> List[Dict]:
    """
    목차 페이지에서 목차 항목 추출

    로마숫자 (I., II., III., IV.) 또는 아라비아숫자 (1., 2., 3.)로 시작하는
    주요 섹션과 하위 숫자 (1, 2, 3) 또는 한글 (가, 나, 다)로 시작하는 하위 섹션을 추출합니다.

    Args:
        toc_page_info: find_toc_page()가 반환한 목차 페이지 정보

    Returns:
        List[Dict]: 추출된 섹션 리스트
    """
    sections = []
    text = toc_page_info['text']
    lines = text.split('\n')

    # 로마숫자 → 아라비아숫자 변환 매핑
    roman_to_arabic = {
        'I': '1', 'II': '2', 'III': '3', 'IV': '4', 'V': '5',
        'VI': '6', 'VII': '7', 'VIII': '8', 'IX': '9', 'X': '10'
    }

    current_main_number = None
    sub_counter = {}  # 각 주요 섹션별 하위 카운터

    for line in lines:
        line_stripped = line.strip()

        if not line_stripped or len(line_stripped) < 3:
            continue

        # 주요 섹션 패턴 (I., II., III. 또는 1., 2., 3.)
        main_match = re.match(r'^([IVX]{1,5}|[1-9])\.\s+(.+?)(?:\s+\.{2,}|\s*$)', line_stripped)

        if main_match:
            section_marker = main_match.group(1)
            section_title = main_match.group(2).strip()

            # 로마숫자를 아라비아숫자로 변환
            if section_marker in roman_to_arabic:
                section_number = roman_to_arabic[section_marker]
            else:
                section_number = section_marker

            # 페이지 번호 제거 (끝에 00, 01 같은 패턴)
            section_title = re.sub(r'\s+\d{2}$', '', section_title).strip()

            # 너무 짧거나 의미 없는 제목 제외
            if len(section_title) < 2:
                continue

            sections.append({
                'number': section_number,
                'title': section_title,
                'level': 'main'
            })

            current_main_number = section_number
            sub_counter[current_main_number] = 1
            continue

        # 하위 섹션 패턴 (숫자만 또는 한글)
        # "1 주진행 및 필요성" 또는 "가 기업 현황" 형식
        if current_main_number:
            sub_match = re.match(r'^([1-9]|[가-힣])\s+(.+?)(?:\s+\.{2,}|\s*$)', line_stripped)

            if sub_match:
                sub_marker = sub_match.group(1)
                sub_title = sub_match.group(2).strip()

                # 페이지 번호 제거
                sub_title = re.sub(r'\s+\d{2}$', '', sub_title).strip()

                # 너무 짧거나 의미 없는 제목 제외
                if len(sub_title) < 2:
                    continue

                # 하위 섹션 번호 생성 (예: 1.1, 1.2)
                sub_number = f"{current_main_number}.{sub_counter[current_main_number]}"
                sub_counter[current_main_number] += 1

                sections.append({
                    'number': sub_number,
                    'title': sub_title,
                    'level': 'sub',
                    'parent_number': current_main_number
                })

    return sections


def convert_pdf_page_to_image(file_bytes: bytes, page_number: int) -> Optional[str]:
    """
    PDF의 특정 페이지를 이미지로 변환하여 base64 인코딩

    Args:
        file_bytes: PDF 파일의 바이트 데이터
        page_number: 변환할 페이지 번호 (1-based)

    Returns:
        Optional[str]: base64로 인코딩된 이미지 문자열 (data URL 형식)
                      실패 시 None
    """
    try:
        # pdf2image 라이브러리 사용
        from pdf2image import convert_from_bytes

        # 특정 페이지만 변환 (first_page, last_page는 1-based)
        images = convert_from_bytes(
            file_bytes,
            first_page=page_number,
            last_page=page_number,
            dpi=100  # 해상도 (150 DPI면 충분히 읽기 좋음)
        )

        if not images:
            return None

        # 첫 번째 (유일한) 이미지를 PNG로 변환
        img = images[0]

        # BytesIO 버퍼에 PNG로 저장
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        # base64 인코딩
        img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')

        return f"data:image/png;base64,{img_base64}"

    except ImportError:
        print("    ⚠️  pdf2image 라이브러리가 설치되지 않았습니다.")
        print("    💡 설치: pip install pdf2image")
        print("    💡 poppler 필요: brew install poppler (macOS) 또는 apt-get install poppler-utils (Ubuntu)")
        return None
    except Exception as e:
        print(f"    ⚠️  PDF → 이미지 변환 실패: {e}")
        return None


def extract_toc_from_image_with_vision(image_base64: str, file_name: str) -> Optional[List[Dict]]:
    """
    Vision API를 사용하여 목차 페이지 이미지에서 목차 추출 (단일 페이지)

    Args:
        image_base64: base64로 인코딩된 이미지 (data URL 형식)
        file_name: 파일명 (로깅용)

    Returns:
        Optional[List[Dict]]: 추출된 섹션 리스트
    """
    try:
        system_prompt = """당신은 PDF 문서의 목차 페이지를 분석하는 전문가입니다.

이미지로 제공된 목차 페이지를 보고, 섹션 구조를 정확하게 추출하세요.

중요 규칙:
1. **로마숫자 (I, II, III, IV) 또는 아라비아숫자 (1, 2, 3, 4)로 시작하는 주요 섹션만 추출**
2. **하위 섹션 (1, 2, 가, 나 등)도 추출**
3. **페이지 번호는 제거**
4. **점선(...)이나 구분자는 제거**
5. **섹션 번호는 아라비아숫자로 통일** (I → 1, II → 2)
6. **number 필드 형식**:
   - 주요 섹션: "1", "2", "3", "4"
   - 하위 섹션: "1.1", "1.2", "2.1", "2.2"

출력 형식 (JSON):
{
  "sections": [
    {
      "number": "1",
      "title": "개요",
      "level": "main"
    },
    {
      "number": "1.1",
      "title": "추진배경 및 필요성",
      "level": "sub",
      "parent_number": "1"
    }
  ]
}"""

        user_prompt = f"""첨부된 이미지는 '{file_name}' 파일의 목차 페이지입니다.

이미지에서 목차 구조를 추출하여 JSON 형식으로 반환하세요.

주의사항:
- 페이지 번호(00, 01 등)는 제거
- 점선(...)은 제거
- 로마숫자를 아라비아숫자로 변환 (I→1, II→2, III→3, IV→4)
- 각 섹션의 제목을 정확하게 추출"""

        response = client.chat.completions.create(
            model="gpt-4o",  # Vision 지원 모델
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_base64,
                                "detail": "high"  # 고해상도 분석
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        content = response.choices[0].message.content
        if not content:
            return None

        result = json.loads(content)
        sections = result.get('sections', [])

        if not sections:
            return None

        print(f"    ✅ Vision API로 {len(sections)}개 섹션 추출")
        return sections

    except Exception as e:
        print(f"    ⚠️  Vision API 호출 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def find_toc_page_range_with_vision(file_bytes: bytes, file_name: str, max_pages: int = 100) -> Optional[Tuple[int, int]]:
    """
    Vision API를 사용하여 목차가 시작하고 끝나는 페이지 범위 찾기

    전략:
    1. 첫 10페이지까지만 검색 (목차는 보통 앞쪽에 있음)
    2. 먼저 "목차" 제목이 있는 페이지 찾기
    3. 목차 제목이 없으면 번호 패턴(1., 2., 3. 또는 I., II., III.)으로 
       목차가 나열되는 구조인지 확인

    Args:
        file_bytes: PDF 파일의 바이트 데이터
        file_name: 파일명 (로깅용)
        max_pages: 최대 검색 페이지 수 (사용하지 않음, 항상 10페이지만 검색)

    Returns:
        Optional[Tuple[int, int]]: (시작 페이지, 종료 페이지) 또는 None
                                  페이지 번호는 1-based
    """
    try:
        from pdf2image import convert_from_bytes

        print(f"    🔍 목차 페이지 범위 찾기 시작 (첫 10페이지 검색)...")

        # 첫 10페이지만 검사
        search_pages = 10
        images = convert_from_bytes(
            file_bytes,
            dpi=100,
            last_page=search_pages
        )

        if not images:
            return None

        toc_start = None
        toc_end = None

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1단계: 목차 제목 기반 탐지 (5페이지씩 배치로 처리)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        for start_idx in range(0, min(10, len(images)), 5):
            end_idx = min(start_idx + 5, len(images))
            batch_images = images[start_idx:end_idx]

            image_contents = []
            for img in batch_images:
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}",
                        "detail": "high"
                    }
                })

            system_prompt = """당신은 PDF 문서를 분석하여 목차 페이지 범위를 찾는 전문가입니다.

제공된 페이지 이미지들을 보고, 목차가 시작하는 페이지와 끝나는 페이지를 찾으세요.

목차 시작 표시 (우선순위 순):
1. "목차", "목 차", "TABLE OF CONTENTS", "CONTENTS" 같은 명확한 제목이 있는 경우
2. 제목이 없어도 일정 패턴으로 번호가 매겨진 섹션 목록이 나열되는 경우
   - 1., 2., 3., 4. ... 또는 I., II., III., IV. ... 같은 패턴
   - 여러 줄에 걸쳐 연속적으로 번호가 나열되는 구조

목차 종료 표시:
- "사업비 소요명세", "소요명세", "예산 소요명세" 같은 항목
- 목차 이후 실제 양식이나 작성요령이 시작되는 부분
- 번호 패턴이 끝나는 지점

JSON 형식으로 반환:
{
  "has_toc_start": true/false,
  "toc_start_page": 페이지번호 (없으면 null),
  "has_toc_end": true/false,
  "toc_end_page": 페이지번호 (없으면 null),
  "detection_method": "title" 또는 "pattern" (목차 제목으로 찾았으면 "title", 번호 패턴으로 찾았으면 "pattern")
}"""

            user_prompt = f"""첨부된 이미지들은 '{file_name}' 파일의 페이지 {start_idx + 1}-{end_idx}입니다.

이 페이지 범위에서 목차가 시작하는지, 끝나는지 판단하여 JSON 형식으로 반환하세요.
페이지 번호는 1부터 시작합니다 (첫 번째 페이지 = 1).

중요: 
- "목차" 제목이 없어도 1., 2., 3. 또는 I., II., III. 같은 패턴으로 
  여러 줄에 걸쳐 연속적으로 번호가 나열되는 구조라면 목차로 판단하세요."""

            messages_content = [{"type": "text", "text": user_prompt}]
            messages_content.extend(image_contents)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": messages_content}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )

            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                if result.get('has_toc_start'):
                    detected_page = result.get('toc_start_page')
                    detection_method = result.get('detection_method', 'title')
                    
                    if toc_start is None:
                        # detected_page가 배치 내 상대 페이지 번호일 수 있음
                        # 일단 시작 인덱스를 기준으로 설정하고, detected_page가 있으면 조정
                        if detected_page and isinstance(detected_page, int):
                            # 배치 내에서 실제 페이지 번호 계산
                            # detected_page가 1-based라면, 배치의 첫 페이지는 start_idx + 1
                            toc_start = start_idx + detected_page
                        else:
                            toc_start = start_idx + 1  # 배치의 첫 페이지
                        
                        method_str = "제목 기반" if detection_method == "title" else "패턴 기반"
                        print(f"    ✅ 목차 시작 페이지 발견: {toc_start} ({method_str})")
                
                if result.get('has_toc_end'):
                    detected_page = result.get('toc_end_page')
                    if toc_end is None and detected_page and isinstance(detected_page, int):
                        toc_end = start_idx + detected_page
                        print(f"    ✅ 목차 종료 페이지 발견: {toc_end}")
                        break

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2단계: 목차 제목을 찾지 못한 경우, 번호 패턴 기반 재탐색
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if not toc_start:
            print(f"    🔍 목차 제목을 찾지 못함 → 번호 패턴 기반 재탐색...")
            
            # 첫 10페이지를 다시 패턴 기반으로 분석
            for start_idx in range(0, min(10, len(images)), 3):  # 3페이지씩 더 세밀하게
                end_idx = min(start_idx + 3, len(images))
                batch_images = images[start_idx:end_idx]

                image_contents = []
                for img in batch_images:
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
                    image_contents.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}",
                            "detail": "high"
                        }
                    })

                pattern_system_prompt = """당신은 PDF 문서를 분석하여 번호 패턴으로 나열된 목차를 찾는 전문가입니다.

"목차"라는 제목 없이도 1., 2., 3. 또는 I., II., III. 같은 번호 패턴으로 
여러 줄에 걸쳐 연속적으로 섹션이 나열되는 구조를 찾으세요.

중요 규칙:
- 3개 이상의 연속적인 번호 항목이 나열되어야 함 (1., 2., 3. ...)
- 각 항목은 제목이나 설명이 있어야 함
- 표나 폼 필드가 아닌 목차 형식이어야 함

JSON 형식으로 반환:
{
  "has_toc_pattern": true/false,
  "toc_start_page": 페이지번호 (패턴 시작 페이지),
  "toc_end_page": 페이지번호 (패턴 종료 페이지 또는 null)
}"""

                pattern_user_prompt = f"""첨부된 이미지들은 '{file_name}' 파일의 페이지 {start_idx + 1}-{end_idx}입니다.

이 페이지들에서 "목차" 제목 없이 번호 패턴(1., 2., 3. 또는 I., II., III.)으로 
나열된 목차 구조가 있는지 확인하세요.

중요: toc_start_page와 toc_end_page는 배치 내에서의 상대 페이지 번호를 반환하세요.
예: 배치의 첫 번째 페이지 = 1, 두 번째 페이지 = 2, 세 번째 페이지 = 3"""

                messages_content = [{"type": "text", "text": pattern_user_prompt}]
                messages_content.extend(image_contents)

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": pattern_system_prompt},
                        {"role": "user", "content": messages_content}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )

                content = response.choices[0].message.content
                if content:
                    result = json.loads(content)
                    if result.get('has_toc_pattern'):
                        detected_start = result.get('toc_start_page')
                        detected_end = result.get('toc_end_page')
                        
                        if not toc_start and detected_start:
                            # 배치 내 상대 페이지 번호를 절대 페이지 번호로 변환
                            if isinstance(detected_start, int):
                                # detected_start가 1-based 상대 페이지 번호라면
                                if 1 <= detected_start <= len(batch_images):
                                    toc_start = start_idx + detected_start  # start_idx는 0-based이므로 +1 필요
                                else:
                                    # 만약 절대 페이지 번호로 반환된 경우
                                    toc_start = detected_start
                            else:
                                # 배치의 첫 페이지를 시작으로 설정
                                toc_start = start_idx + 1
                            
                            print(f"    ✅ 목차 패턴 시작 페이지 발견: {toc_start} (패턴 기반)")
                        
                        if not toc_end and detected_end:
                            if isinstance(detected_end, int):
                                if 1 <= detected_end <= len(batch_images):
                                    toc_end = start_idx + detected_end
                                else:
                                    toc_end = detected_end
                            else:
                                toc_end = start_idx + len(batch_images)
                            
                            if toc_end:
                                print(f"    ✅ 목차 패턴 종료 페이지 발견: {toc_end}")
                        
                        if toc_start:
                            break

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3단계: 목차 종료 페이지 찾기 (시작 페이지는 찾았지만 종료를 못 찾은 경우)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if toc_start and not toc_end:
            print(f"    🔍 목차 종료 페이지 추가 검색 중...")
            # 목차 시작 페이지 이후부터 최대 15페이지까지 검색 (10페이지 제한 내)
            search_end = min(toc_start + 15, len(images), 10)
            for start_idx in range(toc_start - 1, search_end, 3):
                end_idx = min(start_idx + 3, search_end)
                batch_images = images[start_idx:end_idx]

                image_contents = []
                for img in batch_images:
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
                    image_contents.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}",
                            "detail": "high"
                        }
                    })

                end_system_prompt = """목차 종료 지점을 찾으세요. "사업비 소요명세" 또는 번호 패턴이 끝나는 지점을 찾으세요."""

                end_user_prompt = f"""첨부된 이미지들은 '{file_name}' 파일의 페이지 {start_idx + 1}-{end_idx}입니다.
목차가 끝나는 페이지를 찾으세요."""

                messages_content = [{"type": "text", "text": end_user_prompt}]
                messages_content.extend(image_contents)

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": end_system_prompt},
                        {"role": "user", "content": messages_content}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )

                content = response.choices[0].message.content
                if content:
                    result = json.loads(content)
                    if result.get('has_toc_end') and result.get('toc_end_page'):
                        detected_end = result.get('toc_end_page')
                        toc_end = start_idx + detected_end
                        print(f"    ✅ 목차 종료 페이지 발견: {toc_end}")
                        break

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4단계: 결과 반환
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if toc_start:
            # 종료 페이지를 못 찾은 경우, 시작 페이지 + 10 페이지를 종료로 설정
            if not toc_end:
                toc_end = min(toc_start + 10, len(images))
                print(f"    ⚠️  목차 종료 페이지를 찾지 못함 → 시작 페이지 + 10으로 설정: {toc_end}")
            
            return (toc_start, toc_end)
        else:
            print(f"    ⚠️  목차 페이지 범위를 찾지 못함 (첫 10페이지 내에서)")
            return None

    except Exception as e:
        print(f"    ⚠️  목차 페이지 범위 찾기 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_toc_from_page_range_with_vision(file_bytes: bytes, file_name: str, start_page: int, end_page: int) -> Optional[List[Dict]]:
    """
    Vision API를 사용하여 특정 페이지 범위에서 목차 추출

    Args:
        file_bytes: PDF 파일의 바이트 데이터
        file_name: 파일명 (로깅용)
        start_page: 시작 페이지 (1-based)
        end_page: 종료 페이지 (1-based, 포함)

    Returns:
        Optional[List[Dict]]: 추출된 섹션 리스트
    """
    try:
        from pdf2image import convert_from_bytes

        print(f"    📋 목차 페이지 범위 분석: {start_page}-{end_page} 페이지")

        # 해당 페이지 범위를 이미지로 변환
        images = convert_from_bytes(
            file_bytes,
            dpi=100,
            first_page=start_page,
            last_page=end_page
        )

        if not images:
            print(f"    ⚠️  페이지 {start_page}-{end_page} 변환 실패")
            return None

        print(f"    📄 {len(images)}개 페이지를 이미지로 변환 완료")

        # 이미지들을 base64로 인코딩
        image_contents = []
        for img in images:
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}",
                    "detail": "high"
                }
            })

        system_prompt = """당신은 PDF 문서의 목차 페이지를 분석하는 전문가입니다.

제공된 목차 페이지 이미지들을 보고, 목차 구조를 정확하게 추출하세요.

중요 규칙:
1. **로마숫자 (I, II, III, IV) 또는 아라비아숫자 (1, 2, 3, 4)로 시작하는 주요 섹션만 추출**
2. **하위 섹션 (1, 2, 가, 나 등)도 추출**
3. **페이지 번호는 제거** (점선 뒤의 숫자 등)
4. **점선(...)이나 구분자는 제거**
5. **섹션 번호는 아라비아숫자로 통일** (I → 1, II → 2)
6. **"사업비 소요명세" 같은 항목까지 포함** (이것이 목차의 마지막 항목)
7. **number 필드 형식**:
   - 주요 섹션: "1", "2", "3", "4"
   - 하위 섹션: "1.1", "1.2", "2.1", "2.2"

출력 형식 (JSON):
{
  "sections": [
    {
      "number": "1",
      "title": "개요",
      "level": "main"
    },
    {
      "number": "1.1",
      "title": "추진배경 및 필요성",
      "level": "sub",
      "parent_number": "1"
    }
  ]
}"""

        user_prompt = f"""첨부된 이미지들은 '{file_name}' 파일의 목차 페이지 (페이지 {start_page}-{end_page})입니다.

이미지에서 목차 구조를 추출하여 JSON 형식으로 반환하세요.

주의사항:
- 페이지 번호(00, 01 등)는 제거
- 점선(...)은 제거
- 로마숫자를 아라비아숫자로 변환 (I→1, II→2, III→3, IV→4)
- 각 섹션의 제목을 정확하게 추출
- "사업비 소요명세"까지 포함 (이것이 목차의 마지막 항목)"""

        # Vision API 호출
        messages_content = [{"type": "text", "text": user_prompt}]
        messages_content.extend(image_contents)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": messages_content}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        content = response.choices[0].message.content
        if not content:
            print(f"    ⚠️  Vision API 응답 없음")
            return None

        result = json.loads(content)
        sections = result.get('sections', [])

        if not sections:
            print(f"    ⚠️  추출된 섹션 없음")
            return None

        print(f"    ✅ 목차 페이지에서 {len(sections)}개 섹션 추출")
        return sections

    except Exception as e:
        print(f"    ⚠️  목차 페이지 범위 추출 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def find_descriptions_for_toc_sections(
    file_bytes: bytes,
    file_name: str,
    toc_sections: List[Dict],
    toc_end_page: int,
    max_search_pages: int = 50
) -> Dict[str, str]:
    """
    목차 이후 페이지들에서 각 목차 항목에 대한 작성요령/가이드 찾기

    Args:
        file_bytes: PDF 파일의 바이트 데이터
        file_name: 파일명 (로깅용)
        toc_sections: 추출된 목차 섹션 리스트
        toc_end_page: 목차가 끝나는 페이지
        max_search_pages: 최대 검색할 페이지 수

    Returns:
        Dict[str, str]: {섹션 제목: description} 매핑
    """
    try:
        from pdf2image import convert_from_bytes

        print(f"    🔍 각 목차 항목에 대한 작성요령 찾기 시작 (목차 종료 페이지: {toc_end_page})...")

        # 목차 종료 페이지 이후부터 검색
        search_start = toc_end_page + 1
        search_end = min(search_start + max_search_pages, 100)  # 최대 100페이지까지만

        images = convert_from_bytes(
            file_bytes,
            dpi=100,
            first_page=search_start,
            last_page=search_end
        )

        if not images:
            print(f"    ⚠️  페이지 {search_start}-{search_end} 변환 실패")
            return {}

        print(f"    📄 {len(images)}개 페이지를 이미지로 변환 완료 (검색 범위: {search_start}-{search_end} 페이지)")

        # 목차 섹션 제목 리스트 생성
        section_titles = [sec.get('title', '') for sec in toc_sections if sec.get('title')]

        # 10페이지씩 배치로 처리
        batch_size = 10
        all_descriptions = {}

        for batch_start in range(0, len(images), batch_size):
            batch_end = min(batch_start + batch_size, len(images))
            batch_images = images[batch_start:batch_end]
            actual_page_start = search_start + batch_start

            # 이미지들을 base64로 인코딩
            image_contents = []
            for img in batch_images:
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                img_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_base64}",
                        "detail": "high"
                    }
                })

            system_prompt = """당신은 제안서 양식 문서를 분석하여 각 목차 항목에 대한 작성요령과 가이드를 찾는 전문가입니다.

제공된 페이지 이미지들을 보고, 각 목차 항목에 대한 작성요령, 기재요령, 작성 방법 등을 찾아서 정리하세요.

중요 규칙:
1. **각 목차 항목의 제목과 일치하는 섹션을 찾아서 해당 섹션의 작성요령 추출**
2. **"작성요령", "기재요령", "작성 방법", "기재 방법" 같은 가이드 텍스트 추출**
3. **각 항목에 대해 1-2문장으로 요약하여 description 생성**
4. **양식, 예시, 표는 제외하고 실제 작성 방법만 추출**

출력 형식 (JSON):
{
  "descriptions": {
    "목차 항목 제목1": "해당 항목에 대한 작성요령 설명 (1-2문장)",
    "목차 항목 제목2": "해당 항목에 대한 작성요령 설명 (1-2문장)"
  }
}"""

            user_prompt = f"""첨부된 이미지들은 '{file_name}' 파일의 페이지 {actual_page_start}-{actual_page_start + len(batch_images) - 1}입니다.

이 페이지들에서 다음 목차 항목들에 대한 작성요령이나 가이드를 찾아서 JSON 형식으로 반환하세요:

목차 항목들:
{chr(10).join([f"- {title}" for title in section_titles[:20]])}

각 항목에 대해:
- 해당 항목의 제목과 일치하는 섹션 찾기
- 그 섹션의 작성요령, 기재요령, 작성 방법 추출
- 1-2문장으로 요약

찾지 못한 항목은 포함하지 마세요."""

            # Vision API 호출
            messages_content = [{"type": "text", "text": user_prompt}]
            messages_content.extend(image_contents)

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": messages_content}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )

            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                descriptions = result.get('descriptions', {})
                
                # 중복되지 않은 항목만 추가
                for title, desc in descriptions.items():
                    if title and desc and title not in all_descriptions:
                        all_descriptions[title] = desc
                        print(f"      ✅ '{title}'에 대한 작성요령 발견")

            print(f"      ✅ 배치 {batch_start // batch_size + 1} 완료 (누적: {len(all_descriptions)}개 항목)")

        print(f"    ✅ 총 {len(all_descriptions)}개 목차 항목에 대한 작성요령 발견")
        return all_descriptions

    except Exception as e:
        print(f"    ⚠️  작성요령 찾기 실패: {e}")
        import traceback
        traceback.print_exc()
        return {}


def extract_toc_from_full_document_vision(file_bytes: bytes, file_name: str, max_pages: int = 60) -> Optional[List[Dict]]:
    """
    Vision API를 사용하여 양식 문서 전체에서 목차 추출 (개선된 전략)

    새로운 전략:
    1. 목차가 있는 페이지 범위를 먼저 찾기
    2. 목차 페이지 범위만 먼저 분석하여 목차 구조 추출
    3. 이후 페이지들에서 각 목차 항목에 대한 작성요령 찾기
    4. 각 목차 항목의 description에 작성요령 추가

    Args:
        file_bytes: PDF 파일의 바이트 데이터
        file_name: 파일명 (로깅용)
        max_pages: 최대 분석 페이지 수 (기본 60페이지)

    Returns:
        Optional[List[Dict]]: 추출된 섹션 리스트 (description 포함)
    """
    try:
        print(f"    🖼️  개선된 Vision API 분석 전략 시작...")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1단계: 목차 페이지 범위 찾기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        page_range = find_toc_page_range_with_vision(file_bytes, file_name, max_pages)

        if not page_range:
            print(f"    ⚠️  목차 페이지 범위를 찾지 못함 → 기존 배치 방식으로 fallback")
            # 기존 방식으로 fallback (간단한 버전)
            return None

        toc_start_page, toc_end_page = page_range
        print(f"    ✅ 목차 페이지 범위 확인: {toc_start_page}-{toc_end_page} 페이지")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2단계: 목차 페이지 범위만 먼저 분석하여 목차 구조 추출
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        toc_sections = extract_toc_from_page_range_with_vision(
            file_bytes, file_name, toc_start_page, toc_end_page
        )

        if not toc_sections or len(toc_sections) < 3:
            print(f"    ⚠️  목차 추출 실패 또는 섹션 부족 → None 반환")
            return None

        print(f"    ✅ 목차 추출 완료: {len(toc_sections)}개 섹션")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3단계: 목차 이후 페이지들에서 각 항목에 대한 작성요령 찾기
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        descriptions = find_descriptions_for_toc_sections(
            file_bytes, file_name, toc_sections, toc_end_page
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4단계: 목차 섹션에 description 추가
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        final_sections = []
        for section in toc_sections:
            section_title = section.get('title', '')
            
            # 작성요령이 있으면 사용, 없으면 기본 description
            description = descriptions.get(section_title, '')
            if not description:
                # 기본 description 생성
                description = f"{section_title} 섹션에 대한 작성 내용"

            final_section = {
                'number': section.get('number', ''),
                'title': section_title,
                'level': section.get('level', 'main'),
                'parent_number': section.get('parent_number'),
                'description': description
            }
            final_sections.append(final_section)

        print(f"    ✅ 최종 목차 생성 완료: {len(final_sections)}개 섹션 (description 포함)")
        return final_sections

    except ImportError:
        print("    ⚠️  pdf2image 라이브러리가 설치되지 않았습니다.")
        return None
    except Exception as e:
        print(f"    ⚠️  배치 Vision API 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


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
    """
    sections = []
    lines = full_text.split('\n')
    total_lines = len(lines)
    
    # 주요 섹션 패턴 (우선순위 순)
    # [2025-11-19 수정] "숫자)" 패턴은 sub_patterns로 이동 (1), 2)는 보통 하위 섹션)
    main_patterns = [
        # [2025-11-19 추가] < 본문 1 >, < 본문 2 > 형식 지원
        (r'^<\s*본문\s*(\d+)\s*>', '<본문>'),  # < 본문 1 >, < 본문 2 >
        (r'^<본문\s*(\d+)>', '<본문>'),  # <본문 1>, <본문 2>

        (r'^□\s*(.+)$', '□'),  # □ 기업 현황
        (r'^■\s*(.+)$', '■'),  # ■ 기업 현황
        (r'^【([^】]+)】\s*(.+)$', '【】'),  # 【1】 기업 현황
        (r'^\[([^\]]+)\]\s*(.+)$', '[]'),  # [1] 기업 현황
        (r'^([0-9]{1,2})\.\s+(.+)$', '숫자.'),  # 1. 기업 현황 (main 섹션)
        (r'^\(([0-9]{1,2})\)\s+(.+)$', '(숫자)'),  # (1) 기업 현황
        (r'^([가-힣])\.\s+(.+)$', '한글.'),  # 가. 기업 현황
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
    # [2025-11-19 추가] "숫자)", "한글)" 패턴 추가 (1), 2), 가), 나) 등은 하위 섹션)
    sub_patterns = [
        (r'^￭\s*(.+)$', '￭'),  # ￭ 제품 서비스의 개요
        (r'^▪\s*(.+)$', '▪'),  # ▪ 제품 서비스의 개요
        (r'^▫\s*(.+)$', '▫'),  # ▫ 제품 서비스의 개요
        (r'^([0-9]{1,2})\)\s+(.+)$', '숫자)'),  # 1) 연구개발과제의 목표 (sub 섹션)
        (r'^([가-힣])\)\s+(.+)$', '한글)'),  # 가) 제품 서비스 (sub 섹션)
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
        '목 차', '목차', '작성 목차', '작성목차',
        # [2025-11-19 추가] < 본문 1 >, < 본문 2 > 형식 지원
        '< 본문 1 >', '<본문 1>', '< 본문', '<본문'
    ]
    
    end_keywords = [
        '별지', '개인신용정보', '개인정보', '동의서', '동의',
        '첨부서류', '제출서류', '참고사항', '주의사항',
        # [2025-11-19 추가] 작성요령 섹션에서 목차 종료
        '작성요령', '작성 요령', '기재요령', '기재 요령'
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
                    # [2025-11-19 수정] < 본문 > 패턴은 그 라인 자체가 섹션 시작
                    # 현재 라인이 < 본문 > 패턴이면 바로 in_proposal_section = True
                    if (re.match(r'^<\s*본문\s*\d+\s*>', line_clean) or
                        re.match(r'^<본문\s*\d+>', line_clean)):
                        in_proposal_section = True
                        proposal_section_start_line = idx
                        break

                    # 그 외의 경우는 다음 10줄 안에 섹션 마커가 있는지 확인
                    lookahead_range = min(idx + 10, len(lines))
                    found_section_marker = False
                    for lookahead_idx in range(idx + 1, lookahead_range):
                        if lookahead_idx >= len(lines):
                            break
                        lookahead_line = lines[lookahead_idx].strip()
                        # □, ■, ● 패턴 또는 < 본문 > 패턴이 있으면 실제 목차 섹션
                        if (re.match(r'^[□■●○◇◆▲▼]', lookahead_line) or
                            re.match(r'^<\s*본문\s*\d+\s*>', lookahead_line) or
                            re.match(r'^<본문\s*\d+>', lookahead_line)):
                            found_section_marker = True
                            break

                    if found_section_marker:
                        in_proposal_section = True
                        proposal_section_start_line = idx
                        break
            # [2025-11-19 수정] < 본문 > 패턴으로 섹션이 시작된 경우는 continue하지 않음
            # 왜냐하면 그 라인 자체가 섹션 마커이므로 패턴 매칭을 해야 함
            if in_proposal_section:
                # 현재 라인이 < 본문 > 패턴이면 continue하지 않고 패턴 매칭 진행
                if not (re.match(r'^<\s*본문\s*\d+\s*>', line_clean) or
                        re.match(r'^<본문\s*\d+>', line_clean)):
                    continue
        
        # 목차 섹션 종료 확인
        if in_proposal_section:
            should_end = False
            # [2025-11-19 수정] "별지" 단독 vs "별지로" 구분
            # "별지로 작성 가능" 같은 설명은 목차 항목의 일부이므로 제외
            # "별지" 단독으로 나타나면 개인정보 동의서 섹션 시작이므로 종료
            if line_clean == '별지' or (line_clean.startswith('별지') and not '별지로' in line_clean):
                should_end = True
            # "개인신용정보" + "동의서" 조합이 나타나면 종료
            elif '개인신용정보' in line_clean and '동의서' in line_clean:
                should_end = True
            # "개인정보" + "동의서" 조합이 나타나면 종료 (□ 또는 < 본문 >로 시작하지 않는 경우만)
            elif ('개인정보' in line_clean and '동의서' in line_clean and
                  not re.match(r'^[□■●○◇◆▲▼]', line_clean) and
                  not re.match(r'^<\s*본문', line_clean)):
                should_end = True
            # □ 또는 < 본문 >로 시작하는 줄은 목차 섹션이므로 종료하지 않음
            elif (re.match(r'^[□■●○◇◆▲▼]', line_clean) or
                  re.match(r'^<\s*본문', line_clean)):
                should_end = False
            # 그 외 end_keywords가 포함된 경우 (단, □로 시작하지 않는 경우만)
            else:
                for keyword in end_keywords:
                    if keyword in line_clean and not re.match(r'^[□■●○◇◆▲▼]', line_clean):
                        # [2025-11-19 수정] 작성요령은 무조건 종료
                        if keyword in ['작성요령', '작성 요령', '기재요령', '기재 요령']:
                            should_end = True
                            break
                        # "첨부서류", "제출서류" 등이 나타나면 종료
                        elif keyword in ['첨부서류', '제출서류', '참고사항', '주의사항']:
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
                # [2025-11-19 수정] < 본문 1 >, < 본문 2 >는 양식의 구분자이므로 목차에 포함하지 않음
                # 이것은 "이 아래부터 본문 작성 항목이 시작됩니다"라는 표시일 뿐
                if pattern_type == '<본문>':
                    # < 본문 > 패턴은 in_proposal_section을 활성화시키지만, 섹션으로 추가하지 않음
                    matched_main = True  # 패턴은 매칭되었지만 섹션으로 추가하지 않음
                    break
                elif pattern_type in ['【】', '[]']:
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
                
                # [2025-11-19 수정] 필터링: 개인정보 동의서 관련만 제외
                # "신용보증 신청" 등은 정당한 목차 항목이므로 포함
                if (len(title) > 1 and
                    '동의' not in title and
                    '수집' not in title and
                    '제공' not in title and
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
                        # [2025-11-19 수정] sub_number가 있어도 parent 번호를 앞에 붙임
                        # "1) 목표" → "2.1" (parent가 2일 때)
                        sub_section_number = f"{current_main_section['number']}.{sub_counter}"

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
            'level': section.get('level', 'main'),
            'parent_number': None,
            'line_index': section.get('line_index', 0)
        })
        for sub in section.get('subs', []):
            sortable_entries.append({
                'number': sub['number'],
                'title': sub['title'],
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
            {'number': '1', 'title': '연구개발 과제의 개요'},
            {'number': '2', 'title': '연구개발 목표 및 내용'},
            {'number': '3', 'title': '연구개발 추진체계 및 일정'},
            {'number': '4', 'title': '연구개발 성과 활용방안'},
            {'number': '5', 'title': '소요예산'},
        ],
        'total_sections': 5,
        'extracted_at': datetime.now().isoformat(),
        'note': '목차 추출 실패로 기본 템플릿 사용'
    }



