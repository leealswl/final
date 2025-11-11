"""
Oracle DB 저장 노드
실제 서비스 환경에서 분석 결과를 DB에 저장
"""

import json
from datetime import datetime
from typing import Dict, Any

# Oracle 드라이버 (설치 필요: pip install cx_Oracle)
try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False
    print("⚠️ cx_Oracle 미설치: pip install cx_Oracle")

from ..state_types import BatchState


def save_to_oracle(state: BatchState) -> BatchState:
    """
    분석 결과를 Oracle DB에 저장

    저장 테이블:
    1. ANALYSIS_RESULT - Feature 추출 결과
    2. TABLE_OF_CONTENTS - 목차 정보 (JSON)
    3. DOCUMENTS - 문서 메타데이터 (선택)

    Returns:
        state: oracle_ids 필드 업데이트된 State
    """

    print(f"\n{'='*60}")
    print(f"💾 Oracle DB 저장")
    print(f"{'='*60}")

    # Oracle 설정 확인
    oracle_config = state.get('oracle_config')
    if not oracle_config:
        print("  ⚠️  Oracle 설정 없음, 저장 스킵")
        state['status'] = 'oracle_skipped'
        return state

    if not ORACLE_AVAILABLE:
        error_msg = "cx_Oracle 라이브러리 없음"
        print(f"  ❌ {error_msg}")
        state['errors'].append(error_msg)
        state['status'] = 'oracle_unavailable'
        return state

    try:
        # ========================================
        # 1. Oracle 연결
        # ========================================
        print(f"\n  🔌 Oracle 연결 중...")
        conn = cx_Oracle.connect(
            oracle_config['user'],
            oracle_config['password'],
            oracle_config['dsn']
        )
        cursor = conn.cursor()
        print(f"    ✓ 연결 성공")

        project_idx = state['project_idx']
        user_id = state['user_id']

        # ========================================
        # 2. ANALYSIS_RESULT 테이블에 Feature 저장
        # ========================================
        print(f"\n  📊 ANALYSIS_RESULT 저장 중...")
        inserted_features = 0

        for feature in state['extracted_features']:
            cursor.execute("""
                INSERT INTO ANALYSIS_RESULT (
                    project_idx,
                    feature_code,
                    feature_name,
                    title,
                    summary,
                    full_content,
                    key_points,
                    vector_similarity,
                    chunks_from_announcement,
                    chunks_from_attachments,
                    referenced_attachments,
                    extracted_at
                ) VALUES (
                    :project_idx,
                    :feature_code,
                    :feature_name,
                    :title,
                    :summary,
                    :full_content,
                    :key_points,
                    :vector_similarity,
                    :chunks_from_announcement,
                    :chunks_from_attachments,
                    :referenced_attachments,
                    TO_DATE(:extracted_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                )
            """, {
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
                'extracted_at': feature.get('extracted_at', datetime.now().isoformat())[:19]  # 초까지만
            })
            inserted_features += 1

        print(f"    ✓ {inserted_features}개 Feature 저장 완료")

        # ========================================
        # 3. TABLE_OF_CONTENTS 테이블에 목차 저장 (JSON)
        # ========================================
        toc = state.get('table_of_contents')
        toc_saved = False

        if toc:
            print(f"\n  📑 TABLE_OF_CONTENTS 저장 중...")

            # Oracle JSON 타입 또는 CLOB로 저장
            cursor.execute("""
                INSERT INTO TABLE_OF_CONTENTS (
                    project_idx,
                    source,
                    total_sections,
                    toc_data,
                    created_at
                ) VALUES (
                    :project_idx,
                    :source,
                    :total_sections,
                    :toc_data,
                    SYSDATE
                )
            """, {
                'project_idx': project_idx,
                'source': toc.get('source', 'unknown'),
                'total_sections': toc.get('total_sections', 0),
                'toc_data': json.dumps(toc, ensure_ascii=False)  # JSON → 문자열
            })

            toc_saved = True
            print(f"    ✓ 목차 저장 완료 (출처: {toc.get('source', 'unknown')})")
        else:
            print(f"\n  ⚠️  목차 없음, TABLE_OF_CONTENTS 저장 스킵")

        # ========================================
        # 4. 커밋 및 연결 종료
        # ========================================
        conn.commit()
        cursor.close()
        conn.close()

        # State 업데이트
        state['oracle_ids'] = {
            'features_count': inserted_features,
            'toc_saved': toc_saved,
            'saved_at': datetime.now().isoformat()
        }
        state['status'] = 'oracle_saved'

        print(f"\n  ✅ Oracle 저장 완료")
        print(f"    - Features: {inserted_features}개")
        print(f"    - TOC: {'저장됨' if toc_saved else '없음'}")

    except cx_Oracle.DatabaseError as e:
        error_msg = f"Oracle DB 에러: {str(e)}"
        print(f"\n  ❌ {error_msg}")
        state['errors'].append(error_msg)
        state['status'] = 'oracle_error'

        # 연결 정리
        try:
            conn.rollback()
            cursor.close()
            conn.close()
        except:
            pass

    except Exception as e:
        error_msg = f"Oracle 저장 실패: {str(e)}"
        print(f"\n  ❌ {error_msg}")
        state['errors'].append(error_msg)
        state['status'] = 'oracle_error'

    return state
