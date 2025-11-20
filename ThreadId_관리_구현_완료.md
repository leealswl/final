# ThreadId 관리 로직 구현 완료 보고서

## ✅ 구현 완료 사항

### 1. 프론트엔드 (React)

#### `ChatBotMUI.jsx`
- ✅ `threadId` 상태 추가 (`useState`)
- ✅ 응답에서 `threadId` 받아서 저장
- ✅ 다음 요청 시 저장된 `threadId` 전송

**주요 변경사항:**
```javascript
// ThreadId 상태 추가
const [threadId, setThreadId] = useState(null);

// 요청 시 threadId 포함
sendChatMessage({
    userMessage: userText,
    userIdx: user?.idx || 1,
    projectIdx: project?.projectIdx || 1,
    threadId: threadId // 🔑 저장된 threadId 전송
}, {
    onSuccess: (data) => {
        // 응답에서 threadId 받아서 저장
        if (data.threadId) {
            setThreadId(data.threadId);
        }
    }
});
```

#### `useChatbot.js`
- ✅ `threadId` 파라미터 추가
- ✅ `threadId`가 있으면 요청에 포함, 없으면 제외

**주요 변경사항:**
```javascript
mutationFn: async ({userMessage, userIdx, projectIdx, threadId}) => {
    const requestBody = threadId 
        ? { userMessage, userIdx, projectIdx, threadId }
        : { userMessage, userIdx, projectIdx };
    // ...
}
```

### 2. Java 백엔드

#### `AiChatController.java`
- ✅ 요청에서 `threadId` 받기
- ✅ `threadId`를 Service 레이어로 전달

**주요 변경사항:**
```java
@PostMapping("/response")
public AiChat sendMessage(@RequestBody AiChat chatRequest){
    return aiChatService.processChat(
        chatRequest.getUserMessage(),
        chatRequest.getUserIdx(),
        chatRequest.getProjectIdx(),
        chatRequest.getThreadId() // 🔑 ThreadId 전달
    );
}
```

#### `AiChatService.java` (인터페이스)
- ✅ `processChat` 메서드에 `threadId` 파라미터 추가

#### `AiChatServiceImpl.java`
- ✅ `threadId` 파라미터 받기
- ✅ `threadId`를 `FastAPIService`에 전달

**주요 변경사항:**
```java
public AiChat processChat(String userMessage, Long userIdx, Long projectIdx, String threadId) {
    // ...
    fastApiResponse = fastAPIService.ChatbotMessage(
        userMessage, 
        userIdx.toString(),
        projectIdx,
        threadId // 🔑 ThreadId 전달
    );
}
```

#### `FastAPIService.java` (핵심 수정)
- ✅ **ThreadId 기반 라우팅 로직 활성화**
- ✅ `threadId`가 없으면 → `/generate` (최초 요청)
- ✅ `threadId`가 있으면 → `/resume_generation` (재개 요청)

**주요 변경사항:**
```java
if (threadId != null && !threadId.isEmpty()) {
    // 🔑 재개 요청
    endpointPath = this.resumePath; // "/resume_generation"
    requestBody = new HashMap<>();
    requestBody.put("thread_id", threadId);
    requestBody.put("userMessage", message);
    // ...
} else {
    // 🔑 최초 요청
    endpointPath = this.generatePath; // "/generate"
    requestBody = new HashMap<>();
    requestBody.put("userMessage", message);
    // ...
}
```

## 🔄 전체 플로우

### 최초 요청 (threadId 없음)
```
프론트엔드
  ↓ { userMessage, userIdx, projectIdx } (threadId 없음)
Java 백엔드 (AiChatController)
  ↓ threadId = null
Java 백엔드 (FastAPIService)
  ↓ 라우팅: /generate
FastAPI (/generate)
  ↓ LangGraph 실행 → thread_id 생성
  ↓ 응답: { status, message, thread_id, ... }
Java 백엔드
  ↓ thread_id 포함하여 반환
프론트엔드
  ↓ threadId 저장 (다음 요청에 사용)
```

