package com.example.backend.domain;

import java.util.Date;
import lombok.Data;

/**
 * 2025-11-09 suyeon 추가: FastAPI 분석 결과 저장을 위한 도메인 객체
 * ANALYSIS_RESULT 테이블과 매핑
 */
@Data
public class AnalysisResult {
    private Long resultIdx;              // PK (시퀀스)
    private Long projectIdx;             // FK (프로젝트 ID)
    private String featureCode;          // Feature 코드 (예: F1, F2)
    private String featureName;          // Feature 이름
    private String title;                // 제목
    private String summary;              // 요약
    private String fullContent;          // 전체 내용
    private String keyPoints;            // 핵심 포인트 (파이프로 구분)
    private String writingStrategy;      // 작성 전략 (JSON 문자열)
    private Double vectorSimilarity;     // 벡터 유사도
    private Integer chunksFromAnnouncement;   // 공고문 청크 수
    private Integer chunksFromAttachments;    // 첨부파일 청크 수
    private String referencedAttachments;     // 참조 첨부파일 (파이프로 구분)
    private Date extractedAt;            // 추출 시간
    private Date createdAt;              // DB 생성 시간 (자동)
}
