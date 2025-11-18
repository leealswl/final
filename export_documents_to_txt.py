#!/usr/bin/env python3
"""
documents의 페이지 텍스트를 txt 파일로 저장하는 스크립트
extract.py를 거친 후 state에 담긴 documents 확인용
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def export_documents_to_txt(documents, output_dir="./extracted_texts"):
    """
    documents 리스트의 페이지 텍스트를 txt 파일로 저장
    
    Args:
        documents: extract.py를 거친 documents 리스트
        output_dir: 출력 디렉토리
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"📄 documents → txt 파일 변환")
    print(f"{'='*60}")
    
    for doc_idx, doc in enumerate(documents):
        file_name = doc.get('file_name', f'document_{doc_idx+1}')
        doc_type = doc.get('document_type', 'UNKNOWN')
        page_texts = doc.get('page_texts', {})
        tables = doc.get('tables', [])
        
        # 파일명에서 특수문자 제거
        safe_filename = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        safe_filename = safe_filename.replace('.pdf', '').replace('.PDF', '')
        
        print(f"\n  [{doc_idx+1}/{len(documents)}] {file_name} ({doc_type})")
        
        # 1. 전체 텍스트 파일 (full_text)
        if doc.get('full_text'):
            full_text_path = output_path / f"{doc_idx+1}_{safe_filename}_FULL.txt"
            with open(full_text_path, 'w', encoding='utf-8') as f:
                f.write(f"파일명: {file_name}\n")
                f.write(f"문서 타입: {doc_type}\n")
                f.write(f"페이지 수: {doc.get('page_count', 0)}\n")
                f.write(f"표 개수: {len(tables)}\n")
                f.write(f"추출 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n\n")
                f.write(doc['full_text'])
            print(f"    ✓ 전체 텍스트: {full_text_path.name}")
        
        # 2. 페이지별 텍스트 파일
        if page_texts:
            pages_dir = output_path / f"{doc_idx+1}_{safe_filename}_pages"
            pages_dir.mkdir(exist_ok=True)
            
            for page_num, page_text in page_texts.items():
                page_file = pages_dir / f"page_{page_num:03d}.txt"
                with open(page_file, 'w', encoding='utf-8') as f:
                    f.write(f"파일명: {file_name}\n")
                    f.write(f"페이지: {page_num}\n")
                    f.write(f"문서 타입: {doc_type}\n")
                    f.write("="*80 + "\n\n")
                    f.write(page_text)
            
            print(f"    ✓ 페이지별 텍스트: {pages_dir.name}/ (총 {len(page_texts)}개 페이지)")
        
        # 3. 표 데이터 파일 (JSON)
        if tables:
            tables_path = output_path / f"{doc_idx+1}_{safe_filename}_tables.json"
            with open(tables_path, 'w', encoding='utf-8') as f:
                json.dump(tables, f, ensure_ascii=False, indent=2)
            print(f"    ✓ 표 데이터: {tables_path.name} ({len(tables)}개 표)")
    
    print(f"\n  ✅ 저장 완료: {output_path.absolute()}")
    print(f"  📊 총 {len(documents)}개 문서 처리")
    
    return output_path


def load_documents_from_state_json(state_json_path):
    """
    state JSON 파일에서 documents 로드
    """
    with open(state_json_path, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    return state.get('documents', [])


def main():
    """
    사용법:
    1. state JSON 파일이 있는 경우:
       python export_documents_to_txt.py state.json
    
    2. documents JSON 파일이 있는 경우:
       python export_documents_to_txt.py documents.json
    
    3. 직접 documents 리스트를 JSON으로 저장한 경우:
       python export_documents_to_txt.py your_documents.json
    """
    if len(sys.argv) < 2:
        print("=" * 80)
        print("📄 documents → txt 파일 변환 스크립트")
        print("=" * 80)
        print("\n사용법:")
        print("  python export_documents_to_txt.py <state_json_path>")
        print("\n또는")
        print("  python export_documents_to_txt.py <documents_json_path>")
        print("\n예시:")
        print("  python export_documents_to_txt.py state_144.json")
        print("  python export_documents_to_txt.py documents.json")
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    
    if not json_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {json_path}")
        sys.exit(1)
    
    print(f"📂 파일 로드: {json_path}")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # state 구조인지 documents 구조인지 확인
        if 'documents' in data:
            documents = data['documents']
            print(f"✅ state JSON에서 documents 로드: {len(documents)}개")
        elif isinstance(data, list):
            documents = data
            print(f"✅ documents 리스트 로드: {len(documents)}개")
        else:
            print(f"❌ 잘못된 JSON 구조입니다. 'documents' 키가 있거나 리스트여야 합니다.")
            sys.exit(1)
        
        # txt 파일로 변환
        output_dir = export_documents_to_txt(documents)
        
        print(f"\n🎉 완료! 출력 디렉토리: {output_dir}")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

