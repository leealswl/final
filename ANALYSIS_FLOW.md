# 📊 PALADOC 프로젝트 분석 흐름 (전체 정리)

## 🎯 개요
프론트엔드에서 파일 업로드 후 백엔드로 분석 요청이 오면, LangGraph 기반 파이프라인이 문서를 분석하여 핵심 정보를 추출합니다.

---

## 📋 전체 파이프라인 흐름

```
START
  ↓
1. extract_all_texts (PDF 텍스트/표 추출)
  ↓
2. chunk_all_documents (섹션 기반 청킹)
  ↓
3. embed_all_chunks (임베딩 생성)
  ↓
4. init_and_store_vectordb (VectorDB 저장)
  ↓
5. extract_features_rag (Feature 추출) ⚡ 핵심
  ├─ 핵심 정보 (7개): Vision API 우선 → RAG fallback
  └─ 일반 정보: RAG만 사용
  ↓
6. detect_templates (첨부 양식 감지)
  ↓
7. 조건부 라우팅 (TOC_ROUTER)
  ├─ extract_toc_from_template (양식 O)
  └─ extract_toc_from_announcement_and_attachments (양식 X)
  ↓
8. save_to_csv (로컬 저장 - 개발용)
  ↓
9. build_response (최종 응답 + Backend API 호출)
  ↓
END
```

---

## 🔍 5단계: Feature 추출 상세 흐름

### 5-1. Feature 목록 순회 (config.py의 FEATURES)
- 총 50개 이상의 Feature 정의
- 각 Feature마다 순차적으로 추출 시도

### 5-2. 핵심 정보 vs 일반 정보 구분

#### ✅ 핵심 정보 (7개) - 사용자 우선 표시 정보
Frontend `AnalyzeView.jsx`의 `coreFeatures`와 일치:

```python
core_features = [
    'project_name',           # 사업명
    'announcement_date',      # 공고일
    'application_period',     # 접수기간
    'project_period',         # 사업기간
    'support_scale',          # 지원규모
    'announcing_agency',      # 공고기관
]
```

**처리 전략: Vision API 우선 → RAG Fallback**

#### 📋 일반 정보 (나머지 모든 Feature)
- 지원대상, 참여자격, 평가기준, 선정절차, 제출서류 등
- **처리 전략: RAG만 사용**

---

## 👁️ 핵심 정보: Vision API 추출 전략

### 1단계: Vision API 시도

```
핵심 정보 Feature 감지
  ↓
공고문 문서 찾기 (document_type == 'ANNOUNCEMENT')
  ↓
공고문 파일의 bytes 찾기 (state['files'])
  ↓
Vision API 호출
  ├─ PDF → 이미지 변환 (첫 1-2페이지, 150 DPI)
  ├─ GPT-4o Vision으로 실제 값 추출
  └─ 프롬프트: "작성 방법이 아닌 실제 값만 추출"
  ↓
결과 확인
  ├─ found == true → ✅ Vision API 성공 → RAG 건너뛰기
  └─ found == false → ⚠️ Vision API 실패 → RAG로 fallback
```

**Vision API 성공 시:**
- 결과를 `all_features`에 저장
- `extraction_method: 'vision_api'` 표시
- RAG 방식 완전히 건너뛰기 (`continue`)

### 2단계: RAG Fallback (Vision API 실패 시)

```
Vision API 실패
  ↓
공고문 첫 3페이지 텍스트 우선 추가
  ↓
RAG 검색 (VectorDB)
  ├─ Feature 키워드로 임베딩 검색
  ├─ 공고문 + 첨부서류 통합 검색 (상위 10개)
  └─ 유사도 임계값 체크 (1.4 이하)
  ↓
LLM 분석
  └─ 핵심 정보 프롬프트: "실제 값 추출에 집중"
  ↓
결과 저장
```

---

## 📚 일반 정보: RAG 추출 전략

