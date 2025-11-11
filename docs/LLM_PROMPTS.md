# LLM 프롬프트 요약

이 문서는 FastAPI 분석 에이전트에서 OpenAI LLM을 호출하는 주요 함수와 프롬프트 구성을 정리한 것입니다. 각 항목은 실제 코드 위치, 목적, 사용 모델 및 시스템/사용자 프롬프트 내용을 포함합니다.

---

## `extract_features_rag`
- **위치**: `alice/fastAPI/src/v6_rag_real/nodes/processing.py`
- **호출 지점**: 기능 추출 파이프라인에서 RAG 검색 이후 (for-loop 내부)
- **모델**: `gpt-4o-mini` (`client.chat.completions.create`, `response_format=json_object`, `temperature=0`)
- **시스템 프롬프트 요약**:
  ```
  당신은 정부 연구개발 공고문을 분석하는 전문가입니다.
  특정 feature_type에 해당하는 내용을 JSON으로 반환하세요.
  {"found": bool, "title": ..., "content": ..., "full_content": ..., "key_points": [...]}
  ```
- **사용자 프롬프트 구성**:
  - RAG로 수집한 공고문/첨부 청크를 섹션별로 나열한 `context_text`
  - 현재 탐색 중인 `feature_def['feature_type']` 명시
  - 결과를 JSON으로 반환하도록 지시
- **출력 사용 방식**:
  - `result['found']`가 `true`인 경우에만 feature 리스트에 추가
  - JSON 필드를 그대로 저장하고, 관련 청크 메타데이터와 함께 상태(`state['extracted_features']`)에 기록

---

## `extract_toc_from_announcement_and_attachments`
- **위치**: `alice/fastAPI/src/v6_rag_real/nodes/toc_extraction.py`
- **호출 맥락**: 템플릿이 없거나 실패한 경우, 공고문 + 첨부 문서 기반 RAG → LLM 추론 단계
- **모델**: `gpt-4o-mini` (`response_format=json_object`, `temperature=0`)
- **시스템 프롬프트 요약**:
  ```
  당신은 정부 지원사업 공고 분석 전문가입니다.
  제출해야 하는 계획서의 작성 항목(목차)만 JSON으로 추출하세요.
  섹션 번호/제목/필수 여부/설명을 포함하고, 서류명 자체는 제외하세요.
  ```
- **사용자 프롬프트 구성**:
  - 공고문 본문 요약(`announcement_text`)
  - 제출 서류 요구사항(`submission_content`)
  - RAG로 찾은 상위 10개 청크를 문서 타입별로 나열한 `document_context`
  - 공고 성격 파악 및 올바른 목차 생성에 대한 지침 (연구개발/창업지원 등)
- **출력 사용 방식**:
  - `sections` 배열 존재 시 `state['table_of_contents']`에 저장 (`extraction_method='rag_llm'`)
  - 실패 시 기본 템플릿으로 폴백

---

## `_extract_toc_from_template_with_llm`
- **위치**: `alice/fastAPI/src/v6_rag_real/nodes/toc_extraction.py`
- **호출 맥락**: 템플릿 기반 목차 추출에서 표 파싱이 실패했을 때, 템플릿 전문을 LLM으로 분석
- **모델**: `gpt-4o-mini` (`response_format=json_object`, `temperature=0`)
- **시스템 프롬프트 요약**:
  ```
  당신은 정부 R&D 제안서 양식 분석 전문가입니다.
  작성 목차(번호가 있는 섹션)만 JSON으로 추출하고,
  단순 입력 필드(사업명, 담당자 등)는 제외하세요.
  ```
- **사용자 프롬프트 구성**:
  - 전처리된 템플릿 텍스트(`template_text`): 목차 구간만 뽑거나 최대 15,000자 제한
  - "본문 작성 목차를 JSON으로 추출하라"는 명시적 요청
- **출력 사용 방식**:
  - `sections` 배열이 존재하면 `state['table_of_contents']` 업데이트 (`extraction_method='llm_text_analysis'`)
  - 실패 시 기본 목차 템플릿으로 폴백

---

## 참고
- 모든 LLM 호출은 `OpenAI` Python SDK(`client.chat.completions.create`)를 사용하며, `response_format={"type": "json_object"}`로 JSON 스키마 준수를 요구합니다.
- 모델 및 프롬프트는 함수 내부에서 직접 정의되므로, 프롬프트 수정 시 해당 함수 파일을 편집해야 합니다.
- 임베딩 생성(`embed_all_chunks`) 등 다른 OpenAI API 호출도 존재하지만, 명시적인 자연어 프롬프트는 위 세 함수에서만 사용됩니다.


