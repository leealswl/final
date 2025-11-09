package com.example.backend.controller;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.example.backend.FastAPI.FastAPIService;
import com.example.backend.service.DocumentService;

/**
 * 2025-11-09 수연 추가: CustomMultipartFile 클래스
 * 목적: 서버에 이미 저장된 파일을 MultipartFile 형태로 변환하여 FastAPI로 전송
 * 이유: Frontend에서 파일 메타정보만 받고, Backend가 실제 파일을 읽어서 FastAPI로 전달
 */
class CustomMultipartFile implements MultipartFile {
    private final byte[] fileContent;
    private final String fileName;
    private final String contentType;

    public CustomMultipartFile(byte[] fileContent, String fileName, String contentType) {
        this.fileContent = fileContent;
        this.fileName = fileName;
        this.contentType = contentType;
    }

    @Override
    public String getName() {
        return fileName;
    }

    @Override
    public String getOriginalFilename() {
        return fileName;
    }

    @Override
    public String getContentType() {
        return contentType;
    }

    @Override
    public boolean isEmpty() {
        return fileContent == null || fileContent.length == 0;
    }

    @Override
    public long getSize() {
        return fileContent.length;
    }

    @Override
    public byte[] getBytes() throws IOException {
        return fileContent;
    }

    @Override
    public java.io.InputStream getInputStream() throws IOException {
        return new java.io.ByteArrayInputStream(fileContent);
    }

    @Override
    public void transferTo(java.io.File dest) throws IOException, IllegalStateException {
        Files.write(dest.toPath(), fileContent);
    }
}




/**
 * 문서 분석 API 컨트롤러
 * - 파일 업로드 및 FastAPI 연동을 통한 문서 분석 처리
 */
@RestController
@RequestMapping("/api/analysis")
public class AnalysisController {

    @Autowired
    FastAPIService fastApi;

    @Autowired
    DocumentService documentService;

    /**
     * 업로드 경로 테스트용 엔드포인트
     */
    @GetMapping("/path")
    public String test() {
        Path uploadPath = Paths.get("uploads/");
        
        System.out.println(uploadPath);
        return uploadPath.toString();
    }


