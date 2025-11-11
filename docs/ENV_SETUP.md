# 환경 변수 구성 및 서버 실행 가이드

> 2025-11-09 · suyeon · FastAPI 실행 오류 대응 및 실행 절차 표준화

## 1. 구조 개요

- `frontend/.env`  
  - `VITE_ONLYOFFICE_SRC` 관리 (프론트엔드 미리보기용)
- `alice/.env`  
  - 개인 API 키, 토큰 등 프로젝트 전역에서 참조할 값 저장
- `alice/fastAPI/.env`  
  - FastAPI 분석 서버 전용 설정 (`STORAGE_MODE`, `ORACLE_*` 등)

## 2. 정리 원칙

- **FastAPI 용 .env 최소화**  
  - AI 키 등 공용 토큰은 `alice/.env` 또는 OS 환경 변수에 보관  
  - FastAPI는 `config/settings.py`에서 필요한 값만 읽도록 유지  
  - 2025-11-09 수정: `Settings` 모델에 `extra="ignore"` 적용 → 추가 키가 있어도 무시
- **값 표기 방식**  
  - 따옴표 없이 `KEY=value` 형식으로 기록  
  - 운영/개발 분기 필요 시 `env/local/.env.dev`, `env/prod/.env` 등으로 확장 가능
- **변경 이력 기록**  
  - `.env`나 설정 코드 수정 시 날짜·작성자·의도를 주석 또는 본 문서에 남김

## 3. FastAPI 실행 절차

```bash
# 1) 가상환경 활성화
cd /Users/suyeonjo/alice_consultant_agent_real/final/alice
source .venv/bin/activate

# 2) (최초 1회) 의존성 설치
pip install -r fastAPI/requirements.txt
pip install cx_Oracle  # Oracle 모드 대비

# 3) 서버 실행
cd fastAPI
uvicorn fastAPI_v6_integrated:app --reload --host 0.0.0.0 --port 8001 --app-dir src
```

## 4. 프론트엔드 & 백엔드 실행 요약

- **프론트**  
  ```bash
  cd /Users/suyeonjo/alice_consultant_agent_real/final/frontend
  npm install        # 최초 1회
  npm run dev        # http://localhost:5173
  ```

- **백엔드 (Spring Boot)**  
  ```bash
  cd /Users/suyeonjo/alice_consultant_agent_real/final/backend
  ./mvnw spring-boot:run   # http://localhost:8081
  ```

## 5. 자주 묻는 질문

- **Q. FastAPI가 `OPENAI_API_KEY` 때문에 죽어요.**  
  - A. 2025-11-09부터 `Settings`에서 추가 키를 무시하도록 변경되었습니다. 그래도 문제라면 FastAPI `.env`에서 해당 키를 삭제하고 `alice/.env`에만 유지하세요.

- **Q. .env 값 바꾸면 어디에 기록하나요?**  
  - A. 본 문서 상단에 `> 날짜 · 작성자 · 수정 이유`를 추가하거나, `docs/CHANGELOG_ENV.md`를 만들어 누적 관리해 주세요.

