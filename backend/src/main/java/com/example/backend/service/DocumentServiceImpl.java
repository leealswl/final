package com.example.backend.service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.nio.file.Path;
import java.nio.file.Paths;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import com.example.backend.domain.Document;
import com.example.backend.mapper.DocumentMapper;

@Service
public class DocumentServiceImpl implements DocumentService{

    @Autowired
    DocumentMapper documentMapper;

    @Transactional
    @Override
    public int saveFilesAndDocuments(List<MultipartFile> files, List<Long> folders, String userid, Long projectIdx) throws IOException {
        int totalInserted = 0;
        for (int i = 0; i < files.size(); i++) {
            MultipartFile file = files.get(i);
            Long folderName = folders.get(i);

            Path uploadPath = Paths.get("uploads/" + userid + "/" + projectIdx + "/" + folderName);
            if (!Files.exists(uploadPath)) {
                Files.createDirectories(uploadPath);
            }

            Path filePath = uploadPath.resolve(file.getOriginalFilename());
            Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);

            Document document = new Document();
            document.setProjectIdx(projectIdx);
            document.setFolder(String.valueOf(folderName)); // 필요시 String 변환
            document.setFileName(file.getOriginalFilename());
            document.setFilePath(filePath.toString());

            // totalInserted += documentMapper.insertDocument(document);
        }
        return totalInserted;
    }
}