```
Feature 키워드 추출
  ├─ primary → secondary → related 순서
  └─ 상위 5개 키워드로 쿼리 생성
  ↓
VectorDB 유사도 검색
  ├─ 공고문 + 첨부서류 통합 검색
  ├─ 상위 10개 청크 추출
  └─ 유사도 임계값: 1.4 이하
  ↓
공고 vs 첨부 분리
  ↓
LLM 컨텍스트 구성
  ├─ 공고문 관련 섹션
  └─ 첨부서류 관련 섹션
  ↓
LLM 분석 (gpt-4o-mini)
  └─ 작성 전략 프롬프트: "작성 요령, 팁, 주의사항 추출"
  ↓
결과 저장
  ├─ extraction_method: 'rag'
  ├─ vector_similarity 기록
  └─ chunks_from_announcement/attachments 기록
```

---

## 🎨 Vision API vs RAG 비교

| 항목 | Vision API | RAG |
|------|-----------|-----|
| **대상** | 핵심 정보 7개 | 일반 정보 40개+ |
| **방식** | PDF 이미지 직접 분석 | 텍스트 청킹 + 벡터 검색 |
| **정확도** | ⭐⭐⭐⭐⭐ 매우 높음 | ⭐⭐⭐⭐ 높음 |
| **장점** | 레이아웃 정보 활용<br>제목/헤더 정확 인식 | 크로스 문서 검색<br>공고+첨부 통합 분석 |
| **비용** | 높음 (GPT-4o Vision) | 낮음 (GPT-4o-mini) |
| **속도** | 빠름 (1-2페이지만) | 보통 (전체 문서 검색) |
| **Fallback** | 실패 시 RAG로 전환 | 없음 |

---

## 🔄 전체 Feature 추출 플로우

```
for each feature in FEATURES (50개+):
    if feature in core_features (7개):
        # 핵심 정보 처리
        ├─ Vision API 시도
        │   ├─ 성공 → 결과 저장 → continue (RAG 건너뛰기)
        │   └─ 실패 → RAG로 진행
        └─ RAG Fallback
            ├─ 공고문 첫 3페이지 우선 추가
            ├─ VectorDB 검색
            └─ LLM 분석 (실제 값 추출 프롬프트)
    else:
        # 일반 정보 처리
        ├─ VectorDB 검색
        └─ LLM 분석 (작성 전략 프롬프트)
    
    결과 저장 → all_features에 추가
```

---

## 📦 최종 결과 구조

```json
{
  "extracted_features": [
    {
      "feature_code": "project_name",
      "feature_name": "사업명",
      "title": "2025년 공공AX 프로젝트 사업",
      "summary": "2025년 공공AX 프로젝트 사업",
      "full_content": "...",
      "key_points": [...],
      "writing_strategy": {...},
      "extraction_method": "vision_api",  // 또는 "rag"
      "vector_similarity": null,  // Vision API면 null
      "chunks_from_announcement": 0,
      "chunks_from_attachments": 0,
      "project_idx": 112,
      "extracted_at": "2025-11-29T14:00:00"
    },
    ...
  ]
}
```

---

## ✅ 검증 포인트

1. **핵심 정보 우선순위**: Frontend의 `coreFeatures`와 일치하는가?
   - ✅ `project_name`, `announcement_date`, `application_period`, `project_period`, `support_scale`, `announcement_number`, `announcing_agency`

2. **Vision API 동작**: 핵심 정보에서 Vision API가 우선 시도되는가?
   - ✅ 핵심 정보 감지 → Vision API 시도 → 성공 시 RAG 건너뛰기

3. **Fallback 동작**: Vision API 실패 시 RAG로 정상 전환되는가?
   - ✅ Vision 실패 → 공고문 첫 페이지 우선 → RAG 검색

4. **일반 정보 처리**: 핵심 정보가 아닌 Feature는 RAG로만 처리되는가?
   - ✅ 일반 정보는 Vision API 없이 RAG만 사용

---

## 🎯 핵심 아이디어

> **사용자가 첫 화면에서 보는 핵심 정보는 정확도가 최우선!**
> 
> - Vision API로 레이아웃 정보를 활용해 정확하게 추출
> - 일반 정보는 RAG로 효율적으로 추출
> - Vision 실패 시에도 RAG로 안정적으로 fallback

---

## 📝 주의사항

1. **Deadline 제거**: Frontend에서 deadline을 제거했으므로 core_features에도 없음 ✅
2. **일관성**: Frontend의 `coreFeatures`와 Backend의 `core_features` 목록이 일치해야 함 ✅
3. **비용**: Vision API는 비용이 높지만, 핵심 정보 7개만 처리하므로 비용 절감 ✅

