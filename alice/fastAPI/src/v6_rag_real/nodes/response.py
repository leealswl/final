"""
응답 생성 노드
✅ MVP1: form_source 결정 및 사용자 폼 데이터 생성
✅ 2025-11-09 suyeon: Backend API 호출하여 Oracle DB 저장
"""

import os
import requests
from ..state_types import BatchState


def build_response(state: BatchState) -> BatchState:
    """
    FastAPI 응답용 JSON 데이터 생성
    - 첨부 템플릿 우선순위 결정
    - form_source: 'TEMPLATE' (첨부 양식) 또는 'TOC' (공고 목차)
    - 목차 정보 포함
    """
    documents = state['documents']
    all_features = state['extracted_features']
    # cross_references = state['cross_references']  # 🔖 MVP2에서 사용 예정 (현재 미사용)
    attachment_templates = state.get('attachment_templates', [])
    table_of_contents = state.get('table_of_contents')

    print(f"\n{'='*60}")
    print(f"📤 최종 응답 데이터 생성")
    print(f"{'='*60}")

    # ========================================
    # ✅ MVP1: 사용자 입력 폼 소스 결정
    # ========================================
    templates_with_forms = [t for t in attachment_templates if t.get('has_template')]

    if templates_with_forms:
        form_source = 'TEMPLATE'
        primary_template = templates_with_forms[0]
        print(f"\n  📋 사용자 폼 소스: TEMPLATE (첨부 양식 기반)")
        print(f"    - 선택된 양식: {primary_template['file_name']}")
        print(f"    - 필드 수: {len(primary_template['fields'])}개")
    else:
        form_source = 'TOC'
        primary_template = None
        print(f"\n  📋 사용자 폼 소스: TOC (공고 목차 기반)")

    # ========== 기본 응답 데이터 ==========
    response_data = {
        'status': 'success',
        'project_idx': state['project_idx'],
        'user_id': state['user_id'],
        'form_source': form_source,  # ✨ MVP1

        'documents': [
            {
                'document_id': doc['document_id'],
                'file_name': doc['file_name'],
                'document_type': doc['document_type'],
                'page_count': doc['page_count'],
            }
            for doc in documents
        ],

        'features_summary': {
            'total_count': len(all_features),
        },
        'features': all_features,

        'attachment_templates': attachment_templates,  # ✨ MVP1
        'table_of_contents': table_of_contents,  # ✨ NEW: 목차 구조
        'errors': state.get('errors', [])
    }

    # ========== 사용자 폼 데이터 추가 ==========
    if form_source == 'TEMPLATE' and primary_template:
        response_data['user_form'] = {
            'type': 'template_based',
            'source_file': primary_template['file_name'],
            'fields': primary_template['fields'],
            'tables': primary_template['tables']
        }
    else:
        # 목차 기반 폼 (table_of_contents 사용)
        response_data['user_form'] = {
            'type': 'toc_based',
            'table_of_contents': table_of_contents
        }

    state['response_data'] = response_data
    state['status'] = 'completed'

    print(f"\n  ✅ 응답 데이터 생성 완료")
    print(f"    - 폼 소스: {form_source}")
    if table_of_contents:
        print(f"    - 목차 섹션: {table_of_contents.get('total_sections', 0)}개")
        print(f"    - 목차 출처: {table_of_contents.get('source', 'unknown')}")

    # ========================================
    # 2025-11-09 suyeon: Backend API 호출하여 Oracle DB 저장
    # ========================================
    backend_url = os.getenv('BACKEND_URL', 'http://localhost:8080')
    save_to_backend = os.getenv('SAVE_TO_BACKEND', 'true').lower() == 'true'

    if save_to_backend:
        try:
            print(f"\n  🔗 Backend API 호출 중: {backend_url}/api/analysis/save-result")

            # Backend로 전송할 데이터 구조화
            backend_payload = {
                'project_idx': state['project_idx'],
                'user_id': state['user_id'],
                'extracted_features': all_features,
                'table_of_contents': table_of_contents
            }

            response = requests.post(
                f"{backend_url}/api/analysis/save-result",
                json=backend_payload,
                timeout=30
            )

            if response.status_code == 200:
                print(f"  ✅ Backend 저장 성공: {response.json().get('message', 'OK')}")
                state['backend_save_status'] = 'success'
            else:
                print(f"  ⚠️ Backend 저장 실패: {response.status_code} - {response.text}")
                state['backend_save_status'] = 'failed'
                state['errors'].append(f"Backend 저장 실패: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Backend API 호출 실패: {str(e)}")
            state['backend_save_status'] = 'error'
            state['errors'].append(f"Backend API 호출 오류: {str(e)}")
    else:
        print(f"\n  ⏭️ Backend 저장 스킵 (SAVE_TO_BACKEND=false)")

    return state
