package com.example.backend.service;

import java.util.List;
import java.util.Map;

import org.springframework.web.multipart.MultipartFile;

public interface DocumentService {

    public int saveFilesAndDocuments(List<MultipartFile> files, List<Long> folders, String userId, Long projectIdx)
            throws Exception;

    /**
     * 2025-11-09 수연 추가: 파일 정보와 함께 저장 (경로 정보 반환)
     */
    public List<Map<String, Object>> saveFilesAndReturnInfo(List<MultipartFile> files, List<Long> folders, String userId, Long projectIdx)
            throws Exception;

}
