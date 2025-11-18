"""
목차(Table of Contents) 추출 모듈
제안서 양식 또는 공고문/첨부서류에서 목차 구조 추출
"""

import re
import json
import unicodedata
from datetime import datetime
from typing import List, Dict, Any, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv

from ..state_types import BatchState

# OpenAI 클라이언트 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def route_toc_extraction(state: BatchState) -> str:
    """
    목차 추출 방법 결정 (조건부 라우팅)

    Returns:
        "extract_toc_from_template" - 양식 기반 추출
        "extract_toc_from_announcement_and_attachments" - 공고 + 첨부서류 기반 추출
    """
    templates = state.get('attachment_templates', [])
    proposal_template = _find_proposal_template(templates)

    if proposal_template:
        return "extract_toc_from_template"
    else:
        return "extract_toc_from_announcement_and_attachments"


# 라우팅할때 양식 찾기
def _find_proposal_template(templates: List[Dict]) -> Optional[Dict]:
    """
    제안서 양식 찾기 (우선순위: 제안서 > 계획서 > 신청서)
    """
    if not templates:
        return None

    # 양식으로 감지된 것만 필터링
    valid_templates = [t for t in templates if t.get('has_template')]

    if not valid_templates:
        return None

    # 우선순위/가중치 계산
    def template_priority(template: Dict) -> float:
        file_name = template.get('file_name', '')
        score = template.get('confidence_score', 0.0)

        # 파일명 키워드 가중치
        keyword_weights = {
            '계획서': 1.0,
            '제안서': 0.8,
            '신청서': 0.6,
            '양식': 0.2
        }
        for keyword, weight in keyword_weights.items():
            if keyword in file_name:
                score += weight

        # 첨부 번호가 2 (붙임2)면 추가 가중치
        attachment_num = template.get('attachment_number')
        if attachment_num == 2:
            score += 0.3

        return score

    # 계획서가 포함된 템플릿이 있으면 최우선 반환
    for template in valid_templates:
        if '계획서' in template.get('file_name', ''):
            return template

    # 그 외는 최고 점수 템플릿 반환
    return max(valid_templates, key=template_priority)


