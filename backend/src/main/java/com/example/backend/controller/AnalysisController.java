package com.example.backend.controller;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.example.backend.service.DocumentService;




@RestController
@RequestMapping("/api/analysis")
public class AnalysisController {

    // @Autowired
    // FastAPIService fastApi;

    @Autowired
    DocumentService documentService;

    @GetMapping("/path")
    public String test() {
        Path uploadPath = Paths.get("uploads/");
        System.out.println(uploadPath);
        return "test";
    }
    

    @PostMapping(value = {"", "/"}, consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Map<String, Object>> receiveAndSendFiles(
        @RequestParam("files") List<MultipartFile> files,
        @RequestParam("folders") List<Long> folders,
        @RequestParam("projectidx") Long projectidx,
        @RequestParam("userid") String userid) {
            System.out.println("analysis controller 작동 시작");

        try {
            int resultDocs = documentService.saveFilesAndDocuments(files, folders, userid, projectidx);

            if (resultDocs <= 0) {
                return ResponseEntity.badRequest()
                        .body(Map.of("status", "fail", "message", "문서 저장 실패"));
            }

            // Map<String, Object> fastApiResult = fastApi.sendFilesToFastAPI(files, folders, userid);

            // if (fastApiResult != null && "success".equals(fastApiResult.get("status"))) {
            //     return new ResponseEntity<>(fastApiResult, HttpStatus.OK);
            // } else {
            //     return ResponseEntity.internalServerError()
            //             .body(Map.of("status", "fail", "message", "FastAPI 처리 실패"));
            // }

             // ✅ FastAPI를 안 쓰는 동안에는 저장 성공만 바로 반환
            return ResponseEntity.ok(Map.of(
                "status", "success",
                "message", "FastAPI 비활성화",
                "savedCount", resultDocs
            ));

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError()
                    .body(Map.of("status", "error", "message", e.getMessage()));
        }
    }

}