### 재개 요청 (threadId 있음)
```
프론트엔드
  ↓ { userMessage, userIdx, projectIdx, threadId } (저장된 threadId 포함)
Java 백엔드 (AiChatController)
  ↓ threadId 전달
Java 백엔드 (FastAPIService)
  ↓ 라우팅: /resume_generation
FastAPI (/resume_generation)
  ↓ LangGraph 재개 (저장된 상태 로드)
  ↓ 응답: { status, message, thread_id, ... }
Java 백엔드
  ↓ thread_id 포함하여 반환
프론트엔드
  ↓ threadId 유지 (다음 요청에도 사용)
```

## 🎯 해결된 문제

### 1. 세션 증발 문제 해결
- **이전**: 모든 요청이 `/generate`로 전송되어 새 세션이 계속 생성됨
- **현재**: `threadId`가 있으면 `/resume_generation`으로 재개 요청

### 2. LangGraph Pause/Resume 기능 활용
- **이전**: LangGraph의 상태 저장 기능이 사용되지 않음
- **현재**: `threadId`를 통해 이전 상태를 로드하고 재개

### 3. 루프 문제 해결
- **이전**: 사용자 답변을 받지 못하고 새로운 상태 초기화 반복
- **현재**: 사용자 답변이 `current_response`로 주입되어 정상적으로 처리

## 🧪 테스트 방법

### 1. 서버 실행
```bash
# FastAPI (포트 8001)
cd alice/fastAPI/src
python -m uvicorn fastAPI_v6_integrated:app --reload --host 127.0.0.1 --port 8001

# Java 백엔드 (포트 8081)
cd backend
./mvnw.cmd spring-boot:run

# 프론트엔드 (포트 5173)
cd frontend
npm run dev
```

### 2. 테스트 시나리오
1. **최초 요청**: 프론트엔드에서 첫 메시지 전송
   - 로그 확인: `➡️ 자바 백엔드 라우팅: 기획서 생성 최초 요청 -> /generate`
   - 응답에서 `threadId` 확인

2. **재개 요청**: 프론트엔드에서 두 번째 메시지 전송
   - 로그 확인: `➡️ 자바 백엔드 라우팅: LangGraph 재개 요청 -> /resume_generation`
   - 같은 `threadId`로 재개되는지 확인

3. **연속 대화**: 여러 번 메시지 전송
   - 각 요청마다 같은 `threadId` 사용되는지 확인
   - LangGraph가 이전 상태를 유지하며 진행되는지 확인

### 3. 확인할 로그

**Java 백엔드:**
```
💬 Chat 요청 수신: [메시지]
🔑 ThreadId: [threadId 또는 "없음 (최초 요청)"]
➡️ 자바 백엔드 라우팅: [최초 요청 또는 재개 요청] -> [엔드포인트]
✅ FastAPI 응답 수신 완료
```

**FastAPI:**
```
📢 기획서 생성 (LangGraph) 최초 요청 수신: [메시지]
또는
📢 LangGraph 재개 요청 수신: thread_id=[threadId], message=[메시지]
```

**프론트엔드 (브라우저 콘솔):**
```
✅ ThreadId 저장: [threadId]
```

## 📝 추가 개선 사항 (선택적)

1. **ThreadId 영구 저장**: 현재는 React 상태에만 저장되어 페이지 새로고침 시 사라짐
   - `localStorage` 또는 `sessionStorage`에 저장 고려

2. **에러 처리**: `threadId`가 유효하지 않을 때 처리
   - FastAPI에서 `threadId`가 없거나 유효하지 않으면 새 세션 생성

3. **세션 만료**: 오래된 세션 정리
   - FastAPI에서 일정 시간 이상 사용되지 않은 세션 삭제

## ✅ 완료 체크리스트

- [x] 프론트엔드: `threadId` 상태 추가
- [x] 프론트엔드: 응답에서 `threadId` 저장
- [x] 프론트엔드: 요청에 `threadId` 포함
- [x] Java 백엔드: Controller에서 `threadId` 받기
- [x] Java 백엔드: Service에서 `threadId` 전달
- [x] Java 백엔드: FastAPIService에서 `threadId` 기반 라우팅 활성화
- [x] Java 백엔드: `/generate`와 `/resume_generation` 라우팅 분기

