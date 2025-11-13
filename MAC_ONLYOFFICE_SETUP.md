# Mac용 OnlyOffice 설정 가이드

## 개요
이 문서는 프로젝트를 Windows 환경에서 Mac 환경으로 전환할 때 필요한 OnlyOffice 관련 설정 변경사항을 정리합니다.

---

## 1. Backend 설정 변경

### 1.1 StaticMapping.java
**파일 위치:** `backend/src/main/java/com/example/backend/onlyoffice/StaticMapping.java`

**변경 내용:**
```java
@Configuration
public class StaticMapping implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry reg) {
        // ★ Windows (팀원용): backend/uploads
        // Path uploadDir = Path.of("backend/uploads").toAbsolutePath();

        // ★ Mac (현재 사용): uploads (프로젝트 루트)
        Path uploadDir = Path.of("uploads").toAbsolutePath();

        String location = uploadDir.toUri().toString();
        if (!location.endsWith("/")) location += "/";
        // mac용 확인
        System.out.println("[StaticMapping] uploads location: " + location);
        reg.addResourceHandler("/uploads/**")
           .addResourceLocations(location);
    }
}
```

**변경 항목:**
- ✅ Windows용 `Path.of("backend/uploads")` 주석처리 (15-16번 줄)
- ✅ Mac용 `Path.of("uploads")` 활성화 (18-19번 줄)
- ✅ 디버그 로그 활성화 (23-24번 줄)

---

### 1.2 OnlyOfficeController.java
**파일 위치:** `backend/src/main/java/com/example/backend/onlyoffice/OnlyOfficeController.java`

**변경 내용:**
```java
@PostMapping("/config")
public ResponseEntity<?> buildConfig(@RequestBody Map<String, Object> body) {
    String url = (String) body.get("url");
    // System.out.println("url: " + url);  // ← 주석처리

    // mac용 onlyoffice dev 서버 테스트 시
    System.out.println("Original url: " + url);  // ← 활성화

    // Docker 컨테이너에서 실행 중인 OnlyOffice가 호스트 머신의 Spring Boot에 접근하려면
    // 127.0.0.1 또는 localhost를 host.docker.internal로 변경
    if (url != null) {  // ← 활성화
        url = url.replace("127.0.0.1", "host.docker.internal")
                 .replace("localhost", "host.docker.internal");
        System.out.println("Converted url for Docker: " + url);
    }
    
    // ... 나머지 코드
}
```

**변경 항목:**
- ✅ 35번 줄: 기존 `System.out.println("url: " + url);` 주석처리
- ✅ 38번 줄: `System.out.println("Original url: " + url);` 활성화
- ✅ 42-46번 줄: Docker URL 변환 로직 활성화

---

## 2. Frontend 설정 변경

### 2.1 Editor.jsx
**파일 위치:** `frontend/src/pages/works/Editor.jsx`

**변경 내용:**
```javascript
try {
  // mac용 확인
  if (ed && typeof ed.createConnector === 'function') {  // ← if 조건 활성화
    const conn = ed.createConnector();
    window.editorBridge = {
      editor: ed,
      conn,
      insert(text) {
        try {
          console.log("[editorBridge.insert] called with:", text);
          this.conn.executeMethod("PasteText", [text]);
          this.conn.executeMethod("PasteText", ["\n"]);
          console.log("[OO] insert via connector OK");
        } catch (e) {
          console.error("[OO] insert error:", e);
        }
      },
    };
    console.log("[OO] editorBridge ready");
  } else {  // ← else 블록 활성화
    // createConnector를 사용할 수 없는 경우 기본 에디터만 제공
    console.info("[OO] createConnector not available (requires Developer Edition or not supported for this file type)");
    window.editorBridge = {
      editor: ed,
      conn: null,
      // eslint-disable-next-line no-unused-vars
      insert(text) {
        console.warn("[OO] Text insertion not available without connector");
      }
    };
  }
} catch (e) {
  // 에러가 발생해도 에디터는 정상 작동
  console.warn("[OO] connector create failed (this is normal for free edition or HWP files):", e.message);
  window.editorBridge = {
    editor: ed,
    conn: null,
    // eslint-disable-next-line no-unused-vars
    insert(text) {
      console.warn("[OO] Text insertion not available without connector");
    }
  };
}
```

