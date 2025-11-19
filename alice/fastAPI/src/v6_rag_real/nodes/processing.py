"""
문서 처리 노드들 (청킹, 임베딩, VectorDB 등)

✅ 핵심 노드들:
  1. chunk_all_documents: 섹션 기반 청킹 (□, ■, ● 마커 인식)
  2. embed_all_chunks: OpenAI Embedding API로 벡터 변환
  3. init_and_store_vectordb: Chroma VectorDB 저장
  4. extract_features_rag: RAG 기반 Feature 추출 (LLM 분석)
  5. save_to_csv: 로컬 파일 저장 (개발/테스트용)
"""

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
import chromadb
import numpy as np

from ..state_types import BatchState
from ..config import FEATURES, CSV_OUTPUT_DIR
from ..utils import chunk_by_sections

# OpenAI 클라이언트 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def chunk_all_documents(state: BatchState) -> BatchState:
    """
    모든 문서를 섹션 기반으로 청킹 (공고문 + 첨부서류)

    ✅ 핵심 기능: 문서를 의미있는 단위(섹션)로 분할
    📌 청킹 전략:
      - 섹션 마커 감지 (□, ■, ● 등)
      - 섹션이 없으면 고정 길이 청킹 (fallback)
      - MIN_CHUNK_LENGTH(50) 미만은 제외

    Returns:
        state['all_chunks']: 모든 청크 리스트
        - 청크마다 문서 메타데이터, 섹션 정보, 페이지 번호 포함
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

        # [2025-01-10 suyeon] page_texts 타입 체크 추가
        # 변경 이유:
        # 1. 타입 안정성: dict/list 모두 처리하여 AttributeError 방지
        # 2. 유연성: 문서 파싱 로직 변경 시에도 호환
        # 근거: page_texts가 dict 또는 list로 들어올 수 있음

        page_texts = doc.get('page_texts')
        if not page_texts:
            print(f"    ⚠️  page_texts가 없음 - 건너뜀")
            continue

        # 타입에 따라 순회 방식 분기
        if isinstance(page_texts, dict):
            page_items = page_texts.items()
        elif isinstance(page_texts, list):
            page_items = enumerate(page_texts, start=1)
        else:
            print(f"    ⚠️  잘못된 page_texts 타입: {type(page_texts)} - 건너뜀")
            continue

        # 페이지별로 청킹
        empty_page_count = 0
        for page_num, page_text in page_items:
            page_chunks = chunk_by_sections(page_text, page_num)

            # [2025-01-10 suyeon] 빈 페이지 처리 개선
            # 변경 이유:
            # 1. 가시성: 청크 생성 안된 페이지 명시적 로깅
            # 2. 디버깅: 왜 청크 수가 적은지 사용자가 파악 가능
            # 근거: 빈 페이지/짧은 페이지는 MIN_CHUNK_LENGTH(50)로 필터링됨
            if not page_chunks:
                empty_page_count += 1
                continue

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
        print(f"    ✓ {doc_chunk_count}개 청크 생성", end="")

        # 빈 페이지 경고 출력
        if empty_page_count > 0:
            print(f" (⚠️  {empty_page_count}개 페이지 건너뜀: 빈 페이지 또는 너무 짧음)")
        else:
            print()

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
    OpenAI Embedding API로 모든 청크를 임베딩 벡터로 변환

    ✅ 핵심 기능: 텍스트를 벡터로 변환하여 의미 검색 가능하게 만듦
    📌 사용 모델: text-embedding-3-small (1536 차원, $0.02/1M tokens)
    📌 배치 처리: 최대 2048개/요청으로 효율적 처리

    Returns:
        state['all_embeddings']: numpy array (shape: [N, 1536])
        state['embedding_model']: 'text-embedding-3-small'
    """
    all_chunks = state['all_chunks']

    print(f"\n{'='*60}")
    print(f"🧠 OpenAI 임베딩 생성 시작")
    print(f"{'='*60}")

    # 청크 텍스트 추출
    chunk_texts = [chunk['text'] for chunk in all_chunks]

    # OpenAI API 배치 임베딩 (최대 2048개/요청)
    batch_size = 2048
    total_chunks = len(chunk_texts)
    total_batches = (total_chunks + batch_size - 1) // batch_size

    print(f"\n  🔢 {total_chunks}개 청크 임베딩 중... (배치 크기: {batch_size}, 총 {total_batches}개 배치)")
    print(f"  📡 모델: text-embedding-3-small (1536 차원)")

    all_embeddings = []

    for i in range(0, total_chunks, batch_size):
        batch_num = i // batch_size + 1
        batch = chunk_texts[i:i+batch_size]

        print(f"    ⏳ 배치 {batch_num}/{total_batches} 처리 중... ({i+1}-{min(i+len(batch), total_chunks)}/{total_chunks} 청크)")

        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",  # 1536 차원, $0.02/1M tokens
                input=batch
            )

            # 임베딩 추출
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        except Exception as e:
            print(f"    ❌ 배치 {batch_num} 임베딩 실패: {str(e)}")
            state['errors'].append(f"임베딩 배치 {batch_num} 실패: {str(e)}")
            # 실패한 배치는 0 벡터로 채움
            all_embeddings.extend([[0.0] * 1536 for _ in batch])

    embeddings = np.array(all_embeddings)

    state['all_embeddings'] = embeddings
    state['embedding_model'] = 'text-embedding-3-small'  # API 모델명 저장
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

    ✅ 핵심 기능: RAG 검색을 위한 벡터 DB 생성 및 저장 (필수)
    """
    all_chunks = state['all_chunks']
    embeddings = state['all_embeddings']

    print(f"\n{'='*60}")
    print(f"💾 Chroma VectorDB 초기화 및 저장")
    print(f"{'='*60}")

    # Chroma DB 경로 설정
    # TODO: 운영 환경에서는 config.VECTOR_DB_DIR 또는 환경변수 사용 권장
    db_path = Path("./chroma_db")
    db_path.mkdir(exist_ok=True)

    # Chroma Client 생성
    print(f"\n  📂 VectorDB 경로: {db_path.absolute()}")
    client = chromadb.PersistentClient(path=str(db_path))

    # 컬렉션 이름
    collection_name = f"project_{state['project_idx']}"

    # 기존 컬렉션 삭제 (재실행 시 중복 방지)
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


def extract_features_rag(state: BatchState) -> BatchState:
    """
    RAG 기반 Feature 추출 (크로스 문서 검색)

    ✅ 핵심 기능: 공고문과 첨부서류를 종합적으로 분석하여 핵심 정보 추출
    📌 RAG 프로세스:
      1. Feature 키워드로 쿼리 임베딩 생성
      2. VectorDB 유사도 검색 (공고 + 첨부 통합, 상위 7개)
      3. 검색된 청크만 LLM에 전달 (토큰 절약)
      4. LLM이 구조화된 JSON으로 분석 결과 반환

    📋 추출 정보:
      - 핵심 내용 요약
      - key_points (요점 리스트)
      - writing_strategy (작성 전략 - 평가 포인트, 작성 팁, 주의사항)

    Returns:
        state['extracted_features']: 추출된 Feature 리스트
        - feature_code, feature_name, summary, full_content
        - key_points, writing_strategy
        - RAG 메타데이터 (사용된 청크, 유사도 등)
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

            # OpenAI API로 쿼리 임베딩
            query_response = client.embeddings.create(
                model="text-embedding-3-small",
                input=[query_text]
            )
            query_embedding = [query_response.data[0].embedding]

            # 2️⃣ VectorDB 유사도 검색
            results = collection.query(
                query_embeddings=query_embedding,
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
            system_prompt = f"""당신은 정부 R&D 사업계획서 작성 컨설턴트입니다.
공고문 및 첨부서류를 분석하여 '{feature_def['feature_type']}'에 대한 실질적인 작성 전략을 제시해야 합니다.

[분석 대상]
- Feature: {feature_def['feature_type']}
- 설명: {feature_def['description']}

다음 정보를 JSON 형식으로 반환하세요:
{{
  "found": true/false,
  "title": "섹션 제목",
  "content": "추출된 핵심 내용 요약 (200자 이내)",
  "full_content": "전체 내용",
  "key_points": ["핵심 요점 1", "핵심 요점 2"],
  "writing_strategy": {{
    "overview": "이 섹션 작성 시 평가위원이 중요하게 보는 핵심 포인트 (2-3문장)",
    "writing_tips": ["효과적인 작성 팁 1", "효과적인 작성 팁 2", "효과적인 작성 팁 3"],
    "common_mistakes": ["자주 발생하는 실수 1", "피해야 할 오류 2"],
    "example_phrases": ["좋은 작성 예시 문구 1", "좋은 작성 예시 문구 2"]
  }}
}}

**해당 내용을 찾을 수 없으면 found를 false로 반환하세요.**"""

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
                    'writing_strategy': result.get('writing_strategy', {}),  # ✅ 작성 전략 추가

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
# [2025-01-10 suyeon] match_cross_references 함수 삭제
# 삭제 이유:
# 1. 현재 미사용: graph.py에서 노드로 등록되지 않음 (주석 처리됨)
# 2. MVP2 재구현 예정: 현재 코드는 참고용이었으나 Git 히스토리에 보존
# 3. 코드베이스 간소화: 115줄 삭제로 유지보수성 향상
# 근거: MVP2에서 분석 대시보드 구현 시 새로운 구조로 재작성 예정


def save_to_csv(state: BatchState) -> BatchState:
    """
    분석 결과를 로컬 파일로 저장 (개발/테스트용)

    ⚠️ 운영 환경: Backend API 호출(build_response)이 Oracle DB 저장을 담당
    📁 로컬 저장: 개발 중 디버깅, 테스트 결과 확인용

    저장 파일:
    1. ANALYSIS_RESULT_{timestamp}.csv - Feature 추출 결과 (RAG + LLM 분석)
    2. ANALYSIS_RESULT_{timestamp}.json - Feature 추출 결과 (JSON)
    3. table_of_contents_{timestamp}.json - 목차 정보 (JSON)
    """

    print(f"\n{'='*60}")
    print(f"💾 분석 결과 로컬 저장 (개발/테스트용)")
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
                'writing_strategy': feature.get('writing_strategy', {}),  # ✅ 작성 전략 추가
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
                'writing_strategy': json.dumps(feature.get('writing_strategy', {}), ensure_ascii=False),  # ✅ JSON 문자열로 저장
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
