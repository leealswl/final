#!/usr/bin/env python3
"""
목차 추출 모듈 테스트 스크립트
코드 수정 후 안정성 확인
"""

import sys
import os

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'alice', 'fastAPI', 'src'))

def test_imports():
    """모듈 import 테스트"""
    print("=" * 80)
    print("1️⃣ 모듈 Import 테스트")
    print("=" * 80)
    
    try:
        from v6_rag_real.nodes import toc_extraction
        print("✅ toc_extraction 모듈 import 성공")
    except Exception as e:
        print(f"❌ toc_extraction import 실패: {e}")
        return False
    
    try:
        from v6_rag_real.nodes import toc_util
        print("✅ toc_util 모듈 import 성공")
    except Exception as e:
        print(f"❌ toc_util import 실패: {e}")
        return False
    
    return True


def test_utility_functions():
    """유틸리티 함수 테스트"""
    print("\n" + "=" * 80)
    print("2️⃣ 유틸리티 함수 테스트")
    print("=" * 80)
    
    from v6_rag_real.nodes.toc_util import (
        find_proposal_template,
        find_toc_table,
        parse_toc_table,
        extract_sections_from_symbols,
        create_default_toc
    )
    
    # 1. create_default_toc 테스트
    try:
        default_toc = create_default_toc()
        assert isinstance(default_toc, dict)
        assert 'sections' in default_toc
        assert len(default_toc['sections']) > 0
        print("✅ create_default_toc() 정상 동작")
    except Exception as e:
        print(f"❌ create_default_toc() 실패: {e}")
        return False
    
    # 2. find_proposal_template 테스트 (빈 리스트)
    try:
        result = find_proposal_template([])
        assert result is None
        print("✅ find_proposal_template([]) 정상 동작 (None 반환)")
    except Exception as e:
        print(f"❌ find_proposal_template([]) 실패: {e}")
        return False
    
    # 3. find_proposal_template 테스트 (None 체크)
    try:
        result = find_proposal_template(None)
        assert result is None
        print("✅ find_proposal_template(None) 정상 동작 (None 반환)")
    except Exception as e:
        print(f"❌ find_proposal_template(None) 실패: {e}")
        return False
    
    # 4. find_toc_table 테스트 (빈 리스트)
    try:
        result = find_toc_table([])
        assert result is None
        print("✅ find_toc_table([]) 정상 동작 (None 반환)")
    except Exception as e:
        print(f"❌ find_toc_table([]) 실패: {e}")
        return False
    
    # 5. parse_toc_table 테스트 (빈 데이터)
    try:
        result = parse_toc_table([])
        assert isinstance(result, list)
        assert len(result) == 0
        print("✅ parse_toc_table([]) 정상 동작 (빈 리스트 반환)")
    except Exception as e:
        print(f"❌ parse_toc_table([]) 실패: {e}")
        return False
    
    # 6. extract_sections_from_symbols 테스트 (빈 텍스트)
    try:
        result = extract_sections_from_symbols("")
        assert isinstance(result, list)
        print("✅ extract_sections_from_symbols('') 정상 동작")
    except Exception as e:
        print(f"❌ extract_sections_from_symbols('') 실패: {e}")
        return False
    
    return True


def test_edge_cases():
    """엣지 케이스 테스트"""
    print("\n" + "=" * 80)
    print("3️⃣ 엣지 케이스 테스트")
    print("=" * 80)
    
    from v6_rag_real.nodes.toc_util import (
        find_proposal_template,
        find_toc_table,
        parse_toc_table
    )
    
    # 1. 잘못된 데이터 타입 테스트
    try:
        result = find_proposal_template([None, {}, []])
        print("✅ find_proposal_template(잘못된 데이터) 정상 처리")
    except Exception as e:
        print(f"❌ find_proposal_template(잘못된 데이터) 실패: {e}")
        return False
    
    # 2. table에 'data' 키가 없는 경우
    try:
        result = find_toc_table([{'no_data': True}])
        assert result is None
        print("✅ find_toc_table('data' 키 없음) 정상 처리")
    except Exception as e:
        print(f"❌ find_toc_table('data' 키 없음) 실패: {e}")
        return False
    
    # 3. parse_toc_table에 None 포함된 경우
    try:
        result = parse_toc_table([['번호', '제목'], None, ['1', '테스트']])
        assert isinstance(result, list)
        print("✅ parse_toc_table(None 포함) 정상 처리")
    except Exception as e:
        print(f"❌ parse_toc_table(None 포함) 실패: {e}")
        return False
    
    return True


def test_main_functions():
    """메인 함수 시그니처 테스트"""
    print("\n" + "=" * 80)
    print("4️⃣ 메인 함수 시그니처 테스트")
    print("=" * 80)
    
    from v6_rag_real.nodes import toc_extraction
    
    # 함수들이 존재하는지 확인
    functions = [
        'route_toc_extraction',
        'extract_toc_from_template',
        'extract_toc_from_announcement_and_attachments'
    ]
    
    for func_name in functions:
        try:
            func = getattr(toc_extraction, func_name)
            assert callable(func)
            print(f"✅ {func_name}() 함수 존재 확인")
        except Exception as e:
            print(f"❌ {func_name}() 함수 없음: {e}")
            return False
    
    return True


def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 80)
    print("🧪 목차 추출 모듈 테스트 시작")
    print("=" * 80)
    
    tests = [
        ("Import 테스트", test_imports),
        ("유틸리티 함수 테스트", test_utility_functions),
        ("엣지 케이스 테스트", test_edge_cases),
        ("메인 함수 시그니처 테스트", test_main_functions),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{status}: {test_name}")
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과 ({passed}/{total})")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())

