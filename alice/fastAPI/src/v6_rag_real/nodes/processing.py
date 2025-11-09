"""
문서 처리 노드들 (청킹, 임베딩, VectorDB 등)
노트북에서 추출한 전체 구현
"""

import re
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# OpenAI
from openai import OpenAI
import os
from dotenv import load_dotenv

# 임베딩 & VectorDB
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from ..state_types import BatchState
from ..config import FEATURES, RAG_SETTINGS, VECTOR_DB_DIR, CSV_OUTPUT_DIR
from ..utils import detect_section_headers, chunk_by_sections

# OpenAI 클라이언트 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def chunk_all_documents(state: BatchState) -> BatchState:
    """
    모든 문서를 섹션 기반으로 청킹 (공고문 + 첨부서류)
    """
    documents = state['documents']
    all_chunks = []
    chunk_global_id = 0
    
    print(f"\n{'='*60}")
    print(f"📦 섹션 기반 청킹 시작")
    print(f"{'='*60}")
    
    for doc in documents:
        print(f"\n  📄 {doc['file_name']} 청킹 중...")
        
        doc_chunk_start = chunk_global_id
        
        # 페이지별로 청킹
        for page_num, page_text in doc['page_texts'].items():
            page_chunks = chunk_by_sections(page_text, page_num)
            
            for chunk_data in page_chunks:
                all_chunks.append({
                    'chunk_id': f"{doc['document_id']}_chunk_{chunk_global_id}",
                    'text': chunk_data['text'],
                    
                    # 문서 메타데이터
                    'project_idx': state['project_idx'],
                    'document_id': doc['document_id'],
                    'document_type': doc['document_type'],
                    'file_name': doc['file_name'],
                    
                    # 섹션 정보
                    'section': chunk_data['section'],
                    'page': chunk_data['page'],
                    'is_sectioned': chunk_data['is_sectioned'],
                    
                    # 첨부서류 번호
                    'attachment_number': doc.get('attachment_number'),
                })
                chunk_global_id += 1
        
        doc_chunk_count = chunk_global_id - doc_chunk_start
        print(f"    ✓ {doc_chunk_count}개 청크 생성")
        
        # 문서에 청크 범위 저장
        doc['chunk_start_id'] = doc_chunk_start
        doc['chunk_end_id'] = chunk_global_id - 1
        doc['chunk_count'] = doc_chunk_count
    
    state['all_chunks'] = all_chunks
    state['status'] = 'all_chunked'
    
    print(f"\n  ✅ 총 {len(all_chunks)}개 청크 생성 ({len(documents)}개 문서)")
    
    # 통계 출력
    sectioned_count = sum(1 for c in all_chunks if c['is_sectioned'])
    print(f"    - 섹션 기반 청크: {sectioned_count}개")
    print(f"    - 고정 길이 청크: {len(all_chunks) - sectioned_count}개")
    
    return state


def embed_all_chunks(state: BatchState) -> BatchState:
    """
    모든 청크를 임베딩 벡터로 변환
    """
    all_chunks = state['all_chunks']
    
    print(f"\n{'='*60}")
    print(f"🧠 임베딩 생성 시작")
    print(f"{'='*60}")
    
    # 임베딩 모델 로드
    print(f"\n  📥 임베딩 모델 로딩...")
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    print(f"    ✓ 모델 로딩 완료")
    
    # 청크 텍스트 추출
    chunk_texts = [chunk['text'] for chunk in all_chunks]

    # 배치 임베딩 (배치별 진행 상황 표시)
    batch_size = 32  # 64 → 32로 줄여서 더 자주 진행 상황 표시
    total_chunks = len(chunk_texts)
    total_batches = (total_chunks + batch_size - 1) // batch_size

    print(f"\n  🔢 {total_chunks}개 청크 임베딩 중... (배치 크기: {batch_size}, 총 {total_batches}개 배치)")

    import numpy as np
    all_embeddings = []

    for i in range(0, total_chunks, batch_size):
        batch_num = i // batch_size + 1
        batch = chunk_texts[i:i+batch_size]

        print(f"    ⏳ 배치 {batch_num}/{total_batches} 처리 중... ({i+1}-{min(i+len(batch), total_chunks)}/{total_chunks} 청크)")

        batch_embeddings = model.encode(
            batch,
            show_progress_bar=False,  # 배치별로 진행바 끄기
            convert_to_numpy=True
        )
        all_embeddings.append(batch_embeddings)

    embeddings = np.vstack(all_embeddings)

    state['all_embeddings'] = embeddings
    state['embedding_model'] = model
    state['status'] = 'all_embedded'

    print(f"\n  ✅ 임베딩 완료: {embeddings.shape}")
    if len(embeddings.shape) > 1:
        print(f"    - 청크 수: {embeddings.shape[0]}")
        print(f"    - 차원: {embeddings.shape[1]}")
    else:
        print(f"    - 청크 수: {embeddings.shape[0] if embeddings.shape else 0}")
    
    return state


