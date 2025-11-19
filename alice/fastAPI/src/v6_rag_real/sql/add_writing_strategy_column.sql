-- ========================================
-- ANALYSIS_RESULT 테이블에 writing_strategy 컬럼 추가
-- 작성일: 2025-01-17
-- 목적: 사업계획서 작성 전략 저장
-- ========================================

-- 1. writing_strategy 컬럼 추가 (CLOB 타입, JSON 문자열 저장)
ALTER TABLE ANALYSIS_RESULT ADD (
    writing_strategy CLOB
);

-- 2. 컬럼 설명 추가
COMMENT ON COLUMN ANALYSIS_RESULT.writing_strategy IS '사업계획서 작성 전략 (JSON 형식)';

-- 3. 확인
SELECT column_name, data_type, nullable, data_default
FROM user_tab_columns
WHERE table_name = 'ANALYSIS_RESULT'
AND column_name = 'WRITING_STRATEGY';

-- ========================================
-- writing_strategy JSON 구조 예시:
-- {
--   "overview": "이 섹션에서 평가위원이 중요하게 보는 핵심 포인트",
--   "must_include": ["반드시 포함해야 할 내용1", "반드시 포함해야 할 내용2"],
--   "recommended_structure": ["1. 추천 작성 구조 1단계", "2. 추천 작성 구조 2단계"],
--   "writing_tips": ["정량적 데이터 포함 필요", "구체적 수치 제시"],
--   "common_mistakes": ["피해야 할 실수1", "피해야 할 실수2"],
--   "example_phrases": ["좋은 작성 예시1", "좋은 작성 예시2"],
--   "evaluation_criteria": "평가 시 중점 사항",
--   "word_count_guide": "권장 분량 (예: 1-2페이지)"
-- }
-- ========================================
