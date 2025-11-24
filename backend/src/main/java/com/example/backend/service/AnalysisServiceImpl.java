package com.example.backend.service;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.backend.domain.AnalysisResult;
import com.example.backend.domain.TableOfContents;
import com.example.backend.mapper.AnalysisMapper;
import com.fasterxml.jackson.databind.ObjectMapper;

/**
 * 2025-11-09 suyeon 추가: FastAPI 분석 결과를 Oracle DB에 저장하는 서비스 구현체
 */
@Service
public class AnalysisServiceImpl implements AnalysisService {

    @Autowired
    private AnalysisMapper analysisMapper;

    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * FastAPI로부터 받은 분석 결과를 Oracle DB에 저장
     *
     * @param projectIdx 프로젝트 ID
     * @param userId 사용자 ID
     * @param features 추출된 Feature 목록
     * @param tableOfContents 목차 정보
     * @return 저장 결과
     */
    @Transactional
    @Override
    public Map<String, Object> saveAnalysisResult(
            Long projectIdx,
            String userId,
            List<Map<String, Object>> features,
            Map<String, Object> tableOfContents) {

        System.out.println("💾 AnalysisService: 분석 결과 저장 시작");
        int featuresCount = 0;
        boolean tocSaved = false;

        try {
            // ========================================
            // 0. 재분석 대비: 기존 데이터 삭제
            // ========================================
            System.out.println("  🗑️  기존 분석 결과 삭제 중 (projectIdx=" + projectIdx + ")");
            try {
                int deletedFeatures = analysisMapper.deleteAnalysisResultByProject(projectIdx);
                int deletedToc = analysisMapper.deleteTableOfContentsByProject(projectIdx);
                System.out.println("  ✅ 삭제 완료: Features " + deletedFeatures + "개, TOC " + deletedToc + "개");
            } catch (Exception e) {
                System.err.println("  ⚠️ 기존 데이터 삭제 중 오류 (무시하고 계속 진행): " + e.getMessage());
                // 삭제 실패해도 계속 진행 (새 데이터 저장 시도)
            }

            // ========================================
            // 1. ANALYSIS_RESULT 테이블에 Features 저장
            // ========================================
            if (features != null && !features.isEmpty()) {
                System.out.println("  📊 Features 저장 중: " + features.size() + "개");

                for (Map<String, Object> feature : features) {
                    AnalysisResult result = new AnalysisResult();
                    result.setProjectIdx(projectIdx);
                    result.setFeatureCode((String) feature.get("feature_code"));
                    result.setFeatureName((String) feature.get("feature_name"));
                    result.setTitle((String) feature.get("title"));
                    result.setSummary((String) feature.get("summary"));
                    result.setFullContent((String) feature.get("full_content"));

                    // key_points: List<String> → 파이프로 연결
                    @SuppressWarnings("unchecked")
                    List<String> keyPoints = (List<String>) feature.get("key_points");
                    if (keyPoints != null) {
                        result.setKeyPoints(String.join("|", keyPoints));
                    }

                    // writing_strategy: Map<String, Object> → JSON 문자열
                    @SuppressWarnings("unchecked")
                    Map<String, Object> writingStrategy = (Map<String, Object>) feature.get("writing_strategy");
                    if (writingStrategy != null && !writingStrategy.isEmpty()) {
                        String strategyJson = objectMapper.writeValueAsString(writingStrategy);
                        result.setWritingStrategy(strategyJson);
                    }

                    // 숫자 필드 처리
                    result.setVectorSimilarity(getDoubleValue(feature, "vector_similarity"));
                    result.setChunksFromAnnouncement(getIntValue(feature, "chunks_from_announcement"));
                    result.setChunksFromAttachments(getIntValue(feature, "chunks_from_attachments"));

                    // referenced_attachments: List<String> → 파이프로 연결
                    @SuppressWarnings("unchecked")
                    List<String> refAttachments = (List<String>) feature.get("referenced_attachments");
                    if (refAttachments != null) {
                        result.setReferencedAttachments(String.join("|", refAttachments));
                    }

                    // extracted_at: ISO 문자열 → Date (Oracle에서 TO_TIMESTAMP로 변환)
                    String extractedAtStr = (String) feature.get("extracted_at");
                    if (extractedAtStr != null) {
                        try {
                            // ISO 8601 형식: 2025-11-09T12:34:56
                            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss");
                            result.setExtractedAt(sdf.parse(extractedAtStr.substring(0, 19)));
                        } catch (Exception e) {
                            System.err.println("  ⚠️ extracted_at 파싱 실패: " + extractedAtStr);
                        }
                    }

                    // DB 저장 (중복 키 에러 처리)
                    try {
                        analysisMapper.insertAnalysisResult(result);
                        featuresCount++;
                    } catch (DuplicateKeyException e) {
                        System.err.println("  ⚠️ 중복 키 에러 (무시하고 계속 진행): feature_code=" + result.getFeatureCode());
                        // 중복 키 에러는 무시하고 계속 진행 (이미 저장된 데이터로 간주)
                    } catch (Exception e) {
                        System.err.println("  ❌ Feature 저장 실패: " + e.getMessage());
                        e.printStackTrace();
                        // 다른 에러는 로그만 남기고 계속 진행
                    }
                }

                System.out.println("  ✅ Features 저장 완료: " + featuresCount + "개");
            } else {
                System.out.println("  ⚠️ Features 없음");
            }

            // ========================================
            // 2. TABLE_OF_CONTENTS 테이블에 목차 저장
            // ========================================
            if (tableOfContents != null && !tableOfContents.isEmpty()) {
                System.out.println("  📑 목차 저장 중...");

                TableOfContents toc = new TableOfContents();
                toc.setProjectIdx(projectIdx);
                toc.setSource((String) tableOfContents.get("source"));
                toc.setTotalSections(getIntValue(tableOfContents, "total_sections"));

                // 전체 목차 데이터를 JSON 문자열로 변환
                String tocDataJson = objectMapper.writeValueAsString(tableOfContents);
                toc.setTocData(tocDataJson);

                // DB 저장
                analysisMapper.insertTableOfContents(toc);
                tocSaved = true;

                System.out.println("  ✅ 목차 저장 완료 (출처: " + toc.getSource() + ")");
            } else {
                System.out.println("  ⚠️ 목차 없음");
            }

            System.out.println("✅ AnalysisService: 저장 완료");

        } catch (Exception e) {
            System.err.println("❌ AnalysisService: 저장 실패 - " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Oracle DB 저장 실패: " + e.getMessage(), e);
        }

        // 결과 반환
        Map<String, Object> result = new HashMap<>();
        result.put("features_count", featuresCount);
        result.put("toc_saved", tocSaved);
        return result;
    }

    /**
     * Map에서 Double 값 안전하게 추출
     */
    private Double getDoubleValue(Map<String, Object> map, String key) {
        Object value = map.get(key);
        if (value == null) return null;
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        return null;
    }

    /**
     * Map에서 Integer 값 안전하게 추출
     */
    private Integer getIntValue(Map<String, Object> map, String key) {
        Object value = map.get(key);
        if (value == null) return null;
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        return null;
    }

    /**
     * 2025-11-23 추가: 프로젝트별 분석 결과 조회 (v11_generator용)
     * 
     * @param projectIdx 프로젝트 ID
     * @return 분석 결과 컨텍스트
     *   - result_toc: 목차 데이터 (JSON 파싱)
     *   - extracted_features: 분석 결과 배열 (DB 행들을 배열로 변환)
     */
    @Override
    public Map<String, Object> getAnalysisContext(Long projectIdx) {
        System.out.println("📖 AnalysisService: 분석 결과 조회 시작 (projectIdx=" + projectIdx + ")");
        
        Map<String, Object> context = new HashMap<>();
        
        try {
            // 1. 목차 데이터 조회
            TableOfContents toc = analysisMapper.getTableOfContentsByProject(projectIdx);
            if (toc != null && toc.getTocData() != null) {
                // JSON 문자열을 Map으로 파싱
                Map<String, Object> tocData = objectMapper.readValue(toc.getTocData(), Map.class);
                context.put("result_toc", tocData);
                
                // 디버깅: 목차 데이터 구조 확인
                System.out.println("  ✅ 목차 데이터 조회 완료: " + toc.getTotalSections() + "개 섹션");
                System.out.println("  📋 목차 구조 확인:");
                System.out.println("    - source: " + tocData.get("source"));
                System.out.println("    - source_file: " + tocData.get("source_file"));
                System.out.println("    - total_sections: " + tocData.get("total_sections"));
                System.out.println("    - sections 배열 크기: " + (tocData.containsKey("sections") ? ((List<?>) tocData.get("sections")).size() : "없음"));
            } else {
                context.put("result_toc", null);
                System.out.println("  ⚠️ 목차 데이터 없음 (toc=" + (toc != null ? "존재" : "null") + ", tocData=" + (toc != null && toc.getTocData() != null ? "존재" : "null") + ")");
            }

            // 2. 분석 결과(Features) 조회 및 배열로 변환
            List<AnalysisResult> results = analysisMapper.getAnalysisResultsByProject(projectIdx);
            List<Map<String, Object>> features = new ArrayList<>();
            
            for (AnalysisResult result : results) {
                Map<String, Object> feature = new HashMap<>();
                feature.put("result_id", result.getResultIdx());
                feature.put("project_idx", projectIdx);  // JSON 파일과 동일한 형식 유지
                feature.put("feature_code", result.getFeatureCode());
                feature.put("feature_name", result.getFeatureName());
                feature.put("title", result.getTitle());
                feature.put("summary", result.getSummary());
                feature.put("full_content", result.getFullContent());
                
                // key_points: 파이프 구분 문자열 → List
                if (result.getKeyPoints() != null && !result.getKeyPoints().isEmpty()) {
                    feature.put("key_points", List.of(result.getKeyPoints().split("\\|")));
                } else {
                    feature.put("key_points", List.of());
                }
                
                // writing_strategy: JSON 문자열 → Map
                if (result.getWritingStrategy() != null && !result.getWritingStrategy().isEmpty()) {
                    try {
                        Map<String, Object> strategy = objectMapper.readValue(result.getWritingStrategy(), Map.class);
                        feature.put("writing_strategy", strategy);
                    } catch (Exception e) {
                        System.err.println("  ⚠️ writing_strategy 파싱 실패: " + e.getMessage());
                        feature.put("writing_strategy", Map.of());
                    }
                } else {
                    feature.put("writing_strategy", Map.of());
                }
                
                feature.put("vector_similarity", result.getVectorSimilarity());
                feature.put("chunks_from_announcement", result.getChunksFromAnnouncement());
                feature.put("chunks_from_attachments", result.getChunksFromAttachments());
                
                // referenced_attachments: 파이프 구분 문자열 → List
                if (result.getReferencedAttachments() != null && !result.getReferencedAttachments().isEmpty()) {
                    feature.put("referenced_attachments", List.of(result.getReferencedAttachments().split("\\|")));
                } else {
                    feature.put("referenced_attachments", List.of());
                }
                
                if (result.getExtractedAt() != null) {
                    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss");
                    feature.put("extracted_at", sdf.format(result.getExtractedAt()));
                }
                
                features.add(feature);
            }
            
            context.put("extracted_features", features);
            System.out.println("  ✅ 분석 결과 조회 완료: " + features.size() + "개 Feature");
            
        } catch (Exception e) {
            System.err.println("❌ AnalysisService: 조회 실패 - " + e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("분석 결과 조회 실패: " + e.getMessage(), e);
        }
        
        return context;
    }
}
