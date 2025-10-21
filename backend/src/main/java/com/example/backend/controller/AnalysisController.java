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
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;


@RestController
@RequestMapping("/api/analysis/*")
public class AnalysisController {

    @Autowired
    FastAPIService fastApi;

    @GetMapping("/path")
    public String test() {
        Path uploadPath = Paths.get("uploads/");
        System.out.println(uploadPath);
        return "test";
    }
    

    @PostMapping("/")
    public ResponseEntity<String> receiveAndSendFiles(
            @RequestParam("files") List<MultipartFile> files,
            @RequestParam("folders") List<String> folders) {

        try {
            for (int i = 0; i < files.size(); i++) {
                MultipartFile file = files.get(i);
                String folderName = folders.get(i);

                Path uploadPath = Paths.get("uploads/" + folderName);
                if (!Files.exists(uploadPath)) {
                    Files.createDirectories(uploadPath);
                }

                Path filePath = uploadPath.resolve(file.getOriginalFilename());
                Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);
            }

            return ResponseEntity.ok("모든 파일 업로드 성공!");
        } catch (IOException e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError().body("업로드 실패: " + e.getMessage());
        }
    }
}
