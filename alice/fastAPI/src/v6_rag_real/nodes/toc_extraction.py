"""
목차(Table of Contents) 추출 모듈
제안서 양식 또는 공고문/첨부서류에서 목차 구조 추출

핵심 노드 함수만 포함 (유틸리티 함수는 toc_util.py 참조)
"""

import json
import re
import unicodedata
from datetime import datetime
from typing import List, Dict

from ..state_types import BatchState
from .toc_util import (
    find_proposal_template,
    find_toc_table,
    parse_toc_table,
    extract_sections_from_symbols,
    create_default_toc,
    client  # OpenAI 클라이언트는 toc_util.py에서 초기화
)


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


def extract_subsections_from_range(
    lines_block: List[str],
    parent_number: str,
    base_line_index: int,
    end_line_index: int,
    start_counter: int = 1
) -> List[Dict]:
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
                    'required': True,
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


def route_toc_extraction(state: BatchState) -> str:
    """
    목차 추출 방법 결정 (조건부 라우팅)
    
    LangGraph에서 사용하는 라우팅 함수로, 양식이 있는지 확인하여
    적절한 목차 추출 방법을 선택합니다.
    
    동작 방식:
    1. state에서 attachment_templates를 가져옴
    2. 제안서 양식이 있는지 확인 (find_proposal_template)
    3. 양식이 있으면 → "extract_toc_from_template" 반환
    4. 양식이 없으면 → "extract_toc_from_announcement_and_attachments" 반환
    
    Args:
        state: BatchState - 현재 처리 중인 배치 상태
        
    Returns:
        str: 다음에 실행할 노드 이름
        - "extract_toc_from_template": 양식에서 목차 추출
        - "extract_toc_from_announcement_and_attachments": 공고+첨부서류에서 목차 유추
    """
    templates = state.get('attachment_templates', [])
    proposal_template = find_proposal_template(templates)

    if proposal_template:
        return "extract_toc_from_template"
    else:
        return "extract_toc_from_announcement_and_attachments"


