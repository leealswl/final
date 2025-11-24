package com.example.backend.mapper;

import org.apache.ibatis.annotations.Mapper;
import com.example.backend.domain.AnalysisResult;
import com.example.backend.domain.TableOfContents;

/**
 * 2025-11-09 suyeon 추가: FastAPI 분석 결과를 Oracle DB에 저장하기 위한 Mapper
 */
@Mapper
public interface AnalysisMapper {
    /**
     * ANALYSIS_RESULT 테이블에 Feature 저장
     * @param analysisResult Feature 데이터
     * @return 삽입된 행 수
     */
    int insertAnalysisResult(AnalysisResult analysisResult);

    /**
     * TABLE_OF_CONTENTS 테이블에 목차 저장
     * @param tableOfContents 목차 데이터
     * @return 삽입된 행 수
     */
    int insertTableOfContents(TableOfContents tableOfContents);

    /**
     * 2025-11-10 suyeon 추가: 프로젝트별 분석 결과 삭제 (재분석 대비)
     * @param projectIdx 프로젝트 ID
     * @return 삭제된 행 수
     */
    int deleteAnalysisResultByProject(Long projectIdx);

    /**
     * 2025-11-10 suyeon 추가: 프로젝트별 목차 데이터 삭제 (재분석 대비)
     * @param projectIdx 프로젝트 ID
     * @return 삭제된 행 수
     */
    int deleteTableOfContentsByProject(Long projectIdx);
}