def init_and_store_vectordb(state: BatchState) -> BatchState:
    """
    Chroma VectorDB 초기화 및 청크 저장
    """
    all_chunks = state['all_chunks']
    embeddings = state['all_embeddings']
    
    print(f"\n{'='*60}")
    print(f"💾 Chroma VectorDB 초기화 및 저장")
    print(f"{'='*60}")

    # TODO: FastAPI 연동 시 config.VECTOR_DB_DIR 사용하도록 변경 필요
    # Chroma DB 경로 설정 (현재 테스트용 하드코딩)
    db_path = Path("./chroma_db")
    db_path.mkdir(exist_ok=True)
    
    # Chroma Client 생성
    print(f"\n  📂 VectorDB 경로: {db_path.absolute()}")
    client = chromadb.PersistentClient(path=str(db_path))
    
    # 컬렉션 이름
    collection_name = f"project_{state['project_idx']}"
    
    # 기존 컬렉션 삭제 (재실행 시)
    try:
        client.delete_collection(name=collection_name)
        print(f"  🗑️  기존 컬렉션 삭제: {collection_name}")
    except:
        pass
    
    # 새 컬렉션 생성
    collection = client.create_collection(
        name=collection_name,
        metadata={
            "description": "공고문 + 첨부서류 통합 RAG DB",
            "project_idx": state['project_idx'],
            "created_at": datetime.now().isoformat(),
            "hnsw:space": "cosine"  # Cosine distance for text similarity
        }
    )
    
    print(f"  ✓ 컬렉션 생성: {collection_name}")
    
    # 청크 + 임베딩 저장
    print(f"\n  💾 {len(all_chunks)}개 청크 저장 중...")
    
    collection.add(
        ids=[chunk['chunk_id'] for chunk in all_chunks],
        embeddings=embeddings.tolist(),
        documents=[chunk['text'] for chunk in all_chunks],
        metadatas=[
            {
                'document_id': chunk['document_id'],
                'document_type': chunk['document_type'],
                'file_name': chunk['file_name'],
                'section': chunk['section'],
                'page': chunk['page'],
                'attachment_number': chunk.get('attachment_number') or 0
            }
            for chunk in all_chunks
        ]
    )
    
    state['chroma_client'] = client
    state['chroma_collection'] = collection
    state['vector_db_path'] = str(db_path)
    state['status'] = 'vectordb_ready'
    
    print(f"  ✅ VectorDB 저장 완료")
    print(f"    - 컬렉션: {collection_name}")
    print(f"    - 청크 수: {len(all_chunks)}")
    print(f"    - 경로: {db_path.absolute()}")
    
    return state


