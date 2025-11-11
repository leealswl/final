"""
프로덕션 v6_rag 설정 검증 스크립트
"""

import os
import sys
from pathlib import Path

def verify_setup():
    """프로덕션 설정 검증"""
    print("=" * 60)
    print("FastAPI v6 프로덕션 설정 검증")
    print("=" * 60)

    issues = []

    # 1. 필수 파일 존재 확인
    print("\n1️⃣ 필수 파일 확인")
    required_files = [
        "src/fastAPI_v6_integrated.py",
        "src/config/__init__.py",
        "src/config/settings.py",
        "src/v6_rag_real/__init__.py",
        "src/v6_rag_real/graph.py",
        "src/v6_rag_real/state_types.py",
        "src/v6_rag_real/nodes/extract.py",
        "src/v6_rag_real/nodes/processing.py",
        "src/v6_rag_real/nodes/template_detection.py",
        "src/v6_rag_real/nodes/toc_extraction.py",
        "src/v6_rag_real/nodes/oracle_storage.py",
        "src/v6_rag_real/nodes/response.py",
        "requirements.txt",
        ".env.example"
    ]

    for file in required_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - 파일 없음")
            issues.append(f"Missing file: {file}")

    # 2. 패키지 import 테스트
    print("\n2️⃣ 패키지 import 테스트")
    try:
        # sys.path에 src 추가
        sys.path.insert(0, str(Path(__file__).parent / "src"))

        from v6_rag_real import create_batch_graph
        print("  ✅ v6_rag_real.create_batch_graph")

        from v6_rag_real.nodes import (
            extract_all_texts,
            save_to_csv,
            save_to_oracle
        )
        print("  ✅ v6_rag_real.nodes (extract, save_to_csv, save_to_oracle)")

    except ImportError as e:
        print(f"  ❌ Import 실패: {e}")
        issues.append(f"Import error: {e}")

    # 3. 환경 변수 확인
    print("\n3️⃣ 환경 변수 확인")
    storage_mode = os.getenv('STORAGE_MODE', 'csv')
    print(f"  STORAGE_MODE: {storage_mode}")

    if storage_mode == 'oracle':
        oracle_user = os.getenv('ORACLE_USER')
        oracle_password = os.getenv('ORACLE_PASSWORD')
        oracle_dsn = os.getenv('ORACLE_DSN')

        if not oracle_user:
            print("  ⚠️  ORACLE_USER 미설정")
            issues.append("Missing ORACLE_USER")
        else:
            print(f"  ✅ ORACLE_USER: {oracle_user}")

        if not oracle_password:
            print("  ⚠️  ORACLE_PASSWORD 미설정")
            issues.append("Missing ORACLE_PASSWORD")
        else:
            print("  ✅ ORACLE_PASSWORD: ****")

        if not oracle_dsn:
            print("  ⚠️  ORACLE_DSN 미설정")
            issues.append("Missing ORACLE_DSN")
        else:
            print(f"  ✅ ORACLE_DSN: {oracle_dsn}")
    else:
        print("  ✅ CSV 모드 (Oracle 설정 불필요)")

    # 4. 결과 요약
    print("\n" + "=" * 60)
    if issues:
        print(f"❌ 검증 실패: {len(issues)}개 이슈")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ 모든 검증 통과!")
        print("\n실행 명령:")
        print("  cd src")
        print("  python fastAPI_v6_integrated.py")
        return True

if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)
