"""
공고 기반 목차 추출 모듈
양식이 없을 때 공고문과 첨부서류에서 목차를 유추하는 로직
"""

import json
from typing import List, Dict, Tuple
from datetime import datetime

from .toc_util import client


def prepare_announcement_context(state: Dict, collection) -> Tuple[str, List[Dict]]:
    """
    공고문 + 첨부서류에서 RAG 검색으로 관련 청크 수집

    Returns:
        (submission_content, all_chunks) 튜플
    """
    all_features = state.get('extracted_features', [])

    # 1️⃣ 제출서류 feature 찾기
    submission_features = [
        f for f in all_features
        if isinstance(f, dict) and f.get('feature_code') == 'submission_docs'
    ]

    if not submission_features:
        return '', []

    submission_content = '\n\n'.join([
        f.get('full_content', '') for f in submission_features
    ])

    # 2️⃣ RAG 검색
    try:
        query_text = "제출서류 작성항목 구성 목차 제안서 계획서 사업계획서 운영계획"
        query_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[query_text]
        )
        query_embedding = [query_response.data[0].embedding]

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=25
        )

        all_chunks = []
        if results and results.get('ids') and results['ids'][0]:
            ids = results['ids'][0]
            documents = results.get('documents', [[]])[0] if results.get('documents') else []
            metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []

            for i in range(len(ids)):
                if i < len(documents) and i < len(metadatas):
                    metadata = metadatas[i] if isinstance(metadatas[i], dict) else {}
                    all_chunks.append({
                        'text': documents[i] if i < len(documents) else '',
                        'file': metadata.get('file_name', 'UNKNOWN'),
                        'section': metadata.get('section', 'UNKNOWN'),
                        'doc_type': metadata.get('document_type', 'UNKNOWN')
                    })
            print(f"    ✅ RAG 검색 완료: {len(all_chunks)}개 청크 (공고 + 첨부서류)")
    except Exception as e:
        print(f"    ✗ RAG 검색 실패: {e}")
        all_chunks = []

    return submission_content, all_chunks


def build_announcement_prompt(
    announcement_text: str,
    submission_content: str,
    document_context: str
) -> Tuple[str, str]:
    """
    공고 분석용 LLM 프롬프트 생성
    """
    system_prompt = """당신은 정부 지원사업 공고 분석 전문가입니다.

공고문과 첨부서류를 분석하여 **신청 시 제출해야 하는 계획서의 작성 항목(목차)**를 추출하세요.

⚠️ 중요: 공고의 성격을 먼저 파악하세요:
- 연구개발(R&D) 과제 공고 → 연구계획서 목차
- 창업지원 사업 공고 → 사업계획서 목차
- 주관기관 선정 공고 → 주관기관 사업계획서 목차
- 기타 지원사업 공고 → 해당 사업의 계획서 목차

⚠️ 다음을 구분해야 합니다:
- ❌ 제출 서류명 (예: "연구계획서", "신청서", "동의서") → 포함하지 마세요
- ✅ 작성 항목/목차 (예: "사업 추진계획", "운영 전략", "예산 편성") → 이것만 포함하세요

📋 목차 생성 요구사항:
1. **최소 10-15개 이상의 섹션을 생성**하세요 (너무 적으면 안 됩니다)
2. **계층 구조를 포함**하세요 (1, 1.1, 1.2, 2, 2.1, 2.2 등)
3. 공고의 성격에 맞는 **표준 목차 구조**를 참고하되, 실제 공고 내용을 반영하세요

📚 공고 유형별 표준 목차 구조 참고:

【연구개발(R&D) 과제】
1. 연구개발과제의 개요 (필수)
   1.1. 과제의 필요성
   1.2. 과제의 목표
2. 연구개발 목표 및 내용 (필수)
   2.1. 연구개발 목표
   2.2. 연구개발 내용
   2.3. 기술적 해결과제
3. 연구개발 추진체계 및 일정 (필수)
   3.1. 추진체계
   3.2. 연구일정
   3.3. 인력운용계획
4. 연구개발 성과 활용방안 (필수)
   4.1. 기대효과
   4.2. 활용방안
5. 소요예산 및 자금계획 (필수)
   5.1. 예산계획
   5.2. 자금조달계획

【창업지원/사업계획서】
1. 사업 개요 (필수)
   1.1. 사업 배경 및 필요성
   1.2. 사업 목표
2. 사업 모델 (필수)
   2.1. 사업 아이템
   2.2. 사업 전략
3. 추진 계획 (필수)
   3.1. 운영 계획
   3.2. 마케팅 계획
4. 조직 및 인력 (필수)
   4.1. 조직 구성
   4.2. 인력 운영
5. 재무 계획 (필수)
   5.1. 매출 계획
   5.2. 자금 계획

【주관기관/운영기관 선정】
1. 기관 개요 (필수)
   1.1. 기관 현황
   1.2. 조직 구성
2. 운영 계획 (필수)
   2.1. 프로그램 기획
   2.2. 운영 전략
3. 추진 체계 (필수)
   3.1. 조직 체계
   3.2. 인력 운용
4. 예산 및 자금 계획 (필수)
   4.1. 예산 편성
   4.2. 자금 관리

다음 형식으로 JSON 반환:
{
  "sections": [
    {
      "number": "1",
      "title": "사업 추진 개요",
      "required": true,
      "description": "사업의 목적과 필요성"
    },
    {
      "number": "1.1",
      "title": "사업 배경 및 필요성",
      "required": true,
      "description": "사업을 추진하는 배경과 필요성"
    },
    {
      "number": "2",
      "title": "운영 계획 및 전략",
      "required": true,
      "description": "구체적인 운영 방안과 추진 전략"
    }
  ]
}

⚠️ 중요 주의사항:
- 제출 서류의 "이름"이 아닌, 서류 "내부의 작성 항목"을 추출하세요
- 공고의 실제 내용(연구개발/창업지원/주관기관선정 등)을 반영한 목차를 생성하세요
- 섹션 번호는 "1", "1.1", "1.2", "2", "가" 등 계층 구조 형식 유지
- required는 필수 작성 항목 여부
- **반드시 10개 이상의 섹션을 생성**하되, 공고 내용에 근거하여 생성하세요"""

    submission_text_limit = submission_content[:3000]
    document_context_limit = document_context[:4000] if document_context else '(첨부서류 없음)'

    user_prompt = f"""## 공고문 내용

{announcement_text}

## 제출서류 요구사항

{submission_text_limit}

## 첨부서류 관련 내용 (양식/계획서의 작성 항목)

{document_context_limit}

---

## 📋 분석 및 목차 생성 지침

### 1단계: 공고 성격 파악
다음 중 해당하는 항목을 파악하세요:
- [ ] 연구개발(R&D) 과제 공고
- [ ] 창업지원/벤처 지원 사업 공고
- [ ] 주관기관/운영기관 선정 공고
- [ ] 기타 지원사업 공고

### 2단계: 목차 구조 생성
위에서 파악한 공고 성격에 맞는 표준 목차 구조를 참고하되, **공고문과 첨부서류에서 언급된 구체적인 작성 항목**을 반드시 반영하세요.

**⚠️ 반드시 준수할 사항:**
1. **최소 10-15개 이상의 섹션 생성** (계층 구조 포함 시 15-20개 이상)
2. **계층 구조 필수 포함**:
   - 1차 섹션: "1", "2", "3" 등
   - 2차 섹션: "1.1", "1.2", "2.1", "2.2" 등
   - 3차 섹션 (필요시): "1.1.1", "1.1.2" 등
3. **공고 내용 기반 생성**: 표준 구조를 참고하되, 공고문과 첨부서류에서 실제로 언급된 항목을 우선 반영
4. **"서류명"이 아닌 "작성 항목"만 추출**:
   - ❌ 잘못된 목차: ["사업계획서", "신청서", "동의서", "첨부자료"]
   - ✅ 올바른 목차: ["사업 추진 개요", "운영 계획", "예산 편성", "추진 체계"]

### 3단계: 구체적인 예시

**연구개발 과제 예시:**
```
1. 연구개발과제의 개요
   1.1. 과제의 필요성 및 배경
   1.2. 과제의 목표
   1.3. 기대효과
2. 연구개발 목표 및 내용
   2.1. 연구개발 목표
   2.2. 연구개발 내용
   2.3. 기술적 해결과제
   2.4. 핵심기술 요소
3. 연구개발 추진체계 및 일정
   3.1. 추진체계
   3.2. 연구일정 (Gantt 차트 포함)
   3.3. 인력운용계획
   3.4. 역할 분담
4. 연구개발 성과 활용방안
   4.1. 기대효과
   4.2. 활용방안
   4.3. 사업화 계획
5. 소요예산 및 자금계획
   5.1. 예산계획 (연도별)
   5.2. 자금조달계획
   5.3. 예산 집행 계획
```

**⚠️ 주의: 위 예시는 참고용이며, 실제 공고문과 첨부서류의 내용을 반영하여 생성하세요.**

위 내용을 종합적으로 분석하여 신청자가 작성해야 할 계획서의 **상세한 목차(최소 10-15개 섹션, 계층 구조 포함)**를 JSON 형식으로 생성해주세요."""

    return system_prompt, user_prompt


