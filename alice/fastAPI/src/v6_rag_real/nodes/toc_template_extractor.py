"""
양식 기반 목차 추출 모듈
제안서 양식 파일에서 목차를 추출하는 세부 로직

⚠️ [DEPRECATED] 이 파일은 더 이상 사용되지 않습니다.

Vision API 기반 배치 처리가 도입되면서 이 텍스트 기반 추출 방식은 
toc_extraction.py의 extract_toc_from_template 함수로 대체되었습니다.

현재 목차 추출 전략:
- extract_toc_from_template: Vision API로 목차 페이지 범위를 찾고 
  배치 방식으로 목차를 추출하며 각 항목의 작성요령도 함께 찾습니다.

이 파일은 참고용으로만 유지되며, 실제 실행 경로에서 사용되지 않습니다.
"""

import json
import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from .toc_util import (
    find_toc_table,
    parse_toc_table,
    extract_sections_from_symbols,
    create_default_toc,
    client
)


def extract_subsections_from_range(
    lines_block: List[str],
    parent_number: str,
    base_line_index: int,
    end_line_index: int,
    start_counter: int = 1
) -> List[Dict]:
    """
    주어진 라인 블록에서 하위 섹션 패턴(￭, 1), (가) 등)을 추출
    """
    SUBSECTION_PATTERNS = [
        (re.compile(r'^￭\s*(.+)$'), 1),
        (re.compile(r'^▪\s*(.+)$'), 1),
        (re.compile(r'^▫\s*(.+)$'), 1),
        (re.compile(r'^[-–—]\s*(.+)$'), 1),
        (re.compile(r'^●\s*(.+)$'), 1),
        (re.compile(r'^○\s*(.+)$'), 1),
        (re.compile(r'^([0-9]{1,2})\)\s*(.+)$'), 2),
        (re.compile(r'^\(([0-9]{1,2})\)\s*(.+)$'), 2),
        (re.compile(r'^([가-힣])\)\s*(.+)$'), 2),
        (re.compile(r'^\(([가-힣])\)\s*(.+)$'), 2),
    ]

    subsections = []
    counter = start_counter
    for offset, line in enumerate(lines_block):
        clean = line.strip()
        if not clean:
            continue
        for pattern, group_idx in SUBSECTION_PATTERNS:
            match = pattern.match(clean)
            if match:
                title = match.group(group_idx).strip()
                if len(title) < 2:
                    break
                subsection_number = f"{parent_number}.{counter}"
                absolute_index = base_line_index + offset
                subsections.append({
                    'number': subsection_number,
                    'title': title,
                    'level': 'sub',
                    'parent_number': parent_number,
                    'line_index': absolute_index
                })
                counter += 1
                break

    for idx, sub in enumerate(subsections):
        next_line = subsections[idx + 1]['line_index'] if idx + 1 < len(subsections) else end_line_index
        sub['next_line_index'] = next_line

    return subsections


def prepare_template_context(template_doc: Dict, state: Dict, template: Dict) -> str:
    """
    템플릿 문서에서 LLM에 전달할 컨텍스트 추출

    우선순위:
    1. page_texts (원본 페이지 구조 보존)
    2. all_chunks (페이지별 청크)
    3. full_text 일부
    """
    page_texts = template_doc.get('page_texts', {})
    chunk_context = ""

    if page_texts:
        print(f"    ✅ page_texts 사용: {len(page_texts)}개 페이지")
        sorted_pages = sorted(page_texts.items(), key=lambda x: x[0])
        page_context_parts = []

        MAX_PAGES = 20
        for page_num, page_text in sorted_pages[:MAX_PAGES]:
            text_snippet = page_text[:1500]
            page_context_parts.append(f"[페이지 {page_num}]\n{text_snippet}")

        chunk_context = '\n\n'.join(page_context_parts)
        print(f"    📄 페이지 텍스트 길이: {len(chunk_context):,}자 (최대 {MAX_PAGES}페이지)")

    # Fallback: all_chunks 사용
    if not chunk_context:
        print(f"    ⚠️  page_texts 없음 → all_chunks fallback 시도")
        all_chunks = state.get('all_chunks', [])
        template_chunks = []
        template_file_name = template['file_name']

        for chunk in all_chunks:
            if chunk.get('file_name') == template_file_name:
                template_chunks.append(chunk)

        template_chunks.sort(key=lambda c: (c.get('page', 0) or 0, c.get('chunk_id', '')))

        MAX_TEMPLATE_CHUNKS = 20
        chunk_context_parts = []
        for chunk in template_chunks[:MAX_TEMPLATE_CHUNKS]:
            page = chunk.get('page', '?')
            section = chunk.get('section', '섹션')
            text_snippet = chunk.get('text', '')[:800]
            chunk_context_parts.append(f"[페이지 {page} | {section}]\n{text_snippet}")

        chunk_context = '\n\n'.join(chunk_context_parts)
        print(f"    📦 청크 텍스트 길이: {len(chunk_context):,}자 ({len(template_chunks)}개 청크)")

    # 최종 fallback: full_text
    if not chunk_context:
        full_text = template_doc.get('full_text', '')
        chunk_context = full_text[:5000]
        if chunk_context:
            print(f"    ⚠️  청크 없음 → full_text 일부 사용 (길이 {len(chunk_context):,}자)")

    return chunk_context