**변경 항목:**
- ✅ 127번 줄: `if (ed && typeof ed.createConnector === 'function')` 조건 활성화
- ✅ 144-155번 줄: else 블록 활성화 (createConnector 없을 때 대비)
- ✅ 156-167번 줄: catch 블록에서 fallback editorBridge 생성

---

## 3. 설정 변경 전후 비교

### Windows 설정 (팀원용)
```
Backend:
- StaticMapping: Path.of("backend/uploads")
- OnlyOfficeController: URL 변환 로직 주석처리

Frontend:
- Editor.jsx: createConnector 로직 주석처리 (무조건 connector 생성 시도)
```

### Mac 설정 (현재)
```
Backend:
- StaticMapping: Path.of("uploads")
- OnlyOfficeController: URL 변환 로직 활성화 (127.0.0.1 → host.docker.internal)

Frontend:
- Editor.jsx: createConnector 체크 로직 활성화 (Developer Edition 확인)
```

---

## 4. 서버 실행

모든 설정 변경 후 서버를 재시작해야 합니다:

```bash
# 1. FastAPI 서버 (Port 8001)
cd final/alice/fastAPI/src
uvicorn fastAPI_v6_integrated:app --host 0.0.0.0 --port 8001 --reload

# 2. Backend 서버 (Port 8081)
cd final/backend
./mvnw spring-boot:run

# 3. Frontend 서버 (Port 5173)
cd final/frontend
npm run dev
```

---

## 5. 확인 사항

### Backend 로그 확인
```
[StaticMapping] uploads location: file:///Users/[username]/alice_consultant_agent_real/final/backend/uploads/
```
- ✅ Mac 경로가 올바르게 출력되는지 확인

### OnlyOffice 동작 확인
1. Frontend (http://localhost:5173) 접속
2. 파일 업로드 또는 기존 파일 선택
3. OnlyOffice 편집기가 정상적으로 로드되는지 확인
4. 브라우저 콘솔에서 에러 확인:
   - `[OO] editorBridge ready` 또는
   - `[OO] createConnector not available` 메시지 확인

---

## 6. 트러블슈팅

### Maven wrapper 권한 에러
```bash
chmod +x backend/mvnw
```

### Maven wrapper 파일 누락 에러
```bash
# .mvn/wrapper/maven-wrapper.properties 파일 생성
mkdir -p backend/.mvn/wrapper
cat > backend/.mvn/wrapper/maven-wrapper.properties << 'PROPS'
distributionUrl=https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.8.6/apache-maven-3.8.6-bin.zip
wrapperUrl=https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.1.0/maven-wrapper-3.1.0.jar
PROPS
```

### OnlyOffice 파일 로드 실패
1. Backend 로그에서 `[StaticMapping]` 경로 확인
2. `uploads` 디렉토리가 프로젝트 루트에 존재하는지 확인
3. 파일 경로가 올바른지 확인 (127.0.0.1 → host.docker.internal 변환)

---

## 7. Windows로 되돌리기

Mac → Windows 전환 시:

### Backend
```java
// StaticMapping.java
Path uploadDir = Path.of("backend/uploads").toAbsolutePath();
// Path uploadDir = Path.of("uploads").toAbsolutePath();

// OnlyOfficeController.java
System.out.println("url: " + url);
// System.out.println("Original url: " + url);
// if (url != null) { ... } // 주석처리
```

### Frontend
```javascript
// Editor.jsx
// if (ed && typeof ed.createConnector === 'function') { ... } // 조건 주석처리
const conn = ed.createConnector(); // 무조건 실행
```

---

## 참고사항

- OnlyOffice Developer Edition이 없는 경우 `createConnector`가 작동하지 않을 수 있습니다
- HWP 파일의 경우 일부 기능이 제한될 수 있습니다
- Docker 환경에서 OnlyOffice를 사용하는 경우 `host.docker.internal`로 URL 변환이 필요합니다

---

**작성일:** 2025-11-09  
**버전:** 1.0