def extract_toc_from_template(state: BatchState) -> BatchState:
    """
    제안서 양식에서 목차 추출 (LangGraph 노드)

    방법:
    1. 표 구조에서 목차 섹션 찾기 (키워드: "목차", "작성항목", "구성")
    2. 각 행에서 섹션 번호, 제목, 페이지 번호 추출
    3. 계층 구조 파싱 (1. → 1.1. → 1.1.1.)

    Returns:
        state: table_of_contents 업데이트된 BatchState
    """
    print(f"\n{'='*60}")
    print(f"📑 양식에서 목차 추출")
    print(f"{'='*60}")

    # 양식 찾기
    templates = state.get('attachment_templates', [])
    template = _find_proposal_template(templates)

    if not template:
        print(f"\n  ⚠️  양식을 찾을 수 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = _create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    print(f"\n  📋 양식: {template['file_name']}")

    tables = template.get('tables', [])
    if not tables:
        print(f"  ✗ 표 구조 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = _create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    # 목차 관련 표 찾기
    toc_table = _find_toc_table(tables)

    if not toc_table:
        print(f"  ⚠️  목차 표 찾기 실패 → LLM 기반 추출 시도")
        # LLM으로 양식 텍스트 전체 분석
        return _extract_toc_from_template_with_llm(state, template)

    # 표에서 섹션 추출
    sections = _parse_toc_table(toc_table['data'])

    if not sections:
        print(f"  ⚠️  섹션 파싱 실패 → LLM 기반 추출 시도")
        # LLM으로 양식 텍스트 전체 분석
        return _extract_toc_from_template_with_llm(state, template)

    toc = {
        'source': 'template',
        'source_file': template['file_name'],
        'extraction_method': 'table_parsing',
        'sections': sections,
        'total_sections': len(sections),
        'has_page_numbers': any(s.get('page') for s in sections),
        'extracted_at': datetime.now().isoformat()
    }

    state['table_of_contents'] = toc
    state['status'] = 'toc_extracted'

    print(f"\n  ✅ 양식에서 {len(sections)}개 섹션 추출 완료")
    for sec in sections[:5]:
        print(f"    • {sec.get('number', '')} {sec.get('title', '')}")
    if len(sections) > 5:
        print(f"    ... 외 {len(sections) - 5}개")

    return state


def _find_toc_table(tables: List[Dict]) -> Optional[Dict]:
    """
    목차 관련 표 찾기

    조건:
    - 첫 번째 행에 "목차", "작성항목", "구성", "항목" 등 키워드 포함
    - 또는 번호(1., 2., 가., 나.) 패턴이 많이 포함된 표
    """
    TOC_KEYWORDS = ['목차', '작성항목', '구성', '항목', '내용', '제출서류']

    for table in tables:
        data = table['data']
        if not data or len(data) < 2:
            continue

        # 첫 번째 행 검사
        first_row = ' '.join([str(cell) for cell in data[0] if cell])

        if any(kw in first_row for kw in TOC_KEYWORDS):
            return table

        # 전체 데이터에서 번호 패턴 비율 체크
        all_text = '\n'.join([' '.join([str(cell) for cell in row if cell]) for row in data])
        number_pattern_count = len(re.findall(r'\d+\.|가\.|나\.|다\.|①|②|③', all_text))

        if number_pattern_count >= len(data) * 0.3:  # 행의 30% 이상이 번호 패턴
            return table

    return None


def _parse_toc_table(table_data: List[List[str]]) -> List[Dict]:
    """
    목차 표에서 섹션 정보 추출

    Args:
        table_data: 2차원 리스트 [[cell, cell, ...], ...]

    Returns:
        섹션 리스트 [{'number': '1', 'title': '연구목적', 'page': 3}, ...]
    """
    sections = []

    # 헤더 스킵 (첫 번째 행)
    for row_idx, row in enumerate(table_data[1:], start=1):
        if not row or not any(row):  # 빈 행 스킵
            continue

        row_text = ' '.join([str(cell).strip() for cell in row if cell])

        # 섹션 번호 추출 (패턴: 1., 1.1., 가., ①, I., 등)
        number_match = re.search(
            r'^(\d+\.?\d*\.?|[가-힣]\.?|[①-⑳]|[IVX]+\.?)',
            row_text
        )

        if not number_match:
            continue

        section_number = number_match.group(1).strip('.')
        remaining_text = row_text[number_match.end():].strip()

        # 제목과 페이지 번호 분리
        # 패턴: "제목 ... 페이지번호" 또는 "제목"
        page_match = re.search(r'(\d+)\s*$', remaining_text)

        if page_match:
            page_number = int(page_match.group(1))
            title = remaining_text[:page_match.start()].strip()
        else:
            page_number = None
            title = remaining_text

        # 너무 짧거나 의미 없는 제목 필터링
        if len(title) < 2 or title in ['합계', '계', '비고', '']:
            continue

        sections.append({
            'number': section_number,
            'title': title,
            'page': page_number,
            'row_index': row_idx
        })

    return sections


def extract_toc_from_announcement_and_attachments(state: BatchState) -> BatchState:
    """
    공고문 + 모든 첨부서류에서 목차 유추 (RAG + LLM) - LangGraph 노드

    ⚠️ 양식이 없는 경우, 공고문과 모든 첨부서류(RFP, 가이드 등)를 함께 분석하여 목차 생성

    방법:
    1. 공고문에서 "제출서류" feature 찾기
    2. RAG로 모든 문서(공고+첨부)에서 관련 청크 검색
    3. LLM으로 목차 구조 생성

    Returns:
        state: table_of_contents 업데이트된 BatchState
    """
    print(f"\n{'='*60}")
    print(f"📑 공고문 + 첨부서류 기반 목차 유추")
    print(f"{'='*60}")

    all_features = state.get('extracted_features', [])
    collection = state['chroma_collection']

    # 1️⃣ 제출서류 feature 찾기
    submission_features = [
        f for f in all_features
        if f['feature_code'] == 'submission_docs'
    ]

    if not submission_features:
        print(f"\n  ⚠️  '제출서류' feature 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = _create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    submission_content = '\n\n'.join([
        f.get('full_content', '') for f in submission_features
    ])

    # 2️⃣ RAG로 모든 문서(공고+첨부) 검색 (볼륨 증가를 위해 검색 결과 확대)
    try:
        # OpenAI API로 쿼리 임베딩 생성 (processing.py의 extract_features_rag와 동일한 방식)
        query_text = "제출서류 작성항목 구성 목차 제안서 계획서 사업계획서 운영계획"
        query_response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[query_text]
        )
        query_embedding = [query_response.data[0].embedding]

        # ✅ 모든 문서에서 검색 (ATTACHMENT 필터 제거)
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=25  # 15 → 25로 증가: 더 많은 컨텍스트 확보
            # where 조건 제거 → 공고문 + 모든 첨부서류 검색
        )

        all_chunks = []
        if results['ids'][0]:
            for i in range(len(results['ids'][0])):
                all_chunks.append({
                    'text': results['documents'][0][i],
                    'file': results['metadatas'][0][i]['file_name'],
                    'section': results['metadatas'][0][i]['section'],
                    'doc_type': results['metadatas'][0][i].get('document_type', 'UNKNOWN')
                })
            print(f"    ✅ RAG 검색 완료: {len(all_chunks)}개 청크 (공고 + 첨부서류)")
    except Exception as e:
        print(f"    ✗ RAG 검색 실패: {e}")
        all_chunks = []

    # 3️⃣ LLM으로 목차 생성
    print(f"    🤖 LLM으로 목차 구조 생성 중...")

    # 문서 타입별로 정리 (더 많은 컨텍스트 활용)
    document_context = '\n\n'.join([
        f"[{c['doc_type']} - {c['file']} - {c['section']}]\n{c['text']}"
        for c in all_chunks[:20]  # 10 → 20으로 증가: 더 풍부한 컨텍스트 제공
    ])

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

    # 공고문 전체 내용 가져오기 (첨부파일이 없을 때 대비) - 컨텍스트 확대
    announcement_docs = [d for d in state['documents'] if d.get('document_type') == 'ANNOUNCEMENT']
    announcement_text = ''
    if announcement_docs:
        announcement_text = announcement_docs[0].get('text', '')[:5000]  # 3000 → 5000으로 증가

    submission_text_limit = submission_content[:3000]  # 2000 → 3000으로 증가
    document_context_limit = document_context[:4000] if document_context else '(첨부서류 없음)'  # 2000 → 4000으로 증가

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

        result = json.loads(response.choices[0].message.content)

        if result.get('sections'):
            toc = {
                'source': 'announcement',
                'extraction_method': 'rag_llm',
                'inference_confidence': 0.7,  # RAG + LLM 기반이므로 중간 신뢰도
                'sections': result['sections'],
                'total_sections': len(result['sections']),
                'extracted_at': datetime.now().isoformat()
            }

            state['table_of_contents'] = toc
            state['status'] = 'toc_extracted'

            print(f"\n  ✅ LLM으로 {len(result['sections'])}개 섹션 생성 완료")
            for sec in result['sections'][:5]:
                print(f"    • {sec.get('number', '')} {sec.get('title', '')}")
            if len(result['sections']) > 5:
                print(f"    ... 외 {len(result['sections']) - 5}개")

            return state
        else:
            print(f"\n  ✗ LLM 결과에 섹션 없음 → 기본 템플릿 사용")
            state['table_of_contents'] = _create_default_toc()
            state['status'] = 'toc_extracted'
            return state

    except Exception as e:
        print(f"\n  ✗ LLM 호출 실패: {e} → 기본 템플릿 사용")
        state['table_of_contents'] = _create_default_toc()
        state['status'] = 'toc_extracted'
        return state