def generate_toc_from_announcement(
    submission_content: str,
    all_chunks: List[Dict],
    state: Dict
) -> Dict:
    """
    공고문 기반 목차 생성 (LLM 호출)
    """
    print(f"    🤖 LLM으로 목차 구조 생성 중...")

    # 문서 타입별 컨텍스트 정리
    document_context = '\n\n'.join([
        f"[{c['doc_type']} - {c['file']} - {c['section']}]\n{c['text']}"
        for c in all_chunks[:20]
    ])

    # 공고문 전체 내용 가져오기
    documents = state.get('documents', [])
    announcement_docs = [d for d in documents if d.get('document_type') == 'ANNOUNCEMENT']
    announcement_text = ''
    if announcement_docs:
        announcement_text = announcement_docs[0].get('text', '')[:5000]

    system_prompt, user_prompt = build_announcement_prompt(
        announcement_text,
        submission_content,
        document_context
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        # JSON 파싱
        try:
            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM 응답 내용이 비어있음")
            result = json.loads(content)
        except (json.JSONDecodeError, ValueError, AttributeError, IndexError) as e:
            print(f"\n  ✗ LLM 응답 파싱 실패: {e}")
            raise

        if not result.get('sections'):
            print(f"\n  ✗ LLM 결과에 섹션 없음")
            raise ValueError("섹션이 없습니다.")

        toc = {
            'source': 'announcement',
            'extraction_method': 'rag_llm',
            'inference_confidence': 0.7,
            'sections': result['sections'],
            'total_sections': len(result['sections']),
            'extracted_at': datetime.now().isoformat()
        }

        print(f"\n  ✅ LLM으로 {len(result['sections'])}개 섹션 생성 완료")
        for sec in result['sections'][:5]:
            print(f"    • {sec.get('number', '')} {sec.get('title', '')}")
        if len(result['sections']) > 5:
            print(f"    ... 외 {len(result['sections']) - 5}개")

        return toc

    except Exception as e:
        print(f"\n  ✗ LLM 호출 실패: {e}")
        raise