def extract_toc_from_template(state: BatchState) -> BatchState:
    """
    제안서 양식에서 목차 추출 (청킹 + 패턴 힌트 + LLM 단일 경로)
    """
    print(f"\n{'='*60}")
    print(f"📑 양식에서 목차 추출")
    print(f"{'='*60}")

    # 양식 찾기
    templates = state.get('attachment_templates', [])
    template = find_proposal_template(templates)

    # [Fallback] detect_templates 노드가 놓친 경우를 위한 긴급 복구 로직
    # 정상적으로는 detect_templates에서 양식을 감지하지만,
    # 신뢰도가 낮아 누락된 경우 파일명 키워드로 최종 시도
    if not template:
        documents = state.get('documents', [])
        attachment_docs = [d for d in documents if d.get('folder') == 2]

        for att_doc in attachment_docs:
            file_name = att_doc.get('file_name', '')
            # 신청서, 계획서, 제안서 키워드가 있으면 강제로 시도
            if any(kw in file_name for kw in ['신청서', '계획서', '제안서', '양식']):
                print(f"\n  ⚠️  양식 감지 누락 → 파일명 기반 복구 시도: {file_name}")
                # 임시 템플릿 정보 생성
                template = {
                    'file_name': file_name,
                    'tables': att_doc.get('tables', []),
                    'confidence_score': 0.5,  # 낮은 신뢰도로 표시
                    'has_template': False  # 감지는 안 되었지만 시도
                }
                break

        if not template:
            print(f"\n  ⚠️  양식을 찾을 수 없음 → 기본 템플릿 사용")
            state['table_of_contents'] = create_default_toc()
            state['status'] = 'toc_extracted'
            return state

    print(f"\n  📋 양식: {template['file_name']}")

    tables = template.get('tables', [])

    # 양식 문서 텍스트 가져오기
    documents = state.get('documents', [])
    template_file_name = unicodedata.normalize('NFC', template['file_name'])
    template_doc = None
    
    for doc in documents:
        doc_file_name = unicodedata.normalize('NFC', doc.get('file_name', ''))
        if doc_file_name == template_file_name:
            template_doc = doc
            break
    
    # template에 tables가 없으면 documents에서 가져오기
    if not template.get('tables') and template_doc:
        template['tables'] = template_doc.get('tables', [])
    
    if not template_doc or not template_doc.get('full_text'):
        print(f"  ✗ 양식 텍스트 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    full_text = template_doc.get('full_text', '')
    if not full_text:
        print(f"  ✗ 양식 텍스트 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    print(f"  🤖 페이지 기반 LLM 추출 시작 (템플릿 전용)")

    # [2025-11-19 개선] page_texts 우선 사용 → all_chunks 대비 구조 보존 우수
    # page_texts는 페이지별 원본 텍스트를 보존하므로 목차 패턴 인식에 유리
    # all_chunks는 이미 섹션별로 분할된 조각이라 전체 구조 파악이 어려움
    page_texts = template_doc.get('page_texts', {})
    chunk_context = ""

    if page_texts:
        # page_texts 사용 (권장): 원본 페이지 구조 보존
        print(f"    ✅ page_texts 사용: {len(page_texts)}개 페이지")

        # 페이지 번호 순으로 정렬하여 텍스트 결합
        sorted_pages = sorted(page_texts.items(), key=lambda x: x[0])
        page_context_parts = []

        # 최대 20페이지까지 사용 (토큰 절약)
        MAX_PAGES = 20
        for page_num, page_text in sorted_pages[:MAX_PAGES]:
            # 각 페이지당 최대 1500자까지 사용 (목차 추출에 충분)
            text_snippet = page_text[:1500]
            page_context_parts.append(f"[페이지 {page_num}]\n{text_snippet}")

        chunk_context = '\n\n'.join(page_context_parts)
        print(f"    📄 페이지 텍스트 길이: {len(chunk_context):,}자 (최대 {MAX_PAGES}페이지)")

    # Fallback: page_texts가 없으면 all_chunks 사용
    if not chunk_context:
        print(f"    ⚠️  page_texts 없음 → all_chunks fallback 시도")
        all_chunks = state.get('all_chunks', [])
        template_chunks = []
        template_file_name_nfc = unicodedata.normalize('NFC', template['file_name'])

        if all_chunks:
            for chunk in all_chunks:
                chunk_file = unicodedata.normalize('NFC', chunk.get('file_name', ''))
                if chunk_file == template_file_name_nfc:
                    template_chunks.append(chunk)

        # 페이지 순으로 정렬
        template_chunks.sort(key=lambda c: (c.get('page', 0) or 0, c.get('chunk_id', '')))

        # 상위 20개 청크만 사용하여 토큰 절약
        MAX_TEMPLATE_CHUNKS = 20
        chunk_context_parts = []
        for chunk in template_chunks[:MAX_TEMPLATE_CHUNKS]:
            page = chunk.get('page', '?')
            section = chunk.get('section', '섹션')
            text_snippet = chunk.get('text', '')[:800]
            chunk_context_parts.append(
                f"[페이지 {page} | {section}]\n{text_snippet}"
            )

        chunk_context = '\n\n'.join(chunk_context_parts)
        print(f"    📦 청크 텍스트 길이: {len(chunk_context):,}자 ({len(template_chunks)}개 청크)")

    # 최종 fallback: full_text 일부 사용
    if not chunk_context:
        chunk_context = full_text[:5000]
        if chunk_context:
            print(f"    ⚠️  청크 없음 → full_text 일부 사용 (길이 {len(chunk_context):,}자)")
        else:
            print(f"    ✗ 텍스트 컨텍스트 확보 실패 → 기본 템플릿 사용")
            state['table_of_contents'] = create_default_toc()
            state['status'] = 'toc_extracted'
            return state
    
    # 패턴 감지 결과 (LLM에 참고로 제공, 스켈레톤 생성에도 활용)
    toc_table = find_toc_table(tables) if tables else None
    table_sections = parse_toc_table(toc_table['data']) if toc_table else []
    
    # full_text에서 [페이지 X] 마커 제거 (extract_sections_from_symbols용)
    clean_full_text = re.sub(r'\[페이지 \d+\]', '', template_doc['full_text'])
    symbol_sections = extract_sections_from_symbols(clean_full_text)
    full_lines = full_text.split('\n')
    
    # 디버깅: symbol_sections 추출 결과 확인
    print(f"    🔍 패턴 기반 섹션 추출: {len(symbol_sections)}개")
    if symbol_sections:
        print(f"    📋 추출된 섹션 (첫 5개):")
        for sec in symbol_sections[:5]:
            print(f"      • {sec.get('number', '')} {sec.get('title', '')} (level: {sec.get('level', 'unknown')})")
    else:
        print(f"    ⚠️  패턴 기반 섹션 추출 실패 - LLM이 전체 텍스트에서 추출 시도")

    base_sections: List[Dict] = []
    section_contexts: List[Dict] = []
    total_lines = len(full_lines)
    main_sections = [sec for sec in symbol_sections if sec.get('level') == 'main']

    if main_sections:
        for main in main_sections:
            start_line = main.get('line_index', 0)
            end_line = main.get('next_line_index', total_lines)
            block_lines = full_lines[start_line:end_line]
            block_text = '\n'.join(block_lines).strip()

            main_entry = {
                'number': main['number'],
                'title': main['title'],
                'required': True,
                'level': 'main',
                'parent_number': None,
                'line_index': start_line,
                'next_line_index': end_line
            }
            if block_text:
                main_entry['excerpt'] = block_text[:800]
                section_contexts.append({
                    'number': main_entry['number'],
                    'title': main_entry['title'],
                    'excerpt': main_entry['excerpt']
                })
            base_sections.append(main_entry)

            subs = [
                sec for sec in symbol_sections
                if sec.get('level') == 'sub' and sec.get('parent_number') == main['number']
            ]
            if subs:
                subs.sort(key=lambda s: s.get('line_index', 0))
                for sub in subs:
                    sub_start = sub.get('line_index', start_line)
                    sub_end = sub.get('next_line_index', end_line)
                    sub_text = '\n'.join(full_lines[sub_start:sub_end]).strip()
                    sub_entry = {
                        'number': sub['number'],
                        'title': sub['title'],
                        'required': True,
                        'level': 'sub',
                        'parent_number': main_entry['number'],
                        'line_index': sub_start,
                        'next_line_index': sub_end
                    }
                    if sub_text:
                        sub_entry['excerpt'] = sub_text[:600]
                        section_contexts.append({
                            'number': sub_entry['number'],
                            'title': sub_entry['title'],
                            'excerpt': sub_entry['excerpt']
                        })
                    base_sections.append(sub_entry)
            else:
                sub_candidates = extract_subsections_from_range(
                    block_lines,
                    main['number'],
                    start_line,
                    end_line
                )
                for sub in sub_candidates:
                    sub_start = sub.get('line_index', start_line)
                    sub_end = sub.get('next_line_index', end_line)
                    sub_text = '\n'.join(full_lines[sub_start:sub_end]).strip()
                    sub_entry = {
                        'number': sub['number'],
                        'title': sub['title'],
                        'required': True,
                        'level': 'sub',
                        'parent_number': main_entry['number'],
                        'line_index': sub_start,
                        'next_line_index': sub_end
                    }
                    if sub_text:
                        sub_entry['excerpt'] = sub_text[:600]
                        section_contexts.append({
                            'number': sub_entry['number'],
                            'title': sub_entry['title'],
                            'excerpt': sub_entry['excerpt']
                        })
                    base_sections.append(sub_entry)

    skeleton_payload = [
        {'number': sec['number'], 'title': sec['title'], 'required': sec.get('required', True)}
        for sec in base_sections
    ]
    skeleton_json = json.dumps(skeleton_payload, ensure_ascii=False, indent=2) if base_sections else ""
    
    # [2025-11-19 개선] 섹션 추출 상세 디버깅
    print(f"\n    🔍 섹션 추출 결과 상세:")
    print(f"    📊 base_sections: {len(base_sections)}개")
    print(f"    📝 section_contexts (본문 발췌): {len(section_contexts)}개")

    # base_sections가 비어있으면 경고
    if not base_sections:
        print(f"    ⚠️  경고: base_sections가 비어있습니다. LLM이 전체 텍스트에서 추출 시도 (폼 필드 포함 가능)")
    else:
        # 첫 10개 섹션 출력 (기존 5개 → 10개로 확대하여 더 많은 패턴 확인)
        print(f"    📋 추출된 섹션 (첫 10개):")
        for idx, sec in enumerate(base_sections[:10], 1):
            level_icon = "■" if sec.get('level') == 'main' else "  ○"
            print(f"      {level_icon} [{idx}] {sec.get('number', '')} {sec.get('title', '')}")

        # 전체 섹션 레벨 분포 확인
        main_count = sum(1 for sec in base_sections if sec.get('level') == 'main')
        sub_count = sum(1 for sec in base_sections if sec.get('level') == 'sub')
        print(f"    📈 레벨 분포: main={main_count}개, sub={sub_count}개")

    # 섹션별 본문 발췌 샘플
    if section_contexts:
        print(f"\n    📄 섹션 본문 발췌 샘플 (첫 3개):")
        for ctx in section_contexts[:3]:
            excerpt_preview = ctx.get('excerpt', '')[:80]
            print(f"      • {ctx.get('number', '')} {ctx.get('title', '')}")
            print(f"        └─ {excerpt_preview}...")
    
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
    
    # 🔍 텍스트 기반 목차 섹션 추출 (기존 LLM 폴백 로직 통합)
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

    if not template_text:
        template_text = chunk_context

    system_prompt = """당신은 정부 지원사업 신청서/제안서 양식을 분석하여 실제 작성해야 하는 본문 목차를 정리하는 전문가입니다.

⚠️ 중요 규칙:
1. **폼 입력 필드는 절대 목차로 포함하지 마세요:**
   - ❌ 제외: "기업명", "대표자", "연락처", "주소", "전화", "팩스", "mail", "휴대전화", "생년월일", "성별", "직위", "부서" 등
   - ❌ 제외: "1)기업현황", "2)대표자", "3)실무책임자" 같은 폼 섹션 번호
   - ✅ 포함: "□ 기업현황", "□ 대표자 및 경영진 현황", "□ 목표" 같은 본문 작성 섹션

2. **본문 작성 항목만 목차로 추출:**
   - □, ■, ￭로 시작하는 섹션만 추출
   - 각 섹션은 실제로 서술해야 할 내용을 요구하는 항목이어야 함

3. **계층 구조:**
   - □, ■, ●는 주요 섹션 (1, 2, 3...)
   - ￭, ▪, ▫, 1), (가) 등은 하위 섹션 (1.1, 1.2...)

4. **JSON 형식을 반드시 지키고, 섹션은 최소 10개 이상 출력하세요.**
"""
    if skeleton_json:
        system_prompt += "\n\n⚠️ 매우 중요: 제공된 스켈레톤의 number/title 순서를 반드시 그대로 유지하고, 스켈레톤에 없는 섹션은 추가하지 마세요. 스켈레톤에 있는 섹션만 목차로 반환하세요."
    else:
        system_prompt += "\n\n⚠️ 매우 중요: 스켈레톤이 제공되지 않았습니다. 텍스트에서 □, ■, ●로 시작하는 본문 작성 섹션만 추출하세요. 폼 입력 필드(기업명, 대표자, 연락처, mail, 팩스, 휴대전화 등)는 절대 포함하지 마세요."
    
    if section_contexts:
        system_prompt += "\n\n⚠️ 중요: '섹션별 본문 발췌'에 제공된 텍스트는 각 □ 섹션의 시작부터 다음 □ 섹션 직전까지의 실제 원문입니다. 이 텍스트를 사람처럼 읽어서 해당 구간에서 요구하는 하위 항목(￭, 1), (가) 등)을 추출하고, 섹션의 실제 내용을 파악하여 목차를 구성하세요."

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
요구 사항:
1. **폼 입력 필드는 절대 포함하지 마세요:**
   - ❌ 제외: "기업명", "대표자", "연락처", "주소", "전화", "팩스", "mail", "휴대전화", "생년월일", "성별", "직위", "부서", "E-mail" 등
   - ❌ 제외: "1)기업현황", "2)대표자", "3)실무책임자" 같은 폼 섹션 번호
   - ✅ 포함: "□ 기업현황", "□ 대표자 및 경영진 현황", "□ 목표" 같은 본문 작성 섹션

2. 상기 텍스트에서 본문 작성 항목만 추출하여 목차를 생성하세요.

3. "섹션별 본문 발췌"가 제공된 경우, 각 섹션의 excerpt 텍스트를 반드시 읽어서 해당 구간의 실제 내용과 하위 항목을 파악하세요.

4. 계층 구조는 "1 → 1.1 → 1.1.1" 형식을 사용하세요.

5. 각 항목에 'required' 여부와 간단한 설명을 포함하세요.

6. 출력 형식은 아래 JSON 스키마를 따르세요:
{
  "sections": [
    {
      "number": "1",
      "title": "사업 개요",
      "required": true,
      "description": "사업 추진 배경과 목적"
    }
  ]
}""")

    user_prompt = "\n\n".join(user_prompt_parts)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("LLM 응답이 비어 있습니다.")
        
        result = json.loads(content)
        sections = result.get('sections', [])
        
        if not sections:
            raise ValueError("LLM 결과에 sections가 없습니다.")
        
        if base_sections:
            llm_map = {sec.get('number'): sec for sec in sections}
            final_sections = []
            for base in base_sections:
                llm_candidate = llm_map.get(base['number'], {})
                description = llm_candidate.get('description') or base.get('excerpt', '')
                if not isinstance(description, str):
                    description = str(description) if description is not None else ''
                merged = {
                    'number': base['number'],
                    'title': base['title'],
                    'required': llm_candidate.get('required', base.get('required', True)),
                    'description': description.strip()
                }
                final_sections.append(merged)
        else:
            # base_sections가 비어있을 때 폼 필드 필터링
            # ========================================
            # [2025-11-19 수정] 폼 필드 키워드 중복 제거 및 로직 개선
            # - 'E-mail' 중복 제거
            # - 필터링 로직 단순화 (원본 제목 기준으로 체크)
            # ========================================
            form_field_keywords = ['mail', 'e-mail', '이메일', '팩스', '휴대전화', '전화', '주소', '생년월일', '성별', '직위', '부서']
            final_sections = []
            for sec in sections:
                original_title = sec.get('title', '')
                title_lower = original_title.lower()

                # 1. 폼 필드 키워드가 제목에 포함되어 있으면 제외
                if any(keyword in title_lower for keyword in form_field_keywords):
                    continue

                # 2. □, ■, ● 등의 마커가 제목에 포함되어 있는지 확인
                has_marker = any(marker in original_title for marker in ['□', '■', '●', '○'])

                # 마커가 없으면 제외 (폼 필드일 가능성)
                if not has_marker:
                    continue

                final_sections.append(sec)
            
            if not final_sections:
                print(f"    ⚠️  폼 필드 필터링 후 섹션이 없음 → 기본 템플릿 사용")
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
        
        state['table_of_contents'] = toc
        state['status'] = 'toc_extracted'
        
        print(f"\n  ✅ 청킹 기반 LLM 추출 완료: {len(final_sections)}개 섹션")
        for sec in final_sections[:5]:
            print(f"    • {sec.get('number', '')} {sec.get('title', '')}")
        if len(final_sections) > 5:
            print(f"    ... 외 {len(final_sections) - 5}개")
        
        return state
    
    except Exception as e:
        print(f"  ✗ 청킹 기반 LLM 추출 실패: {e} → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'

    return state


def extract_toc_from_announcement_and_attachments(state: BatchState) -> BatchState:
    """
    공고문 + 모든 첨부서류에서 목차 유추 (RAG + LLM) - LangGraph 노드
    
    ⚠️ 양식 파일이 없는 경우 사용되는 함수입니다.
    공고문과 첨부서류를 분석하여 제출해야 할 계획서의 목차를 유추합니다.
    
    🔍 추출 과정:
    1. 제출서류 feature 찾기
       - 공고문에서 "제출서류" 섹션 추출
       - 어떤 서류를 제출해야 하는지 확인
       
    2. RAG 검색 (Retrieval-Augmented Generation)
       - 벡터 DB에서 관련 청크 검색
       - 검색어: "제출서류 작성항목 구성 목차 제안서 계획서..."
       - 공고문 + 모든 첨부서류에서 검색 (25개 청크)
       
    3. LLM으로 목차 생성
       - 검색된 컨텍스트와 공고문 내용을 GPT에 제공
       - 공고 유형별 표준 목차 구조 참고
       - 실제 공고 내용을 반영한 목차 생성
       
    📋 생성되는 목차:
    - 연구개발(R&D) 과제: 연구계획서 목차
    - 창업지원 사업: 사업계획서 목차
    - 주관기관 선정: 주관기관 사업계획서 목차
    - 기타 지원사업: 해당 사업의 계획서 목차
    
    Args:
        state: BatchState - 현재 처리 중인 배치 상태
        
    Returns:
        BatchState: table_of_contents 필드가 업데이트된 상태
        - 성공 시: LLM이 생성한 목차 구조
        - 실패 시: 기본 템플릿 목차 사용
    """
    print(f"\n{'='*60}")
    print(f"📑 공고문 + 첨부서류 기반 목차 유추")
    print(f"{'='*60}")

    all_features = state.get('extracted_features', [])
    collection = state.get('chroma_collection')
    
    if not collection:
        print(f"\n  ⚠️  'chroma_collection' 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    # 1️⃣ 제출서류 feature 찾기
    submission_features = [
        f for f in all_features
        if isinstance(f, dict) and f.get('feature_code') == 'submission_docs'
    ]

    if not submission_features:
        print(f"\n  ⚠️  '제출서류' feature 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    submission_content = '\n\n'.join([
        f.get('full_content', '') for f in submission_features
    ])

    # 2️⃣ RAG로 모든 문서(공고+첨부) 검색 (볼륨 증가를 위해 검색 결과 확대)
    try:
        # OpenAI API로 쿼리 임베딩 생성 (processing.py의 extract_features_rag와 동일한 방식)
        query_text = "제출서류 작성항목 구성 목차 제안서 계획서 사업계획서 운영계획"
        query_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[query_text]
        )
        query_embedding = [query_response.data[0].embedding]

        # ✅ 모든 문서에서 검색 (ATTACHMENT 필터 제거)
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=25  # 15 → 25로 증가: 더 많은 컨텍스트 확보
            # where 조건 제거 → 공고문 + 모든 첨부서류 검색
        )

        all_chunks = []
        if results and results.get('ids') and results['ids'][0]:
            ids = results['ids'][0]
            documents = results.get('documents', [[]])[0] if results.get('documents') else []
            metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []
            
            for i in range(len(ids)):
                if i < len(documents) and i < len(metadatas):
                    metadata = metadatas[i] if isinstance(metadatas[i], dict) else {}
                    all_chunks.append({
                        'text': documents[i] if i < len(documents) else '',
                        'file': metadata.get('file_name', 'UNKNOWN'),
                        'section': metadata.get('section', 'UNKNOWN'),
                        'doc_type': metadata.get('document_type', 'UNKNOWN')
                    })
            print(f"    ✅ RAG 검색 완료: {len(all_chunks)}개 청크 (공고 + 첨부서류)")
    except Exception as e:
        print(f"    ✗ RAG 검색 실패: {e}")
        all_chunks = []

    # 3️⃣ LLM으로 목차 생성
    print(f"    🤖 LLM으로 목차 구조 생성 중...")

    # 문서 타입별로 정리 (더 많은 컨텍스트 활용)
    document_context = '\n\n'.join([
        f"[{c['doc_type']} - {c['file']} - {c['section']}]\n{c['text']}"
        for c in all_chunks[:20]  # 10 → 20으로 증가: 더 풍부한 컨텍스트 제공
    ])

    system_prompt = """당신은 정부 지원사업 공고 분석 전문가입니다.

공고문과 첨부서류를 분석하여 **신청 시 제출해야 하는 계획서의 작성 항목(목차)**를 추출하세요.

⚠️ 중요: 공고의 성격을 먼저 파악하세요:
- 연구개발(R&D) 과제 공고 → 연구계획서 목차
- 창업지원 사업 공고 → 사업계획서 목차
- 주관기관 선정 공고 → 주관기관 사업계획서 목차
- 기타 지원사업 공고 → 해당 사업의 계획서 목차

⚠️ 다음을 구분해야 합니다:
- ❌ 제출 서류명 (예: "연구계획서", "신청서", "동의서") → 포함하지 마세요
- ✅ 작성 항목/목차 (예: "사업 추진계획", "운영 전략", "예산 편성") → 이것만 포함하세요

📋 목차 생성 요구사항:
1. **최소 10-15개 이상의 섹션을 생성**하세요 (너무 적으면 안 됩니다)
2. **계층 구조를 포함**하세요 (1, 1.1, 1.2, 2, 2.1, 2.2 등)
3. 공고의 성격에 맞는 **표준 목차 구조**를 참고하되, 실제 공고 내용을 반영하세요

📚 공고 유형별 표준 목차 구조 참고:

【연구개발(R&D) 과제】
1. 연구개발과제의 개요 (필수)
   1.1. 과제의 필요성
   1.2. 과제의 목표
2. 연구개발 목표 및 내용 (필수)
   2.1. 연구개발 목표
   2.2. 연구개발 내용
   2.3. 기술적 해결과제
3. 연구개발 추진체계 및 일정 (필수)
   3.1. 추진체계
   3.2. 연구일정
   3.3. 인력운용계획
4. 연구개발 성과 활용방안 (필수)
   4.1. 기대효과
   4.2. 활용방안
5. 소요예산 및 자금계획 (필수)
   5.1. 예산계획
   5.2. 자금조달계획

【창업지원/사업계획서】
1. 사업 개요 (필수)
   1.1. 사업 배경 및 필요성
   1.2. 사업 목표
2. 사업 모델 (필수)
   2.1. 사업 아이템
   2.2. 사업 전략
3. 추진 계획 (필수)
   3.1. 운영 계획
   3.2. 마케팅 계획
4. 조직 및 인력 (필수)
   4.1. 조직 구성
   4.2. 인력 운영
5. 재무 계획 (필수)
   5.1. 매출 계획
   5.2. 자금 계획

【주관기관/운영기관 선정】
1. 기관 개요 (필수)
   1.1. 기관 현황
   1.2. 조직 구성
2. 운영 계획 (필수)
   2.1. 프로그램 기획
   2.2. 운영 전략
3. 추진 체계 (필수)
   3.1. 조직 체계
   3.2. 인력 운용
4. 예산 및 자금 계획 (필수)
   4.1. 예산 편성
   4.2. 자금 관리

다음 형식으로 JSON 반환:
{
  "sections": [
    {
      "number": "1",
      "title": "사업 추진 개요",
      "required": true,
      "description": "사업의 목적과 필요성"
    },
    {
      "number": "1.1",
      "title": "사업 배경 및 필요성",
      "required": true,
      "description": "사업을 추진하는 배경과 필요성"
    },
    {
      "number": "2",
      "title": "운영 계획 및 전략",
      "required": true,
      "description": "구체적인 운영 방안과 추진 전략"
    }
  ]
}

⚠️ 중요 주의사항:
- 제출 서류의 "이름"이 아닌, 서류 "내부의 작성 항목"을 추출하세요
- 공고의 실제 내용(연구개발/창업지원/주관기관선정 등)을 반영한 목차를 생성하세요
- 섹션 번호는 "1", "1.1", "1.2", "2", "가" 등 계층 구조 형식 유지
- required는 필수 작성 항목 여부
- **반드시 10개 이상의 섹션을 생성**하되, 공고 내용에 근거하여 생성하세요"""

    # 공고문 전체 내용 가져오기 (첨부파일이 없을 때 대비) - 컨텍스트 확대
    documents = state.get('documents', [])
    announcement_docs = [d for d in documents if d.get('document_type') == 'ANNOUNCEMENT']
    announcement_text = ''
    if announcement_docs:
        announcement_text = announcement_docs[0].get('text', '')[:5000]  # 3000 → 5000으로 증가

    submission_text_limit = submission_content[:3000]  # 2000 → 3000으로 증가
    document_context_limit = document_context[:4000] if document_context else '(첨부서류 없음)'  # 2000 → 4000으로 증가

    user_prompt = f"""## 공고문 내용

{announcement_text}

## 제출서류 요구사항

{submission_text_limit}

## 첨부서류 관련 내용 (양식/계획서의 작성 항목)

{document_context_limit}

---

## 📋 분석 및 목차 생성 지침

### 1단계: 공고 성격 파악
다음 중 해당하는 항목을 파악하세요:
- [ ] 연구개발(R&D) 과제 공고
- [ ] 창업지원/벤처 지원 사업 공고
- [ ] 주관기관/운영기관 선정 공고
- [ ] 기타 지원사업 공고

### 2단계: 목차 구조 생성
위에서 파악한 공고 성격에 맞는 표준 목차 구조를 참고하되, **공고문과 첨부서류에서 언급된 구체적인 작성 항목**을 반드시 반영하세요.

**⚠️ 반드시 준수할 사항:**
1. **최소 10-15개 이상의 섹션 생성** (계층 구조 포함 시 15-20개 이상)
2. **계층 구조 필수 포함**:
   - 1차 섹션: "1", "2", "3" 등
   - 2차 섹션: "1.1", "1.2", "2.1", "2.2" 등
   - 3차 섹션 (필요시): "1.1.1", "1.1.2" 등
3. **공고 내용 기반 생성**: 표준 구조를 참고하되, 공고문과 첨부서류에서 실제로 언급된 항목을 우선 반영
4. **"서류명"이 아닌 "작성 항목"만 추출**:
   - ❌ 잘못된 목차: ["사업계획서", "신청서", "동의서", "첨부자료"]
   - ✅ 올바른 목차: ["사업 추진 개요", "운영 계획", "예산 편성", "추진 체계"]

### 3단계: 구체적인 예시

**연구개발 과제 예시:**
```
1. 연구개발과제의 개요
   1.1. 과제의 필요성 및 배경
   1.2. 과제의 목표
   1.3. 기대효과
2. 연구개발 목표 및 내용
   2.1. 연구개발 목표
   2.2. 연구개발 내용
   2.3. 기술적 해결과제
   2.4. 핵심기술 요소
3. 연구개발 추진체계 및 일정
   3.1. 추진체계
   3.2. 연구일정 (Gantt 차트 포함)
   3.3. 인력운용계획
   3.4. 역할 분담
4. 연구개발 성과 활용방안
   4.1. 기대효과
   4.2. 활용방안
   4.3. 사업화 계획
5. 소요예산 및 자금계획
   5.1. 예산계획 (연도별)
   5.2. 자금조달계획
   5.3. 예산 집행 계획
```

**⚠️ 주의: 위 예시는 참고용이며, 실제 공고문과 첨부서류의 내용을 반영하여 생성하세요.**

위 내용을 종합적으로 분석하여 신청자가 작성해야 할 계획서의 **상세한 목차(최소 10-15개 섹션, 계층 구조 포함)**를 JSON 형식으로 생성해주세요."""

    try:
        import json
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        # JSON 파싱 (예외 처리)
        try:
            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM 응답 내용이 비어있음")
            result = json.loads(content)
        except (json.JSONDecodeError, ValueError, AttributeError, IndexError) as e:
            print(f"\n  ✗ LLM 응답 파싱 실패: {e} → 기본 템플릿 사용")
            state['table_of_contents'] = create_default_toc()
            state['status'] = 'toc_extracted'
            return state

        if result.get('sections'):
            toc = {
                'source': 'announcement',
                'extraction_method': 'rag_llm',
                'inference_confidence': 0.7,  # RAG + LLM 기반이므로 중간 신뢰도
                'sections': result['sections'],
                'total_sections': len(result['sections']),
                'extracted_at': datetime.now().isoformat()
            }

            state['table_of_contents'] = toc
            state['status'] = 'toc_extracted'

            print(f"\n  ✅ LLM으로 {len(result['sections'])}개 섹션 생성 완료")
            for sec in result['sections'][:5]:
                print(f"    • {sec.get('number', '')} {sec.get('title', '')}")
            if len(result['sections']) > 5:
                print(f"    ... 외 {len(result['sections']) - 5}개")

            return state
        else:
            print(f"\n  ✗ LLM 결과에 섹션 없음 → 기본 템플릿 사용")
            state['table_of_contents'] = create_default_toc()
            state['status'] = 'toc_extracted'
            return state

    except Exception as e:
        print(f"\n  ✗ LLM 호출 실패: {e} → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'
        return state
