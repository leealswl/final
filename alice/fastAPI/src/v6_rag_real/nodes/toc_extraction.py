"""
목차(Table of Contents) 추출 모듈
제안서 양식 또는 공고문/첨부서류에서 목차 구조 추출

핵심 노드 함수만 포함 (세부 로직은 하위 모듈 참조)
"""

import json
import re
import unicodedata

from ..state_types import BatchState
from .toc_util import (
    find_proposal_template,
    find_toc_table,
    parse_toc_table,
    extract_sections_from_symbols,
    create_default_toc,
    client
)
from .toc_template_extractor import (
    prepare_template_context,
    build_base_sections,
    extract_template_text,
    build_llm_prompt,
    process_llm_response
)
from .toc_announcement_extractor import (
    prepare_announcement_context,
    generate_toc_from_announcement
)


def route_toc_extraction(state: BatchState) -> str:
    """
    목차 추출 방법 결정 (조건부 라우팅)

    양식이 있으면 → "extract_toc_from_template"
    양식이 없으면 → "extract_toc_from_announcement_and_attachments"
    """
    templates = state.get('attachment_templates', [])
    proposal_template = find_proposal_template(templates)

    if proposal_template:
        return "extract_toc_from_template"
    else:
        return "extract_toc_from_announcement_and_attachments"


