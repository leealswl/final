"""
첨부 양식 감지 모듈
제안서/계획서 양식 여부를 RAG + 규칙 기반으로 판단

✅ 핵심 기능: 첨부서류 중 어떤 파일이 "작성해야 할 양식"인지 자동 감지
📌 목적: 양식 기반 목차 추출 vs 공고 기반 목차 유추 분기 결정
"""

from datetime import datetime
from typing import List, Dict, Any
import unicodedata
import numpy as np

from ..state_types import BatchState


def detect_proposal_templates(state: BatchState) -> BatchState:
    """
    첨부서류에서 제안서 양식 감지 (RAG + 규칙 기반)

    ✅ 필수 노드: 목차 추출 방식 결정의 핵심

    🔍 감지 신호 (다중 신호 융합):
    1. 파일명 키워드 ('계획서', '신청서', '제안서', '양식')
    2. 공고문에서 첨부파일 언급 ('붙임1', '별첨2' 등)
    3. RAG 검색: 양식 관련 키워드 ('양식', '서식', '작성예시')
    4. 표 구조 존재 (입력 칸이 있는 표)

    Returns:
        state['attachment_templates']: 양식 정보 리스트
        - has_template: True/False (양식 여부)
        - confidence_score: 신뢰도 (0.0-1.0)
        - fields: 추출된 필드 목록
    """
    collection = state['chroma_collection']
    model = state['embedding_model']
    documents = state['documents']
    all_features = state.get('extracted_features', [])

    print(f"\n{'='*60}")
    print(f"📋 첨부 양식 감지 (RAG 기반)")
    print(f"{'='*60}")

    attachment_templates = []
    attachment_docs = [d for d in documents if d.get('folder') == 2]

    if not attachment_docs:
        print("\n  ⚠️  첨부 문서(folder=2)가 없습니다.")
        state['attachment_templates'] = []
        return state

    # 1️⃣ 공고문에서 "제출서류" feature 찾기
    submission_features = [
        f for f in all_features
        if f['feature_code'] == 'submission_docs'  # "제출서류" feature
    ]

    # 2️⃣ 각 첨부파일에 대해 양식 여부 판단
    for att_doc in attachment_docs:
        file_name_raw = att_doc['file_name']
        file_name = unicodedata.normalize('NFC', file_name_raw)
        attachment_num = att_doc.get('attachment_number')

        print(f"\n  📄 {file_name}")

        # 신호 1: 파일명 키워드 체크
        keyword_weights = {
            '계획서': 0.5,
            '제안서': 0.45,
            '신청서': 0.5,  # 신청서 가중치 상향 (0.35 → 0.5)
            '양식': 0.2,
            '서식': 0.2,
            '작성요령': 0.2
        }
        matched_keywords = [kw for kw in keyword_weights if kw in file_name]
        keyword_score = max((keyword_weights[kw] for kw in matched_keywords), default=0.0)
        confidence_score = keyword_score

        if matched_keywords:
            print(f"    - 파일명 키워드: ✓ {matched_keywords} (신뢰도: +{keyword_score:.2f})")
        else:
            print("    - 파일명 키워드: ✗ (신뢰도: +0.0)")

        # 신호 2: 공고문에서 해당 첨부파일 언급 체크
        mentioned_in_announcement = False
        mention_context = ""

        for sub_feature in submission_features:
            # 첨부번호가 언급되었는지 체크
            full_content = sub_feature.get('full_content', '')
            if attachment_num:
                if f"붙임{attachment_num}" in full_content or f"붙임 {attachment_num}" in full_content:
                    mentioned_in_announcement = True
                    mention_context = full_content[:200]
                    confidence_score += 0.3
                    break
                elif f"별첨{attachment_num}" in full_content or f"별첨 {attachment_num}" in full_content:
                    mentioned_in_announcement = True
                    mention_context = full_content[:200]
                    confidence_score += 0.3
                    break

        print(f"    - 공고문 언급: {'✓' if mentioned_in_announcement else '✗'} (신뢰도: +{0.3 if mentioned_in_announcement else 0.0})")

        # 신호 3: RAG로 첨부파일 자체에서 "양식" 관련 키워드 검색
        try:
            # OpenAI API로 쿼리 임베딩 생성 (processing.py의 extract_features_rag와 동일한 방식)
            from openai import OpenAI
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            query_text = "양식 서식 작성예시 작성방법 입력칸"
            query_response = client.embeddings.create(
                model="text-embedding-3-small",
                input=[query_text]
            )
            query_embedding = [query_response.data[0].embedding]

            results = collection.query(
                query_embeddings=query_embedding,
                n_results=3,
                where={'file_name': file_name}  # 해당 파일만 검색
            )

            if results['ids'][0] and results['distances'][0][0] < 0.8:
                confidence_score += 0.4
                print(f"    - RAG 양식 키워드: ✓ (거리: {results['distances'][0][0]:.2f}, 신뢰도: +0.4)")
            else:
                print(f"    - RAG 양식 키워드: ✗")
        except Exception as e:
            print(f"    - RAG 양식 키워드: ✗ (검색 실패: {e})")

        # 신호 4: 표 구조 분석
        tables = att_doc.get('tables', [])
        valid_tables = [t for t in tables if t['rows'] >= 2]
        has_table_structure = len(valid_tables) >= 1

        if has_table_structure:
            confidence_score += 0.2
            print(f"    - 표 구조: ✓ ({len(valid_tables)}개 유효 표, 신뢰도: +0.2)")
        else:
            print(f"    - 표 구조: ✗")

        # 계획서/신청서 첨부 번호 가중치 (붙임 1, 2 등에 우선순위 부여)
        if attachment_num in (1, 2):
            if '계획서' in file_name:
                confidence_score += 0.15
                print(f"    - 첨부번호/계획서 우선 가중치 적용 (+0.15)")
            elif '신청서' in file_name:
                confidence_score += 0.1
                print(f"    - 첨부번호/신청서 우선 가중치 적용 (+0.1)")
        
        # 신청서 + 표 구조 조합 가중치 (신청서는 보통 표 구조가 있으면 양식일 가능성 높음)
        if '신청서' in file_name and has_table_structure:
            confidence_score += 0.1
            print(f"    - 신청서+표구조 조합 가중치 적용 (+0.1)")

        # 최종 판단 (임계값: 0.6)
        is_template = confidence_score >= 0.6

        # 필드 추출 (양식인 경우에만)
        fields = []
        if is_template and has_table_structure:
            fields = _extract_fields_from_tables(valid_tables)

        # 템플릿 정보 저장
        template_info = {
            'document_id': att_doc['document_id'],
            'file_name': file_name,
            'attachment_number': attachment_num,
            'has_template': is_template,
            'confidence_score': round(confidence_score, 2),
            'detection_signals': {
                'filename_keyword': matched_keywords,
                'announcement_mention': mentioned_in_announcement,
                'table_structure': has_table_structure
            },
            'fields': fields,
            'tables': valid_tables,  # 목차 추출에 사용
            'mention_context': mention_context if mentioned_in_announcement else None,
            'extracted_at': datetime.now().isoformat()
        }

        attachment_templates.append(template_info)

        print(f"    → 최종 판단: {'✅ 양식 문서' if is_template else '❌ 일반 문서'} (신뢰도: {confidence_score:.2f})")

    state['attachment_templates'] = attachment_templates

    # 요약
    templates_with_forms = [t for t in attachment_templates if t['has_template']]
    print(f"\n  ✅ 양식 감지 완료:")
    print(f"    - 전체 첨부: {len(attachment_templates)}개")
    print(f"    - 양식 문서: {len(templates_with_forms)}개")

    return state


def _extract_fields_from_tables(valid_tables: List[Dict]) -> List[Dict[str, str]]:
    """
    표에서 필드 추출 (헤더 분석)

    Args:
        valid_tables: 표 정보 리스트

    Returns:
        필드 리스트 [{'field_name': '항목명', 'field_type': 'text', 'source': 'table_header'}, ...]
    """
    fields = []

    for table_info in valid_tables[:1]:  # 첫 번째 표만 분석
        table_data = table_info['data']
        if len(table_data) >= 2 and table_data[0]:
            headers = table_data[0]
            for col_idx, header in enumerate(headers):
                if header and header.strip():
                    field_name = header.strip()

                    # 필드 타입 추론
                    field_type = 'text'
                    if any(kw in field_name for kw in ['날짜', '일자']):
                        field_type = 'date'
                    elif any(kw in field_name for kw in ['금액', '수량']):
                        field_type = 'number'

                    fields.append({
                        'field_name': field_name,
                        'field_type': field_type,
                        'source': 'table_header'
                    })

    return fields
