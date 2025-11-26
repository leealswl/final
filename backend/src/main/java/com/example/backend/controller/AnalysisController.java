package com.example.backend.controller;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
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
import com.example.backend.service.AnalysisService;
import com.example.backend.service.DocumentService;
import com.example.backend.util.CustomMultipartFile;

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

    @Autowired
    AnalysisService analysisService; // 2025-11-09 suyeon 추가: Oracle DB 저장용 서비스

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

            // 2단계: FastAPI로 파일 전송 및 분석 수행
            // Map<String, Object> fastApiResult = fastApi.sendFilesToFastAPI(files, folders, userid);

            // 3단계: FastAPI 분석 결과 반환
            // if (fastApiResult != null && "success".equals(fastApiResult.get("status"))) {
            //     return new ResponseEntity<>(fastApiResult, HttpStatus.OK);
            // } else {
            //     return ResponseEntity.internalServerError()
            //             .body(Map.of("status", "fail", "message", "FastAPI 처리 실패"));
            // }

            // FastAPI를 안 쓰는 동안에는 저장 성공만 바로 반환 (현재 비활성화)
            // return ResponseEntity.ok(Map.of(
            //     "status", "success",
            //     "message", "FastAPI 비활성화",
            //     "savedCount", resultDocs
            // ));
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

            // 2025-11-09 수연 추가: 파일이 하나도 없으면 에러 반환
            if (files.isEmpty()) {
                System.err.println("❌ 로드된 파일이 없음");
                return ResponseEntity.badRequest()
                        .body(Map.of(
                            "status", "error",
                            "message", "파일 경로 정보가 없습니다. 파일을 다시 업로드해주세요."
                        ));
            }

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
     * 2025-11-09 suyeon 추가: FastAPI 분석 결과를 받아서 Oracle DB에 저장하는 API
     *
     * FastAPI가 CSV/JSON 파일을 생성한 후 이 API를 호출하여 DB에 저장
     * 이렇게 하면 개발 환경(macOS/Windows/Linux)에 관계없이 모든 팀원이 동일하게 작동
     *
     * @param analysisData FastAPI에서 전송한 분석 결과 데이터
     * @return 저장 성공 여부
     */
    @PostMapping("/save-result")
    public ResponseEntity<Map<String, Object>> saveAnalysisResult(@RequestBody Map<String, Object> analysisData) {
        System.out.println("💾 FastAPI로부터 분석 결과 수신");

        try {
            // 2025-11-09 suyeon: FastAPI로부터 받은 데이터 파싱
            Long projectIdx = ((Number) analysisData.get("project_idx")).longValue();
            String userId = (String) analysisData.get("user_id");

            @SuppressWarnings("unchecked")
            List<Map<String, Object>> features = (List<Map<String, Object>>) analysisData.get("extracted_features");

            @SuppressWarnings("unchecked")
            Map<String, Object> tableOfContents = (Map<String, Object>) analysisData.get("table_of_contents");

            System.out.println("📊 프로젝트 ID: " + projectIdx);
            System.out.println("📊 Features: " + (features != null ? features.size() : 0) + "개");
            System.out.println("📊 목차: " + (tableOfContents != null ? "있음" : "없음"));

            // 2025-11-09 suyeon: AnalysisService를 통해 Oracle DB에 저장
            Map<String, Object> saveResult = analysisService.saveAnalysisResult(
                projectIdx, userId, features, tableOfContents
            );

            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "분석 결과가 Oracle DB에 저장되었습니다.",
                "saved_features", saveResult.get("features_count"),
                "saved_toc", (boolean) saveResult.get("toc_saved") ? "yes" : "no"
            ));

        } catch (Exception e) {
            e.printStackTrace();
            System.err.println("❌ DB 저장 실패: " + e.getMessage());
            return ResponseEntity.internalServerError()
                    .body(Map.of(
                        "status", "error",
                        "message", "DB 저장 실패: " + e.getMessage()
                    ));
        }
    }

    /**
     * 2025-11-17: 프로젝트의 분석 결과 목차(TOC) 조회 API
     * 2025-11-23 수정: FastAPI 로컬 파일 대신 Oracle DB에서 직접 조회
     * 
     * @param projectIdx 프로젝트 ID
     * @return 목차 데이터 (sections 배열)
     */
    @GetMapping("/toc")
    public ResponseEntity<Map<String, Object>> getTableOfContents(
        @RequestParam("projectIdx") Long projectIdx
    ) {
        System.out.println("📚 목차 조회 API 호출: projectIdx=" + projectIdx);
        
        try {
            // Oracle DB에서 목차 데이터 직접 조회
            Map<String, Object> context = analysisService.getAnalysisContext(projectIdx);
            Map<String, Object> tocData = (Map<String, Object>) context.get("result_toc");
            
            if (tocData == null || !tocData.containsKey("sections")) {
                return ResponseEntity.ok(Map.of(
                    "status", "error",
                    "message", "목차 데이터가 없습니다.",
                    "sections", List.of()
                ));
            }
            
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "목차 데이터 조회 성공",
                "data", tocData
            ));
            
        } catch (Exception e) {
            e.printStackTrace();
            System.err.println("❌ 목차 조회 실패: " + e.getMessage());
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "status", "error",
                    "message", "목차 조회 중 오류가 발생했습니다: " + e.getMessage(),
                    "sections", List.of()
                ));
        }
    }

    /**
     * 2025-11-23 추가: v11_generator용 분석 결과 컨텍스트 조회 API
     * 
     * @param projectIdx 프로젝트 ID
     * @return 분석 결과 컨텍스트 (result_toc, extracted_features)
     */
    @GetMapping("/get-context")
    public ResponseEntity<Map<String, Object>> getAnalysisContext(
        @RequestParam("projectIdx") Long projectIdx
    ) {
        System.out.println("📖 분석 결과 컨텍스트 조회 API 호출: projectIdx=" + projectIdx);
        
        try {
            Map<String, Object> context = analysisService.getAnalysisContext(projectIdx);
            
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "분석 결과 컨텍스트 조회 성공",
                "data", context
            ));
            
        } catch (Exception e) {
            e.printStackTrace();
            System.err.println("❌ 분석 결과 컨텍스트 조회 실패: " + e.getMessage());
            return ResponseEntity.internalServerError()
                .body(Map.of(
                    "status", "error",
                    "message", "분석 결과 컨텍스트 조회 중 오류가 발생했습니다: " + e.getMessage()
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
            // 2025-11-09 수연 추가: filePath가 null이면 에러 방지
            if (filePath == null || filePath.isEmpty()) {
                System.err.println("⚠️ 파일 경로가 null 또는 비어있음: " + fileName);
                return null;
            }

            // 2025-11-10 수연 수정: 상대 경로(/uploads/...)를 절대 경로로 변환
            // DB에는 /uploads/userId/1/1/file.pdf 형태로 저장되어 있음
            String absolutePath;
            if (filePath.startsWith("/uploads/")) {
                // /uploads/ 제거하고 backend/uploads/와 결합
                String relativePart = filePath.substring("/uploads/".length());
                absolutePath = "/uploads/" + relativePart;
            } else if (filePath.startsWith("uploads/")) {
                // uploads/로 시작하면 backend/ 추가
                absolutePath = "/" + filePath;
            } else {
                // 이미 절대 경로이거나 다른 형식
                absolutePath = filePath;
            }

            Path path = Paths.get(absolutePath);

            System.out.println("  📂 경로 변환: " + filePath + " → " + absolutePath);

            if (!Files.exists(path)) {
                System.err.println("⚠️ 파일이 존재하지 않음: " + absolutePath);
                System.err.println("   (원본 경로: " + filePath + ")");
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
