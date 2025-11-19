# 🔧 문제 해결 가이드

## ❌ "ECONNREFUSED" 에러 - Backend 서버 연결 실패

### 증상
```
[vite] http proxy error: /api/analysis/toc?projectIdx=1
AggregateError [ECONNREFUSED]:
```

### 원인
Backend 서버(Spring Boot)가 실행되지 않았거나, 포트가 다름

### 해결 방법

#### 1️⃣ Backend 서버 실행 확인
```bash
# Backend 디렉토리로 이동
cd backend

# Maven으로 실행
mvn spring-boot:run

# 또는 JAR 파일 실행
java -jar target/backend-0.0.1-SNAPSHOT.jar
```

#### 2️⃣ 포트 확인
- **Backend 기본 포트**: 8081
- **Frontend 프록시 설정**: `vite.config.js`에서 확인

```javascript
// vite.config.js
proxy: {
  '/backend': {
    target: 'http://localhost:8081', // ← 이 포트 확인
    changeOrigin: true,
  }
}
```

#### 3️⃣ Backend 포트 변경이 필요한 경우
```yaml
# backend/src/main/resources/application.yml
server:
  port: 8081  # ← 원하는 포트로 변경
```

#### 4️⃣ 서버 정상 실행 확인
브라우저에서 접속:
```
http://localhost:8081/api/ai-chat/history
```

정상이면 JSON 응답이 표시됩니다.

---

## ❌ "userIdx is null" 에러

### 증상
```
FastAPI 호출 실패: Cannot invoke "java.lang.Long.toString()" 
because "userIdx" is null
```

### 원인
ChatBotMUI에서 userIdx, projectIdx를 전달하지 않음

### 해결 완료 ✅
`ChatBotMUI.jsx`에서 다음과 같이 수정됨:

```javascript
sendChatMessage(
    { 
        userMessage: userText,
        userIdx: user?.userId || 1,      // ✅ 추가
        projectIdx: project?.projectIdx || 1  // ✅ 추가
    }
)
```

---

## 🚀 전체 서버 실행 순서

### 1. FastAPI 서버
```bash
cd alice/fastapi/src
python fastAPI_v6_integrated.py
```
✅ 실행 확인: `http://localhost:8001/`

### 2. Backend 서버
```bash
cd backend
mvn spring-boot:run
```
✅ 실행 확인: `http://localhost:8081/`

### 3. Frontend 개발 서버
```bash
cd frontend
npm run dev
```
✅ 실행 확인: `http://localhost:5173/`

---

## 📋 체크리스트

실행 전 확인사항:

- [ ] Oracle DB 실행 중 (또는 H2 DB 사용)
- [ ] `.env` 파일에 `OPENAI_API_KEY` 설정됨
- [ ] Java 17 이상 설치됨
- [ ] Python 3.10 이상 설치됨
- [ ] Node.js 18 이상 설치됨
- [ ] Maven 설치됨

---

## 🔍 로그 확인

### Backend 로그
```bash
# backend 디렉토리에서
tail -f logs/application.log
```

### FastAPI 로그
콘솔에서 직접 확인 (uvicorn 출력)

### Frontend 로그
브라우저 개발자 도구 Console 탭

---

## 💡 자주 묻는 질문

### Q: "더미 응답입니다" 메시지가 계속 나와요
**A:** FastAPI 서버가 실행되지 않았거나, OpenAI API Key가 없음
- FastAPI 서버 실행 확인
- `.env` 파일 확인

### Q: 목차가 로드되지 않아요
**A:** Backend 서버 미실행 또는 `result.json` 파일 없음
- Backend 서버 실행 확인
- `alice/fastapi/src/result.json` 파일 존재 확인

### Q: 챗봇이 응답하지 않아요
**A:** 다음을 순서대로 확인:
1. Backend 서버 실행 중?
2. FastAPI 서버 실행 중?
3. OpenAI API Key 설정됨?
4. 브라우저 콘솔에 에러 메시지 확인

---

**작성일**: 2025-11-17  
**업데이트**: 챗봇 userIdx null 문제 해결










