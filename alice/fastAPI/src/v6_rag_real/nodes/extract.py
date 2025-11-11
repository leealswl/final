"""
텍스트 추출 노드
✅ 개선: 모든 문서에 pdfplumber 사용 (표 구조 보존)
✅ 메모리 기반 처리: 바이트 스트림에서 직접 추출 (파일 저장 불필요)
"""

import pdfplumber
import io
from datetime import datetime
from typing import List, Dict, Any

from ..state_types import BatchState
from ..utils import extract_attachment_number


def extract_all_texts(state: BatchState) -> BatchState:
    """
    모든 파일에서 텍스트 추출 (통합 방식)
    - pdfplumber 사용: 텍스트 + 표 구조 추출
    - 공고문/첨부 구분 없이 동일한 품질 보장
    - 메모리 기반: 바이트 스트림에서 직접 추출 (파일 경로 불필요)
    """
    files = state['files']
    documents = []

    print(f"\n{'='*60}")
    print(f"📄 {len(files)}개 파일 텍스트 추출 시작 (메모리 기반 pdfplumber)")
    print(f"{'='*60}")

    for file_idx, file_info in enumerate(files):
        # 바이트 데이터 또는 파일 경로 지원 (하위 호환성)
        file_bytes = file_info.get('bytes')
        file_path = file_info.get('path')
        filename = file_info['filename']
        folder = file_info['folder']

        # 문서 타입 결정 (folder 기반)
        doc_type = "ANNOUNCEMENT" if folder == 1 else "ATTACHMENT"

        print(f"\n  [{file_idx+1}/{len(files)}] {filename} ({doc_type})")

        try:
            doc_id = f"doc_{state['project_idx']}_{file_idx+1}"

            # ========== 모든 문서: pdfplumber 사용 (표 + 텍스트) ==========
            if file_bytes:
                # 바이트 스트림에서 직접 열기 (메모리 기반)
                print(f"    📊 방식: pdfplumber (메모리 스트림)")
                pdf_stream = io.BytesIO(file_bytes)
                pdf_file = pdfplumber.open(pdf_stream)
            elif file_path:
                # 파일 경로에서 열기 (하위 호환성)
                print(f"    📊 방식: pdfplumber (파일 경로)")
                pdf_file = pdfplumber.open(file_path)
            else:
                raise ValueError(f"파일 정보 부족: bytes 또는 path 필요")

            with pdf_file as pdf:
                full_text = ""
                page_texts = {}
                all_tables = []

                for page_num, page in enumerate(pdf.pages):
                    # 텍스트 추출
                    text = page.extract_text() or ""
                    full_text += f"\n[페이지 {page_num + 1}]\n{text}"
                    page_texts[page_num + 1] = text

                    # 표 추출
                    tables = page.extract_tables()
                    if tables:
                        for table_idx, table in enumerate(tables):
                            all_tables.append({
                                'page_number': page_num + 1,
                                'table_index': table_idx,
                                'data': table,
                                'rows': len(table),
                                'cols': len(table[0]) if table else 0
                            })

            documents.append({
                'document_id': doc_id,
                'file_name': filename,
                'file_path': file_path if file_path else None,  # 경로가 있으면 저장, 없으면 None
                'document_type': doc_type,
                'folder': folder,
                'full_text': full_text,
                'page_texts': page_texts,
                'page_count': len(page_texts),
                'attachment_number': extract_attachment_number(filename),
                'tables': all_tables
            })

            print(f"    ✓ 추출 완료: {len(full_text):,}자, {len(page_texts)}페이지, {len(all_tables)}개 표")

        except Exception as e:
            print(f"    ✗ 추출 실패: {e}")
            state['errors'].append(f"{filename} 텍스트 추출 실패: {str(e)}")

    state['documents'] = documents
    state['status'] = 'texts_extracted'

    total_chars = sum(len(d['full_text']) for d in documents)
    total_pages = sum(d['page_count'] for d in documents)
    total_tables = sum(len(d.get('tables', [])) for d in documents)

    print(f"\n  ✅ 총 {len(documents)}개 문서, {total_chars:,}자, {total_pages}페이지, {total_tables}개 표")

    return state
