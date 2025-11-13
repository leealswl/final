"""
Oracle 연결 테스트 스크립트
2025-11-09 suyeon: Oracle DB 연결 및 테이블 확인
"""

import cx_Oracle
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

print("✅ cx_Oracle 사용 (Oracle 11g XE 호환)")

# Oracle 설정
oracle_config = {
    'user': os.getenv('ORACLE_USER'),
    'password': os.getenv('ORACLE_PASSWORD'),
    'dsn': os.getenv('ORACLE_DSN')
}

print(f"\n📋 Oracle 연결 정보:")
print(f"  - User: {oracle_config['user']}")
print(f"  - DSN: {oracle_config['dsn']}")

try:
    # 연결 시도
    print(f"\n🔌 Oracle 연결 중...")
    conn = cx_Oracle.connect(
        user=oracle_config['user'],
        password=oracle_config['password'],
        dsn=oracle_config['dsn']
    )
    cursor = conn.cursor()
    print(f"✅ 연결 성공!")

    # 테이블 존재 여부 확인
    print(f"\n📊 테이블 존재 여부 확인:")

    # ANALYSIS_RESULT 테이블 확인
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM user_tables
            WHERE table_name = 'ANALYSIS_RESULT'
        """)
        count = cursor.fetchone()[0]
        print(f"  - ANALYSIS_RESULT 테이블: {'존재 ✅' if count > 0 else '없음 ❌'}")

        if count > 0:
            # 테이블 구조 확인
            cursor.execute("""
                SELECT column_name, data_type, data_length, nullable
                FROM user_tab_columns
                WHERE table_name = 'ANALYSIS_RESULT'
                ORDER BY column_id
            """)
            print(f"\n  📝 ANALYSIS_RESULT 테이블 구조:")
            for col in cursor.fetchall():
                print(f"    - {col[0]}: {col[1]}({col[2]}) {'NULL' if col[3] == 'Y' else 'NOT NULL'}")
    except Exception as e:
        print(f"  ❌ ANALYSIS_RESULT 테이블 확인 실패: {e}")

    # TABLE_OF_CONTENTS 테이블 확인
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM user_tables
            WHERE table_name = 'TABLE_OF_CONTENTS'
        """)
        count = cursor.fetchone()[0]
        print(f"\n  - TABLE_OF_CONTENTS 테이블: {'존재 ✅' if count > 0 else '없음 ❌'}")

        if count > 0:
            # 테이블 구조 확인
            cursor.execute("""
                SELECT column_name, data_type, data_length, nullable
                FROM user_tab_columns
                WHERE table_name = 'TABLE_OF_CONTENTS'
                ORDER BY column_id
            """)
            print(f"\n  📝 TABLE_OF_CONTENTS 테이블 구조:")
            for col in cursor.fetchall():
                print(f"    - {col[0]}: {col[1]}({col[2]}) {'NULL' if col[3] == 'Y' else 'NOT NULL'}")
    except Exception as e:
        print(f"  ❌ TABLE_OF_CONTENTS 테이블 확인 실패: {e}")

    # 데이터 개수 확인
    print(f"\n📈 현재 저장된 데이터 개수:")
    try:
        cursor.execute("SELECT COUNT(*) FROM ANALYSIS_RESULT")
        count = cursor.fetchone()[0]
        print(f"  - ANALYSIS_RESULT: {count}개")
    except:
        print(f"  - ANALYSIS_RESULT: 테이블 없음")

    try:
        cursor.execute("SELECT COUNT(*) FROM TABLE_OF_CONTENTS")
        count = cursor.fetchone()[0]
        print(f"  - TABLE_OF_CONTENTS: {count}개")
    except:
        print(f"  - TABLE_OF_CONTENTS: 테이블 없음")

    cursor.close()
    conn.close()

except cx_Oracle.DatabaseError as e:
    print(f"\n❌ Oracle 연결 실패:")
    print(f"  {e}")
except Exception as e:
    print(f"\n❌ 오류 발생:")
    print(f"  {e}")