def _create_default_toc() -> Dict:
    """
    기본 목차 생성 (추출 실패 시)

    일반적인 R&D 제안서 표준 목차 제공
    """
    return {
        'source': 'default',
        'extraction_method': 'fallback',
        'inference_confidence': 0.3,
        'sections': [
            {'number': '1', 'title': '연구개발 과제의 개요', 'required': True},
            {'number': '2', 'title': '연구개발 목표 및 내용', 'required': True},
            {'number': '3', 'title': '연구개발 추진체계 및 일정', 'required': True},
            {'number': '4', 'title': '연구개발 성과 활용방안', 'required': True},
            {'number': '5', 'title': '소요예산', 'required': True},
        ],
        'total_sections': 5,
        'extracted_at': datetime.now().isoformat(),
        'note': '목차 추출 실패로 기본 템플릿 사용'
    }


def _extract_toc_from_template_with_llm(state: BatchState, template: Dict) -> BatchState:
    """
    LLM을 사용하여 양식 텍스트에서 목차 추출 (표 파싱 실패 시)

    Args:
        state: BatchState
        template: 양식 문서 정보

    Returns:
        state: table_of_contents 업데이트된 BatchState
    """
    print(f"  🤖 LLM으로 양식 텍스트 분석 중...")

    # 양식 문서에서 텍스트 추출
    documents = state.get('documents', [])
    template_doc = None

    template_file_name = unicodedata.normalize('NFC', template['file_name'])

    for doc in documents:
        doc_file_name = unicodedata.normalize('NFC', doc.get('file_name', ''))
        if doc_file_name == template_file_name:
            template_doc = doc
            break

    if not template_doc or not template_doc.get('full_text'):
        print(f"  ✗ 양식 텍스트 없음 → 기본 템플릿 사용")
        state['table_of_contents'] = _create_default_toc()
        state['status'] = 'toc_extracted'
        return state

    # 목차 섹션 스마트 추출
    full_text = template_doc['full_text']

    # 1단계: 목차 시작 키워드 찾기
    toc_start_keywords = [
        '< 본문', '<본문', '본문>',
        '작성 목차', '제출서류 목차', '계획서 목차',
        '작성항목', '제출항목', '기재사항'
    ]

    toc_section_start = -1
    for keyword in toc_start_keywords:
        idx = full_text.find(keyword)
        if idx != -1:
            toc_section_start = idx
            print(f"    📍 목차 시작 키워드 발견: '{keyword}' (위치: {idx})")
            break

    # 2단계: 목차 끝 지점 찾기
    if toc_section_start != -1:
        # 목차 시작 이후 텍스트
        text_after_start = full_text[toc_section_start:]

        # 끝 지점 후보 키워드
        end_keywords = [
            '< 본문 2', '<본문 2', '본문 2>',
            '작성요령', '작성 요령', '주의사항', '유의사항',
            '참고사항', '기재요령', '첨부서류',
            '※ 참고', '【참고', '[참고'
        ]

        toc_end = len(text_after_start)  # 기본값: 끝까지
        for end_kw in end_keywords:
            end_idx = text_after_start.find(end_kw)
            if end_idx != -1 and end_idx < toc_end:
                toc_end = end_idx
                print(f"    📍 목차 끝 키워드 발견: '{end_kw}' (상대 위치: {end_idx})")
                break

        # 목차 섹션 추출 (최대 5000자로 제한)
        template_text = text_after_start[:min(toc_end, 5000)]
        print(f"    ✅ 목차 섹션 추출 완료 (길이: {len(template_text)}자)")
    else:
        # 3단계: 키워드 없으면 번호 패턴으로 목차 구간 찾기
        print(f"    ⚠️  목차 키워드 미발견 → 번호 패턴 기반 탐지 시도")

        # "1. ", "2. ", "3. " 패턴이 연속으로 나타나는 구간 찾기
        import re
        pattern = r'^[1-9]\.\s+[가-힣]{2,}'
        lines = full_text.split('\n')

        toc_line_start = -1
        consecutive_numbered = 0

        for i, line in enumerate(lines):
            if re.search(pattern, line.strip()):
                if toc_line_start == -1:
                    toc_line_start = i
                consecutive_numbered += 1

                # 3개 이상 연속 번호 패턴이면 목차로 판단
                if consecutive_numbered >= 3:
                    # 목차 시작부터 최대 100줄 또는 5000자
                    toc_lines = lines[toc_line_start:toc_line_start + 100]
                    template_text = '\n'.join(toc_lines)[:5000]
                    print(f"    ✅ 번호 패턴 기반 목차 발견 (라인: {toc_line_start}, 길이: {len(template_text)}자)")
                    break
            else:
                consecutive_numbered = 0
        else:
            # 번호 패턴도 못 찾으면 전체 텍스트 사용
            template_text = full_text[:15000]  # 15000자로 확대
            print(f"    ⚠️  목차 패턴 미발견 → 전체 텍스트 사용 (15000자)")

    system_prompt = """당신은 정부 R&D 제안서 양식 분석 전문가입니다.

제안서 작성 양식의 텍스트를 분석하여 **실제 작성해야 할 목차(섹션)**를 추출하세요.

다음 형식으로 JSON 반환:
{
  "sections": [
    {
      "number": "1",
      "title": "연구개발과제의 필요성",
      "required": true,
      "description": "과제의 필요성 설명"
    }
  ]
}

⚠️ 중요 구분:
- ✅ 추출할 것: "1. 연구개발과제의 필요성", "2. 연구개발과제의 목표 및 내용" 같은 **본문 작성 목차**
- ❌ 제외할 것: "사업명", "연구책임자", "연구개발기간" 같은 **폼 입력 필드**

주의사항:
- 번호가 있는 작성 항목(1., 2., 3. 또는 가., 나., 다.)을 섹션으로 추출
- 섹션 번호는 "1", "1.1", "가" 등 원문 형식 유지
- 계층 구조도 포함 (1) → 2) → 3) 등)
- required는 필수 작성 항목 여부"""

    user_prompt = f"""## 제안서 양식 텍스트

{template_text}

위 양식을 분석하여 **제안서 본문 작성 목차**를 JSON 형식으로 추출해주세요.
단순 폼 필드가 아닌, 실제로 서술해야 할 섹션들을 추출하세요."""

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

        result = json.loads(response.choices[0].message.content)

        if result.get('sections') and len(result['sections']) > 0:
            toc = {
                'source': 'template',
                'source_file': template['file_name'],
                'extraction_method': 'llm_text_analysis',
                'inference_confidence': 0.75,  # LLM 기반이므로 중상 신뢰도
                'sections': result['sections'],
                'total_sections': len(result['sections']),
                'extracted_at': datetime.now().isoformat()
            }

            state['table_of_contents'] = toc
            state['status'] = 'toc_extracted'

            print(f"  ✅ LLM으로 {len(result['sections'])}개 섹션 추출 완료")
            for sec in result['sections'][:5]:
                print(f"    • {sec.get('number', '')} {sec.get('title', '')}")
            if len(result['sections']) > 5:
                print(f"    ... 외 {len(result['sections']) - 5}개")

            return state
        else:
            print(f"  ✗ LLM 결과에 섹션 없음 → 기본 템플릿 사용")
            state['table_of_contents'] = _create_default_toc()
            state['status'] = 'toc_extracted'
            return state

    except Exception as e:
        print(f"  ✗ LLM 호출 실패: {e} → 기본 템플릿 사용")
        state['table_of_contents'] = _create_default_toc()
        state['status'] = 'toc_extracted'
        return state