def build_base_sections(
    symbol_sections: List[Dict],
    full_text: str
) -> Tuple[List[Dict], List[Dict]]:
    """
    패턴 기반으로 추출한 섹션에서 base_sections와 section_contexts 생성

    symbol_sections에 이미 main/sub 섹션이 모두 포함되어 있으므로,
    각 섹션의 본문 excerpt만 추가하여 반환

    Returns:
        (base_sections, section_contexts) 튜플
    """
    base_sections: List[Dict] = []
    section_contexts: List[Dict] = []
    full_lines = full_text.split('\n')
    total_lines = len(full_lines)

    # symbol_sections를 그대로 사용하되, excerpt만 추가
    for sec in symbol_sections:
        start_line = sec.get('line_index', 0)
        end_line = sec.get('next_line_index', total_lines)
        block_lines = full_lines[start_line:end_line]
        block_text = '\n'.join(block_lines).strip()

        # excerpt 추가
        sec_entry = {
            'number': sec['number'],
            'title': sec['title'],
            'level': sec.get('level', 'main'),
            'parent_number': sec.get('parent_number'),
            'line_index': start_line,
            'next_line_index': end_line
        }

        # 본문 발췌 추가
        if block_text:
            max_excerpt = 800 if sec.get('level') == 'main' else 600
            sec_entry['excerpt'] = block_text[:max_excerpt]
            section_contexts.append({
                'number': sec_entry['number'],
                'title': sec_entry['title'],
                'excerpt': sec_entry['excerpt']
            })

        base_sections.append(sec_entry)

    return base_sections, section_contexts


def extract_template_text(full_text: str) -> str:
    """
    full_text에서 목차 섹션만 추출

    키워드 기반으로 "< 본문", "작성 목차" 등을 찾아서 해당 구간 추출
    """
    template_text = ''

    toc_start_keywords = [
        '< 본문', '<본문', '본문>',
        '작성 목차', '제출서류 목차', '계획서 목차',
        '작성항목', '제출항목', '기재사항'
    ]
    toc_section_start = -1
    for keyword in toc_start_keywords:
        idx = full_text.find(keyword)
        if idx != -1:
            toc_section_start = idx
            print(f"    📍 목차 시작 키워드 발견: '{keyword}' (위치: {idx})")
            break

    if toc_section_start != -1:
        text_after_start = full_text[toc_section_start:]
        end_keywords = [
            '< 본문 2', '<본문 2', '본문 2>',
            '작성요령', '작성 요령', '주의사항', '유의사항',
            '참고사항', '기재요령', '첨부서류',
            '※ 참고', '【참고', '[참고'
        ]
        toc_end = len(text_after_start)
        for end_kw in end_keywords:
            end_idx = text_after_start.find(end_kw)
            if end_idx != -1 and end_idx < toc_end:
                toc_end = end_idx
                print(f"    📍 목차 끝 키워드 발견: '{end_kw}' (상대 위치: {end_idx})")
                break
        template_text = text_after_start[:min(toc_end, 5000)]
        print(f"    ✅ 목차 섹션 추출 완료 (길이: {len(template_text)}자)")
    else:
        # 번호 패턴 기반 탐색
        pattern = r'^[1-9]\.\s+[가-힣]{2,}'
        lines = full_text.split('\n')
        toc_line_start = -1
        consecutive_numbered = 0
        for i, line in enumerate(lines):
            if re.search(pattern, line.strip()):
                if toc_line_start == -1:
                    toc_line_start = i
                consecutive_numbered += 1
                if consecutive_numbered >= 3:
                    toc_lines = lines[toc_line_start:toc_line_start + 100]
                    template_text = '\n'.join(toc_lines)[:5000]
                    print(f"    ✅ 번호 패턴 기반 목차 발견 (라인: {toc_line_start}, 길이: {len(template_text)}자)")
                    break
            else:
                consecutive_numbered = 0

        if not template_text:
            template_text = full_text[:15000]
            print(f"    ⚠️  목차 패턴 미발견 → 전체 텍스트 사용 (15000자)")

    return template_text


