package com.example.backend.service;

import java.util.List;

import org.springframework.web.multipart.MultipartFile;

public interface DocumentService {

    public int saveFilesAndDocuments(List<MultipartFile> files, List<Long> folders, String userId, Long projectIdx)
            throws Exception;

}
