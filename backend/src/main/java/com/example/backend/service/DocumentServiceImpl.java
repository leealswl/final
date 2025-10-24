package com.example.backend.service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.List;

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
        int totalInserted = 0;
        for (int i = 0; i < files.size(); i++) {
            MultipartFile file = files.get(i);
            Long folderName = folders.get(i);
            
            Path uploadPath = Paths.get(uploadDir, userid, String.valueOf(projectIdx), String.valueOf(folderName));
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
}
