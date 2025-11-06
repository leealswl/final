package com.example.backend.controller;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.example.backend.FastAPI.FastAPIService;
import com.example.backend.service.DocumentService;




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
        return "test";
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
            // 1단계: DB에 파일 정보 저장 (documentService)
            int resultDocs = documentService.saveFilesAndDocuments(files, folders, userid, projectidx);

            if (resultDocs <= 0) {
                return ResponseEntity.badRequest()
                        .body(Map.of("status", "fail", "message", "문서 저장 실패"));
            }

            // 2단계: FastAPI로 파일 전송 및 분석 수행
            Map<String, Object> fastApiResult = fastApi.sendFilesToFastAPI(files, folders, userid);

            // 3단계: FastAPI 분석 결과 반환
            if (fastApiResult != null && "success".equals(fastApiResult.get("status"))) {
                return new ResponseEntity<>(fastApiResult, HttpStatus.OK);
            } else {
                return ResponseEntity.internalServerError()
                        .body(Map.of("status", "fail", "message", "FastAPI 처리 실패"));
            }

            // FastAPI를 안 쓰는 동안에는 저장 성공만 바로 반환 (현재 비활성화)
            // return ResponseEntity.ok(Map.of(
            //     "status", "success",
            //     "message", "FastAPI 비활성화",
            //     "savedCount", resultDocs
            // ));

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError()
                    .body(Map.of("status", "error", "message", e.getMessage()));
        }
    }

}