def build_llm_prompt(
    template: Dict,
    template_doc: Dict,
    tables: List,
    table_sections: List[Dict],
    symbol_sections: List[Dict],
    template_text: str,
    chunk_context: str,
    skeleton_json: str,
    section_contexts: List[Dict]
) -> Tuple[str, str]:
    """
    LLM에 전달할 system_prompt와 user_prompt 구성
    """
    system_prompt = """당신은 정부 지원사업 신청서/제안서 양식을 분석하여 실제 작성해야 하는 본문 목차를 정리하는 전문가입니다.

⚠️ 중요 규칙:
1. **폼 입력 필드는 절대 목차로 포함하지 마세요:**
   - ❌ 제외: "기업명", "대표자", "연락처", "주소", "전화", "팩스", "mail", "휴대전화", "생년월일", "성별", "직위", "부서" 등
   - ❌ 제외: "1)기업현황", "2)대표자", "3)실무책임자" 같은 폼 섹션 번호
   - ✅ 포함: "□ 기업현황", "□ 대표자 및 경영진 현황", "□ 목표" 같은 본문 작성 섹션

2. **본문 작성 항목만 목차로 추출:**
   - □, ■, ●, ￭ 같은 기호로 시작하는 섹션 추출
   - "1.", "2.", "3." 같은 숫자+점 형식도 주요 섹션
   - **❌ 제외: "< 본문 1 >", "< 본문 2 >" 같은 양식 구분자**는 목차가 아님
   - **❌ 제외: "작성요령", "작성 요령", "기재요령" 섹션**
   - 각 섹션은 실제로 서술해야 할 내용을 요구하는 항목이어야 함

3. **계층 구조:**
   - **주요 섹션 (main)**: "1.", "2.", "3." 또는 □, ■, ●
   - **하위 섹션 (sub)**: "1)", "2)", "3)" 또는 "가)", "나)", "다)" 또는 ￭, ▪, ▫
   - **예시:**
     ```
     1. 연구개발과제의 목표 및 내용  ← main
        1) 연구개발과제의 목표        ← sub
        2) 연구개발과제의 내용        ← sub
     2. 연구개발성과의 활용방안      ← main
        1) 활용방안                   ← sub
     ```

4. **JSON 형식을 반드시 지키고, 섹션은 최소 10개 이상 출력하세요.**
"""

    if skeleton_json:
        system_prompt += "\n\n⚠️ 매우 중요: 제공된 스켈레톤을 참고하되, 중복이나 잘못된 계층 구조가 있으면 수정하세요. 스켈레톤의 number/title을 기반으로 하되, description을 추가하고 필요시 계층을 조정하세요."
    else:
        system_prompt += "\n\n⚠️ 매우 중요: 스켈레톤이 제공되지 않았습니다. 텍스트에서 □, ■, ●로 시작하는 본문 작성 섹션만 추출하세요. 폼 입력 필드(기업명, 대표자, 연락처, mail, 팩스, 휴대전화 등)는 절대 포함하지 마세요."

    if section_contexts:
        system_prompt += "\n\n⚠️ 중요: '섹션별 본문 발췌'에 제공된 텍스트는 각 □ 섹션의 시작부터 다음 □ 섹션 직전까지의 실제 원문입니다. 이 텍스트를 사람처럼 읽어서 해당 구간에서 요구하는 하위 항목(￭, 1), (가) 등)을 추출하고, 섹션의 실제 내용을 파악하여 목차를 구성하세요."

    # detected_outline 생성
    def summarize_sections(sections: List[Dict], label: str, limit: int = 10) -> str:
        if not sections:
            return f"- {label}: 감지되지 않음"
        lines = [f"- {label} (상위 {min(len(sections), limit)}개)"]
        for sec in sections[:limit]:
            lines.append(f"  • {sec.get('number', '-')}: {sec.get('title', '')}")
        if len(sections) > limit:
            lines.append(f"  • ... 외 {len(sections) - limit}개")
        return '\n'.join(lines)

    detected_outline = '\n'.join([
        summarize_sections(table_sections, "표 기반 후보"),
        summarize_sections(symbol_sections, "기호/패턴 기반 후보")
    ])

    user_prompt_parts = [
        f"""## 템플릿 정보
- 파일명: {template['file_name']}
- 페이지 수: {template_doc.get('page_count', '?')}
- 표 수: {len(tables)}""",
        f"""## 사전 감지된 목차 후보 (참고용)
{detected_outline}""",
        f"""## 목차 텍스트 (키워드/패턴 기반)
{template_text}""",
        f"""## 첨부 양식 텍스트 (page_texts 또는 청크)
{chunk_context}"""
    ]

    if skeleton_json:
        user_prompt_parts.append(f"""## 강제 목차 스켈레톤 (number/title을 그대로 사용)
{skeleton_json}""")

    if section_contexts:
        MAX_CONTEXT_SECTIONS = 20
        trimmed_contexts = []
        for ctx in section_contexts:
            excerpt = ctx.get('excerpt', '').strip()
            if not excerpt:
                continue
            trimmed_contexts.append({
                'number': ctx['number'],
                'title': ctx['title'],
                'excerpt': excerpt[:600]
            })
            if len(trimmed_contexts) >= MAX_CONTEXT_SECTIONS:
                break

        if trimmed_contexts:
            context_json = json.dumps(trimmed_contexts, ensure_ascii=False, indent=2)
            user_prompt_parts.append(f"""## 섹션별 본문 발췌 (상위 {len(trimmed_contexts)}개)
⚠️ 중요: 아래 각 섹션의 "excerpt"는 해당 □ 섹션의 시작부터 다음 □ 섹션 직전까지의 실제 원문 텍스트입니다.
이 텍스트를 읽어서 해당 구간에서 요구하는 하위 항목(￭, 1), (가) 등)과 실제 작성 내용을 파악하세요.

{context_json}""")

    user_prompt_parts.append("""---
📋 요구 사항:

1. **폼 입력 필드는 절대 포함하지 마세요:**
   - ❌ 제외: "기업명", "대표자", "연락처", "주소", "전화", "팩스", "mail", "휴대전화", "생년월일", "성별", "직위", "부서", "E-mail" 등
   - ❌ 제외: "1)기업현황", "2)대표자", "3)실무책임자" 같은 폼 섹션 번호
   - ✅ 포함: "□ 기업현황", "□ 대표자 및 경영진 현황", "□ 목표" 같은 본문 작성 섹션

2. **양식 구분자 및 작성요령 제외:**
   - ❌ 제외: "< 본문 1 >", "< 본문 2 >" (이것은 양식의 구분자일 뿐, 목차 항목이 아님)
   - ❌ 제외: "작성요령", "작성 요령", "기재요령" 섹션

3. **계층 구조 명확히:**
   - "1."로 시작하면 주요 섹션 (number: "1", "2", "3" ...)
   - "1)"로 시작하면 하위 섹션 (number: "1.1", "1.2" ...)
   - "가)"로 시작하면 하위 섹션 (number: "1.1.1", "1.2.1" ...)
   - **중복 제거**: 같은 제목이 여러 번 나오면 하나만 포함

4. **"섹션별 본문 발췌" 활용:**
   - 제공된 경우, 각 섹션의 excerpt 텍스트를 반드시 읽어서 description 작성
   - excerpt에서 하위 항목(1), 2), 가), 나) 등)을 확인하여 정확한 계층 구조 생성

5. **각 항목에 포함할 정보:**
   - number: 계층 구조를 반영한 번호 ("1", "1.1", "1.1.1" 형식)
   - title: 섹션 제목 (기호 제거, 예: "□ 기업현황" → "기업현황")
   - description: 해당 섹션에서 요구하는 작성 내용 요약 (1-2문장)

6. **출력 형식 (JSON):**
{
  "sections": [
    {
      "number": "1",
      "title": "연구개발과제의 필요성",
      "description": "연구개발과제와 관련되는 국내외 현황 및 문제점, 전망, 필요성"
    },
    {
      "number": "2",
      "title": "연구개발과제의 목표 및 내용",
      "description": "연구개발 목표, 내용, 수행일정 및 결과물"
    },
    {
      "number": "2.1",
      "title": "연구개발과제의 목표",
      "description": "연구개발하고자 하는 지식, 기술의 정성적/정량적 목표"
    }
  ]
}""")

    user_prompt = "\n\n".join(user_prompt_parts)

    return system_prompt, user_prompt


