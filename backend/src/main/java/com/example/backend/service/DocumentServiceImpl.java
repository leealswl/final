package com.example.backend.service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import com.example.backend.domain.Document;
import com.example.backend.mapper.DocumentMapper;

@Service
public class DocumentServiceImpl implements DocumentService{

    @Value("${upload.dir}") // application.yml의 upload.dir 사용 (예: C:/vs/final/uploads)
    private String uploadDir;

    @Autowired
    DocumentMapper documentMapper;

    @Transactional
    @Override
    public int saveFilesAndDocuments(List<MultipartFile> files, List<Long> folders, String userid, Long projectIdx) throws IOException {
        System.out.println("document service 작동 시작");
        System.out.println("uploadDir: " + uploadDir);
        int totalInserted = 0;
        Path baseUploadPath = Paths.get(uploadDir).toAbsolutePath();
        System.out.println("resolved upload path: " + baseUploadPath);

        for (int i = 0; i < files.size(); i++) {
            MultipartFile file = files.get(i);
            Long folderName = folders.get(i);

            Path uploadPath = baseUploadPath.resolve(Paths.get(userid, String.valueOf(projectIdx), String.valueOf(folderName)));
            System.out.println("uploadPath: " + uploadPath);
            if (!Files.exists(uploadPath)) {
                Files.createDirectories(uploadPath);
            } //절대경로로 저장

            Path filePath = uploadPath.resolve(file.getOriginalFilename());
            Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);

            System.out.println("[SAVE] " + filePath.toAbsolutePath()); // 꼭 찍어보자

            Document document = new Document();
            document.setProjectIdx(projectIdx);
            document.setFolder(String.valueOf(folderName)); // 필요시 String 변환
            document.setFileName(file.getOriginalFilename());
            document.setFilePath(filePath.toString());

            totalInserted += documentMapper.insertDocument(document);
        }
        System.out.println("document service 작동 완료");
        return totalInserted;
    }

    /**
     * 2025-11-09 수연 추가: 파일 저장 후 파일 정보 반환
     * 목적: Frontend가 파일 경로 정보를 받아서 store에 저장할 수 있도록 함
     */
    @Transactional
    @Override
    public List<Map<String, Object>> saveFilesAndReturnInfo(List<MultipartFile> files, List<Long> folders, String userid, Long projectIdx) throws IOException {
        System.out.println("document service (with info) 작동 시작");
        System.out.println("uploadDir: " + uploadDir);

        List<Map<String, Object>> savedFiles = new ArrayList<>();

        Path baseUploadPath = Paths.get(uploadDir).toAbsolutePath();
        System.out.println("resolved upload path: " + baseUploadPath);

        for (int i = 0; i < files.size(); i++) {
            MultipartFile file = files.get(i);
            Long folderName = folders.get(i);

            Path uploadPath = baseUploadPath.resolve(Paths.get(userid, String.valueOf(projectIdx), String.valueOf(folderName)));
            if (!Files.exists(uploadPath)) {
                Files.createDirectories(uploadPath);
            }

            Path filePath = uploadPath.resolve(file.getOriginalFilename());
            Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);

            System.out.println("[SAVE] " + filePath.toAbsolutePath());

            // DB에 저장
            Document document = new Document();
            document.setProjectIdx(projectIdx);
            document.setFolder(String.valueOf(folderName));
            document.setFileName(file.getOriginalFilename());
            document.setFilePath(filePath.toString());

            documentMapper.insertDocument(document);

            // 파일 정보 수집 (Frontend로 반환)
            Map<String, Object> fileInfo = new HashMap<>();
            fileInfo.put("id", document.getDocumentIdx()); // DB에서 생성된 ID
            fileInfo.put("name", file.getOriginalFilename());
            fileInfo.put("path", filePath.toString()); // 파일 경로
            fileInfo.put("folder", folderName);
            fileInfo.put("size", file.getSize());

            savedFiles.add(fileInfo);
        }

        System.out.println("document service (with info) 작동 완료: " + savedFiles.size() + "개");
        return savedFiles;
    }
}