def extract_toc_from_template(state: BatchState) -> BatchState:
    """
    제안서 양식에서 목차 추출

    처리 흐름:
    1. 양식 찾기 (detect_templates 결과 또는 파일명 기반)
    2. 페이지/청크 컨텍스트 준비
    3. 패턴 기반 섹션 추출 (□, ■, ● 등)
    4. base_sections 생성 (섹션 사이 텍스트 추출)
    5. LLM 호출로 목차 상세화
    6. 결과 병합 및 필터링
    """
    print(f"\n{'='*60}")
    print(f"📑 양식에서 목차 추출")
    print(f"{'='*60}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣ 양식 찾기
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    templates = state.get('attachment_templates', [])
    template = find_proposal_template(templates)

    # Fallback: 파일명 기반 복구
    if not template:
        documents = state.get('documents', [])
        attachment_docs = [d for d in documents if d.get('folder') == 2]

        for att_doc in attachment_docs:
            file_name = att_doc.get('file_name', '')
            if any(kw in file_name for kw in ['신청서', '계획서', '제안서', '양식']):
                print(f"\n  ⚠️  양식 감지 누락 → 파일명 기반 복구 시도: {file_name}")
                template = {
                    'file_name': file_name,
                    'tables': att_doc.get('tables', []),
                    'confidence_score': 0.5,
                    'has_template': False
                }
                break

        if not template:
            print(f"\n  ⚠️  양식을 찾을 수 없음 → 기본 템플릿 사용")
            state['table_of_contents'] = create_default_toc()
            state['status'] = 'toc_extracted'
            return state

    print(f"\n  📋 양식: {template['file_name']}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2️⃣ 양식 문서 가져오기
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    documents = state.get('documents', [])
    template_file_name = unicodedata.normalize('NFC', template['file_name'])
    template_doc = None

    for doc in documents:
        doc_file_name = unicodedata.normalize('NFC', doc.get('file_name', ''))
        if doc_file_name == template_file_name:
            template_doc = doc
            break

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

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3️⃣ 컨텍스트 준비 (page_texts 또는 all_chunks)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    chunk_context = prepare_template_context(template_doc, state, template)

    if not chunk_context:
        print(f"    ✗ 텍스트 컨텍스트 확보 실패 → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4️⃣ 패턴 기반 섹션 추출
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    tables = template.get('tables', [])
    toc_table = find_toc_table(tables) if tables else None
    table_sections = parse_toc_table(toc_table['data']) if toc_table else []

    clean_full_text = re.sub(r'\[페이지 \d+\]', '', template_doc['full_text'])
    symbol_sections = extract_sections_from_symbols(clean_full_text)

    print(f"    🔍 패턴 기반 섹션 추출: {len(symbol_sections)}개")
    if symbol_sections:
        print(f"    📋 추출된 섹션 (첫 5개):")
        for sec in symbol_sections[:5]:
            print(f"      • {sec.get('number', '')} {sec.get('title', '')} (level: {sec.get('level', 'unknown')})")
    else:
        print(f"    ⚠️  패턴 기반 섹션 추출 실패 - LLM이 전체 텍스트에서 추출 시도")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5️⃣ base_sections 생성 (섹션 사이의 텍스트 추출)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    base_sections, section_contexts = build_base_sections(symbol_sections, full_text)

    print(f"\n    🔍 섹션 추출 결과 상세:")
    print(f"    📊 base_sections: {len(base_sections)}개")
    print(f"    📝 section_contexts (본문 발췌): {len(section_contexts)}개")

    if not base_sections:
        print(f"    ⚠️  경고: base_sections가 비어있습니다. LLM이 전체 텍스트에서 추출 시도 (폼 필드 포함 가능)")
    else:
        print(f"    📋 추출된 섹션 (첫 10개):")
        for idx, sec in enumerate(base_sections[:10], 1):
            level_icon = "■" if sec.get('level') == 'main' else "  ○"
            print(f"      {level_icon} [{idx}] {sec.get('number', '')} {sec.get('title', '')}")

        main_count = sum(1 for sec in base_sections if sec.get('level') == 'main')
        sub_count = sum(1 for sec in base_sections if sec.get('level') == 'sub')
        print(f"    📈 레벨 분포: main={main_count}개, sub={sub_count}개")

    if section_contexts:
        print(f"\n    📄 섹션 본문 발췌 샘플 (첫 3개):")
        for ctx in section_contexts[:3]:
            excerpt_preview = ctx.get('excerpt', '')[:80]
            print(f"      • {ctx.get('number', '')} {ctx.get('title', '')}")
            print(f"        └─ {excerpt_preview}...")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 6️⃣ 목차 텍스트 추출 (키워드 기반)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    template_text = extract_template_text(full_text)
    if not template_text:
        template_text = chunk_context

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 7️⃣ 스켈레톤 생성
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    skeleton_payload = [
        {'number': sec['number'], 'title': sec['title'], 'required': sec.get('required', True)}
        for sec in base_sections
    ]
    skeleton_json = json.dumps(skeleton_payload, ensure_ascii=False, indent=2) if base_sections else ""

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 8️⃣ LLM 프롬프트 구성 및 호출
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    system_prompt, user_prompt = build_llm_prompt(
        template,
        template_doc,
        tables,
        table_sections,
        symbol_sections,
        template_text,
        chunk_context,
        skeleton_json,
        section_contexts
    )

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

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 9️⃣ LLM 응답 처리 및 병합
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        toc = process_llm_response(sections, base_sections, template)

        state['table_of_contents'] = toc
        state['status'] = 'toc_extracted'

        print(f"\n  ✅ 청킹 기반 LLM 추출 완료: {len(toc['sections'])}개 섹션")
        for sec in toc['sections'][:5]:
            print(f"    • {sec.get('number', '')} {sec.get('title', '')}")
        if len(toc['sections']) > 5:
            print(f"    ... 외 {len(toc['sections']) - 5}개")

        return state

    except Exception as e:
        print(f"  ✗ 청킹 기반 LLM 추출 실패: {e} → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'

    return state


def extract_toc_from_announcement_and_attachments(state: BatchState) -> BatchState:
    """
    공고문 + 모든 첨부서류에서 목차 유추 (RAG + LLM)

    처리 흐름:
    1. 제출서류 feature 찾기
    2. RAG 검색 (공고문 + 첨부서류)
    3. LLM으로 목차 생성
    """
    print(f"\n{'='*60}")
    print(f"📑 공고문 + 첨부서류 기반 목차 유추")
    print(f"{'='*60}")

    collection = state.get('chroma_collection')

    if not collection:
        print(f"\n  ⚠️  'chroma_collection' 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣ 컨텍스트 준비 (제출서류 feature + RAG 검색)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    submission_content, all_chunks = prepare_announcement_context(state, collection)

    if not submission_content:
        print(f"\n  ⚠️  '제출서류' feature 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2️⃣ LLM으로 목차 생성
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    try:
        toc = generate_toc_from_announcement(submission_content, all_chunks, state)
        state['table_of_contents'] = toc
        state['status'] = 'toc_extracted'
        return state

    except Exception as e:
        print(f"\n  ✗ 목차 생성 실패: {e} → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'
        return state
