# Alice Consultant FastAPI v6 - 프로덕션

공고 및 첨부서류 분석 후 사용자 입력 폼 자동 생성 (MVP1)

## 프로젝트 구조

```
fastAPI/
├── src/
│   ├── fastAPI_v6_integrated.py  # 메인 FastAPI 앱
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py           # 앱 설정
│   └── v6_rag_real/              # AI 분석 엔진 (프로덕션 전용)
│       ├── __init__.py
│       ├── graph.py              # LangGraph 구성
│       ├── state_types.py        # 상태 타입 정의
│       ├── config.py             # RAG 설정
│       ├── utils.py              # 유틸리티
│       └── nodes/                # 분석 노드들
│           ├── __init__.py
│           ├── extract.py        # 텍스트/표 추출
│           ├── processing.py     # 청킹/임베딩/RAG
│           ├── template_detection.py  # 양식 감지
│           ├── toc_extraction.py      # 목차 추출
│           ├── oracle_storage.py      # Oracle DB 저장
│           └── response.py            # 응답 생성
├── .env.example                  # 환경 설정 예시
├── requirements.txt              # Python 패키지
└── README.md                     # 이 문서
```

## 주요 기능

### MVP1: 사용자 입력 폼 자동 생성

1. **공고 분석**: 제출 서류, 평가 기준 등 주요 Feature 추출
2. **첨부 양식 감지**: RAG 기반으로 첨부서류 중 양식 자동 감지
3. **목차 추출**:
   - 양식 O → 첨부 양식 기반 목차 추출
   - 양식 X → 공고 목차 기반 추출
4. **사용자 입력 폼 생성**: 목차 기반 폼 스키마 자동 생성

## 저장 모드

### 개발 모드: CSV 저장
- 환경변수: `STORAGE_MODE=csv` (기본값)
- 결과를 CSV 파일로 저장
- 로컬 개발 및 테스트에 적합

### 프로덕션 모드: Oracle DB 저장
- 환경변수: `STORAGE_MODE=oracle`
- Oracle DB에 직접 저장
- 테이블:
  - `ANALYSIS_RESULT`: Feature 분석 결과
  - `TABLE_OF_CONTENTS`: 목차 데이터

## 설치 및 실행

### 1. 패키지 설치

```bash
cd /Users/suyeonjo/alice_consultant_agent_real/final/alice/fastAPI
pip install -r requirements.txt
```

### 2. 환경 설정

개발 환경 (CSV 저장):
```bash
# .env 파일 생성
cp .env.example .env

# 기본값 사용 (CSV 모드)
STORAGE_MODE=csv
```

프로덕션 환경 (Oracle 저장):
```bash
# .env 파일 수정
STORAGE_MODE=oracle
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password
ORACLE_DSN=db.company.com:1521/PROD_DB
```

### 3. 실행

```bash
cd src
python fastAPI_v6_integrated.py
```

또는

```bash
uvicorn src.fastAPI_v6_integrated:app --reload
```

## API 엔드포인트

### POST /analyze

공고 및 첨부서류 분석

**요청 (multipart/form-data):**
```
files: List[UploadFile]  # 업로드 파일 리스트
folders: List[str]       # 각 파일의 폴더 ID ("1"=공고, "2"=첨부)
userid: str              # 사용자 ID
projectidx: int          # 프로젝트 ID
```

**응답:**
```json
{
  "status": "success",
  "form_source": "TEMPLATE",  // "TEMPLATE" or "TOC"
  "user_form": {
    "form_id": "form_1_20250107_...",
    "sections": [
      {
        "section_number": "1",
        "section_title": "사업 개요",
        "fields": [
          {
            "field_id": "field_1_1",
            "label": "사업명",
            "type": "text",
            "required": true
          }
        ]
      }
    ]
  },
  "documents": { ... }
}
```

### GET /health

헬스 체크

```json
{
  "status": "ok",
  "message": "Alice Consultant API is running"
}
```

## 데이터 흐름

```
1. Backend → FastAPI
   └─ multipart/form-data (files + folders + metadata)

2. FastAPI → LangGraph
   └─ bytes 기반 처리 (디스크 저장 없음)

3. LangGraph 처리 흐름
   ├─ extract_all_texts: PDF → 텍스트/표 추출
   ├─ chunk_all_documents: 섹션 기반 청킹
   ├─ embed_all_chunks: 임베딩 생성
   ├─ init_and_store_vectordb: Chroma VectorDB 저장
   ├─ extract_features_rag: RAG 기반 Feature 추출
   ├─ detect_templates: 첨부 양식 감지
   ├─ [조건부 라우팅]
   │   ├─ extract_toc_from_template (양식 O)
   │   └─ extract_toc_from_announcement (양식 X)
   ├─ [저장 라우팅]
   │   ├─ save_to_csv (개발)
   │   └─ save_to_oracle (프로덕션)
   └─ build_response: 최종 응답 생성

4. FastAPI → Backend
   └─ JSON 응답 (form + documents)
```

## Oracle DB 스키마

### ANALYSIS_RESULT 테이블

```sql
CREATE TABLE ANALYSIS_RESULT (
    id NUMBER PRIMARY KEY,
    project_idx NUMBER NOT NULL,
    feature_code VARCHAR2(100),
    feature_name VARCHAR2(255),
    title VARCHAR2(500),
    summary CLOB,
    full_content CLOB,
    confidence_score NUMBER,
    extracted_at TIMESTAMP
);
```

### TABLE_OF_CONTENTS 테이블

```sql
CREATE TABLE TABLE_OF_CONTENTS (
    id NUMBER PRIMARY KEY,
    project_idx NUMBER NOT NULL,
    source VARCHAR2(50),  -- 'TEMPLATE' or 'TOC'
    total_sections NUMBER,
    toc_data CLOB,  -- JSON 형태 목차 데이터
    extracted_at TIMESTAMP
);
```

## 환경 변수

| 변수 | 설명 | 기본값 | 필수 |
|------|------|--------|------|
| `STORAGE_MODE` | 저장 모드 (`csv` or `oracle`) | `csv` | ❌ |
| `ORACLE_USER` | Oracle 사용자명 | - | ✅ (프로덕션) |
| `ORACLE_PASSWORD` | Oracle 비밀번호 | - | ✅ (프로덕션) |
| `ORACLE_DSN` | Oracle DSN | - | ✅ (프로덕션) |

## 개발 vs 프로덕션

### 개발 환경
- ✅ CORS 없음 (Backend가 서버-투-서버로 요청)
- ✅ CSV 저장 (로컬 파일 시스템)
- ✅ 디스크 저장 없음 (bytes 기반 처리)
- ✅ Reload 활성화

### 프로덕션 환경
- ✅ CORS 없음 (Backend가 서버-투-서버로 요청)
- ✅ Oracle DB 저장
- ✅ 디스크 저장 없음 (bytes 기반 처리)
- ✅ Reload 비활성화
- ✅ 로깅 강화

## 변경 이력

### v6 (2025-01-07) - 프로덕션 준비
- ✨ Oracle DB 저장 지원 추가 (`oracle_storage.py`)
- ✨ 환경 기반 저장 라우팅 (CSV vs Oracle)
- ✨ bytes 기반 처리 (디스크 I/O 제거)
- ✨ CORS 제거 (서버-투-서버 통신)
- 🔖 `match_cross_references` 제거 (MVP2 보류)