    /**
     * 파일 업로드 및 분석 요청 처리
     *
     * @param files 업로드할 파일 목록
     * @param folders 파일이 저장될 폴더 ID 목록
     * @param projectidx 프로젝트 ID
     * @param userid 사용자 ID
     * @return FastAPI 분석 결과 또는 에러 메시지
     *
     * 처리 흐름:
     * 1. DB에 문서 정보 저장 (DocumentService)
     * 2. FastAPI로 파일 전송하여 분석 수행
     * 3. FastAPI 분석 결과 반환
     */
    @PostMapping(value = {"", "/"}, consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Map<String, Object>> receiveAndSendFiles(
        @RequestParam("files") List<MultipartFile> files,
        @RequestParam("folders") List<Long> folders,
        @RequestParam("projectidx") Long projectidx,
        @RequestParam("userid") String userid) {
            System.out.println("analysis controller 작동 시작");
            // System.out.println("Received userid: " + userid);
            // System.out.println("Received projectidx: " + projectidx);
            // System.out.println("Received folders: " + folders);

        try {
            // 1단계: DB에 파일 정보 저장하고 파일 정보 반환 (2025-11-09 수연 수정)
            List<Map<String, Object>> savedFiles = documentService.saveFilesAndReturnInfo(files, folders, userid, projectidx);

            if (savedFiles.isEmpty()) {
                return ResponseEntity.badRequest()
                        .body(Map.of("status", "fail", "message", "문서 저장 실패"));
            }

            // 2단계: FastAPI 분석은 "분석 시작" 버튼 클릭 시에만 실행
            // 업로드 시점에는 DB 저장만 수행

            // 업로드 성공 응답 (파일 정보 포함)
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "파일 업로드 완료",
                "savedCount", savedFiles.size(),
                "files", savedFiles // 2025-11-09 수연 추가: 파일 정보 반환
            ));

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError()
                    .body(Map.of("status", "error", "message", e.getMessage()));
        }
    }

    /**
     * 2025-11-09 수연 추가: 분석 시작 API
     * 목적: Frontend의 "분석 시작" 버튼 클릭 시 호출
     * 처리 흐름:
     * 1. Frontend에서 파일 메타정보(id, name, path) 수신
     * 2. 서버에 저장된 실제 파일 읽기
     * 3. FastAPI로 파일 전송하여 AI 분석 실행
     * 4. 분석 결과 반환
     */
    @PostMapping("/start")
    public ResponseEntity<Map<String, Object>> startAnalysis(@RequestBody Map<String, Object> payload) {
        System.out.println("🚀 분석 시작 API 호출됨");

        try {
            // 1. Frontend에서 받은 데이터 추출
            Long projectId = ((Number) payload.get("projectId")).longValue();
            String userId = (String) payload.get("userId");

            @SuppressWarnings("unchecked")
            List<Map<String, Object>> announcementFiles = (List<Map<String, Object>>) payload.get("announcement_files");

            @SuppressWarnings("unchecked")
            List<Map<String, Object>> attachmentFiles = (List<Map<String, Object>>) payload.get("attachment_files");

            System.out.println("📋 프로젝트 ID: " + projectId);
            System.out.println("👤 사용자 ID: " + userId);
            System.out.println("📄 공고문 파일: " + announcementFiles.size() + "개");
            System.out.println("📎 첨부 파일: " + attachmentFiles.size() + "개");

            // 2. 서버에 저장된 파일 읽기 및 MultipartFile로 변환
            List<MultipartFile> files = new ArrayList<>();
            List<Long> folders = new ArrayList<>();

            // 공고문 파일 처리 (폴더 ID: 1)
            for (Map<String, Object> fileInfo : announcementFiles) {
                String filePath = (String) fileInfo.get("path");
                String fileName = (String) fileInfo.get("name");

                MultipartFile multipartFile = loadFileAsMultipart(filePath, fileName);
                if (multipartFile != null) {
                    files.add(multipartFile);
                    folders.add(1L); // 공고문 폴더
                }
            }

            // 첨부 파일 처리 (폴더 ID: 2)
            for (Map<String, Object> fileInfo : attachmentFiles) {
                String filePath = (String) fileInfo.get("path");
                String fileName = (String) fileInfo.get("name");

                MultipartFile multipartFile = loadFileAsMultipart(filePath, fileName);
                if (multipartFile != null) {
                    files.add(multipartFile);
                    folders.add(2L); // 첨부파일 폴더
                }
            }

            System.out.println("✅ 파일 로드 완료: " + files.size() + "개");

            // 3. FastAPI로 파일 전송하여 분석 실행
            Map<String, Object> fastApiResult = fastApi.sendFilesToFastAPI(files, folders, userId, projectId);

            System.out.println("✅ FastAPI 분석 완료");

            // 4. 분석 결과 반환
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "분석이 완료되었습니다.",
                "data", fastApiResult
            ));

        } catch (Exception e) {
            e.printStackTrace();
            System.err.println("❌ 분석 실패: " + e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(Map.of(
                        "status", "error",
                        "message", "분석 중 오류가 발생했습니다: " + e.getMessage()
                    ));
        }
    }

    /**
     * 2025-11-09 수연 추가: 파일 경로로 파일을 읽어서 MultipartFile로 변환하는 헬퍼 메서드
     *
     * @param filePath 서버에 저장된 파일 경로
     * @param fileName 파일명
     * @return MultipartFile 객체 (파일이 없으면 null)
     */
    private MultipartFile loadFileAsMultipart(String filePath, String fileName) {
        try {
            Path path = Paths.get(filePath);

            if (!Files.exists(path)) {
                System.err.println("⚠️ 파일이 존재하지 않음: " + filePath);
                return null;
            }

            byte[] fileContent = Files.readAllBytes(path);
            String contentType = Files.probeContentType(path);

            if (contentType == null) {
                contentType = "application/octet-stream";
            }

            return new CustomMultipartFile(fileContent, fileName, contentType);

        } catch (IOException e) {
            System.err.println("❌ 파일 읽기 실패: " + filePath + " - " + e.getMessage());
            return null;
        }
    }

}
