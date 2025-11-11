# 분석 시작 기능 구현 과정 및 문제 해결

**작성일**: 2025-11-09
**작성자**: 수연

---

## 목차
1. [구현 목표](#구현-목표)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [구현 단계](#구현-단계)
4. [발생한 문제 및 해결](#발생한-문제-및-해결)
5. [최종 결과](#최종-결과)
6. [주요 코드 변경 사항](#주요-코드-변경-사항)

---

## 구현 목표

분석 페이지(`/works/analyze`)에서 **"분석 시작 (RFP 필수)"** 버튼을 클릭하면:

1. 공고문 폴더(`root-01`)와 파일 폴더(`root-02`)에서 업로드된 파일 수집
2. 수집된 파일을 Backend로 전송
3. Backend가 서버에 저장된 실제 파일을 읽어서 FastAPI로 전달
4. FastAPI가 AI 분석 수행 (RAG 기반)
5. 분석 결과를 대시보드 페이지(`/works/analyze/dashboard`)에 표시

---

## 시스템 아키텍처

```
[Frontend - React]
    ↓ 1. 파일 업로드
[Backend - Spring Boot]
    ↓ 2. 파일 저장 + 경로 정보 반환
[Database - Oracle]

[Frontend - React]
    ↓ 3. "분석 시작" 버튼 클릭 (파일 경로 정보 전송)
[Backend - Spring Boot]
    ↓ 4. 서버 파일 읽기 + FastAPI 전송
[FastAPI - Python]
    ↓ 5. AI 분석 (RAG)
[Frontend - React]
    ↓ 6. 분석 결과 표시
```

---

## 구현 단계

### 1단계: Frontend - 파일 업로드 시 경로 정보 저장

**목적**: 업로드된 파일의 서버 경로를 Frontend store에 저장

**파일**: `final/frontend/src/components/Upload.jsx`

**변경 내용**:
```javascript
// Backend에서 반환한 파일 정보를 트리 노드로 변환
if (response?.files && response.files.length > 0) {
  nodes = response.files.map(fileInfo => ({
    id: `file-${fileInfo.id}`,
    type: 'file',
    name: fileInfo.name,
    path: fileInfo.path, // 2025-11-09 수연: 파일 경로 저장
    size: fileInfo.size,
    children: undefined
  }))
}
```

**이유**: 나중에 "분석 시작" 버튼 클릭 시, Frontend가 파일의 서버 경로를 Backend로 전송해야 하므로

---

### 2단계: Backend - 파일 정보 반환 API 추가

**목적**: 파일 업로드 시 파일 경로 정보를 Frontend로 반환

**파일**: `final/backend/src/main/java/com/example/backend/service/DocumentService.java`

**추가 메서드**:
```java
/**
 * 2025-11-09 수연 추가: 파일 정보와 함께 저장 (경로 정보 반환)
 */
public List<Map<String, Object>> saveFilesAndReturnInfo(
    List<MultipartFile> files,
    List<Long> folders,
    String userId,
    Long projectIdx
) throws Exception;
```

**구현**: `DocumentServiceImpl.java`
```java
// 파일 정보 수집 (Frontend로 반환)
Map<String, Object> fileInfo = new HashMap<>();
fileInfo.put("id", document.getDocumentIdx()); // DB에서 생성된 ID
fileInfo.put("name", file.getOriginalFilename());
fileInfo.put("path", filePath.toString()); // 파일 경로
fileInfo.put("folder", folderName);
fileInfo.put("size", file.getSize());
savedFiles.add(fileInfo);
```

**이유**: Frontend가 파일 경로를 알아야 나중에 분석 요청 시 Backend에 전달 가능

---

### 3단계: Frontend - 분석 시작 기능 구현

**목적**: "분석 시작" 버튼 클릭 시 파일 수집 및 Backend 전송

**파일**: `final/frontend/src/pages/works/views/AnalyzeView.jsx`

**핵심 로직**:
```javascript
const handleAnalysisStart = async () => {
  // 1. 공고문 폴더(root-01)와 파일 폴더(root-02)에서 파일 수집
  const 공고문폴더 = tree.find(node => node.id === 'root-01')
  const 파일폴더 = tree.find(node => node.id === 'root-02')

  const 공고문파일들 = 공고문폴더 ? collectFiles([공고문폴더]) : []
  const 첨부파일들 = 파일폴더 ? collectFiles([파일폴더]) : []

  // 2. Backend로 파일 경로 정보 전송
  const payload = {
    projectId: currentProjectId,
    userId: currentUserId,
    announcement_files: 공고문파일들.map(f => ({
      id: f.id,
      name: f.name,
      path: f.path, // 서버 파일 경로
      folderId: 1
    })),
    attachment_files: 첨부파일들.map(f => ({
      id: f.id,
      name: f.name,
      path: f.path,
      folderId: 2
    }))
  }

  // 3. Backend API 호출
  const response = await api.post('/api/analysis/start', payload)

  // 4. 분석 완료 후 대시보드로 이동
  navigate('/works/analyze/dashboard', {
    state: { analysisResult: response.data }
  })
}
```

---

### 4단계: Backend - 분석 시작 API 구현

**목적**: Frontend에서 받은 파일 경로로 실제 파일을 읽어 FastAPI로 전송

**파일**: `final/backend/src/main/java/com/example/backend/controller/AnalysisController.java`

**CustomMultipartFile 클래스 추가**:
```java
/**
 * 2025-11-09 수연 추가: CustomMultipartFile 클래스
 * 목적: 서버에 이미 저장된 파일을 MultipartFile 형태로 변환하여 FastAPI로 전송
 * 이유: Frontend에서 파일 메타정보만 받고, Backend가 실제 파일을 읽어서 FastAPI로 전달
 */
class CustomMultipartFile implements MultipartFile {
    private final byte[] fileContent;
    private final String fileName;
    private final String contentType;
    // ... MultipartFile 인터페이스 구현
}
```

**분석 시작 엔드포인트**:
```java
@PostMapping("/start")
public ResponseEntity<Map<String, Object>> startAnalysis(
    @RequestBody Map<String, Object> payload
) {
    // 1. Frontend에서 받은 데이터 추출
    Long projectId = ((Number) payload.get("projectId")).longValue();
    String userId = (String) payload.get("userId");
    List<Map<String, Object>> announcementFiles = ...
    List<Map<String, Object>> attachmentFiles = ...

    // 2. 서버에 저장된 파일 읽기 및 MultipartFile로 변환
    List<MultipartFile> files = new ArrayList<>();
    List<Long> folders = new ArrayList<>();

    for (Map<String, Object> fileInfo : announcementFiles) {
        String filePath = (String) fileInfo.get("path");
        String fileName = (String) fileInfo.get("name");
        MultipartFile multipartFile = loadFileAsMultipart(filePath, fileName);
        if (multipartFile != null) {
            files.add(multipartFile);
            folders.add(1L); // 공고문 폴더
        }
    }

    // 3. FastAPI로 파일 전송하여 분석 실행
    Map<String, Object> fastApiResult = fastApi.sendFilesToFastAPI(
        files, folders, userId, projectId
    );

    // 4. 분석 결과 반환
    return ResponseEntity.ok(Map.of(
        "status", "success",
        "message", "분석이 완료되었습니다.",
        "data", fastApiResult
    ));
}
```

**헬퍼 메서드**:
```java
private MultipartFile loadFileAsMultipart(String filePath, String fileName) {
    // 2025-11-09 수연 추가: filePath가 null이면 에러 방지
    if (filePath == null || filePath.isEmpty()) {
        System.err.println("⚠️ 파일 경로가 null 또는 비어있음: " + fileName);
        return null;
    }

    Path path = Paths.get(filePath);
    if (!Files.exists(path)) {
        System.err.println("⚠️ 파일이 존재하지 않음: " + filePath);
        return null;
    }

    byte[] fileContent = Files.readAllBytes(path);
    String contentType = Files.probeContentType(path);
    return new CustomMultipartFile(fileContent, fileName, contentType);
}
```

---

### 5단계: Frontend - 분석 대시보드 페이지 생성

**목적**: 분석 결과를 시각적으로 표시

**파일**: `final/frontend/src/pages/works/views/AnalyzeDashboard.jsx` (신규)

**핵심 기능**:
```javascript
const AnalyzeDashboard = () => {
  const location = useLocation()
  const analysisResult = location.state?.analysisResult

  return (
    <Container>
      <Typography variant="h4">분석 결과 대시보드</Typography>

      {/* 분석 상태 */}
      <StatusSection status={analysisResult?.status} />

      {/* 사용자 폼 데이터 */}
      <UserFormSection data={analysisResult?.data?.user_form} />

      {/* 문서 분석 결과 */}
      <DocumentsSection data={analysisResult?.data?.documents} />

      {/* 첨부파일 템플릿 */}
      <AttachmentsSection data={analysisResult?.data?.attachment_templates} />

      {/* 원본 JSON */}
      <RawDataSection data={analysisResult} />
    </Container>
  )
}
```

**라우팅 추가**: `App.jsx`
```javascript
<Route path="analyze/dashboard" element={<AnalyzeDashboard />} />
```

---

## 발생한 문제 및 해결

### 문제 1: 500 Internal Server Error (첫 번째 테스트)

**증상**:
- "분석 시작" 버튼 클릭 시 500 에러 발생
- Frontend 콘솔: `AxiosError: Request failed with status code 500`

**원인**:
- 기존에 업로드된 파일들은 `path` 정보가 없음 (코드 수정 전에 업로드됨)
- Backend에서 `Paths.get(filePath)` 호출 시 `filePath`가 `null`이어서 `NullPointerException` 발생

**해결 방법**:
1. **Backend에 null 체크 추가** (AnalysisController.java)
   ```java
   if (filePath == null || filePath.isEmpty()) {
       System.err.println("⚠️ 파일 경로가 null 또는 비어있음: " + fileName);
       return null;
   }
   ```

2. **파일이 없을 때 명확한 에러 메시지**
   ```java
   if (files.isEmpty()) {
       return ResponseEntity.badRequest()
           .body(Map.of(
               "status", "error",
               "message", "파일 경로 정보가 없습니다. 파일을 다시 업로드해주세요."
           ));
   }
   ```

3. **localStorage 초기화 및 파일 재업로드**
   - 브라우저 개발자도구 → Application → Local Storage → `file-store` 삭제
   - 파일 재업로드 → 이제 `path` 정보 포함

**결과**: 500 에러 해결

---

### 문제 2: Timeout Error (두 번째 테스트)

**증상**:
- "분석 시작" 버튼 클릭 후 스피너 표시
- 약 50초 후 타임아웃 에러 발생
- Frontend 콘솔: `AxiosError: timeout of 50000ms exceeded`

**원인**:
- FastAPI AI 분석이 50초 이상 소요됨
- Frontend axios 기본 타임아웃: 50초 (50000ms)

**해결 방법**:
**axios timeout 증가** (api.js)
```javascript
const api = axios.create({
  baseURL: "/backend",
  withCredentials: true,
  timeout: 300000, // 2025-11-09 수연 수정: 5분으로 증가
  headers: {
    "Content-Type": "application/json",
  },
});
```

**결과**: 타임아웃 에러 해결 가능 (재테스트 필요)

---

### 문제 3: FastAPI 분석 결과 확인 (진행 중)

**현재 상태**:
- Backend에서 FastAPI로 파일 전송 성공 추정
- FastAPI 분석 수행 완료 추정
- 분석 결과 파일 생성 확인: `table_of_contents_1_20251109_122532.json`

**다음 단계**:
- Frontend에서 "분석 시작" 버튼 재클릭
- 분석 완료까지 대기 (최대 5분)
- 대시보드 페이지로 이동 확인
- 분석 결과 표시 확인

---

## 최종 결과

### 구현 완료 항목

✅ **파일 업로드 시 경로 정보 저장**
- Upload.jsx: 파일 경로를 store에 저장
- DocumentService: 파일 정보 반환 API 추가

✅ **분석 시작 기능**
- AnalyzeView.jsx: 파일 수집 및 Backend 전송
- AnalysisController.java: `/api/analysis/start` 엔드포인트 추가
- CustomMultipartFile: 서버 파일을 MultipartFile로 변환

✅ **에러 핸들링**
- Null 체크 추가 (파일 경로)
- Timeout 증가 (50초 → 5분)
- 명확한 에러 메시지

✅ **분석 대시보드**
- AnalyzeDashboard.jsx: 분석 결과 표시 페이지
- 라우팅 설정

### 테스트 필요 항목

🔄 **전체 플로우 테스트**
1. 파일 업로드 (경로 정보 포함)
2. "분석 시작" 버튼 클릭
3. Backend → FastAPI 통신 확인
4. 분석 결과 수신
5. 대시보드 페이지 표시

---

## 주요 코드 변경 사항

### Frontend

| 파일 | 변경 내용 | 이유 |
|------|----------|------|
| `Upload.jsx` | 파일 경로(`path`) store 저장 | 분석 요청 시 서버 경로 필요 |
| `AnalyzeView.jsx` | 분석 시작 핸들러 구현 | 파일 수집 및 Backend 전송 |
| `AnalyzeDashboard.jsx` | 대시보드 페이지 생성 (신규) | 분석 결과 시각화 |
| `App.jsx` | 대시보드 라우트 추가 | 페이지 네비게이션 |
| `api.js` | timeout 50초 → 300초 | AI 분석 시간 확보 |

### Backend

| 파일 | 변경 내용 | 이유 |
|------|----------|------|
| `DocumentService.java` | `saveFilesAndReturnInfo` 메서드 추가 | 파일 경로 정보 반환 |
| `DocumentServiceImpl.java` | 파일 정보 수집 로직 구현 | Frontend로 경로 전달 |
| `AnalysisController.java` | `CustomMultipartFile` 클래스 추가 | 서버 파일 → MultipartFile 변환 |
| `AnalysisController.java` | `/start` 엔드포인트 추가 | 분석 시작 API |
| `AnalysisController.java` | Null 체크 및 에러 핸들링 | 안정성 향상 |

---

## Git 커밋 이력

```bash
# 2025-11-09 로컬 커밋 완료
git add .
git commit -m "Implement analysis start feature with file path tracking"
```

**커밋 내용**:
- Frontend: 파일 업로드 시 경로 저장, 분석 시작 기능, 대시보드 페이지
- Backend: 파일 정보 반환 API, 분석 시작 엔드포인트, CustomMultipartFile
- 에러 핸들링: Null 체크, Timeout 증가

---

## 참고 사항

### 디렉토리 구조
```
final/
├── backend/
│   └── src/main/java/com/example/backend/
│       ├── controller/AnalysisController.java
│       ├── service/DocumentService.java
│       └── service/DocumentServiceImpl.java
├── frontend/
│   └── src/
│       ├── components/Upload.jsx
│       ├── pages/works/views/
│       │   ├── AnalyzeView.jsx
│       │   └── AnalyzeDashboard.jsx (신규)
│       ├── utils/api.js
│       └── App.jsx
└── alice/fastAPI/src/
    └── parsed_results/v6_rag/
        └── table_of_contents_1_20251109_122532.json (분석 결과)
```

### 서버 포트
- Frontend (Vite): `http://localhost:5173`
- Backend (Spring Boot): `http://localhost:8081`
- FastAPI (Python): `http://localhost:8001`

### 현재 서버 상태
- 모든 서버 종료됨 (2025-11-09 12:17 기준)

---

## 다음 작업

1. ✅ 모든 서버 종료
2. 📝 구현 과정 문서화 (현재 파일)
3. 🔄 서버 재시작 및 전체 플로우 재테스트
4. ✅ 분석 결과 확인 및 대시보드 표시 검증
5. 🚀 최종 커밋 및 GitHub 푸시

---

**문서 작성**: 2025-11-09
**최종 수정**: 2025-11-09
