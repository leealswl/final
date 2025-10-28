package com.example.backend.onlyoffice;

import org.springframework.stereotype.Service;

@Service
public class FileService {
    public FileMeta getById(String fileId) {
        if ("doc-1".equals(fileId)) {
            FileMeta f = new FileMeta();
            f.id = "doc-1";
            f.name = "제안서.docx";
            f.mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            f.storageKey = "proposal.docx"; // ./uploads/proposal.docx 로 두자
            return f;
        }
        return null;
    }
    
}
