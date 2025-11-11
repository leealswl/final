package com.example.backend.domain;

import java.util.Date;
import lombok.Data;

/**
 * 2025-11-09 suyeon 추가: 공고문 목차 정보 저장을 위한 도메인 객체
 * TABLE_OF_CONTENTS 테이블과 매핑
 */
@Data
public class TableOfContents {
    private Long tocIdx;            // PK (시퀀스)
    private Long projectIdx;        // FK (프로젝트 ID)
    private String source;          // 목차 출처 (예: announcement_pdf, attachment_pdf)
    private Integer totalSections;  // 전체 섹션 수
    private String tocData;         // 목차 데이터 (JSON 문자열)
    private Date createdAt;         // DB 생성 시간 (자동)
}
