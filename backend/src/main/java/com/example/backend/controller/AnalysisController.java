package com.example.backend.controller;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.example.backend.FastAPI.FastAPIService;
import com.example.backend.service.DocumentService;


@RestController
@RequestMapping("/api/analysis/*")
public class AnalysisController {

    @Autowired
    FastAPIService fastApi;

    @Autowired
    DocumentService documentService;

    @GetMapping("/path")
    public String test() {
        Path uploadPath = Paths.get("uploads/");
        System.out.println(uploadPath);
        return "test";
    }
    

    @PostMapping("/")
    public ResponseEntity<String> receiveAndSendFiles(
            @RequestParam("files") List<MultipartFile> files,
            @RequestParam("folders") List<Long> folders,
            @RequestParam("projectidx") Long projectidx,
            @RequestParam("userid") String userid) {

        try {
            documentService.saveFilesAndDocuments(files, folders, userid, projectidx);
            return ResponseEntity.ok("모든 파일 업로드 성공!");
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError().body("업로드 실패: " + e.getMessage());
        }
    }

}