def process_llm_response(
    llm_sections: List[Dict],
    base_sections: List[Dict],
    template: Dict
) -> Dict:
    """
    LLM 응답을 base_sections와 병합하여 최종 목차 생성

    주요 개선사항:
    1. 폼 필드 필터링을 항상 실행 (base_sections 유무와 관계없이)
    2. 페이지 번호 패턴 제외 ("- 10 -" 같은 패턴)
    3. 표 내용 패턴 제외 ("TO BE >", "AS IS" 등)
    4. 중복 제거 (같은 title이 여러 번 나오면 첫 번째만 유지)
    5. Description 길이 제한 (최대 200자)
    """
    # 🔧 개선 1: 폼 필드 및 제외 키워드 정의 (항상 적용)
    form_field_keywords = [
        'mail', 'e-mail', '이메일', '팩스', '휴대전화', '전화', '주소',
        '생년월일', '성별', '직위', '부서', '과제명', '기관명', '사업비',
        '대표자', '실무책임자', '연락처', '담당자'
    ]

    # 페이지 번호 패턴
    page_number_pattern = re.compile(r'^-\s*\d+\s*-$')

    # 표 내용 패턴
    table_content_keywords = ['TO BE', 'AS IS', 'IS TO', 'BE 기대효과', '⇨']

    # 예시/샘플 패턴
    example_keywords = ['홍길동', 'OO천원', '예시', '샘플', '작성예']

    # 체크박스 반복 항목 (성과지표 관련)
    checkbox_duplicates = ['투입', '과정', '산출', '결과']

    if base_sections:
        # base_sections가 있으면 LLM 결과와 병합
        llm_map = {sec.get('number'): sec for sec in llm_sections}
        raw_sections = []

        for base in base_sections:
            llm_candidate = llm_map.get(base['number'], {})
            description = llm_candidate.get('description') or base.get('excerpt', '')

            if not isinstance(description, str):
                description = str(description) if description is not None else ''

            # 🔧 개선 5: Description 길이 제한 (최대 200자)
            if len(description) > 200:
                description = description[:197] + '...'

            merged = {
                'number': base['number'],
                'title': base['title'],
                'description': description.strip()
            }
            raw_sections.append(merged)
    else:
        # base_sections가 없으면 LLM 결과를 그대로 사용
        raw_sections = llm_sections

    # 🔧 개선 1-4: 모든 섹션에 대해 필터링 적용
    final_sections = []
    seen_titles = set()  # 중복 체크용
    checkbox_count = {}  # 체크박스 항목 카운트

    for sec in raw_sections:
        original_title = sec.get('title', '')
        title_lower = original_title.lower()

        # 🔧 필터 1: 폼 필드 키워드 체크
        if any(keyword in title_lower for keyword in form_field_keywords):
            continue

        # 🔧 필터 2: 페이지 번호 패턴 체크 ("- 10 -" 같은 패턴)
        if page_number_pattern.match(original_title.strip()):
            continue

        # 🔧 필터 3: 표 내용 패턴 체크
        if any(keyword in original_title for keyword in table_content_keywords):
            continue

        # 🔧 필터 4: 예시/샘플 패턴 체크
        if any(keyword in original_title for keyword in example_keywords):
            continue

        # 🔧 필터 5: 체크박스 중복 항목 제한 (최대 2번까지만)
        if original_title in checkbox_duplicates:
            checkbox_count[original_title] = checkbox_count.get(original_title, 0) + 1
            if checkbox_count[original_title] > 2:
                continue

        # 🔧 필터 6: 중복 제거 (같은 title이 여러 번 나오면 첫 번째만 유지)
        if original_title in seen_titles:
            continue

        seen_titles.add(original_title)

        # Description 길이 제한 적용 (base_sections가 없는 경우에도)
        description = sec.get('description', '')
        if len(description) > 200:
            description = description[:197] + '...'

        final_sections.append({
            'number': sec.get('number', ''),
            'title': original_title,
            'description': description
        })

    if not final_sections:
        print(f"    ⚠️  필터링 후 섹션이 없음")
        raise ValueError("유효한 섹션이 없습니다.")

    toc = {
        'source': 'template',
        'source_file': template['file_name'],
        'extraction_method': 'llm_template_chunks',
        'sections': final_sections,
        'total_sections': len(final_sections),
        'has_page_numbers': False,
        'extracted_at': datetime.now().isoformat()
    }

    return toc
