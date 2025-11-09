# 서버 실행 가이드

이 문서는 `alice_consultant_agent_real/final` 프로젝트에서 **프론트엔드**, **백엔드(Spring Boot)**, **FastAPI** 서버를 실행하는 방법을 정리한 것입니다. 모든 경로는 절대 경로 기준으로 안내합니다.

## 1. 공통 준비 사항

- macOS 기준 개발 환경 (JDK 17, Python 3.11+, Node.js 18 LTS 권장)
- 프로젝트 루트: `/Users/suyeonjo/alice_consultant_agent_real/final`
- 터미널은 각각 별도 창/탭에서 실행하면 편리합니다.

---

## 2. FastAPI 서버 실행

FastAPI는 `alice/fastAPI` 디렉터리에서 실행합니다.

1. (선택 사항) 가상환경이 있다면 활성화합니다.
   ```bash
   cd /Users/suyeonjo/alice_consultant_agent_real/final/alice/fastAPI
   source venv/bin/activate  # 가상환경을 사용 중일 때만
   ```

2. 서버 실행
   ```bash
   cd /Users/suyeonjo/alice_consultant_agent_real/final/alice/fastAPI/src
   python3 -m uvicorn fastAPI_v6_integrated:app --reload --host 0.0.0.0 --port 8001
   ```

- `--reload` 옵션으로 코드 변경 시 자동 재시작됩니다.
- FastAPI가 정상적으로 뜨면 `http://127.0.0.1:8001/docs` 에서 OpenAPI 문서를 확인할 수 있습니다.

---

## 3. Spring Boot 백엔드 실행

백엔드는 Maven Wrapper(`mvnw`)를 사용하여 실행합니다.

```bash
cd /Users/suyeonjo/alice_consultant_agent_real/final/backend
./mvnw spring-boot:run
```

- JDK 17이 필요합니다.
- 기본 포트는 `8081` 입니다. FastAPI와의 통신은 `http://localhost:8001` 으로 이루어집니다.
- 서버 로그에 `Tomcat started on port 8081` 메시지가 나오면 정상 실행 상태입니다.

---

## 4. 프론트엔드 실행 (Vite)

프론트엔드는 Vite 기반 React 프로젝트입니다.

1. 최초 1회 의존성 설치
   ```bash
   cd /Users/suyeonjo/alice_consultant_agent_real/final/frontend
   npm install
   ```

2. 개발 서버 실행
   ```bash
   cd /Users/suyeonjo/alice_consultant_agent_real/final/frontend
   npm run dev
   ```

- 기본 포트는 `5173` 이며, 브라우저에서 `http://localhost:5173`로 접속합니다.
- 서버 실행 후 로그에 표시되는 로컬/네트워크 주소를 통해 접근 가능합니다.

---

## 5. 실행 순서 및 체크리스트

1. FastAPI 서버 실행 (포트 8001)
2. Spring Boot 백엔드 실행 (포트 8081)
3. 프론트엔드 개발 서버 실행 (포트 5173)

> 백엔드는 FastAPI에 의존하므로 FastAPI를 먼저 띄워야 합니다. 프론트엔드는 백엔드 API에 접근하므로, 최소 FastAPI와 백엔드가 동작 중인지 확인한 후 실행하세요.

필요 시 각 서버를 종료할 때는 해당 터미널에서 `Ctrl + C` 를 입력하면 됩니다.
