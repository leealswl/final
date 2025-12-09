"""
목차(Table of Contents) 추출 모듈
제안서 양식 또는 공고문/첨부서류에서 목차 구조 추출

핵심 노드 함수만 포함 (세부 로직은 하위 모듈 참조)
"""

import json
import re
import unicodedata
from datetime import datetime

from ..state_types import BatchState
from .toc_util import (
    find_proposal_template,
    create_default_toc,
    client,
    extract_toc_from_full_document_vision
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
    2. Vision API로 전체 문서 분석 (우선)
    3. 실패 시 기본 템플릿 반환
    """
    print(f"\n{'='*60}")
    print(f"📑 양식에서 목차 추출 (Vision API 전용)")
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

    print(f"  🤖 Vision API 기반 목차 추출 시작 (템플릿 전용)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🎯 Vision API로만 목차 추출 (텍스트 기반 fallback 제거)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # file_bytes 찾기 - Unicode 정규화 적용
    file_bytes = None
    target_filename = template['file_name']
    target_filename_normalized = unicodedata.normalize('NFC', str(target_filename))

    for file_info in state.get('files', []):
        current_filename = unicodedata.normalize('NFC', str(file_info.get('filename', '')))
        if current_filename == target_filename_normalized:
            file_bytes = file_info.get('bytes')
            if file_bytes:
                print(f"  ✓ 양식 파일 발견: {target_filename} ({len(file_bytes):,} bytes)")
                break

    if not file_bytes:
        print(f"    ⚠️  file_bytes 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    print(f"    🎯 양식 전체 문서 Vision API 분석 시도...")

    # 전체 문서 Vision API로 목차 추출
    toc_sections = extract_toc_from_full_document_vision(file_bytes, template['file_name'])

    if toc_sections and len(toc_sections) >= 3:
        print(f"    ✅ 전체 문서 Vision API 성공: {len(toc_sections)}개 섹션 추출")
        print(f"    📋 추출된 섹션 (첫 10개):")
        for sec in toc_sections[:10]:
            level_icon = "■" if sec.get('level') == 'main' else "  ○"
            description_preview = sec.get('description', '')[:30] + '...' if len(sec.get('description', '')) > 30 else sec.get('description', '')
            print(f"      {level_icon} {sec.get('number', '')} {sec.get('title', '')}")
            if description_preview:
                print(f"         └─ {description_preview}")

        # 새 함수가 이미 description을 포함하여 반환하므로 그대로 사용
        # description이 없는 항목에만 기본 description 추가
        final_sections = []
        for sec in toc_sections:
            final_section = {
                'number': sec.get('number', ''),
                'title': sec.get('title', ''),
            }
            
            # description이 있으면 사용, 없으면 기본 description 생성
            if sec.get('description'):
                final_section['description'] = sec['description']
            else:
                final_section['description'] = f"{sec.get('title', '')} 섹션에 대한 작성 내용"
            
            # level과 parent_number도 포함 (있는 경우)
            if sec.get('level'):
                final_section['level'] = sec['level']
            if sec.get('parent_number'):
                final_section['parent_number'] = sec['parent_number']
                
            final_sections.append(final_section)

        toc = {
            'source': 'template',
            'source_file': template['file_name'],
            'extraction_method': 'full_document_vision',
            'sections': final_sections,
            'total_sections': len(final_sections),
            'has_page_numbers': False,
            'extracted_at': datetime.now().isoformat()
        }

        state['table_of_contents'] = toc
        state['status'] = 'toc_extracted'

        print(f"\n  ✅ 전체 문서 Vision API 추출 완료: {len(final_sections)}개 섹션 (description 포함)")
        return state
    else:
        print(f"    ⚠️  Vision API 실패 또는 섹션 부족 → 기본 템플릿 사용")
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
