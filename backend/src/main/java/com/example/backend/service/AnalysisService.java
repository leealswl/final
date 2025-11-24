package com.example.backend.service;

import java.util.List;
import java.util.Map;

/**
 * 2025-11-09 suyeon 추가: FastAPI 분석 결과를 Oracle DB에 저장하는 서비스
 */
public interface AnalysisService {
    /**
     * FastAPI로부터 받은 분석 결과를 Oracle DB에 저장
     *
     * @param projectIdx 프로젝트 ID
     * @param userId 사용자 ID
     * @param features 추출된 Feature 목록
     * @param tableOfContents 목차 정보
     * @return 저장 결과 (features_count, toc_saved)
     */
    Map<String, Object> saveAnalysisResult(
        Long projectIdx,
        String userId,
        List<Map<String, Object>> features,
        Map<String, Object> tableOfContents
    );
}