# 키워드 기반으로 rag검색을해서 llm이 분석한다. 
def extract_features_rag(state: BatchState) -> BatchState:
    """
    RAG 기반 Feature 추출 (크로스 문서 검색)
    
    프로세스:
    1. Feature 쿼리 임베딩
    2. VectorDB 유사도 검색 (공고 + 첨부 통합)
    3. 상위 K개 chunk만 LLM에 전달
    4. LLM 분석 결과 저장
    """
    collection = state['chroma_collection']
    model = state['embedding_model']
    documents = state['documents']
    
    print(f"\n{'='*60}")
    print(f"🤖 RAG 기반 Feature 추출")
    print(f"{'='*60}")

    # 전체 프로젝트에서 Feature 추출 (공고 + 첨부 통합 RAG 검색)
    # RAG는 VectorDB에서 모든 문서를 통합 검색하므로 Feature는 프로젝트당 1번만 추출
    all_features = []

    print(f"\n  📋 전체 프로젝트에서 Feature 추출 중... (총 {len(FEATURES)}개)")

    for i, feature_def in enumerate(FEATURES):
        print(f"\n    [{i+1}/{len(FEATURES)}] {feature_def['feature_type']}...", end=" ")

        try:
            # 1️⃣ Feature 쿼리 임베딩
            # 키워드 우선순위: primary → secondary → related
            keywords = feature_def['keywords']
            if isinstance(keywords, dict):
                # 새로운 구조: primary/secondary/related
                all_keywords = []
                all_keywords.extend(keywords.get('primary', []))
                all_keywords.extend(keywords.get('secondary', []))
                all_keywords.extend(keywords.get('related', []))
                keywords_str = " ".join(all_keywords[:5])  # 상위 5개
            else:
                # 이전 구조 호환 (리스트)
                keywords_str = " ".join(keywords[:5])

            query_text = f"{feature_def['feature_type']} {keywords_str}"
            query_embedding = model.encode([query_text], convert_to_numpy=True)

            # 2️⃣ VectorDB 유사도 검색
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=7,  # 상위 7개 (공고 + 첨부 포함)
                # where 조건 없음 → 모든 문서 검색 (공고 + 첨부)
            )

            # 결과 없음
            if not results['ids'][0]:
                print("✗ (검색 결과 없음)")
                continue

            # 3️⃣ 유사도 임계값 체크
            top_distance = results['distances'][0][0]

            if top_distance > 1.2:  # ChromaDB cosine: 0.0-2.0 range
                print(f"✗ (거리 멀음: {top_distance:.3f})")
                continue

            # 4️⃣ 검색된 chunk 정리
            retrieved_chunks = []
            for j in range(len(results['ids'][0])):
                retrieved_chunks.append({
                    'chunk_id': results['ids'][0][j],
                    'text': results['documents'][0][j],
                    'metadata': results['metadatas'][0][j],
                    'distance': results['distances'][0][j]
                })

            # 5️⃣ 공고 vs 첨부 분리
            announcement_chunks = [c for c in retrieved_chunks if c['metadata']['document_type'] == 'ANNOUNCEMENT']
            attachment_chunks = [c for c in retrieved_chunks if c['metadata']['document_type'] == 'ATTACHMENT']

            # 6️⃣ LLM 컨텍스트 구성
            context_parts = []

            if announcement_chunks:
                context_parts.append("=== 📄 공고문 관련 섹션 ===")
                for chunk in announcement_chunks:
                    meta = chunk['metadata']
                    context_parts.append(
                        f"\n[섹션: {meta['section']}, 페이지: {meta['page']}]\n{chunk['text']}"
                    )

            if attachment_chunks:
                context_parts.append("\n=== 📎 첨부서류 관련 섹션 ===")
                for chunk in attachment_chunks:
                    meta = chunk['metadata']
                    context_parts.append(
                        f"\n[파일: {meta['file_name']}, 섹션: {meta['section']}, 페이지: {meta['page']}]\n{chunk['text']}"
                    )

            context_text = "\n\n---\n".join(context_parts)

            # 7️⃣ LLM 호출
            system_prompt = f"""당신은 정부 연구개발 공고문을 분석하는 전문가입니다.

공고문 및 첨부서류에서 '{feature_def['feature_type']}'에 해당하는 내용을 추출해주세요.

설명: {feature_def['description']}

다음 정보를 JSON 형식으로 반환하세요:
{{
"found": true/false,
"title": "섹션 제목",
"content": "추출된 내용 (200자 이내 요약)",
"full_content": "전체 내용",
"key_points": ["요점1", "요점2"]
}}

해당 내용을 찾을 수 없으면 found를 false로 반환하세요."""

            user_prompt = f"""검색된 관련 섹션:

{context_text}

'{feature_def['feature_type']}' 정보를 찾아 JSON으로 반환해주세요."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )

            result = json.loads(response.choices[0].message.content)

            # 8️⃣ 결과 저장
            if result.get("found"):
                all_features.append({
                    'feature_code': feature_def['feature_key'],
                    'feature_name': feature_def['feature_type'],
                    'title': result.get('title', ''),
                    'summary': result.get('content', ''),
                    'full_content': result.get('full_content', ''),
                    'key_points': result.get('key_points', []),

                    # RAG 메타데이터
                    'chunks_used': [
                        {
                            'file': c['metadata']['file_name'],
                            'section': c['metadata']['section'],
                            'page': c['metadata']['page']
                        }
                        for c in retrieved_chunks
                    ],
                    'keywords_detected': all_keywords if isinstance(keywords, dict) else keywords,
                    'vector_similarity': float(top_distance),
                    'chunks_from_announcement': len(announcement_chunks),
                    'chunks_from_attachments': len(attachment_chunks),
                    'referenced_attachments': list(set(
                        c['metadata']['file_name'] for c in attachment_chunks
                    )),

                    # 프로젝트 정보
                    'project_idx': state['project_idx'],
                    'extracted_at': datetime.now().isoformat()
                })

                print(f"✓ (공고:{len(announcement_chunks)} + 첨부:{len(attachment_chunks)}, 유사도:{top_distance:.2f})")
            else:
                print("✗ (LLM: found=false)")

        except Exception as e:
            print(f"✗ (에러: {e})")
            state['errors'].append(f"Feature '{feature_def['feature_type']}' 추출 실패: {str(e)}")
    
    state['extracted_features'] = all_features
    state['status'] = 'features_extracted'

    print(f"\n  🎯 총 {len(all_features)}개 Feature 추출 완료")

    return state


# ========================================
# 🔖 MVP2: 분석 대시보드 (근거 추적)
# ========================================
# 목적: 공고문에서 "붙임 1 참조", "별첨 2 참조" 등의 언급을 감지하여
#       해당 첨부 문서와 자동 매칭
#       → 분석 대시보드에서 사용자가 특정 내용의 근거를 확인할 때 활용
# 
# 예시:
# - 공고문: "제출 서류는 붙임 2 참조"
# - 첨부문서: "붙임2_연구계획서양식.pdf"
# - 매칭 결과: 공고 특정 섹션 ↔ 첨부2 연결 저장
# ========================================

def match_cross_references(state: BatchState) -> BatchState:
    """
    공고문 ↔ 첨부서류 참조 자동 매칭
    
    방법:
    1. 공고문에서 "붙임 1", "별첨 2" 등 패턴 감지
    2. VectorDB로 해당 첨부파일 검색
    3. 매칭 결과 저장
    """
    documents = state['documents']
    collection = state['chroma_collection']
    model = state['embedding_model']
    
    print(f"\n{'='*60}")
    print(f"🔗 참조 자동 매칭")
    print(f"{'='*60}")
    
    cross_references = []
    
    # 공고문에서 참조 패턴 찾기
    announcement_docs = [d for d in documents if d['document_type'] == 'ANNOUNCEMENT']
    
    for ann_doc in announcement_docs:
        full_text = ann_doc['full_text']
        
        # 참조 패턴 추출
        ref_patterns = re.findall(
            r'(붙임|별첨|첨부)\s*(\d+)[.\s:]*([가-힣a-zA-Z\s]+)?',
            full_text
        )
        
        print(f"\n  📄 {ann_doc['file_name']}: {len(ref_patterns)}개 참조 패턴 발견")
        
        for pattern in ref_patterns:
            ref_type = pattern[0]  # "붙임"
            ref_number = int(pattern[1])  # 1
            ref_title = pattern[2].strip() if pattern[2] else ""  # "연구계획서 양식"
            
            print(f"\n    🔍 '{ref_type} {ref_number} {ref_title}' 매칭 중...", end=" ")
            
            # 방법 1: 첨부번호로 직접 매칭
            target_attachment = next(
                (d for d in documents 
                 if d['document_type'] == 'ATTACHMENT' 
                 and d.get('attachment_number') == ref_number),
                None
            )
            
            match_method = "NUMBER_MATCH"
            match_score = 1.0
            
            # 방법 2: 제목으로 Vector 검색
            if not target_attachment and ref_title:
                query = f"{ref_type} {ref_number} {ref_title}"
                query_emb = model.encode([query], convert_to_numpy=True)
                
                results = collection.query(
                    query_embeddings=query_emb.tolist(),
                    n_results=3,
                    where={"document_type": "ATTACHMENT"}
                )
                
                if results['ids'][0] and results['distances'][0][0] < 0.5:
                    # 가장 유사한 청크의 문서 찾기
                    target_doc_id = results['metadatas'][0][0]['document_id']
                    target_attachment = next(
                        (d for d in documents if d['document_id'] == target_doc_id),
                        None
                    )
                    match_method = "VECTOR_SEARCH"
                    match_score = 1.0 - results['distances'][0][0]
            
            # 매칭 성공
            if target_attachment:
                cross_references.append({
                    'source_document_id': ann_doc['document_id'],
                    'source_file_name': ann_doc['file_name'],
                    'target_document_id': target_attachment['document_id'],
                    'target_file_name': target_attachment['file_name'],
                    'reference_type': ref_type,
                    'reference_number': ref_number,
                    'reference_title': ref_title,
                    'match_method': match_method,
                    'match_score': match_score,
                    'created_at': datetime.now().isoformat()
                })
                
                print(f"✓ → {target_attachment['file_name']} ({match_method}, {match_score:.2f})")
            else:
                print("✗ (매칭 실패)")
    
    state['cross_references'] = cross_references
    state['status'] = 'references_matched'
    
    print(f"\n  ✅ 총 {len(cross_references)}개 참조 매칭 완료")
    
    return state


def save_to_csv(state: BatchState) -> BatchState:
    """
    분석 결과를 파일로 저장 (오라클 연결 전 테스트용)

    저장 파일:
    1. ANALYSIS_RESULT_{timestamp}.csv - Feature 추출 결과 (RAG + LLM 분석)
    2. ANALYSIS_RESULT_{timestamp}.json - Feature 추출 결과 (JSON)
    3. table_of_contents_{timestamp}.json - 목차 정보 (JSON)
    """
    
    print(f"\n{'='*60}")
    print(f"💾 분석 결과 저장 (CSV + JSON)")
    print(f"{'='*60}")

    # 저장 디렉토리 생성
    output_folder = Path("./parsed_results/v6_rag")
    output_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_idx = state['project_idx']

    output_paths = {}

    try:
        # ========================================
        # 1. ANALYSIS_RESULT.csv (Feature 추출 결과만)
        # ========================================
        analysis_data = []
        analysis_json = []
        for idx, feature in enumerate(state['extracted_features'], start=1):
            result_id = idx
            analysis_json.append({
                'result_id': result_id,
                'project_idx': project_idx,
                'feature_code': feature['feature_code'],
                'feature_name': feature['feature_name'],
                'title': feature.get('title', ''),
                'summary': feature.get('summary', ''),
                'full_content': feature.get('full_content', ''),
                'key_points': feature.get('key_points', []),
                'vector_similarity': float(feature.get('vector_similarity', 0.0)),
                'chunks_from_announcement': int(feature.get('chunks_from_announcement', 0)),
                'chunks_from_attachments': int(feature.get('chunks_from_attachments', 0)),
                'referenced_attachments': feature.get('referenced_attachments', []),
                'extracted_at': feature.get('extracted_at', datetime.now().isoformat())
            })

            analysis_data.append({
                'result_id': result_id,
                'project_idx': project_idx,
                'feature_code': feature['feature_code'],
                'feature_name': feature['feature_name'],
                'title': feature.get('title', ''),
                'summary': feature.get('summary', ''),
                'full_content': feature.get('full_content', ''),
                'key_points': '|'.join(feature.get('key_points', [])),
                'vector_similarity': feature.get('vector_similarity', 0.0),
                'chunks_from_announcement': feature.get('chunks_from_announcement', 0),
                'chunks_from_attachments': feature.get('chunks_from_attachments', 0),
                'referenced_attachments': '|'.join(feature.get('referenced_attachments', [])),
                'extracted_at': feature.get('extracted_at', datetime.now().isoformat())
            })

        df_analysis = pd.DataFrame(analysis_data)
        csv_path = output_folder / f"ANALYSIS_RESULT_{project_idx}_{timestamp}.csv"
        df_analysis.to_csv(csv_path, index=False, encoding='utf-8-sig')
        output_paths['csv'] = str(csv_path)
        print(f"\n  ✅ ANALYSIS_RESULT.csv: {len(analysis_data)}행")
        print(f"     → {csv_path.name}")

        # ========================================
        # 2. ANALYSIS_RESULT.json (Feature 추출 결과)
        # ========================================
        json_result_path = output_folder / f"ANALYSIS_RESULT_{project_idx}_{timestamp}.json"
        with open(json_result_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_json, f, ensure_ascii=False, indent=2)
        output_paths['analysis_json'] = str(json_result_path)
        print(f"\n  ✅ ANALYSIS_RESULT.json: {len(analysis_json)}개 항목")
        print(f"     → {json_result_path.name}")
        
        # ========================================
        # 3. table_of_contents.json (목차 정보)
        # ========================================
        toc = state.get('table_of_contents')
        if toc:
            json_path = output_folder / f"table_of_contents_{project_idx}_{timestamp}.json"

            # JSON 저장 (들여쓰기 포함)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(toc, f, ensure_ascii=False, indent=2)

            output_paths['json'] = str(json_path)
            print(f"\n  ✅ table_of_contents.json: {toc.get('total_sections', 0)}개 섹션")
            print(f"     → {json_path.name}")
            print(f"     출처: {toc.get('source', 'unknown')}")
        else:
            print(f"\n  ⚠️  table_of_contents.json: 목차 없음, 생성 스킵")

        # State 업데이트
        state['csv_paths'] = output_paths
        state['status'] = 'csv_saved'

        print(f"\n  💾 저장 위치: {output_folder.absolute()}")
        print(f"  📊 총 {len(output_paths)}개 파일 생성")
        
    except Exception as e:
        error_msg = f"파일 저장 실패: {str(e)}"
        print(f"\n  ❌ {error_msg}")
        state['errors'].append(error_msg)

    return state
